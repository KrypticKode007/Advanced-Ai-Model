# src/run_experiments.py

import os
import random
import yaml

# Later you'll import your real classes:
# from agent import Agent
# from environment import Environment

CONFIG_DIR = os.path.join(os.path.dirname(__file__), "..", "config")
LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs", "raw")


def load_yaml(name):
    path = os.path.join(CONFIG_DIR, name)
    with open(path, "r") as f:
        return yaml.safe_load(f)


def ensure_log_dir():
    os.makedirs(LOG_DIR, exist_ok=True)


def run_single_experiment(condition_id, seed, scenario_id="scenario_1", task_id="task_1"):
    random.seed(seed)

    # Load configs
    conditions_cfg = load_yaml("conditions.yaml")["conditions"]
    condition_cfg = None
    for key, cfg in conditions_cfg.items():
        if cfg["id"] == condition_id:
            condition_cfg = cfg
            break
    if condition_cfg is None:
        raise ValueError(f"Unknown condition_id: {condition_id}")

    disturbances_cfg = load_yaml("disturbances_scenario_1.yaml")
    seeds_cfg = load_yaml("seeds_default.yaml")
    tasks_cfg = load_yaml("tasks_gridworld.yaml")

    # TODO: create Environment and Agent using these configs
    # env = Environment(tasks_cfg, scenario_id=scenario_id)
    # agent = Agent(condition_cfg)

    log_filename = f"condition_{condition_id}_seed_{seed:03d}.csv"
    log_path = os.path.join(LOG_DIR, log_filename)

    # For now, just write a placeholder header so the file exists
    ensure_log_dir()
    with open(log_path, "w") as f:
        f.write("step,disturbance,obs,prediction_error,risk,mode,battery,temperature,success\n")
        # TODO: run the real simulation loop and append rows here

    print(f"[INFO] Wrote placeholder log: {log_path}")


def run_all():
    ensure_log_dir()

    seeds_cfg = load_yaml("seeds_default.yaml")
    seeds = seeds_cfg["seeds"]["main"]

    condition_ids = ["A", "B", "C", "D"]

    for cond in condition_ids:
        for s in seeds:
            run_single_experiment(condition_id=cond, seed=s)


if __name__ == "__main__":
    run_all()