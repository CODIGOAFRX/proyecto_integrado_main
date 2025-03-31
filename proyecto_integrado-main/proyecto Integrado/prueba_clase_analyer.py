from audio_analyzer import AudioAnalyzer
import time

analyzer = AudioAnalyzer()
analyzer.start()

try:
    while True:
        data = analyzer.get_audio_data()
        print(f"Volumen (dB): {data['volume']:.2f} | Frecuencia dominante: {data['dominant_freq']:.2f} Hz")
        time.sleep(0.1)
except KeyboardInterrupt:
    print("Análisis detenido.")

