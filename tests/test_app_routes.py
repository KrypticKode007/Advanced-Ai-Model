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
