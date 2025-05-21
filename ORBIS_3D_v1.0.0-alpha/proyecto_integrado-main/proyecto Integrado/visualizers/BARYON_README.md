# 📦 `baryon_web/` – Visualizador 3D Externo Integrado

Este directorio contiene la versión local y embebida del visualizador **Baryon**, una herramienta open-source desarrollada originalmente como experiencia web interactiva en [https://baryon.live](https://baryon.live).

---

## 🌐 ¿Qué es Baryon?

**Baryon** es un visualizador 3D de sonido que simula geometrías naturales basadas en audio (visualización "cimática"). Fue desarrollado con **Three.js** y utiliza `GPUComputationRenderer` para generar partículas reactivas al sonido.

> Descripción original del autor:  
> “Baryon is the world’s first cymatic 3D visualizer that simulates the natural geometry of sound using GPU-based physics in Three.js.”

---

## 🧩 ¿Por qué lo hemos integrado en ORBIS?

El plan original del proyecto ORBIS contemplaba el uso de **Blender** como motor de visualización 3D. Sin embargo, surgieron varios problemas técnicos:

- Inestabilidad con controladores y hardware (drivers de GPU).
- Buffer JSON sobreescrito en tiempo real.
- Complejidad avanzada de los **Geometry Nodes**.
- Tiempo limitado para construir una geometría orgánica interactiva desde cero.

➡️ Por ello, se optó por una **integración estructural** del visualizador Baryon, que actúa como **módulo externo especializado** (renderer visual) dentro del sistema ORBIS.

---

## 🧠 ¿Qué hace este módulo?

- Se lanza desde el propio programa ORBIS (mediante `launch_baryon.py`).
- Recibe datos indirectamente a través de nuestra exportación JSON (`/json/orbis_data.json`).
- Reacciona visualmente a la entrada de audio del sistema.
- Representa una escena tridimensional de partículas con geometría reactiva.

---

## ⚙️ ¿Qué partes podemos controlar?

Desde ORBIS controlamos:

- **Cuándo se lanza** el visualizador.
- Qué archivo HTML se ejecuta (`index.html`).
- **Qué datos mostramos aparte**: ORBIS sigue mostrando LUFS, RMS, espectro, etc., aunque Baryon no lo haga internamente.
- El flujo general de integración Python ↔ visualizador web.

---

## 🚫 ¿Qué partes no podemos modificar?

- El código JavaScript está parcialmente **minificado** u ofuscado.
- La lógica de shaders, simulación de partículas o física no es editable sin reconstruir el sistema original del autor.
- La estructura interna del entorno gráfico no es modificable sin acceso a una versión de desarrollo.

---

## ✅ ¿Qué hemos hecho entonces?

- Extraído todos los archivos HTML, CSS, JS y media necesarios para ejecutar Baryon offline.
- Validado su comportamiento.
- **Integrado en el flujo funcional de ORBIS** como visualizador modular.
- **Mantenido el análisis de audio por parte de nuestro sistema** en Python, con métricas más avanzadas.

---

## 📄 Créditos y licencia

- Proyecto original: [Baryon](https://baryon.live)  
- Autor: Desarrollador independiente (2024)  
- Tecnología: [Three.js](https://threejs.org/), WebGL, GPUComputationRenderer  
- Propósito original: Demostración artística y experimental

⚠️ Este uso se enmarca dentro de un **TFG académico sin fines comerciales**, y se documenta adecuadamente la fuente e integración.

---

## 🧩 Justificación técnica

> “No hemos creado Baryon desde cero. Hemos integrado su funcionamiento como parte del módulo 3D de ORBIS, enfocándonos en el desarrollo del análisis DSP, control de métricas e interfaz general. La visualización 3D es externa pero está controlada y contextualizada dentro de nuestro sistema.”

---

📂 Este directorio forma parte del sistema **ORBIS – Frequency-Driven 3D Visualizer (2025)**.  
Autores: David Erik García Arenas & Pedro Jesús Gómez Pérez · MEDAC Nevada.

