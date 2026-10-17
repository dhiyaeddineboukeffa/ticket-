import cv2
from PIL import Image, ImageTk
import numpy as np

class VideoDisplayManager:
    def __init__(self, video_label):
        self.video_label = video_label
        self.original_frame_width = None
        self.original_frame_height = None
        self.displayed_frame_width = None
        self.displayed_frame_height = None
        
        # Bind the video_label's configure event to update displayed_frame_width/height
        self.video_label.bind("<Configure>", self._on_video_label_configure)

    def set_original_frame_dimensions(self, width, height):
        """Sets the original dimensions of the video frames."""
        self.original_frame_width = width
        self.original_frame_height = height

    def _on_video_label_configure(self, event):
        """
        Called when the video_label (where video is displayed) is resized.
        Updates displayed_frame_width and height based on the label's current size.
        This is crucial for correct click-to-coordinate mapping.
        """
        self.displayed_frame_width = event.width
        self.displayed_frame_height = event.height
        # A full redraw might be needed here if the video is static or paused
        # but for a continuously updating video_loop, this just updates the dimensions.

    def get_displayed_dimensions(self):
        """Returns the current dimensions of the area the image is displayed in."""
        return self.displayed_frame_width, self.displayed_frame_height

    def get_original_dimensions(self):
        """Returns the original dimensions of the video frame."""
        return self.original_frame_width, self.original_frame_height

    def show_frame(self, frame, line_coords=None, processor=None, logger=None):
        """
        Processes and displays a single video frame on the video_label.
        Includes drawing the counting line and ensuring aspect ratio is maintained.
        """
        widget_width = self.video_label.winfo_width()
        widget_height = self.video_label.winfo_height()

        if widget_width <= 1 or widget_height <= 1:
            if logger: logger.debug("Video label dimensions too small for display.")
            return

        # Ensure frame is not None and has valid shape
        if frame is None or frame.shape[0] == 0 or frame.shape[1] == 0:
            if logger: logger.warning("Attempted to show an empty or invalid frame.")
            return

        # Get original frame dimensions if not already set
        if self.original_frame_height is None or self.original_frame_width is None:
            self.original_frame_height, self.original_frame_width, _ = frame.shape
            if logger: logger.info(f"Original frame dimensions detected: {self.original_frame_width}x{self.original_frame_height}")

        h_orig, w_orig, _ = frame.shape

        # Draw line and points for visual feedback during drawing/processing
        if line_coords and len(line_coords) >= 1 and self.original_frame_width and self.original_frame_height:
            # Clamp coordinates to ensure they are within the frame bounds before drawing
            p0 = (max(0, min(line_coords[0][0], self.original_frame_width - 1)),
                  max(0, min(line_coords[0][1], self.original_frame_height - 1)))
            # Outer ring + inner white core for start point
            cv2.circle(frame, p0, 7, (0, 0, 255), 2, cv2.LINE_AA)
            cv2.circle(frame, p0, 3, (255, 255, 255), -1, cv2.LINE_AA)

            if len(line_coords) == 2:
                p1 = (max(0, min(line_coords[1][0], self.original_frame_width - 1)),
                      max(0, min(line_coords[1][1], self.original_frame_height - 1)))
                # Sleek neon yellow/cyan counting line
                cv2.line(frame, p0, p1, (0, 242, 254), 3, cv2.LINE_AA)
                cv2.circle(frame, p1, 7, (0, 0, 255), 2, cv2.LINE_AA)
                cv2.circle(frame, p1, 3, (255, 255, 255), -1, cv2.LINE_AA)

                # Draw the IN direction arrow if processor is provided
                if processor:
                    in_arrow_vector = processor.get_in_arrow_vector()
                    if in_arrow_vector is not None:
                        mid_point = ((line_coords[0][0] + line_coords[1][0]) // 2,
                                     (line_coords[0][1] + line_coords[1][1]) // 2)
                        
                        arrow_len = 28
                        arrow_start_point = (
                            int(mid_point[0] - in_arrow_vector[0] * arrow_len),
                            int(mid_point[1] - in_arrow_vector[1] * arrow_len)
                        )
                        arrow_end_point = (
                            int(mid_point[0] + in_arrow_vector[0] * arrow_len),
                            int(mid_point[1] + in_arrow_vector[1] * arrow_len)
                        )
                        cv2.arrowedLine(frame, arrow_start_point, arrow_end_point, (16, 185, 129), 3, tipLength=0.35)
                        
                        # Modern pill badges for IN and OUT
                        # IN Badge (Emerald Green pill)
                        in_x, in_y = arrow_end_point[0] + 6, arrow_end_point[1] - 10
                        cv2.rectangle(frame, (in_x, in_y), (in_x + 36, in_y + 22), (16, 185, 129), -1)
                        cv2.rectangle(frame, (in_x, in_y), (in_x + 36, in_y + 22), (255, 255, 255), 1)
                        cv2.putText(frame, "IN", (in_x + 6, in_y + 16), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (255, 255, 255), 1, cv2.LINE_AA)
                        
                        # OUT Badge (Rose Red pill)
                        out_x, out_y = arrow_start_point[0] - 46, arrow_start_point[1] - 10
                        cv2.rectangle(frame, (out_x, out_y), (out_x + 44, out_y + 22), (239, 68, 68), -1)
                        cv2.rectangle(frame, (out_x, out_y), (out_x + 44, out_y + 22), (255, 255, 255), 1)
                        cv2.putText(frame, "OUT", (out_x + 6, out_y + 16), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (255, 255, 255), 1, cv2.LINE_AA)

        # Draw Modern Performance HUD Pill
        if processor and hasattr(processor, 'last_fps') and processor.last_fps > 0:
            is_gpu = getattr(processor, 'device', '').startswith('cuda')
            dev_str = "GPU (CUDA)" if is_gpu else "CPU"
            hud_text = f"FPS: {processor.last_fps:.1f}   |   {processor.last_latency_ms:.1f}ms   |   {dev_str}"
            
            # Dark Slate Pill Container
            cv2.rectangle(frame, (14, 14), (370, 46), (15, 23, 42), -1)
            border_color = (16, 185, 129) if is_gpu else (59, 130, 246)
            cv2.rectangle(frame, (14, 14), (370, 46), border_color, 1)
            
            # Pulsing status indicator dot
            dot_color = (16, 185, 129) if is_gpu else (245, 158, 11)
            cv2.circle(frame, (28, 30), 5, dot_color, -1, cv2.LINE_AA)
            cv2.putText(frame, hud_text, (42, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (248, 250, 252), 1, cv2.LINE_AA)


        # Calculate aspect ratios
        aspect_ratio_orig = w_orig / h_orig
        aspect_ratio_widget = widget_width / widget_height

        # Determine new dimensions to fit while maintaining aspect ratio
        if aspect_ratio_widget > aspect_ratio_orig:
            # Widget is wider than original frame, fit by height
            new_h = widget_height
            new_w = int(new_h * aspect_ratio_orig)
        else:
            # Widget is taller than original frame, fit by width
            new_w = widget_width
            new_h = int(new_w / aspect_ratio_orig)
        
        # Ensure minimum dimensions for resize
        if new_w <= 0: new_w = 1
        if new_h <= 0: new_h = 1

        resized_frame = cv2.resize(frame, (new_w, new_h))

        # Create a blank image to paste the resized frame onto, ensuring it fills the label
        final_image = np.full((widget_height, widget_width, 3), (0, 0, 0), dtype=np.uint8) # Black background
        
        # Calculate paste position for centering
        paste_x = (widget_width - new_w) // 2
        paste_y = (widget_height - new_h) // 2
        
        # Ensure paste coordinates and dimensions are valid
        final_image[paste_y:paste_y+new_h, paste_x:paste_x+new_w] = resized_frame

        frame_rgb = cv2.cvtColor(final_image, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        imgtk = ImageTk.PhotoImage(image=img)
        self.video_label.imgtk = imgtk # Keep a reference to prevent garbage collection
        self.video_label.configure(image=imgtk)

    def clear_display(self, default_text="Video feed standby. Select a source and click Start."):
        """Clears the video display."""
        self.video_label.config(image='')
        try:
            self.video_label.config(text=default_text, fg="#64748B", bg="#090D16")
        except Exception:
            self.video_label.config(text=default_text)
        self.original_frame_width = None
        self.original_frame_height = None
        self.displayed_frame_width = None
        self.displayed_frame_height = None