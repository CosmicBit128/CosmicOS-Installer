from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QTextBrowser, QLineEdit, QCheckBox, QComboBox, QProgressBar,
    QVBoxLayout, QHBoxLayout, QStackedWidget, QMainWindow, QMessageBox
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import sys, subprocess, re

from location import LocationSettings
from install_system import Installer


with open('LICENSE.txt', 'r') as f:
    LICENSE = f.read()



class InstallThread(QThread):
    log_signal = pyqtSignal(str)
    done_signal = pyqtSignal(bool, str)

    def __init__(self, root, settings):
        super().__init__()
        self.root = root
        self.settings = settings
        self.success = False
        self.error_msg = ""

    def run(self):
        try:
            # Create dummy app-like object with logger
            class DummyApp:
                def __init__(self, log_signal):
                    self.logger = self
                    self.log_signal = log_signal

                def log(self, msg):
                    self.log_signal.emit(msg)

            from install_system import Installer
            inst = Installer(DummyApp(self.log_signal), self.root, self.settings)
            inst.install()
            self.success = True
        except Exception as e:
            self.error_msg = str(e)
        finally:
            self.done_signal.emit(self.success, self.error_msg)



class InstallerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CosmicOS Installer")
        self.setGeometry(200, 100, 960, 540)

        # Main container
        central = QWidget()
        self.setCentralWidget(central)

        # Create stacked widget for pages
        self.pages = QStackedWidget()
        self.page_list: list[QWidget] = []

        # Navigation buttons
        self.back_btn = QPushButton("Back")
        self.next_btn = QPushButton("Next")
        self.quit_btn = QPushButton("Quit")

        self.back_btn.clicked.connect(self.go_back)
        self.next_btn.clicked.connect(self.go_next)
        self.quit_btn.clicked.connect(self.close)


        # Layout setup
        nav_layout = QHBoxLayout()
        nav_layout.addStretch()
        nav_layout.addWidget(self.back_btn)
        nav_layout.addWidget(self.next_btn)
        nav_layout.addWidget(self.quit_btn)

        main_layout = QVBoxLayout(central)
        main_layout.addWidget(self.pages)
        main_layout.addLayout(nav_layout)

        # Create Widgets
        self.location_settings = LocationSettings()
        self.hostname = QLineEdit("")

        self.license_check = QCheckBox("I read and accept the license agreement")

        self.boot_combo = QComboBox()
        self.root_combo = QComboBox()
        self.home_combo = QComboBox()
        self.uefi = QCheckBox("Is system UEFI?")

        self.user_name = QLineEdit("")
        self.user_pass = QLineEdit("")
        self.root_pass = QLineEdit("")
        self.sudo_check = QCheckBox("Is the user sudo?")
        self.root_check = QCheckBox("Use same password for root")
        self.root_pass_label = QLabel("Root Password")

        self.de = QComboBox()
        
        # Configure Widgets
        self.uefi.setStyleSheet("margin-top: 16px;")
        self.boot_combo.currentTextChanged.connect(self.update_buttons)
        self.root_combo.currentTextChanged.connect(self.update_buttons)
        self.home_combo.currentTextChanged.connect(self.update_buttons)
        self.hostname.textChanged.connect(self.update_buttons)
        self.user_name.textChanged.connect(self.update_buttons)
        self.user_pass.textChanged.connect(self.update_buttons)
        self.root_pass.textChanged.connect(self.update_buttons)
        self.uefi.checkStateChanged.connect(self.update_buttons)
        self.user_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.root_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.root_check.checkStateChanged.connect(self.update_labels)
        self.license_check.checkStateChanged.connect(self.update_buttons)
        self.de.addItems(["GNOME", "KDE Plasma", "Mate", "Hyprland"])

        # Add pages
        self.add_page(self.welcome_page())
        self.add_page(self.license_page())
        self.add_page(self.location_page())
        self.add_page(self.partition_page())
        self.add_page(self.account_page())
        self.add_page(self.setup_page())
        self.add_page(self.summary_page())
        self.add_page(self.install_page())
        self.add_page(self.finish_page())

        self.update_buttons()

    # Helper to add pages
    def add_page(self, widget):
        self.page_list.append(widget)
        self.pages.addWidget(widget)


    # ======== PAGES ======== #

    # Page 1: Welcome
    def welcome_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        label = QLabel("Welcome!")
        label.setStyleSheet("font-size: 24px; font-weight: bold;")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Add image (logo or banner)
        image = QLabel()
        pix = QPixmap("idioma.png")
        image.setPixmap(pix.scaledToWidth(450))
        image.setStyleSheet("margin-top: 96px;")
        image.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(label)
        layout.addWidget(image)
        layout.addStretch()
        return page
    
    # Page 2: License
    def license_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        text = QTextBrowser()
        text.setPlainText(LICENSE)
        text.setMinimumHeight(480)

        layout.addWidget(text)
        layout.addWidget(self.license_check)
        layout.addStretch()
        return page
    
    # Page 3: Location
    def location_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        stage = QLabel("<h1>Stage 1: Location</h1>")

        layout.addWidget(stage)
        layout.addWidget(self.location_settings)
        layout.addStretch()

        return page

    # Page 4: Partitioning
    def partition_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        stage = QLabel("<h1>Stage 2: Partitioning</h1>")

        gp_button = QPushButton("Open GParted")
        gp_button.setMaximumWidth(256)
        gp_button.setStyleSheet("padding: 4px;")
        gp_button.clicked.connect(self.open_gparted)
        label1 = QLabel("<code>/boot</code> Mount Point:")
        label2 = QLabel("<code>/</code> (root) Mount Point:")
        label3 = QLabel("<code>/home</code> Mount Point:")
        label1.setStyleSheet("margin-top: 16px;")
        label2.setStyleSheet("margin-top: 16px;")
        label3.setStyleSheet("margin-top: 16px;")

        for part in self.get_partitions():
            self.root_combo.addItem(part)
            self.boot_combo.addItem(part)
            self.home_combo.addItem(part)

        layout.addWidget(stage)
        layout.addWidget(gp_button)
        layout.addWidget(label1)
        layout.addWidget(self.boot_combo)
        layout.addWidget(label2)
        layout.addWidget(self.root_combo)
        layout.addWidget(label3)
        layout.addWidget(self.home_combo)
        layout.addStretch()
        return page
    
    # Page 5: Account Setup
    def account_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        stage = QLabel("<h1>Stage 3: Users</h1>")

        label1 = QLabel("Username")
        label2 = QLabel("Password")
        label3 = QLabel("Username must be longer than 3 and contain characters a-z, A-Z, 0-9, '-', '.' and must not contain spaces.\n")
        label4 = QLabel("Password length must be greater than 8 and only contain alphanumerals and special characters.\n")
        label3.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label4.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label3.setStyleSheet("color: #a0a0a0;")
        label4.setStyleSheet("color: #a0a0a0;")

        layout.addWidget(stage)
        layout.addWidget(label1)
        layout.addWidget(self.user_name)
        layout.addWidget(label3)
        layout.addWidget(label2)
        layout.addWidget(self.user_pass)
        layout.addWidget(label4)
        layout.addWidget(self.sudo_check)
        layout.addWidget(self.root_check)
        layout.addWidget(self.root_pass_label)
        layout.addWidget(self.root_pass)
        layout.addStretch()
        return page
    
    # Page 6: General Setup
    def setup_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        stage = QLabel("<h1>Stage 4: General Setup</h1>")

        hostname = QHBoxLayout()
        hostname.addWidget(QLabel("Hostname:"))
        hostname.addWidget(self.hostname)

        layout.addWidget(stage)
        layout.addWidget(self.uefi)
        layout.addWidget(self.de)
        layout.addLayout(hostname)
        layout.addStretch()
        return page
    
    # Page 7: Summary
    def summary_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        stage = QLabel("<h1>Stage 5: Summary</h1>")

        self.texts = {
            'lang': f"Language: {self.location_settings.lang_combo.currentText()}",
            'kblayout': f"Keyboard Layout: {self.location_settings.lang_combo.currentText()}",
            'tz': f"Timezone: {self.location_settings.lang_combo.currentText()}",

            'pboot': f"Boot Partition: {self.boot_combo.currentText()}",
            'proot': f"Root Partition: {self.root_combo.currentText()}",
            'phome': f"Home Partition: {self.home_combo.currentText()}",

            'u_name': f"Username: {self.user_name.text()}",
            'u_pass': f"User password: {'*'*len(self.user_pass.text())}",
            'r_pass': f"Root password: " + ('Same as user password' if self.root_check.isChecked() else '*'*len(self.root_pass.text()))
        }

        layout.addWidget(stage)
        layout.addStretch()
        return page

    # Page 8: Installation
    def install_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        stage = QLabel("<h1>Stage 6: Installation</h1>")

        self.progr = QProgressBar()
        self.progr.setMaximum(0)

        self.log_view = QTextBrowser()
        self.log_view.setMinimumHeight(300)
        self.log_view.setStyleSheet("background-color: #101010; color: #00ff00; font-family: monospace;")

        layout.addWidget(stage)
        layout.addWidget(self.progr)
        layout.addWidget(self.log_view)
        layout.addStretch()
        return page

    # Page 8: Finish
    def finish_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        label1 = QLabel("<h1 style=\"\">Installation complete!</h1>")
        label2 = QLabel("You may now reboot your machine.")

        label1.setStyleSheet("margin-top: 128px; font-size: 16px;")
        label1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label2.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(label1)
        layout.addWidget(label2)
        layout.addStretch()
        return page

    # Navigation logic
    def go_next(self):
        current = self.pages.currentIndex()
        if current < len(self.page_list) - 1:
            if current == 6:
                reply = QMessageBox.question(
                    self,
                    "Are you sure?",
                    "This will format your drive which <u>cannot be undone</u>!\nDo you wish to continue?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self.pages.setCurrentIndex(current + 1)
                    self.start_installation()
            else:
                self.pages.setCurrentIndex(current + 1)

        self.update_buttons()

    def go_back(self):
        current = self.pages.currentIndex()
        if len(self.page_list) - 1 > current > 0:
            self.pages.setCurrentIndex(current - 1)
        self.update_buttons()


    def update_buttons(self):
        i = self.pages.currentIndex()
        next_enable = False
        match i:
            case 0|2|6|7|8:
                next_enable = True
            case 1:
                next_enable = self.license_check.isChecked()

            case 3:
                next_enable = (
                    self.boot_combo.currentText() != self.root_combo.currentText() and \
                    self.boot_combo.currentText() != self.home_combo.currentText() and \
                    self.root_combo.currentText() != self.home_combo.currentText()
                )

            case 4:
                name_regex = r"[a-zA-Z\d\.-]+"
                pass_regex = r"[\x20-\x7e]+"
                user_name = self.user_name.text()
                user_pass = self.user_pass.text()
                root_pass = self.root_pass.text()
                user_ok = len(user_name) >= 3 and re.fullmatch(name_regex, user_name)
                pass_ok = len(user_pass) >= 8 and re.fullmatch(pass_regex, user_pass)
                root_ok = (len(root_pass) >= 8 and re.fullmatch(pass_regex, root_pass)) or self.root_check.isChecked()
                next_enable = all([user_ok, pass_ok, root_ok])

            case 5:
                next_enable = len(self.hostname.text()) >= 5

        self.next_btn.setEnabled(next_enable)
        self.back_btn.setEnabled(len(self.page_list) - 1 > i > 0)

        if i == len(self.page_list) - 1:
            self.next_btn.setText("Finish")
            self.next_btn.clicked.connect(self.close)
        else:
            self.next_btn.setText("Next")
    
    
    def update_labels(self):
        i = self.pages.currentIndex()
        if i == 4:
            if self.root_check.isChecked():
                self.root_pass_label.hide()
                self.root_pass.hide()
            else:
                self.root_pass_label.show()
                self.root_pass.show()

    def open_gparted(self):
        subprocess.run(["gparted"])

    def get_partitions(self):
        result = subprocess.run(
            ["lsblk", "-rno", "NAME,SIZE,TYPE,MOUNTPOINT"],
            capture_output=True, text=True
        )
        parts = []
        for line in result.stdout.splitlines():
            name, size, *rest = line.split()
            if rest and rest[0] == "part":
                parts.append(f"/dev/{name} ({size})")
            elif len(rest) == 1 and rest[0] == "part":
                parts.append(f"/dev/{name} ({size})")
        return parts
    
    def start_installation(self):
        self.log_view.clear()
        self.progr.setMaximum(0)
        settings = {
            'parts': [
                {"path": "/boot/efi" if self.uefi.isChecked() else "/boot", "part": self.boot_combo.currentText().split()[0]},
                {"path": "/", "part": self.root_combo.currentText().split()[0]},
                {"path": "/home", "part": self.home_combo.currentText().split()[0]}
            ],
            'location': {
                'timezone': self.location_settings.tz_combo.currentText(),
                'language': self.location_settings.lang_combo.currentText(),
                'kb_layout': self.location_settings.kb_combo.currentText()
            },
            'users': {
                'name': self.user_name.text(),
                'pass': self.user_pass.text(),
                'sudo': self.sudo_check.isChecked(),
                'root_pass': self.root_pass.text() if not self.root_check.isChecked() else self.user_pass.text()
            },
            'hostname': self.hostname.text(),
            'de': self.de.currentText().lower()
        }

        self.inst_thread = InstallThread("/mnt/install", settings)
        self.inst_thread.log_signal.connect(self.append_log)
        self.inst_thread.done_signal.connect(self.install_done)
        self.inst_thread.start()

    def append_log(self, text):
        self.log_view.append(text)
        self.log_view.ensureCursorVisible()

    def install_done(self, success, msg):
        self.progr.setMaximum(1)
        if success:
            self.log_view.append("\nInstallation complete!")
            self.pages.setCurrentIndex(self.pages.currentIndex() + 1)
        else:
            self.log_view.append(f"\nInstallation failed:\n\n----------------\nAw shit! Here we go again...\n----------------\n\n{msg}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = InstallerWindow()
    win.show()
    sys.exit(app.exec())
