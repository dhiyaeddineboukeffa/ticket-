import os
from tkinter import filedialog, messagebox
import cv2 # Required for CAP_PROP_POS_FRAMES (used for seeking current frame)

class EventHandlers:
    def __init__(self, app_instance):
        """
        Initializes the EventHandlers with a reference to the main application instance.
        This allows event handlers to call methods and access attributes of the main app.
        """
        self.app = app_instance

    def on_left_canvas_configure(self, event, left_canvas, canvas_window_id):
        """Called when the scrollable canvas itself is resized."""
        canvas_width = event.width
        # Update the width of the frame inside the canvas to match the canvas's width
        left_canvas.itemconfig(canvas_window_id, width=canvas_width)
        # Also update the scroll region
        left_canvas.configure(scrollregion=left_canvas.bbox("all"))


    def on_source_change(self):
        """Adjusts UI elements based on selected video source type."""
        source = self.app.video_source_var.get()
        self.app.widgets['file_button'].configure(state='normal' if source == "video" else 'disabled')
        self.app.widgets['ip_entry'].configure(state='normal' if source == "ipcam" else 'disabled')
        self.app.widgets['webcam_dropdown'].configure(state='readonly' if source == "webcam" else 'disabled')

        # Control playback controls frame visibility
        if source == "video":
            self.app.widgets['playback_controls_frame'].pack(fill='x', pady=(5,0))
            self.app.widgets['play_pause_btn'].config(state='normal')
            self.app.widgets['seek_slider'].config(state='normal')
            if not self.app.running and self.app.video_display_manager is not None:
                 self.app.load_first_frame()
        else:
            self.app.widgets['playback_controls_frame'].pack_forget()
            self.app.widgets['play_pause_btn'].config(state='disabled')
            self.app.widgets['seek_slider'].config(state='disabled')
            if not self.app.running and self.app.video_display_manager is not None:
                self.app.video_display_manager.clear_display()


        self.app.update_status(f"Source changed to: {source}")
        self.app.logger.info(f"Source changed to: {source}")


    def select_file(self):
        path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4;*.avi;*.mov")])
        if path:
            self.app.video_path_var.set(path)
            self.app.load_first_frame()
            self.app.settings_manager.update_setting("video_path", path)
            self.app.logger.info(f"Video file selected: {path}")
            self.app.update_status(f"Video file selected: {os.path.basename(path)}")


    def on_webcam_selected(self, event=None):
        """Handles webcam selection from the dropdown."""
        # When a webcam is selected, attempt to load its first frame if not running
        if not self.app.running and self.app.video_source_var.get() == "webcam":
            self.app.load_first_frame()


    def start_drawing(self):
        if not self.app.cap:
            messagebox.showwarning("No Video Loaded", "Please load a video source (file, webcam, or IP camera) before drawing a line.")
            self.app.logger.warning("Attempted to draw line without video loaded.")
            self.app.update_status("Please load a video source first.", is_error=True)
            return

        self.app.drawing_line = True
        self.app.line_coords = []
        if 'video_label' in self.app.widgets:
            self.app.widgets['video_label'].config(cursor="crosshair")
        if 'cancel_draw_btn' in self.app.widgets:
            self.app.widgets['cancel_draw_btn'].config(state='normal')
        self.app.widgets['instruction_label'].config(text="Click Point 1 on the video stream (Press ESC to Cancel).")
        # Re-load first frame to clear previous line drawings if any
        self.app.load_first_frame()
        self.app.logger.info("Started line drawing mode.")
        self.app.update_status("Drawing line: Click Point 1 (Press ESC to cancel).")

    def cancel_drawing(self, event=None):
        """Cancels drawing mode and restores previous line."""
        if not self.app.drawing_line:
            return
        self.app.drawing_line = False
        if 'video_label' in self.app.widgets:
            self.app.widgets['video_label'].config(cursor="")
        if 'cancel_draw_btn' in self.app.widgets:
            self.app.widgets['cancel_draw_btn'].config(state='disabled')
        saved_line = self.app.settings_manager.get_setting("line_coords", [])
        self.app.line_coords = saved_line
        if saved_line and len(saved_line) == 2:
            self.app.processor.set_line_and_direction(saved_line)
            self.app.widgets['instruction_label'].config(text="Drawing cancelled. Saved line restored.")
        else:
            self.app.widgets['instruction_label'].config(text="Drawing cancelled. No line set.")
        if self.app.cap:
            self.app.load_first_frame()
        self.app.logger.info("Line drawing cancelled.")
        self.app.update_status("Drawing cancelled.")

    def clear_line(self):
        """Clears the active counting line."""
        self.app.drawing_line = False
        self.app.line_coords = []
        self.app.processor.line_coords = None
        self.app.processor.line_vector = None
        self.app.processor.line_normal = None
        self.app.settings_manager.update_setting("line_coords", [])
        if 'video_label' in self.app.widgets:
            self.app.widgets['video_label'].config(cursor="")
        if 'cancel_draw_btn' in self.app.widgets:
            self.app.widgets['cancel_draw_btn'].config(state='disabled')
        self.app.widgets['instruction_label'].config(text="Line cleared. Click 'Draw New Line' to define.")
        if self.app.cap:
            self.app.load_first_frame()
        self.app.logger.info("Counting line cleared.")
        self.app.update_status("Counting line cleared.")

    def reset_counts(self):
        """Resets the counting metrics without restarting the app."""
        self.app.processor.reset_counters()
        with self.app._log_lock:
            self.app.log_data.clear()
        if 'in_count_val' in self.app.widgets:
            self.app.widgets['in_count_val'].set("0")
        if 'out_count_val' in self.app.widgets:
            self.app.widgets['out_count_val'].set("0")
        if 'in_frame_val' in self.app.widgets:
            self.app.widgets['in_frame_val'].set("0")
        if 'net_flow_val' in self.app.widgets:
            self.app.widgets['net_flow_val'].set("0")
        self.app.logger.info("Session counts reset to 0.")
        self.app.update_status("Counts reset to 0.")

    def handle_video_click(self, event):
        if not self.app.drawing_line:
            return

        # Use the most recent displayed_frame_width/height from video_display_manager
        current_displayed_width, current_displayed_height = self.app.video_display_manager.get_displayed_dimensions()
        original_frame_width, original_frame_height = self.app.video_display_manager.get_original_dimensions()

        if original_frame_width is None or original_frame_height is None or \
           current_displayed_width <= 1 or current_displayed_height <= 1:
            self.app.logger.error("Cannot draw line: Original frame dimensions or displayed label dimensions are invalid.")
            self.app.update_status("Error drawing line: Video display not ready.", is_error=True)
            return

        # Calculate actual scaling factor based on how the frame was scaled to fit the label
        original_aspect = original_frame_width / original_frame_height
        label_aspect = current_displayed_width / current_displayed_height

        scaled_image_width = current_displayed_width
        scaled_image_height = int(current_displayed_width / original_aspect)

        if scaled_image_height > current_displayed_height:
            scaled_image_height = current_displayed_height
            scaled_image_width = int(current_displayed_height * original_aspect)

        # Calculate offset within the label if there are black bars
        offset_x = (current_displayed_width - scaled_image_width) // 2
        offset_y = (current_displayed_height - scaled_image_height) // 2

        # Adjust click coordinates by the offset
        adjusted_click_x = event.x - offset_x
        adjusted_click_y = event.y - offset_y

        # Clamp adjusted click coordinates to the actual image area
        adjusted_click_x = max(0, min(adjusted_click_x, scaled_image_width))
        adjusted_click_y = max(0, min(adjusted_click_y, scaled_image_height))

        # Scale adjusted click coordinates back to original frame dimensions
        original_x = int(adjusted_click_x * (original_frame_width / scaled_image_width))
        original_y = int(adjusted_click_y * (original_frame_height / scaled_image_height))

        scaled_point = (original_x, original_y)

        if len(self.app.line_coords) == 0:
            self.app.line_coords.append(scaled_point)
            self.app.widgets['instruction_label'].config(text="Click Point 2 to complete the counting line.")
            self.app.logger.info(f"Line start point set: {scaled_point}")
            self.app.update_status("Drawing line: Click Point 2.")
            # Show the frame with the first point immediately
            if self.app.cap:
                current_pos = int(self.app.cap.get(cv2.CAP_PROP_POS_FRAMES))
                self.app.cap.set(cv2.CAP_PROP_POS_FRAMES, current_pos)
                ret, frame = self.app.cap.read()
                if ret:
                    self.app.video_display_manager.show_frame(frame, self.app.line_coords, self.app.processor, self.app.logger)
                else:
                    self.app.logger.error("Failed to reread frame to draw first line point.")

        elif len(self.app.line_coords) == 1:
            self.app.line_coords.append(scaled_point)
            self.app.drawing_line = False
            if 'video_label' in self.app.widgets:
                self.app.widgets['video_label'].config(cursor="")
            if 'cancel_draw_btn' in self.app.widgets:
                self.app.widgets['cancel_draw_btn'].config(state='disabled')
            self.app.widgets['instruction_label'].config(text="Line set! You can now start the analysis.")
            self.app.processor.set_line_and_direction(self.app.line_coords)
            # Show the frame with the full line immediately
            if self.app.cap:
                current_pos = int(self.app.cap.get(cv2.CAP_PROP_POS_FRAMES))
                self.app.cap.set(cv2.CAP_PROP_POS_FRAMES, current_pos)
                ret, frame = self.app.cap.read()
                if ret:
                    self.app.video_display_manager.show_frame(frame, self.app.line_coords, self.app.processor, self.app.logger)
                else:
                    self.app.logger.error("Failed to reread frame to draw full line.")
            self.app.logger.info(f"Line end point set: {scaled_point}. Line coords: {self.app.line_coords}")
            self.app.update_status("Counting line set. Ready to analyze.")
            self.app.settings_manager.update_setting("line_coords", self.app.line_coords) # Save line coords

    def switch_direction(self):
        """Switches the IN/OUT direction logic and updates the UI."""
        self.app.processor.switch_direction()
        self.app.settings_manager.update_setting("direction_swapped", self.app.processor.direction_swapped)
        self.app.logger.info(f"Direction swapped: {'IN is now OUT and vice versa' if self.app.processor.direction_swapped else 'Default IN/OUT'}")
        self.app.update_status("IN/OUT direction switched.")
        if not self.app.running and self.app.cap:
            self.app.load_first_frame()

    def step_video_seconds(self, seconds):
        """Steps forward or backward in video by given seconds."""
        if not self.app.running and self.app.video_playback_controls.cap and self.app.video_source_var.get() == "video":
            cap = self.app.video_playback_controls.cap
            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            current_frame = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
            target_frame = max(0, min(total_frames - 1, int(current_frame + seconds * fps)))
            self.on_seek_slider_moved(target_frame)
            if 'seek_slider' in self.app.widgets:
                self.app.widgets['seek_slider'].set(target_frame)

    def test_api_connection(self):
        """Pings the API endpoint in a background thread to verify reachability."""
        url = self.app.api_endpoint_var.get().strip()
        if not url:
            if 'api_test_status' in self.app.widgets:
                self.app.widgets['api_test_status'].config(text="● Please enter a URL first", foreground="#F59E0B")
            return
            
        if 'api_test_status' in self.app.widgets:
            self.app.widgets['api_test_status'].config(text="● Testing connection...", foreground="#38BDF8")

        def _test():
            import urllib.request
            import time
            try:
                t0 = time.perf_counter()
                req = urllib.request.Request(url, headers={'User-Agent': 'PeopleCounter/2.0'}, method='HEAD')
                try:
                    with urllib.request.urlopen(req, timeout=5) as resp:
                        latency = int((time.perf_counter() - t0) * 1000)
                        status_code = resp.status
                except urllib.error.HTTPError as e:
                    latency = int((time.perf_counter() - t0) * 1000)
                    status_code = e.code

                msg = f"● Connected ({status_code}) - {latency}ms"
                color = "#10B981"
            except Exception as ex:
                msg = f"✕ Failed: {type(ex).__name__}"
                color = "#EF4444"

            def _update():
                if 'api_test_status' in self.app.widgets:
                    self.app.widgets['api_test_status'].config(text=msg, foreground=color)
            self.app.root.after(0, _update)

        import threading
        threading.Thread(target=_test, daemon=True).start()

    def export_offline_csv(self):
        """Exports cached offline records to CSV."""
        from datetime import datetime
        count = self.app.offline_manager.get_pending_count()
        if count == 0:
            messagebox.showinfo("Offline Cache", "There are currently 0 queued offline records to export.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
            initialfile=f"people_counter_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        if file_path:
            success, result = self.app.offline_manager.export_to_csv(file_path)
            if success:
                messagebox.showinfo("Export Successful", f"Successfully exported {result} visitor event records to:\n{file_path}")
                self.app.update_status(f"Exported {result} records to CSV.")
            else:
                messagebox.showerror("Export Failed", f"Failed to export CSV: {result}")

    def sync_offline_cache(self):
        """Triggers manual flush of offline cached logs to API server."""
        count = self.app.offline_manager.get_pending_count()
        if count == 0:
            messagebox.showinfo("Offline Queue", "Offline queue is empty. All logs are up to date.")
            return

        if 'offline_count_lbl' in self.app.widgets:
            self.app.widgets['offline_count_lbl'].config(text="Syncing records...")

        def _sync_worker():
            self.app._flush_offline_cache()
            new_count = self.app.offline_manager.get_pending_count()
            def _update():
                if 'offline_count_lbl' in self.app.widgets:
                    self.app.widgets['offline_count_lbl'].config(text=f"{new_count} records pending")
                self.app.update_status(f"Sync complete. {new_count} records remaining.")
            self.app.root.after(0, _update)

        import threading
        threading.Thread(target=_sync_worker, daemon=True).start()
        # Redraw the frame to show the new arrow direction
        if not self.app.running and self.app.cap: # Only reload first frame if not actively processing and a cap exists
            self.app.load_first_frame()
        elif self.app.running: # If running, the video_loop will update the frame
            pass # No explicit action needed as frame will be redrawn by loop


    def toggle_playback(self):
        """Toggles play/pause for video files."""
        if self.app.video_playback_controls.cap and self.app.video_source_var.get() == "video":
            if self.app.video_playback_controls.is_playing():
                self.app.video_playback_controls.pause()
                self.app.widgets['play_pause_btn'].config(text="Play")
                self.app.logger.info("Video paused.")
                self.app.update_status("Video paused.")
            else:
                self.app.video_playback_controls.play()
                self.app.widgets['play_pause_btn'].config(text="Pause")
                self.app.logger.info("Video playing.")
                self.app.update_status("Video playing.")
        else:
            self.app.logger.warning("Attempted to toggle playback for non-video source or no video loaded.")
            self.app.update_status("Playback controls only for video files.", is_error=True)


    def on_seek_slider_moved(self, value):
        """Handles seeking in video files."""
        # Only seek if not currently running processing
        if not self.app.running and self.app.video_playback_controls.cap and self.app.video_source_var.get() == "video":
            frame_number = int(float(value))
            if self.app.video_playback_controls.set_frame_pos(frame_number):
                self.app.logger.debug(f"Seeked to frame: {frame_number}")
                ret, frame = self.app.video_playback_controls.get_frame() # Get the frame at new position (will be paused)
                if ret:
                    self.app.video_display_manager.show_frame(frame, self.app.line_coords, self.app.processor, self.app.logger)
                    self.app.update_status(f"Seeked to frame {frame_number}.")
                else:
                    self.app.update_status("Failed to display seeked frame.", is_error=True)
                    self.app.logger.error("Failed to display frame after seeking.")
            else:
                self.app.logger.warning(f"Failed to seek to frame {frame_number}.")
                self.app.update_status("Failed to seek in video.", is_error=True)
        elif self.app.running and self.app.video_source_var.get() == "video":
            # If running, the slider is updated by video_loop, so this event is ignored
            pass
        else:
            self.app.widgets['seek_slider'].set(0) # Reset slider if not a video
            self.app.widgets['seek_slider'].config(state='disabled') # Disable it
            self.app.logger.warning("Seek slider used for non-video source or while running.")


    def start_processing(self):
        self.app.start_processing_logic() # Delegate to app for core logic


    def stop_processing(self):
        self.app.stop_processing_logic() # Delegate to app for core logic