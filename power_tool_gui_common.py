"""Shared imports, constants, and helpers for PowerTool GUI mixins. / PowerTool GUI mixin 共享导入、常量与辅助函数。"""


from __future__ import annotations


import math
import threading
from datetime import datetime
from pathlib import Path

import tkinter as tk


from tkinter import filedialog, messagebox, ttk


from tkinter.scrolledtext import ScrolledText


import matplotlib


import matplotlib.font_manager as _fm


import numpy as np


from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk


from matplotlib.lines import Line2D
from matplotlib.figure import Figure
from matplotlib.offsetbox import AnnotationBbox, DrawingArea, HPacker, TextArea, VPacker
from matplotlib.patches import Circle, Rectangle


from power_tool_common import InputError, _safe_float, _validate_positive, _validate_nonnegative, load_line_params_reference


from power_tool_params import _format_warnings, convert_2wt_to_pu, convert_3wt_to_pu, convert_line_to_pu


from power_tool_approximations import (
    electromechanical_frequency,
    first_order_frequency_response_value,
    frequency_response_summary,
    frequency_response_value,
    natural_power_and_reactive,
    static_voltage_stability,
)


from power_tool_faults import short_circuit_capacity


from power_tool_stability import equal_area_criterion, impact_method


from power_tool_smib import (
    _SMIB_CONFIG_KEY,
    _SMIB_CONFIG_OPTIONS,
    _SMIB_STATE_LABELS,
    _format_eigenvalue,
    _smib_modal_rows,
    kundur_smib_defaults,
    smib_small_signal_analysis,
)

from power_tool_line_geometry import calculate_cable_sequence, calculate_overhead_line_sequence
from power_tool_sag import analyze_conductor_sag
from power_tool_ai import PowerToolAIError, api_key_status, ask_ai, config_path, load_ai_config
from power_tool_loop_closure import loop_closure_analysis
from power_tool_avc import simulate_avc_strategy
from power_tool_comtrade import (
    estimate_sampling_rate,
    export_waveform_record,
    fourier_summary,
    parse_waveform_file,
    prony_like_summary,
    sequence_components,
    sequence_phasors,
    single_frequency_phasor,
)
from power_tool_i18n import (
    KEY_CONCLUSION_PREFIXES_EN,
    display_text,
    install_runtime_hooks,
    logic_text,
    normalize_language,
    set_active_language,
    translate_text,
    translate_widget_tree,
)


# Chinese-font configuration / 中文字体配置 ──────────────────────────────────────────────────────────────
_CN_FONT_CANDIDATES = [
    "WenQuanYi Zen Hei",
    "WenQuanYi Micro Hei",
    "Noto Sans CJK JP",
    "Noto Serif CJK JP",
    "SimHei",
    "SimSun",
    "Microsoft YaHei",
    "AR PL UMing CN",
]

_available_fonts = {f.name for f in _fm.fontManager.ttflist}
_cn_font = next((f for f in _CN_FONT_CANDIDATES if f in _available_fonts), None)

if _cn_font:
    matplotlib.rcParams["font.family"] = "sans-serif"
    matplotlib.rcParams["font.sans-serif"] = [_cn_font] + matplotlib.rcParams["font.sans-serif"]

matplotlib.rcParams["axes.unicode_minus"] = False
matplotlib.rcParams.update({
    "figure.facecolor": "#ffffff",
    "axes.facecolor": "#ffffff",
    "savefig.facecolor": "#ffffff",
    "axes.edgecolor": "#d0d9e3",
    "axes.labelcolor": "#243447",
    "axes.titlecolor": "#243447",
    "axes.titleweight": "bold",
    "grid.color": "#d9e3ee",
    "grid.alpha": 0.9,
    "grid.linewidth": 0.8,
    "xtick.color": "#5a6c7f",
    "ytick.color": "#5a6c7f",
    "legend.frameon": True,
    "legend.facecolor": "#ffffff",
    "legend.edgecolor": "#d9e3ee",
    "legend.framealpha": 0.95,
    "figure.autolayout": False,
})
# End of font configuration / 中文字体配置结束 ─────────────────────────────────────────────────────────

_KEY_CONCLUSION_PREFIXES = (
    "运行区间判断：",
    "稳定性判断：",
    "结论：",
    "稳定性：",
    "匹配：",
    "不匹配：",
    *KEY_CONCLUSION_PREFIXES_EN,
)


def _lang_of(obj: object | None) -> str:
    """Return the active UI language. / 返回当前界面语言。"""
    return normalize_language(getattr(obj, "language", "zh"))


def _tr_obj(obj: object | None, text: str) -> str:
    """Translate text for a GUI object. / 按 GUI 对象语言翻译文本。"""
    return translate_text(text, _lang_of(obj))


def _logic_obj(obj: object | None, text: str) -> str:
    """Map a display label back to the logic label. / 将显示标签映射回逻辑标签。"""
    return logic_text(text, _lang_of(obj))


def _display_obj(obj: object | None, text: str) -> str:
    """Map a logic label to the display label. / 将逻辑标签映射为显示标签。"""
    return display_text(text, _lang_of(obj))


def _detect_key_conclusion_lines(text: str) -> list[int]:
    """Detect key conclusion lines in result text for red highlighting. / 识别结果文本中的关键性结论行，用于红色高亮。"""
    rows: list[int] = []
    for idx, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if stripped and any(stripped.startswith(prefix) for prefix in _KEY_CONCLUSION_PREFIXES):
            rows.append(idx)
    return rows


def _notebook_style_spec() -> dict[str, dict[str, object]]:
    """Return notebook-style settings so the selected tab keeps its size and uses dark-blue emphasis. / Notebook 样式规格：选中标签不缩小，并以深蓝色区分。"""
    return {
        "configure": {
            "TNotebook": {"background": "#f3f5f7", "borderwidth": 0},
            "TNotebook.Tab": {"padding": (16, 8), "borderwidth": 1},
        },
        "map": {
            "padding": [("selected", (16, 8)), ("!selected", (16, 8))],
            "expand": [("selected", (0, 0, 0, 0)), ("!selected", (0, 0, 0, 0))],
            "background": [("selected", "#173f7a"), ("!selected", "#dfe5ec")],
            "foreground": [("selected", "#ffffff"), ("!selected", "#1e2b37")],
        },
    }


