from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from power_tool_line_geometry import (
    bundle_equivalent_parameters,
    calculate_cable_sequence,
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



def test_cable_sequence_trefoil_with_bonded_sheath_returns_plausible_values() -> None:
    result = calculate_cable_sequence(
        frequency_hz=50.0,
        rated_voltage_kv=10.0,
        soil_resistivity_ohm_m=100.0,
        arrangement="trefoil",
        phase_spacing_m=0.12,
        burial_depth_m=1.2,
        conductor_resistance_ohm_per_km=0.0601,
        conductor_gmr_m=0.0065,
        conductor_radius_m=0.008,
        insulation_outer_radius_m=0.021,
        relative_permittivity=2.3,
        sheath_enabled=True,
        sheath_bonding="both_ends",
        zero_sequence_return="sheath",
        sheath_resistance_ohm_per_km=0.20,
        sheath_radius_m=0.024,
    )
    assert result.D_ab_m == pytest.approx(0.12, rel=1e-12)
    assert result.Z1_ohm_per_km.real == pytest.approx(0.0601, rel=1e-9)
    assert 0.16 < result.Z1_ohm_per_km.imag < 0.21
    assert result.Z0_ohm_per_km.real == pytest.approx(0.2601, rel=1e-9)
    assert result.C1_uF_per_km == pytest.approx(result.C0_uF_per_km, rel=1e-12)
    assert 0.12 < result.C1_uF_per_km < 0.16
    assert result.charging_current_A_per_km > 0.0


def test_cable_sequence_single_point_sheath_uses_earth_return_zero_sequence() -> None:
    bonded = calculate_cable_sequence(
        frequency_hz=50.0,
        rated_voltage_kv=10.0,
        soil_resistivity_ohm_m=100.0,
        arrangement="flat",
        phase_spacing_m=0.12,
        burial_depth_m=1.2,
        conductor_resistance_ohm_per_km=0.0601,
        conductor_gmr_m=0.0065,
        conductor_radius_m=0.008,
        insulation_outer_radius_m=0.021,
        relative_permittivity=2.3,
        sheath_enabled=True,
        sheath_bonding="both_ends",
        zero_sequence_return="sheath",
        sheath_resistance_ohm_per_km=0.20,
        sheath_radius_m=0.024,
    )
    single_point = calculate_cable_sequence(
        frequency_hz=50.0,
        rated_voltage_kv=10.0,
        soil_resistivity_ohm_m=100.0,
        arrangement="flat",
        phase_spacing_m=0.12,
        burial_depth_m=1.2,
        conductor_resistance_ohm_per_km=0.0601,
        conductor_gmr_m=0.0065,
        conductor_radius_m=0.008,
        insulation_outer_radius_m=0.021,
        relative_permittivity=2.3,
        sheath_enabled=True,
        sheath_bonding="single_point",
        zero_sequence_return="sheath",
        sheath_resistance_ohm_per_km=0.20,
        sheath_radius_m=0.024,
    )
    assert abs(single_point.Z0_ohm_per_km) > abs(bonded.Z0_ohm_per_km)
    assert single_point.C1_uF_per_km == pytest.approx(bonded.C1_uF_per_km, rel=1e-12)



def test_cable_zero_sequence_return_models_are_user_selectable() -> None:
    common = dict(
        frequency_hz=50.0,
        rated_voltage_kv=10.0,
        soil_resistivity_ohm_m=100.0,
        arrangement="trefoil",
        phase_spacing_m=0.12,
        burial_depth_m=1.2,
        conductor_resistance_ohm_per_km=0.0601,
        conductor_gmr_m=0.0065,
        conductor_radius_m=0.008,
        insulation_outer_radius_m=0.021,
        relative_permittivity=2.3,
        sheath_enabled=True,
        sheath_bonding="both_ends",
        sheath_resistance_ohm_per_km=0.20,
        sheath_radius_m=0.024,
    )
    earth = calculate_cable_sequence(zero_sequence_return="earth", **common)
    sheath = calculate_cable_sequence(zero_sequence_return="sheath", **common)
    pscad = calculate_cable_sequence(zero_sequence_return="sheath_earth", **common)

    assert earth.zero_sequence_return == "大地回流"
    assert sheath.zero_sequence_return == "护层回流（同轴下限）"
    assert pscad.zero_sequence_return == "护层+大地并联（PSCAD/Kron近似）"
    assert earth.Z0_ohm_per_km.imag > earth.Z1_ohm_per_km.imag
    assert sheath.Z0_ohm_per_km.imag < earth.Z0_ohm_per_km.imag
    assert sheath.Z0_ohm_per_km.imag < pscad.Z0_ohm_per_km.imag < earth.Z0_ohm_per_km.imag



def test_cable_auto_return_model_follows_sheath_bonding() -> None:
    common = dict(
        frequency_hz=50.0,
        rated_voltage_kv=10.0,
        soil_resistivity_ohm_m=100.0,
        arrangement="trefoil",
        phase_spacing_m=0.12,
        burial_depth_m=1.2,
        conductor_resistance_ohm_per_km=0.0601,
        conductor_gmr_m=0.0065,
        conductor_radius_m=0.008,
        insulation_outer_radius_m=0.021,
        relative_permittivity=2.3,
        sheath_resistance_ohm_per_km=0.20,
        sheath_radius_m=0.024,
    )
    both_ends = calculate_cable_sequence(sheath_enabled=True, sheath_bonding="both_ends", **common)
    cross_bonded = calculate_cable_sequence(sheath_enabled=True, sheath_bonding="cross_bonded", **common)
    single_point = calculate_cable_sequence(sheath_enabled=True, sheath_bonding="single_point", **common)
    no_sheath = calculate_cable_sequence(sheath_enabled=False, sheath_bonding="both_ends", **common)

    assert both_ends.zero_sequence_return == "护层+大地并联（PSCAD/Kron近似）"
    assert cross_bonded.zero_sequence_return == "护层+大地并联（PSCAD/Kron近似）"
    assert single_point.zero_sequence_return == "大地回流"
    assert no_sheath.zero_sequence_return == "大地回流"
    assert both_ends.Z0_ohm_per_km.imag < single_point.Z0_ohm_per_km.imag
