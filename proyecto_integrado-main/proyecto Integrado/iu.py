from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QFrame, QSizePolicy, QComboBox
)
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QFont
import sounddevice as sd
import sys
from audio_analyzer import AudioAnalyzer

class CyberUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cyber Audio Cockpit")
        self.setFixedSize(900, 450)
        self.setStyleSheet("background-color: #0d0d0d; color: #00ff99;")

        font_main = QFont("Consolas", 14)

        # Combo de dispositivos de entrada
        self.device_selector = QComboBox()
        self.device_selector.setStyleSheet("background-color: #1a1a1a; color: #00ff99; padding: 5px;")
        self.populate_devices()

        # Panel izquierdo (Frecuencia)
        self.freq_panel = self.create_side_panel("Freq: --- Hz", font_main)
        self.label_freq = self.freq_panel.findChild(QLabel)

        # Panel derecho (Volumen)
        self.vol_panel = self.create_side_panel("Volumen: --- dB", font_main)
        self.label_volume = self.vol_panel.findChild(QLabel)

        # Panel central (Orbe)
        self.orb_panel = QFrame()
        self.orb_panel.setStyleSheet("""
            QFrame {
                background-color: #000000;
                border: 3px solid #00ff99;
                border-radius: 20px;
            }
        """)
        self.label_orb = QLabel("ORBE")
        self.label_orb.setAlignment(Qt.AlignCenter)
        self.label_orb.setFont(QFont("Consolas", 24))
        orb_layout = QVBoxLayout()
        orb_layout.addStretch()
        orb_layout.addWidget(self.label_orb)
        orb_layout.addStretch()
        self.orb_panel.setLayout(orb_layout)

        # Botón para iniciar análisis
        self.button_start = QPushButton("Iniciar análisis")
        self.button_start.setStyleSheet("""
            QPushButton {
                background-color: #00ff99;
                color: #000000;
                border: none;
                padding: 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #33ffaa;
            }
        """)
        self.button_start.clicked.connect(self.start_analysis)

        # Layout principal
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.device_selector)

        panels = QHBoxLayout()
        panels.addWidget(self.freq_panel)
        panels.addWidget(self.orb_panel, stretch=1)
        panels.addWidget(self.vol_panel)

        main_layout.addLayout(panels)
        main_layout.addWidget(self.button_start)
        self.setLayout(main_layout)

        # Timer de actualización
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_ui)

        self.analyzer = None
        self.running = False

    def populate_devices(self):
        self.devices = sd.query_devices()
        input_devices = [(i, d['name']) for i, d in enumerate(self.devices) if d['max_input_channels'] > 0]
        for i, name in input_devices:
            self.device_selector.addItem(f"{name}", userData=i)

    def create_side_panel(self, initial_text, font):
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border: 2px solid #00ff99;
                border-radius: 10px;
                padding: 10px;
            }
            QLabel {
                color: #00ff99;
            }
        """)
        label = QLabel(initial_text)
        label.setFont(font)
        layout = QVBoxLayout()
        layout.addWidget(label)
        panel.setLayout(layout)
        return panel

    def start_analysis(self):
        device_index = self.device_selector.currentData()
        print(f"Usando dispositivo: {sd.query_devices(device_index)['name']} (index: {device_index})")

        # Si ya hay un stream en uso, lo detenemos
        if self.analyzer and self.running:
            try:
                self.analyzer.stop()
                self.running = False
            except Exception as e:
                print("Error al detener el stream anterior:", e)

        # Creamos nuevo analizador con el input seleccionado
        self.analyzer = AudioAnalyzer(device=device_index)
        self.analyzer.start()

        if not self.timer.isActive():
            self.timer.start(100)

        self.running = True

    def update_ui(self):
        if self.analyzer:
            data = self.analyzer.get_audio_data()
            self.label_volume.setText(f"Volumen: {data['volume']:.2f} dB")
            self.label_freq.setText(f"Freq: {data['dominant_freq']:.2f} Hz")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CyberUI()
    window.show()
    sys.exit(app.exec())
