import json
import os
import sys

class SettingsManager:
    def __init__(self, settings_file="settings.json"):
        self.settings_file = self._resolve_settings_file(settings_file)
        self.settings = self.load_settings()

    def _resolve_settings_file(self, settings_file):
        if os.path.isabs(settings_file):
            return settings_file

        if getattr(sys, "frozen", False):
            settings_dir = self._get_user_settings_dir()
            return os.path.join(settings_dir, settings_file)

        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(project_dir, settings_file)

    def _get_user_settings_dir(self):
        base_dir = (
            os.environ.get("LOCALAPPDATA")
            or os.environ.get("APPDATA")
            or os.path.expanduser("~")
        )
        settings_dir = os.path.join(base_dir, "SRDP")
        os.makedirs(settings_dir, exist_ok=True)
        return settings_dir

    def load_settings(self):
        settings = self.get_default_settings()

        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, "r") as f:
                    saved_settings = json.load(f)
                settings.update(saved_settings)
            except (OSError, json.JSONDecodeError):
                pass

        return settings

    def get_default_settings(self):
        return {
            "theme": "System",
            "default_figure_size": [8, 5],
            "line_width": 1.0,
            "rolling_average_window": 1,
            "line_colors": [
                "#1f77b4",
                "#ff7f0e",
                "#2ca02c",
                "#d62728",
                "#9467bd",
                "#8c564b",
                "#e377c2",
                "#7f7f7f",
                "#bcbd22",
                "#17becf",
            ],
        }

    def save_settings(self, settings_dict=None):
        if settings_dict:
            self.settings.update(settings_dict)
        settings_dir = os.path.dirname(self.settings_file)
        if settings_dir:
            os.makedirs(settings_dir, exist_ok=True)
        with open(self.settings_file, "w") as f:
            json.dump(self.settings, f, indent=4)
