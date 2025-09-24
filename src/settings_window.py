import json
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QCheckBox, QPushButton, QDialogButtonBox


class Settings_Window(QDialog):
    """
    Class for the settings window.
    """

    def __init__(self, parent=None):
        """
        Initializes the settings window.
        """
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(300)

        self.layout = QVBoxLayout(self)

        self.tray_checkbox = QCheckBox("Minimize to system tray on close")
        self.layout.addWidget(self.tray_checkbox)

        self.autostart_checkbox = QCheckBox("Auto-start on system launch")
        self.layout.addWidget(self.autostart_checkbox)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

        self.load_settings()

    def load_settings(self):
        """
        Loads settings from config.json.
        """
        try:
            with open("config.json", 'r') as config_file:
                self.config = json.load(config_file)
        except (FileNotFoundError, json.JSONDecodeError):
            self.config = {}

        self.tray_checkbox.setChecked(self.config.get("minimize_to_tray", False))
        self.autostart_checkbox.setChecked(self.config.get("auto_start", False))

    def accept(self):
        """
        Saves settings to config.json and closes the dialog.
        """
        self.config["minimize_to_tray"] = self.tray_checkbox.isChecked()
        self.config["auto_start"] = self.autostart_checkbox.isChecked()

        with open("config.json", 'w') as config_file:
            json.dump(self.config, config_file, indent=4)

        super().accept()
