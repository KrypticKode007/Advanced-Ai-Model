# Reproducibility Guide

This document describes how to **reproduce all experiments and results** for the
*Theory of Embodied Cybernetic Agency and Structural Failure* project.

---

## 1. Environment setup

1. Create a fresh Python environment (e.g., with `venv` or Conda).
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Confirm you can import the project code:

   ```bash
   python -c "import src.agent, src.environment, src.metrics"
   ```

---

## 2. Experimental configuration

All high-level configuration lives in the `config/` directory:

- `config/conditions.yaml`  
  Defines experimental conditions A–D (world model, telemetry, self-model, regulation mode).

- `config/tasks_gridworld.yaml`  
  Defines grid size, obstacles, hazard zones, and tasks.

- `config/disturbances_scenario_1.yaml`  
  Defines the time-indexed disturbance schedule for `scenario_1`.

- `config/seeds_default.yaml`  
  Defines random seeds for `small`, `main`, and `stress` batches.

These files should not be changed for the main reported results. Any changes
must be documented explicitly in the report or appendix.

---

## 3. Running experiments

To reproduce the main batch of runs (conditions A–D × main seeds):

```bash
python -m src.run_experiments