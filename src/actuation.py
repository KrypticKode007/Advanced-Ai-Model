"""Safety-gated battery action interfaces.

Physical actuation is deliberately unavailable by default. A production
adapter must implement the protocol and retain the same interlock checks.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Protocol, Sequence


@dataclass(frozen=True)
class ActuationResult:
    action: str
    status: str
    reason: str

    def as_dict(self) -> dict[str, str]:
        return {
            "action": self.action,
            "status": self.status,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class SafetyPolicy:
    minimum_voltage: float = 2.5
    maximum_temperature: float = 60.0
    conserve_voltage: float = 3.2

    def unsafe_reason(
        self, cells: Sequence[float], temperature: float
    ) -> str | None:
        if min(cells) < self.minimum_voltage:
            return "minimum cell voltage is below the shutdown limit"
        if temperature >= self.maximum_temperature:
            return "temperature is at or above the shutdown limit"
        return None


class BatteryActuator(Protocol):
    def apply(
        self, action: str, cells: Sequence[float], temperature: float
    ) -> ActuationResult:
        ...


@dataclass(frozen=True)
class CableProfile:
    name: str
    maximum_voltage: float
    maximum_current: float
    chemistry: str


class ChargerTransport(Protocol):
    def charger_handshake(self, profile: CableProfile) -> bool:
        ...

    def enable_output(self, current_limit: float) -> None:
        ...

    def disable_output(self) -> None:
        ...

    def faulted(self) -> bool:
        ...


class GuardedHardwareActuator:
    """Hardware gate requiring a recognized profile and explicit arming."""

    def __init__(
        self,
        transport: ChargerTransport,
        profiles: Sequence[CableProfile],
        policy: SafetyPolicy | None = None,
    ) -> None:
        self.transport = transport
        self.profiles = {profile.name: profile for profile in profiles}
        self.policy = policy or SafetyPolicy()
        self.profile: CableProfile | None = None
        self.armed = False

    def connect(self, profile_name: str) -> ActuationResult:
        profile = self.profiles.get(profile_name)
        if profile is None:
            return ActuationResult(
                action="connect",
                status="BLOCKED_UNKNOWN_CABLE",
                reason="Cable profile is not recognized",
            )
        if not self.transport.charger_handshake(profile):
            return ActuationResult(
                action="connect",
                status="BLOCKED_HANDSHAKE",
                reason="Charger handshake failed",
            )
        self.profile = profile
        self.armed = False
        return ActuationResult(
            action="connect",
            status="CONNECTED_NOT_ENERGIZED",
            reason="Recognized cable connected; explicit arming is required",
        )

    def arm(self, confirmation: str) -> ActuationResult:
        if self.profile is None:
            return ActuationResult("arm", "BLOCKED_NOT_CONNECTED", "No verified cable is connected")
        if confirmation != "ARM_CHARGER":
            return ActuationResult("arm", "BLOCKED_NO_CONFIRMATION", "Explicit arming confirmation is required")
        self.armed = True
        return ActuationResult("arm", "ARMED_NOT_ENERGIZED", "Hardware is armed but output remains disabled")

    def request_charge(
        self, cells: Sequence[float], temperature: float, current_limit: float
    ) -> ActuationResult:
        reason = self.policy.unsafe_reason(cells, temperature)
        if self.profile is None:
            return ActuationResult("enable_charging", "BLOCKED_NOT_CONNECTED", "No verified cable is connected")
        if not self.armed:
            return ActuationResult("enable_charging", "BLOCKED_NOT_ARMED", "Explicit arming is required")
        if self.transport.faulted():
            self.transport.disable_output()
            self.armed = False
            return ActuationResult("enable_charging", "BLOCKED_TRANSPORT_FAULT", "Transport fault forced output shutdown")
        if reason is not None:
            self.transport.disable_output()
            self.armed = False
            return ActuationResult("enable_charging", "BLOCKED_BY_INTERLOCK", reason)
        if not math.isfinite(current_limit) or current_limit <= 0 or current_limit > self.profile.maximum_current:
            return ActuationResult("enable_charging", "BLOCKED_CURRENT_LIMIT", "Requested current exceeds cable profile")
        if sum(cells) > self.profile.maximum_voltage:
            return ActuationResult("enable_charging", "BLOCKED_VOLTAGE_LIMIT", "Pack voltage exceeds cable profile")
        self.transport.enable_output(current_limit)
        return ActuationResult("enable_charging", "ENERGIZED", "Output enabled within verified limits")

    def shutdown(self) -> ActuationResult:
        self.transport.disable_output()
        self.armed = False
        return ActuationResult("shutdown_pack", "SHUTDOWN", "Output disabled and actuator disarmed")


class DryRunActuator:
    """Record decisions without energizing hardware."""

    def __init__(self, policy: SafetyPolicy | None = None):
        self.policy = policy or SafetyPolicy()

    def apply(
        self, action: str, cells: Sequence[float], temperature: float
    ) -> ActuationResult:
        reason = self.policy.unsafe_reason(cells, temperature)
        if reason is not None and action != "shutdown_pack":
            return ActuationResult(
                action=action,
                status="BLOCKED_BY_INTERLOCK",
                reason=f"{reason}; pack shutdown is required",
            )
        return ActuationResult(
            action=action,
            status="DRY_RUN",
            reason="No physical actuator is enabled",
        )