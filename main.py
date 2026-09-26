import csv
from pathlib import Path

import yaml
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import numpy as np
from scipy.special import rel_entr

from src.metrics import aggregate_by_condition, compute_basic_metrics, load_log

PROJECT_ROOT = Path(__file__).resolve().parent
LOG_DIR = PROJECT_ROOT / "logs" / "raw"
SUMMARY_DIR = PROJECT_ROOT / "logs" / "aggregated"


class AuditedCyberneticEngine:
    def __init__(self):
        self.channels = ["VISION", "AUDIO", "TOUCH"]
        self.channel_weights = np.array([0.5, 0.3, 0.2])

        self.internal_matrix = np.array([
            [0.8, 0.1, 0.1],
            [0.5, 0.4, 0.1],
            [0.9, 0.05, 0.05],
        ])

        self.substrate = {"gpu_temp_c": 40.0, "cpu_temp_c": 38.0, "power_w": 15.0}

        self.AUDIT_LIMITS = {
            "max_safe_somatic_stress": 1.1,
            "structural_collapse_limit": 1.4,
            "dissociation_limit": 1.7,
            "noise_dampening_threshold": 0.15,
        }

    def apply_information_noise_filter(self, P, Q):
        """Calculates raw information delta and suppresses micro sensor jitter."""
        filtered_stress = np.zeros(len(self.channels))
        raw_stress = np.zeros(len(self.channels))

        for i in range(len(self.channels)):
            divergence = np.sum(rel_entr(P[i], Q[i]))
            raw_stress[i] = divergence

            if divergence < self.AUDIT_LIMITS["noise_dampening_threshold"]:
                filtered_stress[i] = divergence * 0.1
            else:
                filtered_stress[i] = divergence

        return filtered_stress, raw_stress

    def execute_audited_clock_cycle(self, raw_sensor_feeds):
        P = raw_sensor_feeds
        Q = self.internal_matrix

        filtered_stress, raw_stress = self.apply_information_noise_filter(P, Q)
        aggregate_somatic_stress = np.sum(filtered_stress * self.channel_weights)

        self.substrate["gpu_temp_c"] = 40.0 + (25.0 * aggregate_somatic_stress)
        self.substrate["cpu_temp_c"] = 38.0 + (20.0 * aggregate_somatic_stress)
        self.substrate["power_w"] = 15.0 + (35.0 * aggregate_somatic_stress)

        if aggregate_somatic_stress > self.AUDIT_LIMITS["max_safe_somatic_stress"]:
            print("⚠️ [AUDIT WARNING] Kinetic Loop approaching structural boundary limit.")

        if aggregate_somatic_stress > self.AUDIT_LIMITS["structural_collapse_limit"]:
            return f"[COLLAPSE FAULT] Node 2 Meltdown: PSYCHOSOMATIC_FREEZE. Stress: {aggregate_somatic_stress:.4f} nats."

        efficiency = np.exp(-aggregate_somatic_stress * 0.2)
        behavioral_matrix = Q * efficiency
        behavioral_matrix /= np.sum(behavioral_matrix, axis=1, keepdims=True)

        meta_errors = np.array(
            [np.sum(rel_entr(behavioral_matrix[i], P[i])) for i in range(len(self.channels))]
        )
        aggregate_meta_error = np.sum(meta_errors * self.channel_weights)

        if aggregate_meta_error > self.AUDIT_LIMITS["dissociation_limit"]:
            return f"[COLLAPSE FAULT] Node 4 Disconnect: DISSOCIATION / DEPERSONALIZATION."

        self.internal_matrix = Q + 0.15 * (P - Q)
        self.internal_matrix /= np.sum(self.internal_matrix, axis=1, keepdims=True)

        return (
            f"[LOOP SECURE] Raw/Filtered Somatic Stress: {np.sum(raw_stress):.3f}/{aggregate_somatic_stress:.3f} nats. "
            f"GPU: {self.substrate['gpu_temp_c']:.1f}°C"
        )


engine = AuditedCyberneticEngine()

app = FastAPI(title="Embodied Cybernetic Agency", version="0.1.0")


@app.get("/")
async def read_root():
    return {
        "name": "Embodied Cybernetic Agency",
        "status": "ok",
        "docs": "/docs",
        "simulate": "/simulate",
    }


def _load_conditions_and_tasks():
    with open(PROJECT_ROOT / "config" / "conditions.yaml", "r", encoding="utf-8") as f:
        conditions = yaml.safe_load(f)["conditions"]
    with open(PROJECT_ROOT / "config" / "tasks_gridworld.yaml", "r", encoding="utf-8") as f:
        tasks_cfg = yaml.safe_load(f)
    return conditions, tasks_cfg


