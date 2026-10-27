from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "benchmark_ingestion.py"


@pytest.fixture
def benchmark() -> ModuleType:
    spec = importlib.util.spec_from_file_location("benchmark_ingestion", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_percentile_picks_nearest_rank(benchmark: ModuleType) -> None:
    assert benchmark.percentile([5.0, 1.0, 3.0], 0.5) == 3.0
    assert benchmark.percentile([7.0], 0.99) == 7.0


def test_metrics_url_is_derived_from_target(benchmark: ModuleType) -> None:
    assert benchmark.metrics_url("http://127.0.0.1:8765/v1/alerts") == (
        "http://127.0.0.1:8765/v1/metrics"
    )


def test_run_records_environment_and_verifies_stored_count(
    benchmark: ModuleType, live_server: str
) -> None:
    result = benchmark.run(f"{live_server}/v1/alerts", 25)

    assert result["http_status_counts"] == {202: 25}
    assert result["stored_event_count_before_run"] == 0
    assert result["stored_event_count_after_run"] == 25
    assert result["verified"] is True
    environment = result["environment"]
    assert {"commit", "python", "platform", "machine", "cpu_count"} <= environment.keys()


def test_main_writes_raw_result_file(
    benchmark: ModuleType,
    live_server: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    out = tmp_path / "nested" / "result.json"
    monkeypatch.setattr(
        "sys.argv",
        [
            "benchmark_ingestion.py",
            "--target",
            f"{live_server}/v1/alerts",
            "--count",
            "10",
            "--out",
            str(out),
        ],
    )

    assert benchmark.main() == 0
    assert json.loads(out.read_text())["submission_count"] == 10


def test_main_fails_when_target_rejects_submissions(
    benchmark: ModuleType, live_server: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "sys.argv",
        ["benchmark_ingestion.py", "--target", f"{live_server}/v1/nope", "--count", "3"],
    )
    assert benchmark.main() == 1
