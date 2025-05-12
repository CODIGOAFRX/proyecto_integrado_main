# orbis_ui.py — ORBIS v1.0‑beta
# ---------------------------------------------------------------------------
# Stand‑alone PySide 6 UI for the ORBIS – Frequency‑Driven 3D Visualizer.
#
# What’s new in this revision
#   • Overlay buttons wired → zoom‑in / zoom‑out / reset / fullscreen
#   • `capture_spectrum()` saves timestamped PNGs to ./captures/
#   • Updated window title, footer text, logo in header & app icon
#   • Spectrum Y‑axis zoom logic with sensible defaults (0 – 60 dB)
#
# Requires:
#   • audio_analyzer.py  (backend)
#   • resources/fonts/{Rajdhani‑Regular.ttf, Orbitron‑Regular.ttf, Remixicon.ttf}
#   • resources/images/orbis_logo.png         (32 px+ logo)
#
# Tested: Python 3.11 • PySide 6.6.1 • Windows 11 23H2
# ---------------------------------------------------------------------------

from __future__ import annotations

import sys, math, json, time
from pathlib import Path
from typing import Dict, Tuple, List, Any

import numpy as np
import psutil
import sounddevice as sd

# ------------- Qt / PySide ------------
from PySide6.QtCore    import Qt, QTimer, QPointF
from PySide6.QtGui     import (QColor, QPainter, QPen, QBrush, QFont, QFontDatabase,
                               QRadialGradient, QLinearGradient, QPolygonF, QGradient,
                               QPixmap, QIcon)
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                               QLabel, QPushButton, QComboBox, QSlider, QCheckBox, QGroupBox, QStatusBar,
                               QToolButton, QGraphicsDropShadowEffect)
from PySide6.QtOpenGLWidgets import QOpenGLWidget

# pyqtgraph autodetects PySide6
import pyqtgraph as pg

from audio_analyzer import AudioAnalyzer         # live audio backend

# ------------- resources --------------
BASE_DIR      = Path(__file__).resolve().parent
FONT_DIR      = BASE_DIR / "resources" / "fonts"
JSON_PATH     = BASE_DIR / "json" / "orbis_data.json"
LOGO_PATH     = BASE_DIR / "resources" / "images" / "orbis_logo.png"
CAPTURES_DIR  = BASE_DIR / "captures"

# ------------- design tokens ----------
PRIMARY   = "#00FF41"
SECONDARY = "#40E0D0"
BG        = "#121212"
PANEL     = "#1E1E1E"
BORDER    = "#2D2D2D"
TEXT      = "#e0e0e0"
ACCENT    = SECONDARY

# =========================================================================== #
# Helper widgets
# =========================================================================== #
class GLWidget(QOpenGLWidget):
    """Minimal OpenGL viewport – ready for Blender texture frames."""
    def initializeGL(self): glClearColor(18/255, 18/255, 18/255, 1)
    def paintGL(self):       glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

class VisualizationWidget(QWidget):
    """
    Main visual canvas: background grid + hexagon layers, OpenGL viewport,
    and overlay control buttons.
    """
    def __init__(self) -> None:
        super().__init__()
        self._gl = GLWidget(self)
        self._gl.lower()                                        # keep behind decorations

        # ─── overlay buttons ────────────────────────────────────────────────
        glyphs = ["\ue3d4", "\ue3d5", "\ue3a8", "\ue38b"]       # zoom‑in/out, reset, fullscreen
        names  = ["zoom_in", "zoom_out", "reset_zoom", "fullscreen"]

        self.controls: Dict[str, QToolButton] = {}
        self._buttons: List[QToolButton] = []

        for g, n in zip(glyphs, names):
            b = QToolButton(self)
            b.setText(g)
            b.setFont(QFont("Remixicon", 16))
            b.setFixedSize(32, 32)
            b.setStyleSheet(f"background:{PANEL};border-radius:16px")
            self._buttons.append(b)
            self.controls[n] = b

    # overlay layout
    def resizeEvent(self, _) -> None:
        self._gl.setGeometry(self.rect())
        x, y = 10, self.height() - 42
        for b in self._buttons:
            b.move(x, y)
            x += 37

    # decorative background
    def paintEvent(self, _) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = self.rect()

        # grid
        p.setPen(QPen(QColor(64, 224, 208, 25), 1))
        for gx in range(0, r.width(), 20):  p.drawLine(gx, 0, gx, r.height())
        for gy in range(0, r.height(), 20): p.drawLine(0, gy, r.width(), gy)

        # concentric hexagons
        c   = r.center()
        rad = min(r.width(), r.height()) * 0.25
        pts = [QPointF(c.x() + rad * math.cos(math.radians(60*i)),
                       c.y() + rad * math.sin(math.radians(60*i))) for i in range(6)]

        p.setPen(QPen(QColor(64, 224, 208, 51), 1))
        outer = QRadialGradient(c, rad)
        outer.setColorAt(0, QColor(0, 255, 65, 13))
        outer.setColorAt(1, QColor(18, 18, 18))
        p.setBrush(QBrush(outer))
        p.drawPolygon(QPolygonF(pts))

        for fac, alpha in [(0.75, 26), (0.4, 51)]:
            rr = rad * fac
            g  = QRadialGradient(c, rr)
            g.setColorAt(0, QColor(0, 255, 255, alpha) if fac == 0.75 else QColor(0, 255, 65, alpha))
            g.setColorAt(1, QColor(18, 18, 18))
            p.setBrush(QBrush(g))
            p.setPen(Qt.NoPen)
            p.drawEllipse(c, rr, rr)

