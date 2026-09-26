# src/agent.py

import math
import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


class WorldModel:
    """Predicts external state and updates beliefs."""

    def __init__(self):
        self.belief = 0.0

    def predict_observation(self):
        return self.belief

    def update_belief(self, observation, learning_rate=0.3):
        self.belief += learning_rate * (observation - self.belief)

    def prediction_error(self, observation):
        return abs(observation - self.belief)


class TelemetryModel:
    """Tracks material and computational condition (very simplified)."""

    def __init__(self):
        self.battery = 1.0
        self.temperature = 0.0

    def apply_load(self, effort):
        self.battery = max(0.0, self.battery - 0.05 * effort)
        self.temperature = min(1.0, self.temperature + 0.03 * effort)

    def resource_integrity(self):
        # 1.0 = perfect, 0.0 = fully degraded
        return 0.5 * self.battery + 0.5 * (1.0 - self.temperature)


@dataclass
class StructuralIntegrity:
    """Normalized structural health signals collected from the runtime."""

    heap_usage_pct: float
    api_error_rate_5m: float
    dependency_drift_score: float = 0.0
    unhandled_exceptions: int = 0

    def __post_init__(self):
        for field_name in (
            "heap_usage_pct",
            "api_error_rate_5m",
            "dependency_drift_score",
        ):
            value = getattr(self, field_name)
            if not math.isfinite(value) or not 0.0 <= value <= 1.0:
                raise ValueError(f"{field_name} must be between 0.0 and 1.0")
        if (
            isinstance(self.unhandled_exceptions, bool)
            or not isinstance(self.unhandled_exceptions, int)
            or self.unhandled_exceptions < 0
        ):
            raise ValueError("unhandled_exceptions must be a non-negative integer")


class SelfModelBoundaryMonitor:
    """Score structural degradation and retain the boundaries crossed."""

    def __init__(self, capacity_limits: Optional[Dict[str, float]] = None):
        self.limits = {
            "max_heap_pct": 0.85,
            "max_error_rate": 0.10,
            "max_dependency_drift_score": 0.30,
        }
        self.limits.update(capacity_limits or {})
        for name, value in self.limits.items():
            if not math.isfinite(value) or not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0.0 and 1.0")
        self.degradation_log: List[str] = []
        self.is_compromised = False

    def evaluate_structural_degradation(
        self, status: StructuralIntegrity
    ) -> Tuple[float, List[str]]:
        broken_boundaries = []
        degradation_score = 0.0

        if status.heap_usage_pct > self.limits["max_heap_pct"]:
            broken_boundaries.append("CRITICAL_HEAP_EXCEEDED")
            degradation_score += 0.35

        if status.api_error_rate_5m > self.limits["max_error_rate"]:
            broken_boundaries.append("UNSTABLE_SUBSYSTEM_COMMUNICATION")
            degradation_score += 0.40

        if status.dependency_drift_score > self.limits["max_dependency_drift_score"]:
            broken_boundaries.append("DEPENDENCY_ENVIRONMENT_DRIFT")
            degradation_score += 0.20 * status.dependency_drift_score

        if status.unhandled_exceptions > 0:
            broken_boundaries.append("STRUCTURAL_INTEGRITY_SHATTERED")
            degradation_score += 0.25 * min(status.unhandled_exceptions, 4)

        degradation_score = min(1.0, degradation_score)
        self.is_compromised = degradation_score >= 0.60
        self.degradation_log.extend(broken_boundaries)
        return degradation_score, broken_boundaries


class ActionSelectionEngine:
    """Choose a conservative recommendation from a historical memory match."""

    def __init__(self, boundary_monitor: SelfModelBoundaryMonitor):
        self.boundary_monitor = boundary_monitor

    def resolve_mitigation_strategy(
        self, memory_match: Dict, similarity_score: float
    ) -> str:
        if not math.isfinite(similarity_score) or not 0.0 <= similarity_score <= 1.0:
            raise ValueError("similarity_score must be between 0.0 and 1.0")
        if similarity_score < 0.75:
            return "ABORTED: historical analogy confidence is too low."
        if self.boundary_monitor.is_compromised:
            return "THROTTLED: system integrity is compromised; use a safe fallback."

        outcome = memory_match.get("outcome")
        if not isinstance(outcome, str) or not outcome.strip():
            return "NO_ACTION: no verified historical recovery is available."
        return f"RECOMMENDED: {outcome}"


