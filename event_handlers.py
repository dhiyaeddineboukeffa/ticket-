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
            if not self.app.running: # If not running, load first frame for preview
                 self.app.load_first_frame()
        else:
            self.app.widgets['playback_controls_frame'].pack_forget()
            self.app.widgets['play_pause_btn'].config(state='disabled')
            self.app.widgets['seek_slider'].config(state='disabled')
            if not self.app.running: # If not running and switching from video, clear video display
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
        self.app.widgets['instruction_label'].config(text="Click on the video to set the line's START point.")
        # Re-load first frame to clear previous line drawings if any
        self.app.load_first_frame()
        self.app.logger.info("Started line drawing mode.")
        self.app.update_status("Drawing line: Click START point.")


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
            self.app.widgets['instruction_label'].config(text="Click again to set the line's END point.")
            self.app.logger.info(f"Line start point set: {scaled_point}")
            self.app.update_status("Drawing line: Click END point.")
            # Show the frame with the first point immediately
            if self.app.cap:
                # Re-read current frame to draw point on it
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