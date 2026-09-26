import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_metrics_script_runs_from_repo_root():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "recompute_metrics.py")],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )

    assert result.returncode == 0, result.stderr or result.stdout
