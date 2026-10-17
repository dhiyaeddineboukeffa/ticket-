import cv2

class CameraManager:
    def __init__(self):
        pass

    def get_available_webcams(self):
        """
        Detects and returns a list of available webcam indices.
        """
        available_cameras = []
        # Try up to 10 cameras (a common range to check)
        # This loop attempts to open a VideoCapture object for each index
        # If successful, it's considered available.
        for i in range(4): 
            try:
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    available_cameras.append(i)
                    cap.release()
                else:
                    break 
            except Exception:
                break
        return available_cameras

    def open_video_source(self, source_type, source_path):
        """
        Opens a video capture object based on source type and path.
        Returns the cv2.VideoCapture object or None if failed.
        """
        cap = None
        if source_type == "video":
            if not source_path:
                return None
            cap = cv2.VideoCapture(source_path)
        elif source_type == "webcam":
            try:
                # source_path is expected to be an integer for webcam index
                cap = cv2.VideoCapture(int(source_path))
            except ValueError:
                return None # Invalid webcam index
        elif source_type == "ipcam":
            if not source_path:
                return None
            cap = cv2.VideoCapture(source_path)

        if cap and not cap.isOpened():
            cap.release() # Release if opening failed
            return None
        return cap