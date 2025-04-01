# -*- coding: utf-8 -*-
#Añadimos los imports necesarios para la interfaz gráfica y el análisis de audio.
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QFrame, QSizePolicy, QComboBox, QGridLayout
)
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QFont, QPainter, QColor, QBrush
import sounddevice as sd
import sys
from audio_analyzer import AudioAnalyzer
import numpy as np

#Clase que define el widget del orbe, que representa el volumen y la frecuencia dominante en forma de una elipse.
class OrbWidget(QWidget):
    def __init__(self):     #Constructor de la clase.
        super().__init__()
        self.volume = -20
        self.freq = 1000
        self.setMinimumSize(200, 200)

    def update_data(self, volume, freq): #Este método actualiza los valores de volumen y frecuencia, y fuerza un repintado del widget llamando a self.update().
        self.volume = volume
        self.freq = freq
        self.update()

    def paintEvent(self, event): #Este método actualiza los valores de volumen y frecuencia, y fuerza un repintado del widget llamando a self.update().
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor("#000000"))

        scale = max(0.2, min(1.5, (self.volume + 60) / 40)) #El valor de 'scale' se ajusta en base al volumen para escalar el tamaño del orbe. Se limita entre 0.2 y 1.5 para evitar deformaciones excesivas.
        shape_factor = max(0.5, min(1.5, (10000 - self.freq) / 9000)) #Este factor modifica la forma del orbe según la frecuencia dominante: valores graves lo hacen más ancho y valores agudos más alto.

        # Calculamos el ancho y alto del elipse basado en el scale y shape_factor
        w = self.width() * scale * shape_factor * 0.5
        h = self.height() * scale * (2 - shape_factor) * 0.5
        # Centra el orbe.
        x = (self.width() - w) / 2
        y = (self.height() - h) / 2
        #Dibujamos la elipse
        painter.setBrush(QBrush(QColor("#00ff99")))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(x, y, w, h)

#Clase que representa el widget del espectro de audio, que muestra las barras de frecuencia en forma de un gráfico de barras.
class SpectrumWidget(QWidget):
    # Constructor de la clase SpectrumWidget
    def __init__(self):
        super().__init__()
        self.fft_data = [] #Aquí se almacenan los datos de la transformada rápida de Fourier (FFT), que representan las magnitudes de cada frecuencia.
        self.sample_rate = 44100 # Frecuencia de muestreo por defecto
        self.setMinimumSize(200, 200) # Establecemos un tamaño mínimo para el widget del espectro
        #Lista de frecuencias (en Hz) y etiquetas de texto para mostrarlas debajo del gráfico de barras como referencia.
        self.freq_labels = [
            (20, "20"), (40, "40"), (60, "60"), (80, "80"), (125, "125"), (250, "250"),
            (500, "500"), (1000, "1k"), (2000, "2k"), (4000, "4k"), (6000, "6k"),
            (8000, "8k"), (10000, "10k"), (15000, "15k"), (20000, "20k")
        ]
    #Este método recibe los nuevos datos FFT y los agrupa en bandas logarítmicas para representarlos visualmente.
    def update_fft(self, fft):
        if fft is not None and len(fft) > 0:
            freqs = np.fft.rfftfreq(len(fft) * 2 - 1, 1 / self.sample_rate) #Calcula el vector de frecuencias correspondiente a cada punto del FFT. Se usa para asociar magnitudes a frecuencias reales.
            num_bands = 64
            log_min = np.log10(20)
            log_max = np.log10(22050)
            band_edges = np.logspace(log_min, log_max, num_bands + 1) #Genera los bordes de cada banda en escala logarítmica para una representación más precisa del espectro percibido por humanos.
            band_values = []
            #Para cada banda, se calcula el valor promedio de las frecuencias incluidas en ese rango.
            for i in range(num_bands):
                indices = np.where((freqs >= band_edges[i]) & (freqs < band_edges[i + 1]))[0]
                if len(indices) > 0:
                    band_values.append(np.mean(fft[indices]))
                else:
                    band_values.append(0)
            self.fft_data = np.array(band_values)
        else:
            self.fft_data = []
        self.update()

    def paintEvent(self, event):
        # Este método se llama automáticamente cuando el widget necesita redibujarse.
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)        # Mejora la suavidad de los gráficos (bordes redondeados)
        painter.fillRect(self.rect(), QColor("#000000"))    # Rellena el fondo con color negro

        if self.fft_data is None or len(self.fft_data) == 0:
            return      # Si no hay datos FFT, no dibujamos nada

        label_height = 20       # Espacio reservado en la parte inferior para las etiquetas
        spectrum_height = self.height() - label_height  # Altura del espectro, restando el espacio para las etiquetas

        max_value = float(np.max(self.fft_data)) if len(self.fft_data) > 0 else 1 #ESte es el valor máximo del espectro, se usa para escalar barraas proporcionalmente
        bar_width = self.width() / len(self.fft_data) # Ancho de cada barra en el espectro

        for i, value in enumerate(self.fft_data):
            height = (value / max_value) * spectrum_height * 0.9 #Altura de la barra actual
            x = i * bar_width #Posición horizontal de la barra
            y = spectrum_height - height #Posición vertical de la barra
            painter.setBrush(QColor("#00ff99")) # Color de la barra
            painter.setPen(Qt.NoPen) # Sin borde para las barras
            painter.drawRect(x, y, bar_width * 0.9, height) # Dibujamos la barra, dejando un pequeño margen

        painter.setPen(QColor("#00ff99"))
        painter.drawLine(0, spectrum_height, self.width(), spectrum_height)
        # Dibujamos la línea horizontal que separa el espectro de las etiquetas

        font = QFont("Consolas", 8) # Establecemos la fuente para las etiquetas de frecuencia
        painter.setFont(font)
        for freq, label in self.freq_labels:
            #calculamos la posiión de la etiqeta usando una escala logaritmica
            x = int((np.log10(freq) - np.log10(20)) / (np.log10(22050) - np.log10(20)) * self.width())
            painter.drawText(x - 10, self.height() - 5, label)

