from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


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


def test_experiment_route():
    response = client.post("/experiments/run", params={"condition_id": "A", "seed": 42, "task_id": "task_1"})
    assert response.status_code == 200
    data = response.json()
    assert data["condition_id"] == "A"
    assert "result" in data


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
