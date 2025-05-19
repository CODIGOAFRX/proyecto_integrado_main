import bpy
import json
import os
import time
import threading

bl_info = {
    "name":        "Orbis Live Link - Threaded",
    "author":      "Orbis Team",
    "version":     (1, 4, 0),
    "blender":     (3, 6, 0),
    "location":    "View3D > Sidebar > Orbis",
    "description": "Actualiza Geometry Nodes en segundo plano desde JSON con control de pausa",
    "category":    "Object",
}

# JSON path y nodos
JSON_PATH = r"C:\Users\USUARIO\Desktop\proyecto_integrado\proyecto_integrado-main\proyecto Integrado\json\orbis_data.json"
OBJECT_NAME = "Icosphere"
MODIFIER_NAME = "GeometryNodes"
INPUT_VOL = "Volume"
INPUT_FREQ = "DominantFreq"


SPECTRUM_BANDS = {
    "20Hz": "Band_20Hz",
    "50Hz": "Band_50Hz",
    "100Hz": "Band_100Hz",
    "250Hz": "Band_250Hz",
    "500Hz": "Band_500Hz",
    "1000Hz": "Band_1kHz",
    "2000Hz": "Band_2kHz",
    "5000Hz": "Band_5kHz",
    "6000Hz": "Band_6kHz",
    "10000Hz": "Band_10kHz",
    "15000Hz": "Band_15kHz",
    "20000Hz": "Band_20kHz"
}

# --- Agrupaciones de octavas ---------------------------------------------
LOW_BANDS =  ["20Hz","50Hz","100Hz"]         
MID_BANDS =  ["250Hz","500Hz","1000Hz","2000Hz"]              
HI_BANDS  =  ["5000Hz","6000Hz","10000Hz","15000Hz","20000Hz"]

# Señales que llegarán a los sockets de Geometry Nodes
INPUT_BAL_LH  = "SpectralBalance_LH"   # grave ↔ agudo  (‑1 a +1)
INPUT_BAL_MID = "SpectralBalance_MID"  # peso de medios (‑1 a +1)

last_data = {
    "volume": 0.0,
    "dominant_freq": 0.0,
    "bal_lh": 0.0,
    "bal_mid": 0.0,
    "dev_low": 0.0,
    "dev_lowmid": 0.0,
    "dev_mid": 0.0,
    "dev_himid": 0.0,
    "dev_high": 0.0,
    "spectrum": {},
    "timestamp": 0.0,
}

# --- 1 · Valores de referencia pop (dBFS) -----------------------------
REF_DB = {
    "LOW"      : -18,      # 20‑120 Hz
    "LOWMID"   : -16.5,    # 120‑500 Hz
    "MID"      : -13.5,    # 500‑2 kHz
    "HIMID"    : -11,      # 2‑6 kHz
    "HIGH"     : -11.5     # 6‑20 kHz
}
TOLERANCE = 3             # rango que consideramos “ok” (±3 dB)

# --- 2 · Distribución de tus 12 bandas en 5 zonas ---------------------
ZONE_MAP = {
    "LOW"   : ["20Hz", "50Hz", "100Hz"],
    "LOWMID": ["250Hz"],
    "MID"   : ["500Hz", "1000Hz"],
    "HIMID" : ["2000Hz", "5000Hz"],
    "HIGH"  : ["6000Hz", "10000Hz", "15000Hz", "20000Hz"]
}
DEV_SOCKETS = {
    "LOW"   : "Dev_LOW",
    "LOWMID": "Dev_LOWMID",
    "MID"   : "Dev_MID",
    "HIMID" : "Dev_HIMID",
    "HIGH"  : "Dev_HIGH",
}
# --- 3 · Devuelve desviación normalizada (‑1→falta , 0→bien , +1→sobra)
def compute_deviation(db_list, ref):
    if not db_list: 
        return 0
    avg = sum(db_list) / len(db_list)
    delta = avg - ref     # + si sobra (“demasiado fuerte”)
    # normalizamos al rango (‑1 .. 1) usando la tolerancia
    return max(-1, min(1, delta / TOLERANCE))

