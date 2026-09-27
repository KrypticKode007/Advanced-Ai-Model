"""Self-healing redundant-cell battery pack simulation."""

from __future__ import annotations

from dataclasses import dataclass
import random
from typing import Any

from src.actuation import (
    ActuationResult,
    BatteryActuator,
    DryRunActuator,
    SafetyPolicy,
)
from src.telemetry import validate_observation


@dataclass
class BatterySnapshot:
    time: int
    cells: list[float]
    temperature: float
    current: float
    bypass: list[bool]

    def as_dict(self) -> dict[str, Any]:
        return {
            "time": self.time,
            "cells": self.cells,
            "temperature": self.temperature,
            "current": self.current,
            "bypass": self.bypass,
        }


@dataclass
class AutonomyDecision:
    snapshot: BatterySnapshot
    health: float
    risk: float
    confidence: float
    action: str
    safety_override: bool
    predicted_min_voltage: float
    prediction_error: float
    estimated_drop_rate: float
    actuation: ActuationResult

    def as_dict(self) -> dict[str, Any]:
        result = self.snapshot.as_dict()
        result.update(
            {
                "self_model": {
                    "health": round(self.health, 3),
                    "risk": round(self.risk, 3),
                    "confidence": round(self.confidence, 3),
                },
                "action": self.action,
                "safety_override": self.safety_override,
                "prediction": {
                    "predicted_min_voltage": round(self.predicted_min_voltage, 4),
                    "error": round(self.prediction_error, 4),
                    "estimated_drop_rate": round(self.estimated_drop_rate, 4),
                },
                "actuation": self.actuation.as_dict(),
            }
        )
        return result


class SelfHealingBattery:
    """Simulate four cells with automatic bypass of critically low cells."""

    def __init__(self, seed: int = 42) -> None:
        self._random = random.Random(seed)
        self.time = 0
        self.cells = [3.7, 3.7, 3.7, 3.7]
        self.temperature = 25.0
        self.current = 2.0
        self.bypass = [False] * len(self.cells)

    def step(self) -> BatterySnapshot:
        self.time += 1
        self.cells = [
            voltage - self._random.uniform(0.001, 0.003)
            for voltage in self.cells
        ]

        if self.time > 20:
            self.cells[1] -= 0.05

        self.temperature += self._random.uniform(0.1, 0.3)
        self.bypass = [voltage < 2.8 for voltage in self.cells]

        return BatterySnapshot(
            time=self.time,
            cells=[round(voltage, 4) for voltage in self.cells],
            temperature=round(self.temperature, 2),
            current=round(self.current, 2),
            bypass=self.bypass.copy(),
        )

    def run(self, steps: int, speed_multiplier: int = 1) -> list[dict[str, Any]]:
        if steps < 1:
            raise ValueError("steps must be at least 1")
        if speed_multiplier not in range(1, 11):
            raise ValueError("speed_multiplier must be between 1 and 10")
        trace = []
        for _ in range(steps):
            snapshot = self.step()
            for _ in range(speed_multiplier - 1):
                snapshot = self.step()
            trace.append(snapshot.as_dict())
        return trace


class AutonomousBatteryController:
    """Closed-loop controller with a self-model and non-bypassable safety rules."""

    def __init__(
        self,
        seed: int = 42,
        actuator: BatteryActuator | None = None,
        policy: SafetyPolicy | None = None,
    ) -> None:
        self.battery = SelfHealingBattery(seed=seed)
        self.policy = policy or SafetyPolicy()
        self.actuator = actuator or DryRunActuator(policy=self.policy)
        self.mode = "MONITOR"
        self._previous_minimum_voltage: float | None = None
        self._predicted_minimum_voltage = 3.7
        self._estimated_drop_rate = 0.002

    def _decide(self, snapshot: BatterySnapshot) -> AutonomyDecision:
        minimum_voltage = min(snapshot.cells)
        voltage_spread = max(snapshot.cells) - minimum_voltage
        prediction_error = abs(minimum_voltage - self._predicted_minimum_voltage)
        if self._previous_minimum_voltage is not None:
            observed_drop = max(0.0, self._previous_minimum_voltage - minimum_voltage)
            self._estimated_drop_rate = (
                0.8 * self._estimated_drop_rate + 0.2 * observed_drop
            )
        self._previous_minimum_voltage = minimum_voltage
        self._predicted_minimum_voltage = max(
            0.0, minimum_voltage - self._estimated_drop_rate
        )
        risk = min(
            1.0,
            max(
                0.0,
                (3.7 - minimum_voltage) / 1.2
                + voltage_spread / 0.8
                + max(0.0, snapshot.temperature - 45.0) / 40.0,
            ),
        )
        health = max(0.0, 1.0 - risk)
        confidence = max(
            0.0,
            min(1.0, 1.0 - voltage_spread / 0.8 - prediction_error / 0.1),
        )

        if self.policy.unsafe_reason(snapshot.cells, snapshot.temperature) is not None:
            self.mode = "EMERGENCY_SHUTDOWN"
            action = "shutdown_pack"
            safety_override = True
        elif any(snapshot.bypass):
            self.mode = "RECOVERY"
            action = "isolate_bypassed_cells"
            safety_override = False
        elif minimum_voltage < self.policy.conserve_voltage:
            self.mode = "CONSERVE"
            action = "reduce_current"
            self.battery.current = max(0.5, self.battery.current * 0.75)
            safety_override = False
        else:
            self.mode = "MONITOR"
            action = "continue_monitoring"
            safety_override = False

        actuation = self.actuator.apply(action, snapshot.cells, snapshot.temperature)

        return AutonomyDecision(
            snapshot=snapshot,
            health=health,
            risk=risk,
            confidence=confidence,
            action=action,
            safety_override=safety_override,
            predicted_min_voltage=self._predicted_minimum_voltage,
            prediction_error=prediction_error,
            estimated_drop_rate=self._estimated_drop_rate,
            actuation=actuation,
        )

    def step(self) -> AutonomyDecision:
        """Advance the digital twin and make one autonomous decision."""
        return self._decide(self.battery.step())

    def observe(self, observation: dict[str, Any]) -> AutonomyDecision:
        """Make a decision from one external or recorded BMS observation."""
        validate_observation(observation)
        cells = [float(voltage) for voltage in observation["cells"]]
        bypass = [bool(value) for value in observation["bypass"]]
        if len(cells) != 4 or len(bypass) != 4:
            raise ValueError("Battery observations must contain exactly four cells")
        snapshot = BatterySnapshot(
            time=int(observation["time"]),
            cells=cells,
            temperature=float(observation["temperature"]),
            current=float(observation["current"]),
            bypass=bypass,
        )
        return self._decide(snapshot)

    def run(self, steps: int, speed_multiplier: int = 1) -> list[dict[str, Any]]:
        if steps < 1:
            raise ValueError("steps must be at least 1")
        if speed_multiplier not in range(1, 11):
            raise ValueError("speed_multiplier must be between 1 and 10")
        trace = []
        for _ in range(steps):
            decision = self.step()
            for _ in range(speed_multiplier - 1):
                decision = self.step()
            trace.append(decision.as_dict())
        return trace