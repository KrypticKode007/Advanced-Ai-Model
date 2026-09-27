import pytest

from src.android_transport import (
    AndroidKernelTransport,
    AutonomousPreservationOrchestrator,
    BMSTelemetry,
)


def test_android_transport_defaults_to_read_only_dry_run():
    telemetry = BMSTelemetry(4_350_000, -2_500_000, 41.5, 88)
    transport = AndroidKernelTransport(mock_telemetry=telemetry)

    result = AutonomousPreservationOrchestrator(transport).execution_loop_step()

    assert result["decision"]["max_current_ma"] == 500
    assert result["applied"] is False
    assert result["write_enabled"] is False


def test_hot_battery_is_forced_to_suspend():
    telemetry = BMSTelemetry(4_300_000, -1_000_000, 46.0, 70)
    orchestrator = AutonomousPreservationOrchestrator(
        AndroidKernelTransport(mock_telemetry=telemetry)
    )

    result = orchestrator.execution_loop_step()

    assert result["decision"]["suspend_charging"] is True
    assert result["decision"]["valid"] is True


def test_physical_write_opt_in_requires_available_sysfs():
    with pytest.raises(ValueError, match="available Android"):
        AndroidKernelTransport("/path/that/does/not/exist", write_enabled=True)