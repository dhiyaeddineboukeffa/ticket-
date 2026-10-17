import cv2
from ultralytics import YOLO
import numpy as np
import os

class VideoProcessor:
    COOLDOWN_FRAMES = 15 

    def __init__(self, model_path='yolov8n.pt', class_list_path='coco.txt'):
        self.model = YOLO(model_path)
        self.class_list = self._load_class_list(class_list_path)
        self.person_class_index = self.class_list.index('person') if 'person' in self.class_list else -1
        
        self.line_coords = None
        self.line_vector = None
        self.line_normal = None
        
        self.direction_swapped = False
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
            p1 = np.array(self.line_coords[0])
            p2 = np.array(self.line_coords[1])
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
        
        # If swapped, IN is in the direction of the normal. Otherwise, it's against it.
        return normalized_normal if self.direction_swapped else -normalized_normal

    def reset(self):
        self.track_history = {}
        self.counter_in = 0
        self.counter_out = 0
        self.people_in_frame = 0 # Initialize new counter for people in frame

    def process_frame(self, frame):
        results = self.model.track(frame, persist=True, classes=[self.person_class_index])
        
        num_boxes = len(results[0].boxes) if results[0].boxes is not None else 0
        self.people_in_frame = num_boxes
        annotated_frame = results[0].plot()

        if self.line_coords is None:
            return annotated_frame, self.counter_in, self.counter_out, self.people_in_frame

        if results[0].boxes.id is None:
            return annotated_frame, self.counter_in, self.counter_out, self.people_in_frame

        boxes = results[0].boxes.xywh.cpu()
        track_ids = results[0].boxes.id.int().cpu().tolist()

        for box, track_id in zip(boxes, track_ids):
            x, y, w, h = box
            center_point = np.array([x, y])
            point_vector = center_point - np.array(self.line_coords[0])
            side = np.dot(point_vector, self.line_normal)

            if track_id not in self.track_history:
                self.track_history[track_id] = [side, 0]
            else:
                last_side, cooldown = self.track_history[track_id]
                
                if cooldown > 0:
                    self.track_history[track_id][1] -= 1
                
                if cooldown == 0:
                    in_condition = last_side > 0 and side < 0
                    out_condition = last_side < 0 and side > 0

                    if self.direction_swapped:
                        in_condition, out_condition = out_condition, in_condition

                    if in_condition:
                        self.counter_in += 1
                        cv2.line(annotated_frame, self.line_coords[0], self.line_coords[1], (0, 255, 0), 4)
                        self.track_history[track_id][1] = self.COOLDOWN_FRAMES
                    elif out_condition:
                        self.counter_out += 1
                        cv2.line(annotated_frame, self.line_coords[0], self.line_coords[1], (0, 0, 255), 4)
                        self.track_history[track_id][1] = self.COOLDOWN_FRAMES
                
                self.track_history[track_id][0] = side

        # Prune track_history: remove IDs not in current frame to prevent memory leak
        current_ids = set(track_ids)
        stale_ids = [tid for tid in self.track_history if tid not in current_ids]
        for tid in stale_ids:
            del self.track_history[tid]

        return annotated_frame, self.counter_in, self.counter_out, self.people_in_frame