def calc_zone_deltas(spec_dict):
    deltas = {}
    for zone, bands in ZONE_MAP.items():
        values = [spec_dict.get(b, -60) for b in bands]  # -60 dB si no viene
        deltas[zone] = compute_deviation(values, REF_DB[zone])
    return deltas

refresh_active = True
_orbis_thread_running = False

def update_geometry_nodes():
    try:
        obj = bpy.data.objects.get(OBJECT_NAME)
        if obj is None:
            return

        mod = obj.modifiers.get(MODIFIER_NAME)
        if mod is None or not hasattr(mod, "node_group"):
            return

        ng = mod.node_group
        mod["Freq"] = 440.0
        # --- Valores “clásicos” ---------------------------------------
        if INPUT_VOL in ng.inputs:
            ng.inputs[INPUT_VOL].default_value = last_data.get("volume", 0.0)

        if INPUT_FREQ in mod:
            mod[INPUT_FREQ] = last_data.get("dominant_freq", 0.0)

        for band, socket_name in SPECTRUM_BANDS.items():
            if socket_name in ng.inputs:
                ng.inputs[socket_name].default_value = last_data["spectrum"].get(band, 0.0)

        # --- Balance graves/ agudos -----------------------------------
        if INPUT_BAL_LH in ng.inputs:
            ng.inputs[INPUT_BAL_LH].default_value = last_data.get("bal_lh", 0.0)

        # --- Peso (desviación) de los medios --------------------------
        if INPUT_BAL_MID in ng.inputs:
            ng.inputs[INPUT_BAL_MID].default_value = last_data.get("bal_mid", 0.0)

        # --- Desviaciones por zona ------------------------------------
        zone_dev = last_data.get("zone_dev", {})   # dict {'LOW':‑0.2 …}
        for zone_key, socket_name in DEV_SOCKETS.items():
            if socket_name in ng.inputs:
                ng.inputs[socket_name].default_value = zone_dev.get(zone_key, 0.0)
        
        # Balance grave‑agudo y mids (ya lo tienes)
        if INPUT_BAL_LH in ng.inputs:
            ng.inputs[INPUT_BAL_LH].default_value = last_data["bal_lh"]
        if INPUT_BAL_MID in ng.inputs:
            ng.inputs[INPUT_BAL_MID].default_value = last_data["bal_mid"]

        # Desviaciones por banda
        for key, socket_name in DEV_SOCKETS.items():
            if socket_name in ng.inputs:
                ng.inputs[socket_name].default_value = last_data[f"dev_{key.lower()}"]
    except Exception as e:
        print("[Orbis] Error aplicando datos:", e)


    except Exception as e:
        print("[Orbis] Error aplicando datos:", e)

