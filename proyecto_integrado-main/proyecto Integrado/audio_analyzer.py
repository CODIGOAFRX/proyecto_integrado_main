#Librerías necesarias.
import numpy as np
import sounddevice as sd
import threading

#Establecemos la entrada de audio como la salida del pc
sd.default.device = ("Stereo Mix", None)  # entrada, salida
devices = sd.query_devices()
for i, d in enumerate(devices):
    if "Stereo Mix" in d['name']:
        print(f"Usando dispositivo: {d['name']} (index: {i})")
        sd.default.device = i
        break

#Creamos las clase encargada de analizar el audio.
class AudioAnalyzer:
    def __init__(self, sample_rate=44100, chunk_size=8192, device=None): #sample rate es la frecuencia de muestreo y chunk_size es el tamaño del bloque de audio.
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.device = device 
        

        self.volume = 0.0
        self.dominant_freq = 0.0
        self.fft_data = []

        self._stream = sd.InputStream(callback=self._callback,
                              channels=1,
                              samplerate=self.sample_rate,
                              blocksize=self.chunk_size,
                              device=self.device)

        self._thread = threading.Thread(target=self._stream.start)
        self._thread.daemon = True

    def _callback(self, indata, frames, time, status):
        signal = indata[:, 0]
        
        # Volumen en dB
        rms = np.sqrt(np.mean(signal**2))
        self.volume = 20 * np.log10(max(rms, 1e-10))
        
        # Aplicar ventana de Hanning
        window = np.hanning(len(signal))
        windowed_signal = signal * window
        
        # FFT
        fft = np.abs(np.fft.rfft(windowed_signal))
        self.fft_data = fft
        
        # Interpolación parabólica para mejor precisión del pico
        peak_bin = np.argmax(fft)
        
        if 1 <= peak_bin < len(fft) - 1:
            alpha = fft[peak_bin - 1]
            beta = fft[peak_bin]
            gamma = fft[peak_bin + 1]
        
            p = 0.5 * (alpha - gamma) / (alpha - 2 * beta + gamma)
            peak_bin += p  # desplazamiento fraccional del pico
        
        # Cálculo de frecuencia dominante
        self.dominant_freq = peak_bin * self.sample_rate / self.chunk_size
        
    def start(self):
        self._thread.start()

    def stop(self):
        try:
            self._stream.stop()
            self._stream.close()
        except Exception as e:
            print("Error al detener el stream:", e)

    def get_audio_data(self):
        return{
            "volume":self.volume,
            "dominant_freq":self.dominant_freq,
            "fft":self.fft_data
        }