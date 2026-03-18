from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


import pytest

from power_tool_common import load_line_params_reference
from power_tool_params import convert_line_to_pu


def test_line_param_conversion_regression() -> None:
    result = convert_line_to_pu(0.028, 0.299, 0.013, 200.0, 100.0, 500.0)
    assert result.R_total_ohm == pytest.approx(5.6, rel=1e-12)
    assert result.X_total_ohm == pytest.approx(59.8, rel=1e-12)
    assert result.B_half_pu == pytest.approx(1.0210176124166828, rel=1e-12)
    assert result.Zc_ohm == pytest.approx(270.5758189903005, rel=1e-12)
    assert result.warnings == []


def test_line_reference_json_contains_750kv_and_1000kv() -> None:
    data = load_line_params_reference()
    voltages = {section.get("voltage_level_kv") for section in data["sections"]}
    assert 750 in voltages
    assert 1000 in voltages

    titles = {section.get("section_title", "") for section in data["sections"]}
    assert any("750" in title for title in titles)
    assert any("1000" in title for title in titles)