_MANUAL_LIBRARY: tuple[dict[str, str], ...] = (
    {"title_zh": "PowerTool 手册总览", "title_en": "PowerTool Manual Overview", "basename": "PowerTool_Overview"},
    {"title_zh": "频率动态", "title_en": "Frequency Dynamics", "basename": "PowerTool_Frequency_Dynamics"},
    {"title_zh": "机电振荡", "title_en": "Electromechanical Oscillation", "basename": "PowerTool_Electromechanical_Oscillation"},
    {"title_zh": "电压无功分析：静态电压稳定", "title_en": "Voltage / Reactive Power Analysis: Static Voltage Stability", "basename": "PowerTool_Voltage_Reactive_Static_Voltage_Stability"},
    {"title_zh": "电压无功分析：线路自然功率与无功", "title_en": "Voltage / Reactive Power Analysis: Line Natural Power and Reactive Power", "basename": "PowerTool_Voltage_Reactive_Line_Natural_Power_and_Reactive_Power"},
    {"title_zh": "电压无功分析：AVC策略模拟", "title_en": "Voltage / Reactive Power Analysis: AVC Strategy Simulation", "basename": "PowerTool_Voltage_Reactive_AVC_Strategy_Simulation"},
    {"title_zh": "暂稳评估", "title_en": "Transient Stability Assessment", "basename": "PowerTool_Transient_Stability_Assessment"},
    {"title_zh": "小扰动分析", "title_en": "Small-Signal Analysis", "basename": "PowerTool_Small_Signal_Analysis"},
    {"title_zh": "配电网合环分析", "title_en": "Distribution Loop-Closure Analysis", "basename": "PowerTool_Distribution_Loop_Closure_Analysis"},
    {"title_zh": "参数校核与标幺值：线路", "title_en": "Parameter Validation & Per-Unit: Lines and Cables", "basename": "PowerTool_Parameter_Validation_Overhead_Line"},
    {"title_zh": "参数校核与标幺值：导线弧垂", "title_en": "Parameter Validation & Per-Unit: Conductor Sag", "basename": "PowerTool_Parameter_Validation_Conductor_Sag"},
    {"title_zh": "参数校核与标幺值：两绕组变压器", "title_en": "Parameter Validation & Per-Unit: Two-Winding Transformer", "basename": "PowerTool_Parameter_Validation_Two_Winding_Transformer"},
    {"title_zh": "参数校核与标幺值：三绕组变压器", "title_en": "Parameter Validation & Per-Unit: Three-Winding Transformer", "basename": "PowerTool_Parameter_Validation_Three_Winding_Transformer"},
    {"title_zh": "短路电流计算", "title_en": "Short-Circuit Current Calculation", "basename": "PowerTool_Short_Circuit_Current_Calculation"},
    {"title_zh": "日前/年度负荷预测", "title_en": "Day-Ahead / Annual Load Forecasting", "basename": "PowerTool_Load_Forecasting"},
    {"title_zh": "新能源预测", "title_en": "Renewable Forecasting", "basename": "PowerTool_Renewable_Forecasting"},
    {"title_zh": "预测算法与基础数据格式", "title_en": "Forecasting Algorithms and Base Data Format", "basename": "PowerTool_Forecasting_Algorithms_and_Data_Format"},
    {"title_zh": "录波曲线", "title_en": "Waveform Viewer", "basename": "PowerTool_Waveform_Viewer"},
)


def _manual_filename(basename: str, language: str | None = None) -> str:
    """Return the localized manual filename. / 返回按语言选择后的手册文件名。"""
    suffix = "" if normalize_language(language) == "en" else "_zh"
    return f"{basename}{suffix}.md"


def _format_polar_complex(z: complex, unit: str = "") -> str:
    mag = abs(z)
    ang = math.degrees(math.atan2(z.imag, z.real))
    suffix = f" {unit}" if unit else ""
    return f"{mag:.2f} ∠ {ang:+.2f}°{suffix}"


def _draw_block(ax, x: float, y: float, w: float, h: float, text: str, fontsize: int = 10) -> None:
    rect = Rectangle((x, y), w, h, fill=False, linewidth=1.2)
    ax.add_patch(rect)
    ax.text(x + w / 2.0, y + h / 2.0, text, ha="center", va="center", fontsize=fontsize)


def _draw_sum_node(ax, x: float, y: float, r: float = 0.22) -> None:
    circle = Circle((x, y), r, fill=False, linewidth=1.2)
    ax.add_patch(circle)
    ax.text(x, y, "Σ", ha="center", va="center", fontsize=12)


def _draw_signal_arrow(ax, x1: float, y1: float, x2: float, y2: float, text: str | None = None, dy: float = 0.18) -> None:
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="->", linewidth=1.2))
    if text:
        ax.text((x1 + x2) / 2.0, (y1 + y2) / 2.0 + dy, text, ha="center", va="center", fontsize=10)


def _draw_avr_transfer_diagram(ax) -> None:
    ax.clear()
    ax.set_xlim(0, 10.8)
    ax.set_ylim(0, 3.2)
    ax.axis("off")

    ax.text(0.2, 2.9, "AVR 传递函数结构图", fontsize=11, fontweight="bold", ha="left")
    _draw_block(ax, 1.6, 1.5, 1.8, 0.8, "1\n──────\n1+sT_r")
    _draw_sum_node(ax, 4.5, 1.9)
    _draw_block(ax, 5.2, 1.5, 2.0, 0.8, "K_0 · 1+sT_1\n──────────\n  1+sT_2")
    _draw_block(ax, 7.8, 1.5, 1.3, 0.8, "1\n────\n1+sT_e")

    _draw_signal_arrow(ax, 0.4, 1.9, 1.6, 1.9, "E_t")
    _draw_signal_arrow(ax, 3.4, 1.9, 4.28, 1.9, "v_m")
    _draw_signal_arrow(ax, 4.72, 1.9, 5.2, 1.9)
    _draw_signal_arrow(ax, 7.2, 1.9, 7.8, 1.9)
    _draw_signal_arrow(ax, 9.1, 1.9, 10.3, 1.9, "v_f")

    ax.annotate("", xy=(4.5, 2.12), xytext=(4.5, 2.9), arrowprops=dict(arrowstyle="->", linewidth=1.0))
    ax.text(4.62, 2.74, "+  V_ref", fontsize=10, va="center")
    ax.annotate("", xy=(4.5, 1.68), xytext=(4.5, 0.55), arrowprops=dict(arrowstyle="->", linewidth=1.0))
    ax.text(4.62, 0.95, "+  V_s", fontsize=10, va="center")
    ax.text(4.08, 1.55, "−", fontsize=12, va="center")
    ax.text(4.56, 2.02, "+", fontsize=12, va="center")
    ax.text(4.56, 1.60, "+", fontsize=12, va="center")
    ax.text(0.2, 0.20, "当前内核模型：测量环节 1/(1+sT_r)，主调节器 K_0(1+sT_1)/(1+sT_2)，再串联励磁回路 1/(1+sT_e)。", fontsize=9, ha="left")


def _draw_pss_transfer_diagram(ax) -> None:
    ax.clear()
    ax.set_xlim(0, 11.4)
    ax.set_ylim(0, 2.8)
    ax.axis("off")

    ax.text(0.2, 2.45, "PSS 传递函数结构图", fontsize=11, fontweight="bold", ha="left")
    _draw_block(ax, 1.1, 1.1, 1.1, 0.7, "K_w")
    _draw_block(ax, 2.8, 1.1, 1.7, 0.7, "sT_w\n──────\n1+sT_w")
    _draw_block(ax, 5.1, 1.1, 2.1, 0.7, "1+sT_1\n────────\n1+sT_2")
    _draw_block(ax, 7.9, 1.1, 2.1, 0.7, "1+sT_3\n────────\n1+sT_4")

    _draw_signal_arrow(ax, 0.2, 1.45, 1.1, 1.45, "Δω")
    _draw_signal_arrow(ax, 2.2, 1.45, 2.8, 1.45)
    _draw_signal_arrow(ax, 4.5, 1.45, 5.1, 1.45)
    _draw_signal_arrow(ax, 7.2, 1.45, 7.9, 1.45)
    _draw_signal_arrow(ax, 10.0, 1.45, 11.0, 1.45, "V_s")
    ax.text(0.2, 0.22, "当前内核模型含两级超前-滞后补偿与输出限幅；其输出 V_s 叠加到 AVR 求和点。", fontsize=9, ha="left")


