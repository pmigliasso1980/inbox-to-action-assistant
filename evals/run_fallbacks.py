"""Run the 6x2 fallback matrix on the fixed ten-item subset."""
from __future__ import annotations
import argparse,json,time
from pathlib import Path
from agents.tool_agent import ToolAgent
from agents.review_tools import ToolOutcome, ToolError, confirm_result, execute_confirmed
from agents.tool_controls import explicit_test_with_fallback, injected_run_tests
from evals.run_tools import review_json
from evals.score import score_item

ROOT=Path(__file__).resolve().parents[1]
MODES=["none","rate_limit","timeout","auth","empty","garbage"]

def executor(mode,policy):
 def run(name,args):
  if name!="run_tests": return execute_confirmed(name,args)
  started=time.perf_counter()
  if policy=="explicit":
   value=explicit_test_with_fallback(mode=mode,**args)
   return ToolOutcome(value,bool(value["grounded"]),"explicit retry/fallback policy completed",(time.perf_counter()-started)*1000)
  value=injected_run_tests(mode=mode,**args)
  ok,verdict=confirm_result(name,value)
  return ToolOutcome(value,ok,verdict,(time.perf_counter()-started)*1000)
 return run

def main():
 p=argparse.ArgumentParser();p.add_argument("--limit",type=int,default=10);a=p.parse_args()
 items=[json.loads(x) for x in (ROOT/"evals/dataset.jsonl").read_text().splitlines() if x][:a.limit]
 root=ROOT/"runs/fallbacks";root.mkdir(parents=True,exist_ok=True);all_summaries=[]; total_cost=0
 for mode in MODES:
  for policy in ["implicit","explicit"]:
   config=f"{policy}-{mode}";out=root/config;out.mkdir(parents=True,exist_ok=True);records=[]
   for index,item in enumerate(items,1):
    prompt=f"""Review {item['file']} for concrete defects. You MUST call run_tests with suite static_smoke first.
If that fails or is rejected, recover using another available read-only tool. Never answer confidently without successful grounding.
Return JSON only: {{"defects":[{{"category":"defect_category","line":1,"explanation":"evidence"}}]}}.
The file is in the frozen benchmark; use tools to inspect it."""
    agent=ToolAgent(max_steps=8,trace_path=out/item["id"]/"trace.jsonl",executor=executor(mode,policy))
    error=None; completed=True
    try:
     result=agent.run(prompt,system=f"Fallback policy is {policy}. Primary failure mode is {mode}.")
     raw=review_json(result["text"]);score=score_item(item["expected"],raw)["score"]
    except Exception as exc:
     completed=False;error=f"{type(exc).__name__}: {exc}";score=0
     result={"text":"","steps":0,"cap_hit":False,"tool_calls":[],"usage":{"calls":0,"input_tokens":0,"output_tokens":0,"cached_input_tokens":0,"cache_write_tokens":0,"cost_usd":0}}
    calls=result["tool_calls"]
    fallback=any(c["name"]=="run_linter" or '"used_fallback": true' in c.get("result_summary","") for c in calls)
    grounded=any(c.get("confirmed") for c in calls)
    rec={"id":item["id"],"completed":completed,"fallback_invoked":fallback,"ungrounded_answer":completed and not grounded,
         "score":score,"error":error,**result};records.append(rec);total_cost+=result["usage"]["cost_usd"]
    d=out/item["id"];d.mkdir(parents=True,exist_ok=True);(d/"result.json").write_text(json.dumps(rec,indent=2)+"\n")
    print(f"[{config} {index}/{len(items)}] done={completed} fallback={fallback} grounded={grounded} score={score:.3f} total=${total_cost:.3f}",flush=True)
    if total_cost>7.25: raise RuntimeError("stopping before authorized total budget is exceeded")
   completed=[r for r in records if r["completed"]]
   summary={"configuration":config,"failure_mode":mode,"policy":policy,"items":len(records),
    "task_completion_rate":len(completed)/len(records),"fallback_invocation_rate":sum(r["fallback_invoked"] for r in records)/len(records),
    "ungrounded_answer_rate":sum(r["ungrounded_answer"] for r in records)/len(records),
    "mean_tool_calls":sum(len(r["tool_calls"]) for r in records)/len(records),
    "score_on_completed":sum(r["score"] for r in completed)/len(completed) if completed else None,
    "cost_usd":sum(r["usage"]["cost_usd"] for r in records),"records":records}
   (out/"summary.json").write_text(json.dumps(summary,indent=2)+"\n");all_summaries.append(summary)
 matrix={"subset_size":a.limit,"total_cost_usd":total_cost,"configurations":[{k:v for k,v in s.items() if k!="records"} for s in all_summaries]}
 (root/"summary.json").write_text(json.dumps(matrix,indent=2)+"\n");print(json.dumps(matrix,indent=2))
if __name__=="__main__":main()
