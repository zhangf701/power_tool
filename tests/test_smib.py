from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


import pytest

from power_tool_smib import kundur_smib_defaults, smib_small_signal_analysis


def _max_real(config: str) -> float:
    params = kundur_smib_defaults()
    params.pop("config")
    result = smib_small_signal_analysis(config, params)
    return float(np.max(np.real(result.eigenvalues)))


def test_smib_default_machine_case_regression() -> None:
    params = kundur_smib_defaults()
    params.pop("config")
    result = smib_small_signal_analysis("machine", params)
    assert result.stable is True
    assert len(result.state_names) == 6
    assert np.max(np.real(result.eigenvalues)) == pytest.approx(-0.12507785817981243, rel=1e-9)


def test_smib_default_avr_case_regression() -> None:
    params = kundur_smib_defaults()
    params.pop("config")
    result = smib_small_signal_analysis("avr", params)
    assert result.stable is False
    assert len(result.state_names) == 9
    assert np.max(np.real(result.eigenvalues)) == pytest.approx(0.36120264510200195, rel=1e-9)


def test_smib_default_avr_pss_case_regression() -> None:
    params = kundur_smib_defaults()
    config = params.pop("config")
    result = smib_small_signal_analysis(config, params)
    assert result.stable is True
    assert len(result.state_names) == 12
    assert np.max(np.real(result.eigenvalues)) == pytest.approx(-0.7386091983594811, rel=1e-9)
    assert result.config_key == "avr_pss"
