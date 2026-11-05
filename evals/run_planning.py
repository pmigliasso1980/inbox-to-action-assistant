"""Measure the validated planning pipeline on the frozen evaluation set."""
from __future__ import annotations
import argparse,json,math,time
from collections import Counter
from pathlib import Path
from agents.planner import PlanningAgent
from evals.score import score_item

ROOT=Path(__file__).resolve().parents[1]

def percentile(values,p):
 values=sorted(values);return values[min(len(values)-1,max(0,math.ceil(p*len(values))-1))]

def main():
 p=argparse.ArgumentParser();p.add_argument("--name",default="planning");p.add_argument("--limit",type=int,default=20)
 p.add_argument("--no-cache",action="store_true");p.add_argument("--candidate-only",action="store_true");a=p.parse_args()
 candidates=set(json.loads((ROOT/"evals/planning_candidates.json").read_text())["candidate_ids"])
 items=[json.loads(x) for x in (ROOT/"evals/dataset.jsonl").read_text().splitlines() if x]
 if a.candidate_only:items=[x for x in items if x["id"] in candidates]
 items=items[:a.limit];out=ROOT/"runs"/a.name;out.mkdir(parents=True,exist_ok=True);records=[];started=time.perf_counter()
 for index,item in enumerate(items,1):
  agent=PlanningAgent(caching=not a.no_cache,trace_path=out/item["id"]/"trace.jsonl")
  try:r=agent.run(item=item);error=None
  except Exception as exc:r={"id":item["id"],"review":{"defects":[]},"usage":{"calls":0,"input_tokens":0,"output_tokens":0,"cached_input_tokens":0,"cache_write_tokens":0,"cost_usd":0},"latency_seconds":0,"first_plan_valid":False,"validation_log":[],"steps_executed":0,"step_artifacts":[],"step_successes":0,"criterion_caught_failures":0,"replans":0,"escalated":False,"abandoned":True};error=f"{type(exc).__name__}: {exc}"
  r["error"]=error;r["candidate"]=item["id"] in candidates;r["score"]=score_item(item["expected"],json.dumps(r["review"]));records.append(r)
  d=out/item["id"];d.mkdir(parents=True,exist_ok=True);(d/"result.json").write_text(json.dumps(r,indent=2)+"\n")
  print(f"[{index}/{len(items)}] {item['id']} score={r['score']['score']:.3f} steps={r['steps_executed']} replans={r['replans']} cost=${r['usage']['cost_usd']:.3f}",flush=True)
 violations=Counter(v.split(":",1)[0] for r in records for attempt in r.get("validation_log",[]) for v in attempt)
 scores=[r["score"]["score"] for r in records];cand=[r for r in records if r["candidate"]]
 baseline=json.loads((ROOT/"runs/baseline/run-1/summary.json").read_text());reflection=json.loads((ROOT/"runs/reflection/summary.json").read_text());tools=json.loads((ROOT/"runs/tools/summary.json").read_text())
 cost=sum(r["usage"]["cost_usd"] for r in records);mean=sum(scores)/len(scores);success=sum(r["step_successes"] for r in records);steps=sum(r["steps_executed"] for r in records)
 summary={"name":a.name,"items":len(records),"candidate_ids":sorted(candidates),"candidate_items_run":len(cand),"mean_score":mean,
  "candidate_mean_score":sum(r["score"]["score"] for r in cand)/len(cand) if cand else None,"delta_vs_baseline":mean-baseline["mean_score"],
  "delta_vs_reflection":mean-reflection["mean_score"],"delta_vs_tools":mean-tools["mean_score"],"noise_floor":0.06666666666666676,
  "first_attempt_plan_validity_rate":sum(r["first_plan_valid"] for r in records)/len(records),"validation_violations":dict(violations),
  "mean_steps":steps/len(records),"step_count_distribution":dict(Counter(r["steps_executed"] for r in records)),"step_success_rate":success/max(1,steps),
  "criterion_caught_failures":sum(r["criterion_caught_failures"] for r in records),"replan_rate":sum(r["replans"]>0 for r in records)/len(records),
  "escalation_rate":sum(r["escalated"] for r in records)/len(records),"abandoned_items":[r["id"] for r in records if r["abandoned"]],
  "input_tokens":sum(r["usage"]["input_tokens"] for r in records),"output_tokens":sum(r["usage"]["output_tokens"] for r in records),
  "cached_tokens":sum(r["usage"]["cached_input_tokens"] for r in records),"cache_write_tokens":sum(r["usage"]["cache_write_tokens"] for r in records),
  "cost_usd":cost,"cost_multiple_vs_baseline":cost/baseline["cost_usd"],"cost_per_score_point":cost/((mean-baseline["mean_score"])*100) if mean>baseline["mean_score"] else None,
  "mean_latency_seconds":sum(r["latency_seconds"] for r in records)/len(records),"p95_latency_seconds":percentile([r["latency_seconds"] for r in records],.95),
  "wall_clock_seconds":time.perf_counter()-started,"records":records}
 (out/"summary.json").write_text(json.dumps(summary,indent=2)+"\n");print(json.dumps({k:v for k,v in summary.items() if k!="records"},indent=2))
if __name__=="__main__":main()
