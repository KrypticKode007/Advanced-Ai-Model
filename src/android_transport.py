"""Android power-supply telemetry and preservation control.

The transport is read-only by default. Android power-supply sysfs node names
and write semantics are vendor-specific; physical writes require explicit
opt-in and must be validated on the target device first.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
from pathlib import Path
from typing import Mapping


LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class BMSTelemetry:
    voltage_uv: int
    current_now_ua: int
    temp_c: float
    capacity_pct: int


class AndroidKernelTransport:
    """Read Android battery sysfs and optionally write approved controls."""

    DEFAULT_PATH = Path("/sys/class/power_supply/battery")

    def __init__(
        self,
        power_supply_path: str | Path | None = None,
        write_enabled: bool = False,
        mock_telemetry: BMSTelemetry | None = None,
    ) -> None:
        self.power_supply_path = Path(power_supply_path or self.DEFAULT_PATH)
        self.write_enabled = write_enabled
        self.mock_telemetry = mock_telemetry
        self.is_available = self.power_supply_path.is_dir()
        if not self.is_available:
            LOGGER.warning("Android power-supply sysfs path is unavailable: %s", self.power_supply_path)
        if write_enabled and not self.is_available:
            raise ValueError("Physical writes require an available Android power-supply path")

    def _read_sysfs_int(self, node: str) -> int:
        try:
            return int((self.power_supply_path / node).read_text(encoding="utf-8").strip())
        except (FileNotFoundError, PermissionError, ValueError, OSError) as error:
            raise RuntimeError(f"Unable to read Android power node: {node}") from error

    def _write_sysfs_int(self, node: str, value: int) -> None:
        if not self.write_enabled:
            raise PermissionError("Android power writes are disabled")
        try:
            (self.power_supply_path / node).write_text(f"{value}\n", encoding="utf-8")
        except (PermissionError, OSError) as error:
            raise RuntimeError(f"Unable to write Android power node: {node}") from error

    def collect_bms_telemetry(self) -> BMSTelemetry:
        if self.mock_telemetry is not None:
            return self.mock_telemetry
        if not self.is_available:
            raise RuntimeError("No Android power-supply telemetry is available")
        return BMSTelemetry(
            voltage_uv=self._read_sysfs_int("voltage_now"),
            current_now_ua=self._read_sysfs_int("current_now"),
            temp_c=self._read_sysfs_int("temp") / 10.0,
            capacity_pct=self._read_sysfs_int("capacity"),
        )

    def enforce_electrical_limits(
        self, max_current_ma: int, suspend_charging: bool
    ) -> bool:
        if max_current_ma < 0:
            raise ValueError("Maximum current cannot be negative")
        if not self.write_enabled:
            LOGGER.info("Dry-run Android transport: current=%smA suspended=%s", max_current_ma, suspend_charging)
            return False
        self._write_sysfs_int("charging_enabled", 0 if suspend_charging else 1)
        self._write_sysfs_int("constant_charge_current_max", max_current_ma * 1000)
        return True


@dataclass(frozen=True)
class PreservationDecision:
    max_current_ma: int
    suspend_charging: bool
    reason: str
    valid: bool


class HardwareInTheLoopValidation:
    @staticmethod
    def validate_action(max_current_ma: int, telemetry: BMSTelemetry) -> bool:
        if telemetry.temp_c > 45.0 and max_current_ma > 500:
            return False
        if telemetry.voltage_uv > 4_450_000:
            return False
        return 0 <= telemetry.capacity_pct <= 100 and max_current_ma >= 0


class AutonomousPreservationOrchestrator:
    """Derive a bounded charging decision from Android BMS telemetry."""

    def __init__(self, transport: AndroidKernelTransport) -> None:
        self.transport = transport

    def decide(self, telemetry: BMSTelemetry) -> PreservationDecision:
        target_current_ma = 500 if telemetry.temp_c >= 41.0 or telemetry.capacity_pct > 85 else 2000
        suspend_charging = telemetry.temp_c >= 45.0
        valid = HardwareInTheLoopValidation.validate_action(target_current_ma, telemetry)
        if not valid:
            return PreservationDecision(500, True, "hardware validation rejected requested action", False)
        reason = "thermal or high-state-of-charge preservation" if target_current_ma == 500 else "normal charging profile"
        return PreservationDecision(target_current_ma, suspend_charging, reason, True)

    def execution_loop_step(self) -> dict[str, object]:
        telemetry = self.transport.collect_bms_telemetry()
        decision = self.decide(telemetry)
        applied = self.transport.enforce_electrical_limits(
            decision.max_current_ma, decision.suspend_charging
        ) if decision.valid else self.transport.enforce_electrical_limits(500, True)
        return {
            "telemetry": telemetry.__dict__,
            "decision": decision.__dict__,
            "applied": applied,
            "write_enabled": self.transport.write_enabled,
        }