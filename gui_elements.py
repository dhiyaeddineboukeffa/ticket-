import tkinter as tk
from tkinter import ttk
import os
import torch

def build_notebook_tabs(parent_root, notebook):
    """
    Builds the main and settings tabs for the ttk.Notebook.
    Returns the main_tab_frame and settings_tab_frame.
    """
    main_tab_frame = ttk.Frame(notebook, style="TFrame")
    notebook.add(main_tab_frame, text="  Dashboard  ")

    settings_tab_frame = ttk.Frame(notebook, style="TFrame")
    notebook.add(settings_tab_frame, text="  Diagnostics & Settings  ")

    return main_tab_frame, settings_tab_frame

def build_left_control_panel(parent_frame, video_source_var, video_path_var,
                             ip_url_var, webcam_index_var, callbacks):
    """
    Builds the modernized left control panel with dark theme,
    compact source selection, line drawing ergonomics, and 4 KPI metric cards.
    """
    widgets = {}

    # Scrollable container with dark slate background
    left_canvas = tk.Canvas(parent_frame, bg="#0F172A", highlightthickness=0)
    left_canvas.pack(side="left", fill="both", expand=True)

    left_scrollbar = ttk.Scrollbar(parent_frame, orient="vertical", command=left_canvas.yview)
    left_scrollbar.pack(side="right", fill="y")
    left_canvas.configure(yscrollcommand=left_scrollbar.set)

    scrollable_content_frame = ttk.Frame(left_canvas, style="LeftPanel.TFrame")
    canvas_window = left_canvas.create_window((0, 0), window=scrollable_content_frame, anchor="nw")

    scrollable_content_frame.bind(
        "<Configure>",
        lambda e: left_canvas.configure(scrollregion=left_canvas.bbox("all"))
    )
    left_canvas.bind(
        '<Configure>',
        lambda e: callbacks['on_left_canvas_configure'](e, left_canvas, canvas_window)
    )

    # 0. Brand Header
    header_frame = tk.Frame(scrollable_content_frame, bg="#1E293B", padx=12, pady=10)
    header_frame.pack(fill='x', padx=6, pady=(6, 4))
    
    brand_title = tk.Label(
        header_frame, text="PEOPLE COUNTER PRO",
        font=("Segoe UI", 12, "bold"), fg="#38BDF8", bg="#1E293B"
    )
    brand_title.pack(anchor='w')
    brand_sub = tk.Label(
        header_frame, text="AI Vision & Live Flow Analytics",
        font=("Segoe UI", 8), fg="#94A3B8", bg="#1E293B"
    )
    brand_sub.pack(anchor='w')

    # 1. Video Source Section
    source_frame = ttk.LabelFrame(scrollable_content_frame, text=" 1. Video Source ")
    source_frame.pack(fill='x', pady=4, padx=6)

    # Video File Radio + Selector
    ttk.Radiobutton(
        source_frame, text="Video File", variable=video_source_var,
        value="video", command=callbacks['on_source_change']
    ).pack(anchor='w', padx=8, pady=(4, 2))

    file_row = ttk.Frame(source_frame)
    file_row.pack(fill='x', padx=8, pady=2)
    widgets['file_button'] = ttk.Button(file_row, text="📁 Choose File...", command=callbacks['select_file'], style="Primary.TButton")
    widgets['file_button'].pack(fill='x')

    # Truncated compact file label
    compact_path_var = tk.StringVar(value="No file loaded")
    def _update_compact_path(*args):
        p = video_path_var.get()
        if p:
            compact_path_var.set(f"📄 .../{os.path.basename(p)}")
        else:
            compact_path_var.set("📄 No file loaded")
    video_path_var.trace_add("write", _update_compact_path)
    _update_compact_path()

    widgets['video_path_label'] = tk.Label(
        source_frame, textvariable=compact_path_var, font=("Segoe UI", 8),
        fg="#38BDF8", bg="#1E293B", anchor='w'
    )
    widgets['video_path_label'].pack(fill='x', padx=8, pady=(1, 4))

    # Webcam Radio + Dropdown
    ttk.Radiobutton(
        source_frame, text="Webcam", variable=video_source_var,
        value="webcam", command=callbacks['on_source_change']
    ).pack(anchor='w', padx=8, pady=(4, 2))

    widgets['webcam_dropdown'] = ttk.Combobox(source_frame, textvariable=webcam_index_var, state='readonly', width=14)
    widgets['webcam_dropdown'].pack(fill='x', padx=8, pady=(2, 4))
    widgets['webcam_dropdown'].bind("<<ComboboxSelected>>", callbacks['on_webcam_selected'])

    # IP Camera Radio + URL Entry
    ttk.Radiobutton(
        source_frame, text="IP Camera Stream", variable=video_source_var,
        value="ipcam", command=callbacks['on_source_change']
    ).pack(anchor='w', padx=8, pady=(4, 2))

    widgets['ip_entry'] = ttk.Entry(source_frame, textvariable=ip_url_var, state='disabled')
    widgets['ip_entry'].pack(fill='x', padx=8, pady=(2, 6))

    # 2. Line Definition Section
    line_frame = ttk.LabelFrame(scrollable_content_frame, text=" 2. Counting Line & Calibration ")
    line_frame.pack(fill='x', pady=6, padx=6)

    line_btn_row1 = ttk.Frame(line_frame)
    line_btn_row1.pack(fill='x', padx=8, pady=3)
    widgets['draw_line_btn'] = ttk.Button(line_btn_row1, text="✏ Draw New Line", command=callbacks['start_drawing'], style="Primary.TButton")
    widgets['draw_line_btn'].pack(side='left', fill='x', expand=True, padx=(0, 2))

    widgets['cancel_draw_btn'] = ttk.Button(
        line_btn_row1, text="✕ Cancel",
        command=callbacks.get('cancel_drawing', lambda: None),
        state='disabled', style="Secondary.TButton"
    )
    widgets['cancel_draw_btn'].pack(side='right', fill='x', expand=False, padx=(2, 0))

    line_btn_row2 = ttk.Frame(line_frame)
    line_btn_row2.pack(fill='x', padx=8, pady=3)
    widgets['switch_dir_btn'] = ttk.Button(
        line_btn_row2, text="⇄ Flip Direction",
        command=callbacks['switch_direction'], style="Secondary.TButton"
    )
    widgets['switch_dir_btn'].pack(side='left', fill='x', expand=True, padx=(0, 2))

    widgets['clear_line_btn'] = ttk.Button(
        line_btn_row2, text="🗑 Clear Line",
        command=callbacks.get('clear_line', lambda: None),
        style="Secondary.TButton"
    )
    widgets['clear_line_btn'].pack(side='right', fill='x', expand=True, padx=(2, 0))

    # Helper instruction banner
    instr_container = tk.Frame(line_frame, bg="#0F172A", padx=8, pady=6)
    instr_container.pack(fill='x', padx=8, pady=(4, 8))
    widgets['instruction_label'] = tk.Label(
        instr_container, text="Counting line ready.",
        font=("Segoe UI", 8), fg="#94A3B8", bg="#0F172A", wraplength=230, justify='left'
    )
    widgets['instruction_label'].pack(fill='x')

    # 3. Execution Section
    run_frame = ttk.LabelFrame(scrollable_content_frame, text=" 3. Execution ")
    run_frame.pack(fill='x', pady=6, padx=6)

    run_row1 = ttk.Frame(run_frame)
    run_row1.pack(fill='x', padx=8, pady=4)
    widgets['start_btn'] = ttk.Button(
        run_row1, text="▶ START ANALYSIS",
        command=callbacks['start_processing'], style="Start.TButton"
    )
    widgets['start_btn'].pack(side='left', fill='x', expand=True, padx=(0, 3))

    widgets['stop_btn'] = ttk.Button(
        run_row1, text="⏹ STOP",
        command=callbacks['stop_processing'], state='disabled', style="Stop.TButton"
    )
    widgets['stop_btn'].pack(side='right', fill='x', expand=True, padx=(3, 0))

    run_row2 = ttk.Frame(run_frame)
    run_row2.pack(fill='x', padx=8, pady=(0, 6))
    widgets['reset_counts_btn'] = ttk.Button(
        run_row2, text="↺ Reset Counters",
        command=callbacks.get('reset_counts', lambda: None),
        style="Secondary.TButton"
    )
    widgets['reset_counts_btn'].pack(fill='x')

    # 4. Live Counts: 4 Structured KPI Metric Cards
    count_frame = ttk.LabelFrame(scrollable_content_frame, text=" Real-Time Flow Metrics ")
    count_frame.pack(fill='x', pady=6, padx=6)

    # StringVars for numerical values
    widgets['in_count_val'] = tk.StringVar(value="0")
    widgets['out_count_val'] = tk.StringVar(value="0")
    widgets['in_frame_val'] = tk.StringVar(value="0")
    widgets['net_flow_val'] = tk.StringVar(value="0")

    # Legacy variables for backwards compatibility
    widgets['in_count_var'] = tk.StringVar(value="IN: 0")
    widgets['out_count_var'] = tk.StringVar(value="OUT: 0")
    widgets['people_in_frame_var'] = tk.StringVar(value="In Frame: 0")
    widgets['perf_stats_var'] = tk.StringVar(value="Ready")

    cards_grid = tk.Frame(count_frame, bg="#1E293B", padx=4, pady=4)
    cards_grid.pack(fill='x', padx=4, pady=4)
    cards_grid.grid_columnconfigure(0, weight=1)
    cards_grid.grid_columnconfigure(1, weight=1)

    # Card 1: ENTERED (IN) - Emerald
    card_in = tk.Frame(cards_grid, bg="#064E3B", highlightbackground="#059669", highlightthickness=1, padx=6, pady=6)
    card_in.grid(row=0, column=0, sticky='nsew', padx=3, pady=3)
    tk.Label(card_in, text="▲ ENTERED", font=("Segoe UI", 8, "bold"), fg="#34D399", bg="#064E3B").pack(anchor='w')
    tk.Label(card_in, textvariable=widgets['in_count_val'], font=("Consolas", 18, "bold"), fg="#10B981", bg="#064E3B").pack(anchor='center', pady=2)

    # Card 2: EXITED (OUT) - Rose
    card_out = tk.Frame(cards_grid, bg="#4C0519", highlightbackground="#E11D48", highlightthickness=1, padx=6, pady=6)
    card_out.grid(row=0, column=1, sticky='nsew', padx=3, pady=3)
    tk.Label(card_out, text="▼ EXITED", font=("Segoe UI", 8, "bold"), fg="#FB7185", bg="#4C0519").pack(anchor='w')
    tk.Label(card_out, textvariable=widgets['out_count_val'], font=("Consolas", 18, "bold"), fg="#F43F5E", bg="#4C0519").pack(anchor='center', pady=2)

    # Card 3: IN FRAME - Sky Blue
    card_frame = tk.Frame(cards_grid, bg="#0C4A6E", highlightbackground="#0284C7", highlightthickness=1, padx=6, pady=6)
    card_frame.grid(row=1, column=0, sticky='nsew', padx=3, pady=3)
    tk.Label(card_frame, text="● IN FRAME", font=("Segoe UI", 8, "bold"), fg="#38BDF8", bg="#0C4A6E").pack(anchor='w')
    tk.Label(card_frame, textvariable=widgets['in_frame_val'], font=("Consolas", 18, "bold"), fg="#38BDF8", bg="#0C4A6E").pack(anchor='center', pady=2)

    # Card 4: NET FLOW - Indigo
    card_net = tk.Frame(cards_grid, bg="#312E81", highlightbackground="#4F46E5", highlightthickness=1, padx=6, pady=6)
    card_net.grid(row=1, column=1, sticky='nsew', padx=3, pady=3)
    tk.Label(card_net, text="◆ NET FLOW", font=("Segoe UI", 8, "bold"), fg="#A5B4FC", bg="#312E81").pack(anchor='w')
    tk.Label(card_net, textvariable=widgets['net_flow_val'], font=("Consolas", 18, "bold"), fg="#818CF8", bg="#312E81").pack(anchor='center', pady=2)

    # Bottom Performance Readout
    perf_card = tk.Frame(count_frame, bg="#0F172A", padx=6, pady=4)
    perf_card.pack(fill='x', padx=6, pady=(2, 6))
    tk.Label(
        perf_card, textvariable=widgets['perf_stats_var'],
        font=("Consolas", 8), fg="#94A3B8", bg="#0F172A"
    ).pack(anchor='center')

    widgets['left_canvas'] = left_canvas
    widgets['scrollable_content_frame'] = scrollable_content_frame

    return widgets

