import json
import os

class SettingsManager:
    def __init__(self, settings_file="settings.json"):
        self.settings_file = settings_file
        self.default_settings = {
            "line_coords": [],
            "direction_swapped": False,
            "api_endpoint": "https://tramcreditalgeria.up.railway.app/api/transaction/Passenger", # Added API endpoint
            "video_source_type": "video", 
            "video_path": "",            
            "ip_url": "",                
            "webcam_index": 0,
            "conf_threshold": 0.45,
            "model_name": "yolov8n.pt",
            "tracker_type": "bytetrack.yaml"
        }
        self.settings = self.default_settings.copy() # Initialize with defaults

    def load_settings(self):
        """Loads settings from the JSON file, merging with defaults."""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, "r") as f:
                    loaded_settings = json.load(f)
                    # Merge loaded settings with defaults to ensure all keys exist
                    self.settings = {**self.default_settings, **loaded_settings}
            except json.JSONDecodeError:
                print(f"Warning: Could not read settings file '{self.settings_file}' (JSON decode error). Using default settings.")
                self.settings = self.default_settings.copy()
            except Exception as e:
                print(f"Warning: An error occurred while loading settings from '{self.settings_file}': {e}. Using default settings.")
                self.settings = self.default_settings.copy()
        else:
            print(f"Info: Settings file '{self.settings_file}' not found. Using default settings.")
            self.settings = self.default_settings.copy()
        return self.settings

    def save_settings(self, settings_to_save):
        """Saves the provided settings dictionary to the JSON file."""
        try:
            with open(self.settings_file, "w") as f:
                json.dump(settings_to_save, f, indent=4)
        except Exception as e:
            print(f"Error: Failed to save settings to '{self.settings_file}': {e}")

    def get_setting(self, key, default=None):
        """Retrieves a specific setting by key with optional fallback."""
        if default is not None:
            return self.settings.get(key, default)
        return self.settings.get(key, self.default_settings.get(key))

    def update_setting(self, key, value):
        """Updates a specific setting and persists to disk immediately."""
        self.settings[key] = value
        self.save_settings(self.settings)