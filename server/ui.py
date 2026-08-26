import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QSystemTrayIcon, QMenu, QAction, QButtonGroup)
from PyQt5.QtGui import QIcon, QFont, QColor, QPalette
from PyQt5.QtCore import Qt, QTimer, QPoint
from engine import BTDSEngine

class BTDSTrayApp(QWidget):
    def __init__(self):
        super().__init__()
        self.engine = BTDSEngine()
        self.engine.start_server()

        self.init_ui()
        self.init_tray()

        # Telemetry update timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_telemetry)
        self.timer.start(1000)

    def init_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(350, 450)

        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)

        # Background widget for styling
        self.bg_widget = QWidget()
        self.bg_widget.setObjectName("bg_widget")
        self.bg_layout = QVBoxLayout(self.bg_widget)
        self.bg_layout.setSpacing(15)

        # Title
        self.title_label = QLabel("BETTERDISPLAY")
        self.title_label.setObjectName("title_label")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.bg_layout.addWidget(self.title_label)

        # Status
        self.status_label = QLabel("Status: Waiting for connection...")
        self.status_label.setObjectName("status_label")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.bg_layout.addWidget(self.status_label)

        # Connection Mode Switch
        mode_layout = QHBoxLayout()
        self.btn_usb = QPushButton("USB Type-C")
        self.btn_usb.setCheckable(True)
        self.btn_usb.setChecked(True)
        self.btn_wifi = QPushButton("Wi-Fi")
        self.btn_wifi.setCheckable(True)

        self.mode_group = QButtonGroup(self)
        self.mode_group.addButton(self.btn_usb)
        self.mode_group.addButton(self.btn_wifi)
        self.mode_group.buttonClicked.connect(self.change_mode)

        mode_layout.addWidget(self.btn_usb)
        mode_layout.addWidget(self.btn_wifi)
        self.bg_layout.addLayout(mode_layout)

        # Refresh Rate Controls
        self.bg_layout.addWidget(self.create_separator())
        hz_label = QLabel("Refresh Rate (Hz)")
        hz_label.setObjectName("section_label")
        self.bg_layout.addWidget(hz_label)

        hz_layout = QHBoxLayout()
        self.hz_group = QButtonGroup(self)
        for hz in [60, 90, 120, 144]:
            btn = QPushButton(str(hz))
            btn.setCheckable(True)
            if hz == 60:
                btn.setChecked(True)
            self.hz_group.addButton(btn)
            hz_layout.addWidget(btn)
            btn.clicked.connect(lambda checked, h=hz: self.change_fps(h))
        self.bg_layout.addLayout(hz_layout)

        # Telemetry
        self.bg_layout.addWidget(self.create_separator())
        telemetry_label = QLabel("Live Telemetry")
        telemetry_label.setObjectName("section_label")
        self.bg_layout.addWidget(telemetry_label)

        self.lbl_latency = QLabel("Latency: < 5 ms")
        self.lbl_bandwidth = QLabel("Bandwidth: 0.0 Mbps")
        self.lbl_gpu = QLabel("GPU Usage: N/A")
        
        for lbl in [self.lbl_latency, self.lbl_bandwidth, self.lbl_gpu]:
            lbl.setObjectName("telemetry_data")
            self.bg_layout.addWidget(lbl)

        # Close button
        self.btn_hide = QPushButton("Hide")
        self.btn_hide.setObjectName("btn_hide")
        self.btn_hide.clicked.connect(self.hide)
        self.bg_layout.addWidget(self.btn_hide)

        layout.addWidget(self.bg_widget)
        self.setLayout(layout)

        # Apply dark theme stylesheet
        self.setStyleSheet("""
            #bg_widget {
                background-color: #121212;
                border-radius: 15px;
                border: 1px solid #333333;
            }
            #title_label {
                color: #00FFCC;
                font-size: 20px;
                font-weight: bold;
                letter-spacing: 2px;
                margin-top: 10px;
            }
            #status_label {
                color: #B0B0B0;
                font-size: 13px;
                margin-bottom: 10px;
            }
            #section_label {
                color: #FFFFFF;
                font-size: 12px;
                font-weight: bold;
            }
            #telemetry_data {
                color: #00FFCC;
                font-size: 13px;
                font-family: monospace;
            }
            QPushButton {
                background-color: #1E1E1E;
                color: #FFFFFF;
                border: 1px solid #333333;
                border-radius: 5px;
                padding: 8px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2A2A2A;
                border-color: #00FFCC;
            }
            QPushButton:checked {
                background-color: #00FFCC;
                color: #000000;
            }
            #btn_hide {
                background-color: #FF3366;
                color: white;
                margin-top: 10px;
                border: none;
            }
            #btn_hide:hover {
                background-color: #FF5580;
            }
        """)

    def create_separator(self):
        line = QWidget()
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #333333;")
        return line

    def init_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        # In a real app we'd load the generated icon here
        # self.tray_icon.setIcon(QIcon("../assets/icon.jpg")) 
        
        # Create a dummy icon for now
        dummy_icon = QWidget()
        dummy_icon.setStyleSheet("background-color: #00FFCC;")
        self.tray_icon.setIcon(self.style().standardIcon(self.style().SP_ComputerIcon))
        
        tray_menu = QMenu()
        show_action = QAction("Open Status Monitor", self)
        show_action.triggered.connect(self.show_window)
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.quit_app)
        
        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_click)
        self.tray_icon.show()

    def on_tray_click(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.show_window()

    def show_window(self):
        # Position near the system tray (bottom right usually)
        screen = QApplication.primaryScreen().geometry()
        x = screen.width() - self.width() - 20
        y = screen.height() - self.height() - 60
        self.move(x, y)
        self.show()
        self.raise_()
        self.activateWindow()

    def change_mode(self, button):
        mode = "usb" if button == self.btn_usb else "wifi"
        self.engine.set_mode(mode)

    def change_fps(self, fps):
        self.engine.set_fps(fps)

    def update_telemetry(self):
        if self.engine.is_streaming:
            self.status_label.setText("Status: Active & Streaming")
            self.status_label.setStyleSheet("color: #00FF00;")
        else:
            self.status_label.setText("Status: Waiting for connection...")
            self.status_label.setStyleSheet("color: #B0B0B0;")
            
        self.lbl_bandwidth.setText(f"Bandwidth: {self.engine.bandwidth_mbps:.1f} Mbps")
        # In a real scenario, use pynvml or similar for GPU usage.
        self.lbl_gpu.setText("GPU Usage: ~Active (NVENC)")

    def quit_app(self):
        self.engine.shutdown()
        QApplication.quit()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    ex = BTDSTrayApp()
    sys.exit(app.exec_())
