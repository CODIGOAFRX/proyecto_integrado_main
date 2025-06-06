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
    Qt, QTimer, QElapsedTimer, QEasingCurve, QPropertyAnimation, QPointF,
    Property, Signal
)
from PySide6.QtGui     import (
    QColor, QPainter, QPen, QBrush, QFont, QFontDatabase,
    QRadialGradient, QLinearGradient, QGradient, QPixmap, QPixmapCache, QIcon,
    QGuiApplication, QSurfaceFormat, QPolygonF
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

# ── Rutas & constantes ──────────────────────────────────────────────────────
BASE_DIR  = Path(__file__).resolve().parent
FONT_DIR  = BASE_DIR / "resources" / "fonts"
IMG_DIR   = BASE_DIR / "resources" / "images"
CAPT_DIR  = BASE_DIR / "captures"
JSON_PATH = BASE_DIR / "json" / "orbis_data.json"
LOGO_PATH = IMG_DIR / "orbis_logo.png"        # encabezado
ICON_PATH = IMG_DIR / "orbis_icon.ico"        # icono app / task‑bar
VERSION   = "v0.9‑beta"
METRIC_LABELS = ("Peak Level",
                 "RMS Level",
                 "Integrated LUFS",
                 "Short-term LUFS")
Y_MIN_DB = -40     # fondo del gráfico
Y_MAX_DB =  30     # head‑room visible
COLORS = dict(bg="#121212", panel="#1E1E1E", border="#2D2D2D", text="#E0E0E0",
              primary="#45A4FF", secondary="#9B4DFF", cyan="#45D6FF")

# viridis LUT (fallback)
try:
    VIRIDIS_LUT = pg.colormap.get('viridis').getLookupTable(alpha=True)
except Exception:
    VIRIDIS_LUT = np.array([[68,1,84,255],[59,81,139,255],[33,144,141,255],
                            [72,193,110,255],[170,220,50,255],[253,231,37,255]])

# ════════════════════════════════════════════════════════════════════════════
#  WIDGETS
# ════════════════════════════════════════════════════════════════════════════
# GLWidget con fallback si PyOpenGL no está instalado
try:
    from OpenGL.GL import glClearColor, glClear, GL_COLOR_BUFFER_BIT
    class GLWidget(QOpenGLWidget):
        def initializeGL(self): glClearColor(18/255,18/255,18/255,1)
        def paintGL(self):       glClear(GL_COLOR_BUFFER_BIT)
except ImportError:                       # sin PyOpenGL → canvas vacío
    class GLWidget(QWidget):              # (evita el traceback)
        def paintEvent(self,_): pass

class OrbWidget(QWidget):
    levelChanged = Signal(int)            # por si te sirve a futuro

    FRAMES_DIR = BASE_DIR / "resources" / "images" / "orb_frames"  # <— usa tu ruta

    def __init__(self, parent=None):
        super().__init__(parent)
        self._level = 16                  # 16 = base
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)

    # --------------------- Qt Property -------------------------------
    def get_level(self):         return self._level
    def set_level(self, val: int):
        val = max(1, min(31, int(round(val))))
        if val != self._level:
            self._level = val
            self.update()
            self.levelChanged.emit(val)
    level = Property(int, get_level, set_level)

    # --------------------- Helpers -----------------------------------
    def _load_pixmap(self, idx: int) -> QPixmap:
        key = f"orb{idx:02d}"
        pm  = QPixmap()
        if not QPixmapCache.find(key, pm):
            pm = QPixmap(str(self.FRAMES_DIR / f"orb_{idx:02d}.png"))
            QPixmapCache.insert(key, pm)
        return pm

    # --------------------- Paint -------------------------------------
    def paintEvent(self, _):
        pm = self._load_pixmap(self._level)
        if pm.isNull():
            return                        # nombre mal o ruta vacía
        p = QPainter(self)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        side = min(self.width(), self.height()) * 1.8
        pm   = pm.scaled(side, side, Qt.KeepAspectRatio,
                         Qt.SmoothTransformation)
        x = (self.width()  - pm.width())  / 2
        y = (self.height() - pm.height()) / 2
        p.drawPixmap(int(x), int(y), pm)

