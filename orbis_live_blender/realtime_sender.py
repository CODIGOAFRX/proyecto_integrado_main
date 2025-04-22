# realtime_sender.py
import socket
import time
from audio_analyzer import AudioAnalyzer
from exportador_csv import extraer_bandas  # asegúrate de que este está en el mismo path

HOST = 'localhost'
PORT = 65432

analyzer = AudioAnalyzer("tu_audio.wav")  # o sin parámetro para micrófono
sample_rate = analyzer.rate

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    while True:
        data = analyzer.get_frequency_data()
        bandas = extraer_bandas(data, sample_rate)
        mensaje = f"{bandas['Grave']:.3f},{bandas['Medio']:.3f},{bandas['Agudo']:.3f}"
        s.sendto(mensaje.encode(), (HOST, PORT))
        time.sleep(0.1)  # 10 veces por segundo
