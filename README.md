# Embodied Cybernetic Agency

A small research simulator for comparing rule-based agents under changing and unreliable conditions. Agents predict observations, track simulated resources, estimate risk, and change their behavior when risk increases.

This repository contains a FastAPI service, two related agent simulations, a configurable GridWorld experiment runner, and scripts for summarizing experiment results.

## What It Does

### GridWorld experiments

`src/run_experiments.py` runs agents through small grid tasks. A basic breadth-first-search policy navigates around obstacles while configured disturbances can add sensor noise, cause a sensor blackout, shift the goal, or weaken controls. Each run writes a step-by-step CSV file under `logs/raw/`.

The four conditions in `config/conditions.yaml` compare different agent components:

- **A:** reactive baseline without a world model, resource telemetry, or self-model.
- **B:** adds a prediction-based world model.
- **C:** adds simulated battery and temperature tracking.
- **D:** adds a self-model, risk-based regulation, and simulated substrate stress monitoring. A substrate freeze makes the agent shut down.

### Agent simulation

`app.py` contains a separate scalar-state simulation with noisy observations, world changes, and blackouts. Its agent tracks prediction error, uncertainty, risk, battery, and temperature. It also includes in-memory episodic memory, similarity matching, and a global workspace that selects the most salient signal.

Run it directly to print a 30-step trace:

```bash
python app.py
```

The FastAPI route `POST /agent/simulate` runs this simulation and returns a JSON summary and per-step trace.

### Audited substrate demo

`POST /simulate` runs two fixed sensor-distribution examples through an information-stress calculation. It reports simulated substrate temperatures and whether the stress checks pass. It is separate from both the GridWorld experiment and the `app.py` agent simulation.

## Install And Run

`requirements.txt` notes Python 3.10 or later, but this minimum is not enforced by package metadata. The workspace has been tested with Python 3.14.2. Create an environment and install the dependencies:

```bash
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Start the API from the repository root:

```bash
.venv/bin/python -m uvicorn main:app --reload
```

Open `http://127.0.0.1:8000/docs` for interactive API documentation.

Run all configured GridWorld experiments (4 conditions, 5 seeds, 3 tasks):

```bash
.venv/bin/python -m src.run_experiments
```

Summarize the CSV logs and regenerate the figures and table:

```bash
.venv/bin/python scripts/recompute_metrics.py
.venv/bin/python scripts/regenerate_figures.py
```

Run the tests:

```bash
.venv/bin/python -m pytest -q
```

See [report/USAGE.md](report/USAGE.md) for additional usage details.

## API Endpoints

- `GET /health` checks that the service is running.
- `GET /config` returns the configured conditions, tasks, and world.
- `GET /simulate` runs the audited substrate demo.
- `POST /agent/simulate?steps=30&seed=42` runs the `app.py` agent simulation. Steps must be between 1 and 500.
- `POST /experiments/run?condition_id=D&seed=42&task_id=task_1` runs one GridWorld experiment. `condition_id` is required; seed and task have defaults.
- `GET /results` summarizes CSV files in `logs/raw/`.
- `GET /dashboard` serves a small HTML dashboard.

## Versions And Requirements

- FastAPI application metadata version: **0.1.0**.
- Android Buildozer configuration version: **0.1**; it targets Android API 33 with minimum API 21. Android packaging is a separate configuration and is not covered by the Python test suite.
- Python: `requirements.txt` notes **3.10 or later**; this is not enforced by package metadata. The current workspace runtime is **3.14.2**.
- Main dependencies: FastAPI, Uvicorn, NumPy, SciPy, PyYAML, jsonschema, pandas, matplotlib, and pytest. Minimum versions are listed in [requirements.txt](requirements.txt); versions are not pinned in a lockfile.

## Scope And Limitations

- This is a rule-based research prototype, not a trained language model or a production robot controller.
- GridWorld movement and hardware telemetry are simulated; no physical sensors or hardware are accessed.
- The GridWorld runner uses a simple pathfinding policy. The experiments compare the configured risk and resource-monitoring behavior, not learned navigation.
- The scalar simulation in `app.py`, the audited `/simulate` demo, and the GridWorld runner are separate simulation paths; only the API exposes them together as routes.
