from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


import pytest

from power_tool_approximations import frequency_response_summary, natural_power_and_reactive


def test_frequency_response_default_case_regression() -> None:
    summary = frequency_response_summary(0.08, 8.0, 5.0, 1.2, 4.0, 50.0)
    assert summary.regime == "欠阻尼"
    assert summary.rocof_hz_s == pytest.approx(-0.5, abs=1e-12)
    assert summary.nadir_time_s == pytest.approx(5.2339369742773965, rel=1e-9)
    assert summary.f_min_hz == pytest.approx(48.74409381185, rel=1e-9)


def test_natural_power_and_reactive_default_case_regression() -> None:
    summary = natural_power_and_reactive(500.0, 250.0, None, None, 700.0, 1.2, 200.0)
    assert summary.Pn_MW == pytest.approx(1000.0, rel=1e-12)
    assert summary.delta_Q_Mvar == pytest.approx(-122.4, rel=1e-12)
    assert summary.line_state == "总体发无功（净容性）"
