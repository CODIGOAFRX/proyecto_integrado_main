"""iu.py — unified Orbis Audio Cockpit (v0.1‑alpha)
-----------------------------------------------------------------------------
Full PyQt5 UI + original alpha‑logic backend in one file.
Drop this next to `audio_analyzer.py`, keep all other modules unchanged.
"""

from __future__ import annotations
import sys, os, math, json, time, random
from pathlib import Path

import numpy as np
import psutil, pyaudio, sounddevice as sd
from PyQt5.QtCore   import Qt, QTimer, QPointF
from PyQt5.QtGui    import (
    QColor, QPainter, QPen, QBrush, QFont, QFontDatabase,
    QRadialGradient, QLinearGradient, QPolygonF, QGradient, QDropShadowEffect
)
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QComboBox, QSlider, QCheckBox, QGroupBox, QStatusBar,
    QToolButton, QOpenGLWidget
)
from OpenGL.GL import glClearColor, glClear, GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT
import pyqtgraph as pg

# backend analyzer from original project
from audio_analyzer import AudioAnalyzer

# ---------------------------------------------------------------------------
# resources & constants
BASE_DIR   = Path(__file__).resolve().parent
FONT_DIR   = BASE_DIR / "resources" / "fonts"
JSON_PATH  = BASE_DIR / "json" / "orbis_data.json"
for f in ("Rajdhani-Regular.ttf", "Orbitron-Regular.ttf", "Remixicon.ttf"):
    QFontDatabase.addApplicationFont(str(FONT_DIR / f))

PRIMARY   = "#00FF41"
SECONDARY = "#40E0D0"
BG        = "#121212"
PANEL     = "#1E1E1E"
BORDER    = "#2D2D2D"
TEXT      = "#e0e0e0"
ACCENT    = SECONDARY

# ---------------------------------------------------------------------------
# helper widgets
class GLWidget(QOpenGLWidget):
    def initializeGL(self):
        glClearColor(18/255, 18/255, 18/255, 1)
    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

class VisualizationWidget(QWidget):
    def __init__(self):
        super().__init__(); self.opengl = GLWidget(self); self.opengl.lower()
        glyphs = ["\ue3d4", "\ue3d5", "\ue3a8", "\ue38b"]
        self.overlay = []
        for g in glyphs:
            b = QToolButton(self); b.setText(g); b.setFont(QFont("Remixicon",16))
            b.setFixedSize(32,32); b.setStyleSheet(f"background:{PANEL};border-radius:16px")
            self.overlay.append(b)
    def resizeEvent(self, e):
        self.opengl.setGeometry(self.rect())
        x, y = 10, self.height()-42
        for b in self.overlay:
            b.move(x,y); x+=37
    def paintEvent(self, _):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        r = self.rect(); pen = QPen(QColor(64,224,208,25))
        for gx in range(0,r.width(),20): p.drawLine(gx,0,gx,r.height())
        for gy in range(0,r.height(),20): p.drawLine(0,gy,r.width(),gy)
        c=r.center(); rad=min(r.width(),r.height())*0.25
        pts=[QPointF(c.x()+rad*math.cos(math.radians(60*i)), c.y()+rad*math.sin(math.radians(60*i))) for i in range(6)]
        hexpoly=QPolygonF(pts)
        grad=QRadialGradient(c,rad); grad.setColorAt(0,QColor(0,255,65,13)); grad.setColorAt(1,QColor(18,18,18))
        p.setBrush(QBrush(grad)); p.setPen(QPen(QColor(64,224,208,51),1)); p.drawPolygon(hexpoly)
        for fac,alpha in [(0.75,26),(0.4,51)]:
            rr=rad*fac; g=QRadialGradient(c,rr);
            g.setColorAt(0,QColor(0,255,255,alpha) if fac==0.75 else QColor(0,255,65,alpha)); g.setColorAt(1,QColor(18,18,18))
            p.setBrush(QBrush(g)); p.setPen(Qt.NoPen); p.drawEllipse(c,rr,rr)

