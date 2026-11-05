"""Controlled preserving/naive and escalation-threshold experiments."""
from __future__ import annotations
import argparse,json
from collections import Counter
from pathlib import Path
from agents.planner import PlanningAgent
from evals.score import score_item

ROOT=Path(__file__).resolve().parents[1]

def execute(items,name,**config):
 out=ROOT/"runs/replanning"/name;out.mkdir(parents=True,exist_ok=True);records=[]
 for i,item in enumerate(items,1):
  agent=PlanningAgent(trace_path=out/item["id"]/"trace.jsonl",**config)
  try:r=agent.run(item=item);error=None
  except Exception as exc:r={"id":item["id"],"review":{"defects":[]},"usage":{"calls":0,"input_tokens":0,"output_tokens":0,"cached_input_tokens":0,"cache_write_tokens":0,"cost_usd":0},"latency_seconds":0,"steps_executed":0,"step_artifacts":[],"side_effect_count":0,"escalated":True,"escalation_output":None};error=f"{type(exc).__name__}: {exc}"
  r["error"]=error;r["score"]=score_item(item["expected"],json.dumps(r["review"]))["score"]
  signatures=[(a["produced"],json.dumps(a.get("value"),sort_keys=True)) for a in r["step_artifacts"] if a["status"]=="success"]
  r["duplicated_steps"]=len(signatures)-len(set(signatures));records.append(r)
  d=out/item["id"];d.mkdir(parents=True,exist_ok=True);(d/"result.json").write_text(json.dumps(r,indent=2)+"\n")
  print(f"[{name} {i}/{len(items)}] score={r['score']:.3f} steps={r['steps_executed']} dup={r['duplicated_steps']} cost=${r['usage']['cost_usd']:.3f}",flush=True)
 summary={"name":name,"items":len(records),"mean_score":sum(r["score"] for r in records)/len(records),
  "total_tokens":sum(r["usage"]["input_tokens"]+r["usage"]["output_tokens"] for r in records),"total_cost":sum(r["usage"]["cost_usd"] for r in records),
  "mean_steps":sum(r["steps_executed"] for r in records)/len(records),"duplicated_steps":sum(r["duplicated_steps"] for r in records),
  "side_effect_count":sum(r["side_effect_count"] for r in records),"mean_latency":sum(r["latency_seconds"] for r in records)/len(records),
  "items_exceeding_bound":sum(r["steps_executed"]>10 for r in records),"escalation_rate":sum(r["escalated"] for r in records)/len(records),"records":records}
 (out/"summary.json").write_text(json.dumps(summary,indent=2)+"\n");return summary

def main():
 p=argparse.ArgumentParser();p.add_argument("--phase",choices=["variants","preserving","thresholds","threshold5","all"],default="all");a=p.parse_args()
 ids=set(json.loads((ROOT/"evals/planning_candidates.json").read_text())["candidate_ids"]);items=[json.loads(x) for x in (ROOT/"evals/dataset.jsonl").read_text().splitlines() if x and json.loads(x)["id"] in ids]
 summaries=[]
 if a.phase in {"variants","all"}:
  summaries += [execute(items,"controlled-naive",preserve_results=False,failure_once_tool="read_code"),execute(items,"controlled-preserving",preserve_results=True,failure_once_tool="read_code")]
 if a.phase == "preserving":
  summaries.append(execute(items,"controlled-preserving",preserve_results=True,failure_once_tool="read_code"))
 if a.phase in {"thresholds","threshold5","all"}:
  threshold_values=[5] if a.phase=="threshold5" else [1,2,3,5]
  for threshold in threshold_values:
   # Persistent failure on the first three candidates; transient first failure on the rest.
   persistent=items[:3];transient=items[3:];parts=[]
   suffix="-v2" if a.phase=="threshold5" else ""
   if persistent:parts.append(execute(persistent,f"controlled-threshold-{threshold}-persistent{suffix}",strike_limit=threshold,max_replans=threshold,persistent_failure_tool="read_code"))
   if transient:parts.append(execute(transient,f"controlled-threshold-{threshold}-transient{suffix}",strike_limit=threshold,max_replans=threshold,failure_once_tool="read_code"))
   summaries.extend(parts)
 compact=[{k:v for k,v in s.items() if k!="records"} for s in summaries];(ROOT/"runs/replanning/summary.json").write_text(json.dumps(compact,indent=2)+"\n");print(json.dumps(compact,indent=2))
if __name__=="__main__":main()
