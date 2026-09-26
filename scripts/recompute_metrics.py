# scripts/recompute_metrics.py

import csv
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.metrics import aggregate_by_condition, compute_basic_metrics, load_log

RAW_LOG_DIR = ROOT / "logs" / "raw"
AGG_DIR = ROOT / "logs" / "aggregated"

def ensure_dir(path):
    path.mkdir(parents=True, exist_ok=True)


def main():
    ensure_dir(AGG_DIR)
    ensure_dir(RAW_LOG_DIR)

    run_metrics = {}

    for fname in sorted(os.listdir(RAW_LOG_DIR)):
        if not fname.endswith(".csv"):
            continue
        path = RAW_LOG_DIR / fname
        rows = load_log(str(path))
        metrics = compute_basic_metrics(rows)

        run_id = os.path.splitext(fname)[0]
        run_metrics[run_id] = metrics

    summary = aggregate_by_condition(run_metrics)

    summary_path = AGG_DIR / "summary_by_condition.csv"
    with open(summary_path, "w", newline="") as f:
        fieldnames = ["condition", "success", "mean_risk", "max_risk", "steps"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for cond, m in summary.items():
            row = {"condition": cond}
            row.update(m)
            writer.writerow(row)

    print(f"[INFO] Wrote {summary_path}")


if __name__ == "__main__":
    main()