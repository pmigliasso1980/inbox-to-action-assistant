# Cross-team pattern: status chasing hides between systems

## Pattern

WF-O01 prior authorization and WF-P01/P02 credentialing share the same shape: a submission leaves Kestrel,
status lives in multiple payer portals, a spreadsheet schedules follow-up, and staff repeatedly log in or
call to discover whether anything changed. WF-R02 inherits the failure when authorization status or evidence
does not return cleanly.

## Combined impact supported by evidence

- Prior authorization has at least **1,464 chase events/month projected** and a **103.7-hour/month projected
  portal-chase lower bound** [WF-O01].
- New-provider enrollment creates **326.7 form-filling hours/quarter projected**, while status-chase time is
  unknown [OPP-05].
- Recredentialing adds **60 cycles/quarter measured**, but the dossier does not support a time estimate [B9].

The defensible combined numeric floor is therefore **103.7 chase hours/month projected**, plus unquantified
credentialing chase time. Adding enrollment form-filling would mix a different work shape and overstate the
shared pattern.

## Why one foundation is cheaper

A shared submission-status service could provide identity, audit, ownership, follow-up scheduling, exception
queues, notifications, and a governed event model once. Separate teams would otherwise rebuild those
controls around different spreadsheets.

## What genuinely differs and what it costs

Prior authorization is patient- and procedure-specific, time sensitive, and includes clinical evidence.
Credentialing is provider-specific, spans longer **90–120 day reported** cycles, and links to highly sensitive
identity and professional-history documents. Payer connectivity also differs. These differences require
separate schemas, permissions, retention rules, test sets, and human-review paths. One platform is plausible;
one universal workflow is not. A connectivity inventory and workflow observation must precede any shared build.
