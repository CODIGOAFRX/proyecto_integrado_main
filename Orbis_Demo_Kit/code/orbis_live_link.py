bl_info = {
    "name":        "Orbis Live Link – Enhanced",
    "author":      "Orbis Team",
    "version":     (1, 2, 0),
    "blender":     (3, 6, 0),
    "location":    "View3D > Sidebar > Orbis",
    "description": "Lectura de JSON / WAV, setup automático de Geometry Nodes y estadísticas de malla",
    "category":    "Object",
}

import bpy, os, json, time, wave, struct
import numpy as np
from bpy.props import (
    StringProperty, PointerProperty, BoolProperty, EnumProperty
)
from bpy.types import (
    Panel, Operator, PropertyGroup, AddonPreferences
)

# --------------------------------------------------------------
#   PROPERTIES
# --------------------------------------------------------------

class ORBIS_Props(PropertyGroup):
    json_path: StringProperty(
        name="JSON Path",
        description="Ruta al archivo JSON de Orbis (override)",
        subtype='FILE_PATH',
        default=""
    )
    target_obj: PointerProperty(
        name="Target Mesh",
        description="Objeto al que aplicar deformación",
        type=bpy.types.Object
    )
    auto_setup: BoolProperty(
        name="Auto‑setup GN",
        description="Genera nodo de deformación si no existe",
        default=False
    )
    wav_path: StringProperty(
        name="Load WAV",
        description="Archivo de audio .wav para análisis interno",
        subtype='FILE_PATH',
        default=""
    )
    last_log: StringProperty(
        name="Log",
        description="Último mensaje de acción",
        default=""
    )

# --------------------------------------------------------------
#   GLOBAL STATE
# --------------------------------------------------------------

last_data = {"volume":0.0, "dominant_freq":0.0, "timestamp":0.0}

# --------------------------------------------------------------
#   TIMERS & JSON POLLING
# --------------------------------------------------------------

def poll_json():
    props = bpy.context.scene.orbis_props
    path = props.json_path or os.path.abspath(
        os.path.join(os.path.dirname(bpy.data.filepath),"json/orbis_data.json")
    )
    if not os.path.isfile(path):
        last_data["timestamp"] = 0.0
        return 0.5
    try:
        with open(path) as f:
            d = json.load(f)
        last_data["volume"] = float(d.get("volume",0.0))
        last_data["dominant_freq"] = float(d.get("dominant_freq",0.0))
        last_data["timestamp"] = time.time()
        props.last_log = f"JSON OK: {os.path.basename(path)}"
    except Exception as e:
        props.last_log = f"JSON Error: {e}"
    apply_to_geometry()
    return 0.1

# --------------------------------------------------------------
#   GEOMETRY NODES SETUP
# --------------------------------------------------------------

