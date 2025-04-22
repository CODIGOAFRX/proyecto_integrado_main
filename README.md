
![Banner](https://github.com/user-attachments/assets/e81a14ff-b496-4fd1-8c0b-2a4890de06ff)

# **ORBIS – Frequency-Driven 3D Visualizer**
![License](https://img.shields.io/badge/License-Academic-blue.svg)
![Status](https://img.shields.io/badge/Status-Alpha-orange.svg)
![Python](https://img.shields.io/badge/Python-3.11-blue)
![Blender](https://img.shields.io/badge/Blender-3.6%2B-lightgrey)

**Current Version:** `v0.1-alpha` – Core audio export ready. Blender sync in progress.

Orbis is a frequency-based 3D visualizer that transforms any audio track into a dynamic organic shape using Blender, Python, and CRIWARE SDK.

> 🎧 Turn sound into shape.  
> 🌐 See your mix.  
> 🌀 Discover the balance.

Orbis es una herramienta de visualización sonora que convierte datos de frecuencia en geometría 3D orgánica. Esta demo representa una versión alpha del sistema, orientada a la educación, performance y mezcla profesional.

---

## 🛠 Built With / Tecnologías utilizadas

- [Python 3.11](https://www.python.org/)
- [Blender 3.6+](https://www.blender.org/)
- [CRIWARE ADX2 SDK](https://www.criware.com/en/)
- [Figma](https://www.figma.com/) / [Canva](https://www.canva.com/) – UI Mockups

---

## 📦 Project Layout Overview / Estructura general del repositorio

- `/Orbis_Demo_Kit/` → Carpeta central con documentación, renders, y entregable para el tribunal.
- `/proyecto_integrado-main/` → Programa principal de análisis (exporta JSON en tiempo real).
- `/orbis_live_blender/` → Add-on para Blender que lee el JSON y deforma la malla (en desarrollo).

---

## 🧩 Project Overview / Resumen del Proyecto

| Module              | Function (EN)                                      | Función (ES)                                      |
|---------------------|----------------------------------------------------|---------------------------------------------------|
| Audio Analysis      | FFT, RMS, dominant frequency → JSON/CSV            | Análisis de audio FFT y volumen → JSON/CSV       |
| 3D Visualization    | Mesh deformation using Blender scripts             | Deformación geométrica con scripts en Blender    |
| UI Mockups          | Interface designs in Figma / Canva                 | Diseño de interfaces con Figma / Canva           |
| CRIWARE Integration | Cue reading from ACB/WAV files (in progress)       | Lectura de cues desde archivos ACB/WAV (beta)    |

---

## 🔧 Status / Estado del Proyecto
![Captura de pantalla 2025-04-22 124913](https://github.com/user-attachments/assets/45218ce1-b2f0-4427-8777-5d84fccb0d5e)

> Alpha prototype with basic audio export and live JSON streaming every 100ms.  
> Prototipo técnico en estado alpha con exportación JSON continua cada 100ms.

---

## 🚀 How to Run / Cómo Ejecutar

**Requirements / Requisitos**
- Python 3.11
- Blender 3.6+
- Optional: VB-Cable (for real-time audio input / entrada de audio virtual)

**1. Start Audio Core (main Python program)**
```bash
cd proyecto_integrado-main/proyecto\ Integrado/
python iu.py
```

**2. Launch Blender Add-on / Lanzar visualizador en Blender**
```bash
blender -P orbis_live_blender/orbis_live_link.py
```

**3. Live Communication (optional) / Comunicación en tiempo real (opcional)**
```bash
python code/realtime_sender.py
# In parallel terminal / en terminal paralelo:
python code/realtime_receiver.py
```
> *Make sure the JSON output is being written inside `/json/` folder so the add-on can read it correctly.*

---

## 📁 Directory Structure / Estructura del Proyecto

```
/Orbis_Demo_Kit
├── README.txt
├── branding/
├── code/
├── documents/
├── renders/
/orbis_live_blender
├── orbis_live_link.py
/proyecto_integrado-main
├── proyecto Integrado/
│   ├── iu.py
│   └── audio_analyzer.py
```

---

## 🖼️ Mockups / Artes conceptuales PC/WEB y Phone

| ![Concept1](https://github.com/user-attachments/assets/efa67895-7928-4b41-8996-2795801587d7) | ![Concept2](https://github.com/user-attachments/assets/a6c3502e-e795-4e64-9897-364604549cc5) | 
|---|---|

> Diseños no finales en desarrollo, **en caso de que el proyecto alcance un estado comercial y finalizado total.**  
> Work in Progress concept arts of the direction envisioned visually. These mockups represent the visual direction aim for, **should the tool were to be fully developed and commercialized.**

- *However, for the final project and 1.0 version, our focus remains on delivering a functional prototype that clearly conveys the core idea — as required.*

---

## 📚 Documentation / Documentación

- 📘 `/documents/` – TFG technical document
- 🖼️ `/renders/` – Mockups and visual concept
- 🧩 `/code/` – Python and Blender scripts

---

## 🧠 About the Authors / Autores

> Developed for Final Degree Project – Higher National Diploma in Multiplatform Application Development (2024/2025)   
> Desarrollado como Trabajo Fin de Grado – Ciclo Formativo de Grado Superior en Desarrollo de Aplicaciones Multiplataforma (2024/2025)  
> David Erik García Arenas & Pedro Jesús Gómez Pérez  
> MEDAC Davante NEVADA | OnProjects Hub – Granada

---

## 📜 License / Licencia

**Academic license** – All rights reserved.  
**Licencia académica** – Todos los derechos reservados.  
🚫 Commercial use is not allowed without permission.

---
