"""Decoder for the reference CAN telemetry format used by the battery adapter."""

from __future__ import annotations

from dataclasses import dataclass

from src.telemetry import validate_observation


@dataclass
class CanTelemetryDecoder:
    """Combine one cell frame and one status frame into a battery observation.

    Reference format: 0x100 contains four little-endian cell voltages in mV;
    0x101 contains temperature and current in deci-units, a bypass bitmask, and
    a three-byte little-endian timestamp. Production hardware must configure
    these IDs and field encodings to its BMS specification.
    """

    cell_frame_id: int = 0x100
    status_frame_id: int = 0x101

    def __post_init__(self) -> None:
        self._cells: list[float] | None = None

    @staticmethod
    def _payload(data: bytes | bytearray | str) -> bytes:
        if isinstance(data, str):
            try:
                data = bytes.fromhex(data)
            except ValueError as error:
                raise ValueError("CAN payload must be hexadecimal") from error
        return bytes(data)

    def decode(
        self, frame_id: int, data: bytes | bytearray | str
    ) -> dict[str, object] | None:
        payload = self._payload(data)
        if frame_id == self.cell_frame_id:
            if len(payload) != 8:
                raise ValueError("Cell CAN frame must contain exactly 8 bytes")
            self._cells = [
                int.from_bytes(payload[index:index + 2], "little") / 1000
                for index in range(0, 8, 2)
            ]
            return None

        if frame_id != self.status_frame_id:
            return None
        if len(payload) != 8:
            raise ValueError("Status CAN frame must contain exactly 8 bytes")
        if self._cells is None:
            raise ValueError("A cell CAN frame is required before a status frame")

        bypass_mask = payload[4]
        observation = {
            "time": int.from_bytes(payload[5:8], "little"),
            "cells": self._cells.copy(),
            "temperature": int.from_bytes(payload[0:2], "little", signed=True) / 10,
            "current": int.from_bytes(payload[2:4], "little", signed=True) / 10,
            "bypass": [bool(bypass_mask & (1 << index)) for index in range(4)],
        }
        return validate_observation(observation)