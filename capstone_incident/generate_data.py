"""Generate the frozen incident-analysis corpus. No model or network access."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

SERVICES = {
    "checkout": ("Payments", "database_pool_exhaustion", "Cap pool usage and add backpressure", "SEV-1"),
    "catalog": ("Catalog", "stale_cache", "Version cache keys and add invalidation checks", "SEV-2"),
    "notifications": ("Messaging", "queue_backlog", "Add queue autoscaling and age alarms", "SEV-2"),
    "identity": ("Identity", "expired_certificate", "Automate certificate renewal and expiry alerts", "SEV-1"),
    "search": ("Discovery", "dependency_timeout", "Add bounded retries and dependency timeouts", "SEV-2"),
    "gateway": ("Platform", "rate_limit_misconfiguration", "Validate rate-limit policy before rollout", "SEV-1"),
    "billing": ("Finance Systems", "duplicate_delivery", "Add idempotency keys to invoice delivery", "SEV-1"),
    "profile": ("Accounts", "schema_mismatch", "Add consumer-driven schema compatibility checks", "SEV-2"),
    "analytics": ("Data Platform", "partition_skew", "Repartition hot keys and alert on skew", "SEV-2"),
    "inventory": ("Fulfillment", "lock_contention", "Reduce lock scope and cap transaction duration", "SEV-2"),
}


def make_item(index: int, service: str, *, dev: bool = False) -> dict:
    owner, cause, remediation, severity = SERVICES[service]
    recurrence = False if dev else index > 10
    expected_remediation = remediation
    if not dev and index >= 16:
        expected_remediation += "; verify the change with a service-specific load test"
    wording = {
        "database_pool_exhaustion": "Connections hit the configured pool ceiling and requests waited until timeout.",
        "stale_cache": "A stale cache entry survived deployment and served the previous catalog version.",
        "queue_backlog": "Consumer throughput fell below ingress and queue age climbed for 18 minutes.",
        "expired_certificate": "The upstream TLS certificate expired and the renewal job had not run.",
        "dependency_timeout": "The ranking dependency exceeded its timeout while retries amplified traffic.",
        "rate_limit_misconfiguration": "A rate limit policy misconfiguration rejected healthy gateway traffic.",
        "duplicate_delivery": "At-least-once delivery produced duplicate invoices without idempotency keys.",
        "schema_mismatch": "A schema mismatch caused the profile consumer to reject new events.",
        "partition_skew": "A hot tenant caused partition skew and delayed the analytics pipeline.",
        "lock_contention": "Long transactions caused lock contention in the inventory reservation table.",
    }[cause]
    return {
        "id": f"{'dev' if dev else 'incident'}-{index:03}",
        "input": {"title": f"{service.title()} disruption {index}", "service": service,
                  "occurred_at": f"2026-10-{(index % 28) + 1:02}T12:00:00Z",
                  "description": wording},
        "expected": {"primary_cause": cause, "severity": severity, "remediation": expected_remediation,
                     "owner": owner, "recurrence_key": f"{service}:{cause}" if recurrence else None},
        "partition": "repeat-pattern" if recurrence else "first-encounter",
    }


def main() -> None:
    data = ROOT / "data"
    data.mkdir(parents=True, exist_ok=True)
    services = list(SERVICES)
    evaluation = [make_item(i, services[(i - 1) % len(services)]) for i in range(1, 21)]
    development = [make_item(i, services[(i - 1) % len(services)], dev=True) for i in range(1, 6)]
    (data / "eval.jsonl").write_text("".join(json.dumps(x, sort_keys=True) + "\n" for x in evaluation))
    (data / "dev.jsonl").write_text("".join(json.dumps(x, sort_keys=True) + "\n" for x in development))
    (data / "owners.json").write_text(json.dumps({k: v[0] for k, v in SERVICES.items()}, indent=2) + "\n")


if __name__ == "__main__":
    main()
