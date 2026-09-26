# Usage Guide

This document explains how to **run, inspect, and extend** the embodied cybernetic agent experiments.

---

## 1. Running the default experiment suite

From the project root:

```bash
python -m src.run_experiments
```

## 2. Running the API

From the project root, start the FastAPI server:

```bash
python -m uvicorn main:app --reload
```

Open `http://127.0.0.1:8000/docs` to explore the endpoints. To run the agent simulation from `app.py` through the API:

```bash
curl -X POST "http://127.0.0.1:8000/agent/simulate?steps=30&seed=42"
```

The response includes a summary and a per-step trace. The grid-world experiment endpoint remains available at `/experiments/run`.