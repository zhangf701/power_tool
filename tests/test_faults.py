from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from power_tool_common import InputError
from power_tool_faults import short_circuit_capacity


def test_short_circuit_single_phase_ground_regression() -> None:
    result = short_circuit_capacity(110.0, "A相接地", 2000.0, 10.0, 30.0, 0.05, 0.40, 0.15, 1.20, "直接接地", 0.0, 0.0, 0.0, 31.5)
    assert result.fault_type == "A相接地"
    assert result.I_break_kA == pytest.approx(2.4235987107451686, rel=1e-12)
    assert result.breaker_ok is True


def test_short_circuit_invalid_neutral_mode_raises_input_error() -> None:
    with pytest.raises(InputError):
        short_circuit_capacity(110.0, "A相接地", 2000.0, 10.0, 30.0, 0.05, 0.40, 0.15, 1.20, "未知接地方式", 0.0, 0.0, 0.0, 31.5)


def test_short_circuit_dual_source_mode_supports_fault_location() -> None:
    result = short_circuit_capacity(
        110.0, "A相接地", 2000.0, 10.0, 30.0, 0.05, 0.40, 0.15, 1.20,
        "直接接地", 0.0, 0.0, 0.0, 31.5,
        network_mode="双电源", s_sc_right_mva=3000.0, xr_sys_right=12.0,
        fault_pos_from_left_pct=40.0,
    )
    assert "双电源" in result.network_mode
    assert result.fault_pos_from_left_pct == pytest.approx(40.0)
    assert abs(result.Va_V) < 1e-6
    assert result.I_break_kA > 0.0


def test_short_circuit_dual_source_requires_right_side_inputs() -> None:
    with pytest.raises(InputError):
        short_circuit_capacity(
            110.0, "A相接地", 2000.0, 10.0, 30.0, 0.05, 0.40, 0.15, 1.20,
            "直接接地", 0.0, 0.0, 0.0, 31.5,
            network_mode="双电源",
        )


def test_short_circuit_dual_source_angle_difference_changes_result() -> None:
    base = short_circuit_capacity(
        110.0, "AB两相短路", 2000.0, 10.0, 30.0, 0.05, 0.40, 0.15, 1.20,
        "直接接地", 0.0, 0.0, 0.0, None,
        network_mode="双电源", s_sc_right_mva=2000.0, xr_sys_right=10.0, fault_pos_from_left_pct=50.0,
        delta_right_deg=0.0,
    )
    shifted = short_circuit_capacity(
        110.0, "AB两相短路", 2000.0, 10.0, 30.0, 0.05, 0.40, 0.15, 1.20,
        "直接接地", 0.0, 0.0, 0.0, None,
        network_mode="双电源", s_sc_right_mva=2000.0, xr_sys_right=10.0, fault_pos_from_left_pct=50.0,
        delta_right_deg=20.0,
    )
    assert abs(base.I1_A - shifted.I1_A) > 1e-3


def test_short_circuit_phase_specific_boundaries_are_respected() -> None:
    common = (110.0, 2000.0, 10.0, 30.0, 0.05, 0.40, 0.15, 1.20, "直接接地", 0.0, 0.0, 0.0, None)

    b_g = short_circuit_capacity(common[0], "B相接地", *common[1:])
    c_g = short_circuit_capacity(common[0], "C相接地", *common[1:])
    assert abs(b_g.Vb_V) < 1e-6
    assert abs(c_g.Vc_V) < 1e-6
    assert abs(b_g.Ia_A) < 1e-6 and abs(b_g.Ic_A) < 1e-6
    assert abs(c_g.Ia_A) < 1e-6 and abs(c_g.Ib_A) < 1e-6

    ab = short_circuit_capacity(common[0], "AB两相短路", *common[1:])
    ca = short_circuit_capacity(common[0], "CA两相短路", *common[1:])
    assert abs(ab.Va_V - ab.Vb_V) < 1e-6
    assert abs(ab.Ic_A) < 1e-6
    assert abs(ca.Vc_V - ca.Va_V) < 1e-6
    assert abs(ca.Ib_A) < 1e-6

    abg = short_circuit_capacity(common[0], "AB两相接地", *common[1:])
    cag = short_circuit_capacity(common[0], "CA两相接地", *common[1:])
    assert abs(abg.Va_V) < 1e-6 and abs(abg.Vb_V) < 1e-6 and abs(abg.Ic_A) < 1e-6
    assert abs(cag.Vc_V) < 1e-6 and abs(cag.Va_V) < 1e-6 and abs(cag.Ib_A) < 1e-6
