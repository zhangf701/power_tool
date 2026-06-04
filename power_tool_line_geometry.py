"""Compute positive- and zero-sequence overhead-line parameters from geometric data. / 由几何数据计算架空线路正序/零序参数。"""

from __future__ import annotations

import cmath
import math
from dataclasses import dataclass
from typing import Sequence

import numpy as np

from power_tool_common import InputError, _validate_nonnegative, _validate_positive

_MU0 = 4.0 * math.pi * 1e-7
_EPS0 = 8.854187817e-12
_A = np.array(
    [
        [1.0 + 0.0j, 1.0 + 0.0j, 1.0 + 0.0j],
        [1.0 + 0.0j, complex(-0.5, -math.sqrt(3.0) / 2.0), complex(-0.5, math.sqrt(3.0) / 2.0)],
        [1.0 + 0.0j, complex(-0.5, math.sqrt(3.0) / 2.0), complex(-0.5, -math.sqrt(3.0) / 2.0)],
    ],
    dtype=complex,
)
_A_INV = np.linalg.inv(_A)
_TRANSPOSE_PERMUTATIONS: tuple[tuple[int, int, int], ...] = ((0, 1, 2), (1, 2, 0), (2, 0, 1))


@dataclass(frozen=True)
class LineGeometryResult:
    frequency_hz: float
    soil_resistivity_ohm_m: float
    has_ground_wire: bool
    phase_bundle_count: int
    phase_bundle_resistance_ohm_per_km: float
    phase_bundle_gmr_m: float
    phase_bundle_radius_m: float
    D_ab_m: float
    D_bc_m: float
    D_ca_m: float
    Z1_ohm_per_km: complex
    Z0_ohm_per_km: complex
    Y1_S_per_km: complex
    Y0_S_per_km: complex
    C1_uF_per_km: float
    C0_uF_per_km: float
    B1_uS_per_km: float
    B0_uS_per_km: float
    Zabc_ohm_per_km: np.ndarray
    Yabc_S_per_km: np.ndarray
    notes: str




@dataclass(frozen=True)
class CableGeometryResult:
    frequency_hz: float
    rated_voltage_kv: float
    soil_resistivity_ohm_m: float
    arrangement: str
    phase_spacing_m: float
    burial_depth_m: float
    conductor_resistance_ohm_per_km: float
    conductor_gmr_m: float
    conductor_radius_m: float
    insulation_outer_radius_m: float
    relative_permittivity: float
    sheath_enabled: bool
    sheath_bonding: str
    zero_sequence_return: str
    sheath_resistance_ohm_per_km: float
    sheath_radius_m: float
    D_ab_m: float
    D_bc_m: float
    D_ca_m: float
    D_eq_m: float
    Z1_ohm_per_km: complex
    Z0_ohm_per_km: complex
    Y1_S_per_km: complex
    Y0_S_per_km: complex
    C1_uF_per_km: float
    C0_uF_per_km: float
    B1_uS_per_km: float
    B0_uS_per_km: float
    charging_current_A_per_km: float
    phase_positions_m: tuple[tuple[float, float], tuple[float, float], tuple[float, float]]
    notes: str

@dataclass(frozen=True)
class _Conductor:
    x_m: float
    h_m: float
    resistance_ohm_per_km: float
    gmr_m: float
    radius_m: float


