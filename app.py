import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import time
from datetime import datetime
import os
import requests 

# Import refactored modules
from camera_manager import CameraManager
from video_playback_controls import VideoPlaybackControls
from app_logger import AppLogger
from settings_manager import SettingsManager
from video_processor import VideoProcessor
from offline_manager import OfflineManager

# Import new UI-related modules
import gui_elements
from event_handlers import EventHandlers
from video_display_manager import VideoDisplayManager

class PeopleCounterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("People Counter v2.0")
        self.root.geometry("1280x720")
        self.root.configure(bg="#F0F8FF")

        # --- Initialize Managers and Core Logic ---
        self.settings_manager = SettingsManager()
        self.logger = AppLogger()
        self.camera_manager = CameraManager()
        self.video_playback_controls = VideoPlaybackControls()
        self.processor = VideoProcessor(model_path='yolov8n.pt', class_list_path='coco.txt', conf_threshold=0.45, tracker_type='bytetrack.yaml')
        self.offline_manager = OfflineManager()

        # --- State Variables (Tkinter StringVars for UI binding) ---
        self.video_source_var = tk.StringVar()
        self.video_path_var = tk.StringVar()
        self.ip_url_var = tk.StringVar()
        self.webcam_index_var = tk.IntVar(value=0)
        self.api_endpoint_var = tk.StringVar() 
        self.conf_var = tk.DoubleVar(value=0.45)
        self.model_var = tk.StringVar(value="yolov8n.pt")
        self.tracker_var = tk.StringVar(value="bytetrack.yaml") 

        # --- Application Internal State ---
        self.cap = None
        self.running = False
        self.drawing_line = False
        self.line_coords = []

        self.log_data = [] # Data collected for API export
        self._log_lock = threading.Lock()
        self._ui_update_pending = False
        self.start_time = None
        self.video_thread = None

        # --- UI Initialization ---
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self._configure_styles()

        # Dictionary to hold references to UI widgets created by gui_elements
        self.widgets = {}

        # Initialize EventHandlers *before* building the UI
        self.event_handlers = EventHandlers(self)

        self.video_display_manager = None # Placeholder, initialized after _build_ui

        self._build_ui() # Build the UI layout

        # Now that self.widgets['video_label'] exists, initialize VideoDisplayManager properly
        self.video_display_manager = VideoDisplayManager(self.widgets['video_label'])

        # IMPORTANT: Re-bind the configure event now that video_display_manager is fully initialized
        self.widgets['video_label'].bind("<Configure>", self.video_display_manager._on_video_label_configure)


        # --- Load Settings and Initial State ---
        self.load_initial_settings()
        self.update_webcam_list()
        self.event_handlers.on_source_change()

    def _configure_styles(self):
        """Configures dark slate ttk styles for the modern operations console."""
        self.root.configure(bg="#0F172A")
        
        self.style.configure(".", background="#0F172A", foreground="#F8FAFC")
        self.style.configure("TFrame", background="#0F172A")
        self.style.configure("LeftPanel.TFrame", background="#0F172A")
        self.style.configure("Card.TFrame", background="#1E293B")
        
        self.style.configure("TLabelframe", background="#1E293B", bordercolor="#334155", relief="flat")
        self.style.configure("TLabelframe.Label", background="#1E293B", foreground="#38BDF8", font=("Segoe UI", 9, "bold"))
        
        self.style.configure("TLabel", background="#1E293B", foreground="#F8FAFC", font=("Segoe UI", 9))
        self.style.configure("Bold.TLabel", background="#1E293B", foreground="#F8FAFC", font=("Segoe UI", 12, "bold"))
        self.style.configure("Count.TLabel", background="#1E293B", font=("Consolas", 18, "bold"))
        self.style.configure("Status.TLabel", background="#0F172A", font=("Segoe UI", 9), foreground="#38BDF8")
        self.style.configure("Error.Status.TLabel", background="#0F172A", font=("Segoe UI", 9, "bold"), foreground="#EF4444")
        
        self.style.configure("TNotebook", background="#0F172A", borderwidth=0)
        self.style.configure("TNotebook.Tab", background="#1E293B", foreground="#94A3B8", padding=[14, 6], font=("Segoe UI", 9, "bold"))
        self.style.map("TNotebook.Tab", background=[("selected", "#2563EB")], foreground=[("selected", "#FFFFFF")])
        
        # Action Buttons
        self.style.configure("TButton", background="#334155", foreground="#FFFFFF", borderwidth=0, padding=5, font=("Segoe UI", 9, "bold"))
        self.style.map("TButton", background=[("active", "#475569"), ("disabled", "#1E293B")], foreground=[("disabled", "#64748B")])
        
        self.style.configure("Primary.TButton", background="#2563EB", foreground="#FFFFFF", borderwidth=0, padding=5, font=("Segoe UI", 9, "bold"))
        self.style.map("Primary.TButton", background=[("active", "#1D4ED8"), ("disabled", "#1E293B")], foreground=[("disabled", "#64748B")])
        
        self.style.configure("Secondary.TButton", background="#334155", foreground="#F8FAFC", borderwidth=0, padding=4, font=("Segoe UI", 9))
        self.style.map("Secondary.TButton", background=[("active", "#475569"), ("disabled", "#1E293B")], foreground=[("disabled", "#64748B")])
        
        self.style.configure("Start.TButton", background="#10B981", foreground="#FFFFFF", borderwidth=0, padding=6, font=("Segoe UI", 10, "bold"))
        self.style.map("Start.TButton", background=[("active", "#059669"), ("disabled", "#1E293B")], foreground=[("disabled", "#64748B")])
        
        self.style.configure("Stop.TButton", background="#EF4444", foreground="#FFFFFF", borderwidth=0, padding=6, font=("Segoe UI", 10, "bold"))
        self.style.map("Stop.TButton", background=[("active", "#DC2626"), ("disabled", "#1E293B")], foreground=[("disabled", "#64748B")])
        
        self.style.configure("TRadiobutton", background="#1E293B", foreground="#F8FAFC", font=("Segoe UI", 9))
        self.style.map("TRadiobutton", background=[("active", "#1E293B")], foreground=[("active", "#38BDF8")])
        
        self.style.configure("TEntry", fieldbackground="#0F172A", foreground="#F8FAFC", bordercolor="#334155", insertcolor="#FFFFFF")
        self.style.configure("TCombobox", fieldbackground="#0F172A", background="#334155", foreground="#F8FAFC", arrowcolor="#F8FAFC", bordercolor="#334155")
        self.style.map("TCombobox", fieldbackground=[("readonly", "#0F172A")], selectbackground=[("readonly", "#1E293B")], selectforeground=[("readonly", "#38BDF8")])
        
        self.style.configure("Horizontal.TProgressbar", thickness=4, troughcolor="#1E293B", background="#10B981", bordercolor="#334155")
        self.style.configure("Horizontal.TScale", background="#1E293B", troughcolor="#0F172A", sliderlength=14, bordercolor="#334155")

    def _build_ui(self):
        """Assembles the UI using components from gui_elements.py."""
        self.root.title("People Counter Pro v2.0 - AI Vision Analytics")
        self.root.bind("<Escape>", self.event_handlers.cancel_drawing)
        self.root.bind("<space>", lambda e: self.event_handlers.toggle_playback())

        # Main notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=8, pady=8)

        main_tab_frame, settings_tab_frame = gui_elements.build_notebook_tabs(self.root, self.notebook)
        
        # Main frame within the main tab, uses grid for left/right panels
        main_frame = ttk.Frame(main_tab_frame)
        main_frame.pack(fill='both', expand=True)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=0)
        main_frame.grid_columnconfigure(1, weight=1)

        left_panel = ttk.Frame(main_frame)
        left_panel.grid(row=0, column=0, sticky='nsew', padx=(0, 8))

        right_panel = ttk.Frame(main_frame)
        right_panel.grid(row=0, column=1, sticky='nsew')

        # Build left control panel (with scrollbar)
        left_panel_callbacks = {
            'on_source_change': self.event_handlers.on_source_change,
            'select_file': self.event_handlers.select_file,
            'on_webcam_selected': self.event_handlers.on_webcam_selected,
            'start_drawing': self.event_handlers.start_drawing,
            'cancel_drawing': self.event_handlers.cancel_drawing,
            'clear_line': self.event_handlers.clear_line,
            'switch_direction': self.event_handlers.switch_direction,
            'reset_counts': self.event_handlers.reset_counts,
            'start_processing': self.event_handlers.start_processing,
            'stop_processing': self.event_handlers.stop_processing,
            'on_left_canvas_configure': self.event_handlers.on_left_canvas_configure
        }
        self.widgets.update(gui_elements.build_left_control_panel(
            left_panel, self.video_source_var, self.video_path_var,
            self.ip_url_var, self.webcam_index_var, left_panel_callbacks
        ))

        # Build right video panel
        right_panel_callbacks = {
            'toggle_playback': self.event_handlers.toggle_playback,
            'on_seek_slider_moved': self.event_handlers.on_seek_slider_moved,
            'step_video_seconds': self.event_handlers.step_video_seconds,
            'handle_video_click': self.event_handlers.handle_video_click,
            'on_video_label_configure': lambda e: None # Temporarily set, re-bound later
        }
        self.widgets.update(gui_elements.build_right_video_panel(right_panel, right_panel_callbacks))

        # Build status bar and progress bar (at root level)
        self.widgets.update(gui_elements.build_status_and_progress_bar(self.root))

        # Build settings tab content, passing AI and API configuration
        settings_callbacks = {
            'on_model_change': self._on_model_selected,
            'on_tracker_change': self._on_tracker_selected,
            'test_api_connection': self.event_handlers.test_api_connection,
            'sync_offline_cache': self.event_handlers.sync_offline_cache,
            'export_offline_csv': self.event_handlers.export_offline_csv
        }
        self.conf_var.trace_add("write", self._on_conf_changed)

        self.widgets.update(gui_elements.build_settings_tab_content(
            settings_tab_frame, self.api_endpoint_var,
            self.conf_var, self.model_var, self.tracker_var, settings_callbacks
        ))

    def _on_model_selected(self, event=None):
        selected_model = self.model_var.get()
        self.processor.reload_model(selected_model)
        self.settings_manager.update_setting("model_name", selected_model)
        self.logger.info(f"YOLO Model switched to: {selected_model}")
        self.update_status(f"Loaded model: {selected_model}")

    def _on_tracker_selected(self, event=None):
        selected_tracker = self.tracker_var.get()
        self.processor.set_tracker(selected_tracker)
        self.settings_manager.update_setting("tracker_type", selected_tracker)
        self.logger.info(f"Tracker switched to: {selected_tracker}")
        self.update_status(f"Using tracker: {selected_tracker}")

    def _on_conf_changed(self, *args):
        try:
            val = float(self.conf_var.get())
            self.processor.set_confidence(val)
            self.settings_manager.update_setting("conf_threshold", val)
        except Exception:
            pass

    def load_initial_settings(self):
        """Loads settings from SettingsManager and applies them to UI."""
        settings = self.settings_manager.load_settings()

        # Apply video source settings
        self.video_source_var.set(settings.get("video_source_type", "video"))
        self.video_path_var.set(settings.get("video_path", ""))
        self.ip_url_var.set(settings.get("ip_url", ""))
        self.webcam_index_var.set(settings.get("webcam_index", 0))

        # Apply line settings
        self.line_coords = settings.get("line_coords", [])
        if self.line_coords:
            self.processor.set_line_and_direction(self.line_coords)
            self.widgets['instruction_label'].config(text="Saved line loaded. Click 'Draw New Line' to change it.")

        direction_swapped = settings.get("direction_swapped", False)
        self.processor.set_direction_swapped(direction_swapped)

        # AI & Tracker Settings
        conf = float(settings.get("conf_threshold", 0.45))
        self.conf_var.set(conf)
        self.processor.set_confidence(conf)

        model_name = settings.get("model_name", "yolov8n.pt")
        self.model_var.set(model_name)
        if model_name != self.processor.model_path:
            self.processor.reload_model(model_name)

        tracker_name = settings.get("tracker_type", "bytetrack.yaml")
        self.tracker_var.set(tracker_name)
        self.processor.set_tracker(tracker_name)

        # Load API Endpoint from settings
        self.api_endpoint_var.set(settings.get("api_endpoint", "https://tramcreditalgeria.up.railway.app/api/transaction/Passenger"))

        if 'offline_count_lbl' in self.widgets:
            pending_count = self.offline_manager.get_pending_count()
            self.widgets['offline_count_lbl'].config(text=f"{pending_count} records cached in SQLite")

        self.logger.info("Settings loaded.")
        self.update_status("Settings loaded.")

    def update_webcam_list(self):
        """Starts asynchronous detection of webcams to prevent UI freeze on startup."""
        self.logger.info("Detecting webcams...")
        self.update_status("Detecting webcams...")
        threading.Thread(target=self._run_webcam_detection, daemon=True).start()

    def _run_webcam_detection(self):
        """Runs webcam discovery in a background thread."""
        available_cams = self.camera_manager.get_available_webcams()
        self.root.after(0, lambda: self._apply_webcam_list(available_cams))

    def _apply_webcam_list(self, available_cams):
        """Applies detected webcams to the dropdown widget on the main thread."""
        if not available_cams:
            self.widgets['webcam_dropdown']['values'] = ["No cameras found"]
            self.webcam_index_var.set("N/A")
            self.widgets['webcam_dropdown'].config(state='disabled')
            self.logger.warning("No webcams detected.")
            self.update_status("No webcams detected.", is_error=True)
        else:
            self.widgets['webcam_dropdown']['values'] = available_cams
            if self.webcam_index_var.get() not in available_cams:
                self.webcam_index_var.set(available_cams[0])
            self.widgets['webcam_dropdown'].config(state='readonly')
            self.logger.info(f"Detected webcams: {available_cams}")
            self.update_status(f"Detected webcams: {available_cams}")

    def load_first_frame(self):
        """
        Loads the first frame of the selected video source for preview and line drawing.
        If current cap is active, release it first.
        """
        self.update_status("Loading first frame for preview...")
        self.logger.info("Attempting to load first frame for preview.")
        if self.cap:
            self.cap.release()
            self.cap = None

        source_type = self.video_source_var.get()
        source_path = ""
        if source_type == "video":
            source_path = self.video_path_var.get()
        elif source_type == "webcam":
            source_path = self.webcam_index_var.get()
        elif source_type == "ipcam":
            source_path = self.ip_url_var.get()

        self.cap = self.camera_manager.open_video_source(source_type, source_path)
        if self.cap:
            ret, frame = self.cap.read()
            if ret:
                self.video_display_manager.set_original_frame_dimensions(frame.shape[1], frame.shape[0])
                self.video_display_manager.show_frame(frame, self.line_coords, self.processor, self.logger)

                # If it's a video file, set up playback controls
                if source_type == "video":
                    self.video_playback_controls.set_video_capture(self.cap)
                    total_frames = self.video_playback_controls.get_total_frames()
                    self.widgets['seek_slider'].config(to=total_frames)
                    self.widgets['seek_slider'].set(0)
                    self.widgets['play_pause_btn'].config(text="Play", state='normal')
                    self.widgets['seek_slider'].config(state='normal')
                else: # Disable playback controls for webcam/ipcam
                    self.video_playback_controls.release()
                    self.widgets['play_pause_btn'].config(text="Play", state='disabled')
                    self.widgets['seek_slider'].config(state='disabled')

                self.logger.info("First frame loaded successfully.")
                self.update_status("Video source loaded for preview.")
            else:
                self.logger.error("Failed to read first frame from source.")
                self.update_status("Failed to read first frame from source.", is_error=True)
                self.video_display_manager.clear_display("Failed to load video. Check source.")
                if self.cap:
                    self.cap.release()
                    self.cap = None
        else:
            self.logger.error(f"Failed to open video source: {source_path}")
            self.update_status(f"Failed to open video source: {source_path}", is_error=True)
            self.video_display_manager.clear_display("Failed to load video. Check source.")
            self.video_playback_controls.release()
            self.widgets['play_pause_btn'].config(text="Play", state='disabled')
            self.widgets['seek_slider'].config(state='disabled')


        if not self.line_coords and self.cap:
            self.widgets['instruction_label'].config(text="Video loaded. Click 'Draw Line' then click twice on the video to set a line.")
        elif self.line_coords and self.cap:
             self.widgets['instruction_label'].config(text="Saved line loaded. Click 'Draw New Line' to change it.")
        else:
            self.widgets['instruction_label'].config(text="Load video before drawing.")


    def start_processing_logic(self):
        """Contains the core logic to start video processing."""
        if self.running: return
        if not self.line_coords or len(self.line_coords) < 2:
            messagebox.showwarning("No Line", "Please draw or load a counting line first.")
            self.logger.warning("Attempted to start processing without a counting line.")
            self.update_status("Define counting line first.", is_error=True)
            return

        self.update_status("Opening video source...")

        # Open video source (will get a new cap if one exists and is released)
        current_source_type = self.video_source_var.get()
        current_source_path = ""
        if current_source_type == "video":
            current_source_path = self.video_path_var.get()
            self.video_playback_controls.release() # Release any preview cap
        elif current_source_type == "webcam":
            current_source_path = self.webcam_index_var.get()
        elif current_source_type == "ipcam":
            current_source_path = self.ip_url_var.get()

        self.cap = self.camera_manager.open_video_source(current_source_type, current_source_path)

        if not self.cap:
            messagebox.showerror("Error", f"Failed to open video source: {current_source_path}")
            self.logger.error(f"Failed to open video source: {current_source_path}. Processing aborted.")
            self.update_status(f"Failed to open video source: {current_source_path}", is_error=True)
            return

        # Set video playback controls for processing if it's a video file
        if current_source_type == "video":
            self.video_playback_controls.set_video_capture(self.cap)
            self.video_playback_controls.play()
            self.widgets['play_pause_btn'].config(text="Pause", state='normal')
            self.widgets['seek_slider'].config(state='normal')
            self.widgets['seek_slider'].config(to=self.video_playback_controls.get_total_frames())
        else:
            self.video_playback_controls.release()
            self.widgets['play_pause_btn'].config(state='disabled')
            self.widgets['seek_slider'].config(state='disabled')

        self.running = True
        self.widgets['start_btn'].config(state='disabled')
        self.widgets['stop_btn'].config(state='normal')
        self.widgets['draw_line_btn'].config(state='disabled')
        self.widgets['switch_dir_btn'].config(state='disabled')
        self.start_time = datetime.now()
        self.log_data.clear()

        self.logger.info(f"Started processing from {current_source_type} source: {current_source_path}")
        self.update_status("Processing started...")
        self.widgets['progress_bar'].config(mode='indeterminate')
        self.widgets['progress_bar'].start()

        self.video_thread = threading.Thread(target=self.video_loop, daemon=True)
        self.video_thread.start()

        # Save current video source selection to settings
        self.settings_manager.update_setting("video_source_type", current_source_type)
        if current_source_type == "video":
            self.settings_manager.update_setting("video_path", self.video_path_var.get())
        elif current_source_type == "webcam":
            self.settings_manager.update_setting("webcam_index", self.webcam_index_var.get())
        elif current_source_type == "ipcam":
            self.settings_manager.update_setting("ip_url", self.ip_url_var.get())

    def stop_processing_logic(self):
        """Contains the core logic to stop video processing."""
        if not self.running: return
        self.running = False
        self.logger.info("Stopping processing.")
        self.update_status("Stopping processing...")

        if self.video_thread:
             self.video_thread.join(timeout=2.0)

        self.widgets['start_btn'].config(state='normal')
        self.widgets['stop_btn'].config(state='disabled')
        self.widgets['draw_line_btn'].config(state='normal')
        self.widgets['switch_dir_btn'].config(state='normal')

        # Reset playback controls
        self.widgets['play_pause_btn'].config(text="Play", state='disabled')
        self.widgets['seek_slider'].config(state='disabled')
        self.widgets['progress_bar'].stop()
        self.widgets['progress_bar'].config(value=0, mode='determinate')

        if self.cap:
            self.cap.release()
            self.cap = None
        self.video_playback_controls.release()

        with self._log_lock:
            data_to_send = list(self.log_data)
            self.log_data.clear()

        if data_to_send:
            threading.Thread(target=self._send_data_async, args=(data_to_send,), daemon=True).start()

        self.processor.reset()
        self.widgets['in_count_var'].set("IN: 0")
        self.widgets['out_count_var'].set("OUT: 0")
        self.widgets['people_in_frame_var'].set("In Frame: 0")
        self.update_status("Processing stopped. Ready.")
        self.logger.info("Processing stopped.")

    def video_loop(self):
        log_interval = 1.0
        last_log_time = time.time()

        while self.running:
            frame = None
            ret = False

            if self.video_source_var.get() == "video":
                if self.video_playback_controls.is_playing():
                    ret, frame = self.video_playback_controls.get_frame()
                else:
                    time.sleep(0.1) # Idle while paused — prevents 100% CPU/GPU spin
                    continue

                if ret and self.video_playback_controls.cap:
                    current_frame_pos = self.video_playback_controls.get_current_frame_pos()
                    total_frames = self.video_playback_controls.get_total_frames()
                    if total_frames > 0:
                        progress_percent = (current_frame_pos / total_frames) * 100
                        self.root.after(0, lambda p=progress_percent: self.widgets['progress_bar'].config(value=p, mode='determinate'))
                        self.root.after(0, lambda v=current_frame_pos: self.widgets['seek_slider'].set(v))
                    else:
                        self.root.after(0, lambda: self.widgets['progress_bar'].config(mode='indeterminate'))
            else: # Webcam or IP Camera
                if self.cap:
                    ret, frame = self.cap.read()
                else:
                    ret, frame = False, None
                self.root.after(0, lambda: self.widgets['progress_bar'].config(mode='indeterminate'))


            if not ret:
                self.logger.info("End of video stream or error reading frame. Stopping processing.")
                self.root.after(0, self.stop_processing_logic)
                break

            frame, in_c, out_c, people_in_frame = self.processor.process_frame(frame)
            if not self._ui_update_pending:
                self._ui_update_pending = True
                self.root.after(0, lambda f=frame, i=in_c, o=out_c, p=people_in_frame: self._update_ui_frame(f, i, o, p))

            if time.time() - last_log_time >= log_interval:
                # Store data in the new format for API
                timestamp_iso = datetime.now().isoformat(timespec='seconds') # ISO format string
                with self._log_lock:
                    self.log_data.append({
                        'createdAt': timestamp_iso, # Renamed from 'timestamp'
                        'in': self.processor.counter_in,
                        'out': self.processor.counter_out,
                        'inFrame': self.processor.people_in_frame # Renamed from 'in_frame'
                    })
                last_log_time = time.time()
                self.logger.debug(f"Logged data: createdAt={timestamp_iso}, IN={in_c}, OUT={out_c}, InFrame={people_in_frame}")

        if self.running:
            self.root.after(0, self.stop_processing_logic)

    def _update_ui_frame(self, frame, in_c, out_c, people_in_frame):
        """Updates live counts, performance stats, and renders video frame without queue flooding."""
        self._update_live_counts(in_c, out_c, people_in_frame)
        if hasattr(self.processor, 'last_fps') and 'perf_stats_var' in self.widgets:
            dev_label = "GPU (CUDA)" if getattr(self.processor, 'device', '').startswith('cuda') else "CPU"
            self.widgets['perf_stats_var'].set(f"FPS: {self.processor.last_fps:.1f}  |  {self.processor.last_latency_ms:.1f}ms  |  {dev_label}")

        # Update playback timecode if video file
        if self.video_source_var.get() == "video" and 'timecode_lbl' in self.widgets and self.video_playback_controls.cap:
            try:
                pos = self.video_playback_controls.get_current_frame_pos()
                total = self.video_playback_controls.get_total_frames()
                props = self.video_playback_controls.get_video_properties()
                fps = props.get('fps', 30.0) or 30.0
                cur_sec = int(pos / fps)
                tot_sec = int(total / fps)
                self.widgets['timecode_lbl'].config(text=f"{cur_sec//60:02d}:{cur_sec%60:02d} / {tot_sec//60:02d}:{tot_sec%60:02d}")
            except Exception:
                pass

        self.video_display_manager.show_frame(frame, self.line_coords, self.processor, self.logger)
        self._ui_update_pending = False

    def _update_live_counts(self, in_c, out_c, people_in_frame):
        """Updates the live count labels and KPI metric cards in the UI."""
        # Structured KPI Cards
        if 'in_count_val' in self.widgets:
            self.widgets['in_count_val'].set(str(in_c))
        if 'out_count_val' in self.widgets:
            self.widgets['out_count_val'].set(str(out_c))
        if 'in_frame_val' in self.widgets:
            self.widgets['in_frame_val'].set(str(people_in_frame))
        if 'net_flow_val' in self.widgets:
            net = in_c - out_c
            prefix = "+" if net > 0 else ""
            self.widgets['net_flow_val'].set(f"{prefix}{net}")

        # Legacy stringvars for backwards compatibility
        if 'in_count_var' in self.widgets:
            self.widgets['in_count_var'].set(f"IN: {in_c}")
        if 'out_count_var' in self.widgets:
            self.widgets['out_count_var'].set(f"OUT: {out_c}")
        if 'people_in_frame_var' in self.widgets:
            self.widgets['people_in_frame_var'].set(f"In Frame: {people_in_frame}")

    def update_status(self, message, is_error=False):
        """Updates the status bar with a message."""
        if 'status_label' in self.widgets:
            color = "#EF4444" if is_error else "#38BDF8"
            self.widgets['status_label'].config(text=f"● {message}", fg=color)


    def _send_data_async(self, payload):
        """Sends collected session data to the specified API endpoint in a background thread."""
        api_url = self.api_endpoint_var.get()
        if not api_url:
            self.logger.warning("Attempted to send data but API endpoint is not configured. Saving offline.")
            self.offline_manager.save_pending_payload(payload)
            self.root.after(0, lambda: self.update_status("API not set. Data saved offline.", is_error=True))
            return

        headers = {'Content-Type': 'application/json'}
        self.logger.info(f"Attempting to send {len(payload)} data points to API: {api_url}")
        self.root.after(0, lambda: self.update_status("Sending data to API...", is_error=False))

        # First flush any pending offline logs
        pending = self.offline_manager.get_pending_payloads()
        for rec_id, old_batch in pending:
            try:
                res = requests.post(api_url, json=old_batch, headers=headers, timeout=5)
                if res.status_code < 400:
                    self.offline_manager.remove_payload(rec_id)
            except Exception:
                break

        try:
            response = requests.post(api_url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            self.logger.info(f"Data successfully sent to API. Status Code: {response.status_code}")
            self.root.after(0, lambda: self.update_status("Data sent to API successfully!", is_error=False))
        except Exception as e:
            self.logger.warning(f"API request failed ({e}). Caching to offline SQLite database.")
            self.offline_manager.save_pending_payload(payload)
            pending_count = self.offline_manager.get_pending_count()
            self.root.after(0, lambda: self.update_status(f"Saved to offline cache ({pending_count} batches queued).", is_error=True))

    def send_data_to_api(self):
        """Sends collected session data to the specified API endpoint."""
        with self._log_lock:
            data = list(self.log_data)
        if not data:
            self.logger.info("No log data to send to API for this session.")
            self.update_status("No data to send to API.", is_error=False)
            return
        threading.Thread(target=self._send_data_async, args=(data,), daemon=True).start()

    def on_closing(self):
        # Update settings with current UI values
        self.settings_manager.update_setting("api_endpoint", self.api_endpoint_var.get())
        self.settings_manager.update_setting("conf_threshold", float(self.conf_var.get()))
        self.settings_manager.update_setting("model_name", self.model_var.get())
        self.settings_manager.update_setting("tracker_type", self.tracker_var.get())
        
        self.settings_manager.save_settings(self.settings_manager.settings)
        if self.running:
            self.stop_processing_logic()
        self.root.destroy()