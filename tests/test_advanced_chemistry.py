import pytest

from src.advanced_chemistry import (
    DEFAULT_CHEMISTRY,
    DEFAULT_SPECS,
    AutonomousBatteryDynamicsEngine,
)


def test_chemistry_engine_matches_reference_screening_case():
    engine = AutonomousBatteryDynamicsEngine(DEFAULT_CHEMISTRY, DEFAULT_SPECS)

    result = engine.evaluate(350, 42.0, 0.95, 3.0)

    assert result["total_energy_wh"] == 31.5
    assert result["structural_boundary_breach"] is True


def test_chemistry_engine_rejects_invalid_charge_rate():
    engine = AutonomousBatteryDynamicsEngine(DEFAULT_CHEMISTRY, DEFAULT_SPECS)

    with pytest.raises(ValueError, match="Charge rate"):
        engine.compute_swelling_risk(0.5, -1.0)