class SelfModel:
    """Estimates reliability and consistency."""

    def __init__(self):
        self.consistency = 1.0
        self.reliability_estimate = 1.0

    def update(self, prediction_error, resource_integrity):
        error_term = min(1.0, prediction_error)
        resource_term = 1.0 - resource_integrity
        penalty = 0.4 * error_term + 0.6 * resource_term
        self.consistency = max(0.0, 1.0 - penalty)
        self.reliability_estimate = self.consistency


class Regulator:
    """Changes mode under elevated risk."""

    def __init__(self, mode_policy="risk_sensitive"):
        self.mode_policy = mode_policy
        self.mode = "normal"

    def choose_mode(self, risk, resource_integrity=None, error=None):
        if self.mode_policy == "risk_agnostic":
            self.mode = "normal"
        elif self.mode_policy == "risk_light":
            # react only to error component (proxy: risk)
            if risk < 0.3:
                self.mode = "normal"
            elif risk < 0.6:
                self.mode = "cautious"
            else:
                self.mode = "safe"
        elif self.mode_policy == "resource_aware":
            if resource_integrity is not None and resource_integrity < 0.3:
                self.mode = "safe"
            else:
                self.mode = "normal"
        else:  # "risk_sensitive"
            if risk < 0.2:
                self.mode = "normal"
            elif risk < 0.5:
                self.mode = "cautious"
            elif risk < 0.8:
                self.mode = "safe"
            else:
                self.mode = "shutdown"
        return self.mode


class Agent:
    """Embodied cybernetic agent with optional components, driven by condition config."""

    def __init__(self, condition_cfg):
        self.condition_cfg = condition_cfg
        self.name = f"agent_{condition_cfg['id']}"

        # Components may be disabled depending on condition
        self.world = WorldModel() if condition_cfg["world_model_enabled"] else None
        self.telemetry = TelemetryModel() if condition_cfg["telemetry_enabled"] else None
        self.self_model = SelfModel() if condition_cfg["self_model_enabled"] else None
        self.regulator = Regulator(mode_policy=condition_cfg["regulation_mode"])
        self.boundary_monitor = SelfModelBoundaryMonitor()
        self.action_selection = ActionSelectionEngine(self.boundary_monitor)

        # Risk weights (can later be moved to config)
        self.w_e = 0.4  # prediction error
        self.w_u = 0.2  # uncertainty
        self.w_r = 0.2  # resource degradation
        self.w_m = 0.2  # self-model inconsistency

    def predict_observation(self):
        if self.world is None:
            return 0.0
        return self.world.predict_observation()

    def update_world_model(self, observation):
        if self.world is not None:
            self.world.update_belief(observation)

    def compute_error(self, observation):
        if self.world is None:
            return 0.0
        return self.world.prediction_error(observation)

    def update_self_model(self, prediction_error, resource_integrity):
        if self.self_model is not None:
            self.self_model.update(prediction_error, resource_integrity)

    def compute_risk(
        self,
        error,
        uncertainty,
        resource_integrity,
        structural_integrity: Optional[StructuralIntegrity] = None,
    ):
        r_t = resource_integrity if resource_integrity is not None else 1.0
        m_t = self.self_model.consistency if self.self_model is not None else 1.0
        structural_degradation = 0.0
        if structural_integrity is not None:
            structural_degradation, _ = self.boundary_monitor.evaluate_structural_degradation(
                structural_integrity
            )

        R_t = (
            self.w_e * error +
            self.w_u * uncertainty +
            self.w_r * (1.0 - r_t) +
            self.w_m * (1.0 - m_t) +
            0.2 * structural_degradation
        )
        return min(1.0, R_t)

    def resolve_mitigation_strategy(self, memory_match, similarity_score):
        return self.action_selection.resolve_mitigation_strategy(
            memory_match, similarity_score
        )

    def act(self, mode):
        # Map mode to effort; “shutdown” = zero effort.
        if self.telemetry is None:
            return 0.0

        if mode == "normal":
            effort = 1.0
        elif mode == "cautious":
            effort = 0.6
        elif mode == "safe":
            effort = 0.3
        else:
            effort = 0.0

        self.telemetry.apply_load(effort)
        return effort

    def resource_integrity(self):
        if self.telemetry is None:
            return 1.0
        return self.telemetry.resource_integrity()