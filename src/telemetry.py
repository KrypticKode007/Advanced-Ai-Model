"""Validated telemetry adapters for UART, files, and hardware-in-the-loop feeds."""

from __future__ import annotations

import json
import math
from typing import Any, Iterator, TextIO


REQUIRED_FIELDS = {"time", "cells", "temperature", "current", "bypass"}


def validate_observation(observation: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(observation, dict):
        raise ValueError("Battery observation must be an object")
    missing = REQUIRED_FIELDS.difference(observation)
    if missing:
        raise ValueError(f"Missing battery observation fields: {sorted(missing)}")
    cells = observation["cells"]
    bypass = observation["bypass"]
    if not isinstance(cells, (list, tuple)) or not isinstance(bypass, (list, tuple)):
        raise ValueError("Battery cells and bypass values must be arrays")
    if len(cells) != 4 or len(bypass) != 4:
        raise ValueError("Battery observations must contain exactly four cells")
    try:
        numeric_values = [
            float(observation["time"]),
            float(observation["temperature"]),
            float(observation["current"]),
            *(float(voltage) for voltage in cells),
        ]
    except (TypeError, ValueError) as error:
        raise ValueError("Battery measurements must be numeric") from error
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError("Battery measurements must be finite")
    if any(float(voltage) <= 0 for voltage in cells):
        raise ValueError("Cell voltages must be positive")
    if not all(isinstance(value, bool) for value in bypass):
        raise ValueError("Bypass values must be boolean")
    return observation


class JsonLineTelemetryAdapter:
    """Read one validated JSON observation per line from UART or a file."""

    def __init__(self, stream: TextIO) -> None:
        self.stream = stream

    def observations(self) -> Iterator[dict[str, Any]]:
        for line_number, line in enumerate(self.stream, start=1):
            if not line.strip():
                continue
            try:
                observation = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"Invalid telemetry JSON on line {line_number}") from error
            if not isinstance(observation, dict):
                raise ValueError(f"Telemetry line {line_number} must contain an object")
            yield validate_observation(observation)