def build_right_video_panel(parent_frame, callbacks):
    """
    Builds the right panel containing the video monitor,
    crosshair support, and modern video playback controls with frame stepping.
    """
    widgets = {}

    # Playback Controls Frame (Packed at bottom)
    playback_frame = tk.Frame(parent_frame, bg="#1E293B", padx=10, pady=6)
    widgets['playback_controls_frame'] = playback_frame
    playback_frame.pack(side='bottom', fill='x', pady=(6, 0))

    # Backward -5s
    widgets['step_back_btn'] = ttk.Button(
        playback_frame, text="⏪ -5s",
        command=lambda: callbacks.get('step_video_seconds', lambda s: None)(-5),
        style="Secondary.TButton", width=6
    )
    widgets['step_back_btn'].pack(side='left', padx=2)

    # Play / Pause Toggle
    widgets['play_pause_btn'] = ttk.Button(
        playback_frame, text="▶ Play",
        command=callbacks['toggle_playback'],
        style="Primary.TButton", width=8, state='disabled'
    )
    widgets['play_pause_btn'].pack(side='left', padx=4)

    # Forward +5s
    widgets['step_fwd_btn'] = ttk.Button(
        playback_frame, text="⏩ +5s",
        command=lambda: callbacks.get('step_video_seconds', lambda s: None)(5),
        style="Secondary.TButton", width=6
    )
    widgets['step_fwd_btn'].pack(side='left', padx=2)

    # Video Seek Slider
    widgets['seek_slider'] = ttk.Scale(
        playback_frame, from_=0, to=100, orient='horizontal',
        command=callbacks['on_seek_slider_moved'], state='disabled'
    )
    widgets['seek_slider'].pack(side='left', fill='x', expand=True, padx=8)

    # Timecode Label
    widgets['timecode_lbl'] = tk.Label(
        playback_frame, text="00:00 / 00:00",
        font=("Consolas", 9), fg="#94A3B8", bg="#1E293B"
    )
    widgets['timecode_lbl'].pack(side='right', padx=4)

    # Video Monitor Display (Packed to fill remaining space)
    video_container = tk.Frame(parent_frame, bg="#090D16", highlightbackground="#334155", highlightthickness=1)
    video_container.pack(fill='both', expand=True, side='top')

    widgets['video_label'] = tk.Label(
        video_container, text="Video feed standby. Select a source and click Start.",
        font=("Segoe UI", 11), fg="#64748B", bg="#090D16", anchor='center'
    )
    widgets['video_label'].pack(fill='both', expand=True)
    widgets['video_label'].bind("<Button-1>", callbacks['handle_video_click'])
    widgets['video_label'].bind("<Configure>", callbacks['on_video_label_configure'])

    return widgets

