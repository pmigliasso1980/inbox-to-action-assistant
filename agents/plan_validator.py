"""Structured plan schema, seven validation checks, and DAG utilities."""
from __future__ import annotations

from collections import Counter, deque
from typing import Iterable

from pydantic import BaseModel, Field

from agents.review_tools import EXECUTORS


class Step(BaseModel):
    id: str = Field(min_length=1, description="Stable identifier unique within this plan.")
    description: str = Field(min_length=1, description="Bounded action and the inputs it consumes.")
    tool: str | None = Field(description="Registered read-only tool, or null for reasoning/synthesis.")
    depends_on: list[str] = Field(description="Earlier step ids whose produced artifacts are required.")
    produces: str = Field(min_length=1, description="Named bounded artifact produced by this step.")
    success_criterion: str = Field(min_length=1, description="Observable condition required for success.")


class Plan(BaseModel):
    objective: str = Field(min_length=1)
    steps: list[Step]
    completion_criterion: str = Field(min_length=1)


def topological_order(plan: Plan) -> list[str]:
    ids = [step.id for step in plan.steps]
    edges = {step.id: [] for step in plan.steps}; indegree = {step.id: 0 for step in plan.steps}
    for step in plan.steps:
        for dependency in step.depends_on:
            if dependency in edges:
                edges[dependency].append(step.id); indegree[step.id] += 1
    queue = deque(x for x in ids if indegree[x] == 0); ordered = []
    while queue:
        node = queue.popleft(); ordered.append(node)
        for child in edges[node]:
            indegree[child] -= 1
            if indegree[child] == 0: queue.append(child)
    return ordered


def validate_plan(plan: Plan, *, registered_tools: Iterable[str] = EXECUTORS,
                  max_steps: int = 6) -> list[str]:
    """Return specific violations for all seven required validation classes."""
    violations: list[str] = []
    ids = [step.id for step in plan.steps]; positions = {value: index for index, value in enumerate(ids)}
    duplicate_ids = [value for value, count in Counter(ids).items() if count > 1]
    for value in duplicate_ids:
        violations.append(f"duplicate_step_id: step id {value!r} is not unique")
    known = set(ids); tools = set(registered_tools)
    for index, step in enumerate(plan.steps):
        for dependency in step.depends_on:
            if dependency not in known:
                violations.append(f"missing_dependency: step {step.id!r} depends on unknown step {dependency!r}")
            elif positions.get(dependency, index) >= index:
                violations.append(f"later_dependency: step {step.id!r} depends on {dependency!r}, which does not execute earlier")
        if step.tool is not None and step.tool not in tools:
            violations.append(f"unknown_tool: step {step.id!r} names unregistered tool {step.tool!r}")
        if step.depends_on:
            for dependency in step.depends_on:
                source = next((candidate for candidate in plan.steps if candidate.id == dependency), None)
                if source is not None and not source.produces.strip():
                    violations.append(f"missing_required_input: step {step.id!r} requires {dependency!r}, which produces no artifact")
    if len(topological_order(plan)) != len(plan.steps):
        violations.append("cycle: dependency graph is cyclic")
    if len(plan.steps) > max_steps:
        violations.append(f"step_bound: plan has {len(plan.steps)} steps; maximum is {max_steps}")
    if not plan.completion_criterion.strip():
        violations.append("empty_completion_criterion: completion criterion must be non-empty")
    # A non-root reasoning step must name dependencies; otherwise required inputs are unavailable.
    for index, step in enumerate(plan.steps):
        if index > 0 and step.tool is None and not step.depends_on:
            violations.append(f"missing_required_input: reasoning step {step.id!r} declares no prior artifact input")
    return violations
