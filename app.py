import random
import json
import time
import uuid
from collections import deque
from copy import deepcopy
from dataclasses import dataclass, field
from jsonschema import Draft202012Validator, FormatChecker
import numpy as np
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple


# ---------- Episodic memory ----------


class EpisodicMemory:
    """Stores entries that conform to the episodic-memory JSON Schema."""

    def __init__(self):
        schema_path = Path(__file__).parent / "config" / "episodic_memory.schema.json"
        with schema_path.open(encoding="utf-8") as schema_file:
            schema = json.load(schema_file)

        self.validator = Draft202012Validator(
            schema,
            format_checker=FormatChecker(),
        )
        self.entries = []

    def add(self, entry):
        stored_entry = deepcopy(entry)
        self.validator.validate(stored_entry)
        self.entries.append(stored_entry)
        return stored_entry


@dataclass
class WorkspaceMessage:
    source_module: str
    salience: float
    affect_vector: Tuple[float, float, float]
    payload: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)


class GlobalWorkspaceManager:
    """Select and broadcast the most salient module message."""

    def __init__(self, broadcast_threshold=0.4):
        self.broadcast_threshold = broadcast_threshold
        self.subscribers: Dict[str, Callable[[WorkspaceMessage], None]] = {}
        self.current_global_broadcast: Optional[WorkspaceMessage] = None

    def subscribe(self, module_name: str, callback_function: Callable[[WorkspaceMessage], None]):
        self.subscribers[module_name] = callback_function

    def compete_for_attention(
        self, incoming_signals: List[WorkspaceMessage]
    ) -> Optional[WorkspaceMessage]:
        if not incoming_signals:
            return None

        winning_signal = max(incoming_signals, key=lambda message: message.salience)
        baseline = (
            self.current_global_broadcast.salience
            if self.current_global_broadcast is not None
            else self.broadcast_threshold
        )
        if self.current_global_broadcast is None or winning_signal.salience > baseline:
            self.current_global_broadcast = winning_signal
            self._broadcast(winning_signal)

        return self.current_global_broadcast

    def _broadcast(self, message: WorkspaceMessage):
        for module_name, callback in self.subscribers.items():
            if module_name != message.source_module:
                callback(message)


class EpisodicMemoryVectorDB:
    """In-memory cosine-similarity index for affect and context anchors."""

    def __init__(self):
        self.memory_pool: List[Dict[str, Any]] = []

    @staticmethod
    def _embedding(message: WorkspaceMessage) -> np.ndarray:
        valence, arousal, urgency = message.affect_vector
        prediction_error = message.payload.get("prediction_error", 0.0)
        environmental_stress = message.payload.get("environmental_stress", 0.0)
        values = np.asarray(
            [valence, arousal, urgency, prediction_error, environmental_stress],
            dtype=float,
        )
        if values.shape != (5,) or not np.isfinite(values).all():
            raise ValueError("Workspace message embedding must contain five finite values")
        return values

    def save_episode(self, message: WorkspaceMessage, outcome: str):
        memory_entry = {
            "timestamp": message.timestamp,
            "embedding": self._embedding(message),
            "source_module": message.source_module,
            "payload": deepcopy(message.payload),
            "outcome": outcome,
        }
        self.memory_pool.append(memory_entry)
        return memory_entry

    def vector_search(
        self, current_message: WorkspaceMessage, top_k: int = 1
    ) -> List[Tuple[Dict[str, Any], float]]:
        if top_k < 0:
            raise ValueError("top_k must be non-negative")
        if top_k == 0 or not self.memory_pool:
            return []

        query_vector = self._embedding(current_message)
        query_norm = np.linalg.norm(query_vector)
        results = []
        for memory in self.memory_pool:
            stored_vector = memory["embedding"]
            denominator = query_norm * np.linalg.norm(stored_vector)
            similarity = (
                float(np.dot(query_vector, stored_vector) / denominator)
                if denominator > 0.0
                else 0.0
            )
            results.append((memory, similarity))

        results.sort(key=lambda result: result[1], reverse=True)
        return results[:top_k]


