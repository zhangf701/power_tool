from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


from power_tool_gui import _detect_key_conclusion_lines, _notebook_style_spec


def test_key_conclusion_line_detection() -> None:
    text = """推导过程：略
运行区间判断：总体发无功（净容性）
说明：这不是关键结论
稳定性判断：[稳定]
  匹配：额定开断电流 ≥ 计算开断电流。
"""
    assert _detect_key_conclusion_lines(text) == [2, 4, 5]


def test_notebook_style_spec_uses_same_padding_for_selected_and_unselected() -> None:
    spec = _notebook_style_spec()
    padding_map = dict(spec["map"]["padding"])
    background_map = dict(spec["map"]["background"])
    assert padding_map["selected"] == (16, 8)
    assert padding_map["!selected"] == (16, 8)
    assert background_map["selected"] == "#173f7a"
