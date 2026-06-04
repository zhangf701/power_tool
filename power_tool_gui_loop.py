"""Distribution-network loop-closure GUI mixin. / 配电网合环页面 mixin。"""

from __future__ import annotations

from power_tool_gui_common import *


class LoopClosureGuiMixin:
    def _build_loop_closure_tab(self) -> None:
        self.loop_tab.columnconfigure(1, weight=1)
        self.loop_tab.rowconfigure(0, weight=1)

        left = ttk.Frame(self.loop_tab, padding=16, style="Card.TFrame")
        right = ttk.Frame(self.loop_tab, padding=16, style="Card.TFrame")
        left.grid(row=0, column=0, sticky="nsw", padx=(0, 6), pady=8)
        right.grid(row=0, column=1, sticky="nsew", padx=(6, 0), pady=8)
        right.columnconfigure(0, weight=1)
        right.rowconfigure(2, weight=1)
        right.rowconfigure(4, weight=2)

        ttk.Label(left, text="配电网合环分析", style="PageTitle.TLabel").pack(anchor="w")
        ttk.Label(left, text="输入区分为参数、连接点表与线段比例三部分，图形区则拆成稳态点位图与冲击暂态电流两页。", style="Muted.TLabel", justify="left", wraplength=430).pack(fill="x", pady=(4, 10))

        basic = ttk.LabelFrame(left, text="合环近似参数", style="Card.TLabelframe", padding=10)
        basic.pack(fill="x", expand=False, pady=(0, 8))
        basic.columnconfigure(1, weight=1, minsize=112)
        basic.columnconfigure(3, weight=1, minsize=112)

        self.loop_n = self._add_entry(basic, 0, "连接点数量 N", "7", column=0)
        ttk.Label(basic, text="合环点编号", style="Form.TLabel").grid(row=0, column=2, sticky="w", padx=4, pady=4)
        self.loop_closure = ttk.Combobox(basic, state="readonly", width=10, style="Input.TCombobox")
        self.loop_closure.grid(row=0, column=3, sticky="ew", padx=4, pady=4)
        self.loop_closure.bind("<<ComboboxSelected>>", self._refresh_loop_closure_indicator)

        self.loop_u1 = self._add_entry(basic, 1, "U1 / kV（线电压）", "10", column=0)
        self.loop_u2 = self._add_entry(basic, 1, "U2 / kV（线电压）", "10", column=2)
        self.loop_angle = self._add_entry(basic, 2, "两侧相角差 φ / °", "14", column=0)
        self.loop_freq = self._add_entry(basic, 2, "系统频率 / Hz", "50", column=2)
        self.loop_r = self._add_entry(basic, 3, "回路电阻 RΣ / Ω", "1.13", column=0)
        self.loop_x = self._add_entry(basic, 3, "回路电抗 XΣ / Ω", "4.20", column=2)
        self.loop_total_len = self._add_entry(basic, 4, "总线路长度 / km", "11", column=0)
        self.loop_pf = self._add_entry(basic, 4, "统一功率因数 cosφ", "0.99", column=2)

        ttk.Label(basic, text="功率因数类型", style="Form.TLabel").grid(row=5, column=0, sticky="w", padx=4, pady=4)
        self.loop_pf_mode = ttk.Combobox(basic, state="readonly", values=["滞后", "超前"], width=10, style="Input.TCombobox")
        self.loop_pf_mode.grid(row=5, column=1, sticky="ew", padx=4, pady=4)
        self.loop_pf_mode.set(_display_obj(self, "滞后"))
        self.loop_ampacity = self._add_entry(basic, 5, "额定载流量 / A", "442", column=2)
        self.loop_overload = self._add_entry(basic, 6, "短时过载系数 K", "1.5", column=0)
        self.loop_tclose = self._add_entry(basic, 6, "合环时刻 / s", "0.10", column=2)
        self.loop_tend = self._add_entry(basic, 7, "波形结束时刻 / s", "0.30", column=0)

        tools = ttk.Frame(basic, style="Card.TFrame")
        tools.grid(row=8, column=0, columnspan=4, sticky="ew", padx=4, pady=(6, 2))
        ttk.Button(tools, text="按 N 重建表格", command=self._rebuild_loop_closure_rows).pack(side="left", padx=(0, 6))
        ttk.Button(tools, text="加载默认值", command=self._apply_loop_closure_appendix_defaults).pack(side="left", padx=(0, 6))
        ttk.Button(tools, text="计算并绘图", command=self.calculate_loop_closure, style="Accent.TButton").pack(side="left")

        hint = (
            "输入约定：每个连接点填写净线电流（A）。正值表示负荷，负值表示分布式电源回送，0 表示空点。"
            " 合环点必须对应空点。线段比例默认均匀分布；若输入自定义比例，则按 N+1 个线段比例自动归一。"
        )
        ttk.Label(left, text=hint, justify="left", wraplength=430, style="Muted.TLabel").pack(fill="x", pady=(0, 8))

        table_box = ttk.LabelFrame(left, text="连接点表", style="Card.TLabelframe", padding=8)
        table_box.pack(fill="both", expand=True, pady=(0, 8))

        self.loop_table_canvas = tk.Canvas(table_box, height=265, highlightthickness=0)
        self.loop_table_canvas.pack(side="left", fill="both", expand=True)
        table_scroll = ttk.Scrollbar(table_box, orient="vertical", command=self.loop_table_canvas.yview)
        table_scroll.pack(side="right", fill="y")
        self.loop_table_canvas.configure(yscrollcommand=table_scroll.set)

        self.loop_table_frame = ttk.Frame(self.loop_table_canvas)
        self._loop_table_window = self.loop_table_canvas.create_window((0, 0), window=self.loop_table_frame, anchor="nw")
        self.loop_table_frame.bind("<Configure>", lambda e: self.loop_table_canvas.configure(scrollregion=self.loop_table_canvas.bbox("all")))
        self.loop_table_canvas.bind("<Configure>", lambda e: self.loop_table_canvas.itemconfigure(self._loop_table_window, width=e.width))

        ratio_box = ttk.LabelFrame(left, text="线段比例（N+1 段）", style="Card.TLabelframe", padding=8)
        ratio_box.pack(fill="x", expand=False)
        self.loop_ratio_frame = ttk.Frame(ratio_box)
        self.loop_ratio_frame.pack(fill="x", expand=True)

        self.loop_node_label_entries: list[ttk.Entry] = []
        self.loop_node_current_entries: list[ttk.Entry] = []
        self.loop_node_indicator_labels: list[ttk.Label] = []
        self.loop_ratio_entries: list[ttk.Entry] = []
        self._last_loop_result = None

        ttk.Label(right, text="计算结果", style="PageTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(right, text="右侧统一收纳摘要、点位图与冲击暂态电流波形。", style="Muted.TLabel", justify="left", wraplength=760).grid(row=1, column=0, sticky="ew", pady=(4, 8))
        self.loop_result = ScrolledText(right, width=82, height=18, wrap=tk.WORD, font="TkFixedFont")
        self.loop_result.grid(row=2, column=0, sticky="nsew")
        self.loop_result.configure(state="disabled")

        plot_nb = ttk.Notebook(right)
        plot_nb.grid(row=4, column=0, sticky="nsew", pady=(10, 0))

        profile_page = ttk.Frame(plot_nb, padding=4, style="Card.TFrame")
        wave_page = ttk.Frame(plot_nb, padding=4, style="Card.TFrame")
        plot_nb.add(profile_page, text="点位图与稳态电流")
        plot_nb.add(wave_page, text="冲击暂态电流")
        profile_page.columnconfigure(0, weight=1)
        profile_page.rowconfigure(0, weight=1)
        wave_page.columnconfigure(0, weight=1)
        wave_page.rowconfigure(0, weight=1)

        self.loop_profile_fig = Figure(figsize=(7.4, 3.4), dpi=100)
        self.loop_profile_ax = self.loop_profile_fig.add_subplot(111)
        self.loop_profile_canvas = FigureCanvasTkAgg(self.loop_profile_fig, master=profile_page)
        self.loop_profile_canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        self.loop_profile_toolbar = NavigationToolbar2Tk(self.loop_profile_canvas, profile_page, pack_toolbar=False)
        self.loop_profile_toolbar.update()
        self.loop_profile_toolbar.grid(row=1, column=0, sticky="ew")

        self.loop_wave_fig = Figure(figsize=(7.4, 6.0), dpi=100)
        self.loop_wave_ax1 = self.loop_wave_fig.add_subplot(311)
        self.loop_wave_ax2 = self.loop_wave_fig.add_subplot(312)
        self.loop_wave_ax3 = self.loop_wave_fig.add_subplot(313)
        self.loop_wave_canvas = FigureCanvasTkAgg(self.loop_wave_fig, master=wave_page)
        self.loop_wave_canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        self.loop_wave_toolbar = NavigationToolbar2Tk(self.loop_wave_canvas, wave_page, pack_toolbar=False)
        self.loop_wave_toolbar.update()
        self.loop_wave_toolbar.grid(row=1, column=0, sticky="ew")

        self._rebuild_loop_closure_rows()
        self._apply_loop_closure_appendix_defaults()

    def _refresh_loop_closure_indicator(self, _event: object | None = None) -> None:
        try:
            closure = int(self.loop_closure.get())
        except Exception:
            return
        for idx, label in enumerate(self.loop_node_indicator_labels, start=1):
            if idx == closure:
                label.configure(text="◉ Closure point" if self.language == "en" else "◉ 合环点")
            else:
                label.configure(text="")

    def _rebuild_loop_closure_rows(self) -> None:
        try:
            n = int(round(_safe_float(self.loop_n.get(), "连接点数量 N")))
            if n < 1:
                raise InputError("连接点数量 N 必须为正整数。")
        except Exception as exc:
            messagebox.showerror("输入错误", str(exc))
            return

        old_labels = [entry.get() for entry in self.loop_node_label_entries]
        old_currents = [entry.get() for entry in self.loop_node_current_entries]
        old_ratios = [entry.get() for entry in self.loop_ratio_entries]
        try:
            old_closure = int(self.loop_closure.get())
        except Exception:
            old_closure = min(max(1, n // 2 + 1), n)

        for child in self.loop_table_frame.winfo_children():
            child.destroy()
        for child in self.loop_ratio_frame.winfo_children():
            child.destroy()

        self.loop_node_label_entries = []
        self.loop_node_current_entries = []
        self.loop_node_indicator_labels = []
        self.loop_ratio_entries = []

        ttk.Label(self.loop_table_frame, text="编号", font=("TkDefaultFont", 9, "bold")).grid(row=0, column=0, sticky="w", padx=3, pady=2)
        ttk.Label(self.loop_table_frame, text="标签", font=("TkDefaultFont", 9, "bold")).grid(row=0, column=1, sticky="w", padx=3, pady=2)
        ttk.Label(self.loop_table_frame, text="净电流 / A", font=("TkDefaultFont", 9, "bold")).grid(row=0, column=2, sticky="w", padx=3, pady=2)
        ttk.Label(self.loop_table_frame, text="说明", font=("TkDefaultFont", 9, "bold")).grid(row=0, column=3, sticky="w", padx=3, pady=2)

        for i in range(n):
            ttk.Label(self.loop_table_frame, text=str(i + 1)).grid(row=i + 1, column=0, sticky="w", padx=3, pady=2)
            label_entry = ttk.Entry(self.loop_table_frame, width=10, style="Input.TEntry")
            label_entry.grid(row=i + 1, column=1, sticky="ew", padx=3, pady=2)
            default_label = old_labels[i] if i < len(old_labels) else _display_obj(self, f"点{i + 1}")
            label_entry.insert(0, default_label)

            current_entry = ttk.Entry(self.loop_table_frame, width=12, style="Input.TEntry")
            current_entry.grid(row=i + 1, column=2, sticky="ew", padx=3, pady=2)
            current_entry.insert(0, old_currents[i] if i < len(old_currents) else "0")

            note_lbl = ttk.Label(self.loop_table_frame, text="", style="Muted.TLabel")
            note_lbl.grid(row=i + 1, column=3, sticky="w", padx=3, pady=2)

            self.loop_node_label_entries.append(label_entry)
            self.loop_node_current_entries.append(current_entry)
            self.loop_node_indicator_labels.append(note_lbl)

        closure_values = [str(i) for i in range(1, n + 1)]
        self.loop_closure.configure(values=closure_values)
        self.loop_closure.set(str(min(max(1, old_closure), n)))
        self._refresh_loop_closure_indicator()

        ttk.Label(self.loop_ratio_frame, text="段号", font=("TkDefaultFont", 9, "bold")).grid(row=0, column=0, sticky="w", padx=3, pady=2)
        ttk.Label(self.loop_ratio_frame, text="比例", font=("TkDefaultFont", 9, "bold")).grid(row=0, column=1, sticky="w", padx=3, pady=2)
        for idx in range(n + 1):
            r = idx + 1
            row = 1 + idx // 4
            col = (idx % 4) * 2
            ttk.Label(self.loop_ratio_frame, text=f"r{r}").grid(row=row, column=col, sticky="w", padx=3, pady=2)
            entry = ttk.Entry(self.loop_ratio_frame, width=8, style="Input.TEntry")
            entry.grid(row=row, column=col + 1, sticky="w", padx=3, pady=2)
            entry.insert(0, old_ratios[idx] if idx < len(old_ratios) else "1")
            self.loop_ratio_entries.append(entry)

    def _apply_loop_closure_appendix_defaults(self) -> None:
        defaults = {
            self.loop_n: "7",
            self.loop_u1: "10",
            self.loop_u2: "10",
            self.loop_angle: "14",
            self.loop_freq: "50",
            self.loop_r: "1.13",
            self.loop_x: "4.20",
            self.loop_total_len: "11",
            self.loop_pf: "0.99",
            self.loop_ampacity: "442",
            self.loop_overload: "1.5",
            self.loop_tclose: "0.10",
            self.loop_tend: "0.30",
        }
        for widget, value in defaults.items():
            widget.delete(0, tk.END)
            widget.insert(0, value)

        self.loop_pf_mode.set(_display_obj(self, "滞后"))
        self._rebuild_loop_closure_rows()
        self.loop_closure.set("4")
        self._refresh_loop_closure_indicator()

        labels = ["A", "B", "C", _display_obj(self, "联络点"), "D", "E", "F"]
        injections = [79.35, 117.40, 116.60, 0.0, 136.69, 58.81, 158.66]
        for entry, label in zip(self.loop_node_label_entries, labels):
            entry.delete(0, tk.END)
            entry.insert(0, label)
        for entry, value in zip(self.loop_node_current_entries, injections):
            entry.delete(0, tk.END)
            entry.insert(0, f"{value:.2f}")
        for entry in self.loop_ratio_entries:
            entry.delete(0, tk.END)
            entry.insert(0, "1")

        self.calculate_loop_closure()

    def _read_loop_closure_inputs(self):
        n = int(round(_safe_float(self.loop_n.get(), "连接点数量 N")))
        if n < 1:
            raise InputError("连接点数量 N 必须为正整数。")
        if len(self.loop_node_current_entries) != n or len(self.loop_ratio_entries) != n + 1:
            raise InputError("连接点表或线段比例与当前 N 不一致，请先点击“按 N 重建表格”。")

        closure = int(self.loop_closure.get())
        node_labels = [entry.get().strip() or f"点{i}" for i, entry in enumerate(self.loop_node_label_entries, start=1)]
        node_currents = [_safe_float(entry.get(), f"连接点 {i} 净电流") for i, entry in enumerate(self.loop_node_current_entries, start=1)]
        ratios = [_safe_float(entry.get(), f"线段比例 r{i}") for i, entry in enumerate(self.loop_ratio_entries, start=1)]

        ampacity_text = self.loop_ampacity.get().strip()
        ampacity = None if ampacity_text == "" else _safe_float(ampacity_text, "额定载流量")

        result = loop_closure_analysis(
            u1_kv_ll=_safe_float(self.loop_u1.get(), "U1"),
            u2_kv_ll=_safe_float(self.loop_u2.get(), "U2"),
            angle_deg=_safe_float(self.loop_angle.get(), "两侧相角差 φ"),
            r_loop_ohm=_safe_float(self.loop_r.get(), "回路电阻 RΣ"),
            x_loop_ohm=_safe_float(self.loop_x.get(), "回路电抗 XΣ"),
            frequency_hz=_safe_float(self.loop_freq.get(), "系统频率"),
            closure_node_index=closure,
            node_injections_A=node_currents,
            node_labels=node_labels,
            power_factor=_safe_float(self.loop_pf.get(), "统一功率因数 cosφ"),
            pf_mode=_logic_obj(self, self.loop_pf_mode.get().strip()) or "滞后",
            total_length_km=_safe_float(self.loop_total_len.get(), "总线路长度"),
            segment_ratios=ratios,
            ampacity_A=ampacity,
            overload_factor=_safe_float(self.loop_overload.get(), "短时过载系数 K"),
            close_time_s=_safe_float(self.loop_tclose.get(), "合环时刻"),
            t_end_s=_safe_float(self.loop_tend.get(), "波形结束时刻"),
            n_samples=2600,
        )
        return result

    def _plot_loop_closure_profile(self, result) -> None:
        ax = self.loop_profile_ax
        ax.clear()

        lengths = np.asarray(result.segment_lengths_km, dtype=float)
        if float(np.sum(lengths)) > 0.0:
            x = np.concatenate(([0.0], np.cumsum(lengths) / float(np.sum(lengths))))
        else:
            x = np.linspace(0.0, 1.0, len(result.node_labels) + 2)

        ax.plot(x, np.zeros_like(x), linewidth=2.0)
        ax.plot([x[0], x[-1]], [0, 0], "s", markersize=6)
        ax.text(x[0], 0.14, "左端", ha="center", fontsize=9)
        ax.text(x[-1], 0.14, "右端", ha="center", fontsize=9)

        closure_idx = result.closure_node_index
        for i, (label, inj) in enumerate(zip(result.node_labels, result.node_injections_A), start=1):
            xi = x[i]
            if i == closure_idx:
                ax.plot(xi, 0, marker="o", markersize=9, markerfacecolor="white", markeredgewidth=1.4)
                ax.text(xi, 0.24, f"{label}\n合环点", ha="center", fontsize=9)
            else:
                ax.plot(xi, 0, "o", markersize=4)
                ax.text(xi, 0.12, label, ha="center", fontsize=9)
                if abs(inj) > 1e-9:
                    y2 = -0.23 if inj >= 0 else 0.23
                    ax.annotate("", xy=(xi, y2), xytext=(xi, 0.0), arrowprops=dict(arrowstyle="->", linewidth=1.0))
                    va = "top" if inj >= 0 else "bottom"
                    ytxt = y2 - 0.03 if inj >= 0 else y2 + 0.03
                    ax.text(xi, ytxt, f"{inj:+.1f} A", ha="center", va=va, fontsize=8)

        for seg in result.segment_results:
            xm = (x[seg.index - 1] + x[seg.index]) / 2.0
            color = "#c00000" if result.overload_limit_A is not None and seg.post_magnitude_A > result.overload_limit_A + 1e-9 else "black"
            ax.text(xm, 0.30, f"{seg.post_magnitude_A:.1f}", ha="center", va="center", fontsize=8, color=color)
            ax.text(xm, -0.30, f"{seg.pre_magnitude_A:.1f}", ha="center", va="center", fontsize=8)

        ax.text(0.01, 0.96, "上：合环后稳态电流 A；下：合环前电流 A", transform=ax.transAxes, ha="left", va="top", fontsize=9)
        ax.text(0.99, 0.96, f"I_loop = {abs(result.steady_loop_current_A):.1f} A", transform=ax.transAxes, ha="right", va="top", fontsize=9)
        ax.set_title("配电网合环点位示意与各段电流")
        ax.set_xlim(-0.03, 1.03)
        ax.set_ylim(-0.45, 0.45)
        ax.axis("off")
        self.loop_profile_fig.tight_layout()
        self.loop_profile_canvas.draw()

    def _plot_loop_closure_waveforms(self, result) -> None:
        t = result.waveforms.t_s
        close_time = _safe_float(self.loop_tclose.get(), "合环时刻")

        ax1, ax2, ax3 = self.loop_wave_ax1, self.loop_wave_ax2, self.loop_wave_ax3
        for ax in (ax1, ax2, ax3):
            ax.clear()
            ax.axvline(close_time, linestyle=":", linewidth=1.0)
            ax.grid(True)
            ax.set_ylabel("i / A")

        ax1.plot(t, result.waveforms.loop_a_A, linewidth=1.2)
        ax1.set_title("合环环流（A 相瞬时值）")

        ax2.plot(t, result.waveforms.left_a_A, linewidth=1.0, label="A")
        ax2.plot(t, result.waveforms.left_b_A, linewidth=1.0, label="B")
        ax2.plot(t, result.waveforms.left_c_A, linewidth=1.0, label="C")
        ax2.set_title("左侧线路总电流（三相瞬时值）")
        ax2.legend(loc="upper right", ncol=3, fontsize=8)

        ax3.plot(t, result.waveforms.right_a_A, linewidth=1.0, label="A")
        ax3.plot(t, result.waveforms.right_b_A, linewidth=1.0, label="B")
        ax3.plot(t, result.waveforms.right_c_A, linewidth=1.0, label="C")
        ax3.set_title("右侧线路总电流（三相瞬时值）")
        ax3.legend(loc="upper right", ncol=3, fontsize=8)
        ax3.set_xlabel("t / s")

        self.loop_wave_fig.tight_layout()
        self.loop_wave_canvas.draw()

    def calculate_loop_closure(self) -> None:
        try:
            result = self._read_loop_closure_inputs()
            self._last_loop_result = result

            wf = result.waveforms
            loop_peak = float(np.max(np.abs(np.concatenate([wf.loop_a_A, wf.loop_b_A, wf.loop_c_A]))))
            left_peak = float(np.max(np.abs(np.concatenate([wf.left_a_A, wf.left_b_A, wf.left_c_A]))))
            right_peak = float(np.max(np.abs(np.concatenate([wf.right_a_A, wf.right_b_A, wf.right_c_A]))))

            overload_text = "未输入载流量上限。"
            if result.overload_limit_A is not None:
                overload_text = f"允许稳态载流上限 = {result.overload_limit_A:.2f} A"

            if result.overloaded_segments:
                conclusion = f"存在 {len(result.overloaded_segments)} 段超过稳态允许载流量。"
            else:
                conclusion = "按当前输入，上述各段稳态电流均未超过允许载流量。"

            text = (
                f"══ 配电网合环近似分析 ══════════════════════\n"
                f"连接点数量 N = {len(result.node_labels)}，合环点 = {result.node_labels[result.closure_node_index - 1]}（编号 {result.closure_node_index}）\n"
                f"U1 = {_safe_float(self.loop_u1.get(), 'U1'):.4g} kV，U2 = {_safe_float(self.loop_u2.get(), 'U2'):.4g} kV，φ = {_safe_float(self.loop_angle.get(), 'φ'):.4g}°\n"
                f"ΔU = {result.line_to_line_delta_kV:.4f} kV（合环点两侧线电压矢量差）\n"
                f"ZΣ = {result.loop_impedance_ohm.real:.4f} + j{result.loop_impedance_ohm.imag:.4f} Ω，|ZΣ| = {abs(result.loop_impedance_ohm):.4f} Ω，φz = {result.loop_impedance_angle_deg:.3f}°\n"
                f"I_loop = {_format_polar_complex(result.steady_loop_current_A, 'A')}\n"
                f"τ = {result.tau_s:.6f} s，2τ = {result.two_tau_s:.6f} s\n"
                f"左端合环前/后 = {abs(result.pre_left_source_A):.2f} / {abs(result.post_left_source_A):.2f} A\n"
                f"右端合环前/后 = {abs(result.pre_right_source_A):.2f} / {abs(result.post_right_source_A):.2f} A\n"
                f"瞬时峰值：环流 {loop_peak:.2f} A，左侧总电流 {left_peak:.2f} A，右侧总电流 {right_peak:.2f} A\n"
                f"{overload_text}\n"
                f"结论：{conclusion}\n"
                f"\n── 各段稳态电流 ───────────────────────────────\n"
                f"段号  区间                         长度/km    合环前/A    合环后/A    相角/°   状态\n"
                f"{'-' * 86}\n"
            )

            for seg in result.segment_results:
                interval = f"{seg.from_label}->{seg.to_label}"
                status = "超限" if result.overload_limit_A is not None and seg.post_magnitude_A > result.overload_limit_A + 1e-9 else "正常"
                text += (
                    f"{seg.index:>2d}    {interval:<26} {seg.length_km:>8.3f}  {seg.pre_magnitude_A:>10.2f}  "
                    f"{seg.post_magnitude_A:>10.2f}  {seg.post_angle_deg:>8.2f}  {status}\n"
                )

            text += "\n说明：\n" + result.notes
            self._set_text(self.loop_result, text)
            self._plot_loop_closure_profile(result)
            self._plot_loop_closure_waveforms(result)

        except Exception as exc:
            messagebox.showerror("计算错误", str(exc))
