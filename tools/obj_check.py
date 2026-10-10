# -*- coding: utf-8 -*-
"""
Checks the OBJ files of a mod folder the way the mods' DLLs load them: x mirrored, winding flipped (Blender ->
Unity). Every triangle's geometric normal must agree with its vertex normals, otherwise the face would be
invisible from outside in game.

Usage:  python tools/obj_check.py <folder with .obj files>     exit code 1 if any face is flipped
"""
import glob
import os
import sys


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def check(path):
    """Returns (good, flipped) triangle counts."""
    verts, normals, good, flipped = [], [], 0, 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            t = line.split()
            if not t:
                continue
            if t[0] == "v":
                verts.append((-float(t[1]), float(t[2]), float(t[3])))
            elif t[0] == "vn":
                normals.append((-float(t[1]), float(t[2]), float(t[3])))
            elif t[0] == "f":
                idx = [(p.split("/") + ["", ""])[:3] for p in t[1:]]
                for i in range(1, len(idx) - 1):
                    # the loader's triangle order: first, i+1, i
                    tri = (idx[0], idx[i + 1], idx[i])
                    pa, pb, pc = (verts[int(v[0]) - 1] for v in tri)
                    n = cross(sub(pb, pa), sub(pc, pa))
                    if dot(n, n) < 1e-18 or not all(v[2] for v in tri):
                        continue
                    vn = [normals[int(v[2]) - 1] for v in tri]
                    s = (vn[0][0] + vn[1][0] + vn[2][0], vn[0][1] + vn[1][1] + vn[2][1], vn[0][2] + vn[1][2] + vn[2][2])
                    if dot(n, s) > 0:
                        good += 1
                    else:
                        flipped += 1
    return good, flipped


def main():
    folder = sys.argv[1]
    bad = 0
    for path in sorted(glob.glob(os.path.join(folder, "*.obj"))):
        good, flipped = check(path)
        bad += flipped
        print(f"{os.path.basename(path):30s} ok={good:7d} flipped={flipped:6d}")
    print(f"{bad} flipped faces")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
