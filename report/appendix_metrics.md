# Appendix: Metrics and Evaluation Details

This appendix documents the **metrics**, their **formal definitions**, and how
they are computed from the raw logs in `logs/raw/`.

---

## 1. Per-step log schema

Each run produces a CSV file:

```text
logs/raw/condition_<ID>_seed_<NNN>.csv