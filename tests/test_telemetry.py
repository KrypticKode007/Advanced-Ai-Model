import io

import pytest

from src.telemetry import JsonLineTelemetryAdapter


def _observation():
    return '{"time": 1, "cells": [3.7, 3.7, 3.7, 3.7], "temperature": 25, "current": 2, "bypass": [false, false, false, false]}'


def test_json_line_adapter_reads_uart_style_observations():
    adapter = JsonLineTelemetryAdapter(io.StringIO(f"\n{_observation()}\n"))

    observations = list(adapter.observations())

    assert observations[0]["cells"] == [3.7, 3.7, 3.7, 3.7]


def test_json_line_adapter_rejects_invalid_observation():
    adapter = JsonLineTelemetryAdapter(io.StringIO('{"time": 1}\n'))

    with pytest.raises(ValueError, match="Missing battery observation fields"):
        list(adapter.observations())


def test_json_line_adapter_rejects_non_finite_measurements():
    adapter = JsonLineTelemetryAdapter(
        io.StringIO(
            '{"time": 1, "cells": [3.7, NaN, 3.7, 3.7], '
            '"temperature": 25, "current": 2, '
            '"bypass": [false, false, false, false]}\n'
        )
    )

    with pytest.raises(ValueError, match="finite"):
        list(adapter.observations())