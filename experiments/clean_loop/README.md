# Clean-state loop lab

Run from the repository root with Git and Python 3.11 with tar extraction
filters available:

```bash
python3 experiments/clean_loop/run.py
```

The generator and evaluator can also be run separately. From the repository
root, run `python3 experiments/clean_loop/generator.py . 2` to see the JSON
candidate and pipe that command into
`python3 experiments/clean_loop/evaluator.py .` to check it. Use attempt 1
to reproduce a rejection. The coordinator uses an isolated committed snapshot.

See [loop specification](LOOP_SPEC.md), [recorded run](run-log.json), and
[verification debt findings and exit proof](FINDINGS.md).
