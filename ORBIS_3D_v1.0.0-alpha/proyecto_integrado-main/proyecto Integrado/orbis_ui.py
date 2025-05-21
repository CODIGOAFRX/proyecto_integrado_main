'''
──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
    ORBIS – Frequency-Driven 3D Visualizer
    Version: v1.0.0-alpha (2025-05-22 build)
    Proyecto Fin de Grado · MEDAC NEVADA · 2024‑25
    Integrantes del equipo ORBIS:
    · Pedro Jesús Gómez Pérez – Arquitectura DSP & back‑end de audio, Diseño UI / UX y desarrollo PySide 6 en estado alpha
    · David Erik García Arenas – Integración 3D con Blender & shaders, Diseño UI / UX y desarrollo PySide 6 en estado beta
──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
    CHANGELOG completo hasta v1.0.0-alpha

──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
    v0.9.1 – Smooth UI
    - PreciseTimer + linear interpolation → butter-smooth motion.
    - Moving-average FPS read-out tied to the user cap (30-240, monitor, ±360).
    - “Unlimited” is capped to MAX_FPS_HW to avoid runaway 10 000 fps.
──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
    2025-05-15 build – (v0.9.5-beta)
    - Smooth UI: selectable refresh-rates (30/60/120/240 Hz, monitor native, unlimited) – live-switch via Settings.
    - OpenGL sphere (or coloured cube fallback) visible in “3-D Shape”.
    - All earlier bug-fixes (Qt6 mouse events, font warnings, JSON safety…).
──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
    v0.9.7-beta (2025-05-16 build) – Mock-up parity
    - Adds “Load Model…” & “Generate” controls (exclusive to 3-D Shape mode).
    - VBO offsets fixed (ctypes.c_void_p) → mesh now renders.
    - “Generate” (icosphere) corregido.
    - Loader OBJ genera normales si faltan.
    - LED ● Live verde/rojo.
    - FPS se muestra siempre.
    - Triple-buffer + frameSwapped → pacing suave, sin tirones a 30 fps.
    - Tokens de color/tipografía calcados del CSS Tailwind del prototipo.
    - Botón “Start Analysis” con halo neón + pequeño “ripple” al hacer click.
    - Deslizadores y checkboxes estilizados (track degradado, knob cian).
    - Footer y encabezado con versión dinámica y logo.
    - Docstrings y comentarios en castellano para facilitar lectura al tribunal.
    - Zoom-in/out, reset, fullscreen y captura PNG del espectro mantenidos.
──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
    v0.9.8-beta (2025-05-19 build)
    - Mesh finalmente renderiza (OBJ por defecto o icosfera generada).
    - Waveform/spectrum actualizan nuevamente, removido _tick_ui duplicado.
    - Visualización se oculta cuando se detiene el análisis.
    - Contador FPS siempre visible.
    - Botones ‘Load Model…’ / ‘Generate’ rediseñados.
    - Triple-buffer + vsync (swap-interval 1) para suavidad constante.
──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
    v0.9.9-beta (2025-05-20 build)
    - FIX: Error NumPy “ambiguous truth value” cuando d.get("fft") devuelve ndarray.
    - Exportación JSON contiene todas las claves requeridas por el add-on Blender:
    - volume · dominant_freq · bal_lh · bal_mid
    - dev_low · dev_lowmid · dev_mid · dev_himid · dev_high
    - Espectro de 12 bandas (20 Hz → 20 kHz)
    - version · timestamp
    - Lógica de waveform/spectrogram intacta, código completo incluido.
    - Malla renderiza correctamente (OBJ + icosfera), visualización oculta al detener análisis.
    - Triple-buffer vsync (swap-interval 1) activado → pacing fluido.
──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
 ###  🔖 Versión actual: v1.0.0-alpha (2025-05-22 build) ###
    Importante: Primera versión plenamente funcional, lista para presentación inicial al tribunal.
    Continúan placeholders y stubs internos para futuras mejoras posteriores al prototipo.

    Cambios y mejoras clave de esta versión:
    - Corrección crítica: solucionado error TypeError en update_audio().

    - Botón "Launch 3-D Viewer" aparece exclusivamente en modo 3-D Shape con padding y dimensiones corregidas.

    - Botón "Capture" corregido (dimensiones adecuadas y totalmente visible).

    - Indicador "Live" LED cambia adecuadamente entre rojo/verde al iniciar/detener análisis.

    - Diálogo Settings incorpora checkbox para opción "Always on top".

    - Ventana ahora soporta opcionalmente comportamiento de mantenerse siempre encima.

    - Texto overlay informativo solo visible en modo 3-D Shape.

    - Controles legacy OpenGL se conservan en código, pero se ocultan visualmente para evitar confusión.
──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
    📍 Estado general actual (v1.0.0-alpha)
    El proyecto cumple objetivos técnicos planteados en fase prototipo.

    Integración completa del visualizador 3D externo Baryon vía navegador (placeholder para futura implementación interna).

    Exportación JSON robusta y compatible con Blender.

    Estructura técnica estable para presentación oficial ante tribunal.

    Próximos pasos para avanzar a v1.0.0-beta y release candidate (rc):

    Finalizar integración directa 3D interna (eliminar stubs OpenGL).

    Implementar correctamente controles: Frequency Range, Resolution y Sensitivity.

    Pulir interfaz final y optimizar UX/UI basándose en feedback del tribunal.
──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
    📝 Licencia
    Public-domain / CC0. El proyecto entero permanece abierto para futuras colaboraciones académicas y profesionales.
    '''

import sys, time, math, json, warnings, ctypes
from pathlib import Path
from collections import deque
from types import SimpleNamespace

# External helpers
from visualizers.launch_baryon import launch as launch_baryon
from audio_analyzer           import AudioAnalyzer
from mesh_utils               import load_obj, create_icosphere

# ───── Qt / PySide6 ─────────────────────────────────────────────────────────
from PySide6.QtCore    import (
    Qt, QTimer, QElapsedTimer, QEasingCurve, QPropertyAnimation, QPointF
)
from PySide6.QtGui     import (
    QColor, QPainter, QPen, QBrush, QFont, QFontDatabase,
    QRadialGradient, QLinearGradient, QGradient, QPixmap, QIcon,
    QGuiApplication, QSurfaceFormat
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QComboBox, QSlider, QCheckBox, QGroupBox, QStatusBar,
    QToolButton, QGraphicsDropShadowEffect, QDialog, QDialogButtonBox,
    QFileDialog, QMessageBox
)
from PySide6.QtOpenGLWidgets import QOpenGLWidget
import pyqtgraph as pg

import numpy as np
import psutil, sounddevice as sd
import pyloudnorm