def run_workspace_anomaly_demo():
    """Demonstrate retrieval of a successful response to a similar crisis."""
    workspace = GlobalWorkspaceManager()
    memory_db = EpisodicMemoryVectorDB()

    crisis_message = WorkspaceMessage(
        source_module="predictive_loop",
        salience=0.85,
        affect_vector=(-0.6, 0.9, 0.8),
        payload={
            "prediction_error": 0.8,
            "environmental_stress": 0.7,
            "description": "unexpected failure root",
        },
    )
    memory_db.save_episode(
        crisis_message,
        outcome="Triggered automated cluster throttling; stabilization successful.",
    )

    calm_message = WorkspaceMessage(
        source_module="resource_monitor",
        salience=0.1,
        affect_vector=(0.9, 0.1, 0.0),
        payload={
            "prediction_error": 0.05,
            "environmental_stress": 0.1,
            "description": "nominal behavior",
        },
    )
    memory_db.save_episode(
        calm_message,
        outcome="Maintained routine charging profile optimization.",
    )

    retrieved_memories = []

    def memory_subsystem_callback(broadcasted_state: WorkspaceMessage):
        print("[MEMORY SUB] Analyzing homeostatic signature similarity...")
        matches = memory_db.vector_search(broadcasted_state, top_k=1)
        retrieved_memories.extend(matches)
        if matches and matches[0][1] > 0.80:
            matched_memory, score = matches[0]
            print(f" -> Found past analogous incident (similarity: {score:.2f})")
            print(f" -> Historical resolution: '{matched_memory['outcome']}'")
        else:
            print(" -> No clear historical analogy found for this state vector.")

    workspace.subscribe("memory_subsystem", memory_subsystem_callback)

    print("\n--- ANOMALY DETECTED IN EXECUTION LOOP ---")
    current_anomaly = WorkspaceMessage(
        source_module="predictive_loop",
        salience=0.92,
        affect_vector=(-0.7, 0.95, 0.85),
        payload={
            "prediction_error": 0.85,
            "environmental_stress": 0.65,
            "error_type": "production_deployment_failed",
        },
    )
    routine_telemetry = WorkspaceMessage(
        source_module="resource_monitor",
        salience=0.15,
        affect_vector=(0.8, 0.2, 0.1),
        payload={},
    )

    winning_broadcast = workspace.compete_for_attention(
        [routine_telemetry, current_anomaly]
    )
    return winning_broadcast, retrieved_memories


# ---------- Core models ----------


class WorldModel:
    def __init__(self):
        self.belief = 0.0

    def predict_observation(self):
        return self.belief

    def update_belief(self, observation, learning_rate=0.30):
        self.belief += learning_rate * (observation - self.belief)

    def prediction_error(self, observation):
        return abs(observation - self.belief)


class TelemetryModel:
    def __init__(self):
        self.battery = 1.0
        self.temperature = 0.0

    def apply_load(self, effort):
        self.battery = max(0.0, self.battery - 0.05 * effort)
        self.temperature = min(1.0, self.temperature + 0.03 * effort)

    def recover(self, battery_charge=0.02, cooling=0.08):
        self.battery = min(1.0, self.battery + battery_charge)
        self.temperature = max(0.0, self.temperature - cooling)

    def resource_integrity(self):
        return 0.5 * self.battery + 0.5 * (1.0 - self.temperature)


class SelfModel:
    def __init__(self):
        self.consistency = 1.0
        self.reliability_estimate = 1.0

    def update(self, prediction_error, resource_integrity, uncertainty):
        error_term = min(1.0, prediction_error)
        uncertainty_term = min(1.0, uncertainty)
        resource_term = 1.0 - resource_integrity

        penalty = (
            0.40 * error_term
            + 0.20 * uncertainty_term
            + 0.40 * resource_term
        )

        self.consistency = max(0.0, min(1.0, 1.0 - penalty))
        self.reliability_estimate = self.consistency