def build_status_and_progress_bar(parent_root):
    """
    Builds the sleek progress bar and status bar at the bottom of the main window.
    """
    widgets = {}
    bar_container = tk.Frame(parent_root, bg="#0F172A", padx=10, pady=2)
    bar_container.pack(fill='x', side='bottom')

    widgets['progress_bar'] = ttk.Progressbar(
        bar_container, orient='horizontal', mode='determinate',
        style='Horizontal.TProgressbar'
    )
    widgets['progress_bar'].pack(fill='x', pady=(0, 2))

    status_row = tk.Frame(bar_container, bg="#0F172A")
    status_row.pack(fill='x')

    widgets['status_label'] = tk.Label(
        status_row, text="● System Ready", anchor='w',
        font=("Segoe UI", 9), fg="#38BDF8", bg="#0F172A"
    )
    widgets['status_label'].pack(side='left')

    hw_tag = "CUDA GPU: NVIDIA GTX 1070" if torch.cuda.is_available() else "Mode: CPU"
    tag_color = "#10B981" if torch.cuda.is_available() else "#94A3B8"
    widgets['hw_tag_label'] = tk.Label(
        status_row, text=hw_tag, anchor='e',
        font=("Consolas", 9, "bold"), fg=tag_color, bg="#0F172A"
    )
    widgets['hw_tag_label'].pack(side='right')

    return widgets

