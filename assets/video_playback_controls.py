import cv2

class VideoPlaybackControls:
    def __init__(self, cap=None):
        self.cap = cap
        self._is_playing = False
        self._total_frames = 0
        self._current_frame_pos = 0

        if self.cap:
            self.set_video_capture(self.cap)

    def set_video_capture(self, cap):
        """Sets the video capture object and initializes playback properties."""
        self.cap = cap
        if self.cap and self.cap.isOpened():
            self._total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self._current_frame_pos = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
            self._is_playing = False # Start paused by default
        else:
            self._total_frames = 0
            self._current_frame_pos = 0
            self._is_playing = False

    def play(self):
        self._is_playing = True

    def pause(self):
        self._is_playing = False

    def toggle_play_pause(self):
        self._is_playing = not self._is_playing

    def is_playing(self):
        return self._is_playing

    def get_total_frames(self):
        return self._total_frames

    def get_current_frame_pos(self):
        if self.cap and self.cap.isOpened():
            # Ensure _current_frame_pos reflects the actual position from OpenCV
            self._current_frame_pos = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
        return self._current_frame_pos

    def set_frame_pos(self, frame_number):
        """Sets the current frame position of the video."""
        if self.cap and self.cap.isOpened():
            # Clamp frame_number to valid range
            frame_number = max(0, min(frame_number, self._total_frames - 1))
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            self._current_frame_pos = frame_number
            return True
        return False

    def get_frame(self):
        """Reads a frame from the video capture. If not playing, stays on current frame."""
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                # End of video or error, auto-pause
                self._is_playing = False
                # Try to seek back to the last frame if possible, or 0 if empty
                if self._total_frames > 0:
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, self._total_frames - 1)
                else:
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                return False, None # Indicate end of video or failure
            self._current_frame_pos = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
            return True, frame
        return False, None

    def get_video_properties(self):
        """Returns useful video properties like FPS and total frames."""
        if self.cap and self.cap.isOpened():
            fps = self.cap.get(cv2.CAP_PROP_FPS)
            return {'fps': fps, 'total_frames': self._total_frames}
        return {'fps': 0, 'total_frames': 0}

    def release(self):
        """Releases the video capture object and resets properties."""
        if self.cap:
            self.cap.release()
            self.cap = None
            self._total_frames = 0
            self._current_frame_pos = 0
            self._is_playing = False