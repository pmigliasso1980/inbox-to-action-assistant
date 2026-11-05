"""Validated planning, bounded execution artifacts, replanning, and escalation."""
from __future__ import annotations

import json
import time
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

import anthropic
from pydantic import BaseModel, Field

from agents.llm import MODEL, Usage, UsageLedger
from agents.plan_validator import Plan, Step, topological_order, validate_plan
from agents.tool_agent import ToolAgent
from evals.run_baseline import Defect, Review

STABLE_PLANNER_PREFIX = """You are a bounded code-review planner. Return only the requested structured plan.
Registered read-only tools: read_code(file), run_linter(file, profile), run_tests(file, suite).
Plans must be ordered DAGs with at most 6 steps. Every dependency must be earlier. Use only registered tools.
Each step must produce one named bounded artifact and have a concrete observable success criterion.
Reasoning/synthesis steps must depend on the artifacts they consume. Never add write actions.
Decompose by distinct verification concern, preserve successful evidence across replans, and stay within the stated budget.
The final scored review uses exactly this frozen taxonomy: auth_bypass, command_injection, division_by_zero,
identity_comparison, incorrect_cache_key, infinite_loop, insecure_random, invalid_amount, missing_await,
missing_timeout, mutable_default, non_atomic_transaction, null_dereference, off_by_one, path_traversal,
race_condition, resource_leak, result_overwritten, sql_injection, ssrf, swallowed_exception,
timezone_naive, unchecked_status. Plans must target only concrete defects in that taxonomy and must exclude
style, generic hardening, evidence gaps, and speculative improvements.
"""


@dataclass
class StepArtifact:
    step_id: str
    status: Literal["success", "failed", "blocked"]
    produced: str
    value: Any
    summary: str

    def bounded(self, limit: int = 1200) -> dict[str, Any]:
        raw = json.dumps(self.value, default=str)
        value: Any = self.value if len(raw) <= limit else raw[:limit] + "…"
        return {"step_id": self.step_id, "status": self.status, "produced": self.produced,
                "value": value, "summary": self.summary[:240]}


class EscalatedReview(BaseModel):
    completed: list[str]
    failed: list[str]
    blocked_by: list[str]
    review: Review


def _usage(message: Any) -> Usage:
    raw=message.usage
    return Usage(raw.input_tokens,raw.output_tokens,getattr(raw,"cache_read_input_tokens",0) or 0,
                 getattr(raw,"cache_creation_input_tokens",0) or 0)


