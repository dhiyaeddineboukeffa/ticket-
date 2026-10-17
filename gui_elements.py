import tkinter as tk
from tkinter import ttk

def build_notebook_tabs(parent_root, notebook):
    """
    Builds the main and settings tabs for the ttk.Notebook.
    Returns the main_tab_frame and settings_tab_frame.
    """
    main_tab_frame = ttk.Frame(notebook, style="TFrame")
    notebook.add(main_tab_frame, text="Main")

    settings_tab_frame = ttk.Frame(notebook, style="TFrame")
    notebook.add(settings_tab_frame, text="Settings")

    return main_tab_frame, settings_tab_frame

def build_left_control_panel(parent_frame, video_source_var, video_path_var,
                             ip_url_var, webcam_index_var, callbacks):
    """
    Builds the left control panel with video source selection, line drawing,
    start/stop buttons, and live counts. Includes a scrollbar.
    Returns a dictionary of relevant widgets and ttk.StringVar objects.
    """
    # Create a Canvas within the left_panel
    left_canvas = tk.Canvas(parent_frame, bg="#F0F8FF", highlightthickness=0)
    left_canvas.pack(side="left", fill="both", expand=True)

    # Create a Scrollbar and link it to the canvas
    left_scrollbar = ttk.Scrollbar(parent_frame, orient="vertical", command=left_canvas.yview)
    left_scrollbar.pack(side="right", fill="y")
    left_canvas.configure(yscrollcommand=left_scrollbar.set)

    # Create a frame inside the canvas to hold the actual content
    scrollable_content_frame = ttk.Frame(left_canvas, style="TFrame")
    # Add that frame to a window in the canvas
    canvas_window = left_canvas.create_window((0, 0), window=scrollable_content_frame, anchor="nw")

    # Configure canvas scroll region when the inner frame changes size
    scrollable_content_frame.bind("<Configure>",
        lambda e: left_canvas.configure(scrollregion=left_canvas.bbox("all"))
    )
    # Make the canvas itself responsive to resize (e.g., when main window resizes)
    left_canvas.bind('<Configure>', lambda e: callbacks['on_left_canvas_configure'](e, left_canvas, canvas_window))


    widgets = {}

    # Video Source
    source_frame = ttk.LabelFrame(scrollable_content_frame, text="1. Video Source")
    source_frame.pack(fill='x', pady=5, padx=5)

    ttk.Radiobutton(source_frame, text="Video File", variable=video_source_var, value="video", command=callbacks['on_source_change']).pack(anchor='w', padx=5)
    widgets['file_button'] = ttk.Button(source_frame, text="Select File", command=callbacks['select_file'])
    widgets['file_button'].pack(fill='x', padx=5, pady=2)
    widgets['video_path_label'] = ttk.Label(source_frame, textvariable=video_path_var, wraplength=270)
    widgets['video_path_label'].pack(anchor='w', padx=5, pady=2)

    ttk.Radiobutton(source_frame, text="Webcam", variable=video_source_var, value="webcam", command=callbacks['on_source_change']).pack(anchor='w', padx=5)
    widgets['webcam_dropdown'] = ttk.Combobox(source_frame, textvariable=webcam_index_var, state='readonly', width=10)
    widgets['webcam_dropdown'].pack(fill='x', padx=5, pady=2)
    widgets['webcam_dropdown'].bind("<<ComboboxSelected>>", callbacks['on_webcam_selected'])

    ttk.Radiobutton(source_frame, text="IP Camera", variable=video_source_var, value="ipcam", command=callbacks['on_source_change']).pack(anchor='w', padx=5)
    widgets['ip_entry'] = ttk.Entry(source_frame, textvariable=ip_url_var, width=30, state='disabled')
    widgets['ip_entry'].pack(fill='x', padx=5, pady=2)

    # Line Drawing
    line_frame = ttk.LabelFrame(scrollable_content_frame, text="2. Define Counting Line")
    line_frame.pack(fill='x', pady=10, padx=5)
    widgets['draw_line_btn'] = ttk.Button(line_frame, text="Draw New Line", command=callbacks['start_drawing'])
    widgets['draw_line_btn'].pack(fill='x', padx=5, pady=5)
    widgets['switch_dir_btn'] = ttk.Button(line_frame, text="Switch IN/OUT Direction", command=callbacks['switch_direction'])
    widgets['switch_dir_btn'].pack(fill='x', padx=5, pady=5)
    widgets['instruction_label'] = ttk.Label(line_frame, text="Load video before drawing.", wraplength=270)
    widgets['instruction_label'].pack(fill='x', padx=5, pady=5)

    # Start/Stop
    run_frame = ttk.LabelFrame(scrollable_content_frame, text="3. Run Analysis")
    run_frame.pack(fill='x', pady=10, padx=5)
    widgets['start_btn'] = ttk.Button(run_frame, text="Start", command=callbacks['start_processing'])
    widgets['start_btn'].pack(fill='x', padx=5, pady=5)
    widgets['stop_btn'] = ttk.Button(run_frame, text="Stop", command=callbacks['stop_processing'], state='disabled')
    widgets['stop_btn'].pack(fill='x', padx=5, pady=5)

    # Counts
    count_frame = ttk.LabelFrame(scrollable_content_frame, text="Live Counts")
    count_frame.pack(fill='x', pady=10, padx=5)
    widgets['in_count_var'] = tk.StringVar(value="IN: 0")
    widgets['out_count_var'] = tk.StringVar(value="OUT: 0")
    widgets['people_in_frame_var'] = tk.StringVar(value="In Frame: 0")
    widgets['perf_stats_var'] = tk.StringVar(value="Performance: Ready")
    ttk.Label(count_frame, textvariable=widgets['in_count_var'], style="Count.TLabel", foreground="green").pack(padx=5, pady=3)
    ttk.Label(count_frame, textvariable=widgets['out_count_var'], style="Count.TLabel", foreground="red").pack(padx=5, pady=3)
    ttk.Label(count_frame, textvariable=widgets['people_in_frame_var'], style="Count.TLabel", foreground="blue").pack(padx=5, pady=3)
    ttk.Label(count_frame, textvariable=widgets['perf_stats_var'], style="Status.TLabel").pack(padx=5, pady=(2, 5))

    widgets['left_canvas'] = left_canvas # Store canvas reference
    widgets['scrollable_content_frame'] = scrollable_content_frame # Store inner frame reference

    return widgets