def bundle_equivalent_parameters(
    resistance_sub_ohm_per_km: float,
    gmr_sub_m: float,
    radius_sub_m: float,
    bundle_count: int = 1,
    bundle_spacing_m: float = 0.0,
) -> tuple[float, float, float]:
    """Derive equivalent phase-conductor parameters from sub-conductor data. / 由单分裂导线参数得到等效相导线参数。
    
    Return values / 返回值依次为：
    - Equivalent phase-conductor resistance (Ω/km). / 等效相导线电阻（Ω/km）
    - Equivalent phase-conductor GMR (m). / 等效相导线 GMR（m）
    - Equivalent phase-conductor electrostatic radius (m). / 等效相导线电容半径（m）
    
    Conventions / 约定：
    - `bundle_count=1` means a single conductor. / `bundle_count=1` 表示单导线。
    - `bundle_count=2/3/4` are approximated as duplex, equilateral-triplex, and square-quad bundles. / `bundle_count=2/3/4` 分别按双分裂、等边三分裂、正方形四分裂近似。
    - `resistance_sub_ohm_per_km`, `gmr_sub_m`, and `radius_sub_m` are all single sub-conductor data. / `resistance_sub_ohm_per_km`、`gmr_sub_m`、`radius_sub_m` 均为单根子导线数据。"""
    _validate_positive("单分裂导线电阻", resistance_sub_ohm_per_km)
    _validate_positive("单分裂导线 GMR", gmr_sub_m)
    _validate_positive("单分裂导线半径", radius_sub_m)

    if bundle_count not in {1, 2, 3, 4}:
        raise InputError("分裂根数仅支持 1、2、3、4。")

    if bundle_count == 1:
        return resistance_sub_ohm_per_km, gmr_sub_m, radius_sub_m

    _validate_positive("分裂间距", bundle_spacing_m)

    resistance_eq = resistance_sub_ohm_per_km / float(bundle_count)
    if bundle_count == 2:
        gmr_eq = math.sqrt(gmr_sub_m * bundle_spacing_m)
        radius_eq = math.sqrt(radius_sub_m * bundle_spacing_m)
    elif bundle_count == 3:
        gmr_eq = (gmr_sub_m * bundle_spacing_m * bundle_spacing_m) ** (1.0 / 3.0)
        radius_eq = (radius_sub_m * bundle_spacing_m * bundle_spacing_m) ** (1.0 / 3.0)
    else:  # bundle_count == 4, approximated as a square arrangement. / bundle_count == 4，按正方形排列近似
        factor = 2.0 ** 0.125
        gmr_eq = factor * (gmr_sub_m * bundle_spacing_m ** 3) ** 0.25
        radius_eq = factor * (radius_sub_m * bundle_spacing_m ** 3) ** 0.25
    return resistance_eq, gmr_eq, radius_eq


def _validate_phase_positions(phase_positions: Sequence[tuple[float, float]]) -> None:
    if len(phase_positions) != 3:
        raise InputError("相导线几何位置必须恰好提供 A/B/C 三相。")

    names = ("A", "B", "C")
    for name, (x_m, h_m) in zip(names, phase_positions):
        if not math.isfinite(x_m) or not math.isfinite(h_m):
            raise InputError(f"{name} 相坐标必须是有限实数。")
        _validate_positive(f"{name} 相离地高度", h_m)

    for (name_i, (xi, hi)), (name_j, (xj, hj)) in (
        ((names[0], phase_positions[0]), (names[1], phase_positions[1])),
        ((names[1], phase_positions[1]), (names[2], phase_positions[2])),
        ((names[0], phase_positions[0]), (names[2], phase_positions[2])),
    ):
        if math.hypot(xi - xj, hi - hj) <= 1e-9:
            raise InputError(f"{name_i} 与 {name_j} 相几何位置重合，无法计算。")


def _complex_depth(soil_resistivity_ohm_m: float, omega: float) -> complex:
    return cmath.sqrt(soil_resistivity_ohm_m / (1j * omega * _MU0))


def _primitive_series_matrix(
    conductors: Sequence[_Conductor],
    frequency_hz: float,
    soil_resistivity_ohm_m: float,
) -> np.ndarray:
    omega = 2.0 * math.pi * frequency_hz
    p = _complex_depth(soil_resistivity_ohm_m, omega)
    coef = 1j * omega * _MU0 * 1000.0 / (2.0 * math.pi)  # Ω/km / 单位为 Ω/km
    n = len(conductors)
    mat = np.zeros((n, n), dtype=complex)

    for i, ci in enumerate(conductors):
        for j, cj in enumerate(conductors):
            if i == j:
                if ci.h_m <= ci.radius_m:
                    raise InputError("导线离地高度必须大于导线物理半径。")
                mat[i, i] = ci.resistance_ohm_per_km + coef * cmath.log(2.0 * (ci.h_m + p) / ci.gmr_m)
            else:
                dij = math.hypot(ci.x_m - cj.x_m, ci.h_m - cj.h_m)
                if dij <= 1e-12:
                    raise InputError("两导线之间距离为 0，无法构造阻抗矩阵。")
                dij_p = cmath.sqrt((ci.x_m - cj.x_m) ** 2 + (ci.h_m + cj.h_m + 2.0 * p) ** 2)
                mat[i, j] = coef * cmath.log(dij_p / dij)
    return mat


