import csv
import subprocess
import sys
from pathlib import Path

import src.run_experiments as run_experiments

ROOT = Path(__file__).resolve().parents[1]


def test_metrics_script_runs_from_repo_root():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "recompute_metrics.py")],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )

    assert result.returncode == 0, result.stderr or result.stdout


def test_build_test_command_runs_outside_repo_root():
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "Build.py"),
            "test",
        ],
        capture_output=True,
        text=True,
        cwd=ROOT / "tests",
    )

    assert result.returncode == 0, result.stderr or result.stdout


def test_single_experiment_runs_and_writes_step_data(tmp_path, monkeypatch):
    monkeypatch.setattr(run_experiments, "LOG_DIR", str(tmp_path))

    metrics = run_experiments.run_single_experiment("A", 7)

    log_path = tmp_path / "condition_A_seed_007_task_1.csv"
    assert metrics["success"] == 1.0
    assert metrics["steps"] > 1
    with log_path.open(newline="", encoding="utf-8") as log_file:
        rows = list(csv.DictReader(log_file))
    assert len(rows) == metrics["steps"]
    assert rows[0]["step"] == "1"
    assert any(row["disturbance"] == "sensor_noise" for row in rows)