def setup_geometry_nodes(obj):
    """Crea un modifier Geometry Nodes con un setup básico de ruido+volumen."""
    ng_name = f"{obj.name}_OrbisGN"
    # 1) Crear node_group
    node_group = bpy.data.node_groups.new(ng_name, 'GeometryNodeTree')
    # 2) Group inputs / outputs
    gi = node_group.nodes.new('NodeGroupInput')
    go = node_group.nodes.new('NodeGroupOutput')
    node_group.inputs.new('NodeSocketGeometry','Geometry')
    node_group.inputs.new('NodeSocketFloat','Volume')
    node_group.inputs.new('NodeSocketFloat','DominantFreq')
    node_group.outputs.new('NodeSocketGeometry','Geometry')
    # 3) Posición original
    pos = node_group.nodes.new('GeometryNodeInputPosition')
    # 4) Normal
    nor = node_group.nodes.new('GeometryNodeInputNormal')
    # 5) Noise Texture
    noise = node_group.nodes.new('ShaderNodeTexNoise')
    # 6) Map Range para freq → scale
    mr = node_group.nodes.new('FunctionNodeMapRange')
    mr.inputs[1].default_value = 0   # From Min
    mr.inputs[2].default_value = 20000 # From Max
    mr.inputs[3].default_value = 1   # To Min
    mr.inputs[4].default_value = 10  # To Max
    # 7) Multiply normal × Volume
    mul = node_group.nodes.new('ShaderNodeVectorMath'); mul.operation='MULTIPLY'
    # 8) Add (pos + desplazamiento)
    add = node_group.nodes.new('ShaderNodeVectorMath'); add.operation='ADD'
    # 9) Set Position
    sp = node_group.nodes.new('GeometryNodeSetPosition')
    # 10) Transform
    tr = node_group.nodes.new('GeometryNodeTransform')
    # Conexiones:
    links = node_group.links
    # Geometry chain
    links.new(gi.outputs['Geometry'], sp.inputs['Geometry'])
    links.new(sp.outputs['Geometry'], tr.inputs['Geometry'])
    links.new(tr.outputs['Geometry'], go.inputs['Geometry'])
    # Position + normal chain
    links.new(gi.outputs['Geometry'], gi.outputs['Geometry'])
    links.new(gi.outputs['Volume'], mul.inputs[1])
    links.new(nor.outputs['Normal'], mul.inputs[0])
    links.new(mul.outputs['Vector'], add.inputs[1])
    links.new(pos.outputs['Position'], add.inputs[0])
    links.new(add.outputs['Vector'], sp.inputs['Offset'])
    # Noise scale by freq
    links.new(gi.outputs['DominantFreq'], mr.inputs['Value'])
    links.new(mr.outputs['Result'], noise.inputs['Scale'])
    # Noise outputs control deformation
    links.new(noise.outputs['Fac'], mul.inputs[1])  # replace volume for noise*normal?
    # Transform Z scale by freq
    # Combine XYZ
    cb = node_group.nodes.new('ShaderNodeCombineXYZ')
    cb.inputs['X'].default_value = 1
    cb.inputs['Y'].default_value = 1
    links.new(mr.outputs['Result'], cb.inputs['Z'])
    links.new(cb.outputs['Vector'], tr.inputs['Scale'])
    # Exponer inputs
    gi.location = (-600,0)
    go.location = (400,0)
    for n in (pos,nor,noise,mr,mul,add,sp,tr,cb):
        n.location.x += -200
    return node_group

# --------------------------------------------------------------
#   APPLY DEFORM
# --------------------------------------------------------------

def apply_to_geometry():
    props = bpy.context.scene.orbis_props
    obj = props.target_obj
    if not obj or obj.type!='MESH':
        return
    # Asegura modifier Geometry Nodes
    mod = obj.modifiers.get("OrbisGN")
    if not mod:
        # intenta buscar otro GN
        for m in obj.modifiers:
            if m.type=='NODES':
                mod=m; break
    if not mod and props.auto_setup:
        node_group = setup_geometry_nodes(obj)
        mod = obj.modifiers.new("OrbisGN","NODES")
        mod.node_group = node_group
        props.last_log = f"GN creado para {obj.name}"
    if not mod or not mod.node_group:
        return
    ng = mod.node_group
    # Asigna valores a los inputs del group
    try:
        ng.inputs['Volume'].default_value = last_data['volume']
        ng.inputs['DominantFreq'].default_value = last_data['dominant_freq']
    except:
        pass

# --------------------------------------------------------------
#   OPERATORS
# --------------------------------------------------------------

class ORBIS_OT_setup(Operator):
    bl_idname = "orbis.setup_gn"
    bl_label  = "Setup Geometry Nodes"
    bl_description = "Genera o actualiza el node_tree de Orbis en el objeto seleccionado"
    def execute(self,context):
        props = context.scene.orbis_props
        obj = props.target_obj
        if not obj or obj.type!='MESH':
            self.report({'ERROR'},"Selecciona antes un mesh")
            return {'CANCELLED'}
        setup_geometry_nodes(obj)
        self.report({'INFO'},f"GN creado en {obj.name}")
        return {'FINISHED'}