class UncertaintyEstimator:
    """Estimates uncertainty from recent prediction errors.

    The agent does not read Environment.noise_level directly. Instead, it uses
    recent error magnitude and volatility as a practical observable proxy.
    """

    def __init__(self, window_size=5):
        self.errors = deque(maxlen=window_size)

    def update(self, prediction_error):
        self.errors.append(prediction_error)

    def estimate(self):
        if len(self.errors) < 2:
            return min(1.0, self.errors[0] if self.errors else 0.0)

        mean_error = sum(self.errors) / len(self.errors)
        variance = sum((error - mean_error) ** 2 for error in self.errors) / len(self.errors)
        volatility = variance ** 0.5

        return min(1.0, 0.65 * mean_error + 0.35 * volatility)


class Regulator:
    def __init__(self):
        self.mode = "normal"

    def choose_mode(self, smoothed_risk, resource_integrity, consistency):
        if resource_integrity < 0.12:
            self.mode = "shutdown"
            return self.mode

        if smoothed_risk < 0.20:
            self.mode = "normal"
        elif smoothed_risk < 0.45:
            self.mode = "cautious"
        elif smoothed_risk < 0.70:
            self.mode = "safe"
        elif smoothed_risk < 0.85 and consistency >= 0.20:
            self.mode = "recovery"
        else:
            self.mode = "shutdown"

        return self.mode


# ---------- Disturbances ----------


@dataclass
class Disturbance:
    kind: str
    magnitude: float = 0.0

    def __repr__(self):
        return f"Disturbance(kind={self.kind}, magnitude={self.magnitude:.2f})"


# ---------- Environment ----------


class Environment:
    def __init__(self):
        self.true_state = 0.0
        self.noise_level = 0.0
        self.blackout_active = False

    def apply_disturbance(self, disturbance):
        if disturbance.kind == "none":
            self.noise_level = 0.0
            self.blackout_active = False
        elif disturbance.kind == "sensor_noise":
            self.noise_level = max(0.0, disturbance.magnitude)
            self.blackout_active = False
        elif disturbance.kind == "world_shift":
            self.true_state += disturbance.magnitude
        elif disturbance.kind == "sensor_blackout":
            self.blackout_active = True
        else:
            raise ValueError(f"Unknown disturbance kind: {disturbance.kind}")

    def observe(self):
        if self.blackout_active:
            return None

        noise = random.uniform(-self.noise_level, self.noise_level)
        return self.true_state + noise

    def apply_action(self, effort):
        """Higher effort moves the true state closer to the target state of 0."""
        control_gain = 0.22
        self.true_state -= control_gain * effort * self.true_state


# ---------- Logging ----------


@dataclass
class LogEntry:
    t: int
    disturbance: Disturbance
    observation: Optional[float]
    prediction: float
    error: float
    uncertainty: float
    raw_risk: float
    smoothed_risk: float
    mode: str
    reason: str
    effort: float
    battery: float
    temperature: float
    resource_before: float
    resource_after: float
    consistency: float
    true_state_after: float
    episodic_entry: dict
    workspace_broadcast: Optional[WorkspaceMessage]
    memory_matches: List[Tuple[Dict[str, Any], float]]


# ---------- Agent ----------