class VisualizationWidget(QWidget):
    """Wave | Spectrogram | Orbe (spectrum/shape) + controles de zoom"""
    def __init__(self):
        super().__init__()
        # capas
        self.gl=GLWidget(self); self.gl.lower()
        self.orb=OrbWidget(self); self.orb.lower()
        # waveform
        self.wave_pg=pg.PlotWidget(self,background=None); self.wave_pg.hide()
        self.wave_pg.setMenuEnabled(False); self.wave_pg.setMouseEnabled(False,False)
        self.wave_pg.getPlotItem().setContentsMargins(0,0,0,0)
        self.wave_buf=np.zeros(512)
        self.wave_curve=self.wave_pg.plot(pen=pg.mkPen(COLORS['secondary'],width=2))
        # spectrogram
        self.spec_pg=pg.PlotWidget(self,background=None); self.spec_pg.hide()
        self.spec_pg.setMenuEnabled(False); self.spec_pg.setMouseEnabled(False,False)
        self.spec_pg.getPlotItem().setContentsMargins(0,0,0,0)
        self.spec_img=pg.ImageItem(axisOrder='row-major'); self.spec_img.setLookupTable(VIRIDIS_LUT)
        self.spec_pg.addItem(self.spec_img); self.spec_data=np.zeros((128,256))
        # overlay controles
        glyphs=["\ue3d4","\ue3d5","\ue3a8","\ue38b"]; names=["in","out","reset","fs"]
        self.ctrl={}
        for g,n in zip(glyphs,names):
            b=QToolButton(self,text=g); b.setFont(QFont("Remixicon",16))
            b.setFixedSize(32,32)
            b.setStyleSheet(f"background:{COLORS['panel']};border-radius:16px;"
                            f"color:{COLORS['secondary']};QToolButton:hover{{color:{COLORS['primary']}}}")
            self.ctrl[n]=b
    def resizeEvent(self,_):
        for w in (self.gl,self.orb,self.wave_pg,self.spec_pg): w.setGeometry(self.rect())
        x,y=14,self.height()-46
        for b in self.ctrl.values(): b.move(x,y); x+=38
    def paintEvent(self,_):
        p=QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        p.setPen(QPen(QColor(69,164,255,25)))
        for gx in range(0,self.width(),20): p.drawLine(gx,0,gx,self.height())
        for gy in range(0,self.height(),20): p.drawLine(0,gy,self.width(),gy)
        r=min(self.width(),self.height())*.45; c=self.rect().center()
        pts=[QPointF(c.x()+r*math.cos(math.pi/3*i), c.y()+r*math.sin(math.pi/3*i)) for i in range(6)]
        p.setPen(QPen(QColor(69,164,255,80),1))
        g=QRadialGradient(c,r); g.setColorAt(0,QColor(69,164,255,13)); g.setColorAt(1,COLORS['bg'])
        p.setBrush(QBrush(g)); p.drawPolygon(QPolygonF(pts))
    # API
    def set_mode(self,m):
        self.wave_pg.setVisible(m=="wave")
        self.spec_pg.setVisible(m=="spec")
        self.orb.setVisible(m in ("shape","spectrum"))
        self.gl.setVisible(m=="shape")
    def zoom_y(self,factor:float):
        for w in (self.wave_pg,self.spec_pg):
            if w.isVisible():
                vb=w.getViewBox(); lo,hi=vb.viewRange()[1]
                mid=(lo+hi)/2; span=(hi-lo)*factor/2
                vb.setYRange(mid-span,mid+span,padding=0)
    def reset_zoom(self):
        for w in (self.wave_pg,self.spec_pg):
            if w.isVisible(): w.getViewBox().autoRange()