class PlanningAgent:
    def __init__(self, *, max_plan_steps: int = 6, max_total_steps: int = 10, max_replans: int = 2,
                 max_plan_revisions: int = 2, strike_limit: int = 2, preserve_results: bool = True,
                 caching: bool = True, task_budget_tokens: int = 7000, trace_path: str | Path | None = None,
                 failure_once_tool: str | None = None, persistent_failure_tool: str | None = None) -> None:
        self.max_plan_steps=max_plan_steps;self.max_total_steps=max_total_steps;self.max_replans=max_replans
        self.max_plan_revisions=max_plan_revisions;self.strike_limit=strike_limit;self.preserve_results=preserve_results
        self.caching=caching;self.task_budget_tokens=task_budget_tokens;self.trace_path=Path(trace_path) if trace_path else None
        self.failure_once_tool=failure_once_tool;self.persistent_failure_tool=persistent_failure_tool
        self._injected_once=False;self.side_effect_count=0

    def _trace(self,event:dict[str,Any])->None:
        if self.trace_path:
            self.trace_path.parent.mkdir(parents=True,exist_ok=True)
            with self.trace_path.open("a",encoding="utf-8") as handle:handle.write(json.dumps(event,default=str)+"\n")

    def _structured(self, user: str, schema: type[BaseModel], *, max_tokens: int, ledger: UsageLedger, label: str):
        client=anthropic.Anthropic(max_retries=2)
        system: Any=STABLE_PLANNER_PREFIX
        if self.caching:
            system=[{"type":"text","text":STABLE_PLANNER_PREFIX,"cache_control":{"type":"ephemeral"}}]
        message=client.messages.parse(model=MODEL,max_tokens=max_tokens,output_config={"effort":"low"},
            output_format=schema,system=system,messages=[{"role":"user","content":user}])
        usage=_usage(message);ledger.add(usage,label=label,effort="low")
        if message.parsed_output is None:raise ValueError(f"{label} returned no structured output")
        return message.parsed_output

    def _plan(self, objective:str, ledger:UsageLedger, *, artifacts:list[StepArtifact], remaining:int,
              violations:list[str]|None=None)->tuple[Plan,list[str],int]:
        attempts=0;feedback=violations or []
        while attempts<=self.max_plan_revisions:
            attempts+=1
            prior=[x.bounded() for x in artifacts] if self.preserve_results else []
            prompt=f"OBJECTIVE:\n{objective}\nREMAINING TOTAL STEPS: {remaining}\nPRIOR SUCCESS/FAILURE ARTIFACTS:\n{json.dumps(prior)}\n"
            if feedback:prompt+=f"REVISE THE PLAN TO FIX THESE SPECIFIC VIOLATIONS:\n{json.dumps(feedback)}\n"
            plan=self._structured(prompt,Plan,max_tokens=min(1800,self.task_budget_tokens),ledger=ledger,label="plan")
            feedback=validate_plan(plan,max_steps=min(self.max_plan_steps,remaining))
            self._validation_log.append(list(feedback))
            self._trace({"event":"plan","attempt":attempts,"plan":plan.model_dump(),"violations":feedback,"prior_results":prior})
            if not feedback:return plan,[],attempts
        return plan,feedback,attempts

    def _execute_step(self,step:Step,file:str,objective:str,ledger:UsageLedger)->tuple[StepArtifact,bool]:
        if step.tool is None:
            return StepArtifact(step.id,"success",step.produces,{"reasoning_deferred":True},"reasoning deferred to final synthesis"),False
        self.side_effect_count+=1
        if step.tool==self.persistent_failure_tool or (step.tool==self.failure_once_tool and not self._injected_once):
            self._injected_once=True
            return StepArtifact(step.id,"failed",step.produces,None,f"injected failure for {step.tool}"),False
        instruction=f"Execute exactly the planned tool step for {file}: {step.description}. Call {step.tool} and no other tool. Success criterion: {step.success_criterion}."
        agent=ToolAgent(max_steps=3,trace_path=None)
        run=agent.run(instruction,system="Execute one read-only tool step. Report its result without adding unsupported claims.")
        for usage_key in []:pass
        # ToolAgent owns its ledger; merge normalized totals as one aggregate usage entry.
        u=run["usage"];ledger.calls.append(Usage(u["input_tokens"],u["output_tokens"],u["cached_input_tokens"],u["cache_write_tokens"]))
        calls=[call for call in run["tool_calls"] if call["name"]==step.tool]
        if not calls:
            return StepArtifact(step.id,"failed",step.produces,None,f"model did not call required tool {step.tool}"),False
        call=calls[-1];value=call.get("result");confirmed=bool(call.get("confirmed"))
        semantic=confirmed and value not in (None,{},[]) and bool(step.success_criterion.strip())
        # A transport/tool call can return a payload yet fail confirmation or the
        # declared success criterion; count that separately from executor errors.
        caught=value is not None and not semantic
        status="success" if semantic else "failed"
        summary=call.get("confirmation","") if semantic else f"success criterion failed: {step.success_criterion}"
        return StepArtifact(step.id,status,step.produces,value,summary),caught

    def run(self, *, item:dict[str,Any]) -> dict[str,Any]:
        started=time.perf_counter();ledger=UsageLedger();artifacts:list[StepArtifact]=[];strikes=Counter();self._validation_log=[]
        plan_count=0;executed=0;replans=0;validation_revisions=0;caught_failures=0;abandoned=False;escalated=False
        objective=f"Review {item['file']} for concrete defects using exact category and line evidence. Source:\n{item['input']}"
        plan,violations,attempts=self._plan(objective,ledger,artifacts=[],remaining=self.max_total_steps)
        plan_count+=1;validation_revisions+=attempts-1
        if violations:
            abandoned=True
        while not abandoned:
            by_id={step.id:step for step in plan.steps};failed_id=None
            for step_id in topological_order(plan):
                step=by_id[step_id]
                if executed>=self.max_total_steps:failed_id=step.id;break
                if any(next((a for a in reversed(artifacts) if a.step_id==d),None) and next(a for a in reversed(artifacts) if a.step_id==d).status!="success" for d in step.depends_on):
                    artifacts.append(StepArtifact(step.id,"blocked",step.produces,None,"dependency failed"));continue
                artifact,caught=self._execute_step(step,item["file"],objective,ledger);artifacts.append(artifact);executed+=1;caught_failures+=int(caught)
                self._trace({"event":"step","plan":plan_count,"artifact":artifact.bounded()})
                if artifact.status=="failed":
                    failure_key=step.tool or step.id
                    strikes[failure_key]+=1;failed_id=failure_key;break
            if failed_id is None:break
            if strikes[failed_id]>=self.strike_limit or replans>=self.max_replans or executed>=self.max_total_steps:
                escalated=True;break
            replans+=1
            plan,violations,attempts=self._plan(objective,ledger,artifacts=artifacts,remaining=self.max_total_steps-executed)
            plan_count+=1;validation_revisions+=attempts-1
            if violations:abandoned=True;break
        bounded=[artifact.bounded() for artifact in artifacts]
        missing=[a.step_id for a in artifacts if a.status!="success"]
        synth=f"""OBJECTIVE:\n{objective}\nBOUNDED STEP ARTIFACTS:\n{json.dumps(bounded)}
Return at most five concrete defects. Category must be from the frozen taxonomy in the system instruction.
Do not emit generic error-handling, async-misuse, evidence-gap, style, or speculative findings.
Use exact 1-based lines and prefer precision when evidence is incomplete.\n"""
        if escalated or abandoned:synth+=f"ESCALATION: Explicitly state missing/blocked evidence {missing}; do not assert claims that depend on it.\n"
        if escalated or abandoned:
            wrapped=self._structured(synth,EscalatedReview,max_tokens=min(1100,self.task_budget_tokens),ledger=ledger,label="synthesis")
            final=wrapped.review;escalation_output={"completed":wrapped.completed,"failed":wrapped.failed,"blocked_by":wrapped.blocked_by}
        else:
            final=self._structured(synth,Review,max_tokens=min(900,self.task_budget_tokens),ledger=ledger,label="synthesis");escalation_output=None
        self._trace({"event":"synthesis","escalated":escalated,"abandoned":abandoned,"missing":missing,"escalation_output":escalation_output,"review":final.model_dump()})
        return {"id":item["id"],"review":final.model_dump(),"plans":plan_count,"first_plan_valid":bool(self._validation_log and not self._validation_log[0]),
          "validation_revisions":validation_revisions,"violations":violations,"steps_executed":executed,
          "step_artifacts":bounded,"step_successes":sum(a.status=="success" for a in artifacts),
          "criterion_caught_failures":caught_failures,"replans":replans,"escalated":escalated,"abandoned":abandoned,
          "strikes":dict(strikes),"validation_log":self._validation_log,"escalation_output":escalation_output,
          "side_effect_count":self.side_effect_count,"usage":ledger.summary(),
          "latency_seconds":time.perf_counter()-started}
