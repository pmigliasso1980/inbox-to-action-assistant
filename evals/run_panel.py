"""Run the parallel panel and aggregate echo-chamber/formal-role metrics."""
from __future__ import annotations
import argparse,json,time
from pathlib import Path
from agents.panel import ROLES,run_panel_item

ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument("--limit",type=int,default=20);p.add_argument("--name",default="panel");a=p.parse_args()
 items=[json.loads(x) for x in (ROOT/"evals/dataset.jsonl").read_text().splitlines() if x][:a.limit];out=ROOT/"runs"/a.name;records=[];started=time.perf_counter()
 for i,item in enumerate(items,1):
  try:r=run_panel_item(item,out/item["id"]);error=None
  except Exception as exc:r={"id":item["id"],"full_score":0,"overlaps":{"correctness_security":0,"correctness_robustness":0,"security_robustness":0},"unique_contribution":{x:0 for x in ROLES},"triple_overlap":0,"ablations":{x:{"score_without":0,"delta_with_minus_without":0,"usage":{"cost_usd":0}} for x in ROLES},"generator_usage":{"input_tokens":0,"output_tokens":0,"cached_input_tokens":0,"cost_usd":0},"role_usage":{},"full_revision_usage":{"input_tokens":0,"output_tokens":0,"cached_input_tokens":0,"cost_usd":0},"parallel_latency":0,"estimated_sequential_latency":0};error=f"{type(exc).__name__}: {exc}"
  r["error"]=error;records.append(r);(out/item["id"]/"result.json").write_text(json.dumps(r,indent=2)+"\n")
  print(f"[{i}/{len(items)}] {item['id']} score={r['full_score']:.3f} cost=${r['generator_usage']['cost_usd']+sum(x['cost_usd'] for x in r['role_usage'].values())+r['full_revision_usage']['cost_usd']:.3f}",flush=True)
 def mean(path):return sum(r[path] for r in records)/len(records)
 role_unique={role:sum(r["unique_contribution"][role] for r in records)/len(records) for role in ROLES}
 role_cost={role:sum(r["role_usage"].get(role,{}).get("cost_usd",0)+r["ablations"][role]["usage"].get("cost_usd",0) for r in records) for role in ROLES}
 decisions={role:{"unique_defects":sum(sum(1 for entry in r.get("merged",{}).get("defects",[]) if entry["roles"]==[role]) for r in records),"score_with":sum(r["full_score"] for r in records)/len(records),"score_without":sum(r["ablations"][role]["score_without"] for r in records)/len(records),"delta":sum(r["ablations"][role]["delta_with_minus_without"] for r in records)/len(records),"added_cost":role_cost[role]} for role in ROLES}
 primary_cost=sum(r["generator_usage"]["cost_usd"]+sum(x["cost_usd"] for x in r["role_usage"].values())+r["full_revision_usage"]["cost_usd"] for r in records)
 ablation_cost=sum(sum(r["ablations"][role]["usage"].get("cost_usd",0) for role in ROLES) for r in records)
 summary={"items":len(records),"mean_score":sum(r["full_score"] for r in records)/len(records),"thresholds":json.loads((ROOT/"evals/panel_distinctness.json").read_text())["thresholds_declared_before_runs"],
  "mean_pairwise_jaccard":{key:sum(r["overlaps"][key] for r in records)/len(records) for key in records[0]["overlaps"]},"unique_contribution":role_unique,
  "triple_overlap":sum(r["triple_overlap"] for r in records),"role_decisions":decisions,"mean_parallel_latency":sum(r["parallel_latency"] for r in records)/len(records),
  "estimated_sequential_latency":sum(r["estimated_sequential_latency"] for r in records)/len(records),"input_tokens":sum(r["generator_usage"]["input_tokens"]+sum(x["input_tokens"] for x in r["role_usage"].values())+r["full_revision_usage"]["input_tokens"] for r in records),
  "output_tokens":sum(r["generator_usage"]["output_tokens"]+sum(x["output_tokens"] for x in r["role_usage"].values())+r["full_revision_usage"]["output_tokens"] for r in records),
  "cached_tokens":sum(r["generator_usage"]["cached_input_tokens"]+sum(x["cached_input_tokens"] for x in r["role_usage"].values())+r["full_revision_usage"]["cached_input_tokens"] for r in records),
  "cost_usd":primary_cost,"ablation_cost_usd":ablation_cost,"total_experiment_cost_usd":primary_cost+ablation_cost,"wall_clock_seconds":time.perf_counter()-started,"records":records}
 (out/"summary.json").write_text(json.dumps(summary,indent=2)+"\n");print(json.dumps({k:v for k,v in summary.items() if k!="records"},indent=2))
if __name__=="__main__":main()