def _write_run_csv(condition_id: str, seed: int, task_id: str, run_metrics: dict):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_DIR.mkdir(parents=True, exist_ok=True)

    file_name = f"condition_{condition_id}_seed_{seed:03d}_{task_id}.csv"
    path = LOG_DIR / file_name

    fieldnames = ["step", "risk", "success", "condition", "seed", "task_id"]
    rows = [
        {"step": 0, "risk": 0.12, "success": 0, "condition": condition_id, "seed": seed, "task_id": task_id},
        {"step": 1, "risk": 0.24, "success": 0, "condition": condition_id, "seed": seed, "task_id": task_id},
        {"step": 2, "risk": 0.38, "success": 1, "condition": condition_id, "seed": seed, "task_id": task_id},
    ]
    rows[0]["risk"] = run_metrics.get("mean_risk", 0.12)
    rows[1]["risk"] = min(1.0, run_metrics.get("max_risk", 0.24))
    rows[2]["risk"] = max(0.0, run_metrics.get("mean_risk", 0.12) * 0.8)
    rows[2]["success"] = 1 if run_metrics.get("success", 0.0) > 0.5 else 0

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return path


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/config")
async def get_config():
    conditions, tasks_cfg = _load_conditions_and_tasks()
    return {
        "conditions": conditions,
        "tasks": tasks_cfg["tasks"],
        "world": tasks_cfg["world"],
    }


@app.get("/simulate")
async def simulate():
    ambient_jitter = np.array([
        [0.78, 0.11, 0.11],
        [0.49, 0.41, 0.10],
        [0.89, 0.06, 0.05],
    ])

    systemic_trauma = np.array([
        [0.10, 0.10, 0.80],
        [0.40, 0.40, 0.20],
        [0.30, 0.35, 0.35],
    ])

    ambient_result = engine.execute_audited_clock_cycle(ambient_jitter)
    trauma_result = engine.execute_audited_clock_cycle(systemic_trauma)

    return {
        "ambient_jitter": ambient_result,
        "systemic_trauma": trauma_result,
        "substrate": engine.substrate,
    }


@app.post("/experiments/run")
async def run_experiment(
    request: Request,
    condition_id: str | None = None,
    seed: int = 42,
    task_id: str = "task_1",
):
    if request.method == "POST":
        content_type = request.headers.get("content-type", "")
        if "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
            form = await request.form()
            condition_id = form.get("condition_id") or condition_id
            seed = int(form.get("seed", seed))
            task_id = form.get("task_id") or task_id

    if condition_id is None:
        condition_id = request.query_params.get("condition_id")
    if condition_id is None:
        raise ValueError("condition_id is required")

    conditions, tasks_cfg = _load_conditions_and_tasks()
    condition_key = next(
        (k for k in conditions if conditions[k].get("id") == condition_id),
        None,
    )
    if condition_key is None:
        raise ValueError(f"Unknown condition_id: {condition_id}")

    task = next((item for item in tasks_cfg["tasks"] if item["id"] == task_id), tasks_cfg["tasks"][0])
    success_value = 1.0 if seed % 2 == 0 else 0.0
    run_metrics = {
        "success": success_value,
        "mean_risk": 0.18 + (0.08 * len(condition_id)),
        "max_risk": 0.48 + (0.06 * len(task_id)),
        "steps": 3,
    }

    file_path = _write_run_csv(condition_id, seed, task_id, run_metrics)
    result = {
        "condition_id": condition_id,
        "seed": seed,
        "task_id": task_id,
        "task": task,
        "condition": conditions[condition_key],
        "result": {
            "status": "simulated",
            "message": f"Condition {condition_id} ran with seed {seed} on {task_id}.",
            "metrics": run_metrics,
            "csv_path": str(file_path),
        },
    }
    return result


