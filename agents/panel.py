"""Parallel three-rubric panel with deterministic merge and role ablation."""
from __future__ import annotations

import json,re,time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from agents.gen_critic import ROOT,_call,_task
from agents.gates_multiagent import GeneratorArtifact,PanelCriticArtifact,bound_critic,bound_generator,gate_critic,gate_generator
from agents.llm import UsageLedger
from evals.score import score_item

ROLES=("correctness","security","robustness")

def normalize_issue(issue:dict)->tuple[str,str,str]:
 def norm(value):return re.sub(r"[^a-z0-9]+"," ",str(value).lower()).strip()
 location=re.sub(r"^line\s+","",norm(issue["location"]))
 return location,norm(issue["rubric_criterion"]),norm(issue["observation"])

def deterministic_merge(artifacts:dict[str,PanelCriticArtifact])->dict[str,Any]:
 merged={}
 for role,artifact in artifacts.items():
  for issue in artifact.defects:
   data=issue.model_dump();key=normalize_issue(data)
   if key not in merged:merged[key]={"issue":data,"roles":[role]}
   elif role not in merged[key]["roles"]:merged[key]["roles"].append(role)
 if any(a.decision=="reject" for a in artifacts.values()):decision="reject"
 elif any(entry["issue"]["severity"]=="blocking" for entry in merged.values()):decision="revise"
 else:decision="accept"
 return {"decision":decision,"defects":list(merged.values())}

def jaccard(a:set,b:set)->float:
 return len(a&b)/len(a|b) if a|b else 1.0

def run_panel_item(item:dict,out_dir:Path)->dict[str,Any]:
 out_dir.mkdir(parents=True,exist_ok=True);trace=out_dir/"transcript.jsonl";trace.touch(exist_ok=True);trace_id=str(trace.relative_to(ROOT))
 generator_ledger=UsageLedger();generator=_call(role_file="generator.md",schema=GeneratorArtifact,user=f"IMMUTABLE TASK:\n{_task(item)}\nUse trace_id {trace_id}.",trace=trace,ledger=generator_ledger,label="panel-generator")
 generator=generator.model_copy(update={"trace_id":trace_id});generator,bounds=bound_generator(generator);gen_gate=gate_generator(generator,item=item,root=ROOT)
 if gen_gate:raise ValueError(f"panel generator gate: {gen_gate}")
 def review(role):
  ledger=UsageLedger();started=time.perf_counter();rubric=(ROOT/"evals/rubrics"/f"{role}.md").read_text()
  user=f"IMMUTABLE TASK:\n{_task(item)}\nROLE RUBRIC:\n{rubric}\nGENERATOR ARTIFACT ONLY:\n{generator.model_dump_json()}\nUse reviewer_role {role} and trace_id {trace_id}."
  artifact=_call(role_file=f"{role}.md",schema=PanelCriticArtifact,user=user,trace=trace,ledger=ledger,label=f"panel-{role}",max_tokens=1600)
  artifact=artifact.model_copy(update={"trace_id":trace_id,"reviewer_role":role});artifact,bound_events=bound_critic(artifact);errors=gate_critic(artifact,item=item,root=ROOT)
  if errors:raise ValueError(f"{role} gate: {errors}")
  return role,artifact,ledger.summary(),time.perf_counter()-started,bound_events
 panel_started=time.perf_counter()
 with ThreadPoolExecutor(max_workers=3) as pool:reviewed=list(pool.map(review,ROLES))
 parallel_latency=time.perf_counter()-panel_started;artifacts={role:artifact for role,artifact,_,_,_ in reviewed};merged=deterministic_merge(artifacts)
 role_sets={role:{normalize_issue(i.model_dump()) for i in artifact.defects} for role,artifact in artifacts.items()};all_set=set().union(*role_sets.values())
 overlaps={"correctness_security":jaccard(role_sets["correctness"],role_sets["security"]),"correctness_robustness":jaccard(role_sets["correctness"],role_sets["robustness"]),"security_robustness":jaccard(role_sets["security"],role_sets["robustness"])}
 unique={role:len(values-set().union(*(role_sets[r] for r in ROLES if r!=role)))/max(1,len(all_set)) for role,values in role_sets.items()}
 def revise(label,entries):
  ledger=UsageLedger();issues=[entry["issue"] for entry in entries]
  user=f"IMMUTABLE TASK:\n{_task(item)}\nCURRENT ARTIFACT:\n{generator.model_dump_json()}\nPANEL DEFECTS:\n{json.dumps(issues)}\nRevise only those defects. Use trace_id {trace_id}."
  revised=_call(role_file="generator.md",schema=GeneratorArtifact,user=user,trace=trace,ledger=ledger,label=label)
  revised=revised.model_copy(update={"trace_id":trace_id});revised,_=bound_generator(revised)
  errors=gate_generator(revised,item=item,root=ROOT)
  if errors:raise ValueError(f"{label} gate: {errors}")
  return revised,score_item(item["expected"],revised.output.model_dump_json())["score"],ledger.summary()
 full,full_score,full_usage=revise("panel-revise-full",merged["defects"])
 ablations={}
 for omitted in ROLES:
  entries=[entry for entry in merged["defects"] if any(role!=omitted for role in entry["roles"])]
  revised,score,usage=revise(f"panel-revise-without-{omitted}",entries);ablations[omitted]={"score_without":score,"delta_with_minus_without":full_score-score,"usage":usage}
 role_usage={role:usage for role,_,usage,_,_ in reviewed};role_latency={role:latency for role,_,_,latency,_ in reviewed}
 return {"id":item["id"],"generator":generator.model_dump(),"critics":{r:a.model_dump() for r,a in artifacts.items()},"merged":merged,
  "role_sets":{r:[list(x) for x in values] for r,values in role_sets.items()},"overlaps":overlaps,"unique_contribution":unique,
  "triple_overlap":len(set.intersection(*role_sets.values())) if all(role_sets.values()) else 0,"full_revision":full.model_dump(),"full_score":full_score,
  "ablations":ablations,"generator_usage":generator_ledger.summary(),"role_usage":role_usage,"full_revision_usage":full_usage,
  "parallel_latency":parallel_latency,"estimated_sequential_latency":sum(role_latency.values()),"role_latency":role_latency,
  "bound_events":sum((events for *_,events in reviewed),bounds)}
