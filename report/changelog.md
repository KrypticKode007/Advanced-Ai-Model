# Changelog

Version history for the **Theory of Embodied Cybernetic Agency and Structural Failure** project.

---

## v1.0 — Initial conceptual and experimental proposal  
**Date:** 2026-09-17  
**Author:** Brandon Mark Wilson

### Summary

- Defined a unified architecture for embodied, failure-aware agents with:
  1. World model  
  2. Interoceptive model  
  3. Action controller  
  4. Metacognitive self-model  
  5. Regulation and recovery

- Introduced:
  - Structural-risk index $R_t = w_e e_t + w_u u_t + w_r (1 - r_t) + w_m (1 - m_t)$  
  - Failure taxonomy (belief persistence, resource-triggered inhibition, actuator-model mismatch, self-model/action-attribution mismatch, maladaptive loops)
  - Experimental comparison of conditions A–D.

### Code and configuration

- Added core source files in `src/`:
  - `agent.py`, `environment.py`, `disturbances.py`, `metrics.py`, `run_experiments.py`.

- Added configs in `config/`:
  - `conditions.yaml`, `tasks_gridworld.yaml`,
    `disturbances_scenario_1.yaml`, `seeds_default.yaml`.

- Defined logging and results structure:
  - `logs/raw/`, `logs/aggregated/`, `results/figures/`, `results/tables/`.

### Reporting and reproducibility

- Created initial report artifacts:
  - `report/paper.md`
  - `report/appendix_metrics.md`
  - `report/reproducibility.md`

- Added scripts:
  - `scripts/recompute_metrics.py`
  - `scripts/regenerate_figures.py`

---

## Planned next version (v1.1)

Planned changes (not yet implemented):

- Implement full simulation loop in `run_experiments.py`:
  - condition-aware agent instantiation
  - disturbance scheduling
  - per-step logging of risk and mode transitions.

- Extend metrics to:
  - calibration curves,
  - failure-source attribution accuracy,
  - recovery success rate by disturbance type.

- Add additional figures:
  - risk over time,
  - mode-switch frequencies,
  - recovery latency distributions.