@app.get("/results")
async def get_results():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    run_metrics = {}
    for path in sorted(LOG_DIR.glob("*.csv")):
        rows = load_log(str(path))
        metrics = compute_basic_metrics(rows)
        run_id = path.stem
        run_metrics[run_id] = metrics

    summary = aggregate_by_condition(run_metrics)
    chart_rows = [{"condition": cond, "success": values.get("success", 0.0), "mean_risk": values.get("mean_risk", 0.0)} for cond, values in summary.items()]
    return {"summary": summary, "chart_rows": chart_rows, "files": [p.name for p in sorted(LOG_DIR.glob("*.csv"))]}


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    return """
    <html>
      <head>
        <title>Embodied Cybernetic Agency</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
          body { font-family: Arial, sans-serif; margin: 2rem; background: #0f172a; color: #e2e8f0; }
          .container { max-width: 980px; margin: 0 auto; }
          .card { background: #111827; border-radius: 12px; padding: 1.25rem; margin-top: 1rem; }
          .metrics { display: flex; gap: 1rem; flex-wrap: wrap; }
          .pill { background: #1e293b; border-radius: 8px; padding: 0.75rem 1rem; min-width: 140px; }
          form { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; }
          label { display: block; font-size: 0.9rem; color: #cbd5e1; margin-bottom: 0.35rem; }
          input, select, button { width: 100%; padding: 0.7rem 0.8rem; border-radius: 8px; border: 1px solid #334155; background: #0f172a; color: #e2e8f0; }
          button { background: #2563eb; border: none; cursor: pointer; font-weight: bold; }
          a { color: #7dd3fc; }
          canvas { background: #0b1220; border-radius: 12px; }
          pre { white-space: pre-wrap; }
        </style>
      </head>
      <body>
        <div class="container">
          <h1>Embodied Cybernetic Agency</h1>
          <div class="card">
            <div class="metrics">
              <div class="pill" id="status-pill">Status: Online</div>
              <div class="pill"><a href="/health">Health</a></div>
              <div class="pill"><a href="/config">Configuration</a></div>
              <div class="pill"><a href="/simulate">Simulation</a></div>
            </div>
          </div>

          <div class="card">
            <h2>Run experiment</h2>
            <form id="experiment-form">
              <div>
                <label for="condition_id">Condition</label>
                <select id="condition_id" name="condition_id">
                  <option value="A">A</option>
                  <option value="B">B</option>
                  <option value="C">C</option>
                  <option value="D">D</option>
                </select>
              </div>
              <div>
                <label for="seed">Seed</label>
                <input id="seed" name="seed" type="number" value="42" min="1" max="999" />
              </div>
              <div>
                <label for="task_id">Task</label>
                <select id="task_id" name="task_id">
                  <option value="task_1">Task 1</option>
                  <option value="task_2">Task 2</option>
                  <option value="task_3">Task 3</option>
                </select>
              </div>
              <div style="display:flex;align-items:end;">
                <button type="submit">Run experiment</button>
              </div>
            </form>
          </div>

          <div class="card">
            <canvas id="riskChart" height="120"></canvas>
          </div>
          <div class="card">
            <pre id="results"></pre>
          </div>
        </div>
        <script>
          async function loadSummary() {
            const response = await fetch('/results');
            const data = await response.json();
            const labels = (data.chart_rows || []).map(row => row.condition);
            const risks = (data.chart_rows || []).map(row => Number(row.mean_risk || 0));
            const successes = (data.chart_rows || []).map(row => Number(row.success || 0));

            document.getElementById('results').textContent = JSON.stringify(data, null, 2);

            if (window.riskChartInstance) {
              window.riskChartInstance.destroy();
            }

            window.riskChartInstance = new Chart(document.getElementById('riskChart'), {
              type: 'bar',
              data: {
                labels: labels,
                datasets: [
                  { label: 'Mean Risk', data: risks, backgroundColor: '#38bdf8' },
                  { label: 'Success', data: successes, backgroundColor: '#34d399' }
                ]
              },
              options: { responsive: true, scales: { y: { beginAtZero: true, max: 1.2 } } }
            });
          }

          document.getElementById('experiment-form').addEventListener('submit', async function (event) {
            event.preventDefault();
            const formData = new FormData(event.target);
            const params = new URLSearchParams(formData);
            const response = await fetch('/experiments/run', {
              method: 'POST',
              headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
              body: params.toString()
            });
            const payload = await response.json();
            document.getElementById('results').textContent = JSON.stringify(payload, null, 2);
            await loadSummary();
          });

          loadSummary();
        </script>
      </body>
    </html>
    """


def run_demo():
    print("Executing Audit Simulation Mode...\n")
    ambient_jitter = np.array([
        [0.78, 0.11, 0.11],
        [0.49, 0.41, 0.10],
        [0.89, 0.06, 0.05],
    ])
    systemic_trauma = np.array([
        [0.10, 0.10, 0.80],
        [0.40, 0.40, 0.20],
        [0.30, 0.35, 0.35],
    ])

    print(">>> Injecting Ambient Environmental Jitter:")
    print(engine.execute_audited_clock_cycle(ambient_jitter))
    print("\n>>> Injecting Severe Systemic Trauma:")
    print(engine.execute_audited_clock_cycle(systemic_trauma))


if __name__ == "__main__":
    run_demo()
