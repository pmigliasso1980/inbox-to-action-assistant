"""Run reflection or an injected failure configuration over a fixed item set."""
from __future__ import annotations
import argparse,json,time
from pathlib import Path
from agents.reflection import run_item

ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument("--name",default="reflection");p.add_argument("--mode",default="control");p.add_argument("--limit",type=int,default=20);p.add_argument("--max-iterations",type=int,default=3);p.add_argument("--return-last",action="store_true");a=p.parse_args()
 items=[json.loads(x) for x in (ROOT/"evals/dataset.jsonl").read_text().splitlines() if x][:a.limit]
 out=ROOT/"runs"/a.name; out.mkdir(parents=True,exist_ok=True); started=time.perf_counter(); results=[]
 for i,item in enumerate(items,1):
  r=run_item(item,out/item["id"],max_iterations=a.max_iterations,mode=a.mode,return_last=a.return_last);results.append(r);print(f"[{i}/{len(items)}] {item['id']} score={r['final_score']:.3f} iters={r['iterations']} stop={r['termination']}")
 base=json.loads((ROOT/"runs/baseline/run-1/summary.json").read_text()); scores=[r["final_score"] for r in results]; calls=sum(r["usage"]["calls"] for r in results)
 reasons={k:sum(r["termination"]==k for r in results) for k in ["satisfactory","cap"]}; sat1=sum(r["termination"]=="satisfactory" and r["iterations"]==1 for r in results)/len(results)
 allrecs=[x for r in results for x in r["records"]]; nonmono=sum(any(rec["score"]["score"]<max(x["score"]["score"] for x in r["records"]) for rec in r["records"][-1:]) for r in results)/len(results)
 summary={"name":a.name,"mode":a.mode,"items":len(items),"mean_score":sum(scores)/len(scores),"delta_vs_baseline_run1":sum(scores)/len(scores)-base["mean_score"],"noise_floor":0.06666666666666676,"per_item_scores":{r["id"]:r["final_score"] for r in results},"stopping_reasons":reasons,"satisfaction_at_1_rate":sat1,"mean_iterations":sum(r["iterations"] for r in results)/len(results),"gate_failure_fraction":sum(bool(x["gate"]) for x in allrecs)/len(allrecs),"non_monotonic_rate":nonmono,"input_tokens":sum(r["usage"]["input_tokens"] for r in results),"output_tokens":sum(r["usage"]["output_tokens"] for r in results),"cached_tokens":sum(r["usage"]["cached_input_tokens"] for r in results),"cost_usd":sum(r["usage"]["cost_usd"] for r in results),"calls":calls,"wall_clock_seconds":time.perf_counter()-started,"results":results}
 delta=summary["delta_vs_baseline_run1"];summary["cost_per_score_point"]=summary["cost_usd"]/(delta*100) if delta>0 else None
 (out/"summary.json").write_text(json.dumps(summary,indent=2)+"\n");print(json.dumps({k:v for k,v in summary.items() if k!="results"},indent=2))
if __name__=="__main__":main()