def _draw_type1_pss_diagram(ax) -> None:
    ax.clear()
    ax.set_xlim(0, 13.8)
    ax.set_ylim(0, 4.2)
    ax.axis("off")
    ax.text(0.2, 3.85, "1型 PSS 传递函数框图", fontsize=11, fontweight="bold", ha="left")

    _draw_block(ax, 1.4, 2.7, 1.0, 0.8, "Kq1")
    _draw_block(ax, 1.4, 1.7, 1.0, 0.8, "Kq2")
    _draw_block(ax, 1.4, 0.7, 1.0, 0.8, "Kq3")
    _draw_sum_node(ax, 3.6, 2.0, r=0.28)
    _draw_block(ax, 4.8, 1.55, 2.0, 0.9, "K + s\n──────\n1+sT_q")
    _draw_block(ax, 7.4, 1.55, 2.1, 0.9, "1+sT_1e\n────────\n1+sT_2e")
    _draw_block(ax, 10.1, 1.55, 2.1, 0.9, "1+sT_3e\n────────\n1+sT_4e")

    _draw_signal_arrow(ax, 0.2, 3.1, 1.4, 3.1, "ω−ω0")
    _draw_signal_arrow(ax, 0.2, 2.1, 1.4, 2.1, "Pe−Pe0")
    _draw_signal_arrow(ax, 0.2, 1.1, 1.4, 1.1, "Vt−Vt0")
    _draw_signal_arrow(ax, 2.4, 3.1, 3.35, 2.2)
    _draw_signal_arrow(ax, 2.4, 2.1, 3.32, 2.0)
    _draw_signal_arrow(ax, 2.4, 1.1, 3.35, 1.8)
    _draw_signal_arrow(ax, 3.88, 2.0, 4.8, 2.0)
    _draw_signal_arrow(ax, 6.8, 2.0, 7.4, 2.0)
    _draw_signal_arrow(ax, 9.5, 2.0, 10.1, 2.0)
    _draw_signal_arrow(ax, 12.2, 2.0, 13.5, 2.0, "V_s")
    ax.text(12.55, 2.58, "V_smax", fontsize=9)
    ax.text(12.55, 1.38, "V_smin", fontsize=9)


def _draw_type1_avr_diagram(ax) -> None:
    ax.clear()
    ax.set_xlim(0, 15.0)
    ax.set_ylim(0, 4.6)
    ax.axis("off")
    ax.text(0.2, 4.15, "1型 AVR 传递函数框图", fontsize=11, fontweight="bold", ha="left")

    _draw_sum_node(ax, 1.2, 2.7, r=0.26)
    _draw_block(ax, 2.1, 2.2, 1.6, 1.0, "K_r\n──────\n1+sT_r")
    _draw_sum_node(ax, 4.6, 2.7, r=0.26)
    _draw_block(ax, 5.5, 2.2, 1.8, 1.0, "K_a\n──────\n1+sT_a")
    _draw_sum_node(ax, 8.2, 2.7, r=0.26)
    _draw_block(ax, 9.0, 2.2, 1.5, 1.0, "1\n──────\n1+sT_e")
    _draw_block(ax, 6.3, 0.45, 1.8, 1.0, "sK_f\n──────\n1+sT_f")

    _draw_signal_arrow(ax, 0.2, 2.7, 0.95, 2.7, "V_t")
    _draw_signal_arrow(ax, 1.46, 2.7, 2.1, 2.7)
    _draw_signal_arrow(ax, 3.7, 2.7, 4.35, 2.7)
    _draw_signal_arrow(ax, 4.86, 2.7, 5.5, 2.7)
    _draw_signal_arrow(ax, 7.3, 2.7, 7.95, 2.7)
    _draw_signal_arrow(ax, 8.46, 2.7, 9.0, 2.7)
    _draw_signal_arrow(ax, 10.5, 2.7, 12.0, 2.7, "E_fd")
    _draw_signal_arrow(ax, 12.0, 2.7, 12.0, 0.95)
    _draw_signal_arrow(ax, 12.0, 0.95, 8.1, 0.95)
    _draw_signal_arrow(ax, 8.1, 0.95, 8.1, 2.44, "V_F", dy=0.14)

    ax.annotate("", xy=(1.2, 2.96), xytext=(1.2, 3.7), arrowprops=dict(arrowstyle="->", linewidth=1.0))
    ax.text(1.35, 3.46, "V_t0", fontsize=9, va="center")
    ax.text(0.86, 2.66, "−", fontsize=12)

    ax.annotate("", xy=(4.6, 2.96), xytext=(4.6, 3.7), arrowprops=dict(arrowstyle="->", linewidth=1.0))
    ax.text(4.72, 3.46, "V_s", fontsize=9, va="center")
    ax.annotate("", xy=(4.6, 2.44), xytext=(4.6, 1.75), arrowprops=dict(arrowstyle="->", linewidth=1.0))
    ax.text(4.72, 1.9, "V_F", fontsize=9, va="center")
    ax.text(4.2, 2.83, "+", fontsize=12)
    ax.text(4.2, 2.36, "−", fontsize=12)

    ax.annotate("", xy=(8.2, 2.96), xytext=(8.2, 3.7), arrowprops=dict(arrowstyle="->", linewidth=1.0))
    ax.text(8.35, 3.46, "E_fd0", fontsize=9, va="center")
    ax.text(7.85, 2.66, "+", fontsize=12)
    ax.text(11.05, 3.0, "E_fdmax", fontsize=9)
    ax.text(11.05, 2.35, "E_fdmin", fontsize=9)


