from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QComboBox,
                            QPushButton, QHBoxLayout, QVBoxLayout, QWidget,
                            QProgressBar, QToolButton, QMenu, QAction,
                            QSpacerItem, QSizePolicy, QCheckBox)

from PyQt5.QtCore import Qt, QObject, QThread, pyqtSignal, QUrl
from PyQt5.QtGui import QColor, QDesktopServices
from godot_launcher import utils

signaler = utils.signaler

godot_colors = {
    "background": "#262C3B",
    "foreground": "#333B4F",
    "text": "#CCCED3",
    "text_disabled": "#626772",
    "button_bg": "#355570",
    "button_text": "#CCCED3",
    "label_bg": "#262C3B",
    "label_text": "#CCCED3",
}

stylesheet = f"""
    QMainWindow {{
        background-color: {godot_colors["background"]};
        color: {godot_colors["foreground"]};
    }}
    QLabel {{
        color: {godot_colors["text"]};
    }}
    QComboBox {{
        background-color: {godot_colors["button_bg"]};
        color: {godot_colors["button_text"]};
        padding: 5px;
        border-radius: 2px;
        selection-background-color: {godot_colors["background"]};
        selection-color: {godot_colors["foreground"]};
    }}
    QPushButton {{
        background-color: {godot_colors["button_bg"]};
        color: {godot_colors["button_text"]};
        padding: 5px;
        border-radius: 2px;
    }}
    QPushButton:disabled {{
        background-color: {godot_colors["button_bg"]};
        color: {godot_colors["text_disabled"]};
    }}
    QToolButton {{
        background-color: {godot_colors["button_bg"]};
        color: {godot_colors["button_text"]};
        padding: 5px;
        border: none;
    }}
    QCheckBox {{
        background-color: {godot_colors["button_bg"]};
        color: {godot_colors["button_text"]};
        padding: 5px;
        border: none;
    }}

"""

class InstallThread(QThread):

    install_finished = pyqtSignal()

    def __init__(self, app, selected_avail, use_mono):
        super().__init__()
        self.selected_avail = selected_avail
        self.use_mono = use_mono
        self.app = app

    def run(self):
        self.app.install_version(self.selected_avail, self.use_mono)

        self.install_finished.emit()
        
        
class UI:
    def __init__(self, app):
        self.app = app
        self.q_app = QApplication([])
        self.main_window = MainWindow(self)
    
    def initialize(self):
        """ Called from main App at runtime"""
        
        self.main_window.populate_release_versions()
        self.main_window.populate_installed_versions()
        
        # Disable Launch button if no engine is installed
        if not self.main_window.installed_combo.currentText():
            self.main_window.launch_button.setEnabled(False)

    def launch(self):
        self.main_window.show()
        self.q_app.exec_()
        