def build_right_video_panel(parent_frame, callbacks):
    """
    Builds the right panel containing the video display and playback controls.
    Returns a dictionary of relevant widgets.
    """
    widgets = {}

    # Playback Controls Frame (for video files) - Packed first to be at the bottom
    widgets['playback_controls_frame'] = ttk.Frame(parent_frame, style="TFrame")
    widgets['playback_controls_frame'].pack(side='bottom', fill='x', pady=(5,0))

    widgets['play_pause_btn'] = ttk.Button(widgets['playback_controls_frame'], text="Play", command=callbacks['toggle_playback'], state='disabled')
    widgets['play_pause_btn'].pack(side='left', padx=5, pady=2)

    widgets['seek_slider'] = ttk.Scale(widgets['playback_controls_frame'], from_=0, to=100, orient='horizontal',
                                     command=callbacks['on_seek_slider_moved'], state='disabled')
    widgets['seek_slider'].pack(side='left', fill='x', expand=True, padx=5, pady=2)

    # Video Display - Packed second to fill space above controls
    widgets['video_label'] = ttk.Label(parent_frame, text="Video feed will appear here.", anchor='center', style="Bold.TLabel")
    widgets['video_label'].pack(fill='both', expand=True, side='top', anchor="nw")
    widgets['video_label'].bind("<Button-1>", callbacks['handle_video_click'])
    widgets['video_label'].bind("<Configure>", callbacks['on_video_label_configure'])

    return widgets

