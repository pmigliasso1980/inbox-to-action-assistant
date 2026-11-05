"""Consolidate the valid Module 4 controlled experiments without API calls."""
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def load_summary(name):return json.loads((ROOT/"runs/replanning"/name/"summary.json").read_text())
def load_rows(names):
 rows=[]
 for name in names:
  rows.extend(json.loads(p.read_text()) for p in (ROOT/"runs/replanning"/name).glob("item-*/result.json"))
 return rows
def compact(rows):
 return {"items":len(rows),"mean_score":sum(r["score"] for r in rows)/len(rows),
  "total_cost":sum(r["usage"]["cost_usd"] for r in rows),
  "total_tokens":sum(r["usage"]["input_tokens"]+r["usage"]["output_tokens"] for r in rows),
  "mean_steps":sum(r["steps_executed"] for r in rows)/len(rows),
  "duplicated_steps":sum(r["duplicated_steps"] for r in rows),
  "side_effect_count":sum(r["side_effect_count"] for r in rows),
  "escalation_rate":sum(r["escalated"] for r in rows)/len(rows),
  "items_exceeding_bound":sum(r["steps_executed"]>10 for r in rows)}

def main():
 naive=load_rows(["controlled-naive"]);preserving=load_rows(["controlled-preserving"])
 thresholds={}
 for threshold,names in {
  1:["controlled-threshold-1-persistent","controlled-threshold-1-transient"],
  2:["controlled-threshold-2-persistent","controlled-threshold-2-transient"],
  3:["controlled-threshold-3-persistent","controlled-threshold-3-transient"],
  5:["controlled-threshold-5-persistent-v2","controlled-threshold-5-transient-v2"],
 }.items():
  rows=load_rows(names);entry=compact(rows)
  entry["resolved_after_failure_count"]={str(n):sum((r.get("strikes",{}).get("read_code")==n and not r["escalated"]) for r in rows) for n in range(1,6)}
  thresholds[str(threshold)]=entry
 escalation=load_rows(["controlled-threshold-1-persistent","controlled-threshold-1-transient"])
 assessment=[]
 for row in escalation:
  output=row.get("escalation_output") or {};blocked=output.get("blocked_by") or []
  assessment.append({"id":row["id"],"states_missing_work":bool(output.get("failed") or blocked),
   "avoids_hidden_dependency":bool(blocked),
   "human_next_step_is_visible":bool(blocked),"escalation_output":output})
 result={"part1":{"naive":compact(naive),"preserving":compact(preserving)},"part2":{"thresholds":thresholds},
  "part3":{"assessed_items":assessment,"explicit_gap_rate":sum(x["states_missing_work"] for x in assessment)/len(assessment),
   "avoids_hidden_dependency_rate":sum(x["avoids_hidden_dependency"] for x in assessment)/len(assessment),
   "human_next_step_visible_rate":sum(x["human_next_step_is_visible"] for x in assessment)/len(assessment)}}
 (ROOT/"runs/replanning/summary.json").write_text(json.dumps(result,indent=2)+"\n")
 print(json.dumps(result,indent=2))
if __name__=="__main__":main()
