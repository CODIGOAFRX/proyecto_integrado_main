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
JSON_PATH = bpy.path.abspath("//json/orbis_data.json")
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

last_data = {
    "volume": 0.0,
    "dominant_freq": 0.0,
    "timestamp": 0.0,
    "spectrum": {}
}

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

        if INPUT_VOL in ng.inputs:
            ng.inputs[INPUT_VOL].default_value = last_data["volume"]
        if INPUT_FREQ in ng.inputs:
            ng.inputs[INPUT_FREQ].default_value = last_data["dominant_freq"]
        for band, input_name in SPECTRUM_BANDS.items():
            if input_name in ng.inputs and band in last_data["spectrum"]:
                ng.inputs[input_name].default_value = last_data["spectrum"][band]

    except Exception as e:
        print("[Orbis] Error aplicando datos:", e)

def refresh_loop():
    global _orbis_thread_running
    _orbis_thread_running = True
    while _orbis_thread_running:
        if refresh_active:
            try:
                if os.path.exists(JSON_PATH):
                    with open(JSON_PATH, "r") as f:
                        data = json.load(f)

                    last_data["volume"] = float(data.get("volume", 0.0))
                    last_data["dominant_freq"] = float(data.get("dominant_freq", 0.0))
                    last_data["spectrum"] = data.get("spectrum", {})
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
