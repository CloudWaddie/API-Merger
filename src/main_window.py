import json
import sys
import os
from pathlib import Path
import requests
from PyQt5.QtWidgets import QMainWindow, QListView, QPushButton, QMenu, QInputDialog, QMessageBox, QSystemTrayIcon, QAction, QApplication, QWidget, QVBoxLayout, QHBoxLayout
from PyQt5.QtCore import Qt, QAbstractListModel
from PyQt5.QtGui import QIcon
from .api_handler import API_Handler
from .settings_window import Settings_Window
if sys.platform == "win32":
    import winreg


class Main_Window(QMainWindow):
    """
    Class for the main application window.
    """

    def __init__(self):
        """
        Initializes the application window.
        """
        super().__init__()
        self.api = API_Handler()
        self.setWindowTitle("API Merger")
        self.setGeometry(100, 100, 560, 200)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.api_list_model = API_list_model(self.api)

        self.api_list_view = QListView(self)
        self.api_list_view.setModel(self.api_list_model)
        self.api_list_view.selectionModel().selectionChanged.connect(self.update_button_state)
        self.api_list_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.api_list_view.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.api_list_view)

        button_layout = QHBoxLayout()
        layout.addLayout(button_layout)

        self.start_button = QPushButton("Start API", self)
        self.start_button.clicked.connect(self.start)
        button_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop API", self)
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop)
        button_layout.addWidget(self.stop_button)

        self.add_button = QPushButton("Add New", self)
        self.add_button.clicked.connect(self.add)
        button_layout.addWidget(self.add_button)

        self.edit_button = QPushButton("Edit", self)
        self.edit_button.setEnabled(False)
        self.edit_button.clicked.connect(self.edit)
        button_layout.addWidget(self.edit_button)

        self.delete_button = QPushButton("Delete", self)
        self.delete_button.setEnabled(False)
        self.delete_button.clicked.connect(self.delete)
        button_layout.addWidget(self.delete_button)

        menu_bar = self.menuBar()
        settings_menu = menu_bar.addMenu("Settings")
        open_settings_action = settings_menu.addAction("Open Settings")
        open_settings_action.triggered.connect(self.open_settings)

        self.tray_icon = QSystemTrayIcon(self)
        # The icon file needs to be in the same directory as the script, or you can provide an absolute path.
        # This is a placeholder icon, and you should replace it with your own.
        self.tray_icon.setIcon(QIcon("icon.ico"))
        self.tray_icon.setToolTip("API Merger")

        tray_menu = QMenu()
        show_action = tray_menu.addAction("Show/Hide")
        show_action.triggered.connect(self.toggle_visibility)
        quit_action = tray_menu.addAction("Quit")
        quit_action.triggered.connect(self.quit_application)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)

        self.tray_icon.show()

        self.set_autostart()

    def set_autostart(self):
        """
        Sets the application to launch at startup.
        """
        try:
            with open("config.json", 'r') as config_file:
                config = json.load(config_file)
        except (FileNotFoundError, json.JSONDecodeError):
            config = {}

        if config.get("auto_start", False):
            # For this to work in a packaged application, sys.executable needs to be the path to the executable
            if sys.platform == "win32":
                key = winreg.HKEY_CURRENT_USER
                subkey = r"Software\Microsoft\Windows\CurrentVersion\Run"
                with winreg.OpenKey(key, subkey, 0, winreg.KEY_SET_VALUE) as registry_key:
                    winreg.SetValueEx(registry_key, "API Merger", 0, winreg.REG_SZ, sys.executable)
            elif sys.platform == "darwin":
                plist_path = Path.home() / "Library/LaunchAgents/com.api-merger.plist"
                if not plist_path.exists():
                    plist_path.write_text(f"""
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.api-merger</string>
    <key>ProgramArguments</key>
    <array>
        <string>{sys.executable}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
""")
            elif sys.platform == "linux":
                desktop_file_path = Path.home() / ".config/autostart/api-merger.desktop"
                if not desktop_file_path.exists():
                    desktop_file_path.write_text(f"""
[Desktop Entry]
Type=Application
Exec={sys.executable}
Hidden=false
NoDisplay=false
Name=API Merger
Comment=API Merger
X-GNOME-Autostart-enabled=true
""")
        else:
            if sys.platform == "win32":
                key = winreg.HKEY_CURRENT_USER
                subkey = r"Software\Microsoft\Windows\CurrentVersion\Run"
                with winreg.OpenKey(key, subkey, 0, winreg.KEY_SET_VALUE) as registry_key:
                    try:
                        winreg.DeleteValue(registry_key, "API Merger")
                    except FileNotFoundError:
                        pass
            elif sys.platform == "darwin":
                plist_path = Path.home() / "Library/LaunchAgents/com.api-merger.plist"
                if plist_path.exists():
                    plist_path.unlink()
            elif sys.platform == "linux":
                desktop_file_path = Path.home() / ".config/autostart/api-merger.desktop"
                if desktop_file_path.exists():
                    desktop_file_path.unlink()

    def tray_icon_activated(self, reason):
        """
        Handles the tray icon being activated.
        """
        if reason == QSystemTrayIcon.Trigger:
            self.toggle_visibility()

    def toggle_visibility(self):
        """
        Toggles the visibility of the main window.
        """
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.activateWindow()

    def quit_application(self):
        """
        Quits the application.
        """
        self.api.kill_api()
        QApplication.quit()

    def open_settings(self):
        """
        Opens the settings window.
        """
        settings_window = Settings_Window(self)
        if settings_window.exec_():
            self.set_autostart()

    def closeEvent(self, event):
        """
        Overrides the close event to hide the window to the tray.
        """
        try:
            with open("config.json", 'r') as config_file:
                config = json.load(config_file)
        except (FileNotFoundError, json.JSONDecodeError):
            config = {}

        if config.get("minimize_to_tray", False):
            event.ignore()
            self.hide()
        else:
            self.quit_application()

    def show_context_menu(self, pos):
        """
        Called when the user right clicks in api_list_view.
        """
        index = self.api_list_view.indexAt(pos)
        if index.isValid(): # If the user right clicked on an item
            menu = QMenu(self)

            edit_option = menu.addAction('Edit')
            edit_option.triggered.connect(self.edit)

            delete_option = menu.addAction('Delete')
            delete_option.triggered.connect(self.delete)

            if index.row() > 0:
                move_up_option = menu.addAction('Move Up')
                move_up_option.triggered.connect(self.move_up)

            if index.row() < len(self.api_list_model.sources) - 1:
                move_down_option = menu.addAction('Move Down')
                move_down_option.triggered.connect(self.move_down)

            if self.api_list_model.sources[index.row()]["enabled"] == True:
                disable_option = menu.addAction('Disable')
                disable_option.triggered.connect(self.disable)

            else:
                enable_option = menu.addAction('Enable')
                enable_option.triggered.connect(self.enable)

            menu.exec_(self.mapToGlobal(pos))

    def start(self):
        """
        Handles the start button being clicked.
        """
        self.start_button.setEnabled(False)
        self.api.start_api()
        self.stop_button.setEnabled(True)

    def stop(self):
        """
        Handles the stop button being clicked.
        """
        self.stop_button.setEnabled(False)
        self.api.kill_api()
        self.start_button.setEnabled(True)

    def add(self):
        """
        Handles the add button being clicked.
        """
        text, ok = QInputDialog.getText(self, "Input New URL", f"Please input the URL you would like to add:\t\t\t\t{chr(160)}") # Adds whitespace at the end of the line to widen window
        if ok:
            if text.startswith('http'):
                self.api_list_model.sources.append({"url": text, "enabled": True})
                self.api_list_model.update()
            else:
                QMessageBox.information(self, "Error", "Invalid URL! Must begin with 'http' or 'https'", QMessageBox.Ok)

    def delete(self):
        """
        Handles the delete button being clicked.
        """
        selected_indexes = self.api_list_view.selectedIndexes()
        if selected_indexes:
            index = selected_indexes[0]
            url = self.api_list_model.sources[index.row()]["url"].split("?")[0] + "..."
            reply = QMessageBox.question(
                self,
                "Confirm Delete",
                f"Are you sure you want to delete the URL:\n{url}?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                del self.api_list_model.sources[index.row()]
                self.api_list_model.update()
                self.api_list_view.clearSelection()

    def edit(self):
        """
        Handles the edit button being clicked.
        """
        selected_indexes = self.api_list_view.selectedIndexes()
        if selected_indexes:            
            index = selected_indexes[0]
            text, ok = QInputDialog.getText(self, "Edit URL", f"Input edited URL:\t\t\t\t\t\t\t{chr(160)}", text=self.api_list_model.sources[index.row()]["url"]) # Adds whitespace at the end of the line to widen window
            if ok:
                if text.startswith('http'):
                    self.api_list_model.sources[index.row()]["url"] = text
                    self.api_list_model.update()
                else:
                    QMessageBox.information(self, "Error", "Invalid URL! Must begin with 'http' or 'https'", QMessageBox.Ok)

    def move_up(self):
        """
        Moves the selected row up 1 position in the table.
        """
        selected_indexes = self.api_list_view.selectedIndexes()
        if selected_indexes:
            index = selected_indexes[0].row()
            self.api_list_model.sources.insert(index - 1, self.api_list_model.sources.pop(index))
            self.api_list_model.update()

    def move_down(self):
        """
        Moves the selected row down 1 position in the table.
        """
        selected_indexes = self.api_list_view.selectedIndexes()
        if selected_indexes:
            index = selected_indexes[0].row()
            self.api_list_model.sources.insert(index + 1, self.api_list_model.sources.pop(index))
            self.api_list_model.update()

    def disable(self):
        """
        Disables the selected API.
        """
        selected_indexes = self.api_list_view.selectedIndexes()
        if selected_indexes:
            index = selected_indexes[0].row()
            self.api_list_model.sources[index]["enabled"] = False
            self.api_list_model.update()
            url = self.api_list_model.sources[index]["url"]
            if self.api.api_process:
                try:
                    requests.post("http://127.0.0.1:8000/remove_url", json={"url": url})
                except requests.exceptions.ConnectionError:
                    pass # API not running

    def enable(self):
        """
        Enables the selected API.
        """
        selected_indexes = self.api_list_view.selectedIndexes()
        if selected_indexes:
            index = selected_indexes[0].row()
            self.api_list_model.sources[index]["enabled"] = True
            self.api_list_model.update()
            url = self.api_list_model.sources[index]["url"]
            if self.api.api_process:
                try:
                    requests.post("http://127.0.0.1:8000/add_url", json={"url": url})
                except requests.exceptions.ConnectionError:
                    pass # API not running

    def update_button_state(self):
        """
        Updates the state of the edit and delete buttons (called when selection changes).
        """
        selected_indexes = self.api_list_view.selectedIndexes()
        self.delete_button.setEnabled(bool(selected_indexes))
        self.edit_button.setEnabled(bool(selected_indexes))


class API_list_model(QAbstractListModel):
    """
    Class to model the list of URLs.
    """

    def __init__(self, api):
        """
        Initializes the model.
        """
        self.api = api
        super(API_list_model, self).__init__()
        try:
            with open("config.json", 'r') as config_file:
                config = json.load(config_file)

            if "urls" in config.keys(): # Detect and fix outdated config.json files
                self.config = {"sources": []}
                for url in config["urls"]:
                    self.config["sources"].append({"url": url, "enabled": True})
                with open("config.json", 'w') as config_file:
                    json.dump(self.config, config_file)

            else:
                self.config = config

        except FileNotFoundError:
            self.config = {"sources": []}
            with open("config.json", "w") as config_file:
                json.dump(self.config, config_file)
        self.sources = self.config["sources"]

    def data(self, index, role):
        if role == Qt.DisplayRole:
            if self.sources[index.row()]["enabled"] == True:
                return self.sources[index.row()]["url"].split("?")[0] + "..."
            else:
                return f"(disabled) {self.sources[index.row()]['url'].split('?')[0]}..."

    def rowCount(self, index):
        return len(self.sources)

    def update(self):
        """
        Updates config file and applies the changes wherever needed.
        """
        self.layoutChanged.emit()
        self.config["sources"] = self.sources
        with open("config.json", "w") as config_file:
            json.dump(self.config, config_file, indent=4)
