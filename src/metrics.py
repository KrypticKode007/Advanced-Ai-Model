# src/metrics.py

import csv
from collections import defaultdict
from typing import List, Dict


def load_log(path: str) -> List[Dict[str, str]]:
    """Load a single CSV log file into a list of dict rows."""
    rows = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def compute_basic_metrics(rows: List[Dict[str, str]]) -> Dict[str, float]:
    """
    Compute simple metrics from one run:
    - success (0/1)
    - collisions (if you log them later)
    - mean risk
    - max risk
    - steps
    """
    if not rows:
        return {
            "success": 0.0,
            "mean_risk": 0.0,
            "max_risk": 0.0,
            "steps": 0,
        }

    risks = []
    success = 0.0

    for r in rows:
        try:
            risk = float(r.get("risk", 0.0))
        except ValueError:
            risk = 0.0
        risks.append(risk)

        if r.get("success", "0") in ("1", "True", "true", "yes"):
            success = 1.0

    mean_risk = sum(risks) / len(risks) if risks else 0.0
    max_risk = max(risks) if risks else 0.0

    return {
        "success": success,
        "mean_risk": mean_risk,
        "max_risk": max_risk,
        "steps": len(rows),
    }


def aggregate_by_condition(run_metrics: Dict[str, Dict[str, float]]) -> Dict[str, Dict[str, float]]:
    """
    Given a dict like:
        { "condition_A_seed_101": {...}, "condition_B_seed_202": {...}, ... }
    produce per-condition averages.
    """
    buckets = defaultdict(list)

    for run_id, metrics in run_metrics.items():
        # Expect run_id like "condition_A_seed_101"
        parts = run_id.split("_")
        if len(parts) >= 2:
            cond = parts[1]  # "A"
        else:
            cond = "unknown"
        buckets[cond].append(metrics)

    summary = {}
    for cond, metrics_list in buckets.items():
        n = len(metrics_list)
        if n == 0:
            continue

        summed = defaultdict(float)
        for m in metrics_list:
            for k, v in m.items():
                summed[k] += v

        summary[cond] = {k: v / n for k, v in summed.items()}

    return summary