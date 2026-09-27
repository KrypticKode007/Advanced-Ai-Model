import pytest

from src.battery import AutonomousBatteryController
from src.battery_metrics import summarize_decisions


def test_battery_metrics_report_faults_and_actions():
    trace = AutonomousBatteryController(seed=42).run(45)

    metrics = summarize_decisions(trace)

    assert metrics["steps"] == 45
    assert metrics["fault_events"] > 0
    assert metrics["action_counts"]["isolate_bypassed_cells"] > 0
    assert metrics["max_prediction_error"] >= metrics["mean_prediction_error"]


def test_battery_metrics_reject_empty_trace():
    with pytest.raises(ValueError, match="empty"):
        summarize_decisions([])