class MainWindow(QMainWindow):
    def __init__(self, ui):
        self.ui = ui
        
        self.download_percent = 0
        self.total_download_size = ""
        
        self.zip_percent = 0
        self.total_zip_size = ""
        
        signaler.percent_signal.connect(self.on_progress_update)
        signaler.download_finished_signal.connect(self.on_download_finished)
        signaler.unzip_percent_signal.connect(self.on_unzip_progress)
        signaler.unzip_finished_signal.connect(self.on_unzip_finished)
        
        super().__init__()
        self.setStyleSheet(stylesheet)
        
        # Create Widgets
        self.installed_label = QLabel("Installed Versions:")
        self.installed_label.setAlignment(Qt.AlignCenter)    
        self.installed_label.setFixedHeight(10)
        
        self.available_label = QLabel("Available Versions:")
        self.available_label.setAlignment(Qt.AlignCenter)
        self.available_label.setFixedHeight(10)

        # Create the comboboxes
        self.installed_combo = QComboBox()
        self.installed_combo.currentIndexChanged.connect(self.on_installed_changed)

        self.available_combo = QComboBox()
        self.available_combo.currentIndexChanged.connect(self.on_available_changed)
        
        self.use_mono_checkbox = QCheckBox("Install Mono Version")

        self.launch_button = QPushButton("Launch")
        self.launch_button.clicked.connect(self.on_launch_clicked)
        
        self.install_button = QPushButton("Install")
        self.install_button.clicked.connect(self.on_install_clicked)
        self.install_button.setFixedHeight(30)
        self.install_button.setFixedWidth(175)
        

        self.settings_button = QToolButton()
        self.settings_button.setText("Settings")
        self.settings_button.setPopupMode(QToolButton.InstantPopup)
        self.settings_button.setFixedHeight(30)
        self.settings_button.setFixedWidth(175)

        self.menu = QMenu(self.settings_button)
        self.settings_button.setMenu(self.menu)

        self.action1 = QAction("Uninstall", self.settings_button)
        self.action2 = QAction("Open Folder", self.settings_button)
        self.menu.addAction(self.action1)
        self.menu.addAction(self.action2)
        
        self.action1.triggered.connect(self.uninstall_clicked)
        self.action2.triggered.connect(self.open_engine_folder)

        self.message_label = QLabel("")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.hide()
        
        self.zip_bar = QProgressBar()
        self.zip_bar.setRange(0, 100)
        self.zip_bar.hide()
        

        # Set up the layout
        central_widget = QWidget(self)

        # Overall layout
        main_layout = QVBoxLayout(central_widget)

        
        top_layout = QHBoxLayout()
        installed_layout = QVBoxLayout()
        installed_layout.addWidget(self.installed_label)
        installed_layout.addWidget(self.installed_combo)
        installed_layout.addWidget(self.settings_button)
        
        available_layout = QVBoxLayout()
        available_layout.addWidget(self.available_label)
        available_layout.addWidget(self.available_combo)           
        available_layout.addWidget(self.install_button) 
        
        top_layout.addLayout(installed_layout)
        top_layout.addLayout(available_layout)
        
        
        mono_layout = QHBoxLayout()
        spacer_item = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)
        mono_layout.addSpacerItem(spacer_item)
        mono_layout.addWidget(self.use_mono_checkbox)
        
        

        bottom_layout = QVBoxLayout()        
        bottom_layout.addWidget(self.launch_button)
        bottom_layout.addWidget(self.message_label)
        bottom_layout.addWidget(self.progress_bar)
        bottom_layout.addWidget(self.zip_bar)
        self.launch_button.setFixedHeight(50)
        
        main_layout.addLayout(top_layout)
        main_layout.addLayout(mono_layout)
        main_layout.addSpacing(50)
        main_layout.addLayout(bottom_layout)
        
        self.setCentralWidget(central_widget)

        # Set the window properties
        self.setWindowTitle(f"Godot Launcher v{self.ui.app.version}")
        self.setGeometry(350, 350, 300, 300)
        
    def populate_release_versions(self):
        versions = self.ui.app.config.get_available_versions()
        self.available_combo.clear()
        if self.ui.app.config.version_is_installed(versions[0]):
            self.install_button.setEnabled(False)
            self.install_button.setText("Installed")
            
        for version in versions:
            self.available_combo.addItem(version)
            
    def populate_installed_versions(self):
        self.installed_combo.clear()
        installed_versions = self.ui.app.config.get_installed_versions()
        if installed_versions:
            selected_version = self.ui.app.config.get_selected_version()
            
            selected_index = None
            
            for x in range(len(installed_versions)):
                version = installed_versions[x]
                self.installed_combo.addItem(version)
                if version == selected_version:
                    selected_index = x
            if selected_index != None:
                self.installed_combo.setCurrentIndex(selected_index)
            
        else:
            self.installed_combo.addItem("No Engines Found")
            self.installed_combo.setEnabled(False)
            
    def on_available_changed(self):
        selected_avail = self.available_combo.currentText()
        if self.ui.app.config.version_is_installed(selected_avail):
            self.install_button.setEnabled(False)
            self.install_button.setText("Installed")
        else:
            self.install_button.setEnabled(True)
            self.install_button.setText("Install")
            
        
    def on_installed_changed(self):
        selected_installed = self.installed_combo.currentText()
        if selected_installed == "No Engines Found":
            self.launch_button.setEnabled(False)
            return
        else:
            self.ui.app.config.set_selected_version(selected_installed)
            self.launch_button.setEnabled(True)
            
    def on_launch_clicked(self):
        selected_installed = self.installed_combo.currentText()
        engine_path = self.ui.app.config.get_engine_version_path(selected_installed)
        self.ui.app.launch(engine_path)
    
    def on_install_clicked(self):
        selected_avail = self.available_combo.currentText()
        use_mono = self.use_mono_checkbox.isChecked()
        self.ui.app.logger.info(f"Installing version: {selected_avail}")        
        self.message_label.setText("Starting Download...")
        self.progress_bar.show()

        self.install_thread = InstallThread(self.ui.app, selected_avail, use_mono)
        self.install_thread.install_finished.connect(self.on_install_finished)

        self.install_thread.start()
        
    def on_progress_update(self, count, block_size, total_size):
        if not self.total_download_size:
            self.total_download_size = utils.convert_bytes(total_size)
        percent = int(count * block_size * 100 / total_size)
        if percent != self.download_percent:
            self.message_label.setText(f"Downloaded: {utils.convert_bytes(count * block_size)} - {self.total_download_size}")
            self.download_percent = percent
            self.progress_bar.setValue(self.download_percent)
    
        
    def on_download_finished(self):
        
        self.download_percent = 0
        self.total_download_size = ""
        
        self.progress_bar.hide()
        self.progress_bar.setValue(0)
        
        
        self.message_label.setText("Unzipping:...")
        self.zip_bar.setValue(0)
        
        self.zip_bar.show()

    def on_unzip_progress(self, extracted_files, total_files):
        percent = int((extracted_files / total_files) * 100)
        if percent != self.zip_percent:
            self.zip_percent = percent
            self.zip_bar.setValue(self.zip_percent)
    
    def on_unzip_finished(self):
        self.zip_percent = 0
        self.total_zip_size = ""
        
        self.zip_bar.hide()
        
        self.message_label.setText("Unzipped Successfully")
        self.zip_bar.setValue(0)
    
    def on_install_finished(self):
        self.populate_installed_versions()
        self.message_label.setText("Install Completed!")
        self.ui.app.logger.info(f"Installing complete.")

    def uninstall_clicked(self):
        selected_installed = self.installed_combo.currentText()
        engine_path = self.ui.app.config.get_engine_version_path(selected_installed)
        self.ui.app.uninstall_version(engine_path)
        self.populate_installed_versions()

    def open_engine_folder(self):
        selected_installed = self.installed_combo.currentText()
        engine_path = self.ui.app.config.get_engine_version_path(selected_installed)
        url = QUrl.fromLocalFile(engine_path)
        QDesktopServices.openUrl(url)
        