# Benchmark evidence

Performance claims must include the environment, exact commit, configuration, workload shape, warm-up, run count, raw results, and interpretation. Do not commit a polished number without the data that produced it.

The initial sequential baseline can be run while the API is active:

```bash
uv run python scripts/benchmark_ingestion.py --count 1000 --out benchmark-results/run.json
```

The script emits the commit SHA, working-tree dirty flag, Python version, platform, CPU count, HTTP status counts, latency percentiles, and the stored-event count before and after the run, and fails unless every response was `202` and the stored count grew by exactly `--count`. Still record by hand what it cannot see: the server's Python and SQLite versions if they differ from the client's, the exact server command line, and hardware details such as CPU model and storage. Copy the raw JSON into `docs/benchmarks/` alongside the interpretation.

This is a correctness-oriented baseline, not a concurrency or capacity test. Month 6 adds controlled concurrent load, repeated trials, resource measurements, database-size effects, duplicate-heavy workloads, error injection, restart recovery, and confidence intervals.

Recorded baselines:

- [2026-10-11 local sequential ingestion](benchmarks/2026-10-11-local-sequential.md) — recorded before the script emitted commit, environment, and before/after counts itself, so those fields were captured manually and are not machine-verified. Re-run with the current script on the target Python (3.12, as used in CI) to replace it with a fully self-describing record.


