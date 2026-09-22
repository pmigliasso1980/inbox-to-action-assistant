# Capstone Design Review

## The three hard calls

### Triage a case: tool, not resource

Triage can be read-only in some systems, so a computed resource was plausible. I chose a tool because
the model must decide when semantic judgment is needed and supply the priority; Q1’s second clause wins
even without relying on the side effect of storing the result. Building it reinforced the choice: its
evidence rationale and constrained priority are invocation inputs, while a resource read has no natural
place for that auditable decision.

### Case details: resource, not tool

`read_case` would be easy to implement as a tool, but the application or user already knows which case
is selected and simply needs read-only context. A templated resource makes that control model explicit,
gives the data a stable identity, and avoids teaching the model to call a function for a known record.
Building the client strengthened this decision because the same URI works for explicit context loading,
prompt instructions, and verification after mutations.

### Draft a reply: prompt, not tool

A `draft_reply` tool could appear convenient, but this server does not own or call a model. The real
capability is reusable instruction authored by the domain expert and intentionally selected by a user,
so a prompt preserves user control and leaves model execution to the host. Building it did not change
the classification; it made the separation between resolving instructions and generating a reply more
concrete.

## The duplication test

No exact capability is exposed as two primitives. The tools mutate or record model-selected decisions,
while resources expose the resulting store for application-controlled reads; sharing the underlying
case dictionary is intentional, but `set_case_status` and `case_details` represent different user
scenarios rather than duplicate operations.

## The risk audit

`set_case_status` is the most dangerous tool because an incorrect `closed` call removes a case from
active-work views. Its verb-first name makes mutation visible, its description says that closure should
follow verified outcomes or explicit human direction, its `Literal` restricts targets, and same-state
requests fail loudly. The in-memory server cannot prove that an external outcome was actually completed;
the host must enforce authorization, confirmation, and organizational policy before invocation.

## Inspector-driven improvements

The first Inspector tool form rendered `priority` as a plain text field whose help text did not list the
allowed enum values. I changed the description to enumerate `low`, `normal`, `high`, and `urgent`, so a
stranger can fill the form without opening the raw input schema.

The same form did not display Pydantic's `minLength` and `maxLength` constraints next to `rationale`. I
added “10–240 characters” to the field description, preserving the machine constraint while making it
legible in hosts that only render descriptions. The prompt menu already read as human-selected actions,
and its required/optional cues and examples needed no correction.

The in-process `show_all.py` inventory matched `DESIGN.md`: three tools, two direct resources, one
templated resource, and two prompts were present with the intended MIME types and required flags.

## What I would do differently

A real server would replace the dictionary with transactional persistence, enforce per-user permissions,
add idempotency and concurrency controls, and write an immutable audit log before changing ownership or
status. I would also require human confirmation for closure and redact sensitive message content from
logs. The first major topic I would need to learn beyond this course is production MCP authentication and
authorization for a remote, multi-user Streamable HTTP deployment.
