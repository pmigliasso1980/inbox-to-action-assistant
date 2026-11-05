"""Best-of-three generator configuration with one bounded selector critic."""
from __future__ import annotations
import argparse,json,time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from pydantic import BaseModel,Field
from agents.gen_critic import ROOT,_call,_task
from agents.gates_multiagent import GeneratorArtifact,bound_generator,gate_generator
from agents.llm import UsageLedger
from evals.score import score_item

class Selection(BaseModel):
 selected_index:int=Field(ge=0,le=2)
 rationale:str=Field(min_length=1,max_length=800)

def run_item(item,out):
 out.mkdir(parents=True,exist_ok=True);trace=out/"transcript.jsonl";trace.touch(exist_ok=True);trace_id=str(trace.relative_to(ROOT))
 def generate(index):
  ledger=UsageLedger();artifact=_call(role_file="generator.md",schema=GeneratorArtifact,user=f"IMMUTABLE TASK:\n{_task(item)}\nIndependently generate candidate {index}. Use trace_id {trace_id}.",trace=trace,ledger=ledger,label=f"best3-generator-{index}")
  artifact=artifact.model_copy(update={"trace_id":trace_id});artifact,_=bound_generator(artifact);errors=gate_generator(artifact,item=item,root=ROOT)
  if errors:raise ValueError(errors)
  return artifact,ledger.summary()
 with ThreadPoolExecutor(max_workers=3) as pool:generated=list(pool.map(generate,range(3)))
 candidates=[x[0] for x in generated];ledger=UsageLedger();selection=_call(role_file="critic.md",schema=Selection,user=f"IMMUTABLE TASK:\n{_task(item)}\nCANDIDATES:\n{json.dumps([x.model_dump() for x in candidates])}\nSelect the strongest precise review. Do not rewrite it.",trace=trace,ledger=ledger,label="best3-selector",max_tokens=700)
 chosen=candidates[selection.selected_index];usage=[x[1] for x in generated]+[ledger.summary()]
 return {"id":item["id"],"selected_index":selection.selected_index,"selection_rationale":selection.rationale,"output":chosen.output.model_dump(),"score":score_item(item["expected"],chosen.output.model_dump_json())["score"],"usage":{"calls":sum(x["calls"] for x in usage),"input_tokens":sum(x["input_tokens"] for x in usage),"output_tokens":sum(x["output_tokens"] for x in usage),"cached_input_tokens":sum(x["cached_input_tokens"] for x in usage),"cost_usd":sum(x["cost_usd"] for x in usage)}}

def main():
 p=argparse.ArgumentParser();p.add_argument("--limit",type=int,default=5);p.add_argument("--name",default="best-of-3");a=p.parse_args();items=[json.loads(x) for x in (ROOT/"evals/dataset.jsonl").read_text().splitlines() if x][:a.limit];out=ROOT/"runs"/a.name;rows=[];started=time.perf_counter()
 for i,item in enumerate(items,1):
  row=run_item(item,out/item["id"]);rows.append(row);(out/item["id"]/"result.json").write_text(json.dumps(row,indent=2)+"\n");print(f"[{i}/{len(items)}] {item['id']} score={row['score']:.3f} cost=${row['usage']['cost_usd']:.3f}",flush=True)
 summary={"items":len(rows),"mean_score":sum(x["score"] for x in rows)/len(rows),"tokens_per_item":sum(x["usage"]["input_tokens"]+x["usage"]["output_tokens"] for x in rows)/len(rows),"cost_usd":sum(x["usage"]["cost_usd"] for x in rows),"cached_tokens":sum(x["usage"]["cached_input_tokens"] for x in rows),"wall_clock_seconds":time.perf_counter()-started,"records":rows};(out/"summary.json").write_text(json.dumps(summary,indent=2)+"\n");print(json.dumps({k:v for k,v in summary.items() if k!="records"},indent=2))
if __name__=="__main__":main()
