"""Outcome metrics for autonomous battery controller traces."""

from __future__ import annotations

from collections import Counter
from typing import Any


def summarize_decisions(trace: list[dict[str, Any]]) -> dict[str, Any]:
    if not trace:
        raise ValueError("Cannot summarize an empty battery trace")

    risks = [item["self_model"]["risk"] for item in trace]
    errors = [item["prediction"]["error"] for item in trace]
    actions = Counter(item["action"] for item in trace)
    bypass_counts = [sum(item["bypass"]) for item in trace]
    return {
        "steps": len(trace),
        "action_counts": dict(actions),
        "fault_events": sum(1 for count in bypass_counts if count > 0),
        "max_bypassed_cells": max(bypass_counts),
        "safety_override_count": sum(
            1 for item in trace if item["safety_override"]
        ),
        "mean_risk": sum(risks) / len(risks),
        "max_risk": max(risks),
        "mean_prediction_error": sum(errors) / len(errors),
        "max_prediction_error": max(errors),
        "health_delta": (
            trace[-1]["self_model"]["health"]
            - trace[0]["self_model"]["health"]
        ),
    }