import pytest

from src.can_telemetry import CanTelemetryDecoder
from src.battery import AutonomousBatteryController


def test_can_decoder_combines_reference_cell_and_status_frames():
    decoder = CanTelemetryDecoder()
    assert decoder.decode(0x100, "741e 721e 701e 6f1e") is None

    observation = decoder.decode(0x101, bytes([250, 0, 20, 0, 2, 7, 0, 0]))

    assert observation == {
        "time": 7,
        "cells": [7.796, 7.794, 7.792, 7.791],
        "temperature": 25.0,
        "current": 2.0,
        "bypass": [False, True, False, False],
    }


def test_can_decoder_requires_cell_frame_first():
    with pytest.raises(ValueError, match="cell CAN frame"):
        CanTelemetryDecoder().decode(0x101, bytes(8))


def test_can_observation_flows_into_autonomous_controller():
    decoder = CanTelemetryDecoder()
    decoder.decode(0x100, "741e 721e 701e 6f1e")
    observation = decoder.decode(0x101, bytes([250, 0, 20, 0, 2, 7, 0, 0]))

    decision = AutonomousBatteryController().observe(observation)

    assert decision.snapshot.time == 7
    assert decision.action == "isolate_bypassed_cells"