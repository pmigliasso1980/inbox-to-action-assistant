# Lab 2.1 reflection report

## Reflection did not demonstrate lift beyond the baseline noise floor

The two Module 1 baselines were 0.8786 and 0.9452, with a two-run mean of 0.9119 and a 0.0667 noise floor. Reflection scored 0.9452. That is +0.0333 over the two-run mean, only half the noise floor, and exactly equal to the stronger baseline run. **Lift was not demonstrated.**

The loop used 57,861 input tokens and 2,499 output tokens across 40 calls, cost $0.351780, and took 94.99 seconds. Cost per percentage point over the two-run baseline mean was approximately $0.1055. I would not ship this configuration: it roughly doubles inference work while producing no credible quality improvement.

## Diagnostics explain the flat result

1. **Stopping distribution:** all 20 items stopped as satisfactory at iteration 1; mean iterations was 1.0 and the cap rate was zero. The critic is too permissive to activate reflection.
2. **Evaluator audit:** only three final outputs were wrong (items 011, 017, and 018), so all three were audited plus the variable line-attribution cases 006 and 012. The evaluator missed extra findings on 011, the line/evidence mismatch on 017, and the missed cache race on 018. Revisions could not act because no critique was produced.
3. **Per-iteration scores:** every item had one iteration, so the observed sequence was trivially monotonic and the best draft was always the last. This is not evidence that revision is safe; it means revision never ran.
4. **Issue clustering:** no criterion dominated because the critic emitted no issues. The concrete generator change would be to require a second evidence-verification pass before declaring the review complete, especially for multi-defect and shared-state snippets.

The gate failure fraction was 0%. That is good format performance but also confirms that the remaining errors are semantic rather than mechanical. Cached-input tokens were zero because no item reached a repeated evaluator call; a future production version should put the stable task/rubric prefix into explicit prompt caching before multi-iteration use.

## Next change

The next experiment should adversarially frame the critic and require it to cite at least one checked rubric criterion before satisfaction. The benchmark score—not critic satisfaction—must remain the arbiter, and the best-scoring draft must be returned when revisions regress.