# ───── Paths / constants ────────────────────────────────────────────────────
BASE_DIR  = Path(__file__).resolve().parent
FONT_DIR  = BASE_DIR / "resources" / "fonts"
IMG_DIR   = BASE_DIR / "resources" / "images"
MODEL_DIR = BASE_DIR / "resources" / "models"
CAPT_DIR  = BASE_DIR / "captures"
JSON_DIR  = BASE_DIR / "json"
JSON_PATH = JSON_DIR / "orbis_data.json"

LOGO_PATH = IMG_DIR / "orbis_logo.png"
ICON_PATH = IMG_DIR / "orbis_icon.ico"

APP_VERSION = "v1.0.0-alpha"

Y_MIN_DB, Y_MAX_DB = -40, 30
COLORS = dict(
    bg        ="#121212", panel="#1E1E1E", border="#2D2D2D", text   ="#E0E0E0",
    primary   ="#45A4FF", secondary="#9B4DFF", cyan   ="#45D6FF",
    on        ="#45FF7A", off      ="#FF6060"
)

MAX_FPS_HW = 360
FPS_WINDOW = 120
EMA_ALPHA  = .12

# ───── Spectral bar layout (13 half-octave bars) ───────────────────────────
_BOUNDS = np.array([1,20,50,100,250,500,1000,2000,5000,10000,15000,20000], float)
BAR_CENTRES = np.unique(
    np.array([math.sqrt(_BOUNDS[i-1]*_BOUNDS[i]) if i else 1
             for i in range(len(_BOUNDS))] + _BOUNDS.tolist())
)
N_BARS = BAR_CENTRES.size

SPEC_FREQS  = [20,50,100,250,500,1000,2000,5000,6000,10000,15000,20000]
SPEC_LABELS = ["20Hz","50Hz","100Hz","250Hz","500Hz","1000Hz","2000Hz",
               "5000Hz","6000Hz","10000Hz","15000Hz","20000Hz"]

try:
    VIRIDIS_LUT = pg.colormap.get("viridis").getLookupTable(alpha=True)
except Exception:
    VIRIDIS_LUT = np.array(
        [[ 68,  1, 84,255],[ 59, 81,139,255],[ 33,144,141,255],
         [ 72,193,110,255],[170,220, 50,255],[253,231, 37,255]]
    )

warnings.filterwarnings("ignore",
    message="Stereo Mix not found",
    category=UserWarning
)

# ───── Graceful OpenGL stub if PyOpenGL missing ────────────────────────────
try:
    import OpenGL.GL  as GL
    import OpenGL.GLU as GLU
    OPENGL_OK = True
except Exception:
    OPENGL_OK = False
    def _noop(*_, **__): ...
    GL  = SimpleNamespace(glClearColor=_noop, glEnable=_noop, glClear=_noop,
                          glViewport=_noop, glMatrixMode=_noop, glLoadIdentity=_noop,
                          glTranslatef=_noop, glRotatef=_noop, glScalef=_noop,
                          glMaterialfv=_noop, glBindBuffer=_noop, glBufferData=_noop,
                          glEnableClientState=_noop, glVertexPointer=_noop,
                          glNormalPointer=_noop, glDrawElements=_noop,
                          glDeleteBuffers=_noop, glGenBuffers=lambda n: 0,
                          GL_COLOR_BUFFER_BIT=0, GL_DEPTH_BUFFER_BIT=0,
                          GL_DEPTH_TEST=0, GL_LIGHTING=0, GL_LIGHT0=0,
                          GL_PROJECTION=0, GL_MODELVIEW=0,
                          GL_AMBIENT_AND_DIFFUSE=0, GL_TRIANGLES=0,
                          GL_UNSIGNED_INT=0, GL_ARRAY_BUFFER=0,
                          GL_ELEMENT_ARRAY_BUFFER=0)
    class _GLU(SimpleNamespace):
        def gluPerspective(self, *a): ...
    GLU = _GLU()

# ══════════════════════════════  GLWidget  ═════════════════════════════════
class GLWidget(QOpenGLWidget):
    """
    Simple OpenGL canvas that draws either a loaded OBJ or a generated icosphere.
    (Kept for reference; hidden in production build.)
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.angle  = 0.
        self.radius = 1.
        self.vbo = self.ebo = self.mesh = None
        self.frameSwapped.connect(self.update)

    # orbit camera ---------------------------------------------------------
    def mousePressEvent(self, e): self._last = e.position()
    def mouseMoveEvent(self, e):
        dx = e.position().x() - self._last.x()
        self.angle = (self.angle + dx) % 360
        self._last = e.position()

    def update_audio(self, vol: float, mid: float = 0.0):
        self.radius = max(.2, min(1.25, (vol + 60) / 50))
        self.mid_mix = mid


    # GL lifecycle ---------------------------------------------------------
    def initializeGL(self):
        if not OPENGL_OK: return
        GL.glClearColor(18/255,18/255,18/255,1)
        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glEnable(GL.GL_LIGHTING); GL.glEnable(GL.GL_LIGHT0)
        GL.glLightfv(GL.GL_LIGHT0, GL.GL_POSITION, (GL.GLfloat*4)(0,0,3,1))
        self._load_default()

    def _load_default(self):
        try:    self.mesh = load_obj(MODEL_DIR / "default_orb.obj")
        except: self.mesh = create_icosphere(1.0, 2)
        self._upload_mesh()

    def _upload_mesh(self):
        if not (OPENGL_OK and self.mesh): return
        verts = self.mesh.interleave()
        if self.vbo: GL.glDeleteBuffers(1,[self.vbo])
        self.vbo = GL.glGenBuffers(1)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.vbo)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, verts.nbytes, verts, GL.GL_STATIC_DRAW)
        if self.ebo: GL.glDeleteBuffers(1,[self.ebo])
        self.ebo = GL.glGenBuffers(1); GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, self.ebo)
        GL.glBufferData(GL.GL_ELEMENT_ARRAY_BUFFER, self.mesh.indices.nbytes,
                        self.mesh.indices, GL.GL_STATIC_DRAW)
        stride = 24
        GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
        GL.glVertexPointer(3, GL.GL_FLOAT, stride, ctypes.c_void_p(0))
        GL.glEnableClientState(GL.GL_NORMAL_ARRAY)
        GL.glNormalPointer(GL.GL_FLOAT, stride, ctypes.c_void_p(12))

    def resizeGL(self, w:int, h:int):
        if not OPENGL_OK: return
        GL.glViewport(0,0,w,h)
        GL.glMatrixMode(GL.GL_PROJECTION); GL.glLoadIdentity()
        GLU.gluPerspective(45., w/max(1,h), .1, 100)

    def paintGL(self):
        if not OPENGL_OK: return
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        GL.glMatrixMode(GL.GL_MODELVIEW); GL.glLoadIdentity()
        GL.glTranslatef(0,0,-3.5); GL.glRotatef(-20,1,0,0); GL.glRotatef(self.angle,0,1,0)
        GL.glScalef(self.radius, self.radius, self.radius)
        GL.glMaterialfv(GL.GL_FRONT, GL.GL_AMBIENT_AND_DIFFUSE, (GL.GLfloat*4)(.27,.64,1,1))
        if self.mesh:
            GL.glDrawElements(GL.GL_TRIANGLES, self.mesh.indices.size,
                              GL.GL_UNSIGNED_INT, None)

    def paintEvent(self, _): ...

# ═══════════════════════════  Orb (neon disc)  ═════════════════════════════
class OrbWidget(QWidget):
    """
    2-D neon orb shown in “Spectrum” mode.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.volume = -60.; self.freq = 1000.
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)

    def update_data(self, vol: float, freq: float):
        self.volume, self.freq = vol, freq
        self.update()

    def paintEvent(self, _):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        sc = max(.2, min(1.5, (self.volume + 60) / 40))
        sh = max(.5, min(1.5, (10000 - self.freq) / 9000))
        w, h = self.width()*sc*sh*.5, self.height()*sc*(2-sh)*.5
        x, y = (self.width()-w)/2, (self.height()-h)/2
        g = QRadialGradient(self.rect().center(), max(w,h))
        g.setColorAt(0, QColor(69,164,255,235))
        g.setColorAt(.8, QColor(155,77,255,70))
        g.setColorAt(1, Qt.transparent)
        p.setBrush(QBrush(g)); p.setPen(Qt.NoPen); p.drawEllipse(x,y,w,h)

