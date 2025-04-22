# -*- coding: utf-8 -*-
# Añadimos los imports necesarios para la interfaz gráfica, el análisis de audio y JSON.
import json
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QSizePolicy,
    QComboBox, QGridLayout
)
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QFont, QPainter, QColor, QBrush
import sounddevice as sd
import sys
from audio_analyzer import AudioAnalyzer
import numpy as np
import os

# Ruta absoluta donde Blender leerá los datos JSON
# PACEHOLDER - CAMBIAR LA RUTA SEGÚN EL EQUIPO QUE LO EJECUTE 
JSON_PATH = r"E:\TFG 2025\proyecto_integrado_main\proyecto_integrado-main\proyecto Integrado\json\orbis_data.json"

# Clase que define el widget del orbe, que representa el volumen y la frecuencia dominante en forma de una elipse.
class OrbWidget(QWidget):
    def __init__(self):     # Constructor de la clase.
        super().__init__()
        self.volume = -20
        self.freq = 1000
        self.setMinimumSize(200, 200)

    def update_data(self, volume, freq):  # Este método actualiza los valores de volumen y frecuencia, y fuerza un repintado del widget.
        self.volume = volume
        self.freq = freq
        self.update()

    def paintEvent(self, event):  # Método que dibuja la elipse según volumen y frecuencia.
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor("#000000"))

        # El valor de 'scale' se ajusta en base al volumen para escalar el tamaño del orbe.
        scale = max(0.2, min(1.5, (self.volume + 60) / 40))
        # Este factor modifica la forma del orbe según la frecuencia dominante:
        # valores graves lo hacen más ancho y valores agudos más alto.
        shape_factor = max(0.5, min(1.5, (10000 - self.freq) / 9000))

        # Calculamos el ancho y alto del elipse basado en el scale y shape_factor
        w = self.width() * scale * shape_factor * 0.5
        h = self.height() * scale * (2 - shape_factor) * 0.5
        # Centra el orbe.
        x = (self.width() - w) / 2
        y = (self.height() - h) / 2

        # Dibujamos la elipse
        painter.setBrush(QBrush(QColor("#00ff99")))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(x, y, w, h)


# Clase que representa el widget del espectro de audio, que muestra las barras de frecuencia en forma de un gráfico de barras.
class SpectrumWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.fft_data = []  # Aquí se almacenan los datos de la FFT
        self.sample_rate = 44100  # Frecuencia de muestreo por defecto
        self.setMinimumSize(200, 200)  # Tamaño mínimo para el widget del espectro
        # Lista de frecuencias y etiquetas para el eje X
        self.freq_labels = [
            (20, "20"), (40, "40"), (60, "60"), (80, "80"), (125, "125"), (250, "250"),
            (500, "500"), (1000, "1k"), (2000, "2k"), (4000, "4k"), (6000, "6k"),
            (8000, "8k"), (10000, "10k"), (15000, "15k"), (20000, "20k")
        ]

    # Este método recibe los nuevos datos FFT y los agrupa en bandas logarítmicas para representarlos visualmente.
    def update_fft(self, fft):
        if fft is not None and len(fft) > 0:
            freqs = np.fft.rfftfreq(len(fft) * 2 - 1, 1 / self.sample_rate)
            num_bands = 64
            log_min = np.log10(20)
            log_max = np.log10(22050)
            band_edges = np.logspace(log_min, log_max, num_bands + 1)
            band_values = []
            for i in range(num_bands):
                indices = np.where((freqs >= band_edges[i]) & (freqs < band_edges[i + 1]))[0]
                band_values.append(np.mean(fft[indices]) if len(indices) > 0 else 0)
            self.fft_data = np.array(band_values)
        else:
            self.fft_data = []
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor("#000000"))

        # Evita el test ambiguo "if not self.fft_data"
        if self.fft_data is None or len(self.fft_data) == 0:
            return  # Si no hay datos, no dibujamos nada

        label_height = 20  # Altura reservada para etiquetas
        spectrum_height = self.height() - label_height
        max_value = float(np.max(self.fft_data)) if len(self.fft_data) > 0 else 1
        bar_width = self.width() / len(self.fft_data)

        # Dibujar cada barra del espectro
        for i, value in enumerate(self.fft_data):
            height = (value / max_value) * spectrum_height * 0.9
            x = i * bar_width
            y = spectrum_height - height
            painter.setBrush(QColor("#00ff99"))
            painter.setPen(Qt.NoPen)
            painter.drawRect(x, y, bar_width * 0.9, height)

        # Línea base y etiquetas de frecuencia
        painter.setPen(QColor("#00ff99"))
        painter.drawLine(0, spectrum_height, self.width(), spectrum_height)
        font = QFont("Consolas", 8)
        painter.setFont(font)
        for freq, label in self.freq_labels:
            x = int((np.log10(freq) - np.log10(20)) /
                    (np.log10(22050) - np.log10(20)) * self.width())
            painter.drawText(x - 10, self.height() - 5, label)


