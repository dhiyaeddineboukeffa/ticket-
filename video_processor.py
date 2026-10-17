import cv2
from ultralytics import YOLO
import numpy as np
import os
import time
import torch

class VideoProcessor:
    COOLDOWN_FRAMES = 15 

    def __init__(self, model_path='yolov8n.pt', class_list_path='coco.txt', conf_threshold=0.45, tracker_type='bytetrack.yaml'):
        self.device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
        self.model_path = model_path
        self.model = YOLO(model_path)
        self.class_list = self._load_class_list(class_list_path)
        self.person_class_index = self.class_list.index('person') if 'person' in self.class_list else -1
        
        self.conf_threshold = conf_threshold
        self.tracker_type = tracker_type
        
        self.line_coords = None
        self.line_vector = None
        self.line_normal = None
        
        self.direction_swapped = False
        
        # Real-time performance metrics
        self.last_latency_ms = 0.0
        self.last_fps = 0.0
        self._fps_history = []
        
        self.reset()

    def set_confidence(self, conf):
        """Updates detection confidence threshold."""
        self.conf_threshold = float(conf)

    def set_tracker(self, tracker_name):
        """Updates tracker config ('bytetrack.yaml' or 'botsort.yaml')."""
        self.tracker_type = tracker_name

    def reload_model(self, model_path):
        """Dynamically reloads a different model weight file."""
        if os.path.exists(model_path) or model_path.endswith('.pt'):
            self.model_path = model_path
            self.model = YOLO(model_path)
            self.reset()

    def _load_class_list(self, file_path):
        if not os.path.exists(file_path):
            print(f"Warning: Class list file not found at {file_path}. Only 'person' will be detected.")
            return ['person']
        with open(file_path, "r") as file:
            return file.read().strip().split("\n")

    def set_line_and_direction(self, line_coords):
        self.line_coords = line_coords
        if line_coords and len(line_coords) == 2:
            p1 = np.array(self.line_coords[0], dtype=float)
            p2 = np.array(self.line_coords[1], dtype=float)
            self.line_vector = p2 - p1
            self.line_normal = np.array([-self.line_vector[1], self.line_vector[0]])

    def switch_direction(self):
        """Swaps the logic for IN and OUT counts."""
        self.direction_swapped = not self.direction_swapped

    def set_direction_swapped(self, is_swapped):
        """Sets the direction based on loaded settings."""
        self.direction_swapped = is_swapped

    def get_in_arrow_vector(self):
        """Calculates the normalized vector for the 'IN' arrow to be drawn by the UI."""
        if self.line_normal is None:
            return None
        
        norm = np.linalg.norm(self.line_normal)
        if norm == 0:
            return None
            
        normalized_normal = self.line_normal / norm
        return normalized_normal if self.direction_swapped else -normalized_normal

    def reset(self):
        self.track_history = {} # track_id -> {'pos': (x, y), 'side': float, 'cooldown': int}
        self.counter_in = 0
        self.counter_out = 0
        self.people_in_frame = 0
        self._fps_history.clear()

    def reset_counters(self):
        """Resets the IN and OUT counters without resetting the model or tracking state."""
        self.counter_in = 0
        self.counter_out = 0

    @staticmethod
    def _ccw(A, B, C):
        """Tests whether the turn from point A to B to C is counter-clockwise."""
        return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])

    @classmethod
    def _segments_intersect(cls, A, B, C, D):
        """Returns True if line segment AB intersects line segment CD."""
        return (cls._ccw(A, C, D) != cls._ccw(B, C, D)) and (cls._ccw(A, B, C) != cls._ccw(A, B, D))

    def process_frame(self, frame):
        t_start = time.perf_counter()
        
        # Check if CUDA is available
        if self.device == 'cpu' and torch.cuda.is_available():
            self.device = 'cuda:0'

        is_cuda = self.device.startswith('cuda')

        # Fast GPU/CPU inference with ByteTrack
        results = self.model.track(
            frame,
            persist=True,
            classes=[self.person_class_index],
            conf=self.conf_threshold,
            iou=0.5,
            tracker=self.tracker_type,
            device=self.device,
            half=is_cuda,
            verbose=False
        )

        t_elapsed = time.perf_counter() - t_start
        self.last_latency_ms = t_elapsed * 1000.0
        current_fps = 1.0 / t_elapsed if t_elapsed > 0 else 0.0
        self._fps_history.append(current_fps)
        if len(self._fps_history) > 15:
            self._fps_history.pop(0)
        self.last_fps = sum(self._fps_history) / len(self._fps_history)
        
        num_boxes = len(results[0].boxes) if results[0].boxes is not None else 0
        self.people_in_frame = num_boxes
        annotated_frame = results[0].plot()

        if self.line_coords is None or len(self.line_coords) < 2:
            return annotated_frame, self.counter_in, self.counter_out, self.people_in_frame

        if results[0].boxes.id is None:
            return annotated_frame, self.counter_in, self.counter_out, self.people_in_frame

        boxes = results[0].boxes.xywh.cpu()
        track_ids = results[0].boxes.id.int().cpu().tolist()

        p1 = tuple(self.line_coords[0])
        p2 = tuple(self.line_coords[1])

        for box, track_id in zip(boxes, track_ids):
            x, y, w, h = box
            curr_center = (float(x), float(y))
            point_vector = np.array(curr_center) - np.array(self.line_coords[0])
            side = float(np.dot(point_vector, self.line_normal))

            if track_id not in self.track_history:
                self.track_history[track_id] = {
                    'pos': curr_center,
                    'side': side,
                    'cooldown': 0
                }
            else:
                data = self.track_history[track_id]
                prev_center = data['pos']
                last_side = data['side']
                
                if data['cooldown'] > 0:
                    data['cooldown'] -= 1

                if data['cooldown'] == 0:
                    # Check both exact 2D segment intersection and side sign-flip within segment span
                    intersected = self._segments_intersect(p1, p2, prev_center, curr_center)
                    sign_flipped = (last_side > 0 and side < 0) or (last_side < 0 and side > 0)

                    min_x = min(p1[0], p2[0]) - 50
                    max_x = max(p1[0], p2[0]) + 50
                    min_y = min(p1[1], p2[1]) - 50
                    max_y = max(p1[1], p2[1]) + 50
                    within_span = (min_x <= curr_center[0] <= max_x) and (min_y <= curr_center[1] <= max_y)

                    if intersected or (sign_flipped and within_span):
                        motion_vec = np.array(curr_center) - np.array(prev_center)
                        motion_side = np.dot(motion_vec, self.line_normal)

                        is_in = motion_side < 0 if not self.direction_swapped else motion_side > 0

                        line_pt1 = (int(p1[0]), int(p1[1]))
                        line_pt2 = (int(p2[0]), int(p2[1]))

                        if is_in:
                            self.counter_in += 1
                            cv2.line(annotated_frame, line_pt1, line_pt2, (0, 255, 0), 4)
                            data['cooldown'] = self.COOLDOWN_FRAMES
                        else:
                            self.counter_out += 1
                            cv2.line(annotated_frame, line_pt1, line_pt2, (0, 0, 255), 4)
                            data['cooldown'] = self.COOLDOWN_FRAMES

                data['pos'] = curr_center
                data['side'] = side

        # Prune track_history: remove IDs not in current frame to prevent memory leak
        current_ids = set(track_ids)
        stale_ids = [tid for tid in self.track_history if tid not in current_ids]
        for tid in stale_ids:
            del self.track_history[tid]

        return annotated_frame, self.counter_in, self.counter_out, self.people_in_frame