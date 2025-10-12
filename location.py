import sys
import subprocess
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QComboBox, QHBoxLayout
)

class LocationSettings(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Select Your Location Settings")
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("<h2>Select Location Settings</h2>"))

        # --- Language ---
        lang_layout = QHBoxLayout()
        lang_layout.addWidget(QLabel("Language:"))
        self.lang_combo = QComboBox()
        self.add_languages()
        lang_layout.addWidget(self.lang_combo)
        layout.addLayout(lang_layout)

        # --- Keyboard Layout ---
        kb_layout = QHBoxLayout()
        kb_layout.addWidget(QLabel("Keyboard Layout:"))
        self.kb_combo = QComboBox()
        self.add_keymaps()
        kb_layout.addWidget(self.kb_combo)
        layout.addLayout(kb_layout)

        # --- Timezone ---
        tz_layout = QHBoxLayout()
        tz_layout.addWidget(QLabel("Timezone:"))
        self.tz_combo = QComboBox()
        self.add_timezones()
        tz_layout.addWidget(self.tz_combo)
        layout.addLayout(tz_layout)

        layout.addStretch()

    def add_languages(self):
        langs = {
            "English (US)": "en_US.UTF-8",
            "Polish": "pl_PL.UTF-8",
            "German": "de_DE.UTF-8",
            "French": "fr_FR.UTF-8"
        }
        for name in langs:
            self.lang_combo.addItem(name)

    def add_keymaps(self):
        try:
            result = subprocess.run(
                ["localectl", "list-keymaps"],
                capture_output=True, text=True, check=True
            )
            for layout in result.stdout.splitlines():
                self.kb_combo.addItem(layout)
        except Exception as e:
            print("Error loading keymaps:", e)
            self.kb_combo.addItem("us")

    def add_timezones(self):
        """Runs 'timedatectl list-timezones' and fills the dropdown."""
        try:
            result = subprocess.run(
                ["timedatectl", "list-timezones"],
                capture_output=True, text=True, check=True
            )
            zones = result.stdout.splitlines()

            # Add them to the dropdown
            for zone in zones:
                self.tz_combo.addItem(zone)

        except Exception as e:
            self.tz_combo.addItem("Error loading timezones")
            print("Error:", e)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = LocationSettings()
    win.show()
    sys.exit(app.exec())