def refresh_loop():
    global _orbis_thread_running
    _orbis_thread_running = True
    while _orbis_thread_running:
        if refresh_active:
            try:
                if os.path.exists(JSON_PATH):
                    #print(f"[Orbis] JSON leído correctamente: {JSON_PATH}")
                    with open(JSON_PATH, "r") as f:
                        data = json.load(f)
                    last_data["bal_lh"]      = float(data.get("bal_lh", 0.0))
                    last_data["bal_mid"]     = float(data.get("bal_mid", 0.0))
                    last_data["dev_low"]     = float(data.get("dev_low", 0.0))
                    last_data["dev_lowmid"]  = float(data.get("dev_lowmid", 0.0))
                    last_data["dev_mid"]     = float(data.get("dev_mid", 0.0))
                    last_data["dev_himid"]   = float(data.get("dev_himid", 0.0))
                    last_data["dev_high"]    = float(data.get("dev_high", 0.0))
                    last_data["volume"] = float(data.get("volume", 0.0))
                    last_data["dominant_freq"] = float(data.get("dominant_freq") or data.get("dominant-freq") or 0.0)
                    last_data["spectrum"] = data.get("spectrum", {})
                    zone = calc_zone_deltas(last_data["spectrum"])
                    last_data["zone_dev"] = zone     # {'LOW':‑0.3, 'MID':+0.8…}

                    

                    # ------------------------------------------------------------------
                    # Cálculo de los pesos espectrales
                    # ------------------------------------------------------------------
                    # 1 · Helper para pasar de dB → lineal
                    def db_to_amp(db):
                        """Devuelve amplitud lineal a partir de dBFS."""
                        return 10 ** (db / 20.0)

                    # 2 · Suma en lineal (amplitud) y calcula balances normalizados
                    low_amp  = sum(db_to_amp(last_data["spectrum"].get(b, -120)) for b in LOW_BANDS)
                    mid_amp  = sum(db_to_amp(last_data["spectrum"].get(b, -120)) for b in MID_BANDS)
                    high_amp = sum(db_to_amp(last_data["spectrum"].get(b, -120)) for b in HI_BANDS)

                    total = max(low_amp + mid_amp + high_amp, 1e-6)  # evita división 0

                    # −1 (dominan graves) … 0 … +1 (dominan agudos)
                    last_data["bal_lh"] = (high_amp - low_amp) / total

                    # −1 (pocos medios) … 0 … +1 (sobran medios)
                    last_data["bal_mid"] = (mid_amp - 0.5 * (low_amp + high_amp)) / total
                    # ------------------------------------------------------------------

                    last_data["timestamp"] = time.time()

                    bpy.app.timers.register(update_geometry_nodes, first_interval=0.0)

                    # Forzar refresco visual del panel
                    for window in bpy.context.window_manager.windows:
                        for area in window.screen.areas:
                            if area.type == 'VIEW_3D':
                                area.tag_redraw()

            except Exception as e:
                print("[Orbis] Error en hilo:", e)

        time.sleep(0.1)

def stop_thread():
    global _orbis_thread_running
    _orbis_thread_running = False

class ORBIS_OT_toggle_pause(bpy.types.Operator): 
    bl_idname = "orbis.toggle_pause"
    bl_label = "⏯️ Pausar/Continuar"

    def execute(self, context):
        global refresh_active
        refresh_active = not refresh_active
        estado = "Reanudado" if refresh_active else "Pausado"
        self.report({'INFO'}, f"Orbis: {estado}")
        return {'FINISHED'}

class ORBIS_PT_sidebar(bpy.types.Panel):
    bl_label = "Orbis Live Link"
    bl_idname = "ORBIS_PT_sidebar"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Orbis'

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.label(text="JSON path:")
        col.label(text=os.path.basename(JSON_PATH), icon='FILE')

        connected = last_data["timestamp"] > 0 and os.path.exists(JSON_PATH)
        col.label(text="Conectado:" if connected else "Sin datos", 
                  icon='CHECKMARK' if connected else 'ERROR')

        col.label(text=f"dB: {last_data['volume']:.1f}")
        col.label(text=f"Freq: {last_data['dominant_freq']:.1f} Hz")
        col.label(text=f"Bal LH:  {last_data['bal_lh']:+.2f}")
        col.label(text=f"Bal MID: {last_data['bal_mid']:+.2f}")

        if last_data["timestamp"] > 0:
            t = time.localtime(last_data["timestamp"])
            col.label(text="Última lectura: " + time.strftime("%H:%M:%S", t))
    
        col.separator()
        col.label(text="Bandas de Espectro (dB):", icon='SOUND')
        for band, value in last_data["spectrum"].items():
            col.label(text=f"{band}: {value:.1f} dB")

        col.separator()
        icon = 'PAUSE' if refresh_active else 'PLAY'
        col.operator("orbis.toggle_pause", icon=icon)

classes = (
    ORBIS_OT_toggle_pause,
    ORBIS_PT_sidebar,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # Inicia hilo en segundo plano
    thread = threading.Thread(target=refresh_loop, daemon=True)
    thread.start()

    print("[Orbis] Add-on registrado con hilo activo.")

def unregister():
    stop_thread()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    print("[Orbis] Add-on desregistrado y hilo detenido.")