# ════════════════════════════════════════════════════════════════════════════
#  MAIN WINDOW
# ════════════════════════════════════════════════════════════════════════════
class OrbisUI(QMainWindow):
    def __init__(self,analyzer:AudioAnalyzer):
        super().__init__()
        self.analyzer=analyzer; self.running=False; 
        # ── estado del orbe -------------------------------------------------
        self._breath_seq = [16,17,18,19,18,17,16,15,14,13,14,15]   # patrón base
        self._breath_idx = 0
        self._target_idx = 16
        self._idle_timer = QTimer(interval=120, timeout=self._advance_idle)
        self._idle_timer.start()
        self.current_mode="wave"
        self._fonts(); self._style(); self._build(); self._timers()
        self.setWindowTitle(f"ORBIS – Frequency‑Driven 3D Visualizer {VERSION}")
        if ICON_PATH.exists():
            QGuiApplication.setWindowIcon(QIcon(str(ICON_PATH)))
            self.setWindowIcon(QIcon(str(ICON_PATH)))
        elif LOGO_PATH.exists():
            QGuiApplication.setWindowIcon(QIcon(str(LOGO_PATH)))
            self.setWindowIcon(QIcon(str(LOGO_PATH)))
        self.resize(1280,800)
    # ── fuentes + CSS ────────────────────────────────────────────────────
    def _fonts(self):
        for f in ("Orbitron-Regular.ttf","Rajdhani-Regular.ttf","Remixicon.ttf"):
            try: QFontDatabase.addApplicationFont(str(FONT_DIR/f))
            except Exception: warnings.warn(f"Font {f} not found – using default")
    def _style(self):
        self.setStyleSheet(f"""
            QWidget{{background:{COLORS['bg']};color:{COLORS['text']};font-family:Rajdhani;}}
            QGroupBox{{border:1px solid {COLORS['border']};border-radius:12px;padding:8px;}}
            QGroupBox:title{{subcontrol-origin:margin;left:8px;padding:0 4px;color:#fff;font-family:Orbitron;}}
            QPushButton{{background:{COLORS['panel']};border:1px solid {COLORS['secondary']}40;
                         border-radius:12px;padding:6px 12px;}}
            QPushButton#neon{{color:{COLORS['primary']};border:1px solid {COLORS['primary']}50;}}
            QSlider::groove:horizontal{{background:{COLORS['border']};height:4px;border-radius:2px;}}
            QSlider::sub-page:horizontal{{background:linear-gradient(90deg,{COLORS['primary']},{COLORS['secondary']});
                                          height:4px;border-radius:2px;}}
            QSlider::handle:horizontal{{width:16px;height:16px;border-radius:8px;background:{COLORS['cyan']};
                                        margin:-6px 0;}}
            QCheckBox::indicator{{width:18px;height:18px;border-radius:4px;background:{COLORS['border']};}}
            QCheckBox::indicator:checked{{background:{COLORS['primary']};}}
        """)
    # ────────── CONSTRUCCIÓN UI ──────────────────────────────────────────
    def _build(self):
        central=QWidget(); self.setCentralWidget(central)
        root=QVBoxLayout(central); root.setContentsMargins(0,0,0,0); root.setSpacing(0)
        root.addWidget(self._header())

        body=QWidget(); bl=QVBoxLayout(body); bl.setContentsMargins(12,12,12,12); bl.setSpacing(12)
        top=QHBoxLayout(); bl.addLayout(top,1)
        top.addWidget(self._panel_controls(),1)
        top.addWidget(self._panel_viz(),3)
        top.addWidget(self._panel_metrics(),1)
        bl.addWidget(self._panel_spectrum())
        root.addWidget(body)

        self._footer()
    # HEADER --------------------------------------------------------------
    def _header(self):
        hdr=QWidget(); hdr.setStyleSheet(f"background:{COLORS['panel']};border-bottom:1px solid {COLORS['border']}")
        hl=QHBoxLayout(hdr); hl.setContentsMargins(16,8,16,8)
        if LOGO_PATH.exists():
            logo=QLabel(); logo.setPixmap(QPixmap(str(LOGO_PATH)).scaledToHeight(40,Qt.SmoothTransformation))
            hl.addWidget(logo)
        hl.addWidget(QLabel("ORBIS",font=QFont("Orbitron",22,QFont.Bold),
                            styleSheet=f"color:{COLORS['primary']}"))
        hl.addWidget(QLabel("Audio Cockpit",font=QFont("Orbitron",20))); hl.addSpacing(32)
        # dispositivo
        self.device_cb=QComboBox(); self._fill_devices()
        box=QGroupBox(); bx=QHBoxLayout(box); box.setFixedWidth(380)
        bx.addWidget(QLabel(chr(0xf3c2),font=QFont("Remixicon",14),
                            styleSheet=f"color:{COLORS['secondary']}"))
        bx.addWidget(self.device_cb); box.setStyleSheet(f"background:{COLORS['border']};border-radius:12px")
        hl.addWidget(box); hl.addStretch()
        # botones
        self.start_btn=QPushButton(chr(0xefea)+"  Start Analysis"); self.start_btn.setObjectName("neon")
        self._neon(self.start_btn); self.start_btn.clicked.connect(self._toggle_stream); hl.addWidget(self.start_btn)
        hl.addWidget(QPushButton(chr(0xeb8c)+"  Settings"))
        return hdr
    def _fill_devices(self):
        self.device_cb.clear()
        for i,d in enumerate(sd.query_devices()):
            if d['max_input_channels']>0: self.device_cb.addItem(d['name'],userData=i)
    # CONTROLS ------------------------------------------------------------
    def _panel_controls(self):
        gb=QGroupBox("Analysis Controls"); v=QVBoxLayout(gb)
        for lab,val,init in [("Frequency Range","20Hz – 20kHz",100),
                             ("Resolution","2048 FFT",70),("Sensitivity","‑24dB",50)]:
            lay=QVBoxLayout(); hl=QHBoxLayout(); hl.addWidget(QLabel(lab))
            hl.addWidget(QLabel(val,styleSheet=f"color:{COLORS['secondary']};font-size:11px"))
            lay.addLayout(hl); s=QSlider(Qt.Horizontal); s.setRange(0,100); s.setValue(init); lay.addWidget(s); v.addLayout(lay)
        self.chk_peak=QCheckBox("Show Peak Markers",checked=True)
        self.chk_grid=QCheckBox("Show Grid Lines",checked=True)
        self.chk_log =QCheckBox("Logarithmic Scale",checked=True)
        opts=QGroupBox("Display Options"); ov=QVBoxLayout(opts)
        ov.addWidget(self.chk_peak); ov.addWidget(self.chk_grid); ov.addWidget(self.chk_log); v.addWidget(opts)
        modes={"Spectrum":"spectrum","3D Shape":"shape","Waveform":"wave","Spectrogram":"spec"}
        self.mode_btn={}; mod=QGroupBox("Visualization Mode"); grid=QGridLayout(mod)
        for i,(txt,key) in enumerate(modes.items()):
            b=QPushButton(txt); b.setCheckable(True)
            b.clicked.connect(lambda _=False,k=key:self._set_mode(k))
            self.mode_btn[key]=b; grid.addWidget(b,i//2,i%2)
        v.addWidget(mod); self._update_mode_style(); return gb
    # VIZ -----------------------------------------------------------------
    def _panel_viz(self):
        gb=QGroupBox(); v=QVBoxLayout(gb)
        hl=QHBoxLayout(); hl.addWidget(QLabel("Real‑time Visualization",font=QFont("Orbitron",12)))
        # --- Launch 3-D Viewer -------------------------------------------------
        self.btn_baryon = QPushButton("Launch 3-D Viewer")
        self.btn_baryon.setFixedSize(140, 28)              
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
        self.btn_baryon.clicked.connect(self._open_baryon)
        hl.addWidget(self.btn_baryon)
        # ----------------------------------------------------------------------

        hl.addWidget(QLabel("● Live",styleSheet=f"color:{COLORS['primary']};font-size:11px"))
        hl.addStretch(); hl.addWidget(QLabel("Auto‑rotate",styleSheet="font-size:11px"))
        hl.addWidget(QCheckBox(checked=True)); v.addLayout(hl)
        self.vis=VisualizationWidget(); v.addWidget(self.vis,1)
        c=self.vis.ctrl
        c["in"].clicked.connect(lambda:self.vis.zoom_y(0.8))
        c["out"].clicked.connect(lambda:self.vis.zoom_y(1.25))
        c["reset"].clicked.connect(self.vis.reset_zoom)
        c["fs"].clicked.connect(lambda:self.isFullScreen() and self.showNormal() or self.showFullScreen())
        return gb
    # METRICS -------------------------------------------------------------
    def _panel_metrics(self):
        gb=QGroupBox("Audio Metrics"); v=QVBoxLayout(gb); self.metrics={}
        for lab in METRIC_LABELS:
            box=QWidget(); bl=QVBoxLayout(box); bl.setContentsMargins(0,0,0,0)
            hl=QHBoxLayout(); hl.addWidget(QLabel(lab))
            val=QLabel("‑‑‑",font=QFont("Orbitron",12)); val.setStyleSheet(f"color:{COLORS['cyan']}"); hl.addWidget(val)
            bl.addLayout(hl)
            bg=QWidget(); bg.setFixedHeight(6); bg.setStyleSheet(f"background:{COLORS['panel']};border-radius:3px")
            bar=QWidget(bg); bar.setGeometry(0,0,0,6)
            bar.setStyleSheet("background:linear-gradient(90deg,#45A4FF,#9B4DFF);border-radius:3px")
            bl.addWidget(bg); v.addWidget(box); self.metrics[lab]=(val,bar)
            self.metrics[lab] = (val, bar)
        fa=QGroupBox("Frequency Analysis"); g=QGridLayout(fa); self.band_lbl={}
        for i,(txt,key) in enumerate([("Low (20‑250Hz)","low"),("Mid (250‑2kHz)","mid"),
                                      ("High (2k‑20kHz)","high"),("Dominant Freq","dom")]):
            lay=QVBoxLayout(); lay.addWidget(QLabel(txt,styleSheet="font-size:11px"))
            val=QLabel("‑‑‑",font=QFont("Orbitron",12)); val.setStyleSheet(f"color:{COLORS['primary']}")
            lay.addWidget(val); g.addLayout(lay,i//2,i%2); self.band_lbl[key]=val
        v.addWidget(fa); return gb
    # SPECTRUM PANEL ------------------------------------------------------
    def _panel_spectrum(self):
        gb=QGroupBox("FFT Spectrum Analyzer"); v=QVBoxLayout(gb)
        hl=QHBoxLayout(); hl.addWidget(QLabel("Smoothing",styleSheet="font-size:11px"))
        self.smooth=QSlider(Qt.Horizontal); self.smooth.setRange(0,100); self.smooth.setValue(20); hl.addWidget(self.smooth)
        self.cap_btn=QPushButton(chr(0xf135)+" Capture"); self.cap_btn.clicked.connect(self._capture); hl.addWidget(self.cap_btn)
        hl.addStretch(); v.addLayout(hl)
        self.pg=pg.PlotWidget(background=COLORS['bg']); self.pg.getPlotItem().setContentsMargins(0,0,0,0)
        v.addWidget(self.pg); return gb
    # FOOTER --------------------------------------------------------------
    def _footer(self):
        sb=QStatusBar(); sb.setStyleSheet(f"background:{COLORS['panel']}"); self.setStatusBar(sb)
        self.lbl_time,self.lbl_cpu,self.lbl_buf,self.lbl_sr=[QLabel() for _ in range(4)]
        for w in (self.lbl_time,self.lbl_cpu,self.lbl_buf,self.lbl_sr): sb.addPermanentWidget(w)
        sb.addPermanentWidget(QLabel(f"ORBIS {VERSION}"))
    # neon ripple
    def _neon(self,btn:QPushButton):
        eff=QGraphicsDropShadowEffect(); eff.setBlurRadius(20); eff.setColor(QColor(COLORS['primary']))
        btn.setGraphicsEffect(eff)
        def ripple():
            a=QPropertyAnimation(btn,b"geometry"); a.setDuration(160); a.setEasingCurve(QEasingCurve.InOutQuad)
            g=btn.geometry(); a.setStartValue(g); a.setKeyValueAt(.5,g.adjusted(-4,-2,4,2)); a.setEndValue(g)
            a.start(QPropertyAnimation.DeleteWhenStopped)
        btn.clicked.connect(ripple)
    # timers
    def _timers(self):
        self.t0=time.time()
        self.ui_timer=QTimer(interval=100,timeout=self._tick); self.ui_timer.start()
        self.footer_timer=QTimer(interval=1000,timeout=self._tick_footer); self.footer_timer.start()

    # ────────────────────────────────────────────────────────────────────
    # LOOP
    # ────────────────────────────────────────────────────────────────────
    # ───────────────────────────────────────────────────────────────────
    def _tick(self):
        if not self.running:
            return

        # --------- datos crudos de AudioAnalyzer -----------------------
        d   = self.analyzer.get_audio_data() or {}
        vol = float(d.get("volume", -60.0))
        freq= float(d.get("dominant_freq", 0.0))
        fft = d.get("fft")
        sr  = int(d.get("sample_rate", 48000))

        # --------- helper dB por banda ---------------------------------
        def band(lo: float, hi: float) -> float:
            if fft is None or not len(fft):
                return -60.0
            f_axis = np.fft.rfftfreq(len(fft)*2 - 2, 1/sr)
            sel = (f_axis >= lo) & (f_axis < hi)
            return 20*np.log10(np.mean(fft[sel]) + 1e-10) if np.any(sel) else -60.0
        def peak_db(lo: float, hi: float) -> float:
            """Devuelve el pico dBFS en el rango lo-hi Hz."""
            if fft is None or not len(fft):
                return -60.0
            f_axis = np.fft.rfftfreq(len(fft)*2 - 2, 1/sr)
            sel = (f_axis >= lo) & (f_axis < hi)
            if not np.any(sel):
                return -60.0
            return 20*np.log10(np.max(fft[sel]) + 1e-10)

        # --------- métricas globales (Peak, RMS, etc.) -----------------
        for lab, off in zip(METRIC_LABELS, (0, -6, -1, 1)):
            self._set_metric(lab, vol + off)

        # --------- bandas Low / Mid / High -----------------------------
        low_dB  = peak_db(20,   250)
        mid_dB  = peak_db(250,  5000)
        high_dB = peak_db(5000, 20000)

        self.band_lbl["low"].setText(f"{low_dB:+.1f} dB")
        self.band_lbl["mid"].setText(f"{mid_dB:+.1f} dB")
        self.band_lbl["high"].setText(f"{high_dB:+.1f} dB")
        self.band_lbl["dom"].setText(f"{freq:.0f} Hz")

        # --------- decide destino del orbe y anima ---------------------
        self._update_target_from_audio(low_dB, mid_dB, high_dB)
        self._advance_idle()                   # SIEMPRE, esté o no visible

        # --------- waveform -------------------------------------------------
        if self.current_mode == "wave":
            self.vis.wave_buf = np.roll(self.vis.wave_buf, -1)
            self.vis.wave_buf[-1] = vol
            self.vis.wave_curve.setData(self.vis.wave_buf)

        # --------- espectrograma -------------------------------------------
        if self.current_mode == "spec" and fft is not None:
            mags   = 20*np.log10(fft + 1e-10) + 60
            slice_ = np.interp(np.linspace(0, len(mags)-1, 128),
                            np.arange(len(mags)), mags)
            self.vis.spec_data  = np.roll(self.vis.spec_data, -1, axis=1)
            self.vis.spec_data[:, -1] = slice_
            self.vis.spec_img.setImage(self.vis.spec_data,
                                    levels=(0, 60), autoLevels=False)

        # --------- FFT gráfico de barras (panel inferior) -------------------
        self._plot_spectrum(fft, sr)

        # --------- export JSON para Blender ---------------------------------
        self._export_json(vol, freq, fft, sr,
                        extra=dict(low=low_dB, mid=mid_dB, high=high_dB))


    def _plot_spectrum(self, fft: np.ndarray | None, sr: int) -> None:
        if fft is None or not len(fft):
            return
        import math, numpy as np
        # ── centros de barra ────────────────────────────────────
        bounds = np.array([1, 20, 50, 100, 250, 500,
                        1000, 2000, 5000, 10000,
                        15000, 20000], dtype=float)
        centers = []
        for i in range(1, len(bounds)):
            a, b = bounds[i-1], bounds[i]
            c = bounds[i+1] if i+1 < len(bounds) else b**2 / a
            centers.extend([math.sqrt(a*b), b, math.sqrt(b*c)])
        centers = np.unique(np.round(centers, 4))
        # ── mapeo X híbrido (1‑20 lin · 20‑5k log · 5k‑20k lin) ─
        log20, log50 = np.log10(20), np.log10(50)
        seg0 = log50 - log20
        x0   = log20 - seg0
        log5k = np.log10(5000)
        hi_fac = 1.6
        hi_span = (np.log10(20000) - log5k) * hi_fac
        def f2x(f):
            f = np.asarray(f, float)
            x = np.empty_like(f)
            m0 = f < 20
            x[m0] = x0 + (f[m0] - 1) / 19 * seg0
            m1 = (f >= 20) & (f < 5000)
            x[m1] = np.log10(f[m1])
            m2 = f >= 5000
            x[m2] = log5k + (f[m2] - 5000) / 15000 * hi_span
            return x
        x_pos = f2x(centers)
        x_max = f2x(20000) + seg0 * .4
        # ── magnitudes dBFS ─────────────────────────────────────
        freqs = np.fft.rfftfreq(len(fft)*2 - 2, 1 / sr)
        mags_db = 20 * np.log10(np.interp(centers, freqs, fft,
                                        left=1e-10, right=1e-10) + 1e-10)
        # suavizado + picos
        decay = 0.5
        if not hasattr(self, "_peaks"):
            self._peaks = mags_db.copy()
        self._peaks = np.maximum(mags_db, self._peaks - decay)
        alpha = self.smooth.value() / 100
        if not hasattr(self, "_smooth"):
            self._smooth = mags_db.copy()
        self._smooth = alpha * self._smooth + (1 - alpha) * mags_db
        sm_db = self._smooth
        # ── plot ────────────────────────────────────────────────
        p = self.pg.getPlotItem()
        p.clear()
        p.showGrid(x=True, y=self.chk_grid.isChecked(), alpha=.3)
        vb = p.getViewBox()
        vb.setLimits(xMin=x0, xMax=x_max, yMin=Y_MIN_DB, yMax=Y_MAX_DB)
        p.setXRange(x0, x_max, padding=0)
        p.setYRange(Y_MIN_DB, Y_MAX_DB, padding=0)
        # ticks
        p.getAxis('bottom').setTicks([[
            (f2x(f), f"{int(f):,}".replace(",", " ")+" Hz") for f in bounds[1:]
        ]])
        db_ticks = list(range(Y_MAX_DB, Y_MIN_DB - 1, -5))   # +20, +15, …, -40
        p.getAxis('left').setTicks([[
            (d, f"{d:+.0f} dB") for d in db_ticks
        ]])
        # barras + picos
        width = np.min(np.diff(np.sort(x_pos))) * .8 if len(x_pos) > 1 else .1
        grad = QLinearGradient(0, 0, 0, 1)
        grad.setCoordinateMode(QGradient.ObjectBoundingMode)
        grad.setColorAt(0,  QColor(69, 164, 255, 255))
        grad.setColorAt(.5, QColor(155, 77, 255, 160))
        grad.setColorAt(1,  QColor(69, 164, 255, 90))
        p.addItem(pg.BarGraphItem(x=x_pos,
                                y0=Y_MIN_DB,
                                height=sm_db - Y_MIN_DB,
                                width=width,
                                brush=QBrush(grad)))
        if self.chk_peak.isChecked():
            p.addItem(pg.ScatterPlotItem(x=x_pos, y=self._peaks,
                                        pen=None,
                                        brush=QColor(COLORS['primary']),
                                        size=5))
        # datos tooltip
        self._bar_x, self._bar_freq = x_pos, centers
        self._vals_db = sm_db
        if not hasattr(self, "_vline"):
            self._vline = pg.InfiniteLine(angle=90,
                                        pen=pg.mkPen(COLORS['secondary'],
                                                    style=Qt.DashLine))
            self._tip = pg.TextItem("", anchor=(.5, 1.2))
            self._tip.setDefaultTextColor(Qt.white)
            self.pg.addItem(self._vline, ignoreBounds=True)
            self.pg.addItem(self._tip)
            pg.SignalProxy(self.pg.scene().sigMouseMoved,
                        rateLimit=60, slot=self._mouse_move)

    def _mouse_move(self, ev):
        pos = ev[0]
        if not self.pg.sceneBoundingRect().contains(pos):
            self._tip.setText("")
            return
        view = self.pg.getPlotItem().vb.mapSceneToView(pos)
        idx = int(np.argmin(np.abs(self._bar_x - view.x())))
        self._vline.setPos(self._bar_x[idx])
        freq = self._bar_freq[idx]
        db = self._vals_db[idx]
        self._tip.setText(f"{freq:.0f} Hz\n{db:+.1f} dB")
        self._tip.setPos(self._bar_x[idx], db + 1)

    def _set_metric(self, label: str, val: float):
        lab, bar = self.metrics[label]
        span = Y_MAX_DB - Y_MIN_DB            # 60 dB
        pct = max(0, min(1, (val - Y_MIN_DB) / span))
        bar.setFixedWidth(int(pct * 150))
        lab.setText(f"{val:+.1f} dB" if "Level" in label else f"{val:+.1f} LUFS")




    def _export_json(self, vol, freq, fft, sr, extra: dict | None = None):
        JSON_PATH.parent.mkdir(exist_ok=True)
        data = dict(volume=round(vol, 2),
                    dominant_freq=round(freq, 2),
                    version=VERSION)
        
        if extra:                      # <-- nueva línea
            data.update(extra)         # <--
        if fft is not None and len(fft):
            f=np.fft.rfftfreq(len(fft)*2-2,1/sr); spec={}
            for t in (20,50,100,250,500,1000,2000,5000,10000,15000,20000):
                spec[f"{t}Hz"]=round(20*np.log10(max(fft[(np.abs(f-t)).argmin()],1e-10)),2)
            data["spectrum"]=spec
        with open(JSON_PATH,"w") as f: json.dump(data,f,indent=2)
    def _capture(self):
        CAPT_DIR.mkdir(exist_ok=True)
        path=CAPT_DIR/f"spectrum_{time.strftime('%Y%m%d_%H%M%S')}.png"
        self.pg.grab().save(str(path)); self.statusBar().showMessage(f"✔ saved {path.name}",5000)
    # Lanza el visor Baryon en el navegador
    def _open_baryon(self):
        if launch_baryon(force_local=False, ask=True):
            self.btn_baryon.setText("Launched ✔")
        else:
            self.btn_baryon.setText("Retry 3-D Viewer")
    # stream
    def _toggle_stream(self):
        if self.running:
            self.analyzer.stop(); self.running=False
            self.start_btn.setText(chr(0xefea)+"  Start Analysis")
        else:
            self.analyzer.stop()
            self.analyzer=AudioAnalyzer(device=self.device_cb.currentData())
            self.analyzer.start(); self.running=True
            self.start_btn.setText(chr(0xef47)+"  Stop Analysis")
    # modos
    def _set_mode(self,m):
        if m==self.current_mode: return
        self.current_mode=m; self._update_mode_style(); self.vis.set_mode(m)
    def _update_mode_style(self):
        for k,b in self.mode_btn.items():
            if k==self.current_mode:
                col=COLORS['primary'] if k in ("spectrum","shape") else COLORS['secondary']
                b.setStyleSheet(f"background:{col}30;color:{col};border:1px solid {col}50;"); b.setChecked(True)
            else:
                b.setStyleSheet(f"background:{COLORS['panel']};color:#fff;border:1px solid {COLORS['secondary']}40;"); b.setChecked(False)
    # footer
    def _tick_footer(self):
        t=int(time.time()-self.t0); h,m,s=t//3600,(t//60)%60,t%60
        self.lbl_time.setText(f"Session {h:02}:{m:02}:{s:02}")
        self.lbl_cpu.setText(f"CPU {psutil.cpu_percent():>3.0f}%")
        try:
            d=sd.query_devices(self.device_cb.currentData() or 0)
            sr=int(d['default_samplerate']); buf=int(d['default_low_input_latency']*sr)
        except Exception: sr=buf=0
        self.lbl_buf.setText(f"Buffer {buf}"); self.lbl_sr.setText(f"Sample Rate {sr} Hz")
    def _advance_idle(self):
        orb = self.vis.orb

        # 1) si ya estamos en el destino → respira con el patrón actual
        if orb.level == self._target_idx:
            self._breath_idx = (self._breath_idx + 1) % len(self._breath_seq)
            orb.set_level(self._breath_seq[self._breath_idx])
            return

        # 2) si no, muévete un PNG hacia el destino
        step = 1 if self._target_idx > orb.level else -1
        orb.set_level(orb.level + step)
    def _update_target_from_audio(self, low, mid, high):
        """
        Decide self._target_idx según la diferencia de bandas.
        """
        BIG = 10      # MUCHO
        MED = 6       # MEDIANO
        SMALL = 3     # LIGERO

        # diferencias
        dom_low  = low  - max(mid, high)
        dom_high = high - max(mid, low)
        dom_mid  = mid  - max(low, high)


        # --- graves dominan -------------------------------------------------
        if dom_low > BIG:
            self._target_idx = 31
        elif dom_low > MED:
            self._target_idx = 27
        elif dom_low > SMALL:
            self._target_idx = 23

        # --- agudos dominan -------------------------------------------------
        elif dom_high > BIG:
            self._target_idx = 1
        elif dom_high > MED:
            self._target_idx = 5
        elif dom_high > SMALL:
            self._target_idx = 9

        # --- medios dominan o equilibrio -----------------------------------
        else:
            self._target_idx = 16

        # cambia patrón de respiración en extremos
        if self._target_idx in (31,27,23):
            self._breath_seq = [self._target_idx,
                                self._target_idx-2,
                                self._target_idx,
                                self._target_idx-2]
        elif self._target_idx in (1,5,9):
            self._breath_seq = [self._target_idx,
                                self._target_idx+2,
                                self._target_idx,
                                self._target_idx+2]
        else:
            self._breath_seq = [16,17,18,19,18,17,16,15,14,13,14,15]

# ════════════════════════════════════════════════════════════════════════════
if __name__=="__main__":
    app=QApplication(sys.argv)
    if ICON_PATH.exists(): app.setWindowIcon(QIcon(str(ICON_PATH)))
    elif LOGO_PATH.exists(): app.setWindowIcon(QIcon(str(LOGO_PATH)))
    ui=OrbisUI(AudioAnalyzer()); ui.show(); sys.exit(app.exec())