# ---------------------------------------------------------------------------
class OrbisAudioCockpit(QMainWindow):
    def __init__(self, analyzer: AudioAnalyzer):
        super().__init__(); self.analyzer = analyzer
        self.setWindowTitle("Orbis Audio Cockpit v1.2.4 – alpha merge"); self.resize(1280,800)
        self._style(); self._build_ui(); self._timers()

    # --------------------- style sheet ---------------------
    def _style(self):
        self.setStyleSheet(f"""
            QWidget {{background:{BG};color:{TEXT};}}
            QPushButton {{background:{PANEL};border:1px solid rgba(64,224,208,.3);border-radius:12px;padding:6px;}}
            QPushButton#neon {{border:1px solid {PRIMARY};color:{PRIMARY};}}
            QComboBox {{background:transparent;border:none;background-image:url(data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%2340E0D0' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E);background-repeat:no-repeat;background-position:right 8px center;}}
            QSlider::groove:horizontal {{height:4px;border-radius:5px;background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #1e293b,stop:1 {ACCENT});}}
            QSlider::handle:horizontal {{width:16px;height:16px;border-radius:8px;background:#00FFFF;margin:-6px 0;}}
            QCheckBox::indicator {{width:18px;height:18px;border-radius:4px;background:#2D2D2D;}}
            QCheckBox::indicator:checked {{background:{PRIMARY};}}
            QCheckBox#switch::indicator {{width:48px;height:24px;border-radius:12px;background:#2D2D2D;}}
            QCheckBox#switch::indicator:checked {{background:{PRIMARY};}}
        """)

    # --------------------- build UI ----------------------
    def _build_ui(self):
        central=QWidget(); self.setCentralWidget(central)
        v=QVBoxLayout(central); v.setContentsMargins(0,0,0,0); v.setSpacing(0)
        v.addWidget(self._header())
        body=QWidget(); body_v=QVBoxLayout(body); body_v.setContentsMargins(12,12,12,12); body_v.setSpacing(12)
        body_v.addLayout(self._top_panels(),1)
        body_v.addWidget(self._spectrum())
        v.addWidget(body)
        self._footer()

    # ---------- header ----------
    def _header(self):
        w=QWidget(); w.setStyleSheet(f"background:{PANEL};border-bottom:1px solid {BORDER}")
        l=QHBoxLayout(w); l.setContentsMargins(16,8,16,8)
        title=QLabel("Orbis Audio Cockpit"); title.setFont(QFont("Orbitron",20,QFont.Bold)); l.addWidget(title); l.addSpacing(20)
        # device combo
        box=QGroupBox(); box.setStyleSheet(f"background:{BORDER};border-radius:12px"); bl=QHBoxLayout(box); bl.setContentsMargins(8,4,8,4)
        ic=QLabel(chr(0xf3c2)); ic.setFont(QFont("Remixicon",12)); ic.setStyleSheet(f"color:{SECONDARY}"); bl.addWidget(ic)
        self.device_combo=QComboBox(); self._populate_devices(); bl.addWidget(self.device_combo)
        l.addWidget(box); l.addStretch()
        self.start_btn=QPushButton("Start Analysis"); self.start_btn.setObjectName("neon")
        glow=QDropShadowEffect(); glow.setColor(QColor(PRIMARY)); glow.setBlurRadius(15); self.start_btn.setGraphicsEffect(glow)
        self.start_btn.clicked.connect(self._toggle_analysis)
        l.addWidget(self.start_btn); l.addWidget(QPushButton("Settings"))
        return w

    def _populate_devices(self):
        self.device_combo.clear(); devs=sd.query_devices()
        self.input_map=[(i,d['name']) for i,d in enumerate(devs) if d['max_input_channels']>0]
        for idx,name in self.input_map: self.device_combo.addItem(name, userData=idx)

    # ---------- panels ----------
    def _top_panels(self):
        hl=QHBoxLayout(); hl.setSpacing(12)
        hl.addWidget(self._controls_panel(),1)
        hl.addWidget(self._vis_panel(),3)
        hl.addWidget(self._metrics_panel(),1)
        return hl

    def _controls_panel(self):
        gb=QGroupBox("Analysis Controls"); gb.setFont(QFont("Orbitron",12))
        gb.setStyleSheet(f"QGroupBox{{background:{PANEL};border:1px solid {BORDER};border-radius:12px;color:white}}")
        v=QVBoxLayout(gb)
        v.addLayout(self._slider_row("Frequency Range","20Hz ‑ 20kHz",100))
        v.addLayout(self._slider_row("Resolution","2048 FFT",70))
        v.addLayout(self._slider_row("Sensitivity","‑24 dB",50))
        v.addWidget(self._checkbox_group("Display Options",["Show Peak Markers","Show Grid Lines","Logarithmic Scale"]))
        v.addWidget(self._button_grid("Visualization Mode",["Spectrum","3D Shape","Waveform","Spectrogram"]))
        return gb

    def _slider_row(self,label,val,init):
        lay=QVBoxLayout(); top=QHBoxLayout(); top.addWidget(QLabel(label)); lv=QLabel(val); lv.setStyleSheet(f"color:{ACCENT};font-size:10px"); top.addWidget(lv); lay.addLayout(top)
        s=QSlider(Qt.Horizontal); s.setRange(0,100); s.setValue(init); lay.addWidget(s); return lay

    def _checkbox_group(self,title,items):
        gb=QGroupBox(title); gb.setStyleSheet("QGroupBox{border:none;color:white}"); v=QVBoxLayout(gb)
        for it in items: cb=QCheckBox(it); cb.setChecked(True); v.addWidget(cb)
        return gb

    def _button_grid(self,title,items):
        gb=QGroupBox(title); grid=QGridLayout(gb)
        for i,it in enumerate(items): grid.addWidget(QPushButton(it), i//2, i%2)
        return gb

    def _vis_panel(self):
        gb=QGroupBox(); gb.setStyleSheet(f"background:{PANEL};border:1px solid {BORDER};border-radius:12px")
        v=QVBoxLayout(gb); header=QHBoxLayout()
        header.addWidget(QLabel("Real‑time Visualization")); live=QLabel("● Live"); live.setStyleSheet(f"color:{PRIMARY};font-size:10px"); header.addWidget(live)
        header.addStretch(); ar=QCheckBox("Auto‑rotate"); ar.setObjectName("switch"); ar.setChecked(True); header.addWidget(ar)
        v.addLayout(header); self.vis=VisualizationWidget(); v.addWidget(self.vis,1)
        return gb

    def _metrics_panel(self):
        gb=QGroupBox("Audio Metrics"); gb.setFont(QFont("Orbitron",12)); gb.setStyleSheet(f"QGroupBox{{background:{PANEL};border:1px solid {BORDER};border-radius:12px;color:white}}")
        v=QVBoxLayout(gb)
        self.metric_widgets={}
        names=["Peak Level","RMS Level","Integrated LUFS","Short‑term LUFS"]
        for n in names:
            box=QWidget(); box_v=QVBoxLayout(box); box_v.setContentsMargins(0,0,0,0)
            top=QHBoxLayout(); top.addWidget(QLabel(n)); val=QLabel("‑‑‑"); val.setFont(QFont("Orbitron",12)); val.setStyleSheet(f"color:#00FFFF")
            top.addWidget(val); box_v.addLayout(top)
            bar_bg=QWidget(); bar_bg.setFixedHeight(6); bar_bg.setStyleSheet(f"background:#1E1E1E;border-radius:3px")
            bar=QWidget(bar_bg); bar.setGeometry(0,0,0,6); bar.setStyleSheet("background:linear-gradient(90deg,#00FF41,#40E0D0);border-radius:3px")
            box_v.addWidget(bar_bg); v.addWidget(box)
            self.metric_widgets[n]=(val,bar)
        # frequency split grid
        grid=QGridLayout(); labels=[("Low (20‑250Hz)","low"),("Mid (250‑2kHz)","mid"),("High (2k‑20kHz)","high"),("Dominant Freq","dom")]
        self.freq_labels={}
        for i,(txt,key) in enumerate(labels):
            cell=QVBoxLayout(); lab=QLabel(txt); val=QLabel("‑‑‑"); val.setStyleSheet(f"color:{PRIMARY};font-family:Orbitron")
            cell.addWidget(lab); cell.addWidget(val); grid.addLayout(cell,i//2,i%2); self.freq_labels[key]=val
        v.addLayout(grid)
        return gb

    # ---------- spectrum ----------
    def _spectrum(self):
        gb=QGroupBox("FFT Spectrum Analyzer"); gb.setStyleSheet(f"QGroupBox{{background:{PANEL};border:1px solid {BORDER};border-radius:12px;color:white}}"); v=QVBoxLayout(gb)
        ctrl=QHBoxLayout(); ctrl.addWidget(QLabel("Smoothing")); self.smooth=QSlider(Qt.Horizontal); self.smooth.setRange(0,100); self.smooth.setValue(30); ctrl.addWidget(self.smooth)
        ctrl.addWidget(QPushButton("Capture")); ctrl.addStretch(); v.addLayout(ctrl)
        self.pg=pg.PlotWidget(); self.pg.setBackground(BG); self.bar_item=None; v.addWidget(self.pg)
        return gb

    # ---------------- timers & updates ----------------
    def _timers(self):
        self.ui_timer=QTimer(); self.ui_timer.timeout.connect(self._update_ui); self.ui_timer.start(100)
        self.footer_timer=QTimer(); self.footer_timer.timeout.connect(self._update_footer); self.footer_timer.start(1000)
        self.start_time=time.time()
        self.cpu_label=None  # set in footer later

    # ---------- footer ----------
    def _footer(self):
        sb=QStatusBar(); sb.setStyleSheet(f"background:{PANEL};color:{TEXT}"); self.setStatusBar(sb)
        self.session_lbl=QLabel(); self.cpu_lbl=QLabel(); self.buffer_lbl=QLabel(); self.sample_lbl=QLabel(); ver=QLabel("Orbis Audio Cockpit v1.2.4")
        for w in (self.session_lbl,self.cpu_lbl,self.buffer_lbl,self.sample_lbl,ver): sb.addPermanentWidget(w)

    # ---------------- functional slots ----------------
    def _toggle_analysis(self):
        if hasattr(self,"running") and self.running:
            self.analyzer.stop(); self.running=False; self.start_btn.setText("Start Analysis")
        else:
            dev=self.device_combo.currentData()
            if dev is not None: self.analyzer.stop(); self.analyzer=AudioAnalyzer(device=dev)
            self.analyzer.start(); self.running=True; self.start_btn.setText("Stop Analysis")

    def _update_ui(self):
        if not hasattr(self,"running") or not self.running: return
        data=self.analyzer.get_audio_data(); vol=data["volume"]; freq=data["dominant_freq"]; fft=data["fft"]
        # metrics
        self._set_metric("Peak Level",vol); self._set_metric("RMS Level",vol-6)  # placeholder
        self._set_metric("Integrated LUFS",vol); self._set_metric("Short‑term LUFS",vol+1)
        self.freq_labels["dom"].setText(f"{freq:.0f} Hz")
        # bands low mid high
        if fft is not None and len(fft):
            freqs=np.fft.rfftfreq(len(fft)*2-1,1/self.analyzer.sample_rate)
            low=np.where(freqs<250)[0]; mid=np.where((freqs>=250)&(freqs<2000))[0]; high=np.where(freqs>=2000)[0]
            for rng,key in ((low,"low"),(mid,"mid"),(high,"high")):
                db=20*np.log10(np.mean(fft[rng])+1e-10) if len(rng) else -60
                self.freq_labels[key].setText(f"{db:.1f} dB")
        # spectrum
        self._update_spectrum(fft)
        # json export
        self._export_json(vol,freq,fft)

    def _set_metric(self,name,val):
        label,bar=self.metric_widgets[name]
        label.setText(f"{val:.1f} dB" if "LUFS" not in name else f"{val:.1f} LUFS")
        pct=max(0,min(1,(val+60)/60)); bar.setFixedWidth(int(pct*150))

    def _update_spectrum(self, fft):
        if fft is None or not len(fft): return
        freqs=np.fft.rfftfreq(len(fft)*2-1,1/self.analyzer.sample_rate)
        steps=100; bins=np.logspace(np.log10(20),np.log10(20000),steps+1)
        heights=[]; brushes=[]
        for i in range(steps):
            idx=np.where((freqs>=bins[i])&(freqs<bins[i+1]))[0]
            mag=np.mean(fft[idx]) if len(idx) else 0
            db=20*np.log10(mag+1e-10); heights.append(db+60)
            g=QLinearGradient(0,0,0,1); g.setCoordinateMode(QGradient.ObjectBoundingMode)
            g.setColorAt(0,QColor(0,255,65,204)); g.setColorAt(0.5,QColor(64,224,208,128)); g.setColorAt(1,QColor(0,255,255,77))
            brushes.append(QBrush(g))
        self.pg.clear(); self.pg.addItem(pg.BarGraphItem(x=list(range(steps)),height=heights,width=0.8,brushes=brushes))

    def _export_json(self, volume,freq,fft):
        try:
            JSON_PATH.parent.mkdir(parents=True,exist_ok=True)
            payload={"volume":round(float(volume),2),"dominant_freq":round(float(freq),2)}
            if fft is not None and len(fft):
                freqs=np.fft.rfftfreq(len(fft)*2-1,1/self.analyzer.sample_rate); fft=np.array(fft)
                targets=[20,50,100,250,500,1000,2000,5000,6000,7000,12000,15000,20000]
                spec={}
                for t in targets:
                    idx=(np.abs(freqs-t)).argmin(); spec[f"{t}Hz"]=round(20*np.log10(max(fft[idx],1e-10)),2)
                payload["spectrum"]=spec
            with open(JSON_PATH,"w") as f: json.dump(payload,f,indent=4)
        except Exception as e:
            print("JSON export error:",e)

    def _update_footer(self):
        elapsed=int(time.time()-self.start_time); h,m,s=elapsed//3600,(elapsed//60)%60,elapsed%60
        self.session_lbl.setText(f"Session Time: {h:02d}:{m:02d}:{s:02d}")
        self.cpu_lbl.setText(f"CPU: {psutil.cpu_percent()}%")
        try:
            info=pyaudio.PyAudio().get_default_input_device_info(); bf=int(info['defaultLowInputLatency']*info['defaultSampleRate'])
            sr=int(info['defaultSampleRate'])
        except Exception:
            bf=0; sr=0
        self.buffer_lbl.setText(f"Buffer: {bf}"); self.sample_lbl.setText(f"Sample Rate: {sr} Hz")

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app=QApplication(sys.argv)
    analyzer=AudioAnalyzer(); analyzer.start()
    w=OrbisAudioCockpit(analyzer)
    w.show(); sys.exit(app.exec_())