def build_status_and_progress_bar(parent_root):
    """
    Builds the progress bar and status bar at the bottom of the main window.
    Returns a dictionary of relevant widgets.
    """
    widgets = {}
    widgets['progress_bar'] = ttk.Progressbar(parent_root, orient='horizontal', length=100, mode='determinate', style='Horizontal.TProgressbar')
    widgets['progress_bar'].pack(fill='x', padx=10, pady=(0, 5))

    widgets['status_label'] = ttk.Label(parent_root, text="Ready.", anchor='w', style="Status.TLabel")
    widgets['status_label'].pack(fill='x', padx=10, pady=(0, 5))

    return widgets

def build_settings_tab_content(parent_frame, api_endpoint_var, conf_var=None, model_var=None, tracker_var=None, callbacks=None):
    """
    Builds the content for the settings tab: AI model, tracker, confidence threshold, and API settings.
    Returns a dictionary of relevant widgets.
    """
    widgets = {}

    # 1. Detection & AI Settings
    ai_frame = ttk.LabelFrame(parent_frame, text="AI Model & Tracker Settings")
    ai_frame.pack(fill='x', expand=False, padx=20, pady=(15, 10))

    # Model Selection
    ttk.Label(ai_frame, text="YOLO Model:").grid(row=0, column=0, sticky='w', padx=10, pady=8)
    model_cb = ttk.Combobox(ai_frame, textvariable=model_var, values=["yolov8n.pt", "yolov8s.pt"], state='readonly', width=18)
    model_cb.grid(row=0, column=1, sticky='w', padx=10, pady=8)
    if callbacks and 'on_model_change' in callbacks:
        model_cb.bind("<<ComboboxSelected>>", callbacks['on_model_change'])
    widgets['model_dropdown'] = model_cb

    # Tracker Selection
    ttk.Label(ai_frame, text="Tracker Algorithm:").grid(row=1, column=0, sticky='w', padx=10, pady=8)
    tracker_cb = ttk.Combobox(ai_frame, textvariable=tracker_var, values=["bytetrack.yaml", "botsort.yaml"], state='readonly', width=18)
    tracker_cb.grid(row=1, column=1, sticky='w', padx=10, pady=8)
    if callbacks and 'on_tracker_change' in callbacks:
        tracker_cb.bind("<<ComboboxSelected>>", callbacks['on_tracker_change'])
    widgets['tracker_dropdown'] = tracker_cb

    # Confidence Threshold
    ttk.Label(ai_frame, text="Detection Confidence:").grid(row=2, column=0, sticky='w', padx=10, pady=8)
    conf_slider = ttk.Scale(ai_frame, from_=0.15, to=0.85, orient='horizontal', variable=conf_var)
    conf_slider.grid(row=2, column=1, sticky='ew', padx=10, pady=8)
    widgets['conf_slider'] = conf_slider

    conf_disp_lbl = ttk.Label(ai_frame, text="45%")
    conf_disp_lbl.grid(row=2, column=2, sticky='w', padx=5, pady=8)
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

    # 2. API Settings
    api_settings_frame = ttk.LabelFrame(parent_frame, text="API Settings")
    api_settings_frame.pack(fill='x', expand=False, padx=20, pady=10)

    ttk.Label(api_settings_frame, text="API Endpoint URL:").grid(row=0, column=0, sticky='w', padx=10, pady=8)
    widgets['api_entry'] = ttk.Entry(api_settings_frame, textvariable=api_endpoint_var, width=80)
    widgets['api_entry'].grid(row=0, column=1, sticky='ew', padx=10, pady=8)

    ttk.Label(api_settings_frame, text="(Data is sent automatically upon stopping analysis; offline entries are cached locally in SQLite)").grid(row=1, column=1, sticky='w', padx=10, pady=2)
    api_settings_frame.grid_columnconfigure(1, weight=1)

    return widgets