class ORBIS_OT_load_wav(Operator):
    bl_idname = "orbis.load_wav"
    bl_label  = "Analizar WAV"
    bl_description = "Carga el WAV y calcula volumen y freq dominante"
    def execute(self,context):
        props = context.scene.orbis_props
        path = bpy.path.abspath(props.wav_path)
        if not os.path.isfile(path):
            self.report({'ERROR'},"Archivo WAV no encontrado")
            return {'CANCELLED'}
        try:
            w = wave.open(path,'rb')
            nchan = w.getnchannels()
            fr = w.getframerate()
            nframes = w.getnframes()
            data = w.readframes(nframes)
            w.close()
            # convierto a ints
            fmt = {1:'b',2:'h',4:'i'}[w.getsampwidth()]
            samples = np.array(struct.unpack("<"+fmt*nframes*nchan,data))
            samples = samples.reshape(-1,nchan).mean(axis=1)
            # RMS y FFT
            rms = np.sqrt(np.mean(samples**2))
            volume = 20*np.log10(max(rms,1e-10))
            fft = np.abs(np.fft.rfft(samples))
            peak = np.argmax(fft)
            dom = peak*fr/len(samples)
            # guarda en last_data y aplica
            last_data['volume']=volume
            last_data['dominant_freq']=dom
            last_data['timestamp']=time.time()
            props.last_log = f"WAV OK: {os.path.basename(path)}"
            apply_to_geometry()
        except Exception as e:
            props.last_log = f"WAV Error: {e}"
        return {'FINISHED'}

# --------------------------------------------------------------
#   PANEL
# --------------------------------------------------------------

class ORBIS_PT_sidebar(Panel):
    bl_label      = "Orbis Live Link"
    bl_idname     = "ORBIS_PT_sidebar"
    bl_space_type = 'VIEW_3D'
    bl_region_type= 'UI'
    bl_category   = 'Orbis'

    def draw(self, context):
        layout = self.layout
        props = context.scene.orbis_props

        # JSON
        col = layout.column(align=True)
        col.label(text="JSON Path:")
        col.prop(props,"json_path",text="")
        col.operator("orbis.refresh",icon='FILE_REFRESH')

        # WAV
        col.separator()
        col.label(text="Load WAV:")
        col.prop(props,"wav_path",text="")
        col.operator("orbis.load_wav",icon='SOUND')

        # Target mesh
        col.separator()
        col.label(text="Target Object:")
        col.prop(props,"target_obj",text="")
        col.prop(props,"auto_setup",text="Auto‑setup GN")
        col.operator("orbis.setup_gn",icon='NODETREE')

        # Statistics
        obj = props.target_obj
        if obj and obj.type=='MESH':
            me = obj.data
            layout.separator()
            layout.label(text="Mesh Stats:")
            layout.label(text=f"Verts: {len(me.vertices)}")
            layout.label(text=f"Edges: {len(me.edges)}")
            layout.label(text=f"Faces: {len(me.polygons)}")
            tris = sum([p.loop_total-2 for p in me.polygons])
            layout.label(text=f"Tris: {tris}")
            vc = len(me.vertex_colors) if hasattr(me,"vertex_colors") else 0
            layout.label(text=f"VColors: {vc}")
            rig = ("Yes" if obj.find_armature() else "No")
            layout.label(text=f"Armature: {rig}")

        # Data & log
        layout.separator()
        connected = last_data["timestamp"]>0
        icon = 'CHECKMARK' if connected else 'ERROR'
        layout.label(text=f"JSON OK" if connected else "No data",icon=icon)
        if connected:
            layout.label(text=f"dB: {last_data['volume']:.1f}")
            layout.label(text=f"Freq: {last_data['dominant_freq']:.1f} Hz")
            t = time.localtime(last_data['timestamp'])
            layout.label(text="Last: "+time.strftime("%H:%M:%S",t))
        layout.separator()
        layout.label(text="Log:")
        layout.label(text=props.last_log)

# --------------------------------------------------------------
#   REGISTRY
# --------------------------------------------------------------

classes = (
    ORBIS_Props,
    ORBIS_OT_setup,
    ORBIS_OT_load_wav,
    ORBIS_OT_refresh,
    ORBIS_PT_sidebar,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.orbis_props = PointerProperty(type=ORBIS_Props)
    bpy.app.timers.register(poll_json)
    print("[Orbis] Add-on registrado.")

def unregister():
    try:
        bpy.app.timers.unregister(poll_json)
    except:
        pass
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.orbis_props
    print("[Orbis] Add-on desregistrado.")