def _primitive_potential_matrix(conductors: Sequence[_Conductor]) -> np.ndarray:
    coef = 1.0 / (2.0 * math.pi * _EPS0)
    n = len(conductors)
    mat = np.zeros((n, n), dtype=float)

    for i, ci in enumerate(conductors):
        for j, cj in enumerate(conductors):
            if i == j:
                if ci.h_m <= ci.radius_m:
                    raise InputError("导线离地高度必须大于导线物理半径。")
                mat[i, i] = coef * math.log(2.0 * ci.h_m / ci.radius_m)
            else:
                dij = math.hypot(ci.x_m - cj.x_m, ci.h_m - cj.h_m)
                if dij <= 1e-12:
                    raise InputError("两导线之间距离为 0，无法构造电位系数矩阵。")
                dij_img = math.hypot(ci.x_m - cj.x_m, ci.h_m + cj.h_m)
                mat[i, j] = coef * math.log(dij_img / dij)
    return mat


def _kron_reduce_with_ground(mat: np.ndarray) -> np.ndarray:
    if mat.shape[0] <= 3:
        return mat.copy()
    mpp = mat[:3, :3]
    mpg = mat[:3, 3:]
    mgp = mat[3:, :3]
    mgg = mat[3:, 3:]
    return mpp - mpg @ np.linalg.inv(mgg) @ mgp


def _circulantize_three_phase(mat: np.ndarray) -> np.ndarray:
    diag = complex(np.trace(mat) / 3.0)
    off = complex((np.sum(mat) - np.trace(mat)) / 6.0)
    out = np.full((3, 3), off, dtype=complex)
    np.fill_diagonal(out, diag)
    return out


def _sequence_transform(mat_abc: np.ndarray) -> np.ndarray:
    return _A_INV @ mat_abc @ _A