def build_settings_tab_content(parent_frame, api_endpoint_var, conf_var=None, model_var=None, tracker_var=None, callbacks=None):
    """
    Builds the Diagnostics & Settings tab with AI engine configuration,
    live hardware diagnostics, and API connectivity & offline storage tools.
    """
    widgets = {}

    container = tk.Frame(parent_frame, bg="#0F172A", padx=20, pady=15)
    container.pack(fill='both', expand=True)

    # 1. Detection & AI Settings Card
    ai_frame = ttk.LabelFrame(container, text=" AI Model & Tracking Configuration ")
    ai_frame.pack(fill='x', expand=False, pady=(0, 12))

    # Model Selection
    ttk.Label(ai_frame, text="YOLOv8 Model Weight:").grid(row=0, column=0, sticky='w', padx=12, pady=8)
    model_cb = ttk.Combobox(
        ai_frame, textvariable=model_var,
        values=["yolov8n.pt", "yolov8s.pt", "yolov8m.pt"], state='readonly', width=18
    )
    model_cb.grid(row=0, column=1, sticky='w', padx=12, pady=8)
    if callbacks and 'on_model_change' in callbacks:
        model_cb.bind("<<ComboboxSelected>>", callbacks['on_model_change'])
    widgets['model_dropdown'] = model_cb

    # Tracker Selection
    ttk.Label(ai_frame, text="Tracking Engine:").grid(row=1, column=0, sticky='w', padx=12, pady=8)
    tracker_cb = ttk.Combobox(
        ai_frame, textvariable=tracker_var,
        values=["bytetrack.yaml", "botsort.yaml"], state='readonly', width=18
    )
    tracker_cb.grid(row=1, column=1, sticky='w', padx=12, pady=8)
    if callbacks and 'on_tracker_change' in callbacks:
        tracker_cb.bind("<<ComboboxSelected>>", callbacks['on_tracker_change'])
    widgets['tracker_dropdown'] = tracker_cb

    # Confidence Threshold
    ttk.Label(ai_frame, text="Detection Confidence:").grid(row=2, column=0, sticky='w', padx=12, pady=8)
    conf_slider = ttk.Scale(ai_frame, from_=0.15, to=0.85, orient='horizontal', variable=conf_var)
    conf_slider.grid(row=2, column=1, sticky='ew', padx=12, pady=8)
    widgets['conf_slider'] = conf_slider

    conf_disp_lbl = tk.Label(ai_frame, text="45%", font=("Consolas", 10, "bold"), fg="#38BDF8", bg="#1E293B")
    conf_disp_lbl.grid(row=2, column=2, sticky='w', padx=8, pady=8)
    widgets['conf_disp_lbl'] = conf_disp_lbl

    if conf_var:
        def _update_conf_disp(*args):
            try:
                val = int(float(conf_var.get()) * 100)
                conf_disp_lbl.config(text=f"{val}%")
            except Exception:
                pass
        conf_var.trace_add("write", _update_conf_disp)
        _update_conf_disp()

    ai_frame.grid_columnconfigure(1, weight=1)

    # 2. Hardware Acceleration Diagnostics Card
    hw_frame = ttk.LabelFrame(container, text=" Hardware Acceleration & GPU Diagnostics ")
    hw_frame.pack(fill='x', expand=False, pady=12)

    is_cuda = torch.cuda.is_available()
    dev_name = torch.cuda.get_device_name(0) if is_cuda else "CPU (Standard Processor)"
    cuda_ver = torch.version.cuda if is_cuda else "N/A"

    tk.Label(hw_frame, text="Inference Device:", font=("Segoe UI", 9, "bold"), fg="#94A3B8", bg="#1E293B").grid(row=0, column=0, sticky='w', padx=12, pady=6)
    tk.Label(hw_frame, text=dev_name, font=("Segoe UI", 10, "bold"), fg="#F8FAFC", bg="#1E293B").grid(row=0, column=1, sticky='w', padx=12, pady=6)

    tk.Label(hw_frame, text="Acceleration Status:", font=("Segoe UI", 9, "bold"), fg="#94A3B8", bg="#1E293B").grid(row=1, column=0, sticky='w', padx=12, pady=6)
    hw_status_text = f"● CUDA {cuda_ver} ACTIVE (Hardware Accelerated)" if is_cuda else "○ CPU Only"
    hw_status_color = "#10B981" if is_cuda else "#F59E0B"
    tk.Label(hw_frame, text=hw_status_text, font=("Segoe UI", 9, "bold"), fg=hw_status_color, bg="#1E293B").grid(row=1, column=1, sticky='w', padx=12, pady=6)

    tk.Label(hw_frame, text="Inference Mode:", font=("Segoe UI", 9, "bold"), fg="#94A3B8", bg="#1E293B").grid(row=2, column=0, sticky='w', padx=12, pady=6)
    prec_text = "FP16 Half-Precision (10x-15x High Speed)" if is_cuda else "FP32 Single-Precision"
    tk.Label(hw_frame, text=prec_text, font=("Segoe UI", 9), fg="#38BDF8", bg="#1E293B").grid(row=2, column=1, sticky='w', padx=12, pady=6)

    # 3. Cloud API & Offline Queue Management Card
    api_frame = ttk.LabelFrame(container, text=" Cloud API & Offline Queue Synchronization ")
    api_frame.pack(fill='x', expand=False, pady=12)

    ttk.Label(api_frame, text="API Endpoint URL:").grid(row=0, column=0, sticky='w', padx=12, pady=8)
    widgets['api_entry'] = ttk.Entry(api_frame, textvariable=api_endpoint_var, width=60)
    widgets['api_entry'].grid(row=0, column=1, sticky='ew', padx=12, pady=8)

    # Test Ping Button & Status
    test_btn_frame = tk.Frame(api_frame, bg="#1E293B")
    test_btn_frame.grid(row=1, column=1, sticky='w', padx=12, pady=4)

    widgets['test_api_btn'] = ttk.Button(
        test_btn_frame, text="⚡ Test Connection",
        command=callbacks.get('test_api_connection', lambda: None),
        style="Primary.TButton"
    )
    widgets['test_api_btn'].pack(side='left', padx=(0, 10))

    widgets['api_test_status'] = tk.Label(
        test_btn_frame, text="● Click to test API reachability",
        font=("Segoe UI", 9), fg="#94A3B8", bg="#1E293B"
    )
    widgets['api_test_status'].pack(side='left')

    # Offline Queue Controls
    ttk.Label(api_frame, text="Local SQLite Cache:").grid(row=2, column=0, sticky='w', padx=12, pady=10)
    queue_row = tk.Frame(api_frame, bg="#1E293B")
    queue_row.grid(row=2, column=1, sticky='w', padx=12, pady=10)

    widgets['offline_count_lbl'] = tk.Label(
        queue_row, text="Cached records queued",
        font=("Segoe UI", 9, "bold"), fg="#38BDF8", bg="#1E293B"
    )
    widgets['offline_count_lbl'].pack(side='left', padx=(0, 15))

    widgets['sync_offline_btn'] = ttk.Button(
        queue_row, text="↻ Sync Now",
        command=callbacks.get('sync_offline_cache', lambda: None),
        style="Secondary.TButton"
    )
    widgets['sync_offline_btn'].pack(side='left', padx=4)

    widgets['export_csv_btn'] = ttk.Button(
        queue_row, text="📥 Export to CSV",
        command=callbacks.get('export_offline_csv', lambda: None),
        style="Secondary.TButton"
    )
    widgets['export_csv_btn'].pack(side='left', padx=4)

    api_frame.grid_columnconfigure(1, weight=1)

    return widgets