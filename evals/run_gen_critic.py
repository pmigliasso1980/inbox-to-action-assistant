"""Run adversarial or neutral generator–critic evaluation."""
from __future__ import annotations
import argparse,json,time
from pathlib import Path
from agents.gen_critic import run_item

ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument("--name",default="gen-critic");p.add_argument("--neutral",action="store_true");p.add_argument("--limit",type=int,default=20);p.add_argument("--max-iterations",type=int,default=3);p.add_argument("--force-iterations",action="store_true");a=p.parse_args()
 items=[json.loads(x) for x in (ROOT/"evals/dataset.jsonl").read_text().splitlines() if x][:a.limit];out=ROOT/"runs"/a.name;results=[];started=time.perf_counter()
 for i,item in enumerate(items,1):
  try:r=run_item(item,out/item["id"],neutral_critic=a.neutral,max_iterations=a.max_iterations,force_iterations=a.force_iterations);error=None
  except Exception as exc:r={"id":item["id"],"final_score":0,"accepted_at_1":False,"iterations":0,"blocking_defects":0,"assumptions_declared":0,"assumptions_rejected":0,"gate_events":[],"bound_events":[],"records":[],"usage":{"calls":0,"input_tokens":0,"output_tokens":0,"cached_input_tokens":0,"cache_write_tokens":0,"cost_usd":0}};error=f"{type(exc).__name__}: {exc}"
  r["error"]=error;results.append(r);(out/item["id"]/"result.json").write_text(json.dumps(r,indent=2)+"\n")
  print(f"[{i}/{len(items)}] {item['id']} score={r['final_score']:.3f} iters={r['iterations']} cost=${r['usage']['cost_usd']:.3f}",flush=True)
 reflection=json.loads((ROOT/"runs/reflection/summary.json").read_text());base=json.loads((ROOT/"runs/baseline/run-1/summary.json").read_text());events=[e for r in results for e in r["gate_events"]]
 mean=sum(r["final_score"] for r in results)/len(results)
 summary={"name":a.name,"mode":"neutral" if a.neutral else "adversarial","items":len(results),"max_iterations":a.max_iterations,"force_iterations":a.force_iterations,"mean_score":mean,"delta_vs_baseline":mean-base["mean_score"],"noise_floor":0.06666666666666676,
  "reflection_mean_score":reflection["mean_score"],"reflection_accept_at_1":reflection["satisfaction_at_1_rate"],"reflection_mean_iterations":reflection["mean_iterations"],
  "accept_at_1_rate":sum(r["accepted_at_1"] for r in results)/len(results),"mean_iterations":sum(r["iterations"] for r in results)/len(results),
  "blocking_defects_per_item":sum(r["blocking_defects"] for r in results)/len(results),"assumptions_per_item":sum(r["assumptions_declared"] for r in results)/len(results),
  "assumptions_rejected":sum(r["assumptions_rejected"] for r in results),"gate_failure_rate":sum(bool(e["errors"]) for e in events)/max(1,len(events)),
  "bound_events":sum(len(r["bound_events"]) for r in results),"input_tokens":sum(r["usage"]["input_tokens"] for r in results),"output_tokens":sum(r["usage"]["output_tokens"] for r in results),
  "cached_tokens":sum(r["usage"]["cached_input_tokens"] for r in results),"cost_usd":sum(r["usage"]["cost_usd"] for r in results),"wall_clock_seconds":time.perf_counter()-started,"results":results}
 (out/"summary.json").write_text(json.dumps(summary,indent=2)+"\n");print(json.dumps({k:v for k,v in summary.items() if k!="results"},indent=2))
if __name__=="__main__":main()