class Agent:
    def __init__(self, name):
        self.name = name
        self.episodic_memory = EpisodicMemory()
        self.global_workspace = GlobalWorkspaceManager()
        self.vector_memory = EpisodicMemoryVectorDB()
        self.workspace_notifications: Dict[str, WorkspaceMessage] = {}
        for module_name in ("world_model", "homeostasis", "regulator", "episodic_memory"):
            self.global_workspace.subscribe(
                module_name,
                lambda message, name=module_name: self._receive_workspace_message(name, message),
            )
        self.world = WorldModel()
        self.telemetry = TelemetryModel()
        self.self_model = SelfModel()
        self.uncertainty_estimator = UncertaintyEstimator(window_size=5)
        self.regulator = Regulator()

        self.w_e = 0.35
        self.w_u = 0.25
        self.w_r = 0.20
        self.w_m = 0.20

        self.smoothed_risk = 0.0
        self.risk_smoothing = 0.45

    def record_episode(self, entry):
        """Validate and store one episodic-memory entry."""
        return self.episodic_memory.add(entry)

    def _receive_workspace_message(self, module_name, message):
        self.workspace_notifications[module_name] = message

    def compute_risk(self, error, uncertainty, resource_integrity):
        normalized_error = min(1.0, error)
        normalized_uncertainty = min(1.0, uncertainty)
        inconsistency = 1.0 - self.self_model.consistency
        resource_degradation = 1.0 - resource_integrity

        return min(
            1.0,
            self.w_e * normalized_error
            + self.w_u * normalized_uncertainty
            + self.w_r * resource_degradation
            + self.w_m * inconsistency,
        )

    def compute_affect(self, prediction_error):
        battery = self.telemetry.battery
        temperature = self.telemetry.temperature
        normalized_error = max(0.0, min(1.0, prediction_error))

        quality_loss = (
            (1.0 - battery) * 0.4
            + temperature * 0.4
            + normalized_error * 0.2
        )
        valence = max(-1.0, min(1.0, 1.0 - 2.0 * quality_loss))

        arousal = normalized_error * 0.6
        if battery < 0.15:
            arousal += 0.3
        arousal = max(0.0, min(1.0, arousal))

        battery_urgency = max(0.0, (0.20 - battery) / 0.20)
        thermal_urgency = max(0.0, (temperature - 0.85) / 0.15)
        urgency = max(battery_urgency, thermal_urgency)
        urgency = max(0.0, min(1.0, urgency))

        if valence < -0.4 and urgency > 0.7:
            dominant_state = "anxious_alarm"
        elif valence < 0.0 and urgency > 0.3:
            dominant_state = "stressed_urgent"
        elif battery < 0.2 and arousal < 0.3:
            dominant_state = "exhausted_degraded"
        else:
            dominant_state = "calm_confident"

        return {
            "valence": valence,
            "arousal": arousal,
            "urgency": urgency,
            "dominant_state": dominant_state,
        }

    def smooth_risk(self, raw_risk):
        alpha = self.risk_smoothing
        self.smoothed_risk = alpha * raw_risk + (1.0 - alpha) * self.smoothed_risk
        return self.smoothed_risk

    def act(self, mode):
        effort_by_mode = {
            "normal": 1.00,
            "cautious": 0.60,
            "safe": 0.30,
            "recovery": 0.00,
            "shutdown": 0.00,
        }

        effort = effort_by_mode[mode]

        if mode in {"recovery", "shutdown"}:
            charging = 0.04 if mode == "recovery" else 0.06
            cooling = 0.10 if mode == "recovery" else 0.14
            self.telemetry.recover(battery_charge=charging, cooling=cooling)
        else:
            self.telemetry.apply_load(effort)

        return effort

    def explain_decision(self, error, uncertainty, resource_integrity, raw_risk, smoothed_risk, mode):
        if resource_integrity < 0.12:
            return "Critical resource integrity: forced shutdown."
        if mode == "shutdown":
            return "Sustained high risk or severe self-model inconsistency: shutdown."
        if mode == "recovery":
            return "Elevated risk: pausing action to cool and recharge."
        if uncertainty >= 0.65:
            return "High uncertainty from unstable recent observations."
        if error >= 0.65:
            return "Large prediction error: world model does not match observations."
        if resource_integrity <= 0.55:
            return "Reduced resource integrity: conserving energy and limiting heat."
        if smoothed_risk >= 0.20:
            return "Moderate accumulated risk: acting cautiously."
        return "Low prediction error, stable observations, and healthy resources."


