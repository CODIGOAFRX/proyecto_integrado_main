"""
gl_utils.py – OpenGL helpers for ORBIS
Public-domain · May 2025
"""

from __future__ import annotations
import ctypes, numpy as np, OpenGL.GL as GL

# Qt OpenGL classes (Qt 6.5 moved them from QtGui → QtOpenGL)
try:                                  # Qt ≥ 6.5
    from PySide6.QtOpenGL import (QOpenGLShader, QOpenGLShaderProgram,
                                  QOpenGLVertexArrayObject, QOpenGLBuffer)
except ImportError:                   # Qt 6.2 – 6.4
    from PySide6.QtGui    import QOpenGLShader, QOpenGLShaderProgram
    from PySide6.QtOpenGL import QOpenGLVertexArrayObject, QOpenGLBuffer


# ──────────────────────── GLSL (core 3.3) ─────────────────────────────
VERT_SRC = """
#version 330 core
layout(location = 0) in vec3 inPos;
layout(location = 1) in vec3 inNor;

uniform mat4  uMVP;
uniform float uInflate;

out vec3 vNor;
void main()
{
    vec3 displaced = inPos + inNor * uInflate;
    gl_Position    = uMVP * vec4(displaced, 1.0);
    vNor           = inNor;
}
"""

FRAG_SRC = """
#version 330 core
in  vec3 vNor;
out vec4 frag;
void main()
{
    vec3  L  = normalize(vec3(0.15, 0.6, 1.0));
    float d  = max(dot(normalize(vNor), L), 0.0);
    vec3  c  = mix(vec3(0.17,0.39,0.69), vec3(0.55,0.28,1.0), d);
    frag     = vec4(c, 1.0);
}
"""

def compile_shader() -> QOpenGLShaderProgram:
    prog = QOpenGLShaderProgram()
    prog.addShaderFromSourceCode(QOpenGLShader.Vertex,   VERT_SRC)
    prog.addShaderFromSourceCode(QOpenGLShader.Fragment, FRAG_SRC)
    prog.link()
    return prog


# ───────────────────────── GpuMesh helper ─────────────────────────────
class GpuMesh:
    """
    Upload a mesh once and keep VAO / VBO / IBO alive.

    Mesh requirements:
        vertices  (N×3 float32)
        normals   (N×3 float32)
        indices   (M   uint32)
        interleave() -> (N×6 float32)
    """
    def __init__(self, mesh):
        # ─ VAO ─
        self.vao = QOpenGLVertexArrayObject(); self.vao.create(); self.vao.bind()

        # ─ VBO ─
        self.vbo = QOpenGLBuffer(QOpenGLBuffer.VertexBuffer); self.vbo.create()
        self.vbo.bind()
        data = mesh.interleave().astype(np.float32, copy=False)
        self.vbo.allocate(data.tobytes(), data.nbytes)

        # ─ IBO ─
        self.ebo = QOpenGLBuffer(QOpenGLBuffer.IndexBuffer); self.ebo.create()
        self.ebo.bind()
        self.ebo.allocate(mesh.indices.tobytes(), mesh.indices.nbytes)

        # ─ attribute layout (★ fixed) ─
        stride = 6 * 4                                 # 6 floats * 4 B
        GL.glEnableVertexAttribArray(0)                # position
        GL.glVertexAttribPointer(
            0, 3, GL.GL_FLOAT, False, stride, ctypes.c_void_p(0))

        GL.glEnableVertexAttribArray(1)                # normal
        GL.glVertexAttribPointer(
            1, 3, GL.GL_FLOAT, False, stride, ctypes.c_void_p(12))

        # keep objects alive
        self.vbo.release()
        self.ebo.release()
        self.vao.release()

        self.count = int(mesh.indices.size)
