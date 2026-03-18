from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from power_tool_line_geometry import (
    bundle_equivalent_parameters,
    calculate_overhead_line_sequence,
)


def test_bundle_equivalent_parameters_four_bundle_regression() -> None:
    r_eq, gmr_eq, radius_eq = bundle_equivalent_parameters(
        resistance_sub_ohm_per_km=0.032,
        gmr_sub_m=0.0115,
        radius_sub_m=0.0159,
        bundle_count=4,
        bundle_spacing_m=0.45,
    )
    assert r_eq == pytest.approx(0.008, rel=1e-12)
    assert gmr_eq == pytest.approx(0.19620614044080098, rel=1e-12)
    assert radius_eq == pytest.approx(0.21275874303373832, rel=1e-12)


def test_overhead_line_sequence_without_ground_wire_regression() -> None:
    result = calculate_overhead_line_sequence(
        frequency_hz=50.0,
        soil_resistivity_ohm_m=100.0,
        phase_positions=[(-12.0, 20.0), (0.0, 20.0), (12.0, 20.0)],
        phase_resistance_ohm_per_km=0.032,
        phase_gmr_m=0.0115,
        phase_radius_m=0.0159,
        phase_bundle_count=4,
        phase_bundle_spacing_m=0.45,
        has_ground_wire=False,
    )
    assert result.Z1_ohm_per_km.real == pytest.approx(0.008008429256947502, rel=1e-10)
    assert result.Z1_ohm_per_km.imag == pytest.approx(0.27297535943364015, rel=1e-10)
    assert result.Z0_ohm_per_km.real == pytest.approx(0.15087666661604832, rel=1e-10)
    assert result.Z0_ohm_per_km.imag == pytest.approx(1.0696432965187992, rel=1e-10)
    assert result.C1_uF_per_km == pytest.approx(0.013433280796977377, rel=1e-10)
    assert result.C0_uF_per_km == pytest.approx(0.00759757437837856, rel=1e-10)
    assert result.B1_uS_per_km == pytest.approx(4.220189626539296, rel=1e-10)
    assert result.B0_uS_per_km == pytest.approx(2.3868483852216125, rel=1e-10)


def test_ground_wire_reduces_zero_sequence_impedance_for_low_resistance_shield() -> None:
    base = calculate_overhead_line_sequence(
        frequency_hz=50.0,
        soil_resistivity_ohm_m=100.0,
        phase_positions=[(-12.0, 20.0), (0.0, 20.0), (12.0, 20.0)],
        phase_resistance_ohm_per_km=0.032,
        phase_gmr_m=0.0115,
        phase_radius_m=0.0159,
        phase_bundle_count=4,
        phase_bundle_spacing_m=0.45,
        has_ground_wire=False,
    )
    shield = calculate_overhead_line_sequence(
        frequency_hz=50.0,
        soil_resistivity_ohm_m=100.0,
        phase_positions=[(-12.0, 20.0), (0.0, 20.0), (12.0, 20.0)],
        phase_resistance_ohm_per_km=0.032,
        phase_gmr_m=0.0115,
        phase_radius_m=0.0159,
        phase_bundle_count=4,
        phase_bundle_spacing_m=0.45,
        has_ground_wire=True,
        ground_wire_position=(0.0, 28.0),
        ground_wire_resistance_ohm_per_km=0.05,
        ground_wire_gmr_m=0.0045,
        ground_wire_radius_m=0.005,
    )
    assert shield.Z0_ohm_per_km.real < base.Z0_ohm_per_km.real
    assert shield.Z0_ohm_per_km.imag < base.Z0_ohm_per_km.imag
    assert shield.C0_uF_per_km > base.C0_uF_per_km
    assert abs(shield.Z1_ohm_per_km.imag - base.Z1_ohm_per_km.imag) < 1e-3
