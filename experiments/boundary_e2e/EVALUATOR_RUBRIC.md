# Evaluator rubric

Apply the thresholds per dimension. The feature clears acceptance only
with A in all three dimensions.

| Dimension | A | B | C | D |
|---|---|---|---|---|
| Public CLI contract | 3/3 expected output objects match | 2/3 match | 1/3 matches | 0/3 match or CLI unavailable |
| Local component checks | All four checks pass across both components | Three pass | One or two pass | Zero pass or suite unavailable |
| Reproducibility and diagnosis | Recorded command, exit status, and case outputs support a specific boundary diagnosis | Command and output show a mismatch, with one trace detail missing | Failure is reported without enough evidence to reproduce it | No independent run evidence |

Run the black-box harness from a fresh process against the public examples in
the [sprint contract](SPRINT_CONTRACT.md). Capture its verdict before inspecting
component source. Then use the component tests and wire contract to explain
the mismatch.
