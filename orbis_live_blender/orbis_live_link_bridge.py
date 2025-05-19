# orbis_live_link_bridge.py
import bpy, json, pathlib

JSON_PATH = r"C:\Users\USUARIO\Desktop\proyecto_integrado\proyecto_integrado-main\proyecto Integrado\json\orbis_data.json"


OBJ_NAME  = "Icosphere.004"
MOD_NAME  = "OrbisGeoNodes"      # nombre exacto del modificador GN

# Empareja nombre de campo JSON -> nombre de socket expuesto en el modificador
MAP = {
    "dB":          "Volume",
    "Freq":        "Freq",
    "Band_20Hz":   "Band_20Hz",
    "Band_50Hz":   "Band_50Hz",
    # …añade las que necesites
}

def orbis_update(scene):
    try:
        data = json.loads(JSON_PATH.read_text())
    except Exception as e:
        print("OR-BIS: no pude leer JSON:", e)
        return

    mod = bpy.data.objects[OBJ_NAME].modifiers[MOD_NAME]
    for key, socket in MAP.items():
        if key in data:
            mod[socket] = data[key]

# limpia duplicados y registra
h = bpy.app.handlers.frame_change_pre
h[:] = [f for f in h if f.__name__ != "orbis_update"]
h.append(orbis_update)
print("OR-BIS bridge listo 🚀")
