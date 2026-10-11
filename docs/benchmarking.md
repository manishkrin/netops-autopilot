# Benchmark evidence

Performance claims must include the environment, exact commit, configuration, workload shape, warm-up, run count, raw results, and interpretation. Do not commit a polished number without the data that produced it.

The initial sequential baseline can be run while the API is active:

```bash
uv run python scripts/benchmark_ingestion.py --count 1000
```

This is a correctness-oriented baseline, not a concurrency or capacity test. Month 6 adds controlled concurrent load, repeated trials, resource measurements, database-size effects, duplicate-heavy workloads, error injection, restart recovery, and confidence intervals.

Recorded baselines:

- [2026-10-11 local sequential ingestion](benchmarks/2026-10-11-local-sequential.md)


