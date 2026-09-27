import csv

from fastapi.testclient import TestClient

import main
import src.run_experiments as run_experiments

client = TestClient(main.app)


def test_health_route():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_config_route():
    response = client.get("/config")
    assert response.status_code == 200
    data = response.json()
    assert "conditions" in data
    assert "tasks" in data


def test_experiment_route(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "LOG_DIR", tmp_path)
    monkeypatch.setattr(run_experiments, "LOG_DIR", str(tmp_path))

    response = client.post("/experiments/run", params={"condition_id": "A", "seed": 42, "task_id": "task_1"})
    assert response.status_code == 200
    data = response.json()
    assert data["condition_id"] == "A"
    result = data["result"]
    assert result["status"] == "completed"
    assert result["metrics"]["steps"] > 3

    log_path = tmp_path / "condition_A_seed_042_task_1.csv"
    with log_path.open(newline="", encoding="utf-8") as log_file:
        rows = list(csv.DictReader(log_file))
    assert len(rows) == result["metrics"]["steps"]
    assert result["metrics"]["success"] == 1.0


def test_agent_simulation_route_runs_app_py_simulation():
    response = client.post("/agent/simulate", params={"steps": 5, "seed": 42})

    assert response.status_code == 200
    data = response.json()
    assert data["seed"] == 42
    assert data["steps"] == 5
    assert len(data["trace"]) == 5
    assert data["trace"][4]["disturbance"] == "sensor_blackout"
    assert "mean_risk" in data["summary"]
    assert "attention_source" in data["trace"][0]


def test_battery_simulation_route_runs_seeded_self_healing_model():
    response = client.post("/battery/simulate", params={"steps": 25, "seed": 7})

    assert response.status_code == 200
    data = response.json()
    assert data["seed"] == 7
    assert data["steps"] == 25
    assert len(data["trace"]) == 25
    assert data["trace"][20]["time"] == 21
    assert data["summary"]["bypassed_cells"] == []
    assert data["trace"] == client.post(
        "/battery/simulate", params={"steps": 25, "seed": 7}
    ).json()["trace"]


def test_battery_simulation_supports_bounded_ten_times_twin_speed():
    response = client.post(
        "/battery/simulate", params={"steps": 3, "seed": 42, "speed_multiplier": 10}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["speed_multiplier"] == 10
    assert data["trace"][-1]["time"] == 30


def test_autonomous_battery_route_reports_self_model_and_action():
    response = client.post("/battery/autonomous", params={"steps": 3, "seed": 7})

    assert response.status_code == 200
    data = response.json()
    assert data["steps"] == 3
    assert 0.0 <= data["summary"]["final_health"] <= 1.0
    assert 0.0 <= data["summary"]["final_risk"] <= 1.0
    assert data["summary"]["final_action"] == "continue_monitoring"
    assert "confidence" in data["trace"][0]["self_model"]
    assert "predicted_min_voltage" in data["trace"][0]["prediction"]
    assert data["summary"]["estimated_drop_rate"] > 0
    assert data["trace"][0]["actuation"]["status"] == "DRY_RUN"


def test_battery_evaluation_route_replays_recorded_observations():
    observations = [
        {
            "time": 1,
            "cells": [3.7, 3.7, 3.7, 3.7],
            "temperature": 25,
            "current": 2,
            "bypass": [False, False, False, False],
        },
        {
            "time": 2,
            "cells": [3.698, 3.69, 3.698, 3.698],
            "temperature": 25.2,
            "current": 2,
            "bypass": [False, False, False, False],
        },
    ]
    response = client.post("/battery/evaluate", json=observations)

    assert response.status_code == 200
    data = response.json()
    assert data["observations"] == 2
    assert data["summary"]["mean_prediction_error"] > 0
    assert len(data["trace"]) == 2


def test_battery_evaluation_route_returns_validation_error():
    response = client.post("/battery/evaluate", json=[{"time": 1}])

    assert response.status_code == 422
    assert "Missing battery observation fields" in response.json()["detail"]


def test_advanced_chemistry_route_reports_screening_estimate():
    response = client.post(
        "/battery/chemistry/evaluate",
        params={"cycle_count": 350, "average_temp": 42, "state_of_charge": 0.95, "charge_rate_c": 3},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["evaluation"]["model_status"] == "screening_estimate"
    assert data["evaluation"]["structural_boundary_breach"] is True


def test_dashboard_route():
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "Embodied Cybernetic Agency" in response.text


def test_results_route():
    response = client.get("/results")
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "chart_rows" in data