# Clase principal de la UI
class CyberUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cyber Audio Cockpit")
        self.setStyleSheet("background-color: #0d0d0d; color: #00ff99;")
        self.setMinimumSize(1000, 600)
        font_main = QFont("Consolas", 14)

        self.device_selector = QComboBox()
        self.device_selector.setStyleSheet("background-color: #1a1a1a; color: #00ff99; padding: 5px;")
        self.populate_devices()

        self.button_start = QPushButton("INICIAR ANÁLISIS")
        self.button_start.setStyleSheet("""
            QPushButton {
                background-color: #1a1a1a;
                color: #00ff99;
                border: 1px solid #00ff99;
                padding: 5px;
            }
        """)
        self.button_start.clicked.connect(self.start_analysis)

        self.label_db   = QLabel("dB: ---")
        self.label_db.setFont(font_main)
        self.label_lufs = QLabel("LUFS: ---")
        self.label_lufs.setFont(font_main)

        self.orb_widget      = OrbWidget()
        self.spectrum_widget = SpectrumWidget()

        grid = QGridLayout()
        grid.addWidget(QLabel("SELECTOR DE INPUTS"), 0, 0)
        grid.addWidget(self.device_selector, 1, 0)
        grid.addWidget(self.button_start, 1, 1)
        grid.addWidget(self.spectrum_widget, 2, 0)
        grid.addWidget(self.orb_widget, 2, 1)
        grid.addWidget(self.label_db,   3, 1, Qt.AlignLeft)
        grid.addWidget(self.label_lufs, 3, 1, Qt.AlignRight)
        self.setLayout(grid)

        self.analyzer = None
        self.timer    = QTimer()
        self.timer.timeout.connect(self.update_ui)

    def populate_devices(self):
        self.devices = sd.query_devices()
        input_devices = [(i, d['name']) for i, d in enumerate(self.devices) if d['max_input_channels'] > 0]
        for i, name in input_devices:
            self.device_selector.addItem(name, userData=i)

    def start_analysis(self):
        device_index = self.device_selector.currentData()
        if self.analyzer:
            try:
                self.analyzer.stop()
            except Exception as e:
                print("Error al detener el stream anterior:", e)
            finally:
                self.analyzer = None
        self.analyzer = AudioAnalyzer(device=device_index)
        self.analyzer.start()
        if not self.timer.isActive():
            self.timer.start(100)

    def export_to_json(self, volume, freq, fft):
        """Escribe volumen, frecuencia dominante y 13 bandas clave (en dB) en JSON."""
        try:
            freqs = np.fft.rfftfreq(len(fft) * 2 - 1, 1 / self.analyzer.sample_rate)
            fft = np.array(fft)
            target_freqs = [20, 50, 100, 250, 500, 1000, 2000, 5000, 6000, 7000, 12000, 15000, 20000]
            spectrum = {}

            for target in target_freqs:
                idx = (np.abs(freqs - target)).argmin()
                db = 20 * np.log10(max(fft[idx], 1e-10))
                spectrum[f"{target}Hz"] = round(db, 2)

            payload = {
                "volume": round(float(volume), 2),
                "dominant_freq": round(float(freq), 2),
                "spectrum": spectrum
            }

            carpeta = os.path.dirname(JSON_PATH)
            if not os.path.exists(carpeta):
                os.makedirs(carpeta, exist_ok=True)

            with open(JSON_PATH, "w") as f:
                json.dump(payload, f, indent=4)

        except Exception as e:
            print("Error exportando JSON:", e)


    def update_ui(self):
        if not self.analyzer:
            return
        data = self.analyzer.get_audio_data()
        vol  = data["volume"]
        freq = data["dominant_freq"]
        fft  = data["fft"]

        self.label_db.setText(f"dB: {vol:.1f}")
        self.label_lufs.setText(f"LUFS: {vol:.1f}")
        self.orb_widget.update_data(vol, freq)
        self.spectrum_widget.update_fft(fft)

        self.export_to_json(vol, freq, fft)



if __name__ == "__main__":
    # Verifica que se ejecute como script principal
    app = QApplication(sys.argv)
    window = CyberUI()
    window.show()
    sys.exit(app.exec())
