# ORBIS – Frequency-Driven 3D Visualizer (Alpha Demo)

Orbis is a frequency-based 3D visualizer that transforms any audio track into an organic, dynamic shape in Blender, helping audio engineers, artists, and educators visually interpret sound balance.

🎧 Turn sound into shape.  
🌐 See your mix.  
🌀 Discover the balance.

---

## 🔧 Status

> This is a working **alpha prototype** of the Orbis system, built for academic and technical demonstration. Future versions will include standalone applications and deeper CRIWARE SDK integration.

---

## ✨ Key Features

- 🎚️ Real-time FFT analysis (Python)
- 🌀 Deformable 3D mesh using Blender’s Geometry Nodes
- 📦 Export to `.fbx`, `.glb`, `.blend` for Unity/Unreal
- 🧠 Integration-ready with CRIWARE SDK (ADX2)

---

## 📁 Project Modules

| Module | Function |
|--------|----------|
| Audio Analysis | FFT, RMS, dominant frequency → JSON/CSV |
| 3D Visualization | Blender script + GN modifiers |
| UI Mockups | Designed in Figma/Canva |
| CRIWARE SDK | Reading ACB/WAV files + cues (Beta stage) |

---

## 🚀 Quick Start

1. Clone the repo
2. Install dependencies:
```bash
pip install -r requirements.txt
