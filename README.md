![Banner](https://github.com/user-attachments/assets/e81a14ff-b496-4fd1-8c0b-2a4890de06ff)

# **ORBIS – Frequency-Driven 3D Visualizer**

![License](https://img.shields.io/badge/License-Academic-blue.svg)
![Status](https://img.shields.io/badge/Status-Alpha-orange.svg)
![Python](https://img.shields.io/badge/Python-3.11-blue)
![Three.js](https://img.shields.io/badge/Three.js-powered-lightgrey)

**Current Version:** `v1.0.0-alpha` – Real-time audio analysis with integrated 3D visualization.

> 🎧 Turn sound into shape.  
> 🌐 See your mix.  
> 🌀 Discover the balance.

ORBIS es una herramienta multiplataforma desarrollada como Trabajo Fin de Grado para analizar el contenido frecuencial de una señal de audio y generar una visualización 3D reactiva que asista en procesos de mezcla y masterización profesional.

Este sistema incluye un motor completo de análisis en Python, métricas LUFS/RMS/FFT en tiempo real y un módulo visual 3D integrado mediante **Baryon**, un visualizador cymático creado con **Three.js**.

---

## 🔄 Estado del Proyecto / Project Status

| Módulo              | Estado Actual                             |
|---------------------|--------------------------------------------|
| Núcleo de Audio     | ✅ Estable, exporta JSON cada 100ms         |
| Métricas Avanzadas  | ✅ LUFS, FFT, RMS, Dominante, Balance       |
| Interfaz de Usuario | ✅ Estilizada y funcional en PySide6        |
| Visualizador 3D     | ✅ Integrado vía Baryon (Three.js)         |
| Add-on Blender      | ❌ Retirado (complejidad + falta de tiempo) |

> 🎯 El prototipo final utiliza **Baryon** como renderer visual 3D, integrado desde ORBIS.

---

## ⚙️ Tecnologías utilizadas / Tech Stack

- [Python 3.11](https://www.python.org/)
- [PySide6](https://doc.qt.io/qtforpython-6/)
- [NumPy](https://numpy.org/)
- [sounddevice](https://python-sounddevice.readthedocs.io/)
- [Three.js](https://threejs.org/) *(Baryon Visualizer)*
- [QWebEngineView](https://doc.qt.io/qtforpython-6/PySide6/QtWebEngineWidgets/QWebEngineView.html)

---

## 📂 Estructura del Proyecto / Project Structure

```
📁 orbis_main/             # Núcleo del sistema ORBIS
├── audio_analyzer.py     # Módulo de análisis FFT/LUFS/RMS
├── orbis_ui.py           # Interfaz principal PySide6
├── launch_baryon.py      # Lanza el visualizador Baryon
├── /resources/           # Iconos, fuentes, modelos 3D, imágenes
├── /captures/            # Capturas PNG del espectro
├── /json/                # Exportaciones en tiempo real

📁 baryon_web/             # Visualizador 3D embebido (Three.js)
├── index.html            # Entrada principal
├── js/, shaders/, assets/ # Archivos estáticos exportados del site
└── README.md             # Justificación y origen de Baryon

📁 Orbis_Demo_Kit/         # Dossier técnico y recursos del TFG
├── documents/, renders/, branding/
```

---

## 🔍 Sobre el visualizador 3D (Baryon)

> **¿Hicisteis el visualizador 3D?**
>
> No. El motor visual se basa en **Baryon**, una herramienta online desarrollada en Three.js. Hemos integrado sus recursos de forma estructural como módulo visual externo.

**Justificación técnica (README de baryon_web):**

- Baryon fue extraído desde su web original mediante técnicas forenses (wget + inspección de red).
- No se dispone del repositorio oficial, pero se reconstruyó localmente en una versión funcional.
- El motor de ORBIS lanza y sincroniza este visualizador desde Python.
- La visualización solo representa datos generados por nuestro sistema.

> 🧠 Esto se denomina *middleware integration* y es una práctica profesional habitual en entornos reales.

---

## 🧪 ¿Qué métricas analiza ORBIS?

- **FFT (Fast Fourier Transform)** de 13 bandas en escala logarítmica.
- **LUFS Integrado / LUFS Corto / Peak / RMS.**
- **Frecuencia dominante actual.**
- **Balance de frecuencias (graves vs agudos).**
- **Desviaciones por zonas espectrales (LOW, MID, HIGH).**

Los datos se exportan en JSON y controlan dinámicamente la visualización 3D.

---

## 🚀 Cómo ejecutar ORBIS

**Requisitos:**
- Python 3.11
- Paquetes: PySide6, NumPy, sounddevice, pyqtgraph, pyloudnorm
- Navegador moderno (para visualizar Baryon)
- *(opcional)* VB-Cable o entrada virtual

```bash
cd orbis_main/
python orbis_ui.py
```

---

## 🧾 Licencia / License

**Licencia Académica – All rights reserved**  
Uso comercial no autorizado sin permiso expreso.

---

## 👥 Autores

Desarrollado como Trabajo Fin de Grado – Ciclo Formativo de Grado Superior en Desarrollo de Aplicaciones Multiplataforma (2024/2025)  

**David Erik García Arenas** · Arquitectura UI / Motor FFT / Integración Baryon  
**Pedro Jesús Gómez Pérez** · Diseño UI/UX / Envoltorios 3D / Arte conceptual

**Centro:** MEDAC Davante NEVADA | Granada

---
