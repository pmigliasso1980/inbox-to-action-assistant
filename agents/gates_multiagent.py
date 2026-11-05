"""Bounded multi-agent artifact contracts and handoff gates."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from agents.reflection import Issue
from evals.run_baseline import Review

TAXONOMY={"auth_bypass","command_injection","division_by_zero","identity_comparison","incorrect_cache_key","infinite_loop","insecure_random","invalid_amount","missing_await","missing_timeout","mutable_default","non_atomic_transaction","null_dereference","off_by_one","path_traversal","race_condition","resource_leak","result_overwritten","sql_injection","ssrf","swallowed_exception","timezone_naive","unchecked_status"}


class GeneratorArtifact(BaseModel):
    output: Review
    assumptions: list[str] = Field(min_length=1,max_length=8)
    unresolved: list[str] = Field(max_length=8)
    trace_id: str = Field(min_length=1,max_length=240)


class CriticArtifact(BaseModel):
    defects: list[Issue] = Field(max_length=10)
    decision: Literal["accept","revise","reject"]
    rationale: str = Field(min_length=1,max_length=1000)
    rejected_assumptions: list[str] = Field(max_length=8)
    trace_id: str = Field(min_length=1,max_length=240)


class PanelCriticArtifact(CriticArtifact):
    reviewer_role: Literal["correctness","security","robustness","combined"]


def bound_generator(artifact:GeneratorArtifact)->tuple[GeneratorArtifact,list[str]]:
    events=[];data=artifact.model_dump()
    if len(data["output"]["defects"])>8:data["output"]["defects"]=data["output"]["defects"][:8];events.append("truncated output.defects to 8")
    for field in ["assumptions","unresolved"]:
        cleaned=[str(x)[:300] for x in data[field]][:8]
        if cleaned!=data[field]:events.append(f"bounded {field}")
        data[field]=cleaned
    return GeneratorArtifact.model_validate(data),events


def bound_critic(artifact:CriticArtifact)->tuple[CriticArtifact,list[str]]:
    events=[];data=artifact.model_dump()
    if len(data["defects"])>10:data["defects"]=data["defects"][:10];events.append("truncated defects to 10")
    if len(data["rationale"])>1000:data["rationale"]=data["rationale"][:1000];events.append("truncated rationale")
    data["rejected_assumptions"]=[str(x)[:300] for x in data["rejected_assumptions"]][:8]
    cls=type(artifact)
    return cls.model_validate(data),events


def gate_generator(artifact:GeneratorArtifact,*,item:dict,root:Path)->list[str]:
    errors=[];lines=len(item["input"].splitlines())
    if not artifact.trace_id.strip() or not (root/artifact.trace_id).is_file():errors.append(f"trace_id does not reference an existing transcript: {artifact.trace_id!r}")
    if not artifact.assumptions:errors.append("assumptions must be non-empty")
    if len(json.dumps(artifact.model_dump()))>8000:errors.append("generator artifact exceeds 8000-character bound")
    for index,defect in enumerate(artifact.output.defects):
        if defect.category not in TAXONOMY:errors.append(f"output defect {index} has unknown category {defect.category!r}")
        if not 1<=defect.line<=lines:errors.append(f"output defect {index} references nonexistent line {defect.line}")
    return errors


def gate_critic(artifact:CriticArtifact,*,item:dict,root:Path)->list[str]:
    errors=[];lines=len(item["input"].splitlines())
    if not artifact.trace_id.strip() or not (root/artifact.trace_id).is_file():errors.append(f"trace_id does not reference an existing transcript: {artifact.trace_id!r}")
    if len(json.dumps(artifact.model_dump()))>8000:errors.append("critic artifact exceeds 8000-character bound")
    for index,issue in enumerate(artifact.defects):
        location=issue.location.lower().replace("line","").strip(" :#")
        if location.isdigit() and not 1<=int(location)<=lines:errors.append(f"critic defect {index} references nonexistent line {location}")
    if any(issue.severity=="blocking" for issue in artifact.defects) and artifact.decision=="accept":
        errors.append("decision must be revise or reject when a blocking defect exists")
    return errors