class CyberUI(QWidget):
    #Clase principal de la ui
    def __init__(self):
        super().__init__()
        #configuración ppal de la ventana
        self.setWindowTitle("Cyber Audio Cockpit")
        self.setStyleSheet("background-color: #0d0d0d; color: #00ff99;")
        self.setMinimumSize(1000, 600)
        font_main = QFont("Consolas", 14)

        # Desplegable para seleccionar el tipo de entrada
        self.device_selector = QComboBox()
        self.device_selector.setStyleSheet("background-color: #1a1a1a; color: #00ff99; padding: 5px;")
        self.populate_devices()

        #Botón para iniciar el analisis de audio
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

        # Etiquetas para mostrar volumen
        self.label_db = QLabel("dB: ---")
        self.label_db.setFont(font_main)
        self.label_lufs = QLabel("LUFS: ---")
        self.label_lufs.setFont(font_main)

        #etiquetas de ejes decorativas (mal puestas btw)
        self.label_x = QLabel("EJE X")
        self.label_y = QLabel("EJE Y")
        self.label_x.setAlignment(Qt.AlignCenter)
        self.label_y.setAlignment(Qt.AlignCenter)

        #Wigests para el orbe y el espectro
        self.orb_widget = OrbWidget()
        self.spectrum_widget = SpectrumWidget()

        #Layout principal con rejilla (QGridLayout)
        grid = QGridLayout()
        grid.addWidget(QLabel("SELECTOR DE INPUTS"), 0, 0)
        grid.addWidget(self.device_selector, 1, 0)
        grid.addWidget(self.button_start, 1, 1)
        grid.addWidget(self.spectrum_widget, 2, 0)
        grid.addWidget(self.orb_widget, 2, 1)
        grid.addWidget(self.label_db, 3, 1, Qt.AlignLeft)
        grid.addWidget(self.label_lufs, 3, 1, Qt.AlignRight)
        grid.addWidget(self.label_x, 4, 0)
        grid.addWidget(self.label_y, 4, 1)

        self.setLayout(grid)

        #Configuración del sistema de analisis
        self.analyzer = None
        self.running = False

        #Temporizador para actualizar la UI cada 100ms
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_ui)

    def populate_devices(self):
        # Este método llena el ComboBox con todos los dispositivos de entrada de audio disponibles
        self.devices = sd.query_devices() # Consulta todos los dispositivos disponibles
        input_devices = [(i, d['name']) for i, d in enumerate(self.devices) if d['max_input_channels'] > 0]
        # Filtra solo los dispositivos que pueden captar audio
        for i, name in input_devices:
            self.device_selector.addItem(f"{name}", userData=i) # Añade el nombre y guarda su índice como dato asociado

    def start_analysis(self):
        # Obtiene el índice del dispositivo seleccionado en el ComboBox
        device_index = self.device_selector.currentData()
        print(f"Usando dispositivo: {sd.query_devices(device_index)['name']} (index: {device_index})")

        if self.analyzer:   # Si ya hay un analizador en uso
            try:
                self.analyzer.stop() # Detenemos el analizador actual
            except Exception as e:
                print("Error al detener el stream anterior:", e)
            finally:
                self.analyzer = None
                self.running = False
        # Creamos un nuevo analizador de audio 
        self.analyzer = AudioAnalyzer(device=device_index)
        self.analyzer.start()

        #Activamos el temporizador si aún no estaba funcionando
        if not self.timer.isActive():
            self.timer.start(100)

        self.running = True

    def update_ui(self):
        # Este método se llama periódicamente para actualizar la UI con los datos del analizador
        if self.analyzer:
            data = self.analyzer.get_audio_data()   # Obtenemos los datos de audio del analizador
            vol = data["volume"]
            freq = data["dominant_freq"]
            self.label_db.setText(f"dB: {vol:.1f}") # Actualiza la etiqueta de volumen en dB
            self.label_lufs.setText(f"LUFS: {vol:.1f}") # Actualiza la etiqueta de LUFS (usando el mismo valor de volumen para simplificar por ahora)
            self.orb_widget.update_data(vol, freq)  # Actualiza el widget del orbe con el nuevo volumen y frecuencia
            self.spectrum_widget.update_fft(data["fft"])    # Actualiza el widget del espectro con los nuevos datos FFT

if __name__ == "__main__":
    # Verifica que se esté ejecutando como script principal
    app = QApplication(sys.argv)
    window = CyberUI()
    window.show()
    sys.exit(app.exec())