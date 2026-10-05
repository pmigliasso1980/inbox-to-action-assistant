# Baselines and arithmetic

## Summary

| Workflow | Monthly work baseline | Elapsed-time baseline | Confidence |
|---|---:|---|---|
| WF-O01 prior authorization | **≥771.7 hours projected** | Clinic gaps **1 day–1 week reported**; payer decision unknown | Medium-low: observation plus system counts, chase mix missing |
| WF-O02 referral intake | **377.6–485.5 hours projected** for fax cases | Unknown | Medium: ten observed cases plus system counts |
| WF-R02 denials/appeals | **≥258.3 hours projected** before appeal assembly | Evidence wait **1–2 days reported**; payer decision **30–45 days reported** | Low-medium: system counts, interview only, no shadowing |

## Reproducible calculations

```text
WF-O01 new work:
  mean observed completed request = (19 + 14 + 17) / 3 = 16.67 minutes
  2,400 measured requests × 16.67 / 60 = 666.8 hours projected
  (rounded process-map value uses 16.7 minutes: 668.0 hours)

WF-O01 chase lower bound:
  2,400 measured × 61% measured = 1,464 projected chase events
  34 observed minutes / 8 observed portal rows = 4.25 minutes projected per portal chase
  1,464 × 4.25 / 60 = 103.7 hours projected
  Combined rounded lower bound = 668.0 + 103.7 = 771.7 hours projected

WF-O02 fax volume:
  5,800 measured × 62% measured = 3,596 projected fax referrals
  observed ten-case bounds = 10 + (6 × 4..7) + 13 + 16 = 63..81 minutes
  mean range = 6.3..8.1 minutes projected
  monthly range = 3,596 × 6.3..8.1 / 60 = 377.6..485.5 hours projected

WF-R02 first-pass denials:
  47,000 measured × 12.3% measured = 5,781 projected denials
  5,781 projected − 3,100 measured worked = 2,681 projected below-threshold write-offs
  minimum initial review = 3,100 measured × 5 reported minutes / 60 = 258.3 projected hours
```

The rounding difference in WF-O01 is disclosed rather than hidden. No rework multiplier is added where
events may overlap; doing so would create a more impressive but less defensible number.
