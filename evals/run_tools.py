"""Evaluate tools-in-evaluation ordering against frozen baseline drafts."""
from __future__ import annotations
import argparse, json, time
from pathlib import Path
from agents.tool_agent import ToolAgent
from evals.score import score_item

ROOT=Path(__file__).resolve().parents[1]

def review_json(text:str)->str:
    text=text.strip()
    if "```" in text:
        parts=text.split("```")
        text=next((p.removeprefix("json").strip() for p in parts if "defects" in p),text)
    start=text.find("{"); end=text.rfind("}")
    if start<0 or end<start: raise ValueError("final answer contained no JSON object")
    value=json.loads(text[start:end+1])
    return json.dumps(value)

def main():
    p=argparse.ArgumentParser();p.add_argument("--limit",type=int,default=20);p.add_argument("--name",default="tools");a=p.parse_args()
    items=[json.loads(x) for x in (ROOT/"evals/dataset.jsonl").read_text().splitlines() if x][:a.limit]
    out=ROOT/"runs"/a.name;out.mkdir(parents=True,exist_ok=True);results=[];started=time.perf_counter()
    rubric=(ROOT/"evals/rubric.md").read_text(); prompt=(ROOT/"evals/prompt_baseline.txt").read_text()
    for n,item in enumerate(items,1):
        baseline=json.dumps(json.loads((ROOT/"runs/baseline/run-1"/f"{item['id']}.json").read_text())["output"])
        task=f"""You are the evidence-backed evaluator in a code-review evaluator-optimizer loop.
Verify the current draft using the available read-only tools. Call tools whenever they can ground a claim.
Then return a corrected final review as JSON only, matching this shape:
{{"defects":[{{"category":"one_allowed_category","line":1,"explanation":"concise evidence"}}]}}
Use at most 5 defects. Do not mention tool mechanics in the final JSON.

RUBRIC:\n{rubric}\n\nORIGINAL TASK:\n{prompt}\nFile: {item['file']}\n\nCURRENT DRAFT:\n{baseline}"""
        agent=ToolAgent(max_steps=8,trace_path=out/item["id"]/"trace.jsonl")
        before=time.perf_counter(); error=None
        try:
            run=agent.run(task,system="Apply the immutable rubric strictly. Ground claims with tools; never invent tool evidence.")
            raw=review_json(run["text"]); scored=score_item(item["expected"],raw)
        except Exception as exc:
            error=f"{type(exc).__name__}: {exc}"; raw=baseline; scored=score_item(item["expected"],raw)
            run={"text":"","steps":0,"cap_hit":False,"tool_calls":[],"usage":{"calls":0,"input_tokens":0,"output_tokens":0,"cached_input_tokens":0,"cache_write_tokens":0,"cost_usd":0}}
        rec={"id":item["id"],"file":item["file"],"draft":json.loads(baseline),"final":json.loads(raw),"score":scored,
             "error":error,"latency_seconds":time.perf_counter()-before,**run}
        d=out/item["id"];d.mkdir(parents=True,exist_ok=True);(d/"result.json").write_text(json.dumps(rec,indent=2)+"\n");results.append(rec)
        print(f"[{n}/{len(items)}] {item['id']} score={scored['score']:.3f} tools={len(run['tool_calls'])} cost=${run['usage']['cost_usd']:.4f}",flush=True)
    base=json.loads((ROOT/"runs/baseline/run-1/summary.json").read_text()); refl=json.loads((ROOT/"runs/reflection/summary.json").read_text())
    calls=[c for r in results for c in r["tool_calls"]]; names={name:sum(c["name"]==name for c in calls) for name in {c["name"] for c in calls}}
    scores=[r["score"]["score"] for r in results]; cost=sum(r["usage"]["cost_usd"] for r in results); mean=sum(scores)/len(scores)
    summary={"items":len(results),"ordering":"tools_in_evaluation","mean_score":mean,"baseline_mean":base["mean_score"],
      "reflection_mean":refl["mean_score"],"delta_vs_baseline":mean-base["mean_score"],"delta_vs_reflection":mean-refl["mean_score"],
      "noise_floor":0.06666666666666676,"mean_tool_calls":len(calls)/len(results),"tool_call_distribution":names,
      "tool_error_rate_by_tool":{name:sum(c["name"]==name and not c["confirmed"] for c in calls)/max(1,names[name]) for name in names},
      "confirmation_rejection_rate":sum(not c["confirmed"] for c in calls)/max(1,len(calls)),"max_steps_fraction":sum(r["cap_hit"] for r in results)/len(results),
      "input_tokens":sum(r["usage"]["input_tokens"] for r in results),"output_tokens":sum(r["usage"]["output_tokens"] for r in results),
      "cached_tokens":sum(r["usage"]["cached_input_tokens"] for r in results),"cost_usd":cost,"mean_latency_seconds":sum(r["latency_seconds"] for r in results)/len(results),
      "cost_per_score_point":cost/((mean-base["mean_score"])*100) if mean>base["mean_score"] else None,"reflection_cost_per_score_point":refl.get("cost_per_score_point"),
      "wall_clock_seconds":time.perf_counter()-started,"results":results}
    (out/"summary.json").write_text(json.dumps(summary,indent=2)+"\n");print(json.dumps({k:v for k,v in summary.items() if k!="results"},indent=2))
if __name__=="__main__":main()
