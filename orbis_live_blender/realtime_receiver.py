# realtime_receiver.py (Blender)
import bpy
import socket
import threading

HOST = 'localhost'
PORT = 65432

# Deformación en Geometry Nodes (mejor opción a largo plazo),
# pero aquí aplicamos en escala como ejemplo simple
def aplicar_deformacion(obj, grave, medio, agudo):
    s = 1 + grave*2  # eje X
    m = 1 + medio*2  # eje Y
    a = 1 + agudo*2  # eje Z
    obj.scale = (s, m, a)

def receptor():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind((HOST, PORT))
        while True:
            data, _ = s.recvfrom(1024)
            grave, medio, agudo = map(float, data.decode().split(","))
            bpy.app.timers.register(lambda: aplicar_deformacion(bpy.data.objects["Icosphere"], grave, medio, agudo), first_interval=0.0)

# Lanza el receptor como hilo
threading.Thread(target=receptor, daemon=True).start()
