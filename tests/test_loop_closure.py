from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from power_tool_common import InputError
from power_tool_loop_closure import loop_closure_analysis


def _appendix_like_result():
    return loop_closure_analysis(
        u1_kv_ll=10.0,
        u2_kv_ll=10.0,
        angle_deg=14.0,
        r_loop_ohm=1.13,
        x_loop_ohm=4.20,
        frequency_hz=50.0,
        closure_node_index=4,
        node_injections_A=[79.35, 117.40, 116.60, 0.0, 136.69, 58.81, 158.66],
        node_labels=["A", "B", "C", "联络点", "D", "E", "F"],
        power_factor=0.99,
        pf_mode="lagging",
        total_length_km=11.0,
        segment_ratios=[1.0] * 8,
        ampacity_A=442.0,
        overload_factor=1.5,
    )


def test_loop_closure_appendix_like_regression() -> None:
    result = _appendix_like_result()
    assert result.steady_loop_current_magnitude_A == pytest.approx(323.54810130482304, rel=1e-12)
    assert result.steady_loop_current_angle_deg == pytest.approx(22.058703208769636, rel=1e-12)
    assert abs(result.post_left_source_A) == pytest.approx(166.03704456889957, rel=1e-12)
    assert abs(result.post_right_source_A) == pytest.approx(670.9872383796201, rel=1e-12)
    assert result.two_tau_s == pytest.approx(0.02366197384021099, rel=1e-12)
    assert result.overloaded_segments == ["F → 右端"]


def test_loop_closure_tie_adjacent_segments_equal_loop_current() -> None:
    result = _appendix_like_result()
    left_tie = result.segment_results[3]
    right_tie = result.segment_results[4]
    assert left_tie.pre_magnitude_A == pytest.approx(0.0, abs=1e-12)
    assert right_tie.pre_magnitude_A == pytest.approx(0.0, abs=1e-12)
    assert left_tie.post_magnitude_A == pytest.approx(result.steady_loop_current_magnitude_A, rel=1e-12)
    assert right_tie.post_magnitude_A == pytest.approx(result.steady_loop_current_magnitude_A, rel=1e-12)


def test_loop_closure_requires_empty_closure_node() -> None:
    with pytest.raises(InputError):
        loop_closure_analysis(
            u1_kv_ll=10.0,
            u2_kv_ll=10.0,
            angle_deg=10.0,
            r_loop_ohm=1.0,
            x_loop_ohm=4.0,
            frequency_hz=50.0,
            closure_node_index=2,
            node_injections_A=[100.0, 20.0, 0.0],
        )
