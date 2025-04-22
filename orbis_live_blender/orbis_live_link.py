bl_info = {
    "name":        "Orbis Live Link - Alpha Build",
    "author":      "Orbis Team",
    "version":     (1, 1, 0),
    "blender":     (3, 6, 0),
    "location":    "View3D > Sidebar > Orbis",
    "description": "Lee datos JSON desde tu app Qt/Python y actualiza Geometry Nodes en tiempo real, con panel de estado",
    "category":    "Object",
}

import bpy
import json
import os
import time

# Ruta al JSON generado por tu GUI Qt/Python
JSON_PATH = r"E:\TFG 2025\proyecto_integrado_main-main\proyecto_integrado-main\proyecto Integrado\json\orbis_data.json"

# Nombres en tu escena Blender: ajusta si los has llamado distinto
OBJECT_NAME   = "Icosphere"
MODIFIER_NAME = "GeometryNodes"
INPUT_VOL     = "Volume"
INPUT_FREQ    = "DominantFreq"

# Datos leídos más recientemente
last_data = {
    "volume": 0.0,
    "dominant_freq": 0.0,
    "timestamp": 0.0,
}

def poll_json():
    """
    Función llamada periódicamente por bpy.app.timers.
    Lee el JSON y vuelca los valores en los inputs de Geometry Nodes.
    También almacena los datos en last_data para mostrarlos en el panel.
    """
    try:
        # Si el fichero no existe aún, agendar siguiente llamada
        if not os.path.exists(JSON_PATH):
            return 0.1

        with open(JSON_PATH, "r") as f:
            data = json.load(f)

        # Actualizar último timestamp y datos
        last_data["volume"]       = float(data.get("volume", 0.0))
        last_data["dominant_freq"]= float(data.get("dominant_freq", 0.0))
        last_data["timestamp"]    = time.time()

        # Busca el objeto y su modifier
        obj = bpy.data.objects.get(OBJECT_NAME)
        if obj is None:
            print(f"[Orbis] Objeto '{OBJECT_NAME}' no existe.")
            return 0.5

        mod = obj.modifiers.get(MODIFIER_NAME)
        if mod is None or not hasattr(mod, "node_group"):
            print(f"[Orbis] Modifier '{MODIFIER_NAME}' no encontrado o no es GeometryNodes.")
            return 0.5

        ng = mod.node_group

        # Asigna los valores a los inputs del grupo
        if INPUT_VOL in ng.inputs:
            ng.inputs[INPUT_VOL].default_value = last_data["volume"]
        if INPUT_FREQ in ng.inputs:
            ng.inputs[INPUT_FREQ].default_value = last_data["dominant_freq"]

    except Exception as e:
        print("[Orbis] Error leyendo JSON:", e)

    # Repite tras 0.1 segundos
    return 0.1

class ORBIS_OT_refresh(bpy.types.Operator):
    """Forzar lectura de JSON ahora mismo"""
    bl_idname = "orbis.refresh"
    bl_label  = "Refrescar Orbis"

    def execute(self, context):
        # Llamada manual a poll_json (ignora su return)
        poll_json()
        self.report({'INFO'}, "Orbis: datos actualizados")
        return {'FINISHED'}


class ORBIS_PT_sidebar(bpy.types.Panel):
    """Panel lateral para mostrar estado de Orbis Live Link"""
    bl_label      = "Orbis Live Link"
    bl_idname     = "ORBIS_PT_sidebar"
    bl_space_type = 'VIEW_3D'
    bl_region_type= 'UI'
    bl_category   = 'Orbis'

    def draw(self, context):
        layout = self.layout

        # Información de la ruta
        col = layout.column()
        col.label(text="JSON path:")
        col.label(text=os.path.basename(JSON_PATH), icon='FILE')

        # Estado de conexión
        connected = last_data["timestamp"] > 0 and os.path.exists(JSON_PATH)
        row = layout.row()
        row.label(text="Conectado:" if connected else "Sin datos", 
                  icon='CHECKMARK' if connected else 'ERROR')

        # Mostrar últimos valores
        row = layout.row()
        row.label(text=f"dB: {last_data['volume']:.1f}")
        row = layout.row()
        row.label(text=f"Freq: {last_data['dominant_freq']:.1f} Hz")

        # Mostrar hora de la última actualización
        if last_data["timestamp"] > 0:
            t = time.localtime(last_data["timestamp"])
            layout.label(text="Última lectura: " + time.strftime("%H:%M:%S", t))

        # Botón para forzar refresco
        layout.operator("orbis.refresh", icon='FILE_REFRESH')


classes = (
    ORBIS_OT_refresh,
    ORBIS_PT_sidebar,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.app.timers.register(poll_json)
    print("[Orbis] Add-on registrado y timer iniciado.")

def unregister():
    try:
        bpy.app.timers.unregister(poll_json)
    except Exception:
        pass
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    print("[Orbis] Add-on desregistrado y timer detenido.")