def calculate_overhead_line_sequence(
    *,
    frequency_hz: float,
    soil_resistivity_ohm_m: float,
    phase_positions: Sequence[tuple[float, float]],
    phase_resistance_ohm_per_km: float,
    phase_gmr_m: float,
    phase_radius_m: float,
    phase_bundle_count: int = 1,
    phase_bundle_spacing_m: float = 0.0,
    has_ground_wire: bool = False,
    ground_wire_position: tuple[float, float] | None = None,
    ground_wire_resistance_ohm_per_km: float = 0.0,
    ground_wire_gmr_m: float = 0.0,
    ground_wire_radius_m: float = 0.0,
) -> LineGeometryResult:
    """Calculate overhead-line sequence parameters from conductor geometry. / 按导线几何数据计算架空线路序参数。
    
    Parameter notes / 参数说明
    ----------------------------
    `phase_positions` contains the `(x, h)` coordinates of the three phase conductors in metres, where `h` is the height above ground. / `phase_positions` 为三相导线的 `(x, h)` 坐标（m），其中 `h` 为离地高度。
    
    Model / 计算模型：
    - Series parameters use the complex-depth approximation to include earth-return effect and soil resistivity. / 串联参数采用复深度近似计及大地回路与土壤电阻率。
    - Shunt capacitance/admittance uses the method-of-images potential-coefficient matrix. / 对地电容/电纳采用镜像法电位系数矩阵。
    - If a ground wire is enabled, it is treated as a continuously grounded conductor and eliminated through Kron reduction. / 若启用地线，则按连续接地导体处理，并通过 Kron 消去得到三相等值矩阵。
    - Final positive- and zero-sequence values are averaged over a fully transposed three-section line. / 最终按三段完全换位平均，输出正序和零序参数。"""
    _validate_positive("频率", frequency_hz)
    _validate_positive("土壤电阻率", soil_resistivity_ohm_m)
    _validate_phase_positions(phase_positions)

    phase_r_eq, phase_gmr_eq, phase_radius_eq = bundle_equivalent_parameters(
        phase_resistance_ohm_per_km,
        phase_gmr_m,
        phase_radius_m,
        phase_bundle_count,
        phase_bundle_spacing_m,
    )

    phase_cond = [
        _Conductor(x_m=x_m, h_m=h_m, resistance_ohm_per_km=phase_r_eq, gmr_m=phase_gmr_eq, radius_m=phase_radius_eq)
        for x_m, h_m in phase_positions
    ]

    ground_cond: list[_Conductor] = []
    if has_ground_wire:
        if ground_wire_position is None:
            raise InputError("已勾选有地线，但未提供地线几何位置。")
        xg_m, hg_m = ground_wire_position
        if not math.isfinite(xg_m) or not math.isfinite(hg_m):
            raise InputError("地线坐标必须是有限实数。")
        _validate_positive("地线离地高度", hg_m)
        _validate_nonnegative("地线交流电阻", ground_wire_resistance_ohm_per_km)
        _validate_positive("地线 GMR", ground_wire_gmr_m)
        _validate_positive("地线半径", ground_wire_radius_m)
        ground_cond.append(
            _Conductor(
                x_m=xg_m,
                h_m=hg_m,
                resistance_ohm_per_km=ground_wire_resistance_ohm_per_km,
                gmr_m=ground_wire_gmr_m,
                radius_m=ground_wire_radius_m,
            )
        )

    z_abc_acc = np.zeros((3, 3), dtype=complex)
    y_abc_acc = np.zeros((3, 3), dtype=complex)

    for perm in _TRANSPOSE_PERMUTATIONS:
        phase_section = [phase_cond[idx] for idx in perm]
        conductors = phase_section + ground_cond

        z_primitive = _primitive_series_matrix(conductors, frequency_hz, soil_resistivity_ohm_m)
        z_reduced = _kron_reduce_with_ground(z_primitive)
        z_abc_acc += z_reduced

        p_primitive = _primitive_potential_matrix(conductors)
        p_reduced = _kron_reduce_with_ground(p_primitive)
        c_abc_f_per_km = np.linalg.inv(p_reduced) * 1000.0
        y_abc_acc += 1j * 2.0 * math.pi * frequency_hz * c_abc_f_per_km

    z_abc = _circulantize_three_phase(z_abc_acc / 3.0)
    y_abc = _circulantize_three_phase(y_abc_acc / 3.0)

    z_012 = _sequence_transform(z_abc)
    y_012 = _sequence_transform(y_abc)

    z0 = complex(z_012[0, 0])
    z1 = complex(z_012[1, 1])
    y0 = complex(y_012[0, 0])
    y1 = complex(y_012[1, 1])

    omega = 2.0 * math.pi * frequency_hz
    c1_uF_per_km = max(0.0, y1.imag / omega * 1e6)
    c0_uF_per_km = max(0.0, y0.imag / omega * 1e6)
    b1_uS_per_km = y1.imag * 1e6
    b0_uS_per_km = y0.imag * 1e6

    (xa, ha), (xb, hb), (xc, hc) = phase_positions
    d_ab = math.hypot(xa - xb, ha - hb)
    d_bc = math.hypot(xb - xc, hb - hc)
    d_ca = math.hypot(xc - xa, hc - ha)

    notes = (
        "假设：单回架空线路、三相导线型号一致并按三段完全换位平均；"
        "串联参数用复深度近似计及土壤电阻率，大地回路电阻/电抗已包含在序阻抗内；"
        "对地电容/电纳采用镜像法电位系数矩阵，介质电导与土壤介电损耗未计。"
    )
    if has_ground_wire:
        notes += " 地线按连续接地导体处理，并通过 Kron 消去得到三相等值矩阵。"
    else:
        notes += " 当前计算未考虑地线屏蔽效应。"
    if phase_bundle_count == 4:
        notes += " 四分裂导线按正方形排列近似。"

    return LineGeometryResult(
        frequency_hz=frequency_hz,
        soil_resistivity_ohm_m=soil_resistivity_ohm_m,
        has_ground_wire=has_ground_wire,
        phase_bundle_count=phase_bundle_count,
        phase_bundle_resistance_ohm_per_km=phase_r_eq,
        phase_bundle_gmr_m=phase_gmr_eq,
        phase_bundle_radius_m=phase_radius_eq,
        D_ab_m=d_ab,
        D_bc_m=d_bc,
        D_ca_m=d_ca,
        Z1_ohm_per_km=z1,
        Z0_ohm_per_km=z0,
        Y1_S_per_km=y1,
        Y0_S_per_km=y0,
        C1_uF_per_km=c1_uF_per_km,
        C0_uF_per_km=c0_uF_per_km,
        B1_uS_per_km=b1_uS_per_km,
        B0_uS_per_km=b0_uS_per_km,
        Zabc_ohm_per_km=z_abc,
        Yabc_S_per_km=y_abc,
        notes=notes,
    )



