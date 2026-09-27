"""Bounded engineering estimates for advanced battery chemistry concepts.

This module is a screening model, not an electrochemical simulator or a
certification claim. Its outputs must not be used to set physical charger
limits without measured cell data and independent protection.
"""

from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class AdvancedChemistryFormula:
    anode_chemistry: str
    cathode_chemistry: str
    electrolyte_chemistry: str
    fline_notation: str
    theoretical_anode_capacity: float

    def __post_init__(self) -> None:
        if not all(
            isinstance(value, str) and value.strip()
            for value in (
                self.anode_chemistry,
                self.cathode_chemistry,
                self.electrolyte_chemistry,
                self.fline_notation,
            )
        ):
            raise ValueError("Chemistry descriptions must be non-empty strings")
        if not math.isfinite(self.theoretical_anode_capacity) or self.theoretical_anode_capacity <= 0:
            raise ValueError("Theoretical anode capacity must be positive and finite")


@dataclass(frozen=True)
class BatteryAdvancedSpecs:
    volumetric_density_wh_l: float
    gravimetric_density_wh_kg: float
    total_capacity_mah: float
    nominal_voltage: float
    max_charge_c_rate: float
    volume_expansion_tolerance: float

    def __post_init__(self) -> None:
        positive_values = (
            self.volumetric_density_wh_l,
            self.gravimetric_density_wh_kg,
            self.total_capacity_mah,
            self.nominal_voltage,
            self.max_charge_c_rate,
        )
        if not all(math.isfinite(value) and value > 0 for value in positive_values):
            raise ValueError("Battery specification values must be positive and finite")
        if not 0 < self.volume_expansion_tolerance <= 1:
            raise ValueError("Volume expansion tolerance must be between 0 and 1")


class AutonomousBatteryDynamicsEngine:
    """Estimate SoH and swelling risk for chemistry-screening experiments."""

    def __init__(
        self, chemistry: AdvancedChemistryFormula, specs: BatteryAdvancedSpecs
    ) -> None:
        self.chemistry = chemistry
        self.specs = specs
        self.total_energy_wh = specs.total_capacity_mah * specs.nominal_voltage / 1000.0

    def calculate_state_of_health(self, cycle_count: int, average_temp: float) -> float:
        if cycle_count < 0 or not math.isfinite(average_temp):
            raise ValueError("Cycle count must be non-negative and temperature finite")
        thermal_stress = max(1.0, (average_temp / 35.0) ** 2) if average_temp > 35.0 else 1.0
        degradation_factor = (cycle_count / 1000.0) * 0.15 * thermal_stress
        return max(0.0, 1.0 - degradation_factor)

    def compute_swelling_risk(
        self, state_of_charge: float, charge_rate_c: float
    ) -> tuple[float, bool]:
        if not 0 <= state_of_charge <= 1:
            raise ValueError("State of charge must be between 0 and 1")
        if not math.isfinite(charge_rate_c) or charge_rate_c < 0:
            raise ValueError("Charge rate must be finite and non-negative")
        modeled_swelling = 0.02 + (state_of_charge * 0.12) * (1.0 + charge_rate_c * 0.15)
        return min(0.30, modeled_swelling), modeled_swelling > self.specs.volume_expansion_tolerance

    def evaluate(self, cycle_count: int, average_temp: float, state_of_charge: float, charge_rate_c: float) -> dict[str, object]:
        swelling, boundary_breach = self.compute_swelling_risk(state_of_charge, charge_rate_c)
        return {
            "model_status": "screening_estimate",
            "total_energy_wh": round(self.total_energy_wh, 3),
            "state_of_health": round(self.calculate_state_of_health(cycle_count, average_temp), 4),
            "swelling_fraction": round(swelling, 4),
            "structural_boundary_breach": boundary_breach,
            "charge_rate_c": charge_rate_c,
            "max_charge_c_rate": self.specs.max_charge_c_rate,
        }


DEFAULT_CHEMISTRY = AdvancedChemistryFormula(
    anode_chemistry="100% Si nanostructure in carbon matrix",
    cathode_chemistry="Lithium-rich high-nickel NMC",
    electrolyte_chemistry="Halide solid electrolyte concept",
    fline_notation="[Si100::C][Halide][Salt:screening][T:25C]",
    theoretical_anode_capacity=4200.0,
)

DEFAULT_SPECS = BatteryAdvancedSpecs(
    volumetric_density_wh_l=920.0,
    gravimetric_density_wh_kg=385.0,
    total_capacity_mah=7500.0,
    nominal_voltage=4.2,
    max_charge_c_rate=3.0,
    volume_expansion_tolerance=0.15,
)