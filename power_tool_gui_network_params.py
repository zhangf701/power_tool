"""Short-circuit, parameter, sag, and line-geometry GUI mixin. / 短路、参数、导线弧垂和线路几何页面 mixin。"""

from __future__ import annotations

from power_tool_gui_common import *


class NetworkAndParameterGuiMixin:
    def _build_short_circuit_tab(self) -> None:
        self._sc_ui_ready = False
        self._sc_neutral_auto_values: dict[str, float] = {}
        self._sc_neutral_manual_flags = {
            "left_rn": False,
            "left_xn": False,
            "right_rn": False,
            "right_xn": False,
        }

        self.sc_tab.columnconfigure(0, weight=1)
        self.sc_tab.rowconfigure(0, weight=1)

        shell = ttk.Frame(self.sc_tab, padding=8, style="Surface.TFrame")
        shell.grid(row=0, column=0, sticky="nsew")
        shell.columnconfigure(0, weight=0, minsize=620)
        shell.columnconfigure(1, weight=1)
        shell.rowconfigure(0, weight=1)

        left_outer, left, _left_canvas = self._create_scrollable_card(shell, padding=16)
        left_outer.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        right = ttk.Frame(shell, padding=16, style="Card.TFrame")
        right.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        right.columnconfigure(0, weight=1)
        right.rowconfigure(3, weight=1)
        left.columnconfigure(0, weight=1)

        ttk.Label(left, text="短路电流计算", style="PageTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            left,
            text="页面按“系统与故障—线路参数—中性点与开断校核—显示设置”重构；左侧改为滚动表单，右侧增加关键指标摘要与更明亮的向量图。",
            style="Muted.TLabel", justify="left", wraplength=470,
        ).grid(row=1, column=0, sticky="ew", pady=(4, 10))

        basic = ttk.LabelFrame(left, text="系统与故障设定", style="Card.TLabelframe", padding=10)
        basic.grid(row=2, column=0, sticky="ew")
        basic.columnconfigure(1, weight=1, minsize=112)
        basic.columnconfigure(3, weight=1, minsize=112)

        ttk.Label(basic, text="网络模式", style="Form.TLabel").grid(row=0, column=0, sticky="w", padx=4, pady=4)
        self.sc_mode = ttk.Combobox(basic, state="readonly", width=22, style="Input.TCombobox", values=["单电源", "双电源"])
        self.sc_mode.grid(row=0, column=1, sticky="ew", padx=4, pady=4)
        self.sc_mode.set(_display_obj(self, "单电源"))

        ttk.Label(basic, text="故障类型", style="Form.TLabel").grid(row=0, column=2, sticky="w", padx=4, pady=4)
        self.sc_fault_type = ttk.Combobox(
            basic,
            state="readonly",
            width=22,
            style="Input.TCombobox",
            values=["A相接地", "B相接地", "C相接地", "AB两相接地", "BC两相接地", "CA两相接地", "AB两相短路", "BC两相短路", "CA两相短路", "三相接地"],
        )
        self.sc_fault_type.grid(row=0, column=3, sticky="ew", padx=4, pady=4)
        self.sc_fault_type.set(_display_obj(self, "A相接地"))

        self.sc_u = self._add_entry(basic, 1, "系统电压 U / kV（线电压）", "110", column=0)
        self.sc_fault_pos = self._add_entry(basic, 1, "故障点距左侧百分比 / %", "50", column=2)
        self.sc_ssc = self._add_entry(basic, 2, "左侧系统短路容量 S_sc / MVA", "2000", column=0)
        self.sc_xr = self._add_entry(basic, 2, "左侧系统 X/R 比", "10", column=2)
        self.sc_ssc_r = self._add_entry(basic, 3, "右侧系统短路容量 S_sc,R / MVA", "2000", column=0)
        self.sc_xr_r = self._add_entry(basic, 3, "右侧系统 X/R 比", "10", column=2)
        self.sc_e_left = self._add_entry(basic, 4, "左侧预故障电势 E_L / pu", "1.00", column=0)
        self.sc_delta_left = self._add_entry(basic, 4, "左侧预故障相角 δL / °", "0.0", column=2)
        self.sc_e_right = self._add_entry(basic, 5, "右侧预故障电势 E_R / pu", "1.00", column=0)
        self.sc_delta_right = self._add_entry(basic, 5, "右侧预故障相角 δR / °", "0.0", column=2)

        line = ttk.LabelFrame(left, text="线路与序参数", style="Card.TLabelframe", padding=10)
        line.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        line.columnconfigure(1, weight=1, minsize=112)
        line.columnconfigure(3, weight=1, minsize=112)
        self.sc_len = self._add_entry(line, 0, "线路长度 / km", "30", column=0)
        self.sc_rf = self._add_entry(line, 0, "过渡电阻 Rf / Ω", "0.0", column=2)
        self.sc_r1 = self._add_entry(line, 1, "线路正序电阻 R1 / (Ω/km)", "0.05", column=0)
        self.sc_x1 = self._add_entry(line, 1, "线路正序电抗 X1 / (Ω/km)", "0.40", column=2)
        self.sc_r0 = self._add_entry(line, 2, "线路零序电阻 R0 / (Ω/km)", "0.15", column=0)
        self.sc_x0 = self._add_entry(line, 2, "线路零序电抗 X0 / (Ω/km)", "1.20", column=2)
        ttk.Label(line, text="零序参数变化会联动刷新默认中性点参数；若已手工改写，则不会被再次覆盖。",
                  style="Muted.TLabel", justify="left", wraplength=450).grid(
            row=3, column=0, columnspan=4, sticky="w", padx=4, pady=(6, 0)
        )

        neutral = ttk.LabelFrame(left, text="中性点与开断校核", style="Card.TLabelframe", padding=10)
        neutral.grid(row=4, column=0, sticky="ew", pady=(10, 0))
        neutral.columnconfigure(1, weight=1, minsize=112)
        neutral.columnconfigure(3, weight=1, minsize=112)

        ttk.Label(neutral, text="左侧中性点方式", style="Form.TLabel").grid(row=0, column=0, sticky="w", padx=4, pady=4)
        self.sc_neutral_mode = ttk.Combobox(neutral, state="readonly", width=22, style="Input.TCombobox",
                                            values=["直接接地", "中性点不接地", "经消弧线圈接地", "经电阻接地"])
        self.sc_neutral_mode.grid(row=0, column=1, sticky="ew", padx=4, pady=4)
        self.sc_neutral_mode.set(_display_obj(self, "直接接地"))
        ttk.Label(neutral, text="右侧中性点方式", style="Form.TLabel").grid(row=0, column=2, sticky="w", padx=4, pady=4)
        self.sc_neutral_mode_r = ttk.Combobox(neutral, state="readonly", width=22, style="Input.TCombobox",
                                              values=["直接接地", "中性点不接地", "经消弧线圈接地", "经电阻接地"])
        self.sc_neutral_mode_r.grid(row=0, column=3, sticky="ew", padx=4, pady=4)
        self.sc_neutral_mode_r.set(_display_obj(self, "直接接地"))

        self.sc_rn = self._add_entry(neutral, 1, "左侧中性点电阻 Rn,L / Ω", "1.5", column=0)
        self.sc_xn = self._add_entry(neutral, 1, "左侧中性点电抗 Xn,L / Ω", "12.0", column=2)
        self.sc_rn_r = self._add_entry(neutral, 2, "右侧中性点电阻 Rn,R / Ω", "1.5", column=0)
        self.sc_xn_r = self._add_entry(neutral, 2, "右侧中性点电抗 Xn,R / Ω", "12.0", column=2)
        self.sc_brk = self._add_entry(neutral, 3, "断路器额定开断电流 Ik / kA（可留空）", "31.5", column=0)
        self.sc_cycles = self._add_entry(neutral, 3, "仿真周波数（波形）", "10", column=2)

        display = ttk.LabelFrame(left, text="显示与交互", style="Card.TLabelframe", padding=10)
        display.grid(row=5, column=0, sticky="ew", pady=(10, 0))
        display.columnconfigure(0, weight=1)
        self.sc_vector_labels_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(display, text="向量图显示数值标签", variable=self.sc_vector_labels_var,
                        command=self.calculate_short_circuit, style="Card.TCheckbutton").grid(
            row=0, column=0, sticky="w", padx=4, pady=(0, 4)
        )
        ttk.Label(display, text="故障点位置滑条（双电源）", style="Form.TLabel").grid(row=1, column=0, sticky="w", padx=4, pady=(2, 2))
        self.sc_fault_slider = ttk.Scale(display, from_=0.0, to=100.0, orient=tk.HORIZONTAL,
                                         command=self._on_sc_fault_slider, style="Accent.Horizontal.TScale")
        self.sc_fault_slider.grid(row=2, column=0, sticky="ew", padx=4, pady=(0, 4))
        ttk.Label(display, text="单电源模式自动锁定在 100%，双电源模式可拖动定位故障点。",
                  style="Muted.TLabel", justify="left", wraplength=450).grid(
            row=3, column=0, sticky="w", padx=4, pady=(0, 6)
        )
        ttk.Button(display, text="计算并绘图", command=self.calculate_short_circuit, style="Accent.TButton").grid(
            row=4, column=0, sticky="ew", padx=4, pady=(2, 0)
        )

        ttk.Label(left, text="详细结果", style="SectionTitle.TLabel").grid(row=6, column=0, sticky="w", pady=(12, 4))
        self.sc_result = ScrolledText(left, width=58, height=18, wrap=tk.WORD)
        self.sc_result.grid(row=7, column=0, sticky="ew")
        self.sc_result.configure(state="disabled")

        for entry, key in (
            (self.sc_rn, "left_rn"),
            (self.sc_xn, "left_xn"),
            (self.sc_rn_r, "right_rn"),
            (self.sc_xn_r, "right_xn"),
        ):
            entry.bind("<KeyRelease>", lambda _e, field_key=key: self._mark_sc_neutral_manual(field_key))

        self.sc_mode.bind("<<ComboboxSelected>>", self._on_sc_mode_change)
        self.sc_fault_type.bind("<<ComboboxSelected>>", lambda _e: self.calculate_short_circuit())
        self.sc_neutral_mode.bind("<<ComboboxSelected>>", self._on_sc_neutral_mode_change)
        self.sc_neutral_mode_r.bind("<<ComboboxSelected>>", self._on_sc_neutral_mode_change)
        self.sc_len.bind("<FocusOut>", self._on_sc_neutral_mode_change)
        self.sc_r0.bind("<FocusOut>", self._on_sc_neutral_mode_change)
        self.sc_x0.bind("<FocusOut>", self._on_sc_neutral_mode_change)

        ttk.Label(right, text="故障点波形与向量图", style="PageTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            right,
            text="右侧结果区增加关键指标摘要，并将原有极坐标向量图改为浅底高对比版本，使表格、波形与相量关系更容易同时辨认。",
            style="Muted.TLabel", justify="left", wraplength=880,
        ).grid(row=1, column=0, sticky="ew", pady=(4, 10))

        summary = ttk.Frame(right, style="Card.TFrame")
        summary.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        for col in range(4):
            summary.columnconfigure(col, weight=1)
        self.sc_summary_fault_var = tk.StringVar(value="—")
        self.sc_summary_peak_var = tk.StringVar(value="—")
        self.sc_summary_break_var = tk.StringVar(value="—")
        self.sc_summary_tau_var = tk.StringVar(value="—")
        for col, (title, var) in enumerate((
            ("故障模式", self.sc_summary_fault_var),
            ("最大相电流", self.sc_summary_peak_var),
            ("开断校核电流", self.sc_summary_break_var),
            ("直流时间常数", self.sc_summary_tau_var),
        )):
            card = ttk.Frame(summary, style="Metric.TFrame", padding=10)
            card.grid(row=0, column=col, sticky="nsew", padx=(0 if col == 0 else 6, 0))
            ttk.Label(card, text=title, style="MetricTitle.TLabel").pack(anchor="w")
            ttk.Label(card, textvariable=var, style="MetricValue.TLabel").pack(anchor="w", pady=(6, 0))

        self.sc_plot_notebook = ttk.Notebook(right)
        self.sc_plot_notebook.grid(row=3, column=0, sticky="nsew")
        self.sc_plot_current_tab = ttk.Frame(self.sc_plot_notebook, style="Card.TFrame")
        self.sc_plot_voltage_tab = ttk.Frame(self.sc_plot_notebook, style="Card.TFrame")
        self.sc_plot_notebook.add(self.sc_plot_current_tab, text="电流与向量图")
        self.sc_plot_notebook.add(self.sc_plot_voltage_tab, text="电压与向量图")
        self.sc_plot_current_tab.columnconfigure(0, weight=1)
        self.sc_plot_current_tab.rowconfigure(0, weight=1)
        self.sc_plot_voltage_tab.columnconfigure(0, weight=1)
        self.sc_plot_voltage_tab.rowconfigure(0, weight=1)

        self.sc_fig = Figure(figsize=(10.8, 7.0), dpi=100)
        gs = self.sc_fig.add_gridspec(2, 2, hspace=0.30, wspace=0.24)
        self.sc_ax_phase = self.sc_fig.add_subplot(gs[0, 0])
        self.sc_ax_seq = self.sc_fig.add_subplot(gs[1, 0])
        self.sc_ax_i_table = self.sc_fig.add_subplot(gs[0, 1])
        self.sc_ax_i_vector = self.sc_fig.add_subplot(gs[1, 1], projection="polar")
        self.sc_ax_phase.set_ylabel("i_abc / A")
        self.sc_ax_seq.set_ylabel("i_012 / A")
        self.sc_ax_seq.set_xlabel("t / s")
        self.sc_ax_phase.grid(True, alpha=0.45)
        self.sc_ax_seq.grid(True, alpha=0.45)
        self._draw_short_circuit_vector_axis(self.sc_ax_i_vector, {}, "故障点电流向量图", table_ax=self.sc_ax_i_table)

        self.sc_canvas = FigureCanvasTkAgg(self.sc_fig, master=self.sc_plot_current_tab)
        self.sc_canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        self.sc_toolbar = NavigationToolbar2Tk(self.sc_canvas, self.sc_plot_current_tab, pack_toolbar=False)
        self.sc_toolbar.update()
        self.sc_toolbar.grid(row=1, column=0, sticky="ew")

        self.sc_v_fig = Figure(figsize=(10.8, 7.0), dpi=100)
        gs_v = self.sc_v_fig.add_gridspec(2, 2, hspace=0.30, wspace=0.24)
        self.sc_v_ax_phase = self.sc_v_fig.add_subplot(gs_v[0, 0])
        self.sc_v_ax_seq = self.sc_v_fig.add_subplot(gs_v[1, 0])
        self.sc_v_ax_table = self.sc_v_fig.add_subplot(gs_v[0, 1])
        self.sc_v_ax_vector = self.sc_v_fig.add_subplot(gs_v[1, 1], projection="polar")
        self.sc_v_ax_phase.set_ylabel("u_abc / V")
        self.sc_v_ax_seq.set_ylabel("u_012 / V")
        self.sc_v_ax_seq.set_xlabel("t / s")
        self.sc_v_ax_phase.grid(True, alpha=0.45)
        self.sc_v_ax_seq.grid(True, alpha=0.45)
        self._draw_short_circuit_vector_axis(self.sc_v_ax_vector, {}, "故障点电压向量图", table_ax=self.sc_v_ax_table)
        self.sc_v_canvas = FigureCanvasTkAgg(self.sc_v_fig, master=self.sc_plot_voltage_tab)
        self.sc_v_canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        self.sc_v_toolbar = NavigationToolbar2Tk(self.sc_v_canvas, self.sc_plot_voltage_tab, pack_toolbar=False)
        self.sc_v_toolbar.update()
        self.sc_v_toolbar.grid(row=1, column=0, sticky="ew")

        self.sc_fault_slider.set(50.0)
        self._on_sc_neutral_mode_change()
        self._on_sc_mode_change()
        self._sc_ui_ready = True
        self.calculate_short_circuit()

    def _mark_sc_neutral_manual(self, key: str) -> None:
        entry_map = {
            "left_rn": self.sc_rn,
            "left_xn": self.sc_xn,
            "right_rn": self.sc_rn_r,
            "right_xn": self.sc_xn_r,
        }
        entry = entry_map[key]
        auto = self._sc_neutral_auto_values.get(key)
        self._sc_neutral_manual_flags[key] = not self._sc_entry_matches_auto(entry.get().strip(), auto)

    @staticmethod
    def _sc_entry_matches_auto(value: str, auto_value: float | None) -> bool:
        if auto_value is None:
            return False
        try:
            return math.isclose(float(value), float(auto_value), rel_tol=1e-6, abs_tol=1e-6)
        except Exception:
            return value.strip() == f"{auto_value:.6g}"

    @staticmethod
    def _set_entry_text(entry: ttk.Entry, text: str) -> None:
        state = str(entry.cget("state"))
        if state == "disabled":
            entry.configure(state="normal")
        entry.delete(0, tk.END)
        entry.insert(0, text)
        if state == "disabled":
            entry.configure(state="disabled")

    def _sync_sc_neutral_entry(self, entry: ttk.Entry, key: str, value: float, *, force: bool = False) -> None:
        previous_auto = self._sc_neutral_auto_values.get(key)
        current = entry.get().strip()
        should_apply = force or (not self._sc_neutral_manual_flags.get(key, False)) or self._sc_entry_matches_auto(current, previous_auto)
        self._sc_neutral_auto_values[key] = value
        if should_apply:
            self._set_entry_text(entry, f"{value:.6g}")
            self._sc_neutral_manual_flags[key] = False

    def _update_sc_neutral_entry_states(self) -> None:
        def _apply(mode_box: ttk.Combobox, rn_entry: ttk.Entry, xn_entry: ttk.Entry, *, enabled: bool) -> None:
            if not enabled:
                rn_entry.configure(state="disabled")
                xn_entry.configure(state="disabled")
                return
            mode = _logic_obj(self, mode_box.get().strip())
            if mode in {"直接接地", "中性点不接地"}:
                rn_entry.configure(state="disabled")
                xn_entry.configure(state="disabled")
            elif mode == "经电阻接地":
                rn_entry.configure(state="normal")
                xn_entry.configure(state="disabled")
            elif mode == "经消弧线圈接地":
                rn_entry.configure(state="disabled")
                xn_entry.configure(state="normal")
            else:
                rn_entry.configure(state="normal")
                xn_entry.configure(state="normal")

        dual_on = _logic_obj(self, self.sc_mode.get().strip()) == "双电源"
        _apply(self.sc_neutral_mode, self.sc_rn, self.sc_xn, enabled=True)
        _apply(self.sc_neutral_mode_r, self.sc_rn_r, self.sc_xn_r, enabled=dual_on)

    def _on_sc_neutral_mode_change(self, _event: object | None = None) -> None:
        """Populate neutral-point defaults whose magnitude matches the line zero-sequence parameters. / 根据线路零序参数给出与量级匹配的中性点参数默认值。"""
        try:
            length = _safe_float(self.sc_len.get(), "线路长度")
            r0 = _safe_float(self.sc_r0.get(), "R0")
            x0 = _safe_float(self.sc_x0.get(), "X0")
            r0_total = max(0.0, r0 * length)
            x0_total = max(0.0, x0 * length)
        except Exception:
            r0_total, x0_total = 4.5, 36.0

        def _defaults(mode: str) -> tuple[float, float]:
            mode = _logic_obj(self, mode)
            if mode == "直接接地":
                return 0.0, 0.0
            if mode == "中性点不接地":
                return 1e9, 0.0
            if mode == "经消弧线圈接地":
                return 0.0, x0_total / 3.0
            if mode == "经电阻接地":
                return r0_total / 3.0, 0.0
            return 0.0, 0.0

        force_left = _event is None or getattr(_event, "widget", None) is self.sc_neutral_mode
        force_right = _event is None or getattr(_event, "widget", None) is self.sc_neutral_mode_r
        rn_l, xn_l = _defaults(self.sc_neutral_mode.get().strip())
        rn_r, xn_r = _defaults(self.sc_neutral_mode_r.get().strip())

        self._sync_sc_neutral_entry(self.sc_rn, "left_rn", rn_l, force=force_left)
        self._sync_sc_neutral_entry(self.sc_xn, "left_xn", xn_l, force=force_left)
        self._sync_sc_neutral_entry(self.sc_rn_r, "right_rn", rn_r, force=force_right)
        self._sync_sc_neutral_entry(self.sc_xn_r, "right_xn", xn_r, force=force_right)
        self._update_sc_neutral_entry_states()

    def _on_sc_fault_slider(self, value: str) -> None:
        if not getattr(self, "_sc_ui_ready", False):
            return
        try:
            v = float(value)
        except Exception:
            return
        self.sc_fault_pos.configure(state="normal")
        self.sc_fault_pos.delete(0, tk.END)
        self.sc_fault_pos.insert(0, f"{v:.2f}")
        if _logic_obj(self, self.sc_mode.get().strip()) != "双电源":
            self.sc_fault_pos.configure(state="disabled")
        self.calculate_short_circuit()

    def _on_sc_mode_change(self, _event: object | None = None) -> None:
        is_dual = _logic_obj(self, self.sc_mode.get().strip()) == "双电源"
        state = "normal" if is_dual else "disabled"
        dual_entries = (
            self.sc_ssc_r, self.sc_xr_r, self.sc_fault_pos,
            self.sc_e_right, self.sc_delta_right,
        )
        for entry in dual_entries:
            entry.configure(state=state)
        self.sc_neutral_mode_r.configure(state="readonly" if is_dual else "disabled")
        self.sc_fault_slider.configure(state=state)
        if not is_dual:
            self.sc_fault_pos.configure(state="normal")
            self._set_entry_text(self.sc_fault_pos, "100")
            self.sc_fault_pos.configure(state="disabled")
            self.sc_fault_slider.set(100.0)
        else:
            self.sc_fault_pos.configure(state="normal")
            self._set_entry_text(self.sc_fault_pos, f"{self.sc_fault_slider.get():.2f}")
        self._update_sc_neutral_entry_states()
        if getattr(self, "_sc_ui_ready", False):
            self.calculate_short_circuit()

    def _draw_short_circuit_vector_axis(
        self,
        ax,
        vectors: dict[str, complex],
        title: str,
        show_labels: bool = True,
        table_ax=None,
    ) -> None:
        p = self._palette
        ax.clear()
        ax.set_theta_zero_location("E")
        ax.set_theta_direction(1)
        ax.set_facecolor("#fbfdff")
        ax.set_title(title, color=p["text"], fontsize=10.8, pad=14, fontweight="bold")
        if table_ax is not None:
            table_ax.clear()
            table_ax.axis("off")
            table_ax.set_facecolor("#fbfdff")
        colors = {
            "A": "#3b82f6", "B": "#d4a017", "C": "#ef5b5b",
            "1": "#22a06b", "2": "#5b6def", "0": "#9b6df2",
        }
        linestyles = {"A": "-", "B": "-", "C": "-", "1": "--", "2": "--", "0": "--"}
        grid_color = "#d9e3ee"
        if not vectors:
            ax.set_ylim(0.0, 1.0)
            ax.grid(color=grid_color, linestyle="-", linewidth=0.9, alpha=0.95)
            ax.set_yticks([0.25, 0.5, 0.75, 1.0])
            ax.set_yticklabels(["0.25", "0.50", "0.75", "1.00"], color=p["muted"], fontsize=8)
            ax.set_thetagrids(np.arange(0, 360, 45), color=p["muted"], fontsize=8.5)
            ax.spines["polar"].set_color(p["border_strong"])
            ax.spines["polar"].set_linewidth(1.0)
            return
        max_mag = max(1e-6, max(abs(v) for v in vectors.values()))
        radial_max = max_mag * 1.15
        ax.set_ylim(0.0, radial_max)
        rings = np.linspace(radial_max / 4.0, radial_max, 4)
        ax.set_yticks(rings)
        ax.set_yticklabels([f"{tick:.3g}" for tick in rings], color=p["muted"], fontsize=8)
        ax.set_thetagrids(np.arange(0, 360, 45), color=p["muted"], fontsize=8.5)
        ax.grid(color=grid_color, linestyle="-", linewidth=0.9, alpha=0.95)
        ax.spines["polar"].set_color(p["border_strong"])
        ax.spines["polar"].set_linewidth(1.0)
        for name, val in vectors.items():
            theta = math.atan2(val.imag, val.real)
            radius = abs(val)
            color = colors.get(name, p["accent"])
            linestyle = linestyles.get(name, "-")
            ax.annotate(
                "",
                xy=(theta, radius),
                xytext=(theta, 0.0),
                arrowprops=dict(arrowstyle="-|>", color=color, linewidth=2.4, linestyle=linestyle, shrinkA=0, shrinkB=0),
            )
            if show_labels:
                ang = math.degrees(theta)
                ax.text(theta, min(radial_max, radius * 1.08), f"{name}\n{radius:.3g}∠{ang:.1f}°",
                        color=color, fontsize=7.0, ha="center", va="center")
        legend_order = [k for k in ("A", "B", "C", "1", "2", "0") if k in vectors]
        if legend_order:
            table_rows = []
            for k in legend_order:
                val = vectors[k]
                angle = math.degrees(math.atan2(val.imag, val.real))
                table_rows.append([
                    k,
                    f"{abs(val):.4g}",
                    f"{angle:+.2f}",
                    f"{val.real:.4g}",
                    f"{val.imag:.4g}",
                ])
            if table_ax is not None:
                table = table_ax.table(
                    cellText=table_rows,
                    colLabels=["名称", "幅值", "相角/°", "实部", "虚部"],
                    loc="center",
                    cellLoc="center",
                )
                table.auto_set_font_size(False)
                table.set_fontsize(8.6)
                table.scale(1.02, 1.16)
                for (row, _col), cell in table.get_celld().items():
                    cell.set_linewidth(0.8)
                    cell.set_edgecolor(p["border_strong"])
                    if row == 0:
                        cell.set_facecolor("#eef4fb")
                        cell.get_text().set_color(p["text"])
                        cell.get_text().set_fontweight("bold")
                    else:
                        cell.set_facecolor("#ffffff")
                        cell.get_text().set_color(p["text"])
            handles = [
                Line2D([0], [0], color=colors[k], linestyle=linestyles[k], linewidth=2.4, label=k)
                for k in legend_order
            ]
            ax.legend(
                handles=handles,
                loc="upper left",
                bbox_to_anchor=(0.02, 1.05),
                ncol=min(3, len(handles)),
                fontsize=7.6,
                framealpha=0.98,
                facecolor="#ffffff",
                edgecolor=p["border_strong"],
                labelcolor=p["text"],
            )

    def calculate_short_circuit(self) -> None:
        try:
            mode = _logic_obj(self, self.sc_mode.get().strip())
            fault_type = _logic_obj(self, self.sc_fault_type.get().strip())
            neutral_mode = _logic_obj(self, self.sc_neutral_mode.get().strip())
            U = _safe_float(self.sc_u.get(), "U")
            Ssc = _safe_float(self.sc_ssc.get(), "S_sc")
            xr = _safe_float(self.sc_xr.get(), "X/R")
            Ssc_r = _safe_float(self.sc_ssc_r.get(), "S_sc,R")
            xr_r = _safe_float(self.sc_xr_r.get(), "X/R,R")
            e_left = _safe_float(self.sc_e_left.get(), "E_L")
            d_left = _safe_float(self.sc_delta_left.get(), "δL")
            e_right = _safe_float(self.sc_e_right.get(), "E_R")
            d_right = _safe_float(self.sc_delta_right.get(), "δR")
            fault_pos_pct = _safe_float(self.sc_fault_pos.get(), "故障点百分比")
            length = _safe_float(self.sc_len.get(), "线路长度")
            R1 = _safe_float(self.sc_r1.get(), "R1")
            X1 = _safe_float(self.sc_x1.get(), "X1")
            R0 = _safe_float(self.sc_r0.get(), "R0")
            X0 = _safe_float(self.sc_x0.get(), "X0")
            Rf = _safe_float(self.sc_rf.get(), "Rf")
            Rn = _safe_float(self.sc_rn.get(), "Rn")
            Xn = _safe_float(self.sc_xn.get(), "Xn")
            neutral_mode_right = _logic_obj(self, self.sc_neutral_mode_r.get().strip())
            Rn_r = _safe_float(self.sc_rn_r.get(), "Rn,R")
            Xn_r = _safe_float(self.sc_xn_r.get(), "Xn,R")
            cycles = max(1.0, _safe_float(self.sc_cycles.get(), "仿真周波数"))
            brk_txt = self.sc_brk.get().strip()
            brk = _safe_float(brk_txt, "Ik") if brk_txt else None

            r = short_circuit_capacity(U, fault_type, Ssc, xr, length, R1, X1, R0, X0,
                                       neutral_mode, Rn, Xn, Rf, brk,
                                       network_mode=mode, s_sc_right_mva=Ssc_r, xr_sys_right=xr_r,
                                       fault_pos_from_left_pct=fault_pos_pct,
                                       e_left_pu=e_left, e_right_pu=e_right,
                                       delta_left_deg=d_left, delta_right_deg=d_right,
                                       neutral_mode_right=neutral_mode_right,
                                       neutral_rn_right_ohm=Rn_r, neutral_xn_right_ohm=Xn_r)

            def _pa(z: complex) -> str:
                return f"{abs(z):.2f}∠{math.degrees(math.atan2(z.imag, z.real)):.1f}°"

            if r.breaker_ok is None:
                check = "未输入断路器开断电流，未做匹配判断。"
            else:
                check = "匹配：额定开断电流 ≥ 计算开断电流。" if r.breaker_ok else "不匹配：额定开断电流 < 计算开断电流。"

            peak_phase_ka = max(abs(r.Ia_A), abs(r.Ib_A), abs(r.Ic_A)) / 1000.0
            self.sc_summary_fault_var.set(_tr_obj(self, f"{r.network_mode} · {r.fault_type}"))
            self.sc_summary_peak_var.set(f"{peak_phase_ka:.3f} kA")
            self.sc_summary_break_var.set(f"{r.I_break_kA:.3f} kA")
            self.sc_summary_tau_var.set(f"{r.tau_dc_s:.4f} s")

            text = (
                f"══ 复合序网计算结果 ═════════════════════════════\n"
                f"  网络模式：{r.network_mode}\n"
                f"  故障类型：{r.fault_type}，中性点：{r.neutral_mode}\n"
                f"  U = {r.U_kV:.4g} kV，线路长度 = {r.line_len_km:.4g} km，Rf = {r.Rf_ohm:.4g} Ω\n"
                f"  故障点位置（距左侧）= {r.fault_pos_from_left_pct:.3g}%\n"
                f"  Z1 = {r.Z1_ohm.real:.4f}+j{r.Z1_ohm.imag:.4f} Ω\n"
                f"  Z2 = {r.Z2_ohm.real:.4f}+j{r.Z2_ohm.imag:.4f} Ω\n"
                f"  Z0 = {r.Z0_ohm.real:.4f}+j{r.Z0_ohm.imag:.4f} Ω\n"
                f"  Zn = {r.Zn_ohm.real:.4f}+j{r.Zn_ohm.imag:.4f} Ω\n"
                f"  I1 = {_pa(r.I1_A)} A\n"
                f"  I2 = {_pa(r.I2_A)} A\n"
                f"  I0 = {_pa(r.I0_A)} A\n"
                f"  Ia = {_pa(r.Ia_A)} A\n"
                f"  Ib = {_pa(r.Ib_A)} A\n"
                f"  Ic = {_pa(r.Ic_A)} A\n"
                f"  V1 = {_pa(r.V1_V)} V\n"
                f"  V2 = {_pa(r.V2_V)} V\n"
                f"  V0 = {_pa(r.V0_V)} V\n"
                f"  Va = {_pa(r.Va_V)} V\n"
                f"  Vb = {_pa(r.Vb_V)} V\n"
                f"  Vc = {_pa(r.Vc_V)} V\n"
                f"  左侧支路 Ia/Ib/Ic = {_pa(r.Ia_from_left_A)} / {_pa(r.Ib_from_left_A)} / {_pa(r.Ic_from_left_A)} A\n"
                f"  右侧支路 Ia/Ib/Ic = {_pa(r.Ia_from_right_A)} / {_pa(r.Ib_from_right_A)} / {_pa(r.Ic_from_right_A)} A\n"
                f"  左侧开断校核电流 Ibreak,L = {r.I_break_left_kA:.4f} kA\n"
                f"  右侧开断校核电流 Ibreak,R = {r.I_break_right_kA:.4f} kA\n"
                f"  开断校核电流 Ibreak = {r.I_break_kA:.4f} kA\n"
                f"  直流偏置时间常数 τ = {r.tau_dc_s:.6f} s\n"
                f"\n══ 断路器匹配 ═════════════════════════════════════\n"
                f"  {check}\n"
                f"\n说明：{r.notes}"
            )
            self._set_text(self.sc_result, text)

            f = 50.0
            w = 2.0 * math.pi * f
            t_end = cycles / f
            t = np.linspace(0.0, t_end, int(2400 * cycles / 3.0) + 1)

            def iwave(I: complex) -> np.ndarray:
                amp = math.sqrt(2.0) * abs(I)
                phi = math.atan2(I.imag, I.real)
                iac = amp * np.sin(w * t + phi)
                idc = -amp * math.sin(phi) * np.exp(-t / max(r.tau_dc_s, 1e-4))
                return iac + idc

            def uwave(Uv: complex) -> np.ndarray:
                amp = math.sqrt(2.0) * abs(Uv)
                phi = math.atan2(Uv.imag, Uv.real)
                return amp * np.sin(w * t + phi)

            ia = iwave(r.Ia_A)
            ib = iwave(r.Ib_A)
            ic = iwave(r.Ic_A)
            i1 = iwave(r.I1_A)
            i2 = iwave(r.I2_A)
            i0 = iwave(r.I0_A)
            va = uwave(r.Va_V)
            vb = uwave(r.Vb_V)
            vc = uwave(r.Vc_V)
            v1 = uwave(r.V1_V)
            v2 = uwave(r.V2_V)
            v0 = uwave(r.V0_V)

            self.sc_ax_phase.clear()
            self.sc_ax_seq.clear()
            self.sc_ax_phase.plot(t, ia, label="iA", lw=1.2)
            self.sc_ax_phase.plot(t, ib, label="iB", lw=1.2)
            self.sc_ax_phase.plot(t, ic, label="iC", lw=1.2)
            self.sc_ax_phase.set_title("故障相电流")
            self.sc_ax_phase.set_ylabel("i_abc / A")
            self.sc_ax_phase.grid(True, alpha=0.35)
            self.sc_ax_phase.legend(loc="upper right", ncol=3, fontsize=8)

            self.sc_ax_seq.plot(t, i1, label="i1(正序)", lw=1.2)
            self.sc_ax_seq.plot(t, i2, label="i2(负序)", lw=1.2)
            self.sc_ax_seq.plot(t, i0, label="i0(零序)", lw=1.2)
            self.sc_ax_seq.set_title("故障序电流")
            self.sc_ax_seq.set_ylabel("i_012 / A")
            self.sc_ax_seq.set_xlabel("t / s")
            self.sc_ax_seq.grid(True, alpha=0.35)
            self.sc_ax_seq.legend(loc="upper right", ncol=3, fontsize=8)

            self.sc_v_ax_phase.clear()
            self.sc_v_ax_seq.clear()
            self.sc_v_ax_phase.plot(t, va, label="uA", lw=1.2)
            self.sc_v_ax_phase.plot(t, vb, label="uB", lw=1.2)
            self.sc_v_ax_phase.plot(t, vc, label="uC", lw=1.2)
            self.sc_v_ax_phase.set_title("故障相电压")
            self.sc_v_ax_phase.set_ylabel("u_abc / V")
            self.sc_v_ax_phase.grid(True, alpha=0.35)
            self.sc_v_ax_phase.legend(loc="upper right", ncol=3, fontsize=8)

            self.sc_v_ax_seq.plot(t, v1, label="u1(正序)", lw=1.2)
            self.sc_v_ax_seq.plot(t, v2, label="u2(负序)", lw=1.2)
            self.sc_v_ax_seq.plot(t, v0, label="u0(零序)", lw=1.2)
            self.sc_v_ax_seq.set_title("故障序电压")
            self.sc_v_ax_seq.set_ylabel("u_012 / V")
            self.sc_v_ax_seq.set_xlabel("t / s")
            self.sc_v_ax_seq.grid(True, alpha=0.35)
            self.sc_v_ax_seq.legend(loc="upper right", ncol=3, fontsize=8)

            show_labels = bool(self.sc_vector_labels_var.get())
            i_vectors = {"A": r.Ia_A, "B": r.Ib_A, "C": r.Ic_A, "1": r.I1_A, "2": r.I2_A, "0": r.I0_A}
            v_vectors = {"A": r.Va_V, "B": r.Vb_V, "C": r.Vc_V, "1": r.V1_V, "2": r.V2_V, "0": r.V0_V}
            self._draw_short_circuit_vector_axis(
                self.sc_ax_i_vector, i_vectors, "故障点电流向量图（ABC+012）",
                show_labels=show_labels, table_ax=self.sc_ax_i_table
            )
            self._draw_short_circuit_vector_axis(
                self.sc_v_ax_vector, v_vectors, "故障点电压向量图（ABC+012）",
                show_labels=show_labels, table_ax=self.sc_v_ax_table
            )

            self.sc_fig.subplots_adjust(left=0.07, right=0.98, top=0.94, bottom=0.08, wspace=0.28, hspace=0.36)
            self.sc_canvas.draw()
            self.sc_v_fig.subplots_adjust(left=0.07, right=0.98, top=0.94, bottom=0.08, wspace=0.28, hspace=0.36)
            self.sc_v_canvas.draw()

        except Exception as exc:
            messagebox.showerror("计算错误", str(exc))

    def _build_param_tab(self) -> None:
        """Build the "Parameter Validation and Per-Unit Conversion" tab, including the line, two-winding-transformer, and three-winding-transformer subpages. / 构建“参数校核与标幺值转换”标签页（含线路、双绕组变压器、三绕组变压器子页）。"""
        self.param_tab.columnconfigure(0, weight=1)
        self.param_tab.rowconfigure(0, weight=1)

        nb = ttk.Notebook(self.param_tab)
        nb.grid(row=0, column=0, sticky="nsew")
        self.param_notebook = nb
        self.param_notebook.bind("<<NotebookTabChanged>>", self._on_ai_context_changed)

        self._ptab_line = ttk.Frame(nb)
        self._ptab_sag  = ttk.Frame(nb)
        self._ptab_2wt  = ttk.Frame(nb)
        self._ptab_3wt  = ttk.Frame(nb)
        sag_tab_text = "Conductor Sag" if _lang_of(self) == "en" else "导线弧垂"
        line_tab_text = "Line" if _lang_of(self) == "en" else "线路"
        nb.add(self._ptab_line, text=line_tab_text)
        nb.add(self._ptab_sag,  text=sag_tab_text)
        nb.add(self._ptab_2wt,  text="两绕组变压器")
        nb.add(self._ptab_3wt,  text="三绕组变压器")

        self._build_line_param_sub()
        self._build_sag_sub()
        self._build_2wt_sub()
        self._build_3wt_sub()

    def _build_line_param_sub(self) -> None:
        f = self._ptab_line
        f.columnconfigure(0, weight=1)
        f.rowconfigure(0, weight=1)

        shell = ttk.Frame(f, padding=8, style="Surface.TFrame")
        shell.grid(row=0, column=0, sticky="nsew")
        shell.columnconfigure(0, weight=0, minsize=470)
        shell.columnconfigure(1, weight=1)
        shell.rowconfigure(0, weight=1)

        left = ttk.Frame(shell, padding=16, style="Card.TFrame")
        right = ttk.Frame(shell, padding=16, style="Card.TFrame")
        left.grid(row=0, column=0, sticky="nsw", padx=(0, 6))
        right.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        left.columnconfigure(0, weight=1)
        right.columnconfigure(0, weight=1)
        right.rowconfigure(2, weight=1)

        line_title = "Line parameter validation and per-unit conversion (π equivalent)" if _lang_of(self) == "en" else "线路参数校核与标幺值转换（π 型等值）"
        ttk.Label(left, text=line_title, style="PageTitle.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        hint = (
            "典型范围参考（§3.3/3.4）：R₁ 0.005~0.65 Ω/km，X₁ 0.20~0.42 Ω/km，C₁ 0.008~0.014 μF/km，"
            "Zc 240~420 Ω；超高压取下限，配电取上限。点击“线路参数计算”可选择架空线或电缆，由横截面几何、土壤、地线/护层与绝缘数据反算 R₁/X₁/R₀/X₀/C₁/C₀。"
        )
        ttk.Label(left, text=hint, style="Muted.TLabel", justify="left", wraplength=440).grid(
            row=1, column=0, sticky="ew", pady=(4, 10)
        )

        form = ttk.LabelFrame(left, text="输入参数", style="Card.TLabelframe", padding=10)
        form.grid(row=2, column=0, sticky="ew")
        form.columnconfigure(1, weight=1)
        self.lp_r1    = self._add_entry(form, 0, "单位长度电阻 R₁ / (Ω/km)", "0.028")
        self.lp_x1    = self._add_entry(form, 1, "单位长度电抗 X₁ / (Ω/km)", "0.299")
        self.lp_c1    = self._add_entry(form, 2, "单位长度电容 C₁ / (μF/km)", "0.013")
        self.lp_len   = self._add_entry(form, 3, "线路长度 / km", "200")
        self.lp_sbase = self._add_entry(form, 4, "基准容量 Sbase / MVA", "100")
        self.lp_ubase = self._add_entry(form, 5, "基准电压 Ubase / kV（线电压）", "500")

        button_row = ttk.Frame(left, style="Card.TFrame")
        button_row.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        button_row.columnconfigure(0, weight=1)
        button_row.columnconfigure(1, weight=1)
        button_row.columnconfigure(2, weight=1)
        ttk.Button(button_row, text="计算并校核", command=self.calculate_line_param, style="Accent.TButton").grid(
            row=0, column=0, sticky="ew", padx=(0, 4)
        )
        ttk.Button(button_row, text="线路参数计算", command=self.open_line_geometry_calculator).grid(
            row=0, column=1, sticky="ew", padx=4
        )
        ttk.Button(button_row, text="典型参数", command=self.show_line_param_reference).grid(
            row=0, column=2, sticky="ew", padx=(4, 0)
        )

        ttk.Label(right, text="计算结果", style="PageTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            right,
            text="右侧结果区整理有名值、标幺值与参数校核结论。线路几何反算与典型参数窗口可作为辅助资料页。",
            style="Muted.TLabel", justify="left", wraplength=760,
        ).grid(row=1, column=0, sticky="ew", pady=(4, 10))
        self.lp_result = ScrolledText(right, width=88, height=24, wrap=tk.WORD)
        self.lp_result.grid(row=2, column=0, sticky="nsew")
        right.rowconfigure(2, weight=1)
        self.lp_result.configure(state="disabled")
        self.calculate_line_param()

    def _build_2wt_sub(self) -> None:
        f = self._ptab_2wt
        f.columnconfigure(0, weight=1)
        f.rowconfigure(0, weight=1)

        shell = ttk.Frame(f, padding=8, style="Surface.TFrame")
        shell.grid(row=0, column=0, sticky="nsew")
        shell.columnconfigure(0, weight=0, minsize=470)
        shell.columnconfigure(1, weight=1)
        shell.rowconfigure(0, weight=1)

        left = ttk.Frame(shell, padding=16, style="Card.TFrame")
        right = ttk.Frame(shell, padding=16, style="Card.TFrame")
        left.grid(row=0, column=0, sticky="nsw", padx=(0, 6))
        right.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        left.columnconfigure(0, weight=1)
        right.columnconfigure(0, weight=1)
        right.rowconfigure(2, weight=1)

        ttk.Label(left, text="两绕组变压器参数校核与标幺值转换", style="PageTitle.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        hint = (
            "典型范围（§3.5）：Uk% 4~18%（特高压主变 18~24%），I₀% 0.1~5%，短路损耗 1~7 kW/MVA，空载损耗 0.1~3 kW/MVA。"
        )
        ttk.Label(left, text=hint, style="Muted.TLabel", justify="left", wraplength=440).grid(
            row=1, column=0, sticky="ew", pady=(4, 10)
        )

        form = ttk.LabelFrame(left, text="输入参数", style="Card.TLabelframe", padding=10)
        form.grid(row=2, column=0, sticky="ew")
        form.columnconfigure(1, weight=1)
        self.tx2_pk    = self._add_entry(form, 0, "短路损耗 Pk / kW", "290")
        self.tx2_uk    = self._add_entry(form, 1, "短路电压 Uk / %", "11.73")
        self.tx2_p0    = self._add_entry(form, 2, "空载损耗 P0 / kW", "51.3")
        self.tx2_i0    = self._add_entry(form, 3, "空载电流 I₀ / %", "0.3")
        self.tx2_sn    = self._add_entry(form, 4, "额定容量 SN / MVA", "20")
        self.tx2_un    = self._add_entry(form, 5, "高压侧额定电压 UN / kV", "35")
        self.tx2_sbase = self._add_entry(form, 6, "基准容量 Sbase / MVA", "100")
        self.tx2_ubase = self._add_entry(form, 7, "基准电压 Ubase / kV（通常 = UN）", "35")
        ttk.Button(left, text="计算并校核", command=self.calculate_2wt, style="Accent.TButton").grid(
            row=3, column=0, sticky="ew", pady=(10, 0)
        )

        ttk.Label(right, text="计算结果", style="PageTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            right,
            text="右侧统一展示折算阻抗、励磁支路与参数校核结果，便于与铭牌试验数据进行快速比对。",
            style="Muted.TLabel", justify="left", wraplength=760,
        ).grid(row=1, column=0, sticky="ew", pady=(4, 10))
        self.tx2_result = ScrolledText(right, width=88, height=24, wrap=tk.WORD)
        self.tx2_result.grid(row=2, column=0, sticky="nsew")
        self.tx2_result.configure(state="disabled")
        self.calculate_2wt()

    def _build_3wt_sub(self) -> None:
        f = self._ptab_3wt
        f.columnconfigure(0, weight=1)
        f.rowconfigure(0, weight=1)

        shell = ttk.Frame(f, padding=8, style="Surface.TFrame")
        shell.grid(row=0, column=0, sticky="nsew")
        shell.columnconfigure(0, weight=0, minsize=580)
        shell.columnconfigure(1, weight=1)
        shell.rowconfigure(0, weight=1)

        left_outer, left, _left_canvas = self._create_scrollable_card(shell, padding=16)
        left_outer.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        right = ttk.Frame(shell, padding=16, style="Card.TFrame")
        right.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        left.columnconfigure(0, weight=1)
        right.columnconfigure(0, weight=1)
        right.rowconfigure(2, weight=1)

        ttk.Label(left, text="三绕组变压器参数校核与标幺值转换", style="PageTitle.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        hint = (
            "输入约定：Pk 为两两短路试验损耗（kW），Uk% 为两两短路电压（%）。Pk_HL、Uk_HL 若测试是在低压侧额定电流下做的，"
            "程序会自动按 SN_H/SN_L 折算到高压侧额定电流基准。"
        )
        ttk.Label(left, text=hint, style="Muted.TLabel", justify="left", wraplength=530).grid(
            row=1, column=0, sticky="ew", pady=(4, 10)
        )

        form = ttk.LabelFrame(left, text="输入参数", style="Card.TLabelframe", padding=10)
        form.grid(row=2, column=0, sticky="ew")
        form.columnconfigure(1, weight=1, minsize=120)
        form.columnconfigure(3, weight=1, minsize=120)

        row = 0
        self.tx3_pk_hm  = self._add_entry(form, row,   "短路损耗 Pk_HM / kW",    "503.6",  column=0)
        self.tx3_uk_hm  = self._add_entry(form, row,   "Uk_HM / %",              "17.5",   column=2)
        row += 1
        self.tx3_pk_hl  = self._add_entry(form, row,   "短路损耗 Pk_HL / kW",    "129.0",  column=0)
        self.tx3_uk_hl  = self._add_entry(form, row,   "Uk_HL / %",              "11.0",   column=2)
        row += 1
        self.tx3_pk_ml  = self._add_entry(form, row,   "短路损耗 Pk_ML / kW",    "120.7",  column=0)
        self.tx3_uk_ml  = self._add_entry(form, row,   "Uk_ML / %",              "6.0",    column=2)
        row += 1
        self.tx3_p0     = self._add_entry(form, row,   "空载损耗 P0 / kW",       "76.1",   column=0)
        self.tx3_i0     = self._add_entry(form, row,   "空载电流 I₀ / %",        "0.07",   column=2)
        row += 1
        self.tx3_sn_h   = self._add_entry(form, row,   "高压侧额定容量 SN_H / MVA", "180", column=0)
        self.tx3_un_h   = self._add_entry(form, row,   "高压侧额定电压 UN_H / kV",  "220", column=2)
        row += 1
        self.tx3_sn_m   = self._add_entry(form, row,   "中压侧额定容量 SN_M / MVA", "180", column=0)
        self.tx3_sn_l   = self._add_entry(form, row,   "低压侧额定容量 SN_L / MVA", "90",  column=2)
        row += 1
        self.tx3_sbase  = self._add_entry(form, row,   "基准容量 Sbase / MVA",    "100",   column=0)
        self.tx3_ubase  = self._add_entry(form, row,   "基准电压 Ubase / kV",     "220",   column=2)

        ttk.Button(left, text="计算并校核", command=self.calculate_3wt, style="Accent.TButton").grid(
            row=3, column=0, sticky="ew", pady=(10, 0)
        )

        ttk.Label(right, text="计算结果", style="PageTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            right,
            text="结果区统一展示折算到高压侧的 T 型等值参数、标幺阻抗与励磁支路校核结论，便于工程核对。",
            style="Muted.TLabel", justify="left", wraplength=760,
        ).grid(row=1, column=0, sticky="ew", pady=(4, 10))
        self.tx3_result = ScrolledText(right, width=92, height=24, wrap=tk.WORD)
        self.tx3_result.grid(row=2, column=0, sticky="nsew")
        self.tx3_result.configure(state="disabled")
        self.calculate_3wt()

    def _build_sag_sub(self) -> None:
        """Build the conductor-sag page with interactive temperature/current sliders. / 构建导线弧垂页面，提供温度/载流量交互滑块。"""
        lang = _lang_of(self)
        txt = lambda zh, en: en if lang == "en" else zh

        f = self._ptab_sag
        f.columnconfigure(0, weight=1)
        f.rowconfigure(0, weight=1)

        shell = ttk.Frame(f, padding=8, style="Surface.TFrame")
        shell.grid(row=0, column=0, sticky="nsew")
        shell.columnconfigure(0, weight=0, minsize=620)
        shell.columnconfigure(1, weight=1)
        shell.rowconfigure(0, weight=1)

        left_outer, left, _left_canvas = self._create_scrollable_card(shell, padding=16)
        left_outer.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        right = ttk.Frame(shell, padding=16, style="Card.TFrame")
        right.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        left.columnconfigure(0, weight=1)
        right.columnconfigure(0, weight=1)
        right.rowconfigure(2, weight=3)
        right.rowconfigure(4, weight=2)

        title = txt("输电线路导线弧垂计算（单档悬链线）", "Transmission-line conductor sag (single-span catenary)")
        intro = txt(
            "本页按不等高挂点的悬链线模型计算导线弧垂，并以参考温度/参考水平张力为基准回算当前张力。"
            "在“载流量估温”模式下，程序先用简化稳态热平衡把电流换算成导线温度，再求解弧垂。"
            "拖动温度或载流量滑块，可直观看到导线简图和关键指标的变化。",
            "This page evaluates conductor sag using a catenary model with unequal support heights and back-solves the current tension from a reference temperature/reference horizontal tension state. "
            "In current mode the tool first converts line current into conductor temperature through a simplified steady-state thermal balance and then solves the sag-tension state. "
            "Drag either the temperature slider or the current slider to update the conductor sketch and key indicators in real time.",
        )
        ttk.Label(left, text=title, style="PageTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(left, text=intro, style="Card.TLabel", justify="left", wraplength=560).grid(
            row=1, column=0, sticky="ew", pady=(4, 10)
        )

        mech = ttk.LabelFrame(left, text=txt("几何与机械参数", "Geometry and mechanical parameters"), style="Card.TLabelframe", padding=10)
        mech.grid(row=2, column=0, sticky="ew")
        mech.columnconfigure(1, weight=1, minsize=120)
        mech.columnconfigure(3, weight=1, minsize=120)
        self.sag_span = self._add_entry(mech, 0, txt("档距 l / m", "Span length l / m"), "400", column=0)
        self.sag_h_left = self._add_entry(mech, 0, txt("左挂点高度 h_A / m", "Left support height h_A / m"), "25", column=2)
        self.sag_h_right = self._add_entry(mech, 1, txt("右挂点高度 h_B / m", "Right support height h_B / m"), "35", column=0)
        self.sag_mass = self._add_entry(mech, 1, txt("单位质量 m / (kg/m)", "Line mass m / (kg/m)"), "1.35", column=2)
        self.sag_area = self._add_entry(mech, 2, txt("截面积 A / mm²", "Cross-section area A / mm²"), "425", column=0)
        self.sag_E = self._add_entry(mech, 2, txt("等效弹性模量 E / GPa", "Equivalent elastic modulus E / GPa"), "70", column=2)
        self.sag_alpha = self._add_entry(mech, 3, txt("线膨胀系数 α_L / (1/°C)", "Thermal expansion α_L / (1/°C)"), "1.90e-5", column=0)
        self.sag_tref = self._add_entry(mech, 3, txt("参考温度 T_ref / °C", "Reference temperature T_ref / °C"), "20", column=2)
        self.sag_href = self._add_entry(mech, 4, txt("参考水平张力 H_ref / kN", "Reference horizontal tension H_ref / kN"), "20", column=0)
        ttk.Label(mech, text=txt("说明：单位质量自动按 m·g 换算为自重荷载；当前版本未计风偏、覆冰与长期蠕变。", "Note: the line mass is automatically converted into self-weight through m·g; the present model does not include wind swing, ice loading, or long-term creep."), style="Card.TLabel", justify="left", wraplength=520).grid(
            row=5, column=0, columnspan=4, sticky="ew", padx=4, pady=(6, 0)
        )

        thermal = ttk.LabelFrame(left, text=txt("载流量—温度近似模型", "Current-to-temperature approximation"), style="Card.TLabelframe", padding=10)
        thermal.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        thermal.columnconfigure(1, weight=1, minsize=120)
        thermal.columnconfigure(3, weight=1, minsize=120)
        self.sag_ambient = self._add_entry(thermal, 0, txt("环境温度 T_a / °C", "Ambient temperature T_a / °C"), "25", column=0)
        self.sag_r20 = self._add_entry(thermal, 0, txt("20°C 电阻 R20 / (Ω/km)", "20°C resistance R20 / (Ω/km)"), "0.068", column=2)
        self.sag_alpha_r = self._add_entry(thermal, 1, txt("电阻温度系数 α_R / (1/°C)", "Resistance temperature coefficient α_R / (1/°C)"), "0.00403", column=0)
        self.sag_cooling = self._add_entry(thermal, 1, txt("等效冷却系数 k_c / (W/(m·K))", "Effective cooling coefficient k_c / (W/(m·K))"), "1.20", column=2)
        self.sag_solar = self._add_entry(thermal, 2, txt("太阳热增益 q_s / (W/m)", "Solar heat gain q_s / (W/m)"), "4.0", column=0)
        ttk.Label(thermal, text=txt("说明：此处采用 I²R(T)+q_s = k_c(T_c-T_a) 的集总稳态近似，适合滑块交互与快速工程估算。", "Note: the page uses a lumped steady-state approximation I²R(T)+q_s = k_c(T_c-T_a), which is intended for interactive sliders and fast engineering estimates."), style="Card.TLabel", justify="left", wraplength=520).grid(
            row=3, column=0, columnspan=4, sticky="ew", padx=4, pady=(6, 0)
        )

        sliders = ttk.LabelFrame(left, text=txt("交互驱动变量", "Interactive driving variables"), style="Card.TLabelframe", padding=10)
        sliders.grid(row=4, column=0, sticky="ew", pady=(10, 0))
        sliders.columnconfigure(1, weight=1)
        sliders.columnconfigure(2, weight=0)

        self.sag_driver_var = tk.StringVar(value="temperature")
        mode_bar = ttk.Frame(sliders, style="Card.TFrame")
        mode_bar.grid(row=0, column=0, columnspan=3, sticky="ew")
        ttk.Radiobutton(mode_bar, text=txt("按导线温度直接驱动", "Drive by conductor temperature"), value="temperature", variable=self.sag_driver_var, command=self._on_sag_mode_change).grid(row=0, column=0, sticky="w", padx=(0, 12))
        ttk.Radiobutton(mode_bar, text=txt("按载流量估温驱动", "Drive by current-derived temperature"), value="current", variable=self.sag_driver_var, command=self._on_sag_mode_change).grid(row=0, column=1, sticky="w")

        self.sag_temp_scale_var = tk.DoubleVar(value=40.0)
        self.sag_current_scale_var = tk.DoubleVar(value=600.0)
        self.sag_temp_value_var = tk.StringVar(value="40.0 °C")
        self.sag_current_value_var = tk.StringVar(value="600 A")
        ttk.Label(sliders, text=txt("导线运行温度 T_c / °C", "Conductor temperature T_c / °C"), style="Form.TLabel").grid(row=1, column=0, sticky="w", padx=4, pady=(8, 2))
        ttk.Label(sliders, textvariable=self.sag_temp_value_var, style="Card.TLabel").grid(row=1, column=2, sticky="e", padx=4, pady=(8, 2))
        self.sag_temp_slider = ttk.Scale(sliders, from_=-20.0, to=120.0, orient=tk.HORIZONTAL, variable=self.sag_temp_scale_var, command=lambda _v: self._on_sag_slider_change("temperature"), style="Accent.Horizontal.TScale")
        self.sag_temp_slider.grid(row=2, column=0, columnspan=3, sticky="ew", padx=4)

        ttk.Label(sliders, text=txt("载流量 I / A", "Line current I / A"), style="Form.TLabel").grid(row=3, column=0, sticky="w", padx=4, pady=(8, 2))
        ttk.Label(sliders, textvariable=self.sag_current_value_var, style="Card.TLabel").grid(row=3, column=2, sticky="e", padx=4, pady=(8, 2))
        self.sag_current_slider = ttk.Scale(sliders, from_=0.0, to=1200.0, orient=tk.HORIZONTAL, variable=self.sag_current_scale_var, command=lambda _v: self._on_sag_slider_change("current"), style="Accent.Horizontal.TScale")
        self.sag_current_slider.grid(row=4, column=0, columnspan=3, sticky="ew", padx=4)

        ttk.Label(sliders, text=txt("拖动任一滑块时，页面会自动切换到对应驱动方式并刷新弧垂。", "Dragging either slider automatically switches the page to the corresponding driving mode and refreshes the sag state."), style="Card.TLabel", justify="left", wraplength=520).grid(
            row=5, column=0, columnspan=3, sticky="ew", padx=4, pady=(8, 6)
        )
        ttk.Button(sliders, text=txt("计算并绘图", "Calculate & Plot"), command=self.calculate_sag_analysis, style="Accent.TButton").grid(row=6, column=0, columnspan=3, sticky="ew", padx=4, pady=(2, 0))

        ttk.Label(right, text=txt("关键指标", "Key indicators"), style="PageTitle.TLabel").grid(row=0, column=0, sticky="w")
        metrics = ttk.Frame(right, style="Card.TFrame")
        metrics.grid(row=1, column=0, sticky="ew", pady=(6, 10))
        self.sag_metric_vars = {
            "driver": tk.StringVar(value="--"),
            "temp": tk.StringVar(value="--"),
            "current": tk.StringVar(value="--"),
            "sag": tk.StringVar(value="--"),
            "clearance": tk.StringVar(value="--"),
            "tension": tk.StringVar(value="--"),
        }
        metric_defs = [
            (txt("驱动方式", "Driver"), "driver"),
            (txt("导线温度", "Conductor temp."), "temp"),
            (txt("载流量", "Current"), "current"),
            (txt("最大弦垂", "Maximum sag"), "sag"),
            (txt("最小净空", "Minimum clearance"), "clearance"),
            (txt("水平张力", "Horizontal tension"), "tension"),
        ]
        for idx, (metric_title, key) in enumerate(metric_defs):
            row, col = divmod(idx, 3)
            card = ttk.Frame(metrics, padding=(10, 8), style="Metric.TFrame")
            card.grid(row=row, column=col, sticky="nsew", padx=4, pady=4)
            metrics.columnconfigure(col, weight=1)
            ttk.Label(card, text=metric_title, style="MetricTitle.TLabel").grid(row=0, column=0, sticky="w")
            ttk.Label(card, textvariable=self.sag_metric_vars[key], style="MetricValue.TLabel").grid(row=1, column=0, sticky="w", pady=(4, 0))

        plot_frame = ttk.LabelFrame(right, text=txt("输电导线简图与悬链线", "Conductor sketch and catenary"), style="Card.TLabelframe", padding=4)
        plot_frame.grid(row=2, column=0, sticky="nsew")
        plot_frame.columnconfigure(0, weight=1)
        plot_frame.rowconfigure(0, weight=1)
        self.sag_fig = Figure(figsize=(8.1, 5.1), dpi=100)
        self.sag_ax = self.sag_fig.add_subplot(111)
        self.sag_canvas = FigureCanvasTkAgg(self.sag_fig, master=plot_frame)
        self.sag_canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

        toolbar_frame = ttk.Frame(right, style="Card.TFrame")
        toolbar_frame.grid(row=3, column=0, sticky="ew", pady=(4, 8))
        self.sag_toolbar = NavigationToolbar2Tk(self.sag_canvas, toolbar_frame, pack_toolbar=False)
        self.sag_toolbar.update()
        self.sag_toolbar.pack(fill="x")

        ttk.Label(right, text=txt("结果说明", "Result notes"), style="SectionTitle.TLabel").grid(row=4, column=0, sticky="w", pady=(2, 4))
        self.sag_result = ScrolledText(right, width=90, height=13, wrap=tk.WORD)
        self.sag_result.grid(row=5, column=0, sticky="nsew")
        self.sag_result.configure(state="disabled")

        self._sag_last_result = None
        self._update_sag_slider_labels()
        for widget in (
            self.sag_span, self.sag_h_left, self.sag_h_right, self.sag_mass,
            self.sag_area, self.sag_E, self.sag_alpha, self.sag_tref,
            self.sag_href, self.sag_ambient, self.sag_r20, self.sag_alpha_r,
            self.sag_cooling, self.sag_solar,
        ):
            widget.bind("<FocusOut>", lambda _e: self._refresh_sag_analysis(show_error=False))
            widget.bind("<Return>", lambda _e: self._refresh_sag_analysis(show_error=False))
        self._refresh_sag_analysis(show_error=False)

    def _update_sag_slider_labels(self) -> None:
        """Refresh the slider-value labels. / 刷新滑块数值标签。"""
        if not hasattr(self, "sag_temp_value_var"):
            return
        self.sag_temp_value_var.set(f"{float(self.sag_temp_scale_var.get()):.1f} °C")
        self.sag_current_value_var.set(f"{float(self.sag_current_scale_var.get()):.0f} A")

    def _on_sag_mode_change(self) -> None:
        """Refresh the page after the driving mode is changed. / 切换驱动方式后刷新页面。"""
        self._update_sag_slider_labels()
        self._refresh_sag_analysis(show_error=False)

    def _on_sag_slider_change(self, driver: str) -> None:
        """Switch to the corresponding driving mode and refresh interactively. / 拖动滑块时自动切换到相应驱动方式并交互刷新。"""
        if hasattr(self, "sag_driver_var"):
            self.sag_driver_var.set(driver)
        self._update_sag_slider_labels()
        self._refresh_sag_analysis(show_error=False)

    def _collect_sag_inputs(self) -> dict[str, float | str]:
        """Collect conductor-sag inputs from the GUI. / 从界面读取导线弧垂参数。"""
        lang = _lang_of(self)
        txt = lambda zh, en: en if lang == "en" else zh
        return {
            "span_m": _safe_float(self.sag_span.get(), txt("档距", "Span length")),
            "left_support_height_m": _safe_float(self.sag_h_left.get(), txt("左挂点高度", "Left support height")),
            "right_support_height_m": _safe_float(self.sag_h_right.get(), txt("右挂点高度", "Right support height")),
            "line_mass_kg_per_m": _safe_float(self.sag_mass.get(), txt("单位质量", "Line mass")),
            "cross_section_mm2": _safe_float(self.sag_area.get(), txt("截面积", "Cross-section area")),
            "elastic_modulus_gpa": _safe_float(self.sag_E.get(), txt("等效弹性模量", "Equivalent elastic modulus")),
            "thermal_expansion_per_c": _safe_float(self.sag_alpha.get(), txt("线膨胀系数", "Thermal expansion coefficient")),
            "reference_temperature_c": _safe_float(self.sag_tref.get(), txt("参考温度", "Reference temperature")),
            "reference_horizontal_tension_kN": _safe_float(self.sag_href.get(), txt("参考水平张力", "Reference horizontal tension")),
            "driver_mode": self.sag_driver_var.get().strip() or "temperature",
            "conductor_temperature_c": float(self.sag_temp_scale_var.get()),
            "current_a": float(self.sag_current_scale_var.get()),
            "ambient_temp_c": _safe_float(self.sag_ambient.get(), txt("环境温度", "Ambient temperature")),
            "resistance_20c_ohm_per_km": _safe_float(self.sag_r20.get(), txt("20°C 电阻", "20°C resistance")),
            "resistance_temp_coeff_per_c": _safe_float(self.sag_alpha_r.get(), txt("电阻温度系数", "Resistance temperature coefficient")),
            "cooling_coeff_w_per_mk": _safe_float(self.sag_cooling.get(), txt("等效冷却系数", "Effective cooling coefficient")),
            "solar_gain_w_per_m": _safe_float(self.sag_solar.get(), txt("太阳热增益", "Solar heat gain")),
        }

    def _set_sag_metric_defaults(self) -> None:
        """Reset metric cards to placeholders. / 将指标卡片重置为占位值。"""
        for var in getattr(self, "sag_metric_vars", {}).values():
            var.set("--")

    def _render_sag_metrics(self, result) -> None:
        """Render the summary metric cards. / 渲染顶部指标卡片。"""
        if result is None:
            self._set_sag_metric_defaults()
            return
        lang = _lang_of(self)
        driver_text = (
            "Current-derived temperature" if result.driver_mode == "current" else "Direct conductor temperature"
        ) if lang == "en" else (
            "按载流量估温" if result.driver_mode == "current" else "按导线温度直接驱动"
        )
        self.sag_metric_vars["driver"].set(driver_text)
        self.sag_metric_vars["temp"].set(f"{result.conductor_temperature_c:.1f} °C")
        self.sag_metric_vars["current"].set(f"{result.current_a:.0f} A")
        self.sag_metric_vars["sag"].set(f"{result.operating_state.maximum_sag_m:.3f} m")
        self.sag_metric_vars["clearance"].set(f"{result.operating_state.minimum_clearance_m:.3f} m")
        self.sag_metric_vars["tension"].set(f"{result.operating_state.horizontal_tension_n / 1000.0:.3f} kN")

    def _render_sag_plot(self, result) -> None:
        """Draw the conductor sketch and the reference/current catenaries. / 绘制导线简图与参考/当前悬链线。"""
        if getattr(self, "sag_ax", None) is None:
            return
        lang = _lang_of(self)
        txt = lambda zh, en: en if lang == "en" else zh
        ax = self.sag_ax
        ax.clear()

        ref = result.reference_state
        op = result.operating_state
        span = result.span_m
        left_h = result.left_support_height_m
        right_h = result.right_support_height_m

        ground_line = np.zeros_like(op.x_profile_m)
        ax.plot(op.x_profile_m, ground_line, color="#4a5568", linewidth=1.6, label=txt("地面", "Ground"))
        tower_arm = max(4.0, 0.035 * span)
        for x_tower, height, label in ((0.0, left_h, "A"), (span, right_h, "B")):
            ax.plot([x_tower, x_tower], [0.0, height], color="#4a5568", linewidth=2.2)
            if x_tower == 0.0:
                ax.plot([x_tower, x_tower + tower_arm], [height, height], color="#4a5568", linewidth=2.0)
            else:
                ax.plot([x_tower - tower_arm, x_tower], [height, height], color="#4a5568", linewidth=2.0)
            ax.text(x_tower, height + 0.7, label, ha="center", va="bottom", fontsize=10, fontweight="bold")

        ax.plot(ref.x_profile_m, ref.y_profile_m, linestyle="--", linewidth=1.4, label=txt("参考状态导线", "Reference conductor"))
        ax.plot(op.x_profile_m, op.y_profile_m, linewidth=2.4, label=txt("当前状态导线", "Current conductor"))
        ax.plot(op.x_profile_m, op.y_chord_m, linestyle=":", linewidth=1.2, label=txt("挂点连线", "Support chord"))

        x_sag = op.maximum_sag_x_m
        y_conductor = float(np.interp(x_sag, op.x_profile_m, op.y_profile_m))
        y_chord = float(np.interp(x_sag, op.x_profile_m, op.y_chord_m))
        ax.annotate("", xy=(x_sag, y_chord), xytext=(x_sag, y_conductor), arrowprops=dict(arrowstyle="<->", linewidth=1.2, color="#8b5a00"))
        ax.text(
            x_sag + 0.02 * span,
            0.5 * (y_conductor + y_chord),
            txt(f"最大弦垂 {op.maximum_sag_m:.2f} m", f"Max sag {op.maximum_sag_m:.2f} m"),
            fontsize=9,
            va="center",
        )

        x_clear = op.minimum_clearance_x_m
        y_clear = op.minimum_clearance_m
        ax.scatter([x_clear], [y_clear], s=30, zorder=5)
        ax.annotate(
            txt(f"最小净空 {y_clear:.2f} m", f"Min clearance {y_clear:.2f} m"),
            xy=(x_clear, y_clear),
            xytext=(x_clear + 0.06 * span, y_clear + max(1.2, 0.08 * max(left_h, right_h))),
            arrowprops=dict(arrowstyle="->", linewidth=1.0),
            fontsize=9,
        )

        title = txt("输电导线悬链线示意（当前状态 vs 参考状态）", "Transmission-line catenary sketch (current vs reference)")
        subtitle = txt(
            f"驱动方式：{'载流量估温' if result.driver_mode == 'current' else '导线温度'}，当前导线温度 T_c = {result.conductor_temperature_c:.1f} °C",
            f"Driver: {'current-derived temperature' if result.driver_mode == 'current' else 'direct conductor temperature'}, conductor temperature T_c = {result.conductor_temperature_c:.1f} °C",
        )
        ax.set_title(f"{title}\n{subtitle}")
        ax.set_xlabel(txt("跨距坐标 x / m", "Span coordinate x / m"))
        ax.set_ylabel(txt("高度 / m", "Height / m"))
        ax.grid(True)
        ax.legend(loc="upper right")
        ymax = max(float(np.max(ref.y_profile_m)), float(np.max(op.y_profile_m)), left_h, right_h) + max(2.0, 0.12 * max(left_h, right_h))
        ax.set_xlim(-0.04 * span, 1.04 * span)
        ax.set_ylim(-0.5, ymax)
        self.sag_canvas.draw_idle()

    def _render_sag_result_text(self, result) -> str:
        """Build the bilingual result text for the sag page. / 生成弧垂页面的双语结果文本。"""
        lang = _lang_of(self)
        ref = result.reference_state
        op = result.operating_state
        delta_sag = op.maximum_sag_m - ref.maximum_sag_m
        delta_mid = op.midspan_sag_m - ref.midspan_sag_m

        if lang == "en":
            lines = [
                f"Driver mode: {'current-derived temperature' if result.driver_mode == 'current' else 'direct conductor temperature'}",
                f"Current slider value I = {result.current_a:.0f} A",
                f"Active conductor temperature T_c = {result.conductor_temperature_c:.2f} °C",
                f"Reference state: T_ref = {result.reference_temperature_c:.2f} °C, H_ref = {result.reference_horizontal_tension_n / 1000.0:.3f} kN",
                "",
                "══ Operating catenary state ═══════════════════════════════════════",
                f"Horizontal tension H = {op.horizontal_tension_n / 1000.0:.6f} kN",
                f"Average conductor tension T_avg = {op.average_tension_n / 1000.0:.6f} kN",
                f"Left / right support tension = {op.left_support_tension_n / 1000.0:.6f} / {op.right_support_tension_n / 1000.0:.6f} kN",
                f"Left / right support tangent angle = {op.support_angle_left_deg:+.3f}° / {op.support_angle_right_deg:+.3f}°",
                f"Conductor length in span S = {op.arc_length_m:.6f} m (reference {ref.arc_length_m:.6f} m)",
                f"Maximum sag from the support chord f_max = {op.maximum_sag_m:.6f} m at x = {op.maximum_sag_x_m:.3f} m",
                f"Midspan sag f_mid = {op.midspan_sag_m:.6f} m (Δf_mid = {delta_mid:+.6f} m vs reference)",
                f"Minimum ground clearance within the span = {op.minimum_clearance_m:.6f} m at x = {op.minimum_clearance_x_m:.3f} m",
                f"Change in maximum sag relative to the reference state Δf_max = {delta_sag:+.6f} m",
            ]
            if result.thermal_balance is not None:
                th = result.thermal_balance
                lines += [
                    "",
                    "══ Simplified thermal balance ════════════════════════════════════",
                    f"Ambient temperature T_a = {th.ambient_temp_c:.2f} °C",
                    f"Resistance at T_c: R(T_c) = {th.resistance_ohm_per_m * 1000.0:.6f} Ω/km",
                    f"Joule heating I²R = {th.joule_heating_w_per_m:.6f} W/m",
                    f"Solar heat gain q_s = {th.solar_gain_w_per_m:.6f} W/m",
                    f"Equivalent cooling k_c(T_c - T_a) = {th.cooling_w_per_m:.6f} W/m",
                    f"Estimated temperature rise ΔT = {th.temperature_rise_c:.6f} °C",
                ]
            lines += [
                "",
                "Notes:",
                "This page uses a single-span catenary with unequal support heights. Wind swing, ice loading, creep, and nonlinear elastoplastic effects are neglected.",
                "The tension-temperature compatibility is solved from the reference state through thermal expansion plus an average-tension elastic extension approximation.",
                "The current mode uses the lumped steady-state thermal relation I²R(T) + q_s = k_c (T_c - T_a); it is intended for fast engineering interaction and is not equivalent to IEEE 738 or a detailed thermo-fluid model.",
            ]
            if not op.lowest_point_inside_span:
                lines.append("The theoretical catenary low point lies outside the span; therefore the minimum clearance within the span occurs at the lower support side.")
            return "\n".join(lines)

        lines = [
            f"驱动方式：{'按载流量估温' if result.driver_mode == 'current' else '按导线温度直接驱动'}",
            f"当前滑块载流量 I = {result.current_a:.0f} A",
            f"当前导线温度 T_c = {result.conductor_temperature_c:.2f} °C",
            f"参考状态：T_ref = {result.reference_temperature_c:.2f} °C，H_ref = {result.reference_horizontal_tension_n / 1000.0:.3f} kN",
            "",
            "══ 当前悬链线状态 ═══════════════════════════════════════",
            f"水平张力 H = {op.horizontal_tension_n / 1000.0:.6f} kN",
            f"平均导线张力 T_avg = {op.average_tension_n / 1000.0:.6f} kN",
            f"左/右挂点张力 = {op.left_support_tension_n / 1000.0:.6f} / {op.right_support_tension_n / 1000.0:.6f} kN",
            f"左/右挂点切线角 = {op.support_angle_left_deg:+.3f}° / {op.support_angle_right_deg:+.3f}°",
            f"跨内导线长度 S = {op.arc_length_m:.6f} m（参考状态 {ref.arc_length_m:.6f} m）",
            f"最大弦垂 f_max = {op.maximum_sag_m:.6f} m，位置 x = {op.maximum_sag_x_m:.3f} m",
            f"跨中弦垂 f_mid = {op.midspan_sag_m:.6f} m（相对参考状态 Δf_mid = {delta_mid:+.6f} m）",
            f"跨内最小净空 = {op.minimum_clearance_m:.6f} m，位置 x = {op.minimum_clearance_x_m:.3f} m",
            f"相对参考状态的最大弦垂变化 Δf_max = {delta_sag:+.6f} m",
        ]
        if result.thermal_balance is not None:
            th = result.thermal_balance
            lines += [
                "",
                "══ 简化热平衡 ═══════════════════════════════════════════",
                f"环境温度 T_a = {th.ambient_temp_c:.2f} °C",
                f"导线电阻 R(T_c) = {th.resistance_ohm_per_m * 1000.0:.6f} Ω/km",
                f"焦耳热 I²R = {th.joule_heating_w_per_m:.6f} W/m",
                f"太阳热增益 q_s = {th.solar_gain_w_per_m:.6f} W/m",
                f"等效散热 k_c(T_c - T_a) = {th.cooling_w_per_m:.6f} W/m",
                f"估算温升 ΔT = {th.temperature_rise_c:.6f} °C",
            ]
        lines += [
            "",
            "说明：",
            "本页采用单档、不等高挂点的悬链线模型；未计风偏、覆冰、长期蠕变与非线性弹塑性，仅适合快速工程估算。",
            "张力—温度关系由参考状态经热膨胀与平均张力弹性伸长近似回算得到。",
            "载流量模式采用 I²R(T)+q_s = k_c(T_c-T_a) 的集总稳态热平衡，不等价于 IEEE 738 或更详细的热-流体模型。",
        ]
        if not op.lowest_point_inside_span:
            lines.append("当前参数下，理论最低点位于跨外，跨内最小净空出现在较低挂点侧。")
        return "\n".join(lines)

    def _render_sag_error(self, message: str) -> None:
        """Render a non-blocking sag-page error state. / 在弧垂页面中渲染非阻塞错误状态。"""
        self._set_sag_metric_defaults()
        if getattr(self, "sag_ax", None) is not None:
            self.sag_ax.clear()
            self.sag_ax.text(0.5, 0.5, message, ha="center", va="center", transform=self.sag_ax.transAxes, wrap=True)
            self.sag_ax.set_axis_off()
            self.sag_canvas.draw_idle()
        if getattr(self, "sag_result", None) is not None:
            self._set_text(self.sag_result, message)

    def _refresh_sag_analysis(self, show_error: bool = False) -> None:
        """Refresh the sag analysis, optionally raising a popup on errors. / 刷新弧垂分析，并可选地在异常时弹窗。"""
        try:
            inputs = self._collect_sag_inputs()
            result = analyze_conductor_sag(**inputs)
            self._sag_last_result = result
            self._render_sag_metrics(result)
            self._render_sag_plot(result)
            self._set_text(self.sag_result, self._render_sag_result_text(result))
        except Exception as exc:
            self._sag_last_result = None
            self._render_sag_error(str(exc))
            if show_error:
                if _lang_of(self) == "en":
                    messagebox.showerror("Calculation Error", str(exc))
                else:
                    messagebox.showerror("计算错误", str(exc))

    def calculate_sag_analysis(self) -> None:
        """Run the conductor-sag analysis from the button. / 按按钮执行导线弧垂分析。"""
        self._refresh_sag_analysis(show_error=True)

    def show_line_param_reference(self) -> None:
        """Open the typical-parameter window for overhead lines, grouped by voltage level. / 弹出架空线路典型参数窗口（按电压等级展示）。"""
        try:
            data = load_line_params_reference()
        except Exception as exc:
            messagebox.showerror("读取失败", str(exc))
            return

        win = tk.Toplevel(self)
        win.title("架空线路典型参数")
        win.geometry("980x700")
        win.minsize(860, 560)

        container = ttk.Frame(win, padding=8)
        container.pack(fill="both", expand=True)

        title = data.get("description") or "架空线路典型参数"
        ttk.Label(container, text=title, font=("TkDefaultFont", 11, "bold")).pack(anchor="w")
        # Optional source label is kept disabled to reduce visual noise. / 数据来源标签预留但默认关闭，以减少视觉干扰。

        text = ScrolledText(container, wrap=tk.NONE, font="TkFixedFont")
        text.pack(fill="both", expand=True)

        lines = []
        for sec in data.get("sections", []):
            voltage = sec.get("voltage_level_kv")
            line_type = sec.get("line_type") or "-"
            sec_title = sec.get("section_title", "未命名分组")
            lines.append(f"\n【{sec_title}】")
            if voltage:
                lines.append(f"电压等级：{voltage} kV    线路类型：{line_type}")
            source_note = sec.get("source_note") or sec.get("note")
            if source_note:
                lines.append(f"说明：{source_note}")

            entries = sec.get("entries", [])
            if not entries:
                lines.append("  （无数据）")
                continue

            lines.append("型号/布置                          R1(Ω/km)   X1(Ω/km)   C1(μF/km)   R0(Ω/km)   X0(Ω/km)   C0(μF/km)")
            lines.append("-" * 112)
            for item in entries:
                model = str(item.get("conductor_model") or "-")
                layout = item.get("layout")
                if layout:
                    model = f"{model} / {layout}"

                def _fmt(v: object) -> str:
                    return "-" if v is None else f"{float(v):.6g}"

                lines.append(
                    f"{model:<34}"
                    f"{_fmt(item.get('R1_ohm_per_km')):>10}"
                    f"{_fmt(item.get('X1_ohm_per_km')):>12}"
                    f"{_fmt(item.get('C1_uF_per_km')):>13}"
                    f"{_fmt(item.get('R0_ohm_per_km')):>12}"
                    f"{_fmt(item.get('X0_ohm_per_km')):>12}"
                    f"{_fmt(item.get('C0_uF_per_km')):>13}"
                )

        text.insert("1.0", "\n".join(lines).lstrip())
        text.configure(state="disabled")

    def open_line_geometry_calculator(self) -> None:
        if self._line_geometry_window is not None:
            try:
                if self._line_geometry_window.winfo_exists():
                    self._line_geometry_window.deiconify()
                    self._line_geometry_window.lift()
                    self._line_geometry_window.focus_force()
                    return
            except Exception:
                self._line_geometry_window = None

        win = tk.Toplevel(self)
        self._line_geometry_window = win
        win.title("线路参数计算")
        win.geometry("1260x820")
        win.minsize(1120, 740)

        def _on_close() -> None:
            self._line_geometry_window = None
            self._line_geometry_entries = {}
            self._line_geometry_ground_widgets = []
            self._line_geometry_has_gw_var = None
            self._line_geometry_bundle_var = None
            self._line_geometry_notebook = None
            self._line_geometry_result = None
            self._line_geometry_fig = None
            self._line_geometry_canvas = None
            self._line_geometry_ax = None
            self._cable_geometry_entries = {}
            self._cable_geometry_arrangement_var = None
            self._cable_geometry_sheath_var = None
            self._cable_geometry_bonding_var = None
            self._cable_geometry_return_var = None
            self._cable_geometry_return_override_var = None
            self._cable_geometry_return_widgets = []
            self._cable_geometry_sheath_widgets = []
            win.destroy()

        win.protocol("WM_DELETE_WINDOW", _on_close)

        container = ttk.Frame(win, padding=8)
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=0, minsize=500)
        container.columnconfigure(1, weight=1)
        container.rowconfigure(0, weight=1)

        left = ttk.Frame(container, padding=6)
        right = ttk.Frame(container, padding=6)
        left.grid(row=0, column=0, sticky="nsw", padx=(0, 6), pady=8)
        right.grid(row=0, column=1, sticky="nsew", padx=(6, 0), pady=8)
        left.columnconfigure(0, weight=1)
        left.rowconfigure(2, weight=1)
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)
        right.rowconfigure(2, weight=2)

        ttk.Label(left, text="线路参数计算", font=("TkDefaultFont", 12, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 4)
        )
        intro = (
            "按横截面几何反算线路序参数。架空线页保留原三相坐标、土壤和地线模型；"
            "电缆页新增水平/品字形敷设、绝缘介质和金属护层近似，适合方案前期量级校核。"
        )
        ttk.Label(left, text=intro, wraplength=470, justify="left", foreground="#555555").grid(
            row=1, column=0, sticky="ew", pady=(0, 8)
        )

        notebook = ttk.Notebook(left)
        notebook.grid(row=2, column=0, sticky="nsew")
        self._line_geometry_notebook = notebook
        overhead_tab = ttk.Frame(notebook, padding=6)
        cable_tab = ttk.Frame(notebook, padding=6)
        notebook.add(overhead_tab, text="架空线参数计算")
        notebook.add(cable_tab, text="电缆参数计算")
        self._build_overhead_line_geometry_tab(overhead_tab)
        self._build_cable_geometry_tab(cable_tab)
        notebook.bind("<<NotebookTabChanged>>", lambda _event: self.calculate_line_geometry_popup())

        topbar = ttk.Frame(right)
        topbar.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        topbar.columnconfigure(0, weight=1)
        ttk.Label(topbar, text="计算结果", font=("TkDefaultFont", 11, "bold")).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Button(topbar, text="计算", command=self.calculate_line_geometry_popup).grid(
            row=0, column=1, padx=(4, 0)
        )
        ttk.Button(topbar, text="回填正序到参数页", command=self._fill_line_geometry_to_line_param).grid(
            row=0, column=2, padx=(4, 0)
        )
        ttk.Button(topbar, text="回填序参数到短路页", command=self._fill_line_geometry_to_short_circuit).grid(
            row=0, column=3, padx=(4, 0)
        )

        plot_frame = ttk.LabelFrame(right, text="横截面与参数可视化", padding=4)
        plot_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 8))
        plot_frame.columnconfigure(0, weight=1)
        plot_frame.rowconfigure(0, weight=1)
        self._line_geometry_fig = Figure(figsize=(7.8, 4.4), dpi=100)
        self._line_geometry_ax = self._line_geometry_fig.add_subplot(111)
        self._line_geometry_canvas = FigureCanvasTkAgg(self._line_geometry_fig, master=plot_frame)
        self._line_geometry_canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

        self._line_geometry_result = ScrolledText(right, width=82, height=22, wrap=tk.WORD, font="TkFixedFont")
        self._line_geometry_result.grid(row=2, column=0, sticky="nsew")
        self._line_geometry_result.configure(state="disabled")

        self.calculate_line_geometry_popup()

    def _build_overhead_line_geometry_tab(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        self._line_geometry_entries = {}
        self._line_geometry_ground_widgets = []
        self._line_geometry_bundle_var = tk.StringVar(value="4")
        self._line_geometry_has_gw_var = tk.BooleanVar(value=False)

        def add(frame: ttk.Frame, key: str, row: int, label: str, default: str,
                column: int = 0, width: int = 12) -> ttk.Entry:
            entry = self._add_entry(frame, row, label, default, column=column, width=width)
            self._line_geometry_entries[key] = entry
            return entry

        sec0 = ttk.LabelFrame(parent, text="1）系统与导线数据", padding=6)
        sec0.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        sec0.columnconfigure(1, weight=1)
        sec0.columnconfigure(3, weight=1)
        add(sec0, "f_hz", 0, "频率 f / Hz", "50", column=0)
        add(sec0, "rho", 0, "土壤电阻率 ρ / (Ω·m)", "100", column=2)
        add(sec0, "phase_r_sub", 1, "单分裂导线电阻 r / (Ω/km)", "0.032", column=0)
        add(sec0, "phase_gmr_sub", 1, "单分裂导线 GMR / m", "0.0115", column=2)
        add(sec0, "phase_radius_sub", 2, "单分裂导线半径 r / m", "0.0159", column=0)
        add(sec0, "bundle_spacing", 2, "分裂间距 d / m（n>1）", "0.45", column=2)
        ttk.Label(sec0, text="分裂根数 n（4 根按正方形近似）").grid(row=3, column=0, sticky="w", padx=4, pady=4)
        bundle_box = ttk.Combobox(sec0, width=10, state="readonly", textvariable=self._line_geometry_bundle_var, values=["1", "2", "3", "4"])
        bundle_box.grid(row=3, column=1, sticky="ew", padx=4, pady=4)
        ttk.Label(sec0, text="r / GMR / 半径均指单根子导线数据。", foreground="#666666").grid(
            row=3, column=2, columnspan=2, sticky="w", padx=4, pady=4
        )

        sec1 = ttk.LabelFrame(parent, text="2）三相导线几何坐标", padding=6)
        sec1.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        sec1.columnconfigure(1, weight=1)
        sec1.columnconfigure(3, weight=1)
        add(sec1, "xA", 0, "A 相 x / m", "-12", column=0)
        add(sec1, "hA", 0, "A 相 h / m", "20", column=2)
        add(sec1, "xB", 1, "B 相 x / m", "0", column=0)
        add(sec1, "hB", 1, "B 相 h / m", "20", column=2)
        add(sec1, "xC", 2, "C 相 x / m", "12", column=0)
        add(sec1, "hC", 2, "C 相 h / m", "20", column=2)

        sec2 = ttk.LabelFrame(parent, text="3）地线（可选）", padding=6)
        sec2.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        sec2.columnconfigure(1, weight=1)
        sec2.columnconfigure(3, weight=1)
        ttk.Checkbutton(sec2, text="启用地线并计及屏蔽影响", variable=self._line_geometry_has_gw_var,
                        command=self._on_line_geometry_ground_toggle).grid(row=0, column=0, columnspan=4, sticky="w", padx=4, pady=(0, 4))
        gw_widgets: list[tk.Widget] = []
        gw_widgets.extend([
            add(sec2, "xg", 1, "地线 x / m", "0", column=0),
            add(sec2, "hg", 1, "地线 h / m", "28", column=2),
            add(sec2, "gw_r", 2, "地线电阻 r / (Ω/km)", "0.05", column=0),
            add(sec2, "gw_gmr", 2, "地线 GMR / m", "0.0045", column=2),
            add(sec2, "gw_radius", 3, "地线半径 r / m", "0.005", column=0),
        ])
        ttk.Label(sec2, text="地线按单根连续接地导体处理。", foreground="#666666").grid(
            row=3, column=2, columnspan=2, sticky="w", padx=4, pady=4
        )
        self._line_geometry_ground_widgets = gw_widgets
        self._on_line_geometry_ground_toggle()

    def _build_cable_geometry_tab(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        self._cable_geometry_entries = {}
        self._cable_geometry_arrangement_var = tk.StringVar(value="品字形")
        self._cable_geometry_sheath_var = tk.BooleanVar(value=True)
        self._cable_geometry_bonding_var = tk.StringVar(value="两端接地")
        self._cable_geometry_return_var = tk.StringVar(value="护层+大地并联（PSCAD近似）")
        self._cable_geometry_return_override_var = tk.BooleanVar(value=False)
        self._cable_geometry_return_widgets = []
        self._cable_geometry_sheath_widgets = []

        def add(frame: ttk.Frame, key: str, row: int, label: str, default: str,
                column: int = 0, width: int = 12) -> ttk.Entry:
            entry = self._add_entry(frame, row, label, default, column=column, width=width)
            self._cable_geometry_entries[key] = entry
            return entry

        sec0 = ttk.LabelFrame(parent, text="1）系统与电缆芯线", padding=6)
        sec0.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        sec0.columnconfigure(1, weight=1)
        sec0.columnconfigure(3, weight=1)
        add(sec0, "f_hz", 0, "频率 f / Hz", "50", column=0)
        add(sec0, "u_kv", 0, "额定线电压 U / kV", "10", column=2)
        add(sec0, "rho", 1, "土壤电阻率 ρ / (Ω·m)", "100", column=0)
        add(sec0, "core_r", 1, "导体交流电阻 r / (Ω/km)", "0.0601", column=2)
        add(sec0, "core_gmr", 2, "导体 GMR / m", "0.0065", column=0)
        add(sec0, "core_radius", 2, "导体半径 / m", "0.008", column=2)

        sec1 = ttk.LabelFrame(parent, text="2）绝缘与敷设几何", padding=6)
        sec1.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        sec1.columnconfigure(1, weight=1)
        sec1.columnconfigure(3, weight=1)
        add(sec1, "ins_radius", 0, "绝缘外半径 / m", "0.021", column=0)
        add(sec1, "eps_r", 0, "绝缘相对介电常数 εr", "2.3", column=2)
        add(sec1, "spacing", 1, "相间中心距 / m", "0.12", column=0)
        add(sec1, "depth", 1, "电缆中心埋深 / m", "1.2", column=2)
        ttk.Label(sec1, text="排列方式").grid(row=2, column=0, sticky="w", padx=4, pady=4)
        arrangement_box = ttk.Combobox(sec1, width=10, state="readonly", textvariable=self._cable_geometry_arrangement_var, values=["品字形", "水平排列"])
        arrangement_box.grid(row=2, column=1, sticky="ew", padx=4, pady=4)
        ttk.Label(sec1, text="单芯电缆横截面按实际中心距示意，半径会适当放大以便观察。", foreground="#666666").grid(
            row=2, column=2, columnspan=2, sticky="w", padx=4, pady=4
        )

        sec2 = ttk.LabelFrame(parent, text="3）金属护层 / 屏蔽", padding=6)
        sec2.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        sec2.columnconfigure(1, weight=1)
        sec2.columnconfigure(3, weight=1)
        ttk.Checkbutton(sec2, text="启用金属护层并用于零序回流近似", variable=self._cable_geometry_sheath_var,
                        command=self._on_cable_geometry_sheath_toggle).grid(row=0, column=0, columnspan=4, sticky="w", padx=4, pady=(0, 4))
        sheath_widgets: list[tk.Widget] = []
        sheath_widgets.extend([
            add(sec2, "sheath_r", 1, "护层电阻 r / (Ω/km)", "0.20", column=0),
            add(sec2, "sheath_radius", 1, "护层平均半径 / m", "0.024", column=2),
        ])
        ttk.Label(sec2, text="护层接地方式").grid(row=2, column=0, sticky="w", padx=4, pady=4)
        bonding_box = ttk.Combobox(sec2, width=10, state="readonly", textvariable=self._cable_geometry_bonding_var, values=["两端接地", "交叉互联", "单端接地"])
        bonding_box.grid(row=2, column=1, sticky="ew", padx=4, pady=4)
        sheath_widgets.append(bonding_box)
        ttk.Label(sec2, text="零序模型").grid(row=3, column=0, sticky="w", padx=4, pady=4)
        ttk.Label(
            sec2,
            text="按接地方式自动推断：单端/无护层→大地回流；两端/交叉互联→护层+大地并联（PSCAD/Kron）。",
            foreground="#666666",
            wraplength=420,
            justify="left",
        ).grid(row=3, column=1, columnspan=3, sticky="w", padx=4, pady=4)
        override_box = ttk.Checkbutton(
            sec2,
            text="高级：手动指定零序模型",
            variable=self._cable_geometry_return_override_var,
            command=self._on_cable_geometry_return_override_toggle,
        )
        override_box.grid(row=4, column=0, sticky="w", padx=4, pady=4)
        return_box = ttk.Combobox(
            sec2,
            width=24,
            state="readonly",
            textvariable=self._cable_geometry_return_var,
            values=["大地回流", "护层回流（同轴下限）", "护层+大地并联（PSCAD近似）"],
        )
        return_box.grid(row=4, column=1, sticky="ew", padx=4, pady=4)
        self._cable_geometry_return_widgets = [return_box]
        self._cable_geometry_sheath_widgets = sheath_widgets
        self._on_cable_geometry_sheath_toggle()

    def _active_line_geometry_kind(self) -> str:
        if self._line_geometry_notebook is None:
            return "overhead"
        try:
            return "cable" if self._line_geometry_notebook.index("current") == 1 else "overhead"
        except Exception:
            return "overhead"

    def _on_line_geometry_ground_toggle(self) -> None:
        enabled = bool(self._line_geometry_has_gw_var and self._line_geometry_has_gw_var.get())
        self._set_enabled(self._line_geometry_ground_widgets, enabled)

    def _on_cable_geometry_sheath_toggle(self) -> None:
        enabled = bool(self._cable_geometry_sheath_var and self._cable_geometry_sheath_var.get())
        self._set_enabled(self._cable_geometry_sheath_widgets, enabled)
        self._on_cable_geometry_return_override_toggle()

    def _on_cable_geometry_return_override_toggle(self) -> None:
        override = bool(self._cable_geometry_return_override_var and self._cable_geometry_return_override_var.get())
        self._set_enabled(self._cable_geometry_return_widgets, override)

    def _read_line_geometry_inputs(self) -> dict[str, object]:
        if not self._line_geometry_entries:
            raise InputError("架空线参数计算窗口尚未初始化。")

        name_map = {
            "f_hz": "频率", "rho": "土壤电阻率", "phase_r_sub": "单分裂导线电阻",
            "phase_gmr_sub": "单分裂导线 GMR", "phase_radius_sub": "单分裂导线半径", "bundle_spacing": "分裂间距",
            "xA": "A 相 x", "hA": "A 相 h", "xB": "B 相 x", "hB": "B 相 h", "xC": "C 相 x", "hC": "C 相 h",
            "xg": "地线 x", "hg": "地线 h", "gw_r": "地线电阻", "gw_gmr": "地线 GMR", "gw_radius": "地线半径",
        }
        base_keys = ["f_hz", "rho", "phase_r_sub", "phase_gmr_sub", "phase_radius_sub", "bundle_spacing", "xA", "hA", "xB", "hB", "xC", "hC"]
        vals = {key: _safe_float(self._line_geometry_entries[key].get(), name_map.get(key, key)) for key in base_keys}
        if self._line_geometry_bundle_var is None:
            raise InputError("分裂根数控件未初始化。")
        try:
            bundle_count = int(self._line_geometry_bundle_var.get().strip())
        except Exception as exc:
            raise InputError("分裂根数必须为 1、2、3、4。") from exc
        has_ground = bool(self._line_geometry_has_gw_var and self._line_geometry_has_gw_var.get())
        if has_ground:
            for key in ["xg", "hg", "gw_r", "gw_gmr", "gw_radius"]:
                vals[key] = _safe_float(self._line_geometry_entries[key].get(), name_map.get(key, key))
        return {
            "frequency_hz": vals["f_hz"],
            "soil_resistivity_ohm_m": vals["rho"],
            "phase_positions": [(vals["xA"], vals["hA"]), (vals["xB"], vals["hB"]), (vals["xC"], vals["hC"])],
            "phase_resistance_ohm_per_km": vals["phase_r_sub"],
            "phase_gmr_m": vals["phase_gmr_sub"],
            "phase_radius_m": vals["phase_radius_sub"],
            "phase_bundle_count": bundle_count,
            "phase_bundle_spacing_m": vals["bundle_spacing"],
            "has_ground_wire": has_ground,
            "ground_wire_position": (vals["xg"], vals["hg"]) if has_ground else None,
            "ground_wire_resistance_ohm_per_km": vals["gw_r"] if has_ground else 0.0,
            "ground_wire_gmr_m": vals["gw_gmr"] if has_ground else 0.0,
            "ground_wire_radius_m": vals["gw_radius"] if has_ground else 0.0,
        }

    def _read_cable_geometry_inputs(self) -> dict[str, object]:
        if not self._cable_geometry_entries:
            raise InputError("电缆参数计算窗口尚未初始化。")
        name_map = {
            "f_hz": "频率",
            "u_kv": "额定线电压",
            "rho": "土壤电阻率",
            "core_r": "导体交流电阻",
            "core_gmr": "导体 GMR",
            "core_radius": "导体半径",
            "ins_radius": "绝缘外半径",
            "eps_r": "绝缘相对介电常数",
            "spacing": "相间中心距",
            "depth": "电缆中心埋深",
            "sheath_r": "护层电阻",
            "sheath_radius": "护层平均半径",
        }
        vals = {
            key: _safe_float(entry.get(), name_map.get(key, key))
            for key, entry in self._cable_geometry_entries.items()
        }
        sheath_enabled = bool(self._cable_geometry_sheath_var and self._cable_geometry_sheath_var.get())
        arrangement_text = self._cable_geometry_arrangement_var.get() if self._cable_geometry_arrangement_var else "品字形"
        bonding_text = self._cable_geometry_bonding_var.get() if self._cable_geometry_bonding_var else "两端接地"
        return_text = self._cable_geometry_return_var.get() if self._cable_geometry_return_var else "护层+大地并联（PSCAD近似）"
        override_return = bool(self._cable_geometry_return_override_var and self._cable_geometry_return_override_var.get())
        arrangement_code = {
            "水平排列": "flat",
            "品字形": "trefoil",
        }.get(arrangement_text, str(arrangement_text).strip().lower())
        bonding_code = {
            "两端接地": "both_ends",
            "交叉互联": "cross_bonded",
            "单端接地": "single_point",
            "未启用": "disabled",
        }.get(bonding_text, str(bonding_text).strip().lower())
        return_code = "auto"
        if override_return:
            return_code = {
                "大地回流": "earth",
                "护层回流（同轴下限）": "sheath",
                "护层+大地并联（PSCAD近似）": "sheath_earth",
            }.get(return_text, str(return_text).strip().lower())
        return {
            "frequency_hz": vals["f_hz"],
            "rated_voltage_kv": vals["u_kv"],
            "soil_resistivity_ohm_m": vals["rho"],
            "arrangement": arrangement_code,
            "phase_spacing_m": vals["spacing"],
            "burial_depth_m": vals["depth"],
            "conductor_resistance_ohm_per_km": vals["core_r"],
            "conductor_gmr_m": vals["core_gmr"],
            "conductor_radius_m": vals["core_radius"],
            "insulation_outer_radius_m": vals["ins_radius"],
            "relative_permittivity": vals["eps_r"],
            "sheath_enabled": sheath_enabled,
            "sheath_bonding": bonding_code,
            "zero_sequence_return": return_code,
            "sheath_resistance_ohm_per_km": vals["sheath_r"] if sheath_enabled else 0.0,
            "sheath_radius_m": vals["sheath_radius"] if sheath_enabled else vals["ins_radius"] * 1.05,
        }


    @staticmethod
    def _format_line_geometry_complex(z: complex, unit: str, digits: int = 6) -> str:
        sign = "+" if z.imag >= 0 else "-"
        return f"{z.real:.{digits}f} {sign} j{abs(z.imag):.{digits}f} {unit}"

    def calculate_line_geometry_popup(self) -> None:
        try:
            if self._line_geometry_result is None:
                raise InputError("线路参数计算结果窗口未初始化。")
            if self._active_line_geometry_kind() == "cable":
                inputs = self._read_cable_geometry_inputs()
                result = calculate_cable_sequence(**inputs)
                self._line_geometry_last_result = result
                self._set_text(self._line_geometry_result, self._format_cable_geometry_result(result))
                self._draw_cable_geometry_schematic(result)
            else:
                inputs = self._read_line_geometry_inputs()
                result = calculate_overhead_line_sequence(**inputs)
                self._line_geometry_last_result = result
                self._set_text(self._line_geometry_result, self._format_overhead_line_geometry_result(result))
                self._draw_line_geometry_schematic(inputs, result)
        except Exception as exc:
            messagebox.showerror("计算错误", str(exc))

    def _format_overhead_line_geometry_result(self, result) -> str:
        mode = "有地线" if result.has_ground_wire else "无地线"
        return (
            f"架空线参数计算：{mode}，f = {result.frequency_hz:.4g} Hz，ρ = {result.soil_resistivity_ohm_m:.4g} Ω·m\n"
            f"\n── 几何与等效数据 ───────────────────────────\n"
            f"AB 间距 = {result.D_ab_m:.6f} m\n"
            f"BC 间距 = {result.D_bc_m:.6f} m\n"
            f"CA 间距 = {result.D_ca_m:.6f} m\n"
            f"分裂根数 n = {result.phase_bundle_count:d}\n"
            f"等效相导线电阻 = {result.phase_bundle_resistance_ohm_per_km:.6f} Ω/km\n"
            f"等效相导线 GMR = {result.phase_bundle_gmr_m:.6f} m\n"
            f"等效相导线半径 = {result.phase_bundle_radius_m:.6f} m\n"
            f"\n── 每相、每公里的序参数 ───────────────────────\n"
            f"Z1 = {self._format_line_geometry_complex(result.Z1_ohm_per_km, 'Ω/km')}\n"
            f"Z0 = {self._format_line_geometry_complex(result.Z0_ohm_per_km, 'Ω/km')}\n"
            f"Y1 = {self._format_line_geometry_complex(result.Y1_S_per_km, 'S/km', 8)}\n"
            f"Y0 = {self._format_line_geometry_complex(result.Y0_S_per_km, 'S/km', 8)}\n"
            f"C1 = {result.C1_uF_per_km:.6f} μF/km\n"
            f"C0 = {result.C0_uF_per_km:.6f} μF/km\n"
            f"B1 = {result.B1_uS_per_km:.6f} μS/km\n"
            f"B0 = {result.B0_uS_per_km:.6f} μS/km\n"
            f"\n结论：正序参数可回填参数页，零序参数可同步回填短路电流计算页。\n"
            f"\n说明：\n{result.notes}"
        )

    def _format_cable_geometry_result(self, result) -> str:
        sheath = "启用" if result.sheath_enabled else "未启用"
        return (
            f"电缆参数计算：{result.arrangement}，f = {result.frequency_hz:.4g} Hz，U = {result.rated_voltage_kv:.4g} kV，ρ = {result.soil_resistivity_ohm_m:.4g} Ω·m\n"
            f"\n── 几何、绝缘与护层数据 ───────────────────────\n"
            f"AB / BC / CA = {result.D_ab_m:.6f} / {result.D_bc_m:.6f} / {result.D_ca_m:.6f} m\n"
            f"等效相间距 Deq = {result.D_eq_m:.6f} m\n"
            f"电缆中心埋深 = {result.burial_depth_m:.6f} m\n"
            f"导体 r / GMR / 半径 = {result.conductor_resistance_ohm_per_km:.6f} Ω/km / {result.conductor_gmr_m:.6f} m / {result.conductor_radius_m:.6f} m\n"
            f"绝缘外半径 = {result.insulation_outer_radius_m:.6f} m，εr = {result.relative_permittivity:.4g}\n"
            f"金属护层 = {sheath}，接地方式 = {result.sheath_bonding}\n"
            f"零序回流方式 = {result.zero_sequence_return}\n"
            f"护层电阻 / 半径 = {result.sheath_resistance_ohm_per_km:.6f} Ω/km / {result.sheath_radius_m:.6f} m\n"
            f"\n── 每相、每公里的序参数 ───────────────────────\n"
            f"Z1 = {self._format_line_geometry_complex(result.Z1_ohm_per_km, 'Ω/km')}\n"
            f"Z0 = {self._format_line_geometry_complex(result.Z0_ohm_per_km, 'Ω/km')}\n"
            f"Y1 = {self._format_line_geometry_complex(result.Y1_S_per_km, 'S/km', 8)}\n"
            f"Y0 = {self._format_line_geometry_complex(result.Y0_S_per_km, 'S/km', 8)}\n"
            f"C1 = {result.C1_uF_per_km:.6f} μF/km\n"
            f"C0 = {result.C0_uF_per_km:.6f} μF/km\n"
            f"B1 = {result.B1_uS_per_km:.6f} μS/km\n"
            f"B0 = {result.B0_uS_per_km:.6f} μS/km\n"
            f"额定电压下充电电流 ≈ {result.charging_current_A_per_km:.6f} A/km\n"
            f"\n结论：Z1/C1 可回填参数页；Z1/Z0 可回填短路电流计算页。\n"
            f"\n说明：\n{result.notes}"
        )

    def _draw_line_geometry_schematic(self, inputs: dict[str, object], result) -> None:
        if self._line_geometry_fig is None or self._line_geometry_canvas is None:
            return
        self._line_geometry_fig.clear()
        ax = self._line_geometry_fig.add_subplot(111)
        self._line_geometry_ax = ax
        ax.set_facecolor("#f8fafc")
        ax.set_title("架空线横截面：按输入几何尺寸等比例绘制", fontsize=11, pad=10)

        phase_positions = list(inputs["phase_positions"])
        has_ground = bool(inputs["has_ground_wire"])
        ground_position = inputs["ground_wire_position"] if has_ground else None
        radius = max(float(inputs["phase_radius_m"]), float(inputs.get("ground_wire_radius_m", 0.0) or 0.0), 0.12)
        all_points = phase_positions + ([ground_position] if ground_position is not None else [])
        xs = [pt[0] for pt in all_points]
        ys = [pt[1] for pt in all_points]
        x_min, x_max = min(xs), max(xs)
        y_max = max(ys)
        x_pad = max(2.0, 0.15 * max(1.0, x_max - x_min), radius * 6.0)
        y_pad = max(2.0, 0.15 * max(1.0, y_max), radius * 8.0)

        ax.axhline(0.0, color="#5b6470", linewidth=2.0, linestyle="-")
        ax.fill_between([x_min - x_pad, x_max + x_pad], -y_pad * 0.22, 0.0, color="#dde6ef", alpha=0.85)
        ax.text(x_min - x_pad * 0.95, 0.35, "地平面", color="#3a4756", fontsize=9, ha="left", va="bottom")

        phase_colors = [("A相导线", "#4f8ef7"), ("B相导线", "#ffb020"), ("C相导线", "#ff6b6b")]
        legend_handles = []
        for (label, color), (x, y) in zip(phase_colors, phase_positions):
            circle = Circle((x, y), radius=radius, facecolor=color, edgecolor="#1f2933", linewidth=1.2, zorder=3)
            ax.add_patch(circle)
            ax.text(x, y + radius * 1.7, label.replace("导线", ""), ha="center", va="bottom", fontsize=9, color=color, fontweight="bold")
            legend_handles.append(Line2D([0], [0], marker="o", linestyle="", markerfacecolor=color, markeredgecolor="#1f2933", markersize=8, label=label))
            self._draw_vertical_dimension(ax, x, y, f"h={y:.2f} m", color=color)

        if ground_position is not None:
            gx, gy = ground_position
            g_radius = max(float(inputs.get("ground_wire_radius_m", 0.0) or 0.0), radius * 0.7)
            circle = Circle((gx, gy), radius=g_radius, facecolor="#6b7280", edgecolor="#1f2933", linewidth=1.2, zorder=3)
            ax.add_patch(circle)
            ax.text(gx, gy + g_radius * 1.7, "地线", ha="center", va="bottom", fontsize=9, color="#374151", fontweight="bold")
            legend_handles.append(Line2D([0], [0], marker="o", linestyle="", markerfacecolor="#6b7280", markeredgecolor="#1f2933", markersize=8, label="地线"))
            self._draw_vertical_dimension(ax, gx, gy, f"h={gy:.2f} m", color="#4b5563", x_offset=max(radius * 2.0, 0.8))

        xa, ya = phase_positions[0]
        xb, yb = phase_positions[1]
        xc, yc = phase_positions[2]
        self._draw_dimension_line(ax, (xa, ya), (xb, yb), f"AB={result.D_ab_m:.2f} m", "#2563eb")
        self._draw_dimension_line(ax, (xb, yb), (xc, yc), f"BC={result.D_bc_m:.2f} m", "#d97706")
        self._draw_dimension_line(ax, (xa, ya), (xc, yc), f"CA={result.D_ca_m:.2f} m", "#dc2626", text_offset=1.2)

        ax.set_xlim(x_min - x_pad, x_max + x_pad)
        ax.set_ylim(-y_pad * 0.22, y_max + y_pad)
        ax.set_aspect("equal", adjustable="box")
        ax.grid(True, linestyle="--", linewidth=0.7, alpha=0.35)
        ax.set_xlabel("横坐标 x / m")
        ax.set_ylabel("高度 h / m")
        ax.legend(handles=legend_handles, loc="upper right", frameon=True, fontsize=9)
        self._line_geometry_fig.tight_layout()
        self._line_geometry_canvas.draw()

    def _draw_cable_geometry_schematic(self, result) -> None:
        if self._line_geometry_fig is None or self._line_geometry_canvas is None:
            return
        self._line_geometry_fig.clear()
        ax = self._line_geometry_fig.add_subplot(1, 2, 1)
        bar_ax = self._line_geometry_fig.add_subplot(1, 2, 2)
        self._line_geometry_ax = ax
        ax.set_facecolor("#f8fafc")
        ax.set_title("电缆沟横截面", fontsize=11, pad=10)

        positions = list(result.phase_positions_m)
        xs = [p[0] for p in positions]
        depths = [p[1] for p in positions]
        display_r = max(result.insulation_outer_radius_m, result.phase_spacing_m * 0.18, 0.035)
        x_pad = max(0.28, result.phase_spacing_m * 1.25)
        y_pad = max(0.25, result.phase_spacing_m * 1.2)
        x_min = min(xs) - x_pad
        x_max = max(xs) + x_pad
        y_bottom = -(max(depths) + y_pad)

        ax.add_patch(Rectangle((x_min, y_bottom), x_max - x_min, -y_bottom, facecolor="#e5edf5", edgecolor="#c5d2df", linewidth=1.0, zorder=0))
        ax.axhline(0.0, color="#5b6470", linewidth=2.0)
        ax.text(x_min + 0.02, 0.035, "地表", color="#3a4756", fontsize=9, ha="left", va="bottom")

        phase_colors = [("A", "#4f8ef7"), ("B", "#ffb020"), ("C", "#ff6b6b")]
        legend_handles = []
        for (name, color), (x, depth) in zip(phase_colors, positions):
            y = -depth
            ax.add_patch(Circle((x, y), display_r * 1.12, facecolor="#1f2937", edgecolor="#111827", linewidth=0.8, alpha=0.92, zorder=2))
            if result.sheath_enabled:
                ax.add_patch(Circle((x, y), display_r * 0.94, facecolor="#cbd5e1", edgecolor="#64748b", linewidth=0.8, zorder=3))
            ax.add_patch(Circle((x, y), display_r * 0.72, facecolor="#fff7d6", edgecolor="#f59e0b", linewidth=0.8, zorder=4))
            ax.add_patch(Circle((x, y), display_r * 0.36, facecolor=color, edgecolor="#1f2933", linewidth=0.9, zorder=5))
            ax.text(x, y + display_r * 1.55, f"{name}相", ha="center", va="bottom", fontsize=9, color=color, fontweight="bold")
            legend_handles.append(Line2D([0], [0], marker="o", linestyle="", markerfacecolor=color, markeredgecolor="#1f2933", markersize=8, label=f"{name}相芯线"))
            self._draw_vertical_dimension(ax, x + display_r * 1.55, depth, f"埋深={depth:.2f} m", color="#475569", x_offset=0.0)

        self._draw_dimension_line(ax, (positions[0][0], -positions[0][1]), (positions[1][0], -positions[1][1]), f"AB={result.D_ab_m:.2f} m", "#2563eb", text_offset=0.08)
        self._draw_dimension_line(ax, (positions[1][0], -positions[1][1]), (positions[2][0], -positions[2][1]), f"BC={result.D_bc_m:.2f} m", "#d97706", text_offset=0.08)
        if result.arrangement == "品字形":
            self._draw_dimension_line(ax, (positions[0][0], -positions[0][1]), (positions[2][0], -positions[2][1]), f"CA={result.D_ca_m:.2f} m", "#dc2626", text_offset=0.12)

        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_bottom, 0.16)
        ax.set_aspect("equal", adjustable="box")
        ax.grid(True, linestyle="--", linewidth=0.7, alpha=0.3)
        ax.set_xlabel("横坐标 x / m")
        ax.set_ylabel("深度 / m")
        ax.legend(handles=legend_handles, loc="lower left", frameon=True, fontsize=8)

        labels = ["R1", "X1", "R0", "X0", "C1", "C0"]
        values = [
            result.Z1_ohm_per_km.real,
            result.Z1_ohm_per_km.imag,
            result.Z0_ohm_per_km.real,
            result.Z0_ohm_per_km.imag,
            result.C1_uF_per_km,
            result.C0_uF_per_km,
        ]
        colors = ["#3b82f6", "#60a5fa", "#ef4444", "#f87171", "#10b981", "#34d399"]
        y_pos = list(range(len(labels)))
        bar_ax.barh(y_pos, values, color=colors, alpha=0.88)
        bar_ax.set_yticks(y_pos, labels)
        bar_ax.invert_yaxis()
        bar_ax.set_title("关键参数", fontsize=11, pad=10)
        bar_ax.set_xlabel("Ω/km 或 μF/km")
        bar_ax.grid(True, axis="x", linestyle="--", alpha=0.3)
        max_value = max(values) if values else 1.0
        for idx, value in enumerate(values):
            bar_ax.text(value + max_value * 0.025, idx, f"{value:.4g}", va="center", fontsize=8.5)
        bar_ax.text(0.0, 1.03, f"Ic≈{result.charging_current_A_per_km:.3g} A/km", transform=bar_ax.transAxes, fontsize=9, color="#334155")

        self._line_geometry_fig.tight_layout()
        self._line_geometry_canvas.draw()

    @staticmethod
    def _draw_vertical_dimension(ax, x: float, y: float, label: str, color: str, x_offset: float = 0.0) -> None:
        x_dim = x + x_offset
        ax.annotate("", xy=(x_dim, y), xytext=(x_dim, 0.0), arrowprops=dict(arrowstyle="<->", color=color, linewidth=1.1))
        ax.plot([x, x_dim], [y, y], color=color, linewidth=0.9, linestyle=":")
        ax.text(x_dim + 0.018, y / 2.0, label, color=color, fontsize=8.5, va="center", ha="left",
                bbox=dict(boxstyle="round,pad=0.18", facecolor="white", edgecolor="none", alpha=0.75))

    @staticmethod
    def _draw_dimension_line(ax, p1: tuple[float, float], p2: tuple[float, float], label: str, color: str, text_offset: float = 0.7) -> None:
        x1, y1 = p1
        x2, y2 = p2
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="<->", color=color, linewidth=1.2))
        mx = (x1 + x2) / 2.0
        my = (y1 + y2) / 2.0
        dx = x2 - x1
        dy = y2 - y1
        length = max((dx ** 2 + dy ** 2) ** 0.5, 1e-9)
        nx = -dy / length
        ny = dx / length
        ax.text(mx + nx * text_offset, my + ny * text_offset, label, color=color, fontsize=8.5, ha="center", va="center",
                bbox=dict(boxstyle="round,pad=0.18", facecolor="white", edgecolor="none", alpha=0.8))

    @staticmethod
    def _replace_entry(entry: ttk.Entry, value: float, fmt: str = ".6g") -> None:
        entry.delete(0, tk.END)
        entry.insert(0, format(value, fmt))

    def _fill_line_geometry_to_line_param(self) -> None:
        result = self._line_geometry_last_result
        if result is None:
            messagebox.showwarning("尚未计算", "请先在“线路参数计算”窗口中完成计算。")
            return
        self._replace_entry(self.lp_r1, result.Z1_ohm_per_km.real)
        self._replace_entry(self.lp_x1, result.Z1_ohm_per_km.imag)
        self._replace_entry(self.lp_c1, result.C1_uF_per_km)
        self.calculate_line_param()

    def _fill_line_geometry_to_short_circuit(self) -> None:
        result = self._line_geometry_last_result
        if result is None:
            messagebox.showwarning("尚未计算", "请先在“线路参数计算”窗口中完成计算。")
            return
        self._replace_entry(self.sc_r1, result.Z1_ohm_per_km.real)
        self._replace_entry(self.sc_x1, result.Z1_ohm_per_km.imag)
        self._replace_entry(self.sc_r0, result.Z0_ohm_per_km.real)
        self._replace_entry(self.sc_x0, result.Z0_ohm_per_km.imag)
        self._on_sc_neutral_mode_change()

    def calculate_line_param(self) -> None:
        try:
            R1    = _safe_float(self.lp_r1.get(),    "R₁")
            X1    = _safe_float(self.lp_x1.get(),    "X₁")
            C1    = _safe_float(self.lp_c1.get(),    "C₁")
            length = _safe_float(self.lp_len.get(),  "线路长度")
            Sbase = _safe_float(self.lp_sbase.get(), "Sbase")
            Ubase = _safe_float(self.lp_ubase.get(), "Ubase")

            r = convert_line_to_pu(R1, X1, C1, length, Sbase, Ubase)

            text = (
                f"══ 有名值（π型等值，折算后）══════════════════════\n"
                f"  总电阻  R  = {r.R_total_ohm:.6f} Ω\n"
                f"  总电抗  X  = {r.X_total_ohm:.6f} Ω\n"
                f"  对地电纳半值 B/2 = {r.B_half_S:.8f} S\n"
                f"  波阻抗  Zc = {r.Zc_ohm:.4f} Ω\n"
                f"\n══ 标幺值（Sbase={Sbase:.4g} MVA，Ubase={Ubase:.4g} kV）══════\n"
                f"  基准阻抗 Zbase = {r.Zbase_ohm:.4f} Ω，  "
                f"基准导纳 Ybase = {r.Ybase_S:.8f} S\n"
                f"  R_pu   = {r.R_pu:.8f}  pu\n"
                f"  X_pu   = {r.X_pu:.8f}  pu\n"
                f"  B/2_pu = {r.B_half_pu:.8f}  pu\n"
                f"\n══ 参数校核 ═══════════════════════════════════════\n"
                + _format_warnings(r.warnings)
            )
            self._set_text(self.lp_result, text)

        except Exception as exc:
            messagebox.showerror("计算错误", str(exc))

    def calculate_2wt(self) -> None:
        try:
            Pk    = _safe_float(self.tx2_pk.get(),    "Pk")
            Uk    = _safe_float(self.tx2_uk.get(),    "Uk%")
            P0    = _safe_float(self.tx2_p0.get(),    "P0")
            I0    = _safe_float(self.tx2_i0.get(),    "I0%")
            SN    = _safe_float(self.tx2_sn.get(),    "SN")
            UN    = _safe_float(self.tx2_un.get(),    "UN")
            Sbase = _safe_float(self.tx2_sbase.get(), "Sbase")
            Ubase = _safe_float(self.tx2_ubase.get(), "Ubase")

            r = convert_2wt_to_pu(Pk, Uk, P0, I0, SN, UN, Sbase, Ubase)

            text = (
                f"══ 有名值（折算到高压侧 {UN:.4g} kV）══════════════════\n"
                f"  短路电阻   Rk  = {r.Rk_ohm:.6f}  Ω\n"
                f"  短路电抗   Xk  = {r.Xk_ohm:.6f}  Ω\n"
                f"  励磁电导   G₀  = {r.G0_S:.2e}  S\n"
                f"  励磁电纳   B₀  = {r.B0_S:.2e}  S\n"
                f"\n══ 标幺值（Sbase={Sbase:.4g} MVA，Ubase={Ubase:.4g} kV）══════\n"
                f"  基准阻抗 Zbase = {r.Zbase_ohm:.4f} Ω\n"
                f"  Rk_pu  = {r.Rk_pu:.8f}  pu\n"
                f"  Xk_pu  = {r.Xk_pu:.8f}  pu\n"
                f"  G₀_pu  = {r.G0_pu:.8f}  pu\n"
                f"  B₀_pu  = {r.B0_pu:.8f}  pu\n"
                f"  （反算 Uk% ≈ {r.Uk_pct_check:.4f}%，输入 {Uk:.4f}%）\n"
                f"\n══ 参数校核 ═══════════════════════════════════════\n"
                + _format_warnings(r.warnings)
            )
            self._set_text(self.tx2_result, text)

        except Exception as exc:
            messagebox.showerror("计算错误", str(exc))

    def calculate_3wt(self) -> None:
        try:
            Pk_HM  = _safe_float(self.tx3_pk_hm.get(),  "Pk_HM")
            Pk_HL  = _safe_float(self.tx3_pk_hl.get(),  "Pk_HL")
            Pk_ML  = _safe_float(self.tx3_pk_ml.get(),  "Pk_ML")
            Uk_HM  = _safe_float(self.tx3_uk_hm.get(),  "Uk_HM%")
            Uk_HL  = _safe_float(self.tx3_uk_hl.get(),  "Uk_HL%")
            Uk_ML  = _safe_float(self.tx3_uk_ml.get(),  "Uk_ML%")
            P0     = _safe_float(self.tx3_p0.get(),     "P0")
            I0     = _safe_float(self.tx3_i0.get(),     "I0%")
            SN_H   = _safe_float(self.tx3_sn_h.get(),   "SN_H")
            SN_M   = _safe_float(self.tx3_sn_m.get(),   "SN_M")
            SN_L   = _safe_float(self.tx3_sn_l.get(),   "SN_L")
            UN_H   = _safe_float(self.tx3_un_h.get(),   "UN_H")
            Sbase  = _safe_float(self.tx3_sbase.get(),  "Sbase")
            Ubase  = _safe_float(self.tx3_ubase.get(),  "Ubase")

            r = convert_3wt_to_pu(
                Pk_HM, Pk_HL, Pk_ML,
                Uk_HM, Uk_HL, Uk_ML,
                P0, I0,
                SN_H, SN_M, SN_L, UN_H,
                Sbase, Ubase)

            SN_base = SN_H
            text = (
                f"══ 折算参考容量 SN_base = {SN_base:.4g} MVA，折算基压 {UN_H:.4g} kV ══════\n"
                f"\n── 有名值（T型等值，折算到高压侧）────────────────────\n"
                f"  高压绕组  RH = {r.RH_ohm:.6f} Ω，  XH = {r.XH_ohm:.6f} Ω\n"
                f"  中压绕组  RM = {r.RM_ohm:.6f} Ω，  XM = {r.XM_ohm:.6f} Ω\n"
                f"  低压绕组  RL = {r.RL_ohm:.6f} Ω，  XL = {r.XL_ohm:.6f} Ω\n"
                f"\n── 标幺值（Sbase={Sbase:.4g} MVA，Ubase={Ubase:.4g} kV）─────────────\n"
                f"  基准阻抗 Zbase = {r.Zbase_ohm:.4f} Ω\n"
                f"  高压绕组  RH_pu = {r.RH_pu:.8f}，  XH_pu = {r.XH_pu:.8f}\n"
                f"  中压绕组  RM_pu = {r.RM_pu:.8f}，  XM_pu = {r.XM_pu:.8f}\n"
                f"  低压绕组  RL_pu = {r.RL_pu:.8f}，  XL_pu = {r.XL_pu:.8f}\n"
                f"  励磁电导  G₀_pu = {r.G0_pu:.8f}，  励磁电纳 B₀_pu = {r.B0_pu:.8f}\n"
                f"\n══ 参数校核 ═══════════════════════════════════════\n"
                + _format_warnings(r.warnings)
            )
            self._set_text(self.tx3_result, text)

        except Exception as exc:
            messagebox.showerror("计算错误", str(exc))
