"""
mesh_utils  – OBJ loader + procedural icosphere
Copyright 2025  · public domain
"""
from __future__ import annotations
from pathlib import Path
import numpy as np

# ── ultra-lightweight mesh container ───────────────────────────────────
class Mesh:
    def __init__(self, v: np.ndarray, n: np.ndarray, i: np.ndarray):
        self.vertices = v.astype(np.float32)
        self.normals  = n.astype(np.float32)
        self.indices  = i.astype(np.uint32)

    def interleave(self) -> np.ndarray:
        """returns [x y z nx ny nz] float32 array ready for VBO"""
        return np.hstack([self.vertices, self.normals]).astype(np.float32)

# ── OBJ loader (triangulates n-gons, generates normals if absent) ──────
def load_obj(path: str | Path) -> Mesh:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    v, vn, faces = [], [], []
    for ln in path.read_text().splitlines():
        if ln.startswith("v "):              # vertex
            v.append([float(x) for x in ln.split()[1:4]])
        elif ln.startswith("vn"):            # normal
            vn.append([float(x) for x in ln.split()[1:4]])
        elif ln.startswith("f "):            # face: triangulate fan
            ids = [t.split('/') for t in ln.split()[1:]]
            idx = [int(p[0]) - 1 for p in ids]
            for i in range(1, len(idx) - 1):
                faces.append([idx[0], idx[i], idx[i+1]])
    v  = np.asarray(v,  np.float32)
    f  = np.asarray(faces, np.int32)
    if vn:                                   # normals exist
        vn = np.asarray(vn, np.float32)
    else:                                    # compute vertex normals
        vn = np.zeros_like(v)
        for tri in f:
            p, q, r = v[tri]
            n = np.cross(q - p, r - p)
            n /= np.linalg.norm(n) + 1e-9
            vn[tri] += n
        vn /= np.linalg.norm(vn, axis=1, keepdims=True) + 1e-9
    return Mesh(v, vn, f.flatten())

# ── unit icosahedron vertices / indices ────────────────────────────────
t = (1 + 5 ** 0.5) / 2
ICO_VERTS = np.array([
    [-1,  t,  0], [ 1,  t,  0], [-1, -t,  0], [ 1, -t,  0],
    [ 0, -1,  t], [ 0,  1,  t], [ 0, -1, -t], [ 0,  1, -t],
    [ t,  0, -1], [ t,  0,  1], [-t,  0, -1], [-t,  0,  1]], np.float32)
ICO_FACES = np.array([
    [0,11,5],[0,5,1],[0,1,7],[0,7,10],[0,10,11],
    [1,5,9],[5,11,4],[11,10,2],[10,7,6],[7,1,8],
    [3,9,4],[3,4,2],[3,2,6],[3,6,8],[3,8,9],
    [4,9,5],[2,4,11],[6,2,10],[8,6,7],[9,8,1]], np.uint32)

# ── recursive icosphere ────────────────────────────────────────────────
def create_icosphere(r: float = 1.0, subdivisions: int = 2) -> Mesh:
    verts = ICO_VERTS.copy()
    faces = ICO_FACES.copy()

    for _ in range(max(0, subdivisions)):
        new_faces = []
        mid_cache: dict[tuple[int,int], int] = {}

        def midpoint(a: int, b: int) -> int:
            key = tuple(sorted((a, b)))
            if key in mid_cache:
                return mid_cache[key]
            nonlocal verts
            mid = (verts[a] + verts[b]) / 2
            mid /= np.linalg.norm(mid) + 1e-9
            verts = np.vstack([verts, mid])
            mid_cache[key] = len(verts) - 1
            return mid_cache[key]

        for tri in faces:
            v1, v2, v3 = tri
            a = midpoint(v1, v2)
            b = midpoint(v2, v3)
            c = midpoint(v3, v1)
            new_faces.extend([[v1, a, c], [v2, b, a], [v3, c, b], [a, b, c]])
        faces = np.asarray(new_faces, np.uint32)

    verts *= r
    norms = verts / (np.linalg.norm(verts, axis=1, keepdims=True) + 1e-9)
    return Mesh(verts, norms, faces.flatten())