def _normalize_cable_arrangement(arrangement: str) -> str:
    key = (arrangement or "").strip().lower()
    if key in {"flat", "horizontal", "h", "水平排列"}:
        return "flat"
    if key in {"trefoil", "triangle", "triangular", "t", "品字形", "三角", "三角排列"}:
        return "trefoil"
    raise InputError("电缆排列方式仅支持：水平排列/品字形。")


def _normalize_sheath_bonding(sheath_bonding: str) -> str:
    key = (sheath_bonding or "").strip().lower()
    if key in {"both_ends", "both", "solid", "solid_bonded", "两端接地"}:
        return "both_ends"
    if key in {"cross_bonded", "cross", "交叉互联"}:
        return "cross_bonded"
    if key in {"single_point", "single", "one_end", "单端接地"}:
        return "single_point"
    if key in {"", "none", "disabled", "未启用"}:
        return "disabled"
    return key


def _cable_arrangement_label(code: str) -> str:
    return "品字形" if code == "trefoil" else "水平排列"


def _sheath_bonding_label(code: str) -> str:
    if code == "both_ends":
        return "两端接地"
    if code == "cross_bonded":
        return "交叉互联"
    if code == "single_point":
        return "单端接地"
    return "未启用"


def _normalize_cable_return_model(return_model: str) -> str:
    key = (return_model or "").strip().lower()
    if key in {"", "auto", "自动", "自适应"}:
        return "auto"
    if key in {"earth", "ground", "ground_return", "大地回流", "仅大地回流"}:
        return "earth"
    if key in {"sheath", "screen", "shield", "coaxial", "sheath_only", "护层回流", "护层回流下限", "同轴下限"}:
        return "sheath"
    if key in {
        "sheath_earth",
        "sheath+earth",
        "parallel",
        "kron",
        "pscad",
        "pscad_kron",
        "护层+大地",
        "护层+大地并联",
        "护层+大地并联（pscad近似）",
        "护层+大地并联(pscad近似)",
    }:
        return "sheath_earth"
    raise InputError("电缆零序回流方式仅支持：自动/大地回流/护层回流/护层+大地并联。")


def _cable_return_label(code: str) -> str:
    if code == "earth":
        return "大地回流"
    if code == "sheath":
        return "护层回流（同轴下限）"
    if code == "sheath_earth":
        return "护层+大地并联（PSCAD/Kron近似）"
    return "自动"