# =========================================================================== #
# Main window
# =========================================================================== #
class OrbisAudioCockpit(QMainWindow):
    def __init__(self, analyzer: AudioAnalyzer) -> None:
        super().__init__()
        self.analyzer = analyzer                  # live backend
        self.running  = False

        self.setWindowTitle("ORBIS – Frequency‑Driven 3D Visualizer")
        if LOGO_PATH.exists():
            self.setWindowIcon(QIcon(str(LOGO_PATH)))
        self.resize(1280, 800)

        self._apply_styles()
        self._build_ui()
        self._init_timers()

    # ------------------------------------------------------------------ UI --
    def _apply_styles(self) -> None:
        # Register custom fonts once (safe to call multiple times)
        QFontDatabase.addApplicationFont(str(FONT_DIR / "Orbitron-Regular.ttf"))
        QFontDatabase.addApplicationFont(str(FONT_DIR / "Rajdhani-Regular.ttf"))
        QFontDatabase.addApplicationFont(str(FONT_DIR / "Remixicon.ttf"))

        self.setStyleSheet(f"""
            QWidget {{background:{BG};color:{TEXT};font-family:Rajdhani, sans-serif;}}
            QPushButton {{background:{PANEL};border:1px solid rgba(64,224,208,3);
                          border-radius:12px;padding:6px;}}
            QPushButton#neon {{border:1px solid {PRIMARY};color:{PRIMARY};}}

            QComboBox {{background:transparent;border:none;
              background-image:url(data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24'
              viewBox='0 0 24 24' fill='none' stroke='%2340E0D0' stroke-width='2' stroke-linecap='round'
              stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E);
              background-repeat:no-repeat;background-position:right 8px center;}}

            QSlider::groove:horizontal {{height:4px;border-radius:5px;
              background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #1e293b,stop:1 {ACCENT});}}
            QSlider::handle:horizontal {{width:16px;height:16px;border-radius:8px;background:#00FFFF;margin:-6px 0;}}

            QCheckBox::indicator {{width:18px;height:18px;border-radius:4px;background:#2D2D2D;}}
            QCheckBox::indicator:checked {{background:{PRIMARY};}}
            QCheckBox#switch::indicator {{width:48px;height:24px;border-radius:12px;background:#2D2D2D;}}
            QCheckBox#switch::indicator:checked {{background:{PRIMARY};}}
        """)

    # ---- build whole hierarchy -------------------------------------------
    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        root_v  = QVBoxLayout(central)
        root_v.setContentsMargins(0, 0, 0, 0)
        root_v.setSpacing(0)

        # header
        root_v.addWidget(self._build_header())

        # body
        body   = QWidget()
        body_v = QVBoxLayout(body)
        body_v.setContentsMargins(12, 12, 12, 12)
        body_v.setSpacing(12)
        body_v.addLayout(self._build_top_panels(), 1)
        body_v.addWidget(self._build_spectrum_panel())
        root_v.addWidget(body)

        # footer / status bar
        self._build_footer()

    # -------- header -------------------------------------------------------
    def _build_header(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet(f"background:{PANEL};border-bottom:1px solid {BORDER}")
        l = QHBoxLayout(w)
        l.setContentsMargins(16, 8, 16, 8)

        # logo + title
        if LOGO_PATH.exists():
            logo_lbl = QLabel()
            logo_lbl.setPixmap(QPixmap(str(LOGO_PATH)).scaledToHeight(32, Qt.SmoothTransformation))
            l.addWidget(logo_lbl)

        title = QLabel("ORBIS – Frequency‑Driven 3D Visualizer")
        title.setFont(QFont("Orbitron", 20, QFont.Bold))
        l.addWidget(title)
        l.addSpacing(20)

        # device selector
        dev_box = QGroupBox()
        dev_box.setStyleSheet(f"background:{BORDER};border-radius:12px")
        dev_l   = QHBoxLayout(dev_box)
        dev_l.setContentsMargins(8, 4, 8, 4)
        icon = QLabel(chr(0xf3c2))
        icon.setFont(QFont("Remixicon", 12))
        icon.setStyleSheet(f"color:{SECONDARY}")
        dev_l.addWidget(icon)
        self.device_combo = QComboBox()
        self._populate_devices()
        dev_l.addWidget(self.device_combo)
        l.addWidget(dev_box)

        l.addStretch()

        self.start_btn = QPushButton("Start Analysis")
        self.start_btn.setObjectName("neon")
        glow = QGraphicsDropShadowEffect()
        glow.setColor(QColor(PRIMARY))
        glow.setBlurRadius(15)
        self.start_btn.setGraphicsEffect(glow)
        self.start_btn.clicked.connect(self._toggle_analysis)
        l.addWidget(self.start_btn)

        l.addWidget(QPushButton("Settings"))
        return w

    def _populate_devices(self) -> None:
        self.device_combo.clear()
        devs = sd.query_devices()
        self.input_map = [(idx, d['name']) for idx, d in enumerate(devs) if d['max_input_channels'] > 0]
        for idx, name in self.input_map:
            self.device_combo.addItem(name, userData=idx)

    # -------- top panels ---------------------------------------------------
    def _build_top_panels(self) -> QHBoxLayout:
        hl = QHBoxLayout()
        hl.setSpacing(12)
        hl.addWidget(self._controls_panel(),      1)
        hl.addWidget(self._visualization_panel(), 3)
        hl.addWidget(self._metrics_panel(),       1)
        return hl

    # -- left controls ------------------------------------------------------
    def _controls_panel(self) -> QGroupBox:
        gb = QGroupBox("Analysis Controls")
        gb.setFont(QFont("Orbitron", 12))
        gb.setStyleSheet(f"QGroupBox{{background:{PANEL};border:1px solid {BORDER};"
                         f"border-radius:12px;color:white}}")
        v = QVBoxLayout(gb)

        v.addLayout(self._slider_row("Frequency Range", "20 Hz – 20 kHz", 100))
        v.addLayout(self._slider_row("Resolution",      "2048 FFT",      70))
        v.addLayout(self._slider_row("Sensitivity",     "‑24 dB",        50))
        v.addWidget(self._checkbox_group("Display Options",
                                         ["Show Peak Markers", "Show Grid Lines", "Logarithmic Scale"]))
        v.addWidget(self._button_grid("Visualization Mode",
                                      ["Spectrum", "3D Shape", "Waveform", "Spectrogram"]))
        return gb

    def _slider_row(self, label: str, val: str, init: int) -> QVBoxLayout:
        lay = QVBoxLayout()
        top = QHBoxLayout()
        top.addWidget(QLabel(label))
        val_lbl = QLabel(val)
        val_lbl.setStyleSheet(f"color:{ACCENT};font-size:10px")
        top.addWidget(val_lbl)
        lay.addLayout(top)
        s = QSlider(Qt.Horizontal)
        s.setRange(0, 100)
        s.setValue(init)
        lay.addWidget(s)
        return lay

    def _checkbox_group(self, title: str, items: List[str]) -> QGroupBox:
        gb = QGroupBox(title)
        gb.setStyleSheet("QGroupBox{border:none;color:white}")
        v = QVBoxLayout(gb)
        for it in items:
            cb = QCheckBox(it)
            cb.setChecked(True)
            v.addWidget(cb)
        return gb

    def _button_grid(self, title: str, items: List[str]) -> QGroupBox:
        gb = QGroupBox(title)
        grid = QGridLayout(gb)
        for i, it in enumerate(items):
            grid.addWidget(QPushButton(it), i // 2, i % 2)
        return gb

    # -- centre visualisation ----------------------------------------------
    def _visualization_panel(self) -> QGroupBox:
        gb = QGroupBox()
        gb.setStyleSheet(f"background:{PANEL};border:1px solid {BORDER};border-radius:12px")
        v  = QVBoxLayout(gb)

        head = QHBoxLayout()
        head.addWidget(QLabel("Real‑time Visualization"))
        live = QLabel("● Live")
        live.setStyleSheet(f"color:{PRIMARY};font-size:10px")
        head.addWidget(live)
        head.addStretch()
        ar = QCheckBox("Auto‑rotate")
        ar.setObjectName("switch")
        ar.setChecked(True)
        head.addWidget(ar)
        v.addLayout(head)

        self.vis_widget = VisualizationWidget()
        v.addWidget(self.vis_widget, 1)

        # connect overlay buttons *after* widget exists
        self._wire_overlay_buttons()
        return gb

    # -- right‑hand metrics -------------------------------------------------
    def _metrics_panel(self) -> QGroupBox:
        gb = QGroupBox("Audio Metrics")
        gb.setFont(QFont("Orbitron", 12))
        gb.setStyleSheet(f"QGroupBox{{background:{PANEL};border:1px solid {BORDER};"
                         f"border-radius:12px;color:white}}")
        v = QVBoxLayout(gb)

        self.metric_widgets: Dict[str, Tuple[QLabel, QWidget]] = {}
        for name in ["Peak Level", "RMS Level", "Integrated LUFS", "Short‑term LUFS"]:
            box  = QWidget()
            bv   = QVBoxLayout(box)
            bv.setContentsMargins(0, 0, 0, 0)
            top  = QHBoxLayout()
            top.addWidget(QLabel(name))
            val = QLabel("‑‑‑")
            val.setFont(QFont("Orbitron", 12))
            val.setStyleSheet("color:#00FFFF")
            top.addWidget(val)
            bv.addLayout(top)
            bar_bg = QWidget()
            bar_bg.setFixedHeight(6)
            bar_bg.setStyleSheet("background:#1E1E1E;border-radius:3px")
            bar = QWidget(bar_bg)
            bar.setGeometry(0, 0, 0, 6)
            bar.setStyleSheet("background:linear-gradient(90deg,#00FF41,#40E0D0);border-radius:3px")
            bv.addWidget(bar_bg)
            v.addWidget(box)
            self.metric_widgets[name] = (val, bar)

        # band‑energy & dominant frequency read‑out
        grid = QGridLayout()
        self.freq_labels: Dict[str, QLabel] = {}
        for idx, (lab, key) in enumerate([
            ("Low (20‑250 Hz)",      "low"),
            ("Mid (250‑2 kHz)",     "mid"),
            ("High (2 k‑20 kHz)",   "high"),
            ("Dominant Freq",       "dom")
        ]):
            cell = QVBoxLayout()
            l1   = QLabel(lab)
            l2   = QLabel("‑‑‑")
            l2.setStyleSheet(f"color:{PRIMARY};font-family:Orbitron")
            cell.addWidget(l1)
            cell.addWidget(l2)
            grid.addLayout(cell, idx // 2, idx % 2)
            self.freq_labels[key] = l2

        v.addLayout(grid)
        return gb

    # -- bottom spectrum panel ---------------------------------------------
    def _build_spectrum_panel(self) -> QGroupBox:
        gb = QGroupBox("FFT Spectrum Analyzer")
        gb.setStyleSheet(f"QGroupBox{{background:{PANEL};border:1px solid {BORDER};"
                         f"border-radius:12px;color:white}}")
        v = QVBoxLayout(gb)

        # controls row ------------------------------------------------------
        ctrl = QHBoxLayout()
        ctrl.addWidget(QLabel("Smoothing"))
        self.smooth_slider = QSlider(Qt.Horizontal)
        self.smooth_slider.setRange(0, 100)
        self.smooth_slider.setValue(30)
        ctrl.addWidget(self.smooth_slider)

        self.capture_btn = QPushButton("Capture")
        ctrl.addWidget(self.capture_btn)
        ctrl.addStretch()
        v.addLayout(ctrl)

        # pgPlotWidget ------------------------------------------------------
        self.pg = pg.PlotWidget()
        self.pg.setBackground(BG)

        self._default_y_range  = (0, 60)      # 0 → 60 dB visible
        self._current_y_range  = self._default_y_range
        self.pg.setYRange(*self._default_y_range)

        v.addWidget(self.pg)

        # wire screenshot button now pg exists
        self.capture_btn.clicked.connect(self.capture_spectrum)
        return gb

    # -------- footer / status bar -----------------------------------------
    def _build_footer(self) -> None:
        sb = QStatusBar()
        sb.setStyleSheet(f"background:{PANEL};color:{TEXT}")
        self.setStatusBar(sb)

        self.session_lbl = QLabel()
        self.cpu_lbl     = QLabel()
        self.buffer_lbl  = QLabel()
        self.sample_lbl  = QLabel()

        sb.addPermanentWidget(self.session_lbl)
        sb.addPermanentWidget(self.cpu_lbl)
        sb.addPermanentWidget(self.buffer_lbl)
        sb.addPermanentWidget(self.sample_lbl)
        sb.addPermanentWidget(QLabel("ORBIS v1.0‑beta"))

    # -------- timers & update loop ----------------------------------------
    def _init_timers(self) -> None:
        self.start_time   = time.time()
        self.ui_timer     = QTimer()
        self.ui_timer.timeout.connect(self._update_ui)
        self.ui_timer.start(100)                     # main UI refresh 10 Hz
        self.footer_timer = QTimer()
        self.footer_timer.timeout.connect(self._update_footer)
        self.footer_timer.start(1000)                # footer once per second

    # ---------------------------------------------------------------- runtime
    def _toggle_analysis(self) -> None:
        if self.running:
            self.analyzer.stop()
            self.running = False
            self.start_btn.setText("Start Analysis")
        else:
            dev = self.device_combo.currentData()
            if dev is not None:
                self.analyzer.stop()
                self.analyzer = AudioAnalyzer(device=dev)
            self.analyzer.start()
            self.running = True
            self.start_btn.setText("Stop Analysis")

    # -- per‑frame UI refresh ----------------------------------------------
    def _update_ui(self) -> None:
        if not self.running:
            return

        data = self.analyzer.get_audio_data()
        if not data:
            return

        vol  = float(data.get("volume", -60))
        freq = float(data.get("dominant_freq", 0))
        fft  = data.get("fft", None)
        sr   = int(data.get("sample_rate", 48000))

        # metrics (placeholder until LUFS calc is implemented)
        self._set_metric("Peak Level",         vol)
        self._set_metric("RMS Level",          vol - 6)
        self._set_metric("Integrated LUFS",    vol - 1)
        self._set_metric("Short‑term LUFS",    vol + 1)
        self.freq_labels["dom"].setText(f"{freq:.0f} Hz")

        # band energies
        if fft is not None and len(fft):
            freqs = np.fft.rfftfreq(len(fft)*2 - 2, 1/sr)
            def band(db_range): return 20 * np.log10(np.mean(fft[db_range]) + 1e-10)
            low  = band(np.where(freqs < 250))
            mid  = band(np.where((freqs >= 250) & (freqs < 2000)))
            high = band(np.where(freqs >= 2000))
            self.freq_labels["low" ].setText(f"{low :.1f} dB")
            self.freq_labels["mid" ].setText(f"{mid :.1f} dB")
            self.freq_labels["high"].setText(f"{high:.1f} dB")

        # spectrum bars
        self._update_spectrum(fft, sr)

        # JSON gateway for other modules
        self._export_json(vol, freq, fft, sr)

    # helper to update metric bars -----------------------------------------
    def _set_metric(self, name: str, value: float) -> None:
        label, bar = self.metric_widgets[name]
        label.setText(f"{value:.1f} dB" if "LUFS" not in name else f"{value:.1f} LUFS")
        pct = max(0, min(1, (value + 60) / 60))
        bar.setFixedWidth(int(pct * 150))

    # pg.BarGraphItem rebuild each frame -----------------------------------
    def _update_spectrum(self, fft: np.ndarray | None, sr: int) -> None:
        if fft is None or not len(fft):
            return
        steps = 100
        freqs = np.fft.rfftfreq(len(fft)*2 - 2, 1/sr)
        bins  = np.logspace(np.log10(20), np.log10(20000), steps + 1)

        heights: List[float] = []
        brushes: List[QBrush] = []

        for i in range(steps):
            idx = np.where((freqs >= bins[i]) & (freqs < bins[i+1]))[0]
            mag = np.mean(fft[idx]) if len(idx) else 0.0
            db  = 20 * np.log10(mag + 1e-10)
            heights.append(db + 60)           # shift to positive

            grad = QLinearGradient(0, 0, 0, 1)
            grad.setCoordinateMode(QGradient.ObjectBoundingMode)
            grad.setColorAt(0,   QColor(0,   255,  65, 204))
            grad.setColorAt(0.5, QColor(64,  224, 208, 128))
            grad.setColorAt(1,   QColor(0,   255, 255,  77))
            brushes.append(QBrush(grad))

        self.pg.clear()
        self.pg.addItem(pg.BarGraphItem(x=list(range(steps)),
                                        height=heights,
                                        width=0.8,
                                        brushes=brushes))

    # JSON dump for other subsystems ---------------------------------------
    def _export_json(self, vol: float, freq: float,
                     fft: np.ndarray | None, sr: int) -> None:
        JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
        payload: Dict[str, Any] = {
            "volume": round(vol, 2),
            "dominant_freq": round(freq, 2)
        }
        if fft is not None and len(fft):
            freqs = np.fft.rfftfreq(len(fft)*2 - 2, 1/sr)
            spec = {}
            for target in [20, 50, 100, 250, 500, 1000, 2000, 5000, 10000, 15000, 20000]:
                idx = (np.abs(freqs - target)).argmin()
                spec[f"{target}Hz"] = round(20 * np.log10(max(fft[idx], 1e-10)), 2)
            payload["spectrum"] = spec
        with open(JSON_PATH, "w") as f:
            json.dump(payload, f, indent=2)

    # footer periodic update ----------------------------------------------
    def _update_footer(self) -> None:
        elapsed = int(time.time() - self.start_time)
        h, m, s = elapsed // 3600, (elapsed // 60) % 60, elapsed % 60
        self.session_lbl.setText(f"Session Time: {h:02d}:{m:02d}:{s:02d}")
        self.cpu_lbl.setText(f"CPU: {psutil.cpu_percent()}%")

        try:
            dev_info = sd.query_devices(self.device_combo.currentData() or 0)
            buf = int(dev_info["default_low_input_latency"] * dev_info["default_samplerate"])
            sr  = int(dev_info["default_samplerate"])
        except Exception:
            buf, sr = 0, 0
        self.buffer_lbl.setText(f"Buffer: {buf}")
        self.sample_lbl.setText(f"Sample Rate: {sr} Hz")

    # ----------------------------------------------------------------------#
    #                    additional helper slots / wiring                   #
    # ----------------------------------------------------------------------#
    def _zoom_spectrum(self, factor: float) -> None:
        """factor < 1 zooms in, factor > 1 zooms out"""
        low, high = self._current_y_range
        mid  = (low + high) / 2.0
        span = (high - low) * factor / 2.0
        low_new  = max(0, mid - span)
        high_new = mid + span
        self.pg.setYRange(low_new, high_new)
        self._current_y_range = (low_new, high_new)

    def _reset_zoom(self) -> None:
        self.pg.setYRange(*self._default_y_range)
        self._current_y_range = self._default_y_range

    def _toggle_fullscreen(self) -> None:
        self.isFullScreen() and self.showNormal() or self.showFullScreen()

    def _wire_overlay_buttons(self) -> None:
        c = self.vis_widget.controls
        c["zoom_in"   ].clicked.connect(lambda: self._zoom_spectrum(0.80))
        c["zoom_out"  ].clicked.connect(lambda: self._zoom_spectrum(1.25))
        c["reset_zoom"].clicked.connect(self._reset_zoom)
        c["fullscreen"].clicked.connect(self._toggle_fullscreen)

    # capture current spectrum panel to PNG ---------------------------------
    def capture_spectrum(self) -> None:
        CAPTURES_DIR.mkdir(exist_ok=True)
        fname = CAPTURES_DIR / f"spectrum_{time.strftime('%Y%m%d_%H%M%S')}.png"
        if self.pg.grab().save(str(fname)):
            self.statusBar().showMessage(f"Spectrum saved → {fname.name}", 5000)
        else:
            self.statusBar().showMessage("⚠ Capture failed.", 5000)

# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    app = QApplication(sys.argv)
    if LOGO_PATH.exists():
        app.setWindowIcon(QIcon(str(LOGO_PATH)))

    analyzer = AudioAnalyzer()          # backend instance
    window   = OrbisAudioCockpit(analyzer)
    window.show()

    sys.exit(app.exec())