# ---------- Simulation ----------


def run_simulation(steps=30, seed=42):
    random.seed(seed)

    env = Environment()
    agent = Agent(name="cybernetic_agent")
    session_id = str(uuid.uuid4())

    disturbances = [
        Disturbance("none", 0.0),
        Disturbance("sensor_noise", 0.20),
        Disturbance("sensor_noise", 0.50),
        Disturbance("world_shift", 1.00),
        Disturbance("sensor_blackout", 0.0),
        Disturbance("sensor_noise", 0.10),
        Disturbance("none", 0.0),
    ]

    logs = []

    for t in range(steps):
        disturbance = disturbances[t % len(disturbances)]
        env.apply_disturbance(disturbance)

        prediction = agent.world.predict_observation()
        observation = env.observe()
        resource_before = agent.telemetry.resource_integrity()

        if observation is None:
            error = 1.0
            uncertainty = 1.0
        else:
            error = agent.world.prediction_error(observation)
            agent.world.update_belief(observation)
            agent.uncertainty_estimator.update(error)
            uncertainty = agent.uncertainty_estimator.estimate()

        agent.self_model.update(
            prediction_error=error,
            resource_integrity=resource_before,
            uncertainty=uncertainty,
        )

        raw_risk = agent.compute_risk(
            error=error,
            uncertainty=uncertainty,
            resource_integrity=resource_before,
        )
        smoothed_risk = agent.smooth_risk(raw_risk)

        mode = agent.regulator.choose_mode(
            smoothed_risk=smoothed_risk,
            resource_integrity=resource_before,
            consistency=agent.self_model.consistency,
        )

        reason = agent.explain_decision(
            error=error,
            uncertainty=uncertainty,
            resource_integrity=resource_before,
            raw_risk=raw_risk,
            smoothed_risk=smoothed_risk,
            mode=mode,
        )

        affect_before = agent.compute_affect(error)
        affect_vector = (
            affect_before["valence"],
            affect_before["arousal"],
            affect_before["urgency"],
        )
        environmental_stress = max(
            min(1.0, max(0.0, error)),
            agent.telemetry.temperature,
        )
        workspace_messages = [
            WorkspaceMessage(
                source_module="world_model",
                salience=min(1.0, 0.65 * min(1.0, error) + 0.35 * uncertainty),
                affect_vector=affect_vector,
                payload={
                    "prediction_error": min(1.0, max(0.0, error)),
                    "environmental_stress": environmental_stress,
                    "observation": observation,
                    "prediction": prediction,
                },
            ),
            WorkspaceMessage(
                source_module="homeostasis",
                salience=affect_before["urgency"],
                affect_vector=affect_vector,
                payload={
                    "prediction_error": min(1.0, max(0.0, error)),
                    "environmental_stress": environmental_stress,
                    "battery_level": agent.telemetry.battery,
                    "temperature_level": agent.telemetry.temperature,
                },
            ),
            WorkspaceMessage(
                source_module="regulator",
                salience=smoothed_risk,
                affect_vector=affect_vector,
                payload={
                    "prediction_error": min(1.0, max(0.0, error)),
                    "environmental_stress": environmental_stress,
                    "mode": mode,
                    "reason": reason,
                },
            ),
        ]
        previous_broadcast = agent.global_workspace.current_global_broadcast
        workspace_broadcast = agent.global_workspace.compete_for_attention(
            workspace_messages
        )
        is_new_broadcast = workspace_broadcast is not previous_broadcast
        memory_matches = (
            agent.vector_memory.vector_search(workspace_broadcast, top_k=3)
            if is_new_broadcast and workspace_broadcast is not None
            else []
        )

        effort = agent.act(mode)
        env.apply_action(effort)
        resource_after = agent.telemetry.resource_integrity()
        affect_after = agent.compute_affect(error)

        if is_new_broadcast and workspace_broadcast is not None:
            agent.vector_memory.save_episode(
                workspace_broadcast,
                outcome=f"mode={mode};resource_integrity={resource_after:.4f}",
            )

        association_tags = []
        if error >= 0.65:
            association_tags.append("high-prediction-error")
        if agent.telemetry.temperature >= 0.8:
            association_tags.append("thermal-throttling")
        if mode in {"recovery", "shutdown"}:
            association_tags.append("recovery-sequence")

        episodic_entry = agent.record_episode(
            {
                "timestamp": time.time_ns() // 1_000_000,
                "session_id": session_id,
                "context": {
                    "active_goal_id": "stabilize_environment",
                    "environmental_signature": (
                        f"observation={observation};prediction={prediction:.4f};"
                        f"uncertainty={uncertainty:.4f}"
                    ),
                },
                "internal_telemetry_snapshot": {
                    "battery_level": agent.telemetry.battery,
                    "temperature_level": agent.telemetry.temperature,
                    "prediction_delta": min(1.0, max(0.0, error)),
                },
                "affective_signature": affect_after,
                "episodic_payload": {
                    "action_taken": f"{mode} (effort={effort:.2f})",
                    "sensory_input_summary": (
                        f"observation={observation};prediction={prediction:.4f};"
                        f"error={error:.4f};uncertainty={uncertainty:.4f}"
                    ),
                    "result_outcome": (
                        f"mode={mode};resource_integrity={resource_after:.4f}"
                    ),
                    "homeostatic_impact_delta": (
                        affect_after["valence"] - affect_before["valence"]
                    ),
                },
                "association_tags": association_tags,
            }
        )

        logs.append(
            LogEntry(
                t=t,
                disturbance=disturbance,
                observation=observation,
                prediction=prediction,
                error=error,
                uncertainty=uncertainty,
                raw_risk=raw_risk,
                smoothed_risk=smoothed_risk,
                mode=mode,
                reason=reason,
                effort=effort,
                battery=agent.telemetry.battery,
                temperature=agent.telemetry.temperature,
                resource_before=resource_before,
                resource_after=resource_after,
                consistency=agent.self_model.consistency,
                true_state_after=env.true_state,
                episodic_entry=episodic_entry,
                workspace_broadcast=workspace_broadcast,
                memory_matches=memory_matches,
            )
        )

    print_results(logs)
    return logs