class CommonGuiMixin:
    def _hide_tab_muted_explanations(self) -> None:
        tab_roots = [
            self.freq_tab,
            self.osc_tab,
            self.volt_tab,
            self.impact_tab,
            self.smib_tab,
            self.loop_tab,
            self.param_tab,
            self.sc_tab,
            self.load_forecast_tab,
            self.renewable_forecast_tab,
            self.annual_load_forecast_tab,
            self.comtrade_tab,
        ]

        def walk(widget: tk.Widget) -> None:
            if isinstance(widget, ttk.Label) and str(widget.cget("style")) == "Muted.TLabel":
                try:
                    if widget.winfo_manager() == "grid":
                        widget.grid_remove()
                    elif widget.winfo_manager() == "pack":
                        widget.pack_forget()
                    elif widget.winfo_manager() == "place":
                        widget.place_forget()
                except Exception:
                    pass
            for child in widget.winfo_children():
                walk(child)

        for root in tab_roots:
            walk(root)

    def _apply_language(self) -> None:
        """Apply UI translation after widgets are created. / 在控件创建后应用界面翻译。"""
        if self.language != "en":
            return
        translate_widget_tree(self, self.language)
        for value in self.__dict__.values():
            try:
                if isinstance(value, tk.Toplevel) and value.winfo_exists():
                    translate_widget_tree(value, self.language)
            except Exception:
                pass
        self.ai_question_placeholder = _tr_obj(self, self.ai_question_placeholder)
        self.ai_status_var.set(self._ai_status_summary())
        if hasattr(self, "smib_mode_hint_var"):
            self.smib_mode_hint_var.set(_tr_obj(self, self.smib_mode_hint_var.get()))
        if hasattr(self, "sc_summary_fault_var") and self.sc_summary_fault_var.get().strip() not in {"", "—"}:
            self.sc_summary_fault_var.set(_tr_obj(self, self.sc_summary_fault_var.get()))
        if hasattr(self, "_sequence_channel_vars"):
            for key, var in self._sequence_channel_vars.items():
                var.set(_display_obj(self, _logic_obj(self, var.get())))

    @staticmethod
    def _add_entry(parent: ttk.Frame,
                   row: int,
                   label: str,
                   default: str,
                   column: int = 0,
                   width: int = 14) -> ttk.Entry:
        ttk.Label(parent, text=label, style="Form.TLabel").grid(row=row, column=column, sticky="w", padx=4, pady=4)
        entry = ttk.Entry(parent, width=width, style="Input.TEntry")
        entry.grid(row=row, column=column + 1, sticky="ew", padx=4, pady=4)
        entry.insert(0, default)
        return entry

    @staticmethod
    def _set_text(widget: ScrolledText, text: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", tk.END)
        widget.tag_delete("key_conclusion")
        widget.tag_configure("key_conclusion", foreground="#c00000")
        widget.insert(tk.END, text)
        for line_no in _detect_key_conclusion_lines(text):
            widget.tag_add("key_conclusion", f"{line_no}.0", f"{line_no}.end")
        widget.configure(state="disabled")

    def _configure_styles(self) -> None:
        self._palette = {
            "bg": "#edf3f8",
            "bg_alt": "#f5f8fc",
            "surface": "#ffffff",
            "surface_alt": "#f8fbff",
            "border": "#d5dfeb",
            "border_strong": "#c3d1e0",
            "text": "#203040",
            "muted": "#63778c",
            "accent": "#1f4d8b",
            "accent_dark": "#173f7a",
            "accent_soft": "#e8f0fb",
            "success": "#1f8f5f",
        }
        p = self._palette
        self.configure(bg=p["bg"])

        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")

        style.configure("TFrame", background=p["bg"])
        style.configure("Surface.TFrame", background=p["bg_alt"])
        style.configure("Card.TFrame", background=p["surface"])
        style.configure("Metric.TFrame", background=p["surface_alt"], relief="flat")

        style.configure("TLabel", background=p["bg"], foreground=p["text"])
        style.configure("Surface.TLabel", background=p["bg_alt"], foreground=p["text"])
        style.configure("Card.TLabel", background=p["surface"], foreground=p["text"])
        style.configure("Muted.TLabel", background=p["surface"], foreground=p["muted"])
        style.configure("Form.TLabel", background=p["surface"], foreground=p["text"])
        style.configure("PageTitle.TLabel", background=p["surface"], foreground=p["text"], font=("TkDefaultFont", 13, "bold"))
        style.configure("SectionTitle.TLabel", background=p["surface"], foreground=p["accent"], font=("TkDefaultFont", 11, "bold"))
        style.configure("MetricTitle.TLabel", background=p["surface_alt"], foreground=p["muted"], font=("TkDefaultFont", 9))
        style.configure("MetricValue.TLabel", background=p["surface_alt"], foreground=p["text"], font=("TkDefaultFont", 12, "bold"))

        style.configure("TLabelframe", background=p["bg_alt"], borderwidth=1, relief="solid", bordercolor=p["border"], padding=10)
        style.configure("TLabelframe.Label", background=p["bg_alt"], foreground=p["text"], font=("TkDefaultFont", 10, "bold"))
        style.configure("Card.TLabelframe", background=p["surface"], borderwidth=1, relief="solid", bordercolor=p["border"], padding=10)
        style.configure("Card.TLabelframe.Label", background=p["surface"], foreground=p["text"], font=("TkDefaultFont", 10, "bold"))

        notebook_spec = _notebook_style_spec()
        for style_name, options in notebook_spec["configure"].items():
            style.configure(style_name, **options)
        style.map("TNotebook.Tab", **notebook_spec["map"])
        style.configure("TNotebook", background=p["bg"], borderwidth=0, tabmargins=(0, 0, 0, 0))

        style.configure("TButton", padding=(11, 6), background=p["surface_alt"], foreground=p["text"], bordercolor=p["border"], relief="flat")
        style.map(
            "TButton",
            background=[("active", "#ecf3fb"), ("pressed", "#dfeaf7")],
            bordercolor=[("focus", p["accent"]), ("!focus", p["border"])],
        )
        style.configure("Accent.TButton", padding=(12, 6), background=p["accent"], foreground="#ffffff", bordercolor=p["accent"], relief="flat", font=("TkDefaultFont", 10, "bold"))
        style.map("Accent.TButton", background=[("active", p["accent_dark"]), ("pressed", p["accent_dark"])], foreground=[("disabled", "#f4f6f8")])

        style.configure("Input.TEntry", padding=5, fieldbackground="#ffffff", foreground=p["text"], bordercolor=p["border_strong"], lightcolor=p["border_strong"], darkcolor=p["border_strong"], insertcolor=p["text"])
        style.map("Input.TEntry", bordercolor=[("focus", p["accent"]), ("!focus", p["border_strong"])], lightcolor=[("focus", p["accent_soft"]), ("!focus", p["border_strong"])], darkcolor=[("focus", p["accent_soft"]), ("!focus", p["border_strong"])])

        style.configure("Input.TCombobox", padding=4, fieldbackground="#ffffff", background="#ffffff", foreground=p["text"], bordercolor=p["border_strong"], lightcolor=p["border_strong"], darkcolor=p["border_strong"], arrowcolor=p["accent"])
        style.map(
            "Input.TCombobox",
            bordercolor=[("focus", p["accent"]), ("!focus", p["border_strong"])],
            lightcolor=[("focus", p["accent_soft"]), ("!focus", p["border_strong"])],
            darkcolor=[("focus", p["accent_soft"]), ("!focus", p["border_strong"])],
            fieldbackground=[("readonly", "#ffffff"), ("disabled", "#f2f5f8")],
            background=[("readonly", "#ffffff"), ("disabled", "#f2f5f8")],
            foreground=[("readonly", p["text"]), ("disabled", p["muted"])],
            arrowcolor=[("disabled", p["muted"]), ("!disabled", p["accent"])],
        )

        style.configure("TCheckbutton", background=p["surface"], foreground=p["text"])
        style.configure("Card.TCheckbutton", background=p["surface"], foreground=p["text"])
        style.configure("Surface.TCheckbutton", background=p["bg_alt"], foreground=p["text"])
        style.configure("TRadiobutton", background=p["surface"], foreground=p["text"])
        style.configure("Horizontal.TScale", background=p["surface"])
        style.configure("Accent.Horizontal.TScale", background=p["surface"])

        style.configure("Treeview", background="#ffffff", fieldbackground="#ffffff", foreground=p["text"], rowheight=24, bordercolor=p["border"], lightcolor=p["border"], darkcolor=p["border"])
        style.configure("Treeview.Heading", background="#eef3f9", foreground=p["text"], bordercolor=p["border"], relief="flat", font=("TkDefaultFont", 10, "bold"))
        style.map("Treeview", background=[("selected", "#d9e7f7")], foreground=[("selected", p["text"])])

        style.configure("Vertical.TScrollbar", background="#e9eff6", troughcolor=p["bg_alt"], bordercolor=p["bg_alt"], arrowcolor=p["muted"])
        style.configure("Horizontal.TScrollbar", background="#e9eff6", troughcolor=p["bg_alt"], bordercolor=p["bg_alt"], arrowcolor=p["muted"])

    def _style_text_widget(self, widget: tk.Text | ScrolledText, *, font: str | tuple[str, int] = "TkFixedFont") -> None:
        p = self._palette
        widget.configure(
            font=font,
            background=p["surface_alt"],
            foreground=p["text"],
            insertbackground=p["text"],
            relief="flat",
            borderwidth=0,
            highlightthickness=1,
            highlightbackground=p["border"],
            highlightcolor=p["accent"],
            selectbackground="#d7e4f6",
            selectforeground=p["text"],
            padx=10,
            pady=8,
        )
        try:
            widget.configure(inactiveselectbackground="#d7e4f6")
        except Exception:
            pass

    def _style_listbox_widget(self, widget: tk.Listbox) -> None:
        p = self._palette
        widget.configure(
            bg=p["surface_alt"],
            fg=p["text"],
            selectbackground="#d7e4f6",
            selectforeground=p["text"],
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=p["border"],
            highlightcolor=p["accent"],
        )

    def _bind_canvas_mousewheel(self, canvas: tk.Canvas) -> None:
        def _on_mousewheel(event: tk.Event) -> None:
            if getattr(event, "delta", 0):
                canvas.yview_scroll(int(-event.delta / 120), "units")
            elif getattr(event, "num", None) == 4:
                canvas.yview_scroll(-1, "units")
            elif getattr(event, "num", None) == 5:
                canvas.yview_scroll(1, "units")

        canvas.bind("<Enter>", lambda _e: (canvas.bind_all("<MouseWheel>", _on_mousewheel), canvas.bind_all("<Button-4>", _on_mousewheel), canvas.bind_all("<Button-5>", _on_mousewheel)))
        canvas.bind("<Leave>", lambda _e: (canvas.unbind_all("<MouseWheel>"), canvas.unbind_all("<Button-4>"), canvas.unbind_all("<Button-5>")))

    def _create_scrollable_card(self, parent: ttk.Frame, *, padding: int = 16) -> tuple[ttk.Frame, ttk.Frame, tk.Canvas]:
        outer = ttk.Frame(parent, style="Card.TFrame")
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(0, weight=1)
        canvas = tk.Canvas(outer, background=self._palette["surface"], highlightthickness=0, bd=0)
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        canvas.configure(yscrollcommand=scrollbar.set)
        inner = ttk.Frame(canvas, padding=padding, style="Card.TFrame")
        window_id = canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(window_id, width=e.width))
        self._bind_canvas_mousewheel(canvas)
        return outer, inner, canvas

    def _apply_surface_theme(self, widget: tk.Widget, *, card: bool = True) -> None:
        surface_prefix = "Card" if card else "Surface"
        wclass = widget.winfo_class()
        try:
            current_style = str(widget.cget("style")) if wclass.startswith("T") else ""
            if wclass == "TFrame" and not current_style:
                widget.configure(style=f"{surface_prefix}.TFrame")
            elif wclass == "TLabel" and not current_style:
                widget.configure(style=f"{surface_prefix}.TLabel")
            elif wclass == "TLabelframe" and not current_style:
                widget.configure(style="Card.TLabelframe" if card else "TLabelframe")
            elif wclass == "TCheckbutton" and not str(widget.cget("style")):
                widget.configure(style=f"{surface_prefix}.TCheckbutton")
            elif wclass == "TRadiobutton" and not str(widget.cget("style")):
                widget.configure(style="TRadiobutton")
            elif wclass == "TEntry" and not str(widget.cget("style")):
                widget.configure(style="Input.TEntry")
            elif wclass == "TCombobox" and not str(widget.cget("style")):
                widget.configure(style="Input.TCombobox")
            elif wclass == "TScale" and not str(widget.cget("style")):
                widget.configure(style="Accent.Horizontal.TScale")
            elif wclass == "Canvas":
                widget.configure(bg=self._palette["surface" if card else "bg_alt"], highlightthickness=0, bd=0)
        except Exception:
            pass
        for child in widget.winfo_children():
            self._apply_surface_theme(child, card=card)

    def _apply_global_aesthetics(self) -> None:
        for page in (self.freq_tab, self.osc_tab, self.volt_tab, self.impact_tab, self.smib_tab, self.loop_tab, self.param_tab, self.sc_tab, self.comtrade_tab):
            self._apply_surface_theme(page, card=False)
        for panel in (getattr(self, name, None) for name in ("_vr_static_tab", "_vr_line_tab", "_vr_avc_tab", "_ptab_line", "_ptab_sag", "_ptab_2wt", "_ptab_3wt")):
            if panel is not None:
                self._apply_surface_theme(panel, card=True)
        for widget_name in (
            "freq_result", "osc_result", "volt_result", "line_result", "avc_result",
            "imp_result", "eac_result", "smib_result", "smib_type1_result",
            "lp_result", "sag_result", "tx2_result", "tx3_result", "loop_result", "sc_result",
            "comtrade_info", "ai_question", "ai_answer", "comtrade_cursor_label",
        ):
            widget = getattr(self, widget_name, None)
            if widget is not None:
                font = ("TkDefaultFont", 10) if widget_name in {"ai_question", "ai_answer", "comtrade_cursor_label"} else "TkFixedFont"
                self._style_text_widget(widget, font=font)
        if getattr(self, "_line_geometry_result", None) is not None:
            self._style_text_widget(self._line_geometry_result)
        if getattr(self, "comtrade_channel_list", None) is not None:
            self._style_listbox_widget(self.comtrade_channel_list)

    @staticmethod
    def _set_enabled(widgets: list[tk.Widget], enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        for widget in widgets:
            try:
                widget.configure(state=state)
            except Exception:
                pass

    @staticmethod
    def _slice_time_window(time_s: np.ndarray, start_s: float, end_s: float) -> np.ndarray:
        if time_s.size == 0:
            return np.array([], dtype=int)
        start_s = max(float(time_s[0]), float(start_s))
        end_s = min(float(time_s[-1]), float(end_s))
        if end_s <= start_s:
            end_s = min(float(time_s[-1]), start_s + max(float(time_s[-1] - time_s[0]) * 0.02, 1e-4))
        mask = (time_s >= start_s) & (time_s <= end_s)
        idx = np.flatnonzero(mask)
        if idx.size < 2:
            lo = int(np.searchsorted(time_s, start_s, side="left"))
            hi = int(np.searchsorted(time_s, end_s, side="right"))
            idx = np.arange(max(0, lo - 1), min(time_s.size, hi + 1))
        return idx

    def _build_ai_sidebar(self) -> None:
        panel = ttk.Frame(self, padding=10, style="Card.TFrame")
        panel.grid(row=0, column=1, sticky="nsew", padx=(4, 8), pady=8)
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(5, weight=1)

        ttk.Label(panel, text="PowerTool AI", style="Card.TLabel",
                  font=("TkDefaultFont", 12, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(
            panel,
            text="向AI提问时会自动附带当前界面截图和算例摘要",
            style="Card.TLabel", justify="left", wraplength=360,
        ).grid(row=1, column=0, sticky="ew", pady=(4, 8))

        self.ai_status_var = tk.StringVar(value=self._ai_status_summary())
        ttk.Label(panel, textvariable=self.ai_status_var, style="Card.TLabel", justify="left",
                  wraplength=360).grid(row=2, column=0, sticky="ew", pady=(0, 8))

        doc_bar = ttk.Frame(panel, style="Card.TFrame")
        doc_bar.grid(row=3, column=0, sticky="ew", pady=(2, 2))
        doc_bar.columnconfigure(0, weight=1)
        ttk.Button(doc_bar, text="使用手册", command=self._open_manual_popup).grid(row=0, column=0, sticky="w")

        ttk.Label(panel, text="提问", style="Card.TLabel", font=("TkDefaultFont", 10, "bold")).grid(row=4, column=0, sticky="w", pady=(4, 4))
        self.ai_think_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(panel, text="启用思考模式", variable=self.ai_think_var).grid(row=4, column=0, sticky="e", pady=(4, 4))
        self.ai_question = ScrolledText(panel, width=44, height=9, wrap=tk.WORD)
        self.ai_question.grid(row=5, column=0, sticky="nsew")
        self.ai_question_placeholder = "请结合当前界面，解释这个算例的意义、关键结果和下一步建议。"
        self.ai_question.insert("1.0", self.ai_question_placeholder)

        action = ttk.Frame(panel, style="Card.TFrame")
        action.grid(row=6, column=0, sticky="ew", pady=(8, 6))
        action.columnconfigure(0, weight=1)
        action.columnconfigure(1, weight=1)
        ttk.Button(action, text="发送到 PowerTool AI", command=self._ask_power_tool_ai).grid(row=0, column=0, sticky="ew", padx=(0, 4))
        ttk.Button(action, text="填入当前算例摘要", command=self._insert_current_case_summary).grid(row=0, column=1, sticky="ew", padx=(4, 0))

        ttk.Label(panel, text="AI 回复", style="Card.TLabel", font=("TkDefaultFont", 10, "bold")).grid(row=7, column=0, sticky="w", pady=(4, 4))
        self.ai_answer = ScrolledText(panel, width=44, height=18, wrap=tk.WORD)
        self.ai_answer.grid(row=8, column=0, sticky="nsew")
        self.ai_answer.insert("1.0", "PowerTool AI 已就绪。")
        self.ai_answer.configure(state="disabled")

        panel.rowconfigure(8, weight=1)

    def _clear_ai_context(self) -> None:
        self.ai_question.delete("1.0", tk.END)
        self.ai_answer.configure(state="normal")
        self.ai_answer.delete("1.0", tk.END)
        self.ai_answer.insert("1.0", "")
        self.ai_answer.configure(state="disabled")

    def _on_ai_context_changed(self, _event: object | None = None) -> None:
        self._clear_ai_context()
        self.ai_status_var.set(self._ai_status_summary())

    def _ai_status_summary(self) -> str:
        return _tr_obj(
            self,
            (
                f"配置文件：{config_path().name}\n"
                f"当前模式：{self.ai_config.provider.mode}\n"
                f"{api_key_status(self.ai_config)}"
            ),
        )

    def _manual_doc_dir(self) -> Path:
        """Return the manual directory. / 返回手册目录。"""
        return Path(__file__).resolve().parent / "manuals"

    def _current_manual_basename(self) -> str:
        """Return the basename of the manual for the current page. / 返回当前页面对应手册的基础文件名。"""
        tab = _logic_obj(self, self._current_tab_name())
        if tab == "电压无功分析":
            sub = _logic_obj(self, self._vr_notebook.tab(self._vr_notebook.select(), "text"))
            mapping = {
                "静态电压稳定": "PowerTool_Voltage_Reactive_Static_Voltage_Stability",
                "线路自然功率与无功": "PowerTool_Voltage_Reactive_Line_Natural_Power_and_Reactive_Power",
                "AVC策略模拟": "PowerTool_Voltage_Reactive_AVC_Strategy_Simulation",
            }
            return mapping.get(sub, "PowerTool_Overview")
        if tab == "参数校核与标幺值":
            sub = _logic_obj(self, self.param_notebook.tab(self.param_notebook.select(), "text"))
            mapping = {
                "线路": "PowerTool_Parameter_Validation_Overhead_Line",
                "导线弧垂": "PowerTool_Parameter_Validation_Conductor_Sag",
                "两绕组变压器": "PowerTool_Parameter_Validation_Two_Winding_Transformer",
                "三绕组变压器": "PowerTool_Parameter_Validation_Three_Winding_Transformer",
            }
            return mapping.get(sub, "PowerTool_Overview")
        mapping = {
            "频率动态": "PowerTool_Frequency_Dynamics",
            "机电振荡": "PowerTool_Electromechanical_Oscillation",
            "暂稳评估": "PowerTool_Transient_Stability_Assessment",
            "小扰动分析": "PowerTool_Small_Signal_Analysis",
            "小扰动分析（SMIB）": "PowerTool_Small_Signal_Analysis",
            "配电网合环分析": "PowerTool_Distribution_Loop_Closure_Analysis",
            "短路电流计算": "PowerTool_Short_Circuit_Current_Calculation",
            "日前负荷预测": "PowerTool_Load_Forecasting",
            "年度负荷预测": "PowerTool_Load_Forecasting",
            "新能源预测": "PowerTool_Renewable_Forecasting",
            "录波曲线": "PowerTool_Waveform_Viewer",
        }
        return mapping.get(tab, "PowerTool_Overview")

    def _manual_doc_path(self) -> Path:
        """Return the manual path for the current page. / 返回当前页面对应手册路径。"""
        return self._manual_doc_dir() / _manual_filename(self._current_manual_basename(), _lang_of(self))

    def _manual_catalog(self) -> list[tuple[str, Path]]:
        """Build the manual catalog shown from the AI sidebar. / 构造 AI 侧栏打开的手册目录。"""
        lang = _lang_of(self)
        base = self._manual_doc_dir()
        entries: list[tuple[str, Path]] = []
        for item in _MANUAL_LIBRARY:
            title = item["title_en"] if lang == "en" else item["title_zh"]
            path = base / _manual_filename(item["basename"], lang)
            entries.append((title, path))
        return entries

    def _render_markdown_to_text(self, widget: ScrolledText, markdown: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", tk.END)
        widget.tag_configure("h1", font=("TkDefaultFont", 13, "bold"), spacing1=8, spacing3=6)
        widget.tag_configure("h2", font=("TkDefaultFont", 11, "bold"), spacing1=6, spacing3=4)
        widget.tag_configure("bullet", lmargin1=12, lmargin2=24)
        widget.tag_configure("code", font=("TkFixedFont", 10))
        in_code = False
        for raw in markdown.splitlines():
            line = raw.rstrip("\n")
            if line.strip().startswith("```"):
                in_code = not in_code
                continue
            if in_code:
                widget.insert(tk.END, line + "\n", ("code",))
                continue
            if line.startswith("# "):
                widget.insert(tk.END, line[2:].strip() + "\n", ("h1",))
            elif line.startswith("## "):
                widget.insert(tk.END, line[3:].strip() + "\n", ("h2",))
            elif line.startswith("- "):
                widget.insert(tk.END, f"• {line[2:].strip()}\n", ("bullet",))
            else:
                widget.insert(tk.END, line + "\n")
        widget.configure(state="disabled")

    def _open_manual_popup(self) -> None:
        """Open the manual browser from the AI sidebar. / 从 AI 侧栏打开手册浏览器。"""
        catalog = [(title, path) for title, path in self._manual_catalog() if path.exists()]
        if not catalog:
            messagebox.showwarning("使用手册", f"未找到手册目录：{self._manual_doc_dir().name}")
            return

        lang = _lang_of(self)
        current_path = self._manual_doc_path()
        popup = tk.Toplevel(self)
        popup.title("PowerTool Manual" if lang == "en" else "PowerTool 使用手册")
        popup.geometry("1180x760")
        popup.transient(self)
        popup.columnconfigure(1, weight=1)
        popup.rowconfigure(1, weight=1)

        left_title = "Manuals" if lang == "en" else "手册目录"
        right_title = "Document" if lang == "en" else "文档内容"
        status_prefix = "File" if lang == "en" else "文件"

        ttk.Label(popup, text=left_title, style="SectionTitle.TLabel").grid(row=0, column=0, sticky="w", padx=(10, 6), pady=(10, 6))
        ttk.Label(popup, text=right_title, style="SectionTitle.TLabel").grid(row=0, column=1, sticky="w", padx=(6, 10), pady=(10, 6))

        list_frame = ttk.Frame(popup, style="Card.TFrame", padding=8)
        list_frame.grid(row=1, column=0, sticky="nsew", padx=(10, 6), pady=(0, 10))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        listbox = tk.Listbox(list_frame, exportselection=False, width=38)
        listbox.grid(row=0, column=0, sticky="nsew")
        self._style_listbox_widget(listbox)
        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=listbox.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        listbox.configure(yscrollcommand=scroll.set)

        right_frame = ttk.Frame(popup, style="Card.TFrame", padding=8)
        right_frame.grid(row=1, column=1, sticky="nsew", padx=(6, 10), pady=(0, 10))
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=1)
        text = ScrolledText(right_frame, wrap=tk.WORD)
        text.grid(row=0, column=0, sticky="nsew")
        self._style_text_widget(text, font=("TkDefaultFont", 10))

        status_var = tk.StringVar(value="")
        ttk.Label(popup, textvariable=status_var, style="Muted.TLabel").grid(row=2, column=0, columnspan=2, sticky="w", padx=10, pady=(0, 10))

        for title, _path in catalog:
            listbox.insert(tk.END, title)

        def _show_selected(_event: object | None = None) -> None:
            if not listbox.curselection():
                return
            index = int(listbox.curselection()[0])
            title, path = catalog[index]
            markdown = path.read_text(encoding="utf-8")
            self._render_markdown_to_text(text, markdown)
            popup.title(f"{left_title} - {title}")
            status_var.set(f"{status_prefix}: {path.name}")

        listbox.bind("<<ListboxSelect>>", _show_selected)

        selected_index = next((idx for idx, (_title, path) in enumerate(catalog) if path.name == current_path.name), 0)
        listbox.selection_set(selected_index)
        listbox.activate(selected_index)
        _show_selected()

    def _reload_ai_config(self) -> None:
        self.ai_config = load_ai_config()
        self.ai_status_var.set(self._ai_status_summary())

    def _set_ai_answer(self, text: str) -> None:
        self.ai_answer.configure(state="normal")
        self.ai_answer.delete("1.0", tk.END)
        self.ai_answer.insert(tk.END, text)
        self.ai_answer.configure(state="disabled")

    def _current_tab_name(self) -> str:
        return self.main_notebook.tab(self.main_notebook.select(), "text")

    def _tab_numeric_summary(self) -> str:
        tab = _logic_obj(self, self._current_tab_name())
        if tab == "频率动态":
            pairs = [("额定频率 f0 / Hz", self.freq_f0), ("功率缺额 ΔP_OL0 / pu", self.freq_dp), ("系统惯性时间常数 T_s / s", self.freq_ts),
                     ("一次调频时间常数 T_G / s", self.freq_tg), ("负荷频率系数 k_D / pu/pu", self.freq_kd), ("一次调频系数 k_G / pu/pu", self.freq_kg),
                     ("绘图时长 / s", self.freq_tend), ("AGC比例 Kp", self.freq_kp_agc), ("AGC积分 Ki", self.freq_ki_agc)]
        elif tab == "机电振荡":
            pairs = [("内电势 E'_q / pu", self.osc_eq), ("端电压 U / pu", self.osc_u), ("等值电抗 X_Σ / pu", self.osc_x), ("初始有功 P0 / pu", self.osc_p0),
                     ("惯性时间常数 T_j / s", self.osc_tj), ("同步频率 f0 / Hz", self.osc_f0)]
        elif tab == "电压无功分析":
            current = _logic_obj(self, self._vr_notebook.tab(self._vr_notebook.select(), "text"))
            if current == "静态电压稳定":
                pairs = [("送端电压 U_g / pu", self.volt_ug), ("总电抗 X_Σ / pu", self.volt_x), ("功率因数 cosφ", self.volt_pf), ("容量基准 S_base / MVA", self.volt_sbase)]
            elif current == "线路自然功率与无功":
                pairs = [("线路额定电压 U / kV", self.line_u), ("波阻抗 Z_c / Ω", self.line_zc), ("单位长度电感 L", self.line_l), ("单位长度电容 C", self.line_c),
                         ("实际传输有功 P / MW", self.line_p), ("单位长度充电功率 Q_N / (Mvar/km)", self.line_qn), ("线路长度 l / km", self.line_len)]
            else:
                pairs = [("高压侧当前电压 / kV", self.avc_vh), ("有功潮流 P / MW", self.avc_p), ("无功潮流 Q / Mvar", self.avc_q), ("当前档位", self.avc_tap_now)]
            header = f"电压无功子标签: {current}"
            return header + "\n" + "\n".join(f"{name}: {entry.get().strip()}" for name, entry in pairs)
        elif tab == "暂稳评估":
            pairs = [("冲击法 ΔPa / pu", self.imp_dp), ("冲击法 Δt / s", self.imp_dt), ("冲击法 f_d / Hz", self.imp_fd),
                     ("等面积法 Pm / pu", self.eac_pm), ("等面积法 Pmax_pre / pu", self.eac_ppre),
                     ("等面积法 Pmax_fault / pu", self.eac_pf), ("等面积法 Pmax_post / pu", self.eac_ppost), ("等面积法 Δt / s", self.eac_dt)]
        elif tab in {"小扰动分析", "小扰动分析（SMIB）"}:
            lines = [f"模型配置: {self.smib_config.get().strip()}"]
            for key, entry in self.smib_entries.items():
                lines.append(f"{key}: {entry.get().strip()}")
            return "\n".join(lines)
        elif tab == "配电网合环分析":
            pairs = [("连接点数量 N", self.loop_n), ("U1 / kV", self.loop_u1), ("U2 / kV", self.loop_u2), ("相角 φ / °", self.loop_angle), ("系统频率 / Hz", self.loop_freq)]
        elif tab == "参数校核与标幺值":
            current = _logic_obj(self, self.param_notebook.tab(self.param_notebook.select(), "text"))
            if current == "线路":
                pairs = [("线路额定电压 U_base / kV", self.lp_ubase), ("容量基准 S_base / MVA", self.lp_sbase), ("线路长度 l / km", self.lp_len),
                         ("R1 / Ω/km", self.lp_r1), ("X1 / Ω/km", self.lp_x1), ("C1 / μF/km", self.lp_c1)]
                header = f"参数页子标签: {current}"
                return header + "\n" + "\n".join(f"{name}: {entry.get().strip()}" for name, entry in pairs)
            elif current == "导线弧垂":
                mode_var = getattr(self, "sag_driver_var", None)
                mode_text = mode_var.get().strip() if mode_var is not None else "temperature"
                summary_lines = [
                    f"参数页子标签: {current}",
                    f"档距 l / m: {self.sag_span.get().strip()}",
                    f"左挂点高度 h_A / m: {self.sag_h_left.get().strip()}",
                    f"右挂点高度 h_B / m: {self.sag_h_right.get().strip()}",
                    f"单位质量 m / (kg/m): {self.sag_mass.get().strip()}",
                    f"参考水平张力 H_ref / kN: {self.sag_href.get().strip()}",
                    f"驱动方式: {mode_text}",
                    f"温度滑块 T_c / °C: {float(self.sag_temp_scale_var.get()):.1f}",
                    f"电流滑块 I / A: {float(self.sag_current_scale_var.get()):.0f}",
                    f"环境温度 T_a / °C: {self.sag_ambient.get().strip()}",
                ]
                return "\n".join(summary_lines)
            elif current == "两绕组变压器":
                pairs = [("S_base / MVA", self.tx2_sbase), ("额定容量 SN / MVA", self.tx2_sn), ("额定电压 UN / kV", self.tx2_un),
                         ("Uk / %", self.tx2_uk), ("Pk / kW", self.tx2_pk), ("I0 / %", self.tx2_i0), ("P0 / kW", self.tx2_p0), ("Ubase / kV", self.tx2_ubase)]
            else:
                pairs = [("S_base / MVA", self.tx3_sbase), ("Ubase / kV", self.tx3_ubase), ("SN_H / MVA", self.tx3_sn_h), ("UN_H / kV", self.tx3_un_h),
                         ("SN_M / MVA", self.tx3_sn_m), ("SN_L / MVA", self.tx3_sn_l), ("Uk_HM / %", self.tx3_uk_hm), ("Uk_HL / %", self.tx3_uk_hl), ("Uk_ML / %", self.tx3_uk_ml)]
            header = f"参数页子标签: {current}"
            return header + "\n" + "\n".join(f"{name}: {entry.get().strip()}" for name, entry in pairs)
        elif tab == "短路电流计算":
            pairs = [("系统电压 / kV", self.sc_u), ("线路长度 / km", self.sc_len), ("R1 / Ω/km", self.sc_r1), ("X1 / Ω/km", self.sc_x1),
                     ("R0 / Ω/km", self.sc_r0), ("X0 / Ω/km", self.sc_x0), ("左侧中性点电阻 / Ω", self.sc_rn), ("故障电阻 / Ω", self.sc_rf),
                     ("右侧相角 / °", self.sc_delta_right), ("故障点位置 / %", self.sc_fault_pos)]
        elif tab in {"日前负荷预测", "负荷预测"}:
            widgets = self._forecast_widgets.get("load", {})
            return (
                f"数据集: {widgets.get('dataset_var').get() if widgets else '-'}\n"
                f"未来天气CSV: {widgets.get('future_weather_path_var').get() if widgets and widgets.get('future_weather_path_var') else '未导入'}\n"
                f"预测日期: {widgets.get('date_var').get() if widgets else '-'}\n"
                f"位置: {widgets.get('lat_entry').get() if widgets else '-'}, {widgets.get('lon_entry').get() if widgets else '-'}；海拔 {widgets.get('alt_entry').get() if widgets else '-'} m\n"
                f"节假日国家/地区: {widgets.get('holiday_var').get() if widgets else '-'}"
            )
        elif tab == "新能源预测":
            widgets = self._forecast_widgets.get("renewable", {})
            capacity = widgets.get('capacity_entry').get() if widgets and widgets.get('capacity_entry') is not None else '-'
            return (
                f"数据集: {widgets.get('dataset_var').get() if widgets else '-'}\n"
                f"未来天气CSV: {widgets.get('future_weather_path_var').get() if widgets and widgets.get('future_weather_path_var') else '未导入'}\n"
                f"预测日期: {widgets.get('date_var').get() if widgets else '-'}\n"
                f"位置: {widgets.get('lat_entry').get() if widgets else '-'}, {widgets.get('lon_entry').get() if widgets else '-'}；海拔 {widgets.get('alt_entry').get() if widgets else '-'} m\n"
                f"装机容量上限: {capacity} MW\n"
                f"节假日国家/地区: {widgets.get('holiday_var').get() if widgets else '-'}；新能源类型: {widgets.get('resource_var').get() if widgets else '-'}（风电/光伏独立预测）"
            )
        elif tab == "年度负荷预测":
            widgets = self._annual_forecast_widgets
            return (
                f"区域: {widgets.get('region', '-')}\n"
                f"年限: {widgets.get('horizon_entry').get() if widgets else '-'} 年；方法: {widgets.get('algorithm_var').get() if widgets else '-'}\n"
                f"位置: {widgets.get('lat_entry').get() if widgets else '-'}, {widgets.get('lon_entry').get() if widgets else '-'}；气候板块: {widgets.get('climate_var').get() if widgets else '-'}\n"
                f"GDP/人口增长: {widgets.get('gdp_entry').get() if widgets else '-'}% / {widgets.get('pop_entry').get() if widgets else '-'}%；同时率: {widgets.get('coincidence_entry').get() if widgets else '-'}"
            )
        elif tab == "录波曲线":
            return f"当前录波文件: {getattr(self, '_comtrade_cfg_path', '') or '未载入'}\n当前时间窗: {self.comtrade_time_label.cget('text')}"
        else:
            return "当前页暂未定义数值摘要。"
        return "\n".join(f"{name}: {entry.get().strip()}" for name, entry in pairs)

    def _insert_current_case_summary(self) -> None:
        summary = self._tab_numeric_summary()
        self.ai_question.delete("1.0", tk.END)
        self.ai_question.insert("1.0", f"请结合当前界面分析：\n\n{summary}\n")

    def _capture_current_ui(self) -> tuple[Path | None, str]:
        cache_dir = Path(__file__).resolve().with_name(".power_tool_ai_cache")
        cache_dir.mkdir(exist_ok=True)
        filename = cache_dir / f"ui_capture_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.png"
        try:
            from PIL import ImageGrab  # type: ignore
        except Exception:
            return None, "当前环境未安装 Pillow，未能自动截取界面截图。"
        try:
            self.update_idletasks()
            x0 = self.winfo_rootx()
            y0 = self.winfo_rooty()
            x1 = x0 + self.winfo_width()
            y1 = y0 + self.winfo_height()
            image = ImageGrab.grab(bbox=(x0, y0, x1, y1))
            image.save(filename)
            self._latest_ai_screenshot = filename
            return filename, f"已自动截取当前软件界面：{filename.name}"
        except Exception as exc:
            return None, f"自动截图失败：{exc}"

    def _ask_power_tool_ai(self) -> None:
        if self._ai_busy:
            return
        question = self.ai_question.get("1.0", tk.END).strip()
        if not question:
            messagebox.showinfo("PowerTool AI", "请输入问题后再发送。")
            return
        self._reload_ai_config()
        tab_name = self._current_tab_name()
        case_text = _tr_obj(self, self._tab_numeric_summary())
        screenshot_path, screenshot_note = self._capture_current_ui()
        self._ai_busy = True
        self.ai_status_var.set(_tr_obj(self, f"PowerTool AI 正在分析：{tab_name}"))
        self._set_ai_answer("PowerTool AI 正在处理中，请稍候…")

        def worker() -> None:
            try:
                answer = ask_ai(self.ai_config, question, tab_name, case_text, screenshot_note, screenshot_path, think=self.ai_think_var.get(), language=self.language)
                status = f"分析完成：{tab_name}"
            except PowerToolAIError as exc:
                answer = f"PowerTool AI 调用失败：\n{exc}"
                status = "调用失败，请检查本地模型/API 配置。"
            except Exception as exc:
                answer = f"PowerTool AI 发生未预期异常：\n{exc}"
                status = "调用失败，请检查日志与配置。"

            def finish() -> None:
                self._ai_busy = False
                self.ai_status_var.set(_tr_obj(self, f"{status}\n当前截图：{screenshot_note}\n{self._ai_status_summary()}"))
                self._set_ai_answer(answer)

            self.after(0, finish)

        threading.Thread(target=worker, daemon=True).start()


# Export underscored helpers as well; mixin modules intentionally import the GUI helper namespace. / 同时导出下划线辅助函数，供各 GUI mixin 使用。
__all__ = [name for name in globals() if not name.startswith("__")]