def _cable_sheath_kron_sequence(
    phase_positions: tuple[tuple[float, float], tuple[float, float], tuple[float, float]],
    frequency_hz: float,
    soil_resistivity_ohm_m: float,
    conductor_resistance_ohm_per_km: float,
    conductor_gmr_m: float,
    sheath_resistance_ohm_per_km: float,
    sheath_radius_m: float,
) -> np.ndarray:
    """Return sequence matrix after eliminating metallic sheaths as conductor layers."""
    omega = 2.0 * math.pi * frequency_hz
    p = _complex_depth(soil_resistivity_ohm_m, omega)
    coef = 1j * omega * _MU0 * 1000.0 / (2.0 * math.pi)
    sheath_gmr = sheath_radius_m * math.exp(-0.25)
    z = np.zeros((6, 6), dtype=complex)

    for i, (x_i, h_i) in enumerate(phase_positions):
        if h_i <= sheath_radius_m:
            raise InputError("电缆中心埋深必须大于护层半径，无法构造护层回流矩阵。")
        core = i
        sheath = i + 3
        z[core, core] = conductor_resistance_ohm_per_km + coef * cmath.log(2.0 * (h_i + p) / conductor_gmr_m)
        z[sheath, sheath] = sheath_resistance_ohm_per_km + coef * cmath.log(2.0 * (h_i + p) / sheath_gmr)
        z[core, sheath] = z[sheath, core] = coef * cmath.log(2.0 * (h_i + p) / sheath_radius_m)

    for i, (x_i, h_i) in enumerate(phase_positions):
        for j, (x_j, h_j) in enumerate(phase_positions):
            if i == j:
                continue
            dij = math.hypot(x_i - x_j, h_i - h_j)
            if dij <= 1e-12:
                raise InputError("两根电缆中心距离为 0，无法构造互阻抗矩阵。")
            dij_p = cmath.sqrt((x_i - x_j) ** 2 + (h_i + h_j + 2.0 * p) ** 2)
            zij = coef * cmath.log(dij_p / dij)
            for row in (i, i + 3):
                for col in (j, j + 3):
                    z[row, col] = zij

    zcc = z[:3, :3]
    zcs = z[:3, 3:]
    zsc = z[3:, :3]
    zss = z[3:, 3:]
    try:
        reduced = zcc - zcs @ np.linalg.inv(zss) @ zsc
    except np.linalg.LinAlgError as exc:
        raise InputError("护层回流矩阵奇异，无法进行 Kron 消元。") from exc
    return _sequence_transform(_circulantize_three_phase(reduced))


def _cable_phase_positions(arrangement: str, phase_spacing_m: float, burial_depth_m: float) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float]]:
    arrangement_key = _normalize_cable_arrangement(arrangement)
    _validate_positive("相间中心距", phase_spacing_m)
    _validate_positive("电缆埋深", burial_depth_m)

    if arrangement_key == "flat":
        return ((-phase_spacing_m, burial_depth_m), (0.0, burial_depth_m), (phase_spacing_m, burial_depth_m))

    tri_h = math.sqrt(3.0) / 2.0 * phase_spacing_m
    return (
        (-phase_spacing_m / 2.0, burial_depth_m + tri_h / 3.0),
        (phase_spacing_m / 2.0, burial_depth_m + tri_h / 3.0),
        (0.0, burial_depth_m - 2.0 * tri_h / 3.0),
    )


