import sounddevice as sd
sd.default.device = ("Stereo Mix", None)

devices = sd.query_devices()
for i, d in enumerate(devices):
    if "Stereo Mix" in d['name']:
        print(f"Usando dispositivo: {d['name']} (index: {i})")
        sd.default.device = i
        break

