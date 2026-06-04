"""COMTRADE waveform-analysis GUI mixin. / COMTRADE 录波分析页面 mixin。"""

from __future__ import annotations

from power_tool_gui_common import *


class ComtradeGuiMixin:
    def _build_comtrade_tab(self) -> None:
        self._comtrade_record = None
        self._comtrade_popup = None
        self._comtrade_popup_canvas = None
        self._comtrade_popup_fig = None
        self._harmonic_popup = None
        self._harmonic_popup_fig = None
        self._harmonic_popup_canvas = None
        self._sequence_channel_vars: dict[str, tk.StringVar] = {}
        self._sequence_result_text = None
        self._sequence_numeric_text = None
        self._sequence_numeric_table = None
        self._sequence_fig = None
        self._sequence_canvas = None
        self._sequence_axes = ()
        self._sequence_chart_notebook = None
        self._sequence_tab_defs = ()
        self._sequence_cache: dict[tuple[str, tuple[int, int, int], float], dict[str, np.ndarray]] = {}
        self._comtrade_overlay_mode = tk.StringVar(value="stacked")
        self._comtrade_default_window_s = 0.12
        self._comtrade_vertical_zoom = 1.0
        self._comtrade_visible_count = 6
        self._comtrade_channel_scroll = 0
        self._comtrade_cursor_positions: dict[str, float | None] = {"T1": None}
        self._comtrade_cursor_dragging = False
        self._comtrade_cursor_refresh_after_id = None
        self._comtrade_is_syncing_view = False
        self._comtrade_xlimit_callback_registered = False

        self.comtrade_tab.columnconfigure(1, weight=1)
        self.comtrade_tab.rowconfigure(0, weight=1)

        left = ttk.Frame(self.comtrade_tab, padding=14, style="Card.TFrame")
        right = ttk.Frame(self.comtrade_tab, padding=14, style="Card.TFrame")
        left.grid(row=0, column=0, sticky="nsw", padx=(0, 6), pady=8)
        right.grid(row=0, column=1, sticky="nsew", padx=(6, 0), pady=8)
        left.columnconfigure(0, weight=1)
        left.columnconfigure(1, weight=1)
        left.columnconfigure(2, weight=1)
        left.columnconfigure(3, weight=1)
        left.rowconfigure(9, weight=1)
        right.columnconfigure(0, weight=1)
        right.rowconfigure(3, weight=1)

        ttk.Label(left, text="录波曲线（COMTRADE / Yokogawa / MATLAB）", style="PageTitle.TLabel").grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 2))
        ttk.Label(left, text="保持录波页原有的深色浏览风格，同时将左侧控制区整理为更清晰的白色操作面板。", style="Muted.TLabel", justify="left", wraplength=420).grid(row=1, column=0, columnspan=4, sticky="w", pady=(0, 8))

        self.comtrade_path_var = tk.StringVar(value="")
        ttk.Entry(left, textvariable=self.comtrade_path_var, width=42).grid(row=2, column=0, columnspan=3, sticky="ew", padx=(0, 4), pady=2)
        ttk.Button(left, text="选择录波", command=self._browse_comtrade_cfg).grid(row=2, column=3, sticky="ew", pady=2)
        ttk.Button(left, text="加载录波", command=self._load_comtrade_file).grid(row=3, column=0, sticky="ew", pady=(4, 4), padx=(0, 4))
        ttk.Button(left, text="序量分析", command=self._open_sequence_analysis_window).grid(row=3, column=1, sticky="ew", pady=(4, 4), padx=(0, 4))
        ttk.Button(left, text="重新导出", command=self._open_comtrade_reexport_window).grid(row=3, column=2, sticky="ew", pady=(4, 4), padx=(0, 4))
        ttk.Button(left, text="多通道同图", command=self._open_comtrade_overlay_window).grid(row=3, column=3, sticky="ew", pady=(4, 4))

        ttk.Label(left, text="通道选择（Ctrl/Shift 多选）", style="SectionTitle.TLabel").grid(row=4, column=0, columnspan=4, sticky="w", pady=(4, 2))
        self.comtrade_channel_list = tk.Listbox(left, selectmode=tk.EXTENDED, width=42, height=12, exportselection=False)
        self.comtrade_channel_list.grid(row=5, column=0, columnspan=4, sticky="ew")
        self.comtrade_channel_list.bind("<<ListboxSelect>>", lambda _e: self._refresh_comtrade_plot())

        ttk.Label(left, text="起始时间 / s").grid(row=6, column=0, sticky="w", pady=(8, 2))
        self.comtrade_start_entry = ttk.Entry(left, width=12)
        self.comtrade_start_entry.grid(row=6, column=1, sticky="ew", pady=(8, 2), padx=(0, 4))
        ttk.Label(left, text="结束时间 / s").grid(row=6, column=2, sticky="w", pady=(8, 2))
        self.comtrade_end_entry = ttk.Entry(left, width=12)
        self.comtrade_end_entry.grid(row=6, column=3, sticky="ew", pady=(8, 2))

        ttk.Label(left, text="窗口宽度 / s").grid(row=7, column=0, sticky="w", pady=(6, 2))
        self.comtrade_window_entry = ttk.Entry(left, width=12)
        self.comtrade_window_entry.grid(row=7, column=1, sticky="ew", pady=(6, 2), padx=(0, 4))
        self.comtrade_window_entry.insert(0, "0.12")
        ttk.Button(left, text="应用时间窗", command=self._apply_comtrade_window).grid(row=7, column=2, sticky="ew", pady=(6, 2), padx=(0, 4))
        ttk.Button(left, text="恢复初始状态", command=self._reset_comtrade_view).grid(row=7, column=3, sticky="ew", pady=(6, 2))

        ttk.Label(left, text="基波频率 / Hz").grid(row=8, column=0, sticky="w", pady=(6, 2))
        self.comtrade_fund_entry = ttk.Entry(left, width=12)
        self.comtrade_fund_entry.grid(row=8, column=1, sticky="ew", pady=(6, 2), padx=(0, 4))
        self.comtrade_fund_entry.insert(0, "50")
        ttk.Button(left, text="分析选中通道", command=self._analyze_comtrade_selection).grid(row=8, column=2, sticky="ew", pady=(6, 2), padx=(0, 4))
        ttk.Button(left, text="全选通道", command=self._select_all_comtrade_channels).grid(row=8, column=3, sticky="ew", pady=(6, 2))

        self.comtrade_analysis_host = ttk.Frame(left, style="Card.TFrame")
        self.comtrade_analysis_host.grid(row=9, column=0, columnspan=4, sticky="nsew", pady=(8, 0))
        self.comtrade_analysis_host.columnconfigure(0, weight=1)
        self.comtrade_analysis_host.rowconfigure(0, weight=1)

        self.comtrade_overview_frame = ttk.Frame(self.comtrade_analysis_host, style="Card.TFrame")
        self.comtrade_overview_frame.grid(row=0, column=0, sticky="nsew")
        self.comtrade_overview_frame.columnconfigure(0, weight=1)
        self.comtrade_overview_frame.rowconfigure(0, weight=1)
        self.comtrade_info = ScrolledText(self.comtrade_overview_frame, width=54, height=24, wrap=tk.WORD, font="TkFixedFont")
        self.comtrade_info.grid(row=0, column=0, sticky="nsew")
        self.comtrade_info.configure(state="disabled")

        self.comtrade_sequence_frame = ttk.Frame(self.comtrade_analysis_host, style="Card.TFrame")
        self.comtrade_sequence_frame.columnconfigure(0, weight=1)
        self.comtrade_sequence_frame.rowconfigure(2, weight=1)
        self.comtrade_sequence_frame.rowconfigure(4, weight=1)
        self.comtrade_sequence_frame.grid(row=0, column=0, sticky="nsew")
        self.comtrade_sequence_frame.grid_remove()
        self._build_embedded_sequence_panel()

        ttk.Label(right, text="录波浏览区", style="PageTitle.TLabel").grid(row=0, column=0, sticky="w")
        self.comtrade_time_label = ttk.Label(right, text="未加载文件")
        self.comtrade_time_label.grid(row=1, column=0, sticky="w", pady=(0, 2))
        self.comtrade_cursor_label = tk.Text(right, height=1, wrap=tk.WORD)
        self.comtrade_cursor_label.insert("1.0", "光标：左键点击曲线区放置游标，按住左键可连续拖拽。")
        self.comtrade_cursor_label.configure(state="disabled")

        self.comtrade_fig = Figure(figsize=(9.0, 6.2), dpi=100, facecolor="#101010")
        self.comtrade_ax = self.comtrade_fig.add_subplot(111)
        self._style_comtrade_axis(self.comtrade_ax)
        plot_host = ttk.Frame(right, style="Card.TFrame")
        plot_host.grid(row=3, column=0, sticky="nsew")
        plot_host.columnconfigure(0, weight=1)
        plot_host.rowconfigure(0, weight=1)
        self.comtrade_canvas = FigureCanvasTkAgg(self.comtrade_fig, master=plot_host)
        self.comtrade_canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        self.comtrade_channel_scrollbar = tk.Scale(plot_host, from_=0, to=0, orient=tk.VERTICAL, showvalue=0, command=lambda _v: self._on_comtrade_vertical_scroll(), highlightthickness=0, length=480)
        self.comtrade_channel_scrollbar.grid(row=0, column=1, sticky="ns", padx=(4, 0))
        self.comtrade_toolbar = NavigationToolbar2Tk(self.comtrade_canvas, right, pack_toolbar=False)
        self.comtrade_toolbar.update()
        self.comtrade_toolbar.grid(row=4, column=0, sticky="ew")

        slider_frame = ttk.Frame(right, style="Card.TFrame")
        slider_frame.grid(row=2, column=0, sticky="ew", pady=(0, 4))
        slider_frame.columnconfigure(0, weight=1)
        ttk.Label(slider_frame, text="时间拖动").grid(row=0, column=0, sticky="w")
        zoom_bar = ttk.Frame(slider_frame, style="Card.TFrame")
        zoom_bar.grid(row=0, column=1, sticky="e")
        ttk.Button(zoom_bar, text="纵向放大", command=lambda: self._zoom_comtrade_vertical(1.2)).pack(side="left", padx=(0, 4))
        ttk.Button(zoom_bar, text="纵向缩小", command=lambda: self._zoom_comtrade_vertical(1 / 1.2)).pack(side="left", padx=(0, 8))
        ttk.Button(zoom_bar, text="横向放大", command=lambda: self._zoom_comtrade_horizontal(1 / 1.25)).pack(side="left", padx=(0, 4))
        ttk.Button(zoom_bar, text="横向缩小", command=lambda: self._zoom_comtrade_horizontal(1.25)).pack(side="left")
        self.comtrade_scroll = tk.Scale(slider_frame, from_=0, to=1000, orient=tk.HORIZONTAL, showvalue=0, command=lambda _v: self._refresh_comtrade_plot(from_scroll=True), highlightthickness=0)
        self.comtrade_scroll.grid(row=1, column=0, columnspan=2, sticky="ew")

        self._set_text(self.comtrade_info, "未加载录波文件。")
        self.comtrade_ax.callbacks.connect("xlim_changed", self._on_comtrade_axis_xlim_changed)
        self.comtrade_canvas.mpl_connect("button_press_event", self._on_comtrade_mouse_click)
        self.comtrade_canvas.mpl_connect("motion_notify_event", self._on_comtrade_mouse_drag)
        self.comtrade_canvas.mpl_connect("button_release_event", self._on_comtrade_mouse_release)
        self._comtrade_xlimit_callback_registered = True
        self.comtrade_canvas.draw()

    def _style_comtrade_axis(self, ax) -> None:
        ax.set_facecolor("#050505")
        ax.grid(True, color="#005f00", alpha=0.9, linewidth=0.7)
        ax.tick_params(colors="#d8d8d8")
        for spine in ax.spines.values():
            spine.set_color("#9a9a9a")
        ax.xaxis.label.set_color("#d8d8d8")
        ax.yaxis.label.set_color("#d8d8d8")
        ax.title.set_color("#f0f0f0")

    def _browse_comtrade_cfg(self) -> None:
        filename = filedialog.askopenfilename(
            title="选择录波文件",
            filetypes=[
                ("录波文件", "*.cfg *.wdf *.wvf *.hdr *.mat"),
                ("COMTRADE CFG", "*.cfg"),
                ("MATLAB MAT", "*.mat"),
                ("Yokogawa WDF", "*.wdf"),
                ("Yokogawa WVF", "*.wvf"),
                ("Yokogawa HDR", "*.hdr"),
                ("All files", "*.*"),
            ],
        )
        if filename:
            self.comtrade_path_var.set(filename)

    def _default_comtrade_window(self, duration: float) -> float:
        if duration <= 0.0:
            return self._comtrade_default_window_s
        return min(max(duration * 0.1, 0.02), min(max(duration, 0.02), 0.20))

    def _set_comtrade_time_entries(self, start_s: float, end_s: float) -> None:
        self.comtrade_start_entry.delete(0, tk.END)
        self.comtrade_start_entry.insert(0, f"{start_s:.6g}")
        self.comtrade_end_entry.delete(0, tk.END)
        self.comtrade_end_entry.insert(0, f"{end_s:.6g}")
        self.comtrade_window_entry.delete(0, tk.END)
        self.comtrade_window_entry.insert(0, f"{max(0.0, end_s - start_s):.6g}")

    def _load_comtrade_file(self) -> None:
        try:
            cfg_path = self.comtrade_path_var.get().strip()
            if not cfg_path:
                raise InputError("请先选择录波文件。")
            self._comtrade_record = parse_waveform_file(cfg_path)
            self._populate_comtrade_channels()
            self._reset_comtrade_view()
            self._set_text(self.comtrade_info, self._format_comtrade_overview())
            self._refresh_sequence_analysis_window()
        except Exception as exc:
            messagebox.showerror("录波加载失败", str(exc))

    def _populate_comtrade_channels(self) -> None:
        record = self._comtrade_record
        self.comtrade_channel_list.delete(0, tk.END)
        if record is None:
            return
        for idx, ch in enumerate(record.analog_channels):
            self.comtrade_channel_list.insert(tk.END, f"{idx+1:02d} | {ch.name} | {ch.phase or '-'} | {ch.unit or '-'}")

    def _open_comtrade_reexport_window(self) -> None:
        record = self._comtrade_record
        if record is None:
            messagebox.showwarning("提示", "请先加载录波文件。")
            return

        win = tk.Toplevel(self)
        win.title("录波重新导出")
        win.geometry("520x500")
        win.transient(self)
        win.grab_set()
        frame = ttk.Frame(win, padding=12)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(0, weight=1)

        ttk.Label(frame, text="选择一个或多个通道", style="SectionTitle.TLabel").grid(row=0, column=0, sticky="w")
        channel_list = tk.Listbox(frame, selectmode=tk.EXTENDED, exportselection=False, height=14)
        channel_list.grid(row=1, column=0, sticky="nsew", pady=(6, 8))
        frame.rowconfigure(1, weight=1)
        for idx, ch in enumerate(record.analog_channels):
            channel_list.insert(tk.END, f"{idx+1:02d} | {ch.name} | {ch.unit or '-'}")
        pre = list(self.comtrade_channel_list.curselection()) or list(range(len(record.analog_channels)))
        for idx in pre:
            channel_list.selection_set(idx)

        form = ttk.Frame(frame)
        form.grid(row=2, column=0, sticky="ew")
        form.columnconfigure(1, weight=1)
        ttk.Label(form, text="导出格式").grid(row=0, column=0, sticky="w")
        fmt_var = tk.StringVar(value="COMTRADE")
        fmt_combo = ttk.Combobox(form, textvariable=fmt_var, values=["COMTRADE", "CSV", "MATLAB"], state="readonly", width=14)
        fmt_combo.grid(row=0, column=1, sticky="w")

        ttk.Label(form, text="输出路径/文件名").grid(row=1, column=0, sticky="w", pady=(6, 0))
        path_var = tk.StringVar(value=str(Path(record.cfg_path).with_name(f"{Path(record.cfg_path).stem}_reexport")))
        ttk.Entry(form, textvariable=path_var).grid(row=1, column=1, sticky="ew", pady=(6, 0))

        def _browse_out() -> None:
            fmt = fmt_var.get().upper()
            if fmt == "CSV":
                filename = filedialog.asksaveasfilename(title="保存 CSV", defaultextension=".csv", filetypes=[("CSV", "*.csv"), ("All files", "*.*")])
            elif fmt == "MATLAB":
                filename = filedialog.asksaveasfilename(title="保存 MATLAB", defaultextension=".mat", filetypes=[("MATLAB MAT", "*.mat"), ("All files", "*.*")])
            else:
                filename = filedialog.asksaveasfilename(title="保存 COMTRADE（选择基名或 cfg）", defaultextension=".cfg", filetypes=[("COMTRADE CFG", "*.cfg"), ("All files", "*.*")])
            if filename:
                path_var.set(filename)

        ttk.Button(form, text="浏览...", command=_browse_out).grid(row=1, column=2, padx=(6, 0), pady=(6, 0))

        hint = (
            "说明：\n"
            "1) CSV / MATLAB 直接输出物理量（无需考虑整数比例系数）；\n"
            "2) 会同时保存通道名；\n"
            "3) COMTRADE 导出会生成 .cfg + .dat。"
        )
        ttk.Label(frame, text=hint, style="Muted.TLabel", justify="left", wraplength=480).grid(row=3, column=0, sticky="w", pady=(8, 0))

        def _do_export() -> None:
            try:
                selected = list(channel_list.curselection())
                if not selected:
                    raise InputError("请至少选择一个通道。")
                target = path_var.get().strip()
                if not target:
                    raise InputError("请填写输出路径。")
                paths = export_waveform_record(record, selected, target, fmt_var.get())
                messagebox.showinfo("导出完成", "已导出文件：\n" + "\n".join(str(p) for p in paths))
                win.destroy()
            except Exception as exc:
                messagebox.showerror("导出失败", str(exc))

        btns = ttk.Frame(frame)
        btns.grid(row=4, column=0, sticky="e", pady=(10, 0))
        ttk.Button(btns, text="导出", command=_do_export).pack(side="left", padx=(0, 6))
        ttk.Button(btns, text="取消", command=win.destroy).pack(side="left")

    def _select_all_comtrade_channels(self) -> None:
        if self._comtrade_record is None:
            return
        self.comtrade_channel_list.selection_clear(0, tk.END)
        if self._comtrade_record.analog_channels:
            self.comtrade_channel_list.selection_set(0, tk.END)
        self._comtrade_channel_scroll = 0
        self._show_comtrade_overview_panel()
        self._refresh_comtrade_plot()

    def _reset_comtrade_view(self) -> None:
        record = self._comtrade_record
        if record is None:
            return
        self._select_all_comtrade_channels()
        self._comtrade_vertical_zoom = 1.0
        self._comtrade_channel_scroll = 0
        self._comtrade_cursor_positions = {"T1": None}
        self._comtrade_cursor_dragging = False
        default_window = self._default_comtrade_window(record.duration_s)
        self._set_comtrade_time_entries(float(record.time_s[0]), float(record.time_s[0]) + default_window)
        self._comtrade_is_syncing_view = True
        self.comtrade_scroll.set(0)
        self._comtrade_is_syncing_view = False
        self._refresh_comtrade_plot()

    def _format_comtrade_overview(self) -> str:
        record = self._comtrade_record
        if record is None:
            return "未加载录波文件。"
        sample_rate = estimate_sampling_rate(record)
        text = (
            f"══ 录波概览 ═══════════════════════\n"
            f"站名：{record.station_name or '-'}\n设备：{record.device_id or '-'}\n版本：{record.revision}\n"
            f"文件类型：{record.file_type}\n模拟量通道：{len(record.analog_channels)}\n数字量通道：{len(record.digital_channel_names)}\n"
            f"采样率：{sample_rate:.3f} Hz\n工频：{record.frequency_hz:.3f} Hz\n时长：{record.duration_s:.6f} s\n"
            f"文件：{record.cfg_path.name} / {record.dat_path.name}"
        )
        return text

    def _current_comtrade_window(self) -> tuple[float, float]:
        record = self._comtrade_record
        if record is None or record.time_s.size == 0:
            return 0.0, 0.0
        total = max(record.duration_s, 0.0)
        try:
            width = max(1e-4, _safe_float(self.comtrade_window_entry.get(), "窗口宽度"))
        except Exception:
            width = self._default_comtrade_window(total)
        width = min(width, max(total, width))
        if total <= width + 1e-12:
            return float(record.time_s[0]), float(record.time_s[-1])
        start = float(record.time_s[0]) + (float(self.comtrade_scroll.get()) / 1000.0) * (total - width)
        end = min(float(record.time_s[-1]), start + width)
        return start, end

    def _sample_for_plot(self, time_s: np.ndarray, values: np.ndarray, max_points: int = 12000) -> tuple[np.ndarray, np.ndarray]:
        if time_s.size <= max_points:
            return time_s, values
        step = max(1, int(np.ceil(time_s.size / max_points)))
        return time_s[::step], values[::step]

    def _current_visible_comtrade_indices(self, selection: list[int]) -> list[int]:
        if len(selection) <= self._comtrade_visible_count:
            return selection
        max_start = max(0, len(selection) - self._comtrade_visible_count)
        start = min(max(0, self._comtrade_channel_scroll), max_start)
        return selection[start:start + self._comtrade_visible_count]

    def _sync_comtrade_vertical_scrollbar(self, total_selected: int) -> None:
        max_start = max(0, total_selected - self._comtrade_visible_count)
        self.comtrade_channel_scrollbar.configure(from_=max_start, to=0 if max_start > 0 else 0)
        self.comtrade_channel_scroll = min(max(0, self._comtrade_channel_scroll), max_start)
        self.comtrade_channel_scrollbar.set(self.comtrade_channel_scroll)

    def _on_comtrade_vertical_scroll(self) -> None:
        try:
            self._comtrade_channel_scroll = int(round(float(self.comtrade_channel_scrollbar.get())))
        except Exception:
            self._comtrade_channel_scroll = 0
        self._refresh_comtrade_plot()

    def _nearest_comtrade_index(self, x_value: float) -> int | None:
        record = self._comtrade_record
        if record is None or record.time_s.size == 0:
            return None
        idx = int(np.clip(np.searchsorted(record.time_s, x_value), 0, record.time_s.size - 1))
        if idx > 0 and abs(record.time_s[idx - 1] - x_value) <= abs(record.time_s[idx] - x_value):
            idx -= 1
        return idx

    def _clip_comtrade_cursor_x(self, x_value: float) -> float:
        record = self._comtrade_record
        if record is None or record.time_s.size == 0:
            return float(x_value)
        return float(np.clip(float(x_value), float(record.time_s[0]), float(record.time_s[-1])))

    def _current_comtrade_cursor_index(self, key: str) -> int | None:
        record = self._comtrade_record
        cursor_x = self._comtrade_cursor_positions.get(key)
        if record is None or cursor_x is None:
            return None
        return self._nearest_comtrade_index(cursor_x)

    def _current_comtrade_cursor_x(self, key: str) -> float | None:
        cursor_x = self._comtrade_cursor_positions.get(key)
        if cursor_x is None:
            return None
        return self._clip_comtrade_cursor_x(cursor_x)

    def _update_comtrade_cursor_label(self) -> None:
        record = self._comtrade_record
        if record is None:
            text = "光标：左键点击曲线区放置游标，按住左键可连续拖拽。"
        else:
            idx = self._current_comtrade_cursor_index("T1")
            if idx is None:
                text = "光标：左键点击曲线区放置游标，按住左键可连续拖拽。"
            else:
                text = f"游标：t={float(record.time_s[idx]):.6f}s，点号={idx + 1}。数值见曲线区游标右侧方框。"
        self.comtrade_cursor_label.configure(state="normal")
        self.comtrade_cursor_label.delete("1.0", tk.END)
        self.comtrade_cursor_label.insert("1.0", text)
        self.comtrade_cursor_label.configure(state="disabled")

    def _set_comtrade_cursor_from_x(self, x_value: float) -> None:
        self._comtrade_cursor_positions["T1"] = self._clip_comtrade_cursor_x(x_value)
        self._update_comtrade_cursor_label()

    def _comtrade_event_xdata(self, event) -> float | None:
        if event.xdata is not None:
            return float(event.xdata)
        if event.x is None or event.y is None:
            return None
        try:
            x_value, _y_value = self.comtrade_ax.transData.inverted().transform((event.x, event.y))
        except Exception:
            return None
        return float(x_value)

    def _schedule_comtrade_cursor_refresh(self) -> None:
        if self._comtrade_cursor_refresh_after_id is not None:
            return
        self._comtrade_cursor_refresh_after_id = self.after_idle(self._flush_comtrade_cursor_refresh)

    def _flush_comtrade_cursor_refresh(self) -> None:
        self._comtrade_cursor_refresh_after_id = None
        self._refresh_comtrade_plot(update_sequence=not self._comtrade_cursor_dragging)

    def _on_comtrade_mouse_click(self, event) -> None:
        if event.inaxes is not self.comtrade_ax or event.button != 1:
            return
        x_value = self._comtrade_event_xdata(event)
        if x_value is None:
            return
        self._comtrade_cursor_dragging = True
        self._set_comtrade_cursor_from_x(x_value)
        self._refresh_comtrade_plot()

    def _on_comtrade_mouse_drag(self, event) -> None:
        if not self._comtrade_cursor_dragging:
            return
        x_value = self._comtrade_event_xdata(event)
        if x_value is None:
            return
        self._set_comtrade_cursor_from_x(x_value)
        self._schedule_comtrade_cursor_refresh()

    def _on_comtrade_mouse_release(self, event) -> None:
        if event.button != 1 or not self._comtrade_cursor_dragging:
            return
        self._comtrade_cursor_dragging = False
        x_value = self._comtrade_event_xdata(event)
        if x_value is not None:
            self._set_comtrade_cursor_from_x(x_value)
        self._schedule_comtrade_cursor_refresh()

    def _zoom_comtrade_vertical(self, factor: float) -> None:
        self._comtrade_vertical_zoom = min(6.0, max(0.25, self._comtrade_vertical_zoom * factor))
        self._refresh_comtrade_plot()

    def _zoom_comtrade_horizontal(self, factor: float) -> None:
        record = self._comtrade_record
        if record is None:
            return
        start_s, end_s = self._current_comtrade_window()
        center = 0.5 * (start_s + end_s)
        total = max(record.duration_s, 1e-4)
        current_width = max(1e-4, end_s - start_s)
        new_width = min(total, max(1e-4, current_width * factor))
        data_min = float(record.time_s[0])
        data_max = float(record.time_s[-1])
        new_start = max(data_min, min(center - new_width / 2.0, data_max - new_width))
        if total <= new_width + 1e-12:
            slider = 0.0
        else:
            slider = (new_start - data_min) / max(total - new_width, 1e-12) * 1000.0
        self._comtrade_is_syncing_view = True
        self.comtrade_window_entry.delete(0, tk.END)
        self.comtrade_window_entry.insert(0, f"{new_width:.6g}")
        self.comtrade_scroll.set(max(0.0, min(1000.0, slider)))
        self._comtrade_is_syncing_view = False
        self._refresh_comtrade_plot()

    def _apply_comtrade_window(self) -> None:
        record = self._comtrade_record
        if record is None:
            return
        start_txt = self.comtrade_start_entry.get().strip()
        end_txt = self.comtrade_end_entry.get().strip()
        if start_txt and end_txt:
            start_s = max(float(record.time_s[0]), _safe_float(start_txt, "起始时间"))
            end_s = min(float(record.time_s[-1]), _safe_float(end_txt, "结束时间"))
            if end_s <= start_s:
                raise InputError("结束时间必须大于起始时间。")
            total = max(record.duration_s, 1e-12)
            width = end_s - start_s
            slider = 0.0 if total <= width + 1e-12 else (start_s - float(record.time_s[0])) / max(total - width, 1e-12) * 1000.0
            self._comtrade_is_syncing_view = True
            self.comtrade_window_entry.delete(0, tk.END)
            self.comtrade_window_entry.insert(0, f"{width:.6g}")
            self.comtrade_scroll.set(max(0.0, min(1000.0, slider)))
            self._comtrade_is_syncing_view = False
        self._refresh_comtrade_plot()

    def _on_comtrade_axis_xlim_changed(self, ax) -> None:
        record = self._comtrade_record
        if record is None or self._comtrade_is_syncing_view:
            return
        xmin, xmax = ax.get_xlim()
        data_min = float(record.time_s[0])
        data_max = float(record.time_s[-1])
        total = max(record.duration_s, 0.0)
        if not np.isfinite([xmin, xmax]).all() or total <= 0.0:
            return
        width = max(1e-4, min(abs(xmax - xmin), total))
        center = 0.5 * (xmin + xmax)
        start = max(data_min, min(center - width / 2.0, data_max - width))
        if abs(width - total) < 1e-12:
            slider = 0.0
        else:
            slider = (start - data_min) / max(total - width, 1e-12) * 1000.0
        slider = max(0.0, min(1000.0, slider))
        self._comtrade_is_syncing_view = True
        self.comtrade_window_entry.delete(0, tk.END)
        self.comtrade_window_entry.insert(0, f"{width:.6g}")
        self.comtrade_scroll.set(slider)
        self._comtrade_is_syncing_view = False
        self._set_comtrade_time_entries(start, start + width)
        self.comtrade_time_label.configure(text=f"当前时间窗：{start:.6f} s ~ {start + width:.6f} s")

    def _add_comtrade_cursor_value_box(
        self,
        ax,
        cursor_axis_frac: float,
        draw_x: float,
        cursor_idx: int,
        visible_selection: list[int],
        colors: list[str],
    ) -> None:
        record = self._comtrade_record
        if record is None:
            return
        rows = [
            TextArea(
                f"游标  t={float(record.time_s[cursor_idx]):.6f}s  点号={cursor_idx + 1}",
                textprops={"color": "#00ffff", "fontsize": 8, "weight": "bold"},
            )
        ]
        for pos, ch_idx in enumerate(visible_selection):
            ch = record.analog_channels[ch_idx]
            color = colors[pos % len(colors)]
            value = float(record.analog_values[cursor_idx, ch_idx])
            unit = ch.unit or ""
            swatch = DrawingArea(18, 10, 0, 0)
            swatch.add_artist(Line2D([1, 17], [5, 5], color=color, linewidth=2.4))
            value_text = TextArea(
                f"{ch.name}: {value:.5g}{unit}",
                textprops={"color": "#f3f3f3", "fontsize": 8},
            )
            rows.append(HPacker(children=[swatch, value_text], align="center", pad=0, sep=4))
        box = VPacker(children=rows, align="left", pad=0, sep=2)
        x_frac = min(0.78, max(0.03, cursor_axis_frac + 0.015))
        y_frac = 0.86
        value_box = AnnotationBbox(
            box,
            (x_frac, y_frac),
            xycoords=ax.transAxes,
            box_alignment=(0.0, 1.0),
            frameon=True,
            bboxprops={
                "boxstyle": "round,pad=0.35",
                "facecolor": "#101010",
                "edgecolor": "#00ffff",
                "linewidth": 0.9,
                "alpha": 0.94,
            },
            annotation_clip=False,
        )
        ax.add_artist(value_box)
        ax.text(
            draw_x,
            0.98,
            "游标",
            transform=ax.get_xaxis_transform(),
            color="#00ffff",
            fontsize=9,
            ha="center",
            va="top",
            bbox=dict(facecolor="#101010", edgecolor="#00ffff", boxstyle="round,pad=0.2"),
        )

    def _refresh_comtrade_plot(self, from_scroll: bool = False, update_sequence: bool = True) -> None:
        record = self._comtrade_record
        ax = self.comtrade_ax
        previous_sync_state = self._comtrade_is_syncing_view
        self._comtrade_is_syncing_view = True
        ax.clear()
        self._style_comtrade_axis(ax)
        if record is None or record.analog_values.size == 0:
            ax.set_title("请先加载 COMTRADE 录波")
            ax.set_xlabel("t / s")
            self.comtrade_canvas.draw()
            self._comtrade_is_syncing_view = previous_sync_state
            return
        selection = list(self.comtrade_channel_list.curselection())
        if not selection:
            selection = list(range(record.analog_values.shape[1]))
        self._sync_comtrade_vertical_scrollbar(len(selection))
        visible_selection = self._current_visible_comtrade_indices(selection)
        start_s, end_s = self._current_comtrade_window()
        colors = ["#f5e663", "#00ff00", "#ff4040", "#e0e0e0", "#00ffff", "#ff7f00", "#adff2f", "#ff66cc", "#4db6ff", "#ffb3e6"]
        band_gap = 1.55
        base_offset = (len(visible_selection) - 1) * band_gap

        for pos, ch_idx in enumerate(visible_selection):
            raw_time, raw_values = self._sample_for_plot(record.time_s, record.analog_values[:, ch_idx])
            scale = float(np.max(np.abs(raw_values))) or 1.0
            offset = base_offset - pos * band_gap
            y_norm = raw_values / scale * (0.92 * self._comtrade_vertical_zoom) + offset
            color = colors[pos % len(colors)]
            ax.plot(raw_time, y_norm, color=color, linewidth=1.0)
            ax.axhline(offset + 0.98, color="#0c8f0c", linewidth=0.6, alpha=0.8)
            ax.axhline(offset - 0.98, color="#0c8f0c", linewidth=0.6, alpha=0.8)
            ax.text(0.01, offset + 1.05, record.analog_channels[ch_idx].name, transform=ax.get_yaxis_transform(), color=color, fontsize=9, ha="left", va="bottom")

        cursor_x = self._current_comtrade_cursor_x("T1")
        if cursor_x is not None and start_s <= cursor_x <= end_s:
            cursor_axis_frac = (cursor_x - start_s) / max(end_s - start_s, 1e-12)
            cursor_idx = self._current_comtrade_cursor_index("T1")
            ax.axvline(cursor_x, color="#00ffff", linewidth=1.1, linestyle="--")
            if cursor_idx is not None:
                self._add_comtrade_cursor_value_box(ax, cursor_axis_frac, cursor_x, cursor_idx, visible_selection, colors)

        lower = -1.2
        upper = base_offset + 1.35
        ax.set_xlim(start_s, end_s)
        ax.set_ylim(lower, upper)
        ax.set_xlabel("t / s")
        ax.set_yticks([])
        ax.set_title("录波曲线浏览")
        shown_text = f"显示通道：{visible_selection[0] + 1}-{visible_selection[-1] + 1}" if visible_selection else "显示通道：无"
        self._set_comtrade_time_entries(start_s, end_s)
        self.comtrade_time_label.configure(text=f"当前时间窗：{start_s:.6f} s ~ {end_s:.6f} s，共 {len(record.time_s)} 点，{shown_text}")
        self._update_comtrade_cursor_label()
        self.comtrade_fig.subplots_adjust(left=0.06, right=0.98, top=0.93, bottom=0.10)
        self.comtrade_canvas.draw()
        self._comtrade_is_syncing_view = previous_sync_state
        if update_sequence:
            self._refresh_sequence_analysis_window()
        if self._comtrade_popup is not None and self._comtrade_popup.winfo_exists() and not from_scroll:
            self._draw_comtrade_overlay()

    def _selected_comtrade_indices(self) -> list[int]:
        if self._comtrade_record is None:
            raise InputError("请先加载录波文件。")
        selection = list(self.comtrade_channel_list.curselection())
        if not selection:
            return list(range(len(self._comtrade_record.analog_channels)))
        return selection

    def _analyze_comtrade_selection(self) -> None:
        try:
            record = self._comtrade_record
            if record is None:
                raise InputError("请先加载录波文件。")
            selection = self._selected_comtrade_indices()
            start_s, end_s = self._current_comtrade_window()
            idx = self._slice_time_window(record.time_s, start_s, end_s)
            sample_rate = estimate_sampling_rate(record)
            fundamental = _safe_float(self.comtrade_fund_entry.get(), "基波频率")
            lines = [self._format_comtrade_overview(), "", f"══ 当前窗口分析（{start_s:.6f}s ~ {end_s:.6f}s）══"]
            primary = selection[0]
            ch = record.analog_channels[primary]
            signal = np.asarray(record.analog_values[idx, primary], dtype=float)
            if signal.size < 4:
                raise InputError("当前时间窗采样点不足，无法分析。")
            summary = fourier_summary(signal, sample_rate, fundamental_hz=fundamental, max_order=19)
            min_idx = int(np.argmin(signal))
            max_idx = int(np.argmax(signal))
            min_val = float(signal[min_idx])
            max_val = float(signal[max_idx])
            min_time = float(record.time_s[idx][min_idx])
            max_time = float(record.time_s[idx][max_idx])
            dc_const, dc_decay_amp, dc_tau = self._estimate_nonperiodic_components(signal, sample_rate)
            lines.append(f"傅里叶分析通道：{ch.name} ({ch.unit or '-'})")
            lines.append(f"DC = {summary.dc:.6g}，THD = {summary.thd_percent:.3f}%")
            lines.append(f"最小值：{min_val:.6g} @ t={min_time:.6f}s")
            lines.append(f"最大值：{max_val:.6g} @ t={max_time:.6f}s")
            lines.append(
                "非周期分量："
                f"恒定直流={dc_const:.6g}，"
                f"衰减直流={dc_decay_amp:.6g}，"
                f"衰减时间常数={dc_tau:.6g}s"
            )
            lines.append("阶次   频率/Hz   幅值(pk)    RMS       相角/°")
            lines.append("-" * 48)
            for item in summary.harmonics[:10]:
                lines.append(f"{item.order:>2d}   {item.frequency_hz:>8.3f}   {item.amplitude:>9.5g}   {item.rms:>8.5g}   {item.phase_deg:>8.2f}")
            try:
                prony = prony_like_summary(signal, sample_rate)
                lines.append("")
                lines.append(f"Prony 类估计：主振荡频率 {prony.dominant_frequency_hz:.4f} Hz，阻尼比 {prony.damping_ratio_percent:.3f}%，时间常数 {prony.decay_time_constant_s:.5g} s")
            except Exception as exc:
                lines.append(f"Prony 类估计：{exc}")
            if len(selection) >= 3:
                a, b, c = selection[:3]
                seq = sequence_components(
                    record.analog_values[idx, a],
                    record.analog_values[idx, b],
                    record.analog_values[idx, c],
                    sample_rate_hz=sample_rate,
                    fundamental_hz=fundamental,
                )
                lines.append("")
                lines.append(f"序分量（按前三个选中通道的基波相量计算）：正序={seq.positive:.5g}，负序={seq.negative:.5g}，零序={seq.zero:.5g}，不平衡度={seq.unbalance_percent:.3f}%")
            else:
                lines.append("")
                lines.append("序分量提取：请选择至少 3 个相量/电流同类通道。")
            self._set_text(self.comtrade_info, "\n".join(lines))
            self._open_harmonic_analysis_window(signal, sample_rate, fundamental, ch.name, ch.unit or "-")
        except Exception as exc:
            messagebox.showerror("录波分析失败", str(exc))

    @staticmethod
    def _estimate_nonperiodic_components(signal: np.ndarray, sample_rate: float) -> tuple[float, float, float]:
        x = np.asarray(signal, dtype=float).reshape(-1)
        if x.size < 8 or sample_rate <= 0:
            return float(np.mean(x) if x.size else 0.0), 0.0, 0.0
        tail_count = max(4, int(round(x.size * 0.15)))
        dc_const = float(np.mean(x[-tail_count:]))
        resid = x - dc_const
        amp = float(resid[0])
        env = np.abs(resid)
        floor = max(1e-9, float(np.max(env)) * 1e-5)
        mask = env > floor
        if np.count_nonzero(mask) < 3:
            return dc_const, amp, 0.0
        t = np.arange(x.size, dtype=float) / sample_rate
        coeff = np.polyfit(t[mask], np.log(env[mask]), 1)
        sigma = float(coeff[0])
        tau = float(-1.0 / sigma) if sigma < -1e-12 else 0.0
        return dc_const, amp, tau

    def _open_harmonic_analysis_window(
        self,
        signal: np.ndarray,
        sample_rate: float,
        fundamental_hz: float,
        channel_name: str,
        channel_unit: str,
    ) -> None:
        if self._harmonic_popup is not None and self._harmonic_popup.winfo_exists():
            self._harmonic_popup.destroy()
        win = tk.Toplevel(self)
        win.title(f"谐波分析 - {channel_name}")
        win.geometry("840x420")
        self._harmonic_popup = win

        host = ttk.Frame(win, padding=8)
        host.pack(fill="both", expand=True)
        host.columnconfigure(1, weight=1)
        host.rowconfigure(1, weight=1)

        top = ttk.Frame(host)
        top.grid(row=0, column=0, columnspan=2, sticky="ew")
        ttk.Label(top, text="谐波分析最高次数").pack(side="left")
        order_var = tk.IntVar(value=19)
        spin = tk.Spinbox(top, from_=3, to=50, increment=1, textvariable=order_var, width=6)
        spin.pack(side="left", padx=(6, 8))
        ttk.Label(top, text=f"通道：{channel_name} ({channel_unit})").pack(side="left", padx=(8, 0))

        table_frame = ttk.Frame(host)
        table_frame.grid(row=1, column=0, sticky="nsw", padx=(0, 8))
        cols = ("order", "amp", "ratio")
        tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=16)
        tree.heading("order", text="谐波")
        tree.heading("amp", text="含有量")
        tree.heading("ratio", text="含有率")
        tree.column("order", width=78, anchor="center")
        tree.column("amp", width=118, anchor="e")
        tree.column("ratio", width=100, anchor="e")
        yscroll = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=yscroll.set)
        tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")

        fig = Figure(figsize=(6.2, 3.2), dpi=100)
        ax = fig.add_subplot(111)
        ax.grid(True, axis="y", alpha=0.25)
        self._harmonic_popup_fig = fig
        self._harmonic_popup_canvas = FigureCanvasTkAgg(fig, master=host)
        self._harmonic_popup_canvas.get_tk_widget().grid(row=1, column=1, sticky="nsew")

        def _refresh_view() -> None:
            max_order = max(2, int(order_var.get()))
            summary = fourier_summary(signal, sample_rate, fundamental_hz=fundamental_hz, max_order=max_order)
            tree.delete(*tree.get_children())
            base_amp = summary.harmonics[0].amplitude if summary.harmonics else 0.0
            tree.insert("", "end", values=("基波", f"{base_amp:.4f}", "100.00%"))
            tree.insert("", "end", values=("直流分量", f"{summary.dc:.4f}", f"{(abs(summary.dc) / max(base_amp, 1e-9) * 100.0):.2f}%"))
            orders = []
            percents = []
            for item in summary.harmonics[1:]:
                ratio = item.amplitude / max(base_amp, 1e-12) * 100.0
                tree.insert("", "end", values=(f"{item.order}次谐波", f"{item.amplitude:.4f}", f"{ratio:.2f}%"))
                orders.append(item.order)
                percents.append(ratio)
            ax.clear()
            ax.bar(orders, percents, width=0.6, color="#7d7d7d")
            ax.set_xlabel("谐波次数")
            ax.set_ylabel("含有率 / %")
            ax.set_title("谐波含有率柱状图")
            ax.set_xticks(orders if len(orders) <= 20 else orders[::2])
            ax.grid(True, axis="y", alpha=0.3)
            self._harmonic_popup_canvas.draw()

        ttk.Button(top, text="刷新", command=_refresh_view).pack(side="left", padx=(8, 0))
        _refresh_view()

    def _build_embedded_sequence_panel(self) -> None:
        top = ttk.Frame(self.comtrade_sequence_frame)
        top.grid(row=0, column=0, sticky="ew")
        top.columnconfigure(0, weight=1)
        top.columnconfigure(1, weight=1)
        self._sequence_channel_vars = {key: tk.StringVar(value=_display_obj(self, "未设置")) for key in ["Ua", "Ub", "Uc", "Ia", "Ib", "Ic"]}
        self._sequence_comboboxes: list[ttk.Combobox] = []

        for box_idx, (title, prefix) in enumerate((("三相电压通道", "U"), ("三相电流通道", "I"))):
            lf = ttk.LabelFrame(top, text=title, padding=4)
            lf.grid(row=0, column=box_idx, sticky="nsew", padx=(0, 6) if box_idx == 0 else 0)
            for ridx, phase in enumerate(("a", "b", "c")):
                show_key = f"{prefix}{phase}"
                ttk.Label(lf, text=show_key).grid(row=ridx, column=0, sticky="w", padx=2, pady=2)
                cmb = ttk.Combobox(lf, textvariable=self._sequence_channel_vars[show_key], values=[_display_obj(self, "未设置")], state="readonly", width=24)
                cmb.grid(row=ridx, column=1, sticky="ew", padx=2, pady=2)
                cmb.bind("<<ComboboxSelected>>", lambda _e: self._refresh_sequence_analysis_window())
                self._sequence_comboboxes.append(cmb)
            lf.columnconfigure(1, weight=1)

        btn_row = ttk.Frame(self.comtrade_sequence_frame)
        btn_row.grid(row=1, column=0, sticky="ew", pady=(6, 4))
        ttk.Button(btn_row, text="应用配置", command=self._refresh_sequence_analysis_window).pack(side="left")
        ttk.Button(btn_row, text="返回概览", command=self._show_comtrade_overview_panel).pack(side="left", padx=(6, 0))

        self._sequence_result_text = ScrolledText(self.comtrade_sequence_frame, width=54, height=12, wrap=tk.WORD, font="TkFixedFont")
        self._sequence_result_text.grid(row=2, column=0, sticky="nsew")
        self._sequence_result_text.configure(state="disabled")

        chart_nb = ttk.Notebook(self.comtrade_sequence_frame)
        chart_nb.grid(row=3, column=0, sticky="ew", pady=(6, 0))
        self._sequence_tab_defs = (
            ("电压相量", "voltage_phase"),
            ("电流相量", "current_phase"),
            ("V 序分量", "voltage_seq"),
            ("I 序分量", "current_seq"),
        )
        for tab_text, key in self._sequence_tab_defs:
            frame = ttk.Frame(chart_nb)
            chart_nb.add(frame, text=tab_text)
        chart_host = ttk.Frame(self.comtrade_sequence_frame)
        chart_host.grid(row=4, column=0, sticky="nsew")
        chart_host.columnconfigure(0, weight=0)
        chart_host.columnconfigure(1, weight=1)
        chart_host.rowconfigure(0, weight=1)

        table_frame = ttk.Frame(chart_host)
        table_frame.grid(row=0, column=0, sticky="nsw", padx=(0, 8))
        columns = ("name", "mag", "ang", "real", "imag")
        table = ttk.Treeview(table_frame, columns=columns, show="headings", height=7)
        headers = {"name": "名称", "mag": "幅值", "ang": "相角/°", "real": "实部", "imag": "虚部"}
        widths = {"name": 64, "mag": 90, "ang": 90, "real": 88, "imag": 88}
        for key in columns:
            table.heading(key, text=headers[key])
            table.column(key, width=widths[key], anchor="center", stretch=False)
        table.grid(row=0, column=0, sticky="nsew")
        unit_label = ttk.Label(table_frame, text="单位：-", foreground="#555555")
        unit_label.grid(row=1, column=0, sticky="w", pady=(4, 0))
        self._sequence_numeric_table = table
        self._sequence_numeric_text = unit_label

        plot_frame = ttk.Frame(chart_host)
        plot_frame.grid(row=0, column=1, sticky="nsew")
        plot_frame.columnconfigure(0, weight=1)
        plot_frame.rowconfigure(0, weight=1)
        self._sequence_fig = Figure(figsize=(4.8, 4.8), dpi=100, facecolor="#101418")
        ax_seq = self._sequence_fig.add_subplot(111, projection="polar")
        self._sequence_axes = (ax_seq,)
        self._sequence_canvas = FigureCanvasTkAgg(self._sequence_fig, master=plot_frame)
        self._sequence_canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        self._sequence_chart_notebook = chart_nb
        self._sequence_chart_notebook.bind("<<NotebookTabChanged>>", lambda _e: self._refresh_sequence_analysis_window())

    def _show_comtrade_overview_panel(self) -> None:
        self.comtrade_sequence_frame.grid_remove()
        self.comtrade_overview_frame.grid()

    def _show_comtrade_sequence_panel(self) -> None:
        options = self._sequence_channel_options()
        for cmb in self._sequence_comboboxes:
            cmb.configure(values=options)
        self.comtrade_overview_frame.grid_remove()
        self.comtrade_sequence_frame.grid()
        self._refresh_sequence_analysis_window()

    def _sequence_channel_options(self) -> list[str]:
        record = self._comtrade_record
        options = [_display_obj(self, "未设置")]
        if record is None:
            return options
        for idx, ch in enumerate(record.analog_channels):
            options.append(f"{idx}:{ch.name} [{ch.phase or '-'}] {ch.unit or ''}".strip())
        return options

    def _parse_sequence_channel_selection(self, value: str) -> int | None:
        value = value.strip()
        if not value or _logic_obj(self, value) == "未设置":
            return None
        return int(value.split(":", 1)[0])

    def _open_sequence_analysis_window(self) -> None:
        self._show_comtrade_sequence_panel()

    def _read_sequence_group(self, labels: tuple[str, str, str]) -> tuple[int, int, int] | None:
        indices = [self._parse_sequence_channel_selection(self._sequence_channel_vars[key].get()) for key in labels]
        return tuple(indices) if all(idx is not None for idx in indices) else None

    def _format_sequence_complex(self, value: complex, unit: str) -> str:
        mag = abs(value)
        ang = math.degrees(math.atan2(value.imag, value.real))
        return f"{mag:.5g} ∠ {ang:+.2f}° {unit}"

    def _build_sequence_cache(self, group_key: str, indices: tuple[int, int, int], sample_rate: float, fundamental: float) -> dict[str, np.ndarray]:
        cache_key = (group_key, indices, round(fundamental, 6))
        if cache_key in self._sequence_cache:
            return self._sequence_cache[cache_key]
        record = self._comtrade_record
        if record is None:
            raise InputError("未加载录波文件。")
        n = max(8, int(round(sample_rate / max(fundamental, 1e-9))))
        basis = np.exp(-1j * 2.0 * np.pi * fundamental * np.arange(n, dtype=float) / sample_rate)[::-1]
        scale = 2.0 / n / math.sqrt(2.0)

        def _phasor_track(signal: np.ndarray) -> np.ndarray:
            return np.convolve(np.asarray(signal, dtype=float), basis, mode="same") * scale

        pa = _phasor_track(record.analog_values[:, indices[0]])
        pb = _phasor_track(record.analog_values[:, indices[1]])
        pc = _phasor_track(record.analog_values[:, indices[2]])
        alpha = complex(-0.5, math.sqrt(3.0) / 2.0)
        zero = (pa + pb + pc) / 3.0
        positive = (pa + alpha * pb + (alpha ** 2) * pc) / 3.0
        negative = (pa + (alpha ** 2) * pb + alpha * pc) / 3.0
        result = {
            "a": pa,
            "b": pb,
            "c": pc,
            "zero": zero,
            "positive": positive,
            "negative": negative,
        }
        self._sequence_cache[cache_key] = result
        return result

    def _draw_sequence_phasor_axis(self, ax, vectors: dict[str, complex], title: str) -> None:
        ax.clear()
        ax.set_theta_zero_location("E")
        ax.set_theta_direction(1)
        ax.set_facecolor("#11161d")
        colors = {
            "Ua": "#7ec8ff", "Ub": "#ffe082", "Uc": "#ff8a80",
            "Ia": "#4dd0e1", "Ib": "#ffd54f", "Ic": "#ffab91",
            "V0": "#b388ff", "V1": "#66bb6a", "V2": "#42a5f5",
            "I0": "#f06292", "I1": "#26c6da", "I2": "#ffb74d",
        }
        max_mag = max(1.0, max(abs(v) for v in vectors.values())) if vectors else 1.0
        radial_max = max_mag * 1.15
        rings = np.linspace(radial_max / 4.0, radial_max, 4)
        ax.set_ylim(0.0, radial_max)
        ax.set_yticks(rings)
        ax.set_yticklabels([f"{tick:.3g}" for tick in rings], color="#aeb8c2", fontsize=8)
        ax.set_rlabel_position(22.5)
        ax.set_thetagrids(
            np.arange(0, 360, 45),
            labels=["0°", "45°", "90°", "135°", "180°", "-135°", "-90°", "-45°"],
            fontsize=8,
            color="#8ea1b4",
        )
        ax.grid(color="#5f6f7e", linestyle="-", linewidth=0.8, alpha=0.45)
        ax.spines["polar"].set_color("#7c8794")
        ax.spines["polar"].set_linewidth(1.0)
        for name, val in vectors.items():
            theta = math.atan2(val.imag, val.real)
            radius = abs(val)
            color = colors.get(name, "#ffffff")
            ax.annotate(
                "",
                xy=(theta, radius),
                xytext=(theta, 0.0),
                arrowprops=dict(arrowstyle="-|>", color=color, linewidth=2.2, linestyle="-", shrinkA=0, shrinkB=0),
            )
        ax.set_title("")

    def _active_sequence_tab_key(self) -> str:
        notebook = getattr(self, "_sequence_chart_notebook", None)
        tab_defs = getattr(self, "_sequence_tab_defs", ())
        if notebook is None or not tab_defs:
            return "voltage_phase"
        current = notebook.index(notebook.select())
        return tab_defs[current][1]

    def _update_sequence_numeric_table(self, vectors: dict[str, complex], unit: str) -> None:
        if self._sequence_numeric_table is None or self._sequence_numeric_text is None:
            return
        for item in self._sequence_numeric_table.get_children():
            self._sequence_numeric_table.delete(item)
        for name, value in vectors.items():
            mag = abs(value)
            ang = math.degrees(math.atan2(value.imag, value.real))
            self._sequence_numeric_table.insert(
                "",
                tk.END,
                values=(name, f"{mag:.5g}", f"{ang:.2f}", f"{value.real:.5g}", f"{value.imag:.5g}"),
            )
        self._sequence_numeric_text.configure(text=f"单位：{unit or '-'}")

    def _refresh_sequence_analysis_window(self) -> None:
        if self._sequence_result_text is None or self._sequence_fig is None or self._sequence_canvas is None or self._sequence_numeric_text is None:
            return
        record = self._comtrade_record
        if record is None:
            self._set_text(self._sequence_result_text, "未加载录波文件。")
            self._update_sequence_numeric_table({}, "-")
            for ax in self._sequence_axes:
                ax.clear()
            self._sequence_canvas.draw()
            return
        t1 = self._current_comtrade_cursor_index("T1")
        if t1 is None:
            self._set_text(self._sequence_result_text, "请先在主窗口左键设置 T1 光标，再进行序量分析。")
            self._update_sequence_numeric_table({}, "-")
            for ax in self._sequence_axes:
                ax.clear()
                ax.set_title("等待 T1 光标")
            self._sequence_canvas.draw()
            return
        sample_rate = estimate_sampling_rate(record)
        fundamental = _safe_float(self.comtrade_fund_entry.get(), "基波频率")
        lines = [f"T1 点号 = {t1 + 1}", f"T1 时间 = {record.time_s[t1]:.6f} s", ""]
        voltage_group = self._read_sequence_group(("Ua", "Ub", "Uc"))
        current_group = self._read_sequence_group(("Ia", "Ib", "Ic"))
        tab_vectors = {"voltage_phase": {}, "current_phase": {}, "voltage_seq": {}, "current_seq": {}}
        titles = {
            "voltage_phase": "电压相量",
            "current_phase": "电流相量",
            "voltage_seq": "V 序分量",
            "current_seq": "I 序分量",
        }
        tab_units = {"voltage_phase": "", "current_phase": "", "voltage_seq": "", "current_seq": ""}
        if voltage_group is not None:
            vcache = self._build_sequence_cache("V", voltage_group, sample_rate, fundamental)
            tab_vectors["voltage_phase"] = {
                "Ua": complex(vcache["a"][t1]),
                "Ub": complex(vcache["b"][t1]),
                "Uc": complex(vcache["c"][t1]),
            }
            tab_vectors["voltage_seq"] = {
                "V0": complex(vcache["zero"][t1]),
                "V1": complex(vcache["positive"][t1]),
                "V2": complex(vcache["negative"][t1]),
            }
            unit = record.analog_channels[voltage_group[0]].unit or "pu"
            tab_units["voltage_phase"] = unit
            tab_units["voltage_seq"] = unit
            lines.append("【电压序分量】")
            lines.append(f"V0: {self._format_sequence_complex(tab_vectors['voltage_seq']['V0'], unit)}")
            lines.append(f"V1: {self._format_sequence_complex(tab_vectors['voltage_seq']['V1'], unit)}")
            lines.append(f"V2: {self._format_sequence_complex(tab_vectors['voltage_seq']['V2'], unit)}")
            lines.append("")
        if current_group is not None:
            icache = self._build_sequence_cache("I", current_group, sample_rate, fundamental)
            tab_vectors["current_phase"] = {
                "Ia": complex(icache["a"][t1]),
                "Ib": complex(icache["b"][t1]),
                "Ic": complex(icache["c"][t1]),
            }
            tab_vectors["current_seq"] = {
                "I0": complex(icache["zero"][t1]),
                "I1": complex(icache["positive"][t1]),
                "I2": complex(icache["negative"][t1]),
            }
            unit = record.analog_channels[current_group[0]].unit or "A"
            tab_units["current_phase"] = unit
            tab_units["current_seq"] = unit
            lines.append("【电流序分量】")
            lines.append(f"I0: {self._format_sequence_complex(tab_vectors['current_seq']['I0'], unit)}")
            lines.append(f"I1: {self._format_sequence_complex(tab_vectors['current_seq']['I1'], unit)}")
            lines.append(f"I2: {self._format_sequence_complex(tab_vectors['current_seq']['I2'], unit)}")
        if not any(tab_vectors.values()):
            self._set_text(self._sequence_result_text, "请在序量分析窗口中至少完整设置一组三相电压或三相电流通道。")
            self._update_sequence_numeric_table({}, "-")
            ax = self._sequence_axes[0]
            ax.clear()
            ax.set_title(f"{titles[self._active_sequence_tab_key()]}\n（未配置）", color="#f5f7fa", pad=16, fontsize=11)
            self._sequence_canvas.draw()
            return
        active_key = self._active_sequence_tab_key()
        ax = self._sequence_axes[0]
        if tab_vectors[active_key]:
            self._draw_sequence_phasor_axis(ax, tab_vectors[active_key], titles[active_key])
            self._update_sequence_numeric_table(tab_vectors[active_key], tab_units[active_key] or "-")
        else:
            ax.clear()
            ax.set_title(f"{titles[active_key]}\n（未配置）", color="#f5f7fa", pad=16, fontsize=11)
            self._update_sequence_numeric_table({}, "-")
        self._set_text(self._sequence_result_text, "\n".join(lines).strip())
        self._sequence_fig.subplots_adjust(left=0.03, right=0.97, top=0.97, bottom=0.03)
        self._sequence_canvas.draw()

    def _toggle_comtrade_overlay_mode(self) -> None:
        self._comtrade_overlay_mode.set("overlay" if self._comtrade_overlay_mode.get() == "stacked" else "stacked")
        self._draw_comtrade_overlay()

    def _open_comtrade_overlay_window(self) -> None:
        try:
            self._selected_comtrade_indices()
        except Exception as exc:
            messagebox.showwarning("无法绘图", str(exc))
            return
        if self._comtrade_popup is not None and self._comtrade_popup.winfo_exists():
            self._comtrade_popup.deiconify()
            self._comtrade_popup.lift()
            self._draw_comtrade_overlay()
            return
        win = tk.Toplevel(self)
        self._comtrade_popup = win
        win.geometry("1220x840")
        win.rowconfigure(1, weight=1)
        win.columnconfigure(0, weight=1)

        tool = ttk.Frame(win, padding=6)
        tool.grid(row=0, column=0, sticky="ew")
        ttk.Label(tool, text="显示风格").pack(side="left")
        ttk.Label(tool, textvariable=self._comtrade_overlay_mode).pack(side="left", padx=(6, 12))
        ttk.Button(tool, text="一键切换风格", command=self._toggle_comtrade_overlay_mode).pack(side="left")

        frame = ttk.Frame(win, padding=6)
        frame.grid(row=1, column=0, sticky="nsew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        self._comtrade_popup_fig = Figure(figsize=(10.8, 7.4), dpi=100)
        self._comtrade_popup_canvas = FigureCanvasTkAgg(self._comtrade_popup_fig, master=frame)
        self._comtrade_popup_canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        toolbar = NavigationToolbar2Tk(self._comtrade_popup_canvas, frame, pack_toolbar=False)
        toolbar.update()
        toolbar.grid(row=1, column=0, sticky="ew")
        self._draw_comtrade_overlay()

    def _draw_comtrade_overlay(self) -> None:
        record = self._comtrade_record
        if record is None or self._comtrade_popup_fig is None or self._comtrade_popup_canvas is None:
            return
        selection = self._selected_comtrade_indices()
        start_s, end_s = self._current_comtrade_window()
        idx = self._slice_time_window(record.time_s, start_s, end_s)
        t = record.time_s[idx]
        mode = self._comtrade_overlay_mode.get()
        self._comtrade_popup_fig.clear()
        colors = ["#1f77b4", "#d62728", "#2ca02c", "#9467bd", "#ff7f0e", "#17becf", "#8c564b", "#e377c2"]

        if mode == "overlay":
            ax = self._comtrade_popup_fig.add_subplot(111)
            legend_labels = []
            for pos, ch_idx in enumerate(selection):
                ch = record.analog_channels[ch_idx]
                y = record.analog_values[idx, ch_idx]
                ax.plot(t, y, linewidth=1.2, color=colors[pos % len(colors)], label=ch.name)
                legend_labels.append(ch.name)
            ax.grid(True, linestyle="--", alpha=0.35)
            ax.set_title("多通道同图 / MATLAB 单轴叠加风格")
            ax.set_xlabel("t / s")
            ax.set_ylabel("幅值")
            ax.legend(loc="upper right", fontsize=8, frameon=True, title="通道 / 线形")
            self._comtrade_popup.title("录波曲线 - 多通道同图（MATLAB 单轴叠加风格）")
        else:
            axes = []
            for pos, ch_idx in enumerate(selection, start=1):
                axes.append(self._comtrade_popup_fig.add_subplot(len(selection), 1, pos, sharex=axes[0] if axes else None))
            for ax, ch_idx, color in zip(axes, selection, colors * 10):
                ch = record.analog_channels[ch_idx]
                ax.plot(t, record.analog_values[idx, ch_idx], linewidth=1.1, color=color, label=ch.name)
                ax.grid(True, linestyle='--', alpha=0.35)
                ax.legend(loc='upper right', fontsize=8)
                ax.set_ylabel(ch.unit or '值')
            axes[0].set_title('多通道同图 / MATLAB 学术论文风格（分轴堆叠）')
            axes[-1].set_xlabel('t / s')
            self._comtrade_popup.title("录波曲线 - 多通道同图（MATLAB 学术风格）")

        self._comtrade_popup_fig.tight_layout()
        self._comtrade_popup_canvas.draw()