def calculate_cable_sequence(
    *,
    frequency_hz: float,
    rated_voltage_kv: float,
    soil_resistivity_ohm_m: float,
    arrangement: str,
    phase_spacing_m: float,
    burial_depth_m: float,
    conductor_resistance_ohm_per_km: float,
    conductor_gmr_m: float,
    conductor_radius_m: float,
    insulation_outer_radius_m: float,
    relative_permittivity: float,
    sheath_enabled: bool = True,
    sheath_bonding: str = "both_ends",
    zero_sequence_return: str = "auto",
    sheath_resistance_ohm_per_km: float = 0.2,
    sheath_radius_m: float = 0.024,
) -> CableGeometryResult:
    """Approximate sequence parameters for three single-core power cables."""
    _validate_positive("频率", frequency_hz)
    _validate_positive("额定线电压", rated_voltage_kv)
    _validate_positive("土壤电阻率", soil_resistivity_ohm_m)
    _validate_positive("导体交流电阻", conductor_resistance_ohm_per_km)
    _validate_positive("导体 GMR", conductor_gmr_m)
    _validate_positive("导体半径", conductor_radius_m)
    _validate_positive("绝缘外半径", insulation_outer_radius_m)
    _validate_positive("绝缘相对介电常数", relative_permittivity)

    if insulation_outer_radius_m <= conductor_radius_m:
        raise InputError("绝缘外半径必须大于导体半径。")

    arrangement_code = _normalize_cable_arrangement(arrangement)
    phase_positions = _cable_phase_positions(arrangement_code, phase_spacing_m, burial_depth_m)
    min_depth = min(depth for _x, depth in phase_positions)
    if min_depth <= insulation_outer_radius_m:
        raise InputError("电缆中心埋深必须大于绝缘外半径，避免几何越界。")

    sheath_r = 0.0
    sheath_radius = 0.0
    bonding_code = _normalize_sheath_bonding(sheath_bonding)
    if sheath_enabled:
        _validate_positive("金属护层电阻", sheath_resistance_ohm_per_km)
        _validate_positive("金属护层半径", sheath_radius_m)
        if sheath_radius_m <= insulation_outer_radius_m:
            raise InputError("金属护层半径应大于绝缘外半径。")
        sheath_r = sheath_resistance_ohm_per_km
        sheath_radius = sheath_radius_m
    else:
        bonding_code = "disabled"

    conductors = [
        _Conductor(x_m=x_m, h_m=depth_m, resistance_ohm_per_km=conductor_resistance_ohm_per_km, gmr_m=conductor_gmr_m, radius_m=conductor_radius_m)
        for x_m, depth_m in phase_positions
    ]
    z_abc_raw = _primitive_series_matrix(conductors, frequency_hz, soil_resistivity_ohm_m)
    z_abc = _circulantize_three_phase(z_abc_raw)
    z_012 = _sequence_transform(z_abc)
    z0_earth = complex(z_012[0, 0])
    z1 = complex(z_012[1, 1])

    requested_return_model = _normalize_cable_return_model(zero_sequence_return)
    if requested_return_model == "auto":
        return_model_code = "sheath_earth" if sheath_enabled and bonding_code in {"both_ends", "cross_bonded"} else "earth"
        auto_note = "零序回流方式由护层接地方式自动推断。"
    else:
        return_model_code = requested_return_model
        auto_note = "零序回流方式由高级设置手动指定。"

    forced_note = ""
    if return_model_code in {"sheath", "sheath_earth"} and (not sheath_enabled or bonding_code not in {"both_ends", "cross_bonded"}):
        forced_note = "所选回流方式需要连续接地护层；当前护层未启用或为单端接地，已自动退回大地回流。"
        return_model_code = "earth"

    if return_model_code == "sheath":
        x_loop = 2.0 * math.pi * frequency_hz * 2.0e-4 * math.log(max(sheath_radius_m / conductor_gmr_m, 1.0 + 1e-9))
        z0 = complex(conductor_resistance_ohm_per_km + sheath_resistance_ohm_per_km, x_loop)
        zero_note = "零序按芯线-金属护层同轴回路下限近似，适合估计护层强回流时的最小零序电抗。"
    elif return_model_code == "sheath_earth":
        z012_kron = _cable_sheath_kron_sequence(
            phase_positions,
            frequency_hz,
            soil_resistivity_ohm_m,
            conductor_resistance_ohm_per_km,
            conductor_gmr_m,
            sheath_resistance_ohm_per_km,
            sheath_radius_m,
        )
        z0 = complex(z012_kron[0, 0])
        z1 = complex(z012_kron[1, 1])
        zero_note = "零序按芯线、金属护层与大地回路组成的多导体矩阵计算，并对护层作 Kron 消元，近似 PSCAD LCP 的导体层消元思路。"
        if bonding_code == "cross_bonded":
            zero_note += " 交叉互联可降低工频护层环流损耗，但零序故障暂按等效连续护层回流近似。"
    else:
        z0 = z0_earth
        zero_note = "零序按大地回路复深度近似，未把护层作为连续回流通道。"
    if forced_note:
        zero_note = f"{zero_note} {forced_note}"

    c_f_per_km = 2.0 * math.pi * _EPS0 * relative_permittivity / math.log(insulation_outer_radius_m / conductor_radius_m) * 1000.0
    omega = 2.0 * math.pi * frequency_hz
    y = 1j * omega * c_f_per_km
    c_uF_per_km = c_f_per_km * 1e6
    b_uS_per_km = y.imag * 1e6
    charging_current = omega * c_f_per_km * (rated_voltage_kv * 1000.0 / math.sqrt(3.0))

    (xa, da), (xb, db), (xc, dc) = phase_positions
    d_ab = math.hypot(xa - xb, da - db)
    d_bc = math.hypot(xb - xc, db - dc)
    d_ca = math.hypot(xc - xa, dc - da)
    d_eq = (d_ab * d_bc * d_ca) ** (1.0 / 3.0)

    x0_x1_ratio = (z0.imag / z1.imag) if abs(z1.imag) > 1e-12 else float("inf")
    if z0.imag < z1.imag:
        ratio_note = (
            f"当前 X0/X1 = {x0_x1_ratio:.3f}，小于 1；这通常只在护层/屏蔽层形成近距离零序回流时出现。"
            "若用于保护整定或短路容量校核，应优先采用厂家序阻抗表、实测值或完整多导体矩阵。"
        )
    else:
        ratio_note = f"当前 X0/X1 = {x0_x1_ratio:.3f}。"

    notes = (
        "假设：三根单芯电缆按水平或品字形敷设，芯线型号一致；"
        "电容按芯线-绝缘-屏蔽同轴结构计算，因此 C1 与 C0 取同一绝缘电容。"
        f" 零序回流方式：{_cable_return_label(return_model_code)}。{auto_note}{zero_note} {ratio_note} "
        "未计护层环流损耗精细分布、铠装/钢管、邻近效应、温度修正、交叉互联分段不平衡和多回电缆互感。"
    )

    return CableGeometryResult(
        frequency_hz=frequency_hz,
        rated_voltage_kv=rated_voltage_kv,
        soil_resistivity_ohm_m=soil_resistivity_ohm_m,
        arrangement=_cable_arrangement_label(arrangement_code),
        phase_spacing_m=phase_spacing_m,
        burial_depth_m=burial_depth_m,
        conductor_resistance_ohm_per_km=conductor_resistance_ohm_per_km,
        conductor_gmr_m=conductor_gmr_m,
        conductor_radius_m=conductor_radius_m,
        insulation_outer_radius_m=insulation_outer_radius_m,
        relative_permittivity=relative_permittivity,
        sheath_enabled=sheath_enabled,
        sheath_bonding=_sheath_bonding_label(bonding_code),
        zero_sequence_return=_cable_return_label(return_model_code),
        sheath_resistance_ohm_per_km=sheath_r,
        sheath_radius_m=sheath_radius,
        D_ab_m=d_ab,
        D_bc_m=d_bc,
        D_ca_m=d_ca,
        D_eq_m=d_eq,
        Z1_ohm_per_km=z1,
        Z0_ohm_per_km=z0,
        Y1_S_per_km=y,
        Y0_S_per_km=y,
        C1_uF_per_km=c_uF_per_km,
        C0_uF_per_km=c_uF_per_km,
        B1_uS_per_km=b_uS_per_km,
        B0_uS_per_km=b_uS_per_km,
        charging_current_A_per_km=charging_current,
        phase_positions_m=phase_positions,
        notes=notes,
    )


__all__ = [
    "LineGeometryResult",
    "CableGeometryResult",
    "bundle_equivalent_parameters",
    "calculate_overhead_line_sequence",
    "calculate_cable_sequence",
]