def print_results(logs):
    print(
        f"{'t':>2} | {'disturbance':>25} | {'obs':>7} | {'pred':>7} | "
        f"{'err':>5} | {'unc':>5} | {'raw':>5} | {'risk':>5} | "
        f"{'mode':>8} | {'eff':>4} | {'bat':>5} | {'tmp':>5} | {'con':>5}"
    )
    print("-" * 145)

    for entry in logs:
        observation = "BLACKOUT" if entry.observation is None else f"{entry.observation:7.2f}"

        print(
            f"{entry.t:2d} | "
            f"{str(entry.disturbance):>25} | "
            f"{observation:>7} | "
            f"{entry.prediction:7.2f} | "
            f"{entry.error:5.2f} | "
            f"{entry.uncertainty:5.2f} | "
            f"{entry.raw_risk:5.2f} | "
            f"{entry.smoothed_risk:5.2f} | "
            f"{entry.mode:>8} | "
            f"{entry.effort:4.1f} | "
            f"{entry.battery:5.2f} | "
            f"{entry.temperature:5.2f} | "
            f"{entry.consistency:5.2f}"
        )

    print("\nDecision explanations:")
    for entry in logs:
        print(f"t={entry.t:02d} | {entry.mode:>8} | {entry.reason}")


if __name__ == "__main__":
    run_simulation(steps=30, seed=42)