"""Frequency, oscillation, voltage, stability, and SMIB GUI mixin. / 频率、振荡、电压、暂稳和 SMIB 页面 mixin。"""

from __future__ import annotations

from power_tool_gui_common import *


class DynamicsGuiMixin:
    def _build_frequency_tab(self) -> None:
        self.freq_tab.columnconfigure(0, weight=1)
        self.freq_tab.rowconfigure(0, weight=1)

        shell = ttk.Frame(self.freq_tab, padding=8, style="Surface.TFrame")
        shell.grid(row=0, column=0, sticky="nsew")
        shell.columnconfigure(0, weight=0)
        shell.columnconfigure(1, weight=1)
        shell.rowconfigure(0, weight=1)

        left = ttk.Frame(shell, padding=16, style="Card.TFrame")
        right = ttk.Frame(shell, padding=16, style="Card.TFrame")
        left.grid(row=0, column=0, sticky="nsw", padx=(0, 6))
        right.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        right.columnconfigure(0, weight=1)
        right.rowconfigure(2, weight=1)
        left.columnconfigure(0, weight=1)
        left.rowconfigure(5, weight=1)

        ttk.Label(left, text="二阶频率动态（含一次调频）", style="PageTitle.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            left,
            text="界面按“基础模型—AGC—结果”组织。默认参数对应常规机组一次调频算例；启用 AGC 后会自动放宽绘图时长。",
            style="Muted.TLabel", justify="left", wraplength=430,
        ).grid(row=1, column=0, sticky="ew", pady=(4, 10))

        basic = ttk.LabelFrame(left, text="基础模型参数", style="Card.TLabelframe", padding=10)
        basic.grid(row=2, column=0, sticky="ew")
        basic.columnconfigure(1, weight=1)
        self.freq_f0 = self._add_entry(basic, 0, "额定频率 f0 / Hz", "50")
        self.freq_dp = self._add_entry(basic, 1, "功率缺额 ΔP_OL0 / pu", "0.08")
        self.freq_ts = self._add_entry(basic, 2, "系统惯性时间常数 T_s / s", "8")
        self.freq_tg = self._add_entry(basic, 3, "一次调频时间常数 T_G / s", "5")
        self.freq_kd = self._add_entry(basic, 4, "负荷频率系数 k_D / pu/pu", "1.2")
        self.freq_kg = self._add_entry(basic, 5, "一次调频系数 k_G / pu/pu", "4.0")
        self.freq_tend = self._add_entry(basic, 6, "绘图时长 / s", "30")
        self.show_first_order = tk.BooleanVar(value=True)
        ttk.Checkbutton(basic, text="同时绘制无一次调频一阶对照", variable=self.show_first_order, style="Card.TCheckbutton").grid(
            row=7, column=0, columnspan=2, sticky="w", padx=4, pady=(4, 2)
        )

        agc = ttk.LabelFrame(left, text="二次调频（AGC）", style="Card.TLabelframe", padding=10)
        agc.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        agc.columnconfigure(1, weight=1)
        self.enable_agc = tk.BooleanVar(value=False)
        ttk.Checkbutton(agc, text="启用 AGC（默认关闭）", variable=self.enable_agc,
                        command=self._on_agc_toggle, style="Card.TCheckbutton").grid(
            row=0, column=0, columnspan=2, sticky="w", padx=4, pady=(0, 6)
        )
        self.freq_beta = self._add_entry(agc, 1, "ACE频偏系数 B / (MW/Hz, 标幺化)", "15")
        self.freq_kp_agc = self._add_entry(agc, 2, "AGC比例 Kp", "0.12")
        self.freq_ki_agc = self._add_entry(agc, 3, "AGC积分 Ki / s⁻¹", "0.010")
        self.freq_tace = self._add_entry(agc, 4, "ACE滤波时间常数 Tace / s", "8")
        self.freq_tcmd = self._add_entry(agc, 5, "主站到机组执行滞后 Tcmd / s", "20")
        self.freq_p2max = self._add_entry(agc, 6, "二次调频最大调节量 |P2|max / pu", "0.08")
        self.freq_deadband = self._add_entry(agc, 7, "频率死区 |Δf| / Hz", "0.01")

        action = ttk.Frame(left, style="Card.TFrame")
        action.grid(row=4, column=0, sticky="ew", pady=(10, 8))
        action.columnconfigure(0, weight=1)
        ttk.Button(action, text="计算并绘图", command=self.calculate_frequency, style="Accent.TButton").grid(
            row=0, column=0, sticky="ew"
        )

        ttk.Label(left, text="结果摘要", style="SectionTitle.TLabel").grid(row=5, column=0, sticky="w", pady=(2, 4))
        self.freq_result = ScrolledText(left, width=54, height=22, wrap=tk.WORD)
        self.freq_result.grid(row=6, column=0, sticky="nsew")
        self.freq_result.configure(state="disabled")
        left.rowconfigure(6, weight=1)

        ttk.Label(right, text="频率响应曲线", style="PageTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(right, text="右侧绘图区与录波页保持相同的“图表 + 工具栏”组织形式，但改为浅色工程风格。",
                  style="Muted.TLabel", justify="left", wraplength=760).grid(row=1, column=0, sticky="w", pady=(4, 0))

        self.freq_fig = Figure(figsize=(7.6, 5.4), dpi=100)
        self.freq_ax = self.freq_fig.add_subplot(111)
        self.freq_ax.set_xlabel("t / s")
        self.freq_ax.set_ylabel("f / Hz")
        self.freq_ax.grid(True)

        self.freq_canvas = FigureCanvasTkAgg(self.freq_fig, master=right)
        self.freq_canvas.get_tk_widget().grid(row=2, column=0, sticky="nsew", pady=(10, 0))
        self.freq_toolbar = NavigationToolbar2Tk(self.freq_canvas, right, pack_toolbar=False)
        self.freq_toolbar.update()
        self.freq_toolbar.grid(row=3, column=0, sticky="ew", pady=(6, 0))

        self._on_agc_toggle()
        self.calculate_frequency()

    def _on_agc_toggle(self) -> None:
        agc_on = bool(self.enable_agc.get())
        state = "normal" if agc_on else "disabled"
        for ent in (self.freq_beta, self.freq_kp_agc, self.freq_ki_agc, self.freq_tace, self.freq_tcmd, self.freq_p2max, self.freq_deadband):
            ent.configure(state=state)

    def _build_oscillation_tab(self) -> None:
        self.osc_tab.columnconfigure(0, weight=1)
        self.osc_tab.rowconfigure(0, weight=1)

        shell = ttk.Frame(self.osc_tab, padding=8, style="Surface.TFrame")
        shell.pack(fill="both", expand=True)
        shell.columnconfigure(0, weight=0)
        shell.columnconfigure(1, weight=1)
        shell.rowconfigure(0, weight=1)

        left = ttk.Frame(shell, padding=16, style="Card.TFrame")
        right = ttk.Frame(shell, padding=16, style="Card.TFrame")
        left.grid(row=0, column=0, sticky="nsw", padx=(0, 6))
        right.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        left.columnconfigure(0, weight=1)
        right.columnconfigure(0, weight=1)
        right.rowconfigure(2, weight=1)

        ttk.Label(left, text="机电振荡频率快估", style="PageTitle.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            left,
            text="适用于单机与等值系统之间的小扰动初步核算。界面保留轻量输入，但使用更清晰的参数卡片与结果卡片布局。",
            style="Muted.TLabel", justify="left", wraplength=400,
        ).grid(row=1, column=0, sticky="ew", pady=(4, 10))

        form = ttk.LabelFrame(left, text="计算参数", style="Card.TLabelframe", padding=10)
        form.grid(row=2, column=0, sticky="ew")
        form.columnconfigure(1, weight=1)
        self.osc_eq = self._add_entry(form, 0, "内电势 E'_q / pu", "1.12")
        self.osc_u = self._add_entry(form, 1, "端电压 U / pu", "1.0")
        self.osc_x = self._add_entry(form, 2, "等值电抗 X_Σ / pu", "0.55")
        self.osc_p0 = self._add_entry(form, 3, "初始有功 P0 / pu", "0.8")
        self.osc_tj = self._add_entry(form, 4, "惯性时间常数 T_j / s", "9")
        self.osc_f0 = self._add_entry(form, 5, "同步频率 f0 / Hz", "50")

        ttk.Button(left, text="计算", command=self.calculate_oscillation, style="Accent.TButton").grid(
            row=3, column=0, sticky="ew", pady=(10, 0)
        )

        ttk.Label(right, text="计算结果", style="PageTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(right, text="右侧统一收纳摘要、点位图与冲击暂态电流波形。", style="Muted.TLabel", justify="left", wraplength=760).grid(row=1, column=0, sticky="ew", pady=(4, 8))
        ttk.Label(
            right,
            text="结果区强调固有频率、同步系数与线性化假设。与其它页统一为白色结果面板。",
            style="Muted.TLabel", justify="left", wraplength=720,
        ).grid(row=1, column=0, sticky="ew", pady=(4, 10))
        self.osc_result = ScrolledText(right, width=90, height=24, wrap=tk.WORD)
        self.osc_result.grid(row=2, column=0, sticky="nsew")
        self.osc_result.configure(state="disabled")

        self.calculate_oscillation()

    def _build_voltage_tab(self) -> None:
        self.volt_tab.columnconfigure(0, weight=1)
        self.volt_tab.rowconfigure(0, weight=1)
        nb = ttk.Notebook(self.volt_tab)
        nb.grid(row=0, column=0, sticky="nsew")
        self._vr_notebook = nb
        self._vr_notebook.bind("<<NotebookTabChanged>>", self._on_ai_context_changed)

        self._vr_static_tab = ttk.Frame(nb)
        self._vr_line_tab = ttk.Frame(nb)
        self._vr_avc_tab = ttk.Frame(nb)
        nb.add(self._vr_static_tab, text="静态电压稳定")
        nb.add(self._vr_line_tab, text="线路自然功率与无功")
        nb.add(self._vr_avc_tab, text="AVC策略模拟")

        # Subpage 1: static voltage stability / 子页1：静态电压稳定
        self._vr_static_tab.columnconfigure(0, weight=1)
        self._vr_static_tab.rowconfigure(0, weight=1)
        static_shell = ttk.Frame(self._vr_static_tab, padding=8, style="Surface.TFrame")
        static_shell.grid(row=0, column=0, sticky="nsew")
        static_shell.columnconfigure(0, weight=0, minsize=420)
        static_shell.columnconfigure(1, weight=1)
        static_shell.rowconfigure(0, weight=1)

        static_left = ttk.Frame(static_shell, padding=16, style="Card.TFrame")
        static_right = ttk.Frame(static_shell, padding=16, style="Card.TFrame")
        static_left.grid(row=0, column=0, sticky="nsw", padx=(0, 6))
        static_right.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        static_left.columnconfigure(0, weight=1)
        static_right.columnconfigure(0, weight=1)
        static_right.rowconfigure(2, weight=1)

        ttk.Label(static_left, text="静态电压稳定极限快估", style="PageTitle.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            static_left,
            text="界面改为“输入参数—结果说明”双栏结构，适合快速评估受端最低电压、最大有功传输与折算 MW 指标。",
            style="Muted.TLabel", justify="left", wraplength=390,
        ).grid(row=1, column=0, sticky="ew", pady=(4, 10))

        static_form = ttk.LabelFrame(static_left, text="参数输入", style="Card.TLabelframe", padding=10)
        static_form.grid(row=2, column=0, sticky="ew")
        static_form.columnconfigure(1, weight=1)
        self.volt_ug = self._add_entry(static_form, 0, "送端电压 U_g / pu", "1.0")
        self.volt_x = self._add_entry(static_form, 1, "总电抗 X_Σ / pu", "0.32")
        self.volt_pf = self._add_entry(static_form, 2, "功率因数 cosφ（默认滞后）", "0.95")
        self.volt_sbase = self._add_entry(static_form, 3, "容量基准 S_base / MVA（可改）", "100")
        ttk.Button(static_left, text="计算", command=self.calculate_voltage, style="Accent.TButton").grid(
            row=3, column=0, sticky="ew", pady=(10, 0)
        )

        ttk.Label(static_right, text="计算结果", style="PageTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            static_right,
            text="结果区强调稳定极限、受端最低电压与工程适用条件，便于与负荷水平或规划指标对照。",
            style="Muted.TLabel", justify="left", wraplength=760,
        ).grid(row=1, column=0, sticky="ew", pady=(4, 10))
        self.volt_result = ScrolledText(static_right, width=88, height=24, wrap=tk.WORD)
        self.volt_result.grid(row=2, column=0, sticky="nsew")
        self.volt_result.configure(state="disabled")

        # Subpage 2: natural power and reactive power / 子页2：线路自然功率与无功
        self._vr_line_tab.columnconfigure(0, weight=1)
        self._vr_line_tab.rowconfigure(0, weight=1)
        line_shell = ttk.Frame(self._vr_line_tab, padding=8, style="Surface.TFrame")
        line_shell.grid(row=0, column=0, sticky="nsew")
        line_shell.columnconfigure(0, weight=0, minsize=450)
        line_shell.columnconfigure(1, weight=1)
        line_shell.rowconfigure(0, weight=1)

        line_left = ttk.Frame(line_shell, padding=16, style="Card.TFrame")
        line_right = ttk.Frame(line_shell, padding=16, style="Card.TFrame")
        line_left.grid(row=0, column=0, sticky="nsw", padx=(0, 6))
        line_right.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        line_left.columnconfigure(0, weight=1)
        line_right.columnconfigure(0, weight=1)
        line_right.rowconfigure(2, weight=1)

        ttk.Label(line_left, text="长线路自然功率与无功行为快估", style="PageTitle.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            line_left,
            text="左侧保留线路额定电压、波阻抗、充电功率与长度等输入；右侧集中展示自然功率、无功平衡与实际运行偏离。",
            style="Muted.TLabel", justify="left", wraplength=420,
        ).grid(row=1, column=0, sticky="ew", pady=(4, 10))

        line_form = ttk.LabelFrame(line_left, text="线路参数", style="Card.TLabelframe", padding=10)
        line_form.grid(row=2, column=0, sticky="ew")
        line_form.columnconfigure(1, weight=1)
        self.line_u = self._add_entry(line_form, 0, "线路额定电压 U / kV（线电压）", "500")
        self.line_zc = self._add_entry(line_form, 1, "波阻抗 Z_c / Ω（优先）", "250")
        self.line_l = self._add_entry(line_form, 2, "单位长度电感 L（可留空）", "")
        self.line_c = self._add_entry(line_form, 3, "单位长度电容 C（可留空）", "")
        self.line_p = self._add_entry(line_form, 4, "实际传输有功 P / MW", "700")
        self.line_qn = self._add_entry(line_form, 5, "单位长度充电功率 Q_N / (Mvar/km)", "1.2")
        self.line_len = self._add_entry(line_form, 6, "线路长度 l / km", "200")
        ttk.Button(line_left, text="计算", command=self.calculate_line, style="Accent.TButton").grid(
            row=3, column=0, sticky="ew", pady=(10, 0)
        )

        ttk.Label(line_right, text="计算结果", style="PageTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            line_right,
            text="结果区按照自然功率、充电无功、实际潮流偏离三部分整理，更适合教学展示与方案初步核算。",
            style="Muted.TLabel", justify="left", wraplength=760,
        ).grid(row=1, column=0, sticky="ew", pady=(4, 10))
        self.line_result = ScrolledText(line_right, width=88, height=24, wrap=tk.WORD)
        self.line_result.grid(row=2, column=0, sticky="nsew")
        self.line_result.configure(state="disabled")

        # Subpage 3: AVC strategy simulation / 子页3：AVC策略模拟
        self._vr_avc_tab.columnconfigure(0, weight=1)
        self._vr_avc_tab.rowconfigure(0, weight=1)
        avc_shell = ttk.Frame(self._vr_avc_tab, padding=8, style="Surface.TFrame")
        avc_shell.grid(row=0, column=0, sticky="nsew")
        avc_shell.columnconfigure(0, weight=0, minsize=500)
        avc_shell.columnconfigure(1, weight=1)
        avc_shell.rowconfigure(0, weight=1)

        avc_left_outer, avc_left, _avc_canvas = self._create_scrollable_card(avc_shell, padding=16)
        avc_left_outer.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        avc_right = ttk.Frame(avc_shell, padding=16, style="Card.TFrame")
        avc_right.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        avc_left.columnconfigure(0, weight=1)
        avc_right.columnconfigure(0, weight=1)
        avc_right.rowconfigure(2, weight=1)

        ttk.Label(avc_left, text="AVC策略模拟（降压变压器+无功补偿）", style="PageTitle.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            avc_left,
            text="将 AVC 页改为滚动输入卡片，减少长表单带来的压迫感；右侧单独显示 9 区策略判断、推荐档位与无功投切结果。",
            style="Muted.TLabel", justify="left", wraplength=460,
        ).grid(row=1, column=0, sticky="ew", pady=(4, 10))

        avc_form = ttk.LabelFrame(avc_left, text="运行点与设备参数", style="Card.TLabelframe", padding=10)
        avc_form.grid(row=2, column=0, sticky="ew")
        avc_form.columnconfigure(1, weight=1)
        self.avc_hv_kv = self._add_entry(avc_form, 0, "高压侧额定电压 / kV", "220")
        self.avc_lv_kv = self._add_entry(avc_form, 1, "低压侧额定电压 / kV", "110")
        self.avc_vh = self._add_entry(avc_form, 2, "高压侧当前电压 / kV", "226")
        self.avc_lv_min = self._add_entry(avc_form, 3, "低压侧电压下限 / kV", "108")
        self.avc_lv_max = self._add_entry(avc_form, 4, "低压侧电压上限 / kV", "116")
        self.avc_tap_min = self._add_entry(avc_form, 5, "变压器最小档位", "-8")
        self.avc_tap_max = self._add_entry(avc_form, 6, "变压器最大档位", "8")
        self.avc_tap_now = self._add_entry(avc_form, 7, "变压器当前档位", "0")
        self.avc_tap_step = self._add_entry(avc_form, 8, "单档电压调节率 / %", "1.25")
        self.avc_cap_num = self._add_entry(avc_form, 9, "低压侧电容器组数量", "2")
        self.avc_cap_each = self._add_entry(avc_form, 10, "每组电容器容量 / Mvar", "10")
        self.avc_rea_num = self._add_entry(avc_form, 11, "低压侧电抗器组数量", "1")
        self.avc_rea_each = self._add_entry(avc_form, 12, "每组电抗器容量 / Mvar", "10")
        self.avc_p = self._add_entry(avc_form, 13, "高压侧有功潮流 P / MW", "160")
        self.avc_q = self._add_entry(avc_form, 14, "高压侧无功潮流 Q / Mvar（感性为正）", "45")
        self.avc_sys_sc_mva = self._add_entry(avc_form, 15, "高压侧系统容量 Ssc / MVA", "6000")
        self.avc_tx_mva = self._add_entry(avc_form, 16, "变压器容量 SN / MVA", "180")
        self.avc_tx_uk_pct = self._add_entry(avc_form, 17, "变压器短路电压 Uk / %", "12")
        ttk.Button(avc_left, text="执行9区策略模拟", command=self.calculate_avc_strategy, style="Accent.TButton").grid(
            row=3, column=0, sticky="ew", pady=(10, 0)
        )

        ttk.Label(avc_right, text="策略结果", style="PageTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            avc_right,
            text="结果区突出 AVC 当前区间、建议调压方向、档位与补偿设备动作。适合作为运行策略解释面板。",
            style="Muted.TLabel", justify="left", wraplength=760,
        ).grid(row=1, column=0, sticky="ew", pady=(4, 10))
        self.avc_result = ScrolledText(avc_right, width=88, height=22, wrap=tk.WORD)
        self.avc_result.grid(row=2, column=0, sticky="nsew")
        self.avc_result.configure(state="disabled")

        self.calculate_voltage()
        self.calculate_line()
        self.calculate_avc_strategy()

    def _build_impact_tab(self) -> None:
        self.impact_tab.columnconfigure(0, weight=1)
        self.impact_tab.rowconfigure(0, weight=1)

        shell = ttk.Frame(self.impact_tab, padding=8, style="Surface.TFrame")
        shell.grid(row=0, column=0, sticky="nsew")
        shell.columnconfigure(0, weight=0)
        shell.columnconfigure(1, weight=1)
        shell.rowconfigure(0, weight=1)

        left = ttk.Frame(shell, padding=16, style="Card.TFrame")
        right = ttk.Frame(shell, padding=16, style="Card.TFrame")
        left.grid(row=0, column=0, sticky="nsw", padx=(0, 6))
        right.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        right.columnconfigure(0, weight=1)
        right.rowconfigure(2, weight=1)

        ttk.Label(left, text="暂稳评估", style="PageTitle.TLabel").pack(anchor="w")
        ttk.Label(
            left,
            text="左侧统一收纳等面积法与冲击法。上框侧重 P-δ 曲线及临界清除判断，下框用于快估功率振荡幅度。",
            style="Muted.TLabel", justify="left", wraplength=430,
        ).pack(fill="x", pady=(4, 10))

        eac_frame = ttk.LabelFrame(left, text="等面积法（单机无穷大）", style="Card.TLabelframe", padding=10)
        eac_frame.pack(fill="both", expand=True, pady=(0, 10))
        eac_frame.columnconfigure(1, weight=1)
        eac_frame.rowconfigure(8, weight=1)
        self.eac_pm    = self._add_entry(eac_frame, 0, "机械功率 Pm / pu", "0.90")
        self.eac_ppre  = self._add_entry(eac_frame, 1, "故障前 Pmax_pre / pu", "1.65")
        self.eac_pf    = self._add_entry(eac_frame, 2, "故障中 Pmax_fault / pu（三相故障填 0）", "0.0")
        self.eac_ppost = self._add_entry(eac_frame, 3, "故障后 Pmax_post / pu", "1.65")
        self.eac_dt    = self._add_entry(eac_frame, 4, "故障切除时间 Δt / s", "0.12")
        self.eac_tj    = self._add_entry(eac_frame, 5, "惯性时间常数 Tj / s", "9")
        self.eac_f0    = self._add_entry(eac_frame, 6, "额定频率 f0 / Hz", "50")
        ttk.Button(eac_frame, text="计算并绘图", command=self.calculate_eac, style="Accent.TButton").grid(
            row=7, column=0, columnspan=2, sticky="ew", padx=4, pady=(8, 4)
        )
        self.eac_result = ScrolledText(eac_frame, width=50, height=13, wrap=tk.WORD)
        self.eac_result.grid(row=8, column=0, columnspan=2, sticky="nsew", padx=2, pady=4)
        self.eac_result.configure(state="disabled")

        imp_frame = ttk.LabelFrame(left, text="冲击法快估", style="Card.TLabelframe", padding=10)
        imp_frame.pack(fill="x", expand=False)
        imp_frame.columnconfigure(1, weight=1)
        self.imp_dp   = self._add_entry(imp_frame, 0, "故障加速功率 ΔPa / pu", "0.9")
        self.imp_dt   = self._add_entry(imp_frame, 1, "故障切除时间 Δt / s", "0.12")
        self.imp_fd   = self._add_entry(imp_frame, 2, "故障后振荡频率 f_d / Hz", "1.106")
        ttk.Button(imp_frame, text="计算冲击法", command=self.calculate_impact, style="Accent.TButton").grid(
            row=3, column=0, columnspan=2, sticky="ew", padx=4, pady=(8, 4)
        )
        self.imp_result = ScrolledText(imp_frame, width=50, height=8, wrap=tk.WORD)
        self.imp_result.grid(row=4, column=0, columnspan=2, sticky="nsew", padx=2, pady=4)
        self.imp_result.configure(state="disabled")

        ttk.Label(right, text="功角曲线（等面积法）", style="PageTitle.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            right,
            text="图形区改为浅色工程图风格，重点突出故障前/中/后功角曲线与加减速面积。",
            style="Muted.TLabel", justify="left", wraplength=760,
        ).grid(row=1, column=0, sticky="ew", pady=(4, 8))

        self.eac_fig = Figure(figsize=(7.4, 5.6), dpi=100)
        self.eac_ax  = self.eac_fig.add_subplot(111)
        self.eac_ax.set_xlabel("δ / °")
        self.eac_ax.set_ylabel("P / pu")
        self.eac_ax.set_title("功角曲线（等待计算）")
        self.eac_ax.grid(True)

        self.eac_canvas = FigureCanvasTkAgg(self.eac_fig, master=right)
        self.eac_canvas.get_tk_widget().grid(row=2, column=0, sticky="nsew")
        self.eac_toolbar = NavigationToolbar2Tk(self.eac_canvas, right, pack_toolbar=False)
        self.eac_toolbar.update()
        self.eac_toolbar.grid(row=3, column=0, sticky="ew", pady=(6, 0))

        self.calculate_impact()
        self.calculate_eac()

    def _build_smib_tab(self) -> None:
        self.smib_tab.columnconfigure(1, weight=1)
        self.smib_tab.rowconfigure(0, weight=1)

        left = ttk.Frame(self.smib_tab, padding=10, style="Card.TFrame")
        right = ttk.Frame(self.smib_tab, padding=10, style="Card.TFrame")
        left.grid(row=0, column=0, sticky="nsw", padx=(0, 6), pady=2)
        right.grid(row=0, column=1, sticky="nsew", padx=(6, 0), pady=2)

        left.columnconfigure(0, weight=1)
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=2)
        right.rowconfigure(3, weight=3)

        ttk.Label(left, text="单机无穷大系统小扰动分析", style="Card.TLabel",
                  font=("TkDefaultFont", 11, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 6))
        intro = (
            "采用 Kundur 经典 SMIB 示例的六阶同步机模型；可切换“机组”“机组+AVR”“机组+AVR+PSS”三种配置。"
            " 新增“1型AVR/PSS模型”参数页（按教材框图）用于控制环节频域校核。"
            " 程序先由给定运行点构造平衡点，再对非线性模型数值线性化并求取特征值。"
        )
        ttk.Label(left, text=intro, style="Card.TLabel", justify="left",
                  wraplength=430).grid(row=1, column=0, sticky="w", pady=(0, 8))

        topbar = ttk.Frame(left, style="Card.TFrame")
        topbar.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        topbar.columnconfigure(1, weight=1)

        ttk.Label(topbar, text="模型配置", style="Card.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 6))
        self.smib_config = ttk.Combobox(topbar, state="readonly", width=22, values=_SMIB_CONFIG_OPTIONS)
        self.smib_config.grid(row=0, column=1, sticky="ew", padx=(0, 6))
        self.smib_config.bind("<<ComboboxSelected>>", self._on_smib_config_change)
        ttk.Button(topbar, text="恢复 Kundur 默认值", command=self._apply_smib_defaults).grid(row=0, column=2, padx=(0, 6))
        ttk.Button(topbar, text="切换到1型 AVR/PSS", command=self._goto_type1_avr_pss_page).grid(row=0, column=3, padx=(0, 6))
        ttk.Button(topbar, text="计算并绘图", command=self.calculate_smib).grid(row=0, column=4)

        self.smib_mode_hint_var = tk.StringVar(value="提示：主分析采用 Kundur 六阶小扰动模型；1型 AVR/PSS 用于参数校核。")
        ttk.Label(left, textvariable=self.smib_mode_hint_var, style="Muted.TLabel", wraplength=560, justify="left").grid(
            row=3, column=0, sticky="ew", pady=(0, 6)
        )

        nb = ttk.Notebook(left)
        nb.grid(row=4, column=0, sticky="nsew")
        left.rowconfigure(4, weight=1)
        self.smib_sub_notebook = nb

        page_case = ttk.Frame(nb, padding=8)
        page_machine = ttk.Frame(nb, padding=8)
        page_avr = ttk.Frame(nb, padding=8)
        page_pss = ttk.Frame(nb, padding=8)
        page_type1 = ttk.Frame(nb, padding=0)
        page_type1.columnconfigure(0, weight=1)
        page_type1.rowconfigure(0, weight=1)
        self.smib_page_type1 = page_type1
        nb.add(page_case, text="工况与网络")
        nb.add(page_machine, text="六阶机组")
        nb.add(page_avr, text="AVR III")
        nb.add(page_pss, text="PSS II")
        nb.add(page_type1, text="1型 AVR/PSS")

        for page in (page_case, page_machine, page_avr, page_pss):
            page.columnconfigure(1, weight=1)
            page.columnconfigure(3, weight=1)

        page_type1_canvas = tk.Canvas(page_type1, highlightthickness=0)
        page_type1_scroll = ttk.Scrollbar(page_type1, orient="vertical", command=page_type1_canvas.yview)
        page_type1_body = ttk.Frame(page_type1_canvas, padding=8)
        page_type1_body.columnconfigure(1, weight=1)
        page_type1_body.columnconfigure(3, weight=1)
        page_type1_canvas.configure(yscrollcommand=page_type1_scroll.set)
        page_type1_canvas.grid(row=0, column=0, sticky="nsew")
        page_type1_scroll.grid(row=0, column=1, sticky="ns")
        page_type1_window = page_type1_canvas.create_window((0, 0), window=page_type1_body, anchor="nw")
        page_type1_body.bind("<Configure>", lambda _e: page_type1_canvas.configure(scrollregion=page_type1_canvas.bbox("all")))
        page_type1_canvas.bind("<Configure>", lambda e: page_type1_canvas.itemconfigure(page_type1_window, width=e.width))

        self.smib_entries: dict[str, ttk.Entry] = {}
        self.smib_avr_widgets: list[tk.Widget] = []
        self.smib_pss_widgets: list[tk.Widget] = []

        def add(page: ttk.Frame, key: str, row: int, label: str, default: str, column: int = 0, width: int = 12) -> ttk.Entry:
            entry = self._add_entry(page, row, label, default, column=column, width=width)
            self.smib_entries[key] = entry
            return entry

        add(page_case, "P0", 0, "有功 P0 / pu", "0.90", column=0)
        add(page_case, "Q0", 0, "无功 Q0 / pu", "0.436002238697", column=2)
        add(page_case, "Vt", 1, "端电压 |Vt| / pu", "1.00", column=0)
        add(page_case, "theta_deg", 1, "端电压角 θt / °", "28.342914463", column=2)
        add(page_case, "xT", 2, "变压器电抗 xT / pu", "0.15", column=0)
        add(page_case, "xL1", 2, "线路 1 电抗 xL1 / pu", "0.50", column=2)
        add(page_case, "xL2", 3, "线路 2 电抗 xL2 / pu", "0.93", column=0)
        add(page_case, "f0", 3, "系统频率 f0 / Hz", "60", column=2)
        ttk.Label(page_case, text="说明：程序自动将无穷大母线相角平移为 0°；若 xL2≤0，则视为第二回线路停运。",
                  wraplength=390).grid(row=4, column=0, columnspan=4, sticky="w", padx=4, pady=(6, 0))

        add(page_machine, "ra", 0, "电枢电阻 ra / pu", "0.003", column=0)
        add(page_machine, "xd", 0, "同步电抗 xd / pu", "1.81", column=2)
        add(page_machine, "xq", 1, "同步电抗 xq / pu", "1.76", column=0)
        add(page_machine, "x1d", 1, "暂态电抗 x'd / pu", "0.30", column=2)
        add(page_machine, "x1q", 2, "暂态电抗 x'q / pu", "0.65", column=0)
        add(page_machine, "x2d", 2, "次暂态电抗 x''d / pu", "0.23", column=2)
        add(page_machine, "x2q", 3, "次暂态电抗 x''q / pu", "0.25", column=0)
        add(page_machine, "T1d0", 3, "开路 T'd0 / s", "8.0", column=2)
        add(page_machine, "T1q0", 4, "开路 T'q0 / s", "1.0", column=0)
        add(page_machine, "T2d0", 4, "开路 T''d0 / s", "0.03", column=2)
        add(page_machine, "T2q0", 5, "开路 T''q0 / s", "0.07", column=0)
        add(page_machine, "M", 5, "机械起动时间 M=2H / s", "7.0", column=2)
        add(page_machine, "D", 6, "阻尼 D / pu", "0.0", column=0)

        self.smib_avr_widgets.extend([
            add(page_avr, "avr_K0", 0, "放大倍数 K0", "200", column=0),
            add(page_avr, "avr_T1", 0, "零点 T1 / s", "1.0", column=2),
            add(page_avr, "avr_T2", 1, "极点 T2 / s", "1.0", column=0),
            add(page_avr, "avr_Te", 1, "励磁回路 Te / s", "0.0001", column=2),
            add(page_avr, "avr_Tr", 2, "测量时间 Tr / s", "0.015", column=0),
            add(page_avr, "avr_vfmax", 2, "上限 vfmax / pu", "7.0", column=2),
            add(page_avr, "avr_vfmin", 3, "下限 vfmin / pu", "-6.4", column=0),
        ])

        self.smib_pss_widgets.extend([
            add(page_pss, "pss_Kw", 0, "洗出增益 Kw", "9.5", column=0),
            add(page_pss, "pss_Tw", 0, "洗出时间 Tw / s", "1.41", column=2),
            add(page_pss, "pss_T1", 1, "一阶超前 T1 / s", "0.154", column=0),
            add(page_pss, "pss_T2", 1, "一阶滞后 T2 / s", "0.033", column=2),
            add(page_pss, "pss_T3", 2, "二阶超前 T3 / s", "1.0", column=0),
            add(page_pss, "pss_T4", 2, "二阶滞后 T4 / s", "1.0", column=2),
            add(page_pss, "pss_vsmax", 3, "上限 vsmax / pu", "0.2", column=0),
            add(page_pss, "pss_vsmin", 3, "下限 vsmin / pu", "-0.2", column=2),
        ])

        page_avr.rowconfigure(5, weight=1)
        self.smib_avr_fig = Figure(figsize=(6.4, 2.2), dpi=100)
        self.smib_avr_ax = self.smib_avr_fig.add_subplot(111)
        _draw_avr_transfer_diagram(self.smib_avr_ax)
        self.smib_avr_canvas = FigureCanvasTkAgg(self.smib_avr_fig, master=page_avr)
        self.smib_avr_canvas.get_tk_widget().grid(row=5, column=0, columnspan=4, sticky="nsew", padx=4, pady=(8, 0))
        self.smib_avr_canvas.draw()

        page_pss.rowconfigure(5, weight=1)
        self.smib_pss_fig = Figure(figsize=(6.4, 2.1), dpi=100)
        self.smib_pss_ax = self.smib_pss_fig.add_subplot(111)
        _draw_pss_transfer_diagram(self.smib_pss_ax)
        self.smib_pss_canvas = FigureCanvasTkAgg(self.smib_pss_fig, master=page_pss)
        self.smib_pss_canvas.get_tk_widget().grid(row=5, column=0, columnspan=4, sticky="nsew", padx=4, pady=(8, 0))
        self.smib_pss_canvas.draw()

        self.smib_type1_entries: dict[str, ttk.Entry] = {}
        def add_type1(key: str, row: int, label: str, default: str, column: int = 0) -> None:
            self.smib_type1_entries[key] = self._add_entry(page_type1_body, row, label, default, column=column, width=11)

        add_type1("Kr", 0, "Kr", "1.0", 0); add_type1("Tr", 0, "Tr / s", "0.02", 2)
        add_type1("Ka", 1, "Ka", "200", 0); add_type1("Ta", 1, "Ta / s", "0.05", 2)
        add_type1("Kf", 2, "Kf", "0.05", 0); add_type1("Tf", 2, "Tf / s", "1.0", 2)
        add_type1("Te", 3, "Te / s", "0.5", 0); add_type1("Efd_max", 3, "Efd_max / pu", "6.0", 2)
        add_type1("Efd_min", 4, "Efd_min / pu", "-6.0", 0)
        add_type1("Kq1", 5, "Kq1", "10", 0); add_type1("Kq2", 5, "Kq2", "2", 2)
        add_type1("Kq3", 6, "Kq3", "1", 0); add_type1("Kpss", 6, "K", "10", 2)
        add_type1("Tq", 7, "Tq / s", "0.1", 0); add_type1("T1e", 7, "T1e / s", "0.15", 2)
        add_type1("T2e", 8, "T2e / s", "0.03", 0); add_type1("T3e", 8, "T3e / s", "0.15", 2)
        add_type1("T4e", 9, "T4e / s", "0.03", 0); add_type1("Vsmax", 9, "Vsmax / pu", "0.2", 2)
        add_type1("Vsmin", 10, "Vsmin / pu", "-0.2", 0); add_type1("f_eval", 10, "评估频率 / Hz", "1.0", 2)

        ttk.Label(
            page_type1_body,
            text="传递函数框图（参考教材 1型 AVR/PSS）：",
            style="Muted.TLabel",
        ).grid(row=11, column=0, columnspan=4, sticky="w", padx=4, pady=(8, 2))

        self.smib_type1_pss_fig = Figure(figsize=(6.4, 2.6), dpi=100)
        self.smib_type1_pss_ax = self.smib_type1_pss_fig.add_subplot(111)
        _draw_type1_pss_diagram(self.smib_type1_pss_ax)
        self.smib_type1_pss_canvas = FigureCanvasTkAgg(self.smib_type1_pss_fig, master=page_type1_body)
        self.smib_type1_pss_canvas.get_tk_widget().grid(row=12, column=0, columnspan=4, sticky="nsew", padx=4, pady=(0, 2))
        self.smib_type1_pss_canvas.draw()

        self.smib_type1_avr_fig = Figure(figsize=(6.4, 2.8), dpi=100)
        self.smib_type1_avr_ax = self.smib_type1_avr_fig.add_subplot(111)
        _draw_type1_avr_diagram(self.smib_type1_avr_ax)
        self.smib_type1_avr_canvas = FigureCanvasTkAgg(self.smib_type1_avr_fig, master=page_type1_body)
        self.smib_type1_avr_canvas.get_tk_widget().grid(row=13, column=0, columnspan=4, sticky="nsew", padx=4, pady=(0, 4))
        self.smib_type1_avr_canvas.draw()

        ttk.Button(page_type1_body, text="计算1型 AVR/PSS 指标", command=self.calculate_type1_avr_pss).grid(
            row=14, column=0, columnspan=4, sticky="ew", padx=4, pady=(4, 4)
        )
        self.smib_type1_result = ScrolledText(page_type1_body, width=56, height=8, wrap=tk.WORD)
        self.smib_type1_result.grid(row=15, column=0, columnspan=4, sticky="nsew", padx=4, pady=(2, 2))
        self.smib_type1_result.configure(state="disabled")

        ttk.Label(right, text="模态结果", style="Card.TLabel",
                  font=("TkDefaultFont", 11, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 4))
        self.smib_result = ScrolledText(right, width=78, height=18, wrap=tk.WORD, font="TkFixedFont")
        self.smib_result.grid(row=1, column=0, sticky="nsew")
        self.smib_result.configure(state="disabled")

        ttk.Label(right, text="特征值复平面", style="Card.TLabel",
                  font=("TkDefaultFont", 11, "bold")).grid(row=2, column=0, sticky="w", pady=(10, 4))
        self.smib_fig = Figure(figsize=(7.6, 4.8), dpi=100)
        self.smib_ax = self.smib_fig.add_subplot(111)
        self.smib_ax.set_xlabel("Re(λ) / 1/s")
        self.smib_ax.set_ylabel("Im(λ) / rad/s")
        self.smib_ax.grid(True, alpha=0.35)

        self.smib_canvas = FigureCanvasTkAgg(self.smib_fig, master=right)
        self.smib_canvas.get_tk_widget().grid(row=3, column=0, sticky="nsew")
        self.smib_toolbar = NavigationToolbar2Tk(self.smib_canvas, right, pack_toolbar=False)
        self.smib_toolbar.update()
        self.smib_toolbar.grid(row=4, column=0, sticky="ew")

        self._apply_smib_defaults()

    def calculate_type1_avr_pss(self) -> None:
        try:
            p = {k: _safe_float(v.get(), k) for k, v in self.smib_type1_entries.items()}
            for key in ("Tr", "Ta", "Tf", "Te", "Tq", "T1e", "T2e", "T3e", "T4e"):
                _validate_positive(key, p[key])
            _validate_positive("评估频率", p["f_eval"])
            if p["Efd_min"] >= p["Efd_max"]:
                raise InputError("Efd_min 必须小于 Efd_max。")
            if p["Vsmin"] >= p["Vsmax"]:
                raise InputError("Vsmin 必须小于 Vsmax。")

            w = 2.0 * math.pi * p["f_eval"]
            s = complex(0.0, w)
            avr_meas = p["Kr"] / (1.0 + s * p["Tr"])
            avr_amp = p["Ka"] / (1.0 + s * p["Ta"])
            avr_exc = 1.0 / (1.0 + s * p["Te"])
            avr_fb = s * p["Kf"] / (1.0 + s * p["Tf"])
            avr_open = avr_meas * avr_amp * avr_exc
            avr_closed = avr_open / (1.0 + avr_open * avr_fb)

            pss_in = p["Kq1"] + p["Kq2"] + p["Kq3"]
            pss_core = (p["Kpss"] + s) / (1.0 + s * p["Tq"])
            lead1 = (1.0 + s * p["T1e"]) / (1.0 + s * p["T2e"])
            lead2 = (1.0 + s * p["T3e"]) / (1.0 + s * p["T4e"])
            pss_tf = pss_in * pss_core * lead1 * lead2
            vs_est = max(p["Vsmin"], min(p["Vsmax"], pss_tf.real))

            def _fmt(z: complex) -> str:
                return f"{abs(z):.4f}∠{math.degrees(math.atan2(z.imag, z.real)):+.2f}°"

            text = (
                "══ 1型 AVR/PSS 模型校核 ═════════════════\n"
                f"评估频率：{p['f_eval']:.4f} Hz\n\n"
                "【AVR】\n"
                f"Gm(s)=Kr/(1+sTr) = {_fmt(avr_meas)}\n"
                f"Ga(s)=Ka/(1+sTa) = {_fmt(avr_amp)}\n"
                f"Ge(s)=1/(1+sTe) = {_fmt(avr_exc)}\n"
                f"Gf(s)=sKf/(1+sTf) = {_fmt(avr_fb)}\n"
                f"开环 Gavr = {_fmt(avr_open)}\n"
                f"闭环 Gavr_cl = {_fmt(avr_closed)}\n"
                f"Efd 限幅区间 = [{p['Efd_min']:.3f}, {p['Efd_max']:.3f}] pu\n\n"
                "【PSS】\n"
                f"输入加权 Kq1+Kq2+Kq3 = {pss_in:.4f}\n"
                f"Gpss(s) = {_fmt(pss_tf)}\n"
                f"Vs 估算（实部限幅）= {vs_est:.4f} pu，限值[{p['Vsmin']:.3f}, {p['Vsmax']:.3f}]\n\n"
                "说明：该页按截图中的1型 AVR/PSS 传函进行环节校核，用于小扰动控制参数整定参考。"
            )
            self._set_text(self.smib_type1_result, text)
        except Exception as exc:
            messagebox.showerror("计算错误", str(exc))

    def _apply_smib_defaults(self) -> None:
        defaults = kundur_smib_defaults()
        self.smib_config.set(_display_obj(self, str(defaults["config"])))
        for key, value in defaults.items():
            if key == "config":
                continue
            entry = self.smib_entries[key]
            entry.configure(state="normal")
            entry.delete(0, tk.END)
            entry.insert(0, str(value))
        self._on_smib_config_change()
        self.calculate_smib()

    def _on_smib_config_change(self, _event: object | None = None) -> None:
        config_label = _logic_obj(self, self.smib_config.get().strip())
        config_key = _SMIB_CONFIG_KEY.get(config_label, "avr_pss")
        self._set_enabled(self.smib_avr_widgets, config_key in {"avr", "avr_pss"})
        self._set_enabled(self.smib_pss_widgets, config_key == "avr_pss")
        label = self.smib_config.get().strip() or _display_obj(self, "未选择")
        if hasattr(self, "smib_mode_hint_var"):
            self.smib_mode_hint_var.set(
                _tr_obj(self, f"提示：当前主分析模型为「{label}」（Kundur 六阶线化）；如需 1型 AVR/PSS 请点击上方按钮切换到参数校核页。")
            )

    def _goto_type1_avr_pss_page(self) -> None:
        if hasattr(self, "smib_sub_notebook") and hasattr(self, "smib_page_type1"):
            self.smib_sub_notebook.select(self.smib_page_type1)
        if hasattr(self, "smib_mode_hint_var"):
            self.smib_mode_hint_var.set(_tr_obj(self, "提示：已切换到 1型 AVR/PSS 参数页，可直接输入参数并点击“计算1型 AVR/PSS 指标”。"))

    def _read_smib_inputs(self) -> tuple[str, dict[str, float]]:
        label = _logic_obj(self, self.smib_config.get().strip()) or "六阶机组 + AVR + PSS"
        config_key = _SMIB_CONFIG_KEY.get(label)
        if config_key is None:
            raise InputError("请选择有效的小扰动模型配置。")

        params: dict[str, float] = {}
        for key, entry in self.smib_entries.items():
            text = entry.get().strip()
            if key == "xL2" and text == "":
                params[key] = 0.0
                continue
            params[key] = _safe_float(text, key)

        if params["xL2"] <= 0:
            params["xL2"] = 0.0
        return config_key, params

    def calculate_smib(self) -> None:
        try:
            config_key, params = self._read_smib_inputs()
            result = smib_small_signal_analysis(config_key, params)
            op = result.operating_point
            eigs = result.eigenvalues
            rows = _smib_modal_rows(eigs)
            max_real = float(np.max(np.real(eigs))) if eigs.size else float("nan")

            status = "稳定" if result.stable else "不稳定"
            text = (
                f"配置：{result.config_label}\n"
                f"状态维数：{len(result.state_names)}\n"
                f"稳定性：{status}（max Re(λ) = {max_real:+.6f} 1/s）\n"
                f"\n── 平衡点（以无穷大母线为角度参考）────────────────\n"
                f"V∞ = {op.infinite_bus_voltage_pu:.6f} pu\n"
                f"Vt = {op.terminal_voltage_pu:.6f} ∠ {op.terminal_angle_deg:.6f}° pu\n"
                f"P + jQ = {op.P_pu:.6f} + j{op.Q_pu:.6f} pu\n"
                f"δ0 = {op.delta_deg:.6f}°\n"
                f"pm0 = {op.pm_pu:.6f} pu，vf0 = {op.vf0_pu:.6f} pu\n"
                f"id0 = {op.id_pu:.6f} pu，iq0 = {op.iq_pu:.6f} pu\n"
                f"vd0 = {op.vd_pu:.6f} pu，vq0 = {op.vq_pu:.6f} pu\n"
                f"Xline,eq = {op.xline_eq_pu:.6f} pu，Xnet = {op.xnet_pu:.6f} pu\n"
                f"参考角平移 = {op.reference_shift_deg:+.6f}°\n"
            )

            if result.dominant_mode_index is not None:
                lam = eigs[result.dominant_mode_index]
                freq = abs(lam.imag) / (2.0 * math.pi)
                zeta = None if abs(lam.imag) < 1e-8 else -lam.real / abs(lam)
                text += "\n── 最弱阻尼模态 ───────────────────────────────────\n"
                text += f"λ_dom = {_format_eigenvalue(lam)} 1/s\n"
                if zeta is None:
                    text += "该模态为实根，非振荡模态。\n"
                else:
                    text += f"f_dom = {freq:.6f} Hz，ζ = {zeta * 100:.3f} %\n"
                if result.dominant_participation:
                    parts = []
                    for name, weight in result.dominant_participation[:4]:
                        parts.append(f"{_SMIB_STATE_LABELS.get(name, name)} {weight * 100:.1f}%")
                    text += "主导参与状态：" + "， ".join(parts) + "\n"

            text += "\n── 模态表（仅列 Im(λ) ≥ 0 的独立模态）──────────────\n"
            text += "序号  特征值 λ / (1/s)                 f / Hz     ζ / %     类型\n"
            text += "-" * 70 + "\n"
            for row in rows:
                lam = row["lambda"]
                zeta = row["zeta"]
                ztxt = "   -   " if zeta is None else f"{zeta * 100:8.3f}"
                text += (
                    f"{row['idx']:>2d}    {_format_eigenvalue(lam):<28}  "
                    f"{row['freq']:>8.4f}  {ztxt}   {row['type']}\n"
                )

            text += "\n说明：\n" + result.notes
            self._set_text(self.smib_result, text)

            ax = self.smib_ax
            ax.clear()
            ax.axvline(0.0, linestyle=":", linewidth=1.2)
            ax.axhline(0.0, linestyle="--", linewidth=0.8)
            ax.plot(np.real(eigs), np.imag(eigs), "o", markersize=5)
            for i, lam in enumerate(eigs):
                if abs(lam.imag) > 1e-8 and lam.imag > 0:
                    lbl = f"{abs(lam.imag) / (2.0 * math.pi):.2f} Hz"
                    if i == result.dominant_mode_index or lam.real > -1.5:
                        ax.annotate(lbl, (lam.real, lam.imag), textcoords="offset points", xytext=(4, 4), fontsize=8)
            real_vals = np.real(eigs)
            imag_vals = np.imag(eigs)
            xr = max(1.0, float(np.max(real_vals) - np.min(real_vals)))
            yr = max(1.0, float(np.max(imag_vals) - np.min(imag_vals)))
            ax.set_xlim(float(np.min(real_vals) - 0.12 * xr), float(np.max(real_vals) + 0.12 * xr))
            ax.set_ylim(float(np.min(imag_vals) - 0.12 * yr), float(np.max(imag_vals) + 0.12 * yr))
            ax.set_xlabel("Re(λ) / 1/s")
            ax.set_ylabel("Im(λ) / rad/s")
            ax.set_title(f"SMIB 小扰动特征值分布：{result.config_label}（{status}）")
            ax.grid(True, alpha=0.35)
            self.smib_fig.tight_layout()
            self.smib_canvas.draw()


        except Exception as exc:
            messagebox.showerror("计算错误", str(exc))

    def calculate_frequency(self) -> None:
        try:
            f0 = _safe_float(self.freq_f0.get(), "额定频率 f0")
            delta_p = _safe_float(self.freq_dp.get(), "功率缺额 ΔP_OL0")
            Ts = _safe_float(self.freq_ts.get(), "T_s")
            TG = _safe_float(self.freq_tg.get(), "T_G")
            kD = _safe_float(self.freq_kd.get(), "k_D")
            kG = _safe_float(self.freq_kg.get(), "k_G")
            t_end = _safe_float(self.freq_tend.get(), "绘图时长")
            _validate_positive("绘图时长", t_end)
            agc_on = bool(self.enable_agc.get())

            summary = frequency_response_summary(delta_p, Ts, TG, kD, kG, f0)

            t = np.linspace(0.0, t_end, max(1400, int(8 * t_end)))
            y2 = frequency_response_value(t, delta_p, Ts, TG, kD, kG)
            ace_f = None
            p2_act = None
            if agc_on:
                beta_mw_hz = _safe_float(self.freq_beta.get(), "B")
                kp_agc = _safe_float(self.freq_kp_agc.get(), "Kp")
                ki_agc = _safe_float(self.freq_ki_agc.get(), "Ki")
                t_ace = _safe_float(self.freq_tace.get(), "Tace")
                t_cmd = _safe_float(self.freq_tcmd.get(), "Tcmd")
                p2max = _safe_float(self.freq_p2max.get(), "P2max")
                deadband_hz = _safe_float(self.freq_deadband.get(), "频率死区")
                _validate_positive("B", beta_mw_hz)
                _validate_nonnegative("Kp", kp_agc)
                _validate_nonnegative("Ki", ki_agc)
                _validate_positive("Tace", t_ace)
                _validate_positive("Tcmd", t_cmd)
                _validate_nonnegative("P2max", p2max)
                _validate_nonnegative("频率死区", deadband_hz)

                dt = float(t[1] - t[0])
                df = 0.0
                pg1 = 0.0
                ace_state = 0.0
                ace_int = 0.0
                p2 = 0.0
                y2_num = np.zeros_like(t)
                ace_f = np.zeros_like(t)
                p2_act = np.zeros_like(t)
                for i, _ti in enumerate(t):
                    df_hz = df * f0
                    df_eff_hz = 0.0 if abs(df_hz) <= deadband_hz else df_hz
                    ace_raw = beta_mw_hz * df_eff_hz
                    dace = (ace_raw - ace_state) / t_ace
                    ace_state += dt * dace
                    ace_int += dt * ace_state
                    p2_cmd = -(kp_agc * ace_state + ki_agc * ace_int)
                    p2_cmd = max(-p2max, min(p2max, p2_cmd))
                    dp2 = (p2_cmd - p2) / t_cmd
                    p2 += dt * dp2

                    dpg1 = (-pg1 - kG * df) / TG
                    pg1 += dt * dpg1
                    ddf = (-delta_p + pg1 + p2 - kD * df) / Ts
                    df += dt * ddf

                    y2_num[i] = df
                    ace_f[i] = ace_state
                    p2_act[i] = p2
                y2 = y2_num

            f2 = f0 * (1.0 + y2)

            self.freq_ax.clear()
            main_label = "含二次调频（AGC）" if agc_on else "含一次调频二阶模型"
            self.freq_ax.plot(t, f2, label=main_label, linewidth=2.0, color=("#005f73" if agc_on else None))
            if self.show_first_order.get():
                y1 = first_order_frequency_response_value(t, delta_p, Ts, kD)
                f1 = f0 * (1.0 + y1)
                self.freq_ax.plot(t, f1, "--", label="无一次调频一阶对照", linewidth=1.7)

            self.freq_ax.axhline(
                y=f0 * (1.0 + summary.steady_pu),
                linestyle=":",
                linewidth=1.2,
                label="二阶模型稳态频率"
            )

            if summary.nadir_time_s is not None and 0.0 <= summary.nadir_time_s <= t_end + 1e-9:
                self.freq_ax.scatter(
                    [summary.nadir_time_s],
                    [summary.f_min_hz],
                    s=40,
                    label=f"最低点 ({summary.nadir_time_s:.3f} s)"
                )

            self.freq_ax.set_xlabel("t / s")
            self.freq_ax.set_ylabel("f / Hz")
            self.freq_ax.set_title(f"频率响应曲线（{summary.regime}）")
            self.freq_ax.grid(True)
            self.freq_ax.legend(loc="best")
            self.freq_fig.tight_layout()
            self.freq_canvas.draw()

            text = (
                f"阻尼类型：{summary.regime}\n"
                f"α = {summary.alpha:.6f} 1/s\n"
                f"Ω = {summary.omega_d:.6f} rad/s\n" if summary.omega_d is not None else
                f"阻尼类型：{summary.regime}\n"
                f"α = {summary.alpha:.6f} 1/s\n"
            )

            text += (
                f"初始频率变化率 RoCoF = {summary.rocof_pu_s:.6f} pu/s = {summary.rocof_hz_s:.6f} Hz/s\n"
                f"稳态频差 Δf∞ = {summary.steady_pu:.6f} pu = {summary.steady_hz:.6f} Hz\n"
            )

            if summary.nadir_time_s is not None:
                text += (
                    f"频率最低点时刻 t_m = {summary.nadir_time_s:.6f} s\n"
                    f"最低频差 Δf_min = {summary.nadir_pu:.6f} pu = {summary.nadir_hz:.6f} Hz\n"
                    f"最低频率 f_min = {summary.f_min_hz:.6f} Hz\n"
                )
            else:
                text += (
                    "该参数组合不产生典型欠阻尼最低点。\n"
                    f"单调极限（稳态）Δf∞ = {summary.steady_pu:.6f} pu，"
                    f"对应频率 {f0 * (1.0 + summary.steady_pu):.6f} Hz\n"
                )

            text += "\n说明：\n" + summary.notes
            if agc_on and ace_f is not None and p2_act is not None:
                text += (
                    "\n\n══ 二次调频（AGC-FFC）附加结果 ═════════════\n"
                    f"仿真末端频差 = {y2[-1]:+.6f} pu ({y2[-1] * f0:+.4f} Hz)\n"
                    f"末端滤波ACE = {ace_f[-1]:+.6f}\n"
                    f"末端二次调频出力 P2 = {p2_act[-1]:+.6f} pu\n"
                    "ACE按定频率控制（FFC）仅考虑频偏项，主站指令到机组执行采用一阶滞后。"
                )
            self._set_text(self.freq_result, text)

        except Exception as exc:
            messagebox.showerror("计算错误", str(exc))

    def calculate_oscillation(self) -> None:
        try:
            Eq = _safe_float(self.osc_eq.get(), "E'_q")
            U = _safe_float(self.osc_u.get(), "U")
            X = _safe_float(self.osc_x.get(), "X_Σ")
            P0 = _safe_float(self.osc_p0.get(), "P0")
            Tj = _safe_float(self.osc_tj.get(), "T_j")
            f0 = _safe_float(self.osc_f0.get(), "f0")

            summary = electromechanical_frequency(Eq, U, X, P0, Tj, f0)

            text = (
                f"初始功角 δ0 = {summary.delta0_deg:.6f} °\n"
                f"同步转矩系数 K_s = {summary.Ks:.6f} pu/rad（按本文近似定义）\n"
                f"固有角频率 ω_n = {summary.omega_n:.6f} rad/s\n"
                f"机电振荡频率 f_n = {summary.f_n:.6f} Hz\n\n"
                f"说明：\n{summary.notes}"
            )
            self._set_text(self.osc_result, text)

        except Exception as exc:
            messagebox.showerror("计算错误", str(exc))

    def calculate_voltage(self) -> None:
        try:
            Ug = _safe_float(self.volt_ug.get(), "U_g")
            X = _safe_float(self.volt_x.get(), "X_Σ")
            cos_phi = _safe_float(self.volt_pf.get(), "cosφ")
            s_base_text = self.volt_sbase.get().strip()
            s_base = _safe_float(s_base_text, "S_base") if s_base_text else None

            summary = static_voltage_stability(Ug, X, cos_phi, s_base)

            text = (
                f"sinφ = {summary.sin_phi:.6f}\n"
                f"最大可送有功 P_L,max = {summary.Pmax_pu:.6f} pu\n"
            )
            if summary.Pmax_MW is not None:
                text += f"折算有名值 = {summary.Pmax_MW:.6f} MW\n"
            text += (
                f"受端最低电压（相对送端电压归一化）V_min/U_g = {summary.Vmin_norm_to_sending:.6f} pu\n"
                f"受端最低电压（与 U_g 同一基准）V_min = {summary.Vmin_same_base_as_Ug:.6f} pu\n\n"
                f"说明：\n{summary.notes}"
            )
            self._set_text(self.volt_result, text)

        except Exception as exc:
            messagebox.showerror("计算错误", str(exc))

    def calculate_line(self) -> None:
        try:
            U = _safe_float(self.line_u.get(), "U")
            zc_text = self.line_zc.get().strip()
            zc = _safe_float(zc_text, "Z_c") if zc_text else None

            l_text = self.line_l.get().strip()
            c_text = self.line_c.get().strip()
            L = _safe_float(l_text, "L") if l_text else None
            C = _safe_float(c_text, "C") if c_text else None

            P = _safe_float(self.line_p.get(), "P")
            QN = _safe_float(self.line_qn.get(), "Q_N")
            length = _safe_float(self.line_len.get(), "l")

            summary = natural_power_and_reactive(U, zc, L, C, P, QN, length)

            text = (
                f"波阻抗 Z_c = {summary.Zc_ohm:.6f} Ω\n"
                f"自然功率 P_N = {summary.Pn_MW:.6f} MW\n"
                f"线路无功估算 ΔQ_L = {summary.delta_Q_Mvar:.6f} Mvar\n"
                f"运行区间判断：{summary.line_state}\n\n"
                f"说明：\n{summary.notes}"
            )
            self._set_text(self.line_result, text)

        except Exception as exc:
            messagebox.showerror("计算错误", str(exc))

    def calculate_avc_strategy(self) -> None:
        """Apply the simplified nine-zone AVC policy and report tap/reactive-compensation recommendations together with the adjusted result. / 按简化 9 区策略给出档位与无功补偿调控建议及调后结果。"""
        try:
            hv_base = _safe_float(self.avc_hv_kv.get(), "高压额定电压")
            lv_base = _safe_float(self.avc_lv_kv.get(), "低压额定电压")
            vh = _safe_float(self.avc_vh.get(), "高压侧电压")
            lv_min = _safe_float(self.avc_lv_min.get(), "低压侧下限")
            lv_max = _safe_float(self.avc_lv_max.get(), "低压侧上限")
            tap_min = int(round(_safe_float(self.avc_tap_min.get(), "最小档位")))
            tap_max = int(round(_safe_float(self.avc_tap_max.get(), "最大档位")))
            tap_now = int(round(_safe_float(self.avc_tap_now.get(), "当前档位")))
            tap_step_pct = _safe_float(self.avc_tap_step.get(), "单档调节率")
            cap_num = max(0, int(round(_safe_float(self.avc_cap_num.get(), "电容器组数量"))))
            cap_each = max(0.0, _safe_float(self.avc_cap_each.get(), "每组电容容量"))
            rea_num = max(0, int(round(_safe_float(self.avc_rea_num.get(), "电抗器组数量"))))
            rea_each = max(0.0, _safe_float(self.avc_rea_each.get(), "每组电抗容量"))
            p_mw = _safe_float(self.avc_p.get(), "有功潮流")
            q_mvar = _safe_float(self.avc_q.get(), "无功潮流")
            sys_sc_mva = _safe_float(self.avc_sys_sc_mva.get(), "高压侧系统容量")
            tx_mva = _safe_float(self.avc_tx_mva.get(), "变压器容量")
            tx_uk_pct = _safe_float(self.avc_tx_uk_pct.get(), "变压器短路电压")
            result = simulate_avc_strategy(
                hv_base=hv_base,
                lv_base=lv_base,
                vh=vh,
                lv_min=lv_min,
                lv_max=lv_max,
                tap_min=tap_min,
                tap_max=tap_max,
                tap_now=tap_now,
                tap_step_pct=tap_step_pct,
                cap_num=cap_num,
                cap_each=cap_each,
                rea_num=rea_num,
                rea_each=rea_each,
                p_mw=p_mw,
                q_mvar=q_mvar,
                sys_sc_mva=sys_sc_mva,
                tx_mva=tx_mva,
                tx_uk_pct=tx_uk_pct,
            )
            result_text = (
                f"══ AVC 9区策略模拟结果 ═══════════════════════\n"
                f"当前分区：{result.zone_name}\n"
                f"电压判据：{result.v_zone}（估算低压侧 Vlv={result.lv_est_kv:.3f} kV，限值[{lv_min:.3f}, {lv_max:.3f}]）\n"
                f"无功判据：{result.q_zone}（Q={result.q_now_mvar:.3f} Mvar，阈值±{result.q_abs_ref:.3f} Mvar）\n\n"
                f"建议策略：\n  - " + "\n  - ".join(result.action_steps) + "\n\n"
                f"调控后估算：\n"
                f"  档位 {result.tap_now} → {result.tap_target}\n"
                f"  无功 {result.q_now_mvar:.3f} → {result.q_after_mvar:.3f} Mvar\n"
                f"  低压侧电压 {result.lv_est_kv:.3f} → {result.lv_after_kv:.3f} kV\n"
                f"  无功补偿总动作量 = {result.q_comp_mvar:+.3f} Mvar\n"
                f"\n相对准确潮流计算（当前 / 动作后）：\n"
                f"  等值电抗 Xsys={result.x_sys_pu:.4f} pu，Xtx={result.x_tx_pu:.4f} pu，XΣ={result.x_total_pu:.4f} pu\n"
                f"  支路电流 |I| = {result.i_now_pu:.4f} → {result.i_after_pu:.4f} pu\n"
                f"  高压侧注入有功 P = {result.p_src_now_mw:.3f} → {result.p_src_after_mw:.3f} MW\n"
                f"  高压侧注入无功 Q = {result.q_src_now_mvar:.3f} → {result.q_src_after_mvar:.3f} Mvar\n"
                f"  串联电抗附加无功压降 = {result.q_drop_now_mvar:.3f} → {result.q_drop_after_mvar:.3f} Mvar\n"
            )
            self._set_text(self.avc_result, result_text)
        except Exception as exc:
            messagebox.showerror("计算错误", str(exc))

    def calculate_impact(self) -> None:
        try:
            delta_p = _safe_float(self.imp_dp.get(), "ΔPa")
            delta_t = _safe_float(self.imp_dt.get(), "Δt")
            f_d     = _safe_float(self.imp_fd.get(), "f_d")

            summary = impact_method(delta_p, delta_t, f_d)

            text = (
                f"══ 冲击法：功率振荡幅度快估 ═════════════\n"
                f"冲击量 Dp = {summary.Dp_pu:.6f} pu\n"
                f"估算第一摆功率振荡幅值 ΔP_osc ≈ {summary.osc_amp_pu:.6f} pu\n"
                f"\n说明：\n{summary.notes}"
            )

            self._set_text(self.imp_result, text)

        except Exception as exc:
            messagebox.showerror("计算错误", str(exc))

    def calculate_eac(self) -> None:
        try:
            Pm        = _safe_float(self.eac_pm.get(),    "Pm")
            Pmax_pre  = _safe_float(self.eac_ppre.get(),  "Pmax_pre")
            Pmax_f    = _safe_float(self.eac_pf.get(),    "Pmax_fault")
            Pmax_post = _safe_float(self.eac_ppost.get(), "Pmax_post")
            dt        = _safe_float(self.eac_dt.get(),    "Δt")
            Tj        = _safe_float(self.eac_tj.get(),    "Tj")
            f0        = _safe_float(self.eac_f0.get(),    "f0")

            r = equal_area_criterion(Pm, Pmax_pre, Pmax_f, Pmax_post, dt, Tj, f0)

            # Result text / 结果文字 ────────────────────────────────────────────────
            stab_str = "[稳定]" if r.stable else "[失稳]（加速面积 > 可用减速面积）"
            text = (
                f"稳定性判断：{stab_str}\n"
                f"裕度 = {r.margin_pct:+.2f} %\n"
                f"\n── 关键角度 ──────────────────────\n"
                f"故障前平衡角 δ0  = {r.delta0_deg:.3f}°\n"
                f"故障切除角   δc  = {r.deltac_deg:.3f}°\n"
                f"不稳定平衡角 δu  = {r.deltau_deg:.3f}°\n"
            )
            if r.deltamax_deg is not None:
                text += f"实际最大摆角 δmax= {r.deltamax_deg:.3f}°\n"
            text += (
                f"\n── 等面积 ────────────────────────\n"
                f"加速面积  Aacc       = {r.A_acc:.6f} pu·rad\n"
                f"可用减速面积 Adec    = {r.A_dec_avail:.6f} pu·rad\n"
            )
            if r.A_dec_actual is not None:
                text += f"实际减速面积 Adec_act= {r.A_dec_actual:.6f} pu·rad\n"
            text += (
                f"\n── 极限切除 ──────────────────────\n"
                f"极限切除角 δcr = {r.delta_cr_deg:.3f}°\n"
                f"极限切除时间 tcr = {r.t_cr_s:.4f} s\n"
                f"当前切除时间 Δt  = {dt:.4f} s  "
                f"({'< tcr OK' if dt < r.t_cr_s else '>= tcr NG'})\n"
                f"\n说明：\n{r.notes}"
            )
            self._set_text(self.eac_result, text)

            # P-δ plot / P-δ 图 ──────────────────────────────────────────────────
            ax = self.eac_ax
            ax.clear()

            delta_deg = np.linspace(0, 200, 1000)
            delta_rad = np.radians(delta_deg)

            Pe_pre   = Pmax_pre  * np.sin(delta_rad)
            Pe_fault = Pmax_f    * np.sin(delta_rad)
            Pe_post  = Pmax_post * np.sin(delta_rad)

            ax.plot(delta_deg, Pe_pre,   "b-",  linewidth=1.8,
                    label=f"故障前  Pmax={Pmax_pre:.3f} pu")
            fault_lbl = (f"故障中  Pmax={Pmax_f:.3f} pu"
                         + ("（三相短路≈0）" if Pmax_f < 1e-9 else ""))
            ax.plot(delta_deg, Pe_fault, "r--", linewidth=1.5, label=fault_lbl)
            ax.plot(delta_deg, Pe_post,  "g-",  linewidth=1.8,
                    label=f"故障后  Pmax={Pmax_post:.3f} pu")
            ax.axhline(Pm, color="k", linewidth=1.4, linestyle=":",
                       label=f"Pm = {Pm:.3f} pu")

            # Acceleration area (red fill) from δ0 to δc, using the faulted sine curve. / 加速面积（红色填充）δ0 → δc，曲线为故障中正弦
            d_acc = np.linspace(r.delta0_rad, r.deltac_rad, 500)
            Pe_f_acc = Pmax_f * np.sin(d_acc)
            # Positive acceleration (Pm > Pe_fault) is red; negative acceleration (Pe_fault > Pm) is blue-violet. / 正加速（Pm > Pe_fault）→ 红色；负加速（Pe_fault > Pm）→ 蓝紫色
            ax.fill_between(np.degrees(d_acc), Pm, Pe_f_acc,
                            where=(Pm >= Pe_f_acc),
                            color="tomato", alpha=0.45,
                            label=f"加速面积（+）{r.A_acc:.4f} pu·rad")
            if np.any(Pe_f_acc > Pm):
                neg_area = float(
                    np.trapz(np.maximum(0, Pe_f_acc - Pm), d_acc))
                ax.fill_between(np.degrees(d_acc), Pe_f_acc, Pm,
                                where=(Pe_f_acc > Pm),
                                color="mediumpurple", alpha=0.40,
                                label=f"减速（故障中）{neg_area:.4f} pu·rad")

            # Deceleration area (green fill) from δc to δmax (or δu). / 减速面积（绿色填充）δc → δmax（或 δu）
            d_end = r.deltamax_rad if r.deltamax_rad is not None else r.deltau_rad
            d_dec = np.linspace(r.deltac_rad, d_end, 500)
            Pe_post_dec = Pmax_post * np.sin(d_dec)
            ax.fill_between(np.degrees(d_dec),
                            Pe_post_dec, Pm,
                            where=(Pe_post_dec >= Pm),
                            color="limegreen", alpha=0.45,
                            label=f"减速面积 {r.A_dec_avail:.4f} pu·rad")

            # Key-angle annotations. / 关键角度标注
            def _vline(deg: float, color: str, ls: str, label: str) -> None:
                ax.axvline(deg, color=color, linestyle=ls, linewidth=1.2, label=label)

            _vline(r.delta0_deg,  "blue",  "-.",  f"δ0={r.delta0_deg:.1f}°")
            _vline(r.deltac_deg,  "red",   "--",  f"δc={r.deltac_deg:.1f}°")
            _vline(r.deltau_deg,  "green", "-.",  f"δu={r.deltau_deg:.1f}°")
            _vline(r.delta_cr_deg,"purple",":",   f"δcr={r.delta_cr_deg:.1f}°")
            if r.deltamax_deg is not None:
                _vline(r.deltamax_deg, "darkorange", "--",
                       f"δmax={r.deltamax_deg:.1f}°")

            ax.set_xlabel("δ / °")
            ax.set_ylabel("P / pu")
            title_flag = "[稳定]" if r.stable else "[失稳]"
            ax.set_title(
                f"功角曲线  {title_flag}  裕度 {r.margin_pct:+.1f}%  "
                f"tcr={r.t_cr_s:.3f} s"
            )
            ax.set_xlim(0, 200)
            ymax = max(Pmax_pre, Pmax_post, Pm) * 1.18
            ax.set_ylim(-0.08, ymax)
            ax.legend(loc="upper right", fontsize=7.5, ncol=2)
            ax.grid(True, alpha=0.4)
            self.eac_fig.tight_layout()
            self.eac_canvas.draw()

        except Exception as exc:
            messagebox.showerror("计算错误", str(exc))
