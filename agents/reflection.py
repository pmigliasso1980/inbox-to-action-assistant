"""Production-shaped generate → gate → critique → revise reflection loop."""
from __future__ import annotations
import json, time
from dataclasses import asdict
from pathlib import Path
from typing import Literal
from pydantic import BaseModel
from agents.gates import check
from agents.llm import UsageLedger, call_json
from evals.run_baseline import Defect, Review
from evals.score import score_item

ROOT=Path(__file__).resolve().parents[1]
CRITERIA={"valid_json","required_fields","line_numbers_valid","no_duplicate_findings","finding_limit","concrete_defect","evidence_alignment","coverage","precision"}

class Issue(BaseModel):
    location:str; observation:str; rubric_criterion:str
    severity:Literal["blocking","major","minor"]
class Critique(BaseModel):
    satisfactory:bool; issues:list[Issue]; revision_instructions:list[str]

def _task(item):
    prompt=(ROOT/"evals/prompt_baseline.txt").read_text()
    return f"{prompt}\n\nFile: {item['file']}\n```python\n{item['input']}\n```"

def run_item(item:dict,out_dir:Path,*,max_iterations=3,mode="control",return_last=False):
    task=_task(item); rubric=(ROOT/"evals/rubric.md").read_text(); ledger=UsageLedger(); records=[]; best=None
    draft_obj,u=call_json(task,Review,max_tokens=700,effort="low"); ledger.add(u,label="generate",effort="low")
    draft=draft_obj.model_dump_json(); mechanical_retries=0
    for iteration in range(1,max_iterations+1):
        gate=check(item["input"],draft)
        while gate and mechanical_retries<2:
            mechanical_retries+=1
            repair=f"{task}\n\nPrevious output failed mechanical checks: {gate}. Return a corrected review only."
            draft_obj,u=call_json(repair,Review,max_tokens=700,effort="low"); ledger.add(u,label="mechanical-retry",effort="low"); draft=draft_obj.model_dump_json(); gate=check(item["input"],draft)
        critic_rubric=rubric
        critic_task=task
        framing="You did not write this output. Apply the rubric strictly."
        if mode=="self-confirm": critic_task="The task is to provide a helpful professional code review of the draft's own concerns."; framing="Respect the draft author's framing and evaluate whether it accomplished its stated goals."
        if mode=="drift": critic_rubric="Evaluate whether this output is clear, well-organized, and professionally written. Report any issues."
        cp=f"{framing}\n\nIMMUTABLE TASK:\n{critic_task}\n\nIMMUTABLE RUBRIC:\n{critic_rubric}\n\nCURRENT DRAFT:\n{draft}"
        critique,u=call_json(cp,Critique,max_tokens=1600,effort="low"); ledger.add(u,label="critique",effort="low")
        invalid=[x.rubric_criterion for x in critique.issues if x.rubric_criterion not in CRITERIA]
        if any(x.severity=="blocking" for x in critique.issues): critique.satisfactory=False
        scored=score_item(item["expected"],draft); rec={"iteration":iteration,"draft":json.loads(draft),"gate":gate,"critique":critique.model_dump(),"invalid_criteria":invalid,"score":scored,"usage_so_far":ledger.summary()}
        if best is None or scored["score"]>best["score"]["score"]: best=rec
        if mode=="nonmono":
            stop="cap" if iteration==max_iterations else "revise"
        else:
            stop="satisfactory" if critique.satisfactory and not gate else ("cap" if iteration==max_iterations else "revise")
        rec["stopping_decision"]=stop; records.append(rec); out_dir.mkdir(parents=True,exist_ok=True); (out_dir/f"iter-{iteration}.json").write_text(json.dumps(rec,indent=2)+"\n")
        if stop!="revise": break
        change_guard="" if mode=="nonmono" else "Fix only the listed issues; change nothing else."
        rp=f"{task}\n\nCURRENT DRAFT:\n{draft}\n\nCRITIQUE:\n{critique.model_dump_json()}\n\n{change_guard} Return the revised review."
        draft_obj,u=call_json(rp,Review,max_tokens=700,effort="low"); ledger.add(u,label="revise",effort="low"); draft=draft_obj.model_dump_json()
    selected=records[-1] if return_last else best
    return {"id":item["id"],"selected_iteration":selected["iteration"],"final_score":selected["score"]["score"],"termination":records[-1]["stopping_decision"],"iterations":len(records),"mechanical_retries":mechanical_retries,"records":records,"usage":ledger.summary()}
