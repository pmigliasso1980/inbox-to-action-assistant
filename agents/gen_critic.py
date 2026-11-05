"""Role-separated generator–critic loop with typed, gated handoffs."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import anthropic

from agents.gates_multiagent import CriticArtifact,GeneratorArtifact,bound_critic,bound_generator,gate_critic,gate_generator
from agents.llm import MODEL,Usage,UsageLedger
from evals.score import score_item

ROOT=Path(__file__).resolve().parents[1]

def _usage(message:Any)->Usage:
 raw=message.usage
 return Usage(raw.input_tokens,raw.output_tokens,getattr(raw,"cache_read_input_tokens",0) or 0,getattr(raw,"cache_creation_input_tokens",0) or 0)

def _task(item:dict)->str:
 return f"File: {item['file']}\n```python\n{item['input']}\n```"

def _stable(role_file:str,schema:type)->str:
 return "\n\n".join([(ROOT/"agents/roles"/role_file).read_text(),(ROOT/"evals/prompt_baseline.txt").read_text(),(ROOT/"evals/rubric.md").read_text(),json.dumps(schema.model_json_schema())])

def _call(*,role_file:str,schema:type,user:str,trace:Path,ledger:UsageLedger,label:str,max_tokens:int=1400):
 client=anthropic.Anthropic(max_retries=2);stable=_stable(role_file,schema)
 trace.parent.mkdir(parents=True,exist_ok=True);trace.touch(exist_ok=True)
 message=client.messages.parse(model=MODEL,max_tokens=max_tokens,output_config={"effort":"low"},output_format=schema,
  system=[{"type":"text","text":stable,"cache_control":{"type":"ephemeral"}}],messages=[{"role":"user","content":user}])
 usage=_usage(message);ledger.add(usage,label=label,effort="low")
 if message.parsed_output is None:raise ValueError(f"{label} returned no structured artifact")
 with trace.open("a",encoding="utf-8") as handle:handle.write(json.dumps({"role":label,"user":user,"artifact":message.parsed_output.model_dump(),"usage":usage.__dict__})+"\n")
 return message.parsed_output

def run_item(
    item: dict,
    out_dir: Path,
    *,
    neutral_critic: bool = False,
    max_iterations: int = 3,
    force_iterations: bool = False,
) -> dict:
 out_dir.mkdir(parents=True,exist_ok=True);trace=out_dir/"transcript.jsonl";trace.touch(exist_ok=True)
 trace_id=str(trace.relative_to(ROOT));ledger=UsageLedger();records=[];best=None;gate_events=[];bound_events=[]
 role="critic_neutral.md" if neutral_critic else "critic.md";previous=None;critique=None
 for iteration in range(1,max_iterations+1):
  if iteration==1:
   user=f"IMMUTABLE TASK:\n{_task(item)}\nProduce the generator artifact. Use trace_id {trace_id}."
  else:
   user=f"IMMUTABLE TASK:\n{_task(item)}\nCURRENT ARTIFACT:\n{previous.model_dump_json()}\nCRITIC DEFECTS AND REJECTED ASSUMPTIONS:\n{critique.model_dump_json()}\nRevise only to address those issues. Use trace_id {trace_id}."
  generator=_call(role_file="generator.md",schema=GeneratorArtifact,user=user,trace=trace,ledger=ledger,label=f"generator-{iteration}")
  generator=generator.model_copy(update={"trace_id":trace_id});generator,bounds=bound_generator(generator);bound_events+=bounds
  errors=gate_generator(generator,item=item,root=ROOT);gate_events.append({"iteration":iteration,"handoff":"generator","errors":errors})
  if errors:
   retry=_call(role_file="generator.md",schema=GeneratorArtifact,user=user+f"\nGATE VIOLATIONS:\n{json.dumps(errors)}\nReturn one corrected artifact.",trace=trace,ledger=ledger,label=f"generator-gate-retry-{iteration}")
   generator=retry.model_copy(update={"trace_id":trace_id});generator,bounds=bound_generator(generator);bound_events+=bounds
   errors=gate_generator(generator,item=item,root=ROOT);gate_events.append({"iteration":iteration,"handoff":"generator-retry","errors":errors})
   if errors:raise ValueError(f"generator gate escalation: {errors}")
  critic_user=f"IMMUTABLE TASK:\n{_task(item)}\nIMMUTABLE RUBRIC:\n{(ROOT/'evals/rubric.md').read_text()}\nGENERATOR ARTIFACT ONLY:\n{generator.model_dump_json()}\nCheck every declared assumption and list rejected ones. Use trace_id {trace_id}."
  critique=_call(role_file=role,schema=CriticArtifact,user=critic_user,trace=trace,ledger=ledger,label=f"critic-{iteration}",max_tokens=1800)
  critique=critique.model_copy(update={"trace_id":trace_id});critique,bounds=bound_critic(critique);bound_events+=bounds
  errors=gate_critic(critique,item=item,root=ROOT);gate_events.append({"iteration":iteration,"handoff":"critic","errors":errors})
  if errors:
   retry=_call(role_file=role,schema=CriticArtifact,user=critic_user+f"\nGATE VIOLATIONS:\n{json.dumps(errors)}\nReturn one corrected artifact.",trace=trace,ledger=ledger,label=f"critic-gate-retry-{iteration}",max_tokens=1800)
   critique=retry.model_copy(update={"trace_id":trace_id});critique,bounds=bound_critic(critique);bound_events+=bounds
   errors=gate_critic(critique,item=item,root=ROOT);gate_events.append({"iteration":iteration,"handoff":"critic-retry","errors":errors})
   if errors:raise ValueError(f"critic gate escalation: {errors}")
  score=score_item(item["expected"],generator.output.model_dump_json())
  record={"iteration":iteration,"generator":generator.model_dump(),"critic":critique.model_dump(),"score":score}
  (out_dir/f"iter-{iteration}.json").write_text(json.dumps(record,indent=2)+"\n");records.append(record)
  if best is None or score["score"]>best["score"]["score"]:best=record
  previous=generator
  if critique.decision=="accept" and not force_iterations:break
 return {"id":item["id"],"mode":"neutral" if neutral_critic else "adversarial","selected_iteration":best["iteration"],
  "final_score":best["score"]["score"],"accepted_at_1":records[0]["critic"]["decision"]=="accept","iterations":len(records),
  "blocking_defects":sum(issue["severity"]=="blocking" for record in records for issue in record["critic"]["defects"]),
  "assumptions_declared":sum(len(record["generator"]["assumptions"]) for record in records),
  "assumptions_rejected":sum(len(record["critic"]["rejected_assumptions"]) for record in records),
  "gate_events":gate_events,"bound_events":bound_events,"records":records,"usage":ledger.summary()}
