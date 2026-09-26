# src/run_experiments.py

import csv
import os
import random
from collections import deque

import yaml

from src.agent import Agent
from src.disturbances import build_disturbance_schedule
from src.environment import GridWorld
from src.metrics import compute_basic_metrics, load_log

CONFIG_DIR = os.path.join(os.path.dirname(__file__), "..", "config")
LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs", "raw")


def load_yaml(name):
    path = os.path.join(CONFIG_DIR, name)
    with open(path, "r", encoding="utf-8") as config_file:
        return yaml.safe_load(config_file)


def ensure_log_dir():
    os.makedirs(LOG_DIR, exist_ok=True)


def _next_action(environment):
    start = tuple(environment.pos)
    goal = tuple(environment.goal)
    if start == goal:
        return None

    directions = (
        ("up", (0, 1)),
        ("right", (1, 0)),
        ("down", (0, -1)),
        ("left", (-1, 0)),
    )
    queue = deque([start])
    previous = {start: None}

    while queue:
        x, y = queue.popleft()
        for action, (dx, dy) in directions:
            position = (x + dx, y + dy)
            if (
                position in previous
                or not 0 <= position[0] < environment.width
                or not 0 <= position[1] < environment.height
                or position in environment.obstacles
            ):
                continue
            previous[position] = ((x, y), action)
            if position == goal:
                queue.clear()
                break
            queue.append(position)

    if goal not in previous:
        return None

    position = goal
    while previous[position][0] != start:
        position = previous[position][0]
    return previous[position][1]


def _substrate_input(environment):
    if environment.sensor_blackout:
        return [0.0, 0.0, 1.0]

    noise = max(0.0, min(1.0, environment.sensor_noise_level))
    return [0.6 * (1.0 - noise), 0.3 + 0.6 * noise, 0.1]


def run_single_experiment(condition_id, seed, scenario_id="scenario_1", task_id="task_1"):
    random.seed(seed)

    conditions_cfg = load_yaml("conditions.yaml")["conditions"]
    condition_cfg = next(
        (cfg for cfg in conditions_cfg.values() if cfg["id"] == condition_id),
        None,
    )
    if condition_cfg is None:
        raise ValueError(f"Unknown condition_id: {condition_id}")

    scenario_cfg = load_yaml(f"disturbances_{scenario_id}.yaml")
    tasks_cfg = load_yaml("tasks_gridworld.yaml")
    task_cfg = next(
        (task for task in tasks_cfg["tasks"] if task["id"] == task_id),
        None,
    )
    if task_cfg is None:
        raise ValueError(f"Unknown task_id: {task_id}")

    environment = GridWorld(tasks_cfg["world"], task_cfg)
    agent = Agent(condition_cfg)
    disturbance_schedule = build_disturbance_schedule(scenario_cfg)
    max_steps = min(
        task_cfg["max_steps"],
        scenario_cfg.get("time_horizon", task_cfg["max_steps"]),
    )
    max_distance = max(1.0, (environment.width**2 + environment.height**2) ** 0.5)
    rows = []

    for step in range(1, max_steps + 1):
        disturbance = disturbance_schedule.get(step)
        if disturbance is not None:
            environment.apply_disturbance(disturbance.to_dict())
            if disturbance.kind == "battery_drain" and agent.telemetry is not None:
                agent.telemetry.battery = max(
                    0.0, agent.telemetry.battery - disturbance.magnitude
                )
            elif disturbance.kind == "thermal_limit":
                if agent.telemetry is not None:
                    agent.telemetry.temperature = min(
                        1.0, agent.telemetry.temperature + disturbance.magnitude
                    )
                if agent.substrate_engine is not None:
                    agent.substrate_engine.core_temperature_celsius += (
                        disturbance.magnitude * 15.0
                    )

        observation = environment.observe()
        prediction_error = agent.compute_error(observation)
        normalized_error = min(1.0, prediction_error / max_distance)
        agent.update_world_model(observation)

        uncertainty = (
            1.0
            if environment.sensor_blackout
            else min(1.0, environment.sensor_noise_level)
        )
        agent.update_substrate(step, _substrate_input(environment))
        resource_integrity = agent.resource_integrity()
        risk = agent.compute_risk(
            normalized_error,
            uncertainty,
            resource_integrity,
        )
        agent.update_self_model(normalized_error, resource_integrity)
        mode = agent.choose_mode(
            risk,
            resource_integrity=resource_integrity,
            error=normalized_error,
        )
        effort = agent.act(mode)

        latency_spike = disturbance is not None and disturbance.kind == "latency_spike"
        if mode != "shutdown" and not environment.done:
            environment.step(None if latency_spike else _next_action(environment))

        substrate = agent.substrate_engine
        rows.append(
            {
                "step": step,
                "disturbance": disturbance.kind if disturbance else "none",
                "obs": observation,
                "prediction_error": normalized_error,
                "risk": risk,
                "mode": mode,
                "effort": effort,
                "battery": agent.telemetry.battery if agent.telemetry else "",
                "temperature": agent.telemetry.temperature if agent.telemetry else "",
                "substrate_stress": substrate.last_stress if substrate else "",
                "substrate_temperature_celsius": (
                    substrate.core_temperature_celsius if substrate else ""
                ),
                "substrate_state": substrate.somatic_state if substrate else "",
                "collisions": environment.collisions,
                "success": int(environment.success),
            }
        )

        if environment.done or mode == "shutdown":
            break

    log_filename = f"condition_{condition_id}_seed_{seed:03d}_{task_id}.csv"
    log_path = os.path.join(LOG_DIR, log_filename)
    ensure_log_dir()
    fieldnames = [
        "step",
        "disturbance",
        "obs",
        "prediction_error",
        "risk",
        "mode",
        "effort",
        "battery",
        "temperature",
        "substrate_stress",
        "substrate_temperature_celsius",
        "substrate_state",
        "collisions",
        "success",
    ]
    with open(log_path, "w", newline="", encoding="utf-8") as log_file:
        writer = csv.DictWriter(log_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    metrics = compute_basic_metrics(load_log(log_path))
    print(f"[INFO] Wrote {len(rows)} simulation steps: {log_path}")
    return metrics


def run_all():
    ensure_log_dir()

    seeds = load_yaml("seeds_default.yaml")["seeds"]["main"]
    condition_ids = [
        cfg["id"] for cfg in load_yaml("conditions.yaml")["conditions"].values()
    ]
    task_ids = [task["id"] for task in load_yaml("tasks_gridworld.yaml")["tasks"]]

    for condition_id in condition_ids:
        for seed in seeds:
            for task_id in task_ids:
                run_single_experiment(
                    condition_id=condition_id,
                    seed=seed,
                    task_id=task_id,
                )


if __name__ == "__main__":
    run_all()