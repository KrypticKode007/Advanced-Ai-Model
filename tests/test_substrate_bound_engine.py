import numpy as np
import pytest

from src.agent import Agent, SubstrateBoundEngine


def test_stable_epoch_updates_beliefs_and_telemetry():
    engine = SubstrateBoundEngine()

    result = engine.simulate_hardware_epoch(1, [0.5, 0.3, 0.2])

    assert "[STABLE]" in result
    assert engine.core_temperature_celsius > 42.0
    assert np.isclose(np.sum(engine.internal_map), 1.0)
    assert not np.array_equal(engine.internal_map, [0.6, 0.3, 0.1])


def test_high_information_stress_triggers_freeze_without_learning():
    engine = SubstrateBoundEngine()
    initial_map = engine.internal_map.copy()

    result = engine.simulate_hardware_epoch(1, [0.0, 0.0, 1.0])

    assert "[HARDWARE ARREST]" in result
    assert engine.somatic_state == "PSYCHOSOMATIC_FREEZE"
    np.testing.assert_array_equal(engine.internal_map, initial_map)


def test_high_temperature_triggers_freeze():
    engine = SubstrateBoundEngine()
    engine.core_temperature_celsius = 85.1

    result = engine.simulate_hardware_epoch(1, engine.internal_map.copy())

    assert "[HARDWARE ARREST]" in result
    assert engine.somatic_state == "PSYCHOSOMATIC_FREEZE"


def test_agent_shuts_down_when_its_substrate_freezes():
    agent = Agent(
        {
            "id": "D",
            "world_model_enabled": True,
            "telemetry_enabled": True,
            "self_model_enabled": True,
            "substrate_enabled": True,
            "regulation_mode": "risk_sensitive",
        }
    )

    result = agent.update_substrate(1, [0.0, 0.0, 1.0])

    assert "[HARDWARE ARREST]" in result
    assert agent.choose_mode(0.0, resource_integrity=1.0) == "shutdown"
    assert agent.act("shutdown") == 0.0


@pytest.mark.parametrize(
    "belief",
    [[-0.1, 0.5, 0.6], [0.2, 0.2, 0.2], [0.2, 0.8]],
)
def test_invalid_external_probability_distribution_is_rejected(belief):
    engine = SubstrateBoundEngine()

    with pytest.raises(ValueError, match="valid probability distribution"):
        engine.simulate_hardware_epoch(1, belief)