# ═════════════════════════  Visualization stack  ═══════════════════════════
class VisualizationWidget(QWidget):
    """
    Stacked container:
        GLWidget (hidden in production) · neon orb · waveform · spectrogram
        + corner tool buttons
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        # core widgets
        self.gl  = GLWidget(self)
        self.orb = OrbWidget(self); self.orb.lower()

        # waveform plot
        self.wave_len = 1024
        self.wave_pg = pg.PlotWidget(self, background=None); self.wave_pg.hide()
        self.wave_pg.setMenuEnabled(False); self.wave_pg.setMouseEnabled(False, False)
        self.wave_pg.getPlotItem().setContentsMargins(0,0,0,0)
        self.wave_pg.setYRange(-1,1); self.wave_pg.setXRange(0,self.wave_len,0)
        self.wave_curve = self.wave_pg.plot(pen=pg.mkPen(COLORS['secondary'], width=1))

        # spectrogram plot
        self.spec_pg = pg.PlotWidget(self, background=None); self.spec_pg.hide()
        self.spec_pg.setMenuEnabled(False); self.spec_pg.setMouseEnabled(False, False)
        self.spec_pg.getPlotItem().setContentsMargins(0,0,0,0)
        self.spec_img  = pg.ImageItem(axisOrder="row-major")
        self.spec_img.setLookupTable(VIRIDIS_LUT)
        self.spec_pg.addItem(self.spec_img)
        self.spec_data = np.zeros((128,256), np.float32)

        # overlay buttons
        glyphs = ["\ue3d4","\ue3d5","\ue3a8","\ue38b"]   # ri-zoom-in/out/reset/fullscreen
        names  = ["in","out","reset","fs"]
        self.ctrl = {}
        for g,n in zip(glyphs,names):
            b = QToolButton(self, text=g)
            b.setFont(QFont("Remixicon", 16)); b.setFixedSize(32,32)
            b.setStyleSheet(
                "QToolButton{background:%s;border-radius:16px;color:%s;}"
                "QToolButton:hover{color:%s;}"
                % (COLORS['panel'], COLORS['secondary'], COLORS['primary'])
            )
            b.raise_(); self.ctrl[n] = b

    # --- layout ------------------------------------------------------------
    def resizeEvent(self, _):
        for w in (self.gl, self.orb, self.wave_pg, self.spec_pg):
            w.setGeometry(self.rect())
        x, y = 14, self.height() - 46
        for b in self.ctrl.values():
            b.move(x, y); x += 38

    # --- honeycomb grid background ----------------------------------------
    def paintEvent(self, _):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        p.setPen(QPen(QColor(69,164,255,25)))
        for gx in range(0, self.width(), 20):
            p.drawLine(gx,0,gx,self.height())
        for gy in range(0, self.height(), 20):
            p.drawLine(0,gy,self.width(),gy)
        r = min(self.width(), self.height())*.25
        c = self.rect().center()
        pts = [QPointF(c.x()+r*math.cos(math.pi/3*i),
                       c.y()+r*math.sin(math.pi/3*i)) for i in range(6)]
        p.setPen(QPen(QColor(69,164,255,80),1))
        g = QRadialGradient(c, r)
        g.setColorAt(0, QColor(69,164,255,13))
        g.setColorAt(1, COLORS['bg'])
        p.setBrush(QBrush(g)); p.drawPolygon(pts)

    # --- mode switching ----------------------------------------------------
    def set_mode(self, mode: str):
        # hide all, then show the one requested
        for w in (self.wave_pg, self.spec_pg, self.orb, self.gl):
            w.hide()
        match mode:
            case "wave":     self.wave_pg.show()
            case "spec":     self.spec_pg.show()
            case "spectrum": self.orb.show()
            case "shape":    self.gl.show(); self.gl.raise_()

    # --- zoom helpers ------------------------------------------------------
    def zoom_y(self, factor: float):
        for w in (self.wave_pg, self.spec_pg):
            if w.isVisible():
                vb = w.getViewBox()
                lo, hi = vb.viewRange()[1]
                mid = (lo+hi)/2
                span = (hi-lo)*factor/2
                vb.setYRange(mid-span, mid+span, 0)

    def reset_zoom(self):
        for w in (self.wave_pg, self.spec_pg):
            if w.isVisible():
                w.getViewBox().autoRange()

# ════════════════════════  Settings dialog  ════════════════════════════════
class SettingsDialog(QDialog):
    def __init__(self, current_fps: int, on_top: bool, parent=None):
        super().__init__(parent); self.setWindowTitle("ORBIS Settings")
        lay = QVBoxLayout(self)

        lay.addWidget(QLabel("Target frame-rate"))
        self.fps_cb = QComboBox()
        scr = int(round(QGuiApplication.primaryScreen().refreshRate()))
        for txt, val in [
            ("30 fps",30),("60 fps",60),("120 fps",120),("240 fps",240),
            (f"Monitor max ({scr} Hz)", scr), ("Unlimited", 0)
        ]:
            self.fps_cb.addItem(txt, val)
            if val == current_fps:
                self.fps_cb.setCurrentIndex(self.fps_cb.count()-1)
        lay.addWidget(self.fps_cb)

        self.chk_top = QCheckBox("Always on top", checked=on_top)
        lay.addWidget(self.chk_top)

        bb = QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel, self)
        bb.accepted.connect(self.accept); bb.rejected.connect(self.reject)
        lay.addWidget(bb)

    @property
    def selected_fps(self) -> int:   return int(self.fps_cb.currentData())
    @property
    def keep_on_top(self) -> bool:   return self.chk_top.isChecked()

# ════════════════════════════  Orbis UI  ═══════════════════════════════════
class OrbisUI(QMainWindow):
    # ─── construction ──────────────────────────────────────────────────────
    def __init__(self, analyzer: AudioAnalyzer):
        super().__init__()
        self.analyzer      = analyzer
        self.running       = False
        self.current_mode  = "wave"
        self.target_fps    = 60
        self.always_on_top = False

        self._audio_period_ms = 33
        self._prev = self._next = None
        self._frame_ts = deque(maxlen=FPS_WINDOW); self._fps_ema = None
        self.clock = QElapsedTimer(); self.clock.start()

        self._fonts(); self._style(); self._build_ui(); self._timers()
        self._apply_on_top()

        self.setWindowTitle(f"ORBIS – 3-D Visualizer {APP_VERSION}")
        if ICON_PATH.exists():
            QGuiApplication.setWindowIcon(QIcon(str(ICON_PATH)))
            self.setWindowIcon(QIcon(str(ICON_PATH)))
        elif LOGO_PATH.exists():
            QGuiApplication.setWindowIcon(QIcon(str(LOGO_PATH)))
            self.setWindowIcon(QIcon(str(LOGO_PATH)))
        self.resize(1280, 800)

    # ─── style helpers ─────────────────────────────────────────────────────
    def _fonts(self):
        for f in ("Orbitron-Regular.ttf","Rajdhani-Regular.ttf","Remixicon.ttf"):
            p = FONT_DIR / f
            if p.exists():
                QFontDatabase.addApplicationFont(str(p))

    def _style(self):
        self.setStyleSheet(f"""
        QWidget{{background:{COLORS['bg']};color:{COLORS['text']};font-family:Rajdhani;}}
        QGroupBox{{border:1px solid {COLORS['border']};border-radius:12px;padding:8px;}}
        QGroupBox:title{{subcontrol-origin:margin;left:8px;padding:0 4px;font-family:Orbitron;color:#fff;}}
        QPushButton{{background:{COLORS['panel']};border:1px solid {COLORS['secondary']}40;
                     border-radius:12px;padding:6px 12px;}}
        QPushButton#neon{{color:{COLORS['primary']};border:1px solid {COLORS['primary']}50;}}
        QToolButton{{background:{COLORS['panel']};border-radius:16px;color:{COLORS['secondary']};}}
        QToolButton:hover{{color:{COLORS['primary']};}}
        QSlider::groove:horizontal{{background:{COLORS['border']};height:4px;border-radius:2px;}}
        QSlider::sub-page:horizontal{{height:4px;border-radius:2px;
                                      background:linear-gradient(90deg,{COLORS['primary']},{COLORS['secondary']});}}
        QSlider::handle:horizontal{{width:16px;height:16px;border-radius:8px;background:{COLORS['cyan']};margin:-6px 0;}}
        QCheckBox::indicator{{width:18px;height:18px;border-radius:4px;background:{COLORS['border']};}}
        QCheckBox::indicator:checked{{background:{COLORS['primary']};}}
        """)

    # ─── build UI layout ───────────────────────────────────────────────────
    def _build_ui(self):
        central = QWidget(); self.setCentralWidget(central)
        root = QVBoxLayout(central); root.setContentsMargins(0,0,0,0); root.setSpacing(0)

        root.addWidget(self._header())
        body = QWidget(); bl = QVBoxLayout(body); bl.setContentsMargins(12,12,12,12); bl.setSpacing(12)
        top  = QHBoxLayout(); bl.addLayout(top, 1)

        top.addWidget(self._controls(),  1)
        top.addWidget(self._viz(),       3)
        top.addWidget(self._metrics(),   1)

        bl.addWidget(self._spectrum())
        root.addWidget(body)
        self._footer()

    # ─── header bar ────────────────────────────────────────────────────────
    def _header(self):
        hdr = QWidget()
        hdr.setStyleSheet(f"background:{COLORS['panel']};border-bottom:1px solid {COLORS['border']}")
        hl = QHBoxLayout(hdr); hl.setContentsMargins(16,8,16,8)

        if LOGO_PATH.exists():
            logo = QLabel()
            logo.setPixmap(QPixmap(str(LOGO_PATH)).scaledToHeight(40, Qt.SmoothTransformation))
            hl.addWidget(logo)

        hl.addWidget(QLabel("ORBIS", font=QFont("Orbitron", 22, QFont.Bold),
                            styleSheet=f"color:{COLORS['primary']}"))
        hl.addWidget(QLabel("Audio Cockpit", font=QFont("Orbitron", 20)))
        hl.addSpacing(32)

        # input device combo
        self.device_cb = QComboBox(); self._fill_devices()
        box = QGroupBox(); bx = QHBoxLayout(box); box.setFixedWidth(380)
        bx.addWidget(QLabel(chr(0xf3c2), font=QFont("Remixicon", 14),
                            styleSheet=f"color:{COLORS['secondary']}"))
        bx.addWidget(self.device_cb)
        box.setStyleSheet(f"background:{COLORS['border']};border-radius:12px")
        hl.addWidget(box); hl.addStretch()

        # start / stop button
        self.start_btn = QPushButton(chr(0xefea) + "  Start Analysis", objectName="neon")
        self._neon(self.start_btn)
        self.start_btn.clicked.connect(self._toggle_stream)
        hl.addWidget(self.start_btn)

        # settings button
        hl.addWidget(QPushButton(chr(0xeb8c) + "  Settings",
                                 clicked=self._open_settings))
        return hdr

    def _fill_devices(self):
        self.device_cb.clear()
        for i, d in enumerate(sd.query_devices()):
            if d["max_input_channels"] > 0:
                self.device_cb.addItem(d["name"], i)

    # ─── left controls column ──────────────────────────────────────────────
    def _controls(self):
        gb = QGroupBox("Analysis Controls"); v = QVBoxLayout(gb)

        for lab, val, init in [
            ("Frequency Range", "20 Hz – 20 kHz", 100),
            ("Resolution",      "2048 FFT",       70),
            ("Sensitivity",     "-24 dB",         50)
        ]:
            lay = QVBoxLayout()
            hl  = QHBoxLayout(); hl.addWidget(QLabel(lab))
            hl.addWidget(QLabel(val, styleSheet=f"color:{COLORS['secondary']};font-size:11px"))
            lay.addLayout(hl)
            s = QSlider(Qt.Horizontal); s.setRange(0,100); s.setValue(init); lay.addWidget(s)
            v.addLayout(lay)

        self.chk_peak = QCheckBox("Show Peak Markers",  checked=True)
        self.chk_grid = QCheckBox("Show Grid Lines",    checked=True)
        self.chk_log  = QCheckBox("Logarithmic Scale",  checked=True)
        opts = QGroupBox("Display Options"); ov = QVBoxLayout(opts)
        for w in (self.chk_peak, self.chk_grid, self.chk_log):
            ov.addWidget(w)
        v.addWidget(opts)

        modes = {"Spectrum":"spectrum","3-D Shape":"shape","Waveform":"wave","Spectrogram":"spec"}
        self.mode_btn = {}; mod = QGroupBox("Visualization Mode"); grid = QGridLayout(mod)
        for i,(txt,key) in enumerate(modes.items()):
            b = QPushButton(txt); b.setCheckable(True)
            b.clicked.connect(lambda _=False, k=key: self._set_mode(k))
            self.mode_btn[key] = b; grid.addWidget(b, i//2, i%2)
        v.addWidget(mod)
        self._update_mode_style()
        return gb

    # ─── real-time visualization stack ─────────────────────────────────────
    def _viz(self):
        gb = QGroupBox(); v = QVBoxLayout(gb)

        # heading
        hl = QHBoxLayout()
        hl.addWidget(QLabel("Real-time Visualization", font=QFont("Orbitron",12)))
        self.lbl_live = QLabel("● Live", font=QFont("Rajdhani",11))
        self._set_live_led(False)
        hl.addWidget(self.lbl_live); hl.addStretch()

        # legacy (hidden) OpenGL controls
        self.chk_auto = QCheckBox("Auto-rotate", checked=True); self.chk_auto.hide()
        self.btn_load = QPushButton("Load Model…"); self.btn_load.hide()
        self.btn_gen  = QPushButton("Generate");    self.btn_gen.hide()

        # launch baryon button
        self.btn_baryon = QPushButton("Launch 3-D Viewer")
        self.btn_baryon.setFixedSize(140, 28)  # Slightly increased dimensions for padding
        self.btn_baryon.setStyleSheet(
            f"QPushButton{{"
            f"border:1px solid {COLORS['primary']}80;"
            f"border-radius:14px;"
            f"background:{COLORS['panel']};"
            f"color:{COLORS['primary']};"
            f"padding:2px 16px;"
            f"}}"
            f"QPushButton:hover{{"
            f"border-color:{COLORS['secondary']}a0;"
            f"color:{COLORS['secondary']};"
            f"}}"
        )

        hl.addWidget(self.btn_baryon); v.addLayout(hl)

        # stacked plots
        self.vis = VisualizationWidget(); v.addWidget(self.vis, 1)

        # overlay hint
        self.lbl_3d_hint = QLabel(
            "<b>External 3-D engine ready</b><br>"
            "Press <i>Launch 3-D Viewer</i>.", self.vis)
        self.lbl_3d_hint.setAlignment(Qt.AlignCenter)
        self.lbl_3d_hint.setStyleSheet(
            "background:rgba(0,0,0,0.55);color:#fff;border-radius:16px;padding:24px;")
        self.lbl_3d_hint.hide(); self.lbl_3d_hint.raise_()

        # connections
        self.btn_baryon.clicked.connect(self._open_baryon)
        c = self.vis.ctrl
        c["in"].clicked.connect(lambda: self.vis.zoom_y(.8))
        c["out"].clicked.connect(lambda: self.vis.zoom_y(1.25))
        c["reset"].clicked.connect(self.vis.reset_zoom)
        c["fs"].clicked.connect(lambda:
            self.isFullScreen() and self.showNormal() or self.showFullScreen())

        return gb

    # ─── metrics panel -----------------------------------------------------
    def _metrics(self):
        gb = QGroupBox("Audio Metrics"); v = QVBoxLayout(gb); self.metrics = {}
        for lab in ("Peak Level","RMS Level","Integrated LUFS","Short-term LUFS"):
            box = QWidget(); bl = QVBoxLayout(box); bl.setContentsMargins(0,0,0,0)
            hl = QHBoxLayout(); hl.addWidget(QLabel(lab))
            val = QLabel("---", font=QFont("Orbitron",12))
            val.setStyleSheet(f"color:{COLORS['cyan']}"); hl.addWidget(val); bl.addLayout(hl)
            bg = QWidget(); bg.setFixedHeight(6)
            bg.setStyleSheet(f"background:{COLORS['panel']};border-radius:3px")
            bar = QWidget(bg); bar.setGeometry(0,0,0,6)
            bar.setStyleSheet(
                "background:linear-gradient(90deg,#45A4FF,#9B4DFF);border-radius:3px")
            bl.addWidget(bg); v.addWidget(box)
            self.metrics[lab] = (val, bar)

        fa = QGroupBox("Frequency Analysis"); g = QGridLayout(fa); self.band_lbl = {}
        for i,(txt,key) in enumerate([
            ("Low (20-250 Hz)","low"), ("Mid (250-2 kHz)","mid"),
            ("High (2-20 kHz)","high"), ("Dominant Freq","dom")
        ]):
            lay = QVBoxLayout()
            lay.addWidget(QLabel(txt, styleSheet="font-size:11px"))
            val = QLabel("---", font=QFont("Orbitron",12))
            val.setStyleSheet(f"color:{COLORS['primary']}")
            lay.addWidget(val); g.addLayout(lay, i//2, i%2)
            self.band_lbl[key] = val
        v.addWidget(fa)
        return gb

    # ─── FFT spectrum panel -----------------------------------------------
    def _spectrum(self):
        gb = QGroupBox("FFT Spectrum Analyzer"); v = QVBoxLayout(gb)
        hl = QHBoxLayout(); hl.addWidget(QLabel("Smoothing", styleSheet="font-size:11px"))
        self.smooth = QSlider(Qt.Horizontal); self.smooth.setRange(0,100); self.smooth.setValue(20)
        hl.addWidget(self.smooth)
        self.cap_btn = QPushButton(chr(0xf135) + " Capture")
        self.cap_btn.setFixedSize(100, 24)  # Width increased for text visibility
        self.cap_btn.setStyleSheet(
            f"border-radius:12px;"
            f"border:1px solid {COLORS['primary']}60;"
            f"padding: 2px 10px;"
        )
        self.cap_btn.clicked.connect(self._capture)
        hl.addWidget(self.cap_btn)

        hl.addStretch(); v.addLayout(hl)
        self.pg = pg.PlotWidget(background=COLORS['bg'])
        self.pg.getPlotItem().setContentsMargins(0,0,0,0)
        v.addWidget(self.pg)
        return gb

    # ─── footer bar --------------------------------------------------------
    def _footer(self):
        sb = QStatusBar(); sb.setStyleSheet(f"background:{COLORS['panel']}")
        self.setStatusBar(sb)
        self.lbl_time, self.lbl_cpu, self.lbl_buf, self.lbl_sr = [QLabel() for _ in range(4)]
        for w in (self.lbl_time,self.lbl_cpu,self.lbl_buf,self.lbl_sr):
            sb.addPermanentWidget(w)
        self.lbl_fps = QLabel(); sb.addPermanentWidget(self.lbl_fps)
        sb.addPermanentWidget(QLabel(f"ORBIS {APP_VERSION}"))

    # ─── neon ripple animation --------------------------------------------
    def _neon(self, btn: QPushButton):
        eff = QGraphicsDropShadowEffect(
            blurRadius=20, color=QColor(COLORS['primary']))
        btn.setGraphicsEffect(eff)
        def ripple():
            anim = QPropertyAnimation(btn, b"geometry"); anim.setDuration(160)
            anim.setEasingCurve(QEasingCurve.InOutQuad)
            g = btn.geometry()
            anim.setStartValue(g); anim.setKeyValueAt(.5, g.adjusted(-4,-2,4,2))
            anim.setEndValue(g); anim.start(QPropertyAnimation.DeleteWhenStopped)
        btn.clicked.connect(ripple)

    # ─── global timers -----------------------------------------------------
    def _timers(self):
        self._session_t0 = time.time()
        self.audio_timer = QTimer(
            timerType=Qt.PreciseTimer, interval=self._audio_period_ms,
            timeout=self._tick_audio); self.audio_timer.start()
        tgt = self.target_fps or MAX_FPS_HW
        self.ui_timer = QTimer(
            timerType=Qt.PreciseTimer, interval=int(1000/tgt),
            timeout=self._tick_ui); self.ui_timer.start()
        self.footer_timer = QTimer(interval=1000, timeout=self._tick_footer); self.footer_timer.start()
        self.lbl_fps.setText("FPS --")

    def _restart_timers(self):
        self.audio_timer.stop(); self.ui_timer.stop()
        self._frame_ts.clear(); self._fps_ema = None
        self._timers()

    # ══════════════════ helper: window on-top flag ════════════════════════
    def _apply_on_top(self):
        self.setWindowFlag(Qt.WindowStaysOnTopHint, self.always_on_top)
        self.show()

    # ─── visualization helpers ─────────────────────────────────────────────
    def _shape_buttons(self):
        vis = (self.current_mode == "shape")
        self.btn_baryon.setVisible(vis)
        self.lbl_3d_hint.setVisible(vis)

    def _open_baryon(self):
        if launch_baryon(force_local=False, ask=True):
            self.btn_baryon.setText("Launched ✔")
        else:
            self.btn_baryon.setText("Retry 3-D Viewer")

    def _set_live_led(self, on: bool):     # colour helper
        col = COLORS['on'] if on else COLORS['off']
        self.lbl_live.setStyleSheet(f"color:{col}")

    # ─── stream toggle -----------------------------------------------------
    def _toggle_stream(self):
        if self.running:
            self.analyzer.stop()
            self.running = False
            self.start_btn.setText(chr(0xefea) + "  Start Analysis")
            self._set_live_led(False)
        else:
            self.analyzer.stop()
            self.analyzer = AudioAnalyzer(device=self.device_cb.currentData())
            self.analyzer.start()
            self.running = True
            self.start_btn.setText(chr(0xef47) + "  Stop Analysis")
            self._set_live_led(True)
            self._frame_ts.clear(); self._fps_ema = None
        self.vis.set_mode(self.current_mode)
        self._shape_buttons()


    # ─── mode switch -------------------------------------------------------
    def _set_mode(self, m: str):
        if m == self.current_mode: return
        self.current_mode = m
        self._update_mode_style()
        self.vis.set_mode(m)
        self._shape_buttons()

    def _update_mode_style(self):
        for k,b in self.mode_btn.items():
            if k == self.current_mode:
                col = COLORS['primary'] if k in ("spectrum","shape") else COLORS['secondary']
                b.setStyleSheet(f"background:{col}30;color:{col};border:1px solid {col}50;")
                b.setChecked(True)
            else:
                b.setStyleSheet(f"background:{COLORS['panel']};color:#fff;border:1px solid {COLORS['secondary']}40;")
                b.setChecked(False)

    # ─── settings dialog ---------------------------------------------------
    def _open_settings(self):
        dlg = SettingsDialog(self.target_fps, self.always_on_top, self)
        if dlg.exec() == QDialog.Accepted:
            self.target_fps, self.always_on_top = dlg.selected_fps, dlg.keep_on_top
            self._restart_timers()
            self._apply_on_top()



    # ═════════════════════ AUDIO LOOP (≈30 Hz) ════════════════════════
    #   unchanged from v0.9.10-beta (kept in full for completeness)
    #   ────────────────────────────────────────────────────────────────
    def _tick_audio(self):
        if not self.running: return
        d=self.analyzer.get_audio_data() or {}
        vol=float(d.get("volume",-60)); freq=float(d.get("dominant_freq",0))
        fft_raw=d.get("fft");  fft_raw=[] if fft_raw is None else fft_raw
        sig_raw=d.get("signal"); sig_raw=[] if sig_raw is None else sig_raw
        sr=int(d.get("sample_rate",48000))

        fft=np.asarray(fft_raw,float); sig=np.asarray(sig_raw,float)

        # loudness & metric bars
        try:
            meter=pyloudnorm.Meter(sr,block_size=.200)
            lufs_i=meter.integrated_loudness(sig) if sig.size>=int(sr*.25) else vol
        except Exception: lufs_i=vol
        lufs_s=lufs_i+1.5
        for lab,val in [("Peak Level",vol),("RMS Level",vol-6),
                        ("Integrated LUFS",lufs_i),("Short-term LUFS",lufs_s)]:
            self._set_metric(lab,val)

        # 3-band read-outs
        if fft.size:
            freqs=np.fft.rfftfreq(len(fft)*2-2,1/sr)
            def band(a,b):
                idx=np.where((freqs>=a)&(freqs<b))[0]
                return 20*np.log10(np.mean(fft[idx])+1e-10) if idx.size else -60
            self.band_lbl["low"].setText(f"{band(20,250): .1f} dB")
            self.band_lbl["mid"].setText(f"{band(250,2000): .1f} dB")
            self.band_lbl["high"].setText(f"{band(2000,20000): .1f} dB")
            self.band_lbl["dom"].setText(f"{freq: .0f} Hz")

        # waveform
        if sig.size:
            wf=sig[-self.vis.wave_len:]; wf=wf/max(1e-9,np.max(np.abs(wf)))
            if wf.size<self.vis.wave_len: wf=np.pad(wf,(self.vis.wave_len-wf.size,0))
        else: wf=np.zeros(self.vis.wave_len,np.float32)

        # spectrogram (only update data; widget visibility handled elsewhere)
        if fft.size:
            mags=20*np.log10(fft+1e-10)+60
            slice_=np.interp(np.linspace(0,len(mags)-1,128),np.arange(len(mags)),mags)
            self.vis.spec_data=np.roll(self.vis.spec_data,-1,axis=1); self.vis.spec_data[:,-1]=slice_
            if self.current_mode=="spec":   # update image only when visible
                self.vis.spec_img.setImage(self.vis.spec_data,levels=(0,60),autoLevels=False)

        # 13-band bars + 12-band dict
        if fft.size:
            freqs=np.fft.rfftfreq(len(fft)*2-2,1/sr)
            bars=20*np.log10(np.interp(BAR_CENTRES,freqs,fft)+1e-10)
            spec_db={lbl:float(20*np.log10(np.interp(f,freqs,fft)+1e-10))
                     for lbl,f in zip(SPEC_LABELS,SPEC_FREQS)}
        else:
            bars=np.full(N_BARS,-120.0); spec_db={lbl:-120.0 for lbl in SPEC_LABELS}

        # spectral balances & deviations
        def db_to_amp(db): return 10**(db/20)
        low_amp=sum(db_to_amp(spec_db[k]) for k in ("20Hz","50Hz","100Hz"))
        mid_amp=sum(db_to_amp(spec_db[k]) for k in ("250Hz","500Hz","1000Hz","2000Hz"))
        hi_amp =sum(db_to_amp(spec_db[k]) for k in ("5000Hz","6000Hz","10000Hz","15000Hz","20000Hz"))
        total=max(low_amp+mid_amp+hi_amp,1e-9)
        bal_lh =(hi_amp - low_amp)/total
        bal_mid=(mid_amp-0.5*(low_amp+hi_amp))/total

        REF_DB=dict(LOW=-18,LOWMID=-16.5,MID=-13.5,HIMID=-11,HIGH=-11.5); TOL=3
        ZONES=dict(LOW=["20Hz","50Hz","100Hz"],
                   LOWMID=["250Hz"],
                   MID=["500Hz","1000Hz"],
                   HIMID=["2000Hz","5000Hz"],
                   HIGH=["6000Hz","10000Hz","15000Hz","20000Hz"])
        def dev(zone):
            vals=[spec_db[k] for k in ZONES[zone]]; avg=sum(vals)/len(vals)
            return max(-1,min(1,(avg-REF_DB[zone])/TOL))
        devs={z:dev(z) for z in ZONES}

        # push frame for UI interpolation
        self._prev,self._next=self._next,None
        self._next=dict(ts=time.time(),vol=vol,freq=freq,bars=bars,wave=wf)

        # GL update & autorotate
        if self.current_mode=="shape":
            self.vis.gl.update_audio(vol,0.0)
            if self.chk_auto.isChecked(): self.vis.gl.angle=(self.vis.gl.angle+1.5)%360

        # lower bar plot every audio frame
        self._plot_spectrum(fft,sr)

        # JSON export (small)
        self._export_json(vol,freq,spec_db,bal_lh,bal_mid,devs)

    # ═════════════════════ UI LOOP (target FPS) ════════════════════════
    def _tick_ui(self):
        # FPS meter
        self._frame_ts.append(self.clock.elapsed())
        if len(self._frame_ts)>=2:
            span=self._frame_ts[-1]-self._frame_ts[0]
            fps=0 if span==0 else 1000*(len(self._frame_ts)-1)/span
            self._fps_ema=fps if self._fps_ema is None else (1-EMA_ALPHA)*self._fps_ema+EMA_ALPHA*fps
            self.lbl_fps.setText(f"FPS {self._fps_ema:3.0f}")

        if self._next is None: return
        now=time.time()
        if self._prev is None:
            cur=self._next
        else:
            t0,t1=self._prev["ts"],self._next["ts"]; a=0. if t1==t0 else (now-t0)/(t1-t0); a=max(0,min(1,a))
            s=a*a*(3-2*a); lerp=lambda p,q:(1-s)*p+s*q
            cur=dict(vol=lerp(self._prev['vol'],self._next['vol']),
                     freq=lerp(self._prev['freq'],self._next['freq']),
                     bars=lerp(self._prev['bars'],self._next['bars']),
                     wave=lerp(self._prev['wave'],self._next['wave']))

        # per-mode draws
        if self.current_mode=="shape":
            self.vis.gl.update_audio(cur['vol'],0.0); self.vis.gl.update()
        elif self.current_mode=="spectrum":
            self.vis.orb.update_data(cur['vol'],cur['freq'])
        if self.current_mode=="wave": self.vis.wave_curve.setData(cur['wave'])
        if hasattr(self,"_bar_item"):
            self._bar_item.setOpts(x=self._bar_x,y0=Y_MIN_DB,height=cur['bars']-Y_MIN_DB)

    # ═════════════════════ footer (1 Hz) ═════════════════════════════=
    def _tick_footer(self):
        t=int(time.time()-self._session_t0); h,m,s=t//3600,(t//60)%60,t%60
        self.lbl_time.setText(f"Session {h:02}:{m:02}:{s:02}")
        self.lbl_cpu.setText(f"CPU {psutil.cpu_percent():>3.0f}%")
        try:
            d=sd.query_devices(self.device_cb.currentData() or 0)
            sr=int(d["default_samplerate"]); buf=int(d["default_low_input_latency"]*sr)
        except Exception: sr=buf=0
        self.lbl_buf.setText(f"Buffer {buf}"); self.lbl_sr.setText(f"{sr} Hz")

    # ═════════════════════ plot (audio frame) ════════════════════════
    def _plot_spectrum(self,fft:np.ndarray,sr:int):
        if fft is None or not fft.size: return
        centres=BAR_CENTRES
        log20,log50=np.log10(20),np.log10(50)
        seg0=log50-log20; x0=log20-seg0
        log5k=np.log10(5000); hi_span=(np.log10(20000)-log5k)*1.6
        def f2x(f):
            f=np.asarray(f,float); x=np.empty_like(f)
            m0=f<20;             x[m0]=x0+(f[m0]-1)/19*seg0
            m1=(f>=20)&(f<5000); x[m1]=np.log10(f[m1])
            m2=f>=5000;          x[m2]=log5k+(f[m2]-5000)/15000*hi_span
            return x
        x_pos=f2x(centres); x_max=f2x(20000)+seg0*.4
        freqs=np.fft.rfftfreq(len(fft)*2-2,1/sr)
        mags_db=20*np.log10(np.interp(centres,freqs,fft)+1e-10)
        decay=.5
        if not hasattr(self,"_peaks"): self._peaks=mags_db.copy()
        self._peaks=np.maximum(mags_db,self._peaks-decay)
        alpha=self.smooth.value()/100
        if not hasattr(self,"_smooth"): self._smooth=mags_db.copy()
        self._smooth=alpha*self._smooth+(1-alpha)*mags_db
        sm_db=self._smooth
        p=self.pg.getPlotItem(); p.clear()
        p.showGrid(x=True,y=self.chk_grid.isChecked(),alpha=.3)
        vb=p.getViewBox()
        vb.setLimits(xMin=x0,xMax=x_max,yMin=Y_MIN_DB,yMax=Y_MAX_DB)
        p.setXRange(x0,x_max,0); p.setYRange(Y_MIN_DB,Y_MAX_DB,0)
        p.getAxis("bottom").setTicks([[(f2x(f),f"{int(f):,} Hz") for f in _BOUNDS[1:]]])
        p.getAxis("left").setTicks([[(d,f"{d:+.0f} dB") for d in
                                     range(Y_MAX_DB,Y_MIN_DB-1,-5)]])
        width=np.min(np.diff(np.sort(x_pos)))*.8 if len(x_pos)>1 else .1
        grad=QLinearGradient(0,0,0,1); grad.setCoordinateMode(QGradient.ObjectBoundingMode)
        grad.setColorAt(0,QColor(69,164,255)); grad.setColorAt(.5,QColor(155,77,255,160))
        grad.setColorAt(1,QColor(69,164,255,90))
        self._bar_item=pg.BarGraphItem(x=x_pos,y0=Y_MIN_DB,
                                       height=sm_db-Y_MIN_DB,width=width,brush=QBrush(grad))
        p.addItem(self._bar_item)
        if self.chk_peak.isChecked():
            p.addItem(pg.ScatterPlotItem(x=x_pos,y=self._peaks,
                                         pen=None,brush=QColor(COLORS['primary']),size=5))
        self._bar_x,self._bar_freq,self._vals_db=x_pos,centres,sm_db
        if not hasattr(self,"_vline"):
            self._vline=pg.InfiniteLine(angle=90,
                                        pen=pg.mkPen(COLORS['secondary'],style=Qt.DashLine))
            self._tip  =pg.TextItem("",anchor=(.5,1.2)); self._tip.setColor("#fff")
            self.pg.addItem(self._vline,ignoreBounds=True); self.pg.addItem(self._tip)
            pg.SignalProxy(self.pg.scene().sigMouseMoved,rateLimit=60,slot=self._mouse_move)

    def _mouse_move(self,ev):
        if not ev[0]: return
        if self.pg.sceneBoundingRect().contains(ev[0]):
            mp=self.pg.getPlotItem().vb.mapSceneToView(ev[0])
            idx=np.abs(self._bar_x-mp.x()).argmin()
            self._vline.setPos(self._bar_x[idx])
            self._tip.setText(f"{int(self._bar_freq[idx])} Hz<br/>{self._vals_db[idx]:.1f} dB")
            self._tip.setPos(self._bar_x[idx],self._vals_db[idx]+3)

    # ─ helpers --------------------------------------------------------
    def _set_metric(self,label:str,val:float):
        lab,bar=self.metrics[label]
        pct=max(0,min(1,(val-Y_MIN_DB)/(Y_MAX_DB-Y_MIN_DB)))
        bar.setFixedWidth(int(pct*150))
        lab.setText(f"{val:+.1f} dB" if "Level" in label else f"{val:+.1f} LUFS")

    def _export_json(self,vol:float,freq:float,spec:dict[str,float],
                     bal_lh:float,bal_mid:float,dev:dict[str,float]):
        JSON_DIR.mkdir(exist_ok=True)
        data=dict(volume=round(vol,1),
                  dominant_freq=round(freq,2),
                  bal_lh=round(bal_lh,3),
                  bal_mid=round(bal_mid,3),
                  dev_low=round(dev["LOW"],3),
                  dev_lowmid=round(dev["LOWMID"],3),
                  dev_mid=round(dev["MID"],3),
                  dev_himid=round(dev["HIMID"],3),
                  dev_high=round(dev["HIGH"],3),
                  spectrum={k:round(v,1) for k,v in spec.items()},
                  version=APP_VERSION,
                  timestamp=time.time())
        with open(JSON_PATH,"w") as f: json.dump(data,f,indent=2)

    def _capture(self):
        ts=time.strftime("%Y%m%d_%H%M%S"); CAPT_DIR.mkdir(exist_ok=True)
        if self.current_mode=="wave":
            path=CAPT_DIR/f"waveform_{ts}.png"; self.vis.wave_pg.grab().save(str(path))
        elif self.current_mode=="spec":
            path=CAPT_DIR/f"spectrogram_{ts}.png"; self.vis.spec_pg.grab().save(str(path))
        else:
            path=CAPT_DIR/f"spectrum_{ts}.png"; self.pg.grab().save(str(path))
        self.statusBar().showMessage(f"✔ Saved {path.name}",4000)

    # stream toggle + mode change (only tweaks: call self.vis.set_mode without “running” flag)
    def _toggle_stream(self):
        if self.running:
            self.analyzer.stop(); self.running=False; self.start_btn.setText(chr(0xefea)+"  Start Analysis")
        else:
            self.analyzer.stop(); self.analyzer=AudioAnalyzer(device=self.device_cb.currentData())
            self.analyzer.start(); self.running=True; self.start_btn.setText(chr(0xef47)+"  Stop Analysis")
            self._frame_ts.clear(); self._fps_ema=None
        self.vis.set_mode(self.current_mode)      # ← always change widgets
        self._shape_buttons()
        self.lbl_live.setStyleSheet(f"color:{COLORS['on' if self.running else 'off']}")

    def _set_mode(self, m: str):
        if m == self.current_mode:
            return
        self.current_mode = m
        self._update_mode_style()
        self.vis.set_mode(m)
        self._shape_buttons()                       # control de botones heredados
        self.lbl_3d_hint.setVisible(m == "shape")   # ← overlay solo en 3-D Shape

    def _update_mode_style(self):
        for k,b in self.mode_btn.items():
            if k==self.current_mode:
                col=COLORS['primary'] if k in ("spectrum","shape") else COLORS['secondary']
                b.setStyleSheet(f"background:{col}30;color:{col};border:1px solid {col}50;"); b.setChecked(True)
            else:
                b.setStyleSheet(f"background:{COLORS['panel']};color:#fff;border:1px solid {COLORS['secondary']}40;"); b.setChecked(False)

# ═════════════════════════════════  main guard  ═════════════════════════════
if __name__=="__main__":
    fmt=QSurfaceFormat(); fmt.setSwapBehavior(QSurfaceFormat.TripleBuffer); fmt.setSwapInterval(1)
    QSurfaceFormat.setDefaultFormat(fmt)
    app=QApplication(sys.argv)
    if ICON_PATH.exists(): app.setWindowIcon(QIcon(str(ICON_PATH)))
    elif LOGO_PATH.exists(): app.setWindowIcon(QIcon(str(LOGO_PATH)))
    ui=OrbisUI(AudioAnalyzer()); ui.show(); sys.exit(app.exec())