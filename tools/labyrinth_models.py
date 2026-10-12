# -*- coding: utf-8 -*-
"""
Blender models of "Das Dornenlabyrinth" (Zeki.Dornenlabyrinth). Run with Blender 4.2 LTS:

    blender -b -P tools/labyrinth_models.py -- path/to/Zeki.Dornenlabyrinth [path/to/previews]

Reuses the helpers of tools/verdornt_models.py (everything above its "the bodies" section, and export/render).

Outputs <mod>/assets/models/*.obj (+.mtl), loaded by the DLL (Models.cs):
  farbkranz        a glowing thorn gimbal of radius 1; the DLL tints it per node colour and scales it to the node
  wasserkristalle  a cluster of solid water crystals, about 40 m (Frostkammer)
  eisblock         an anglerfish skeleton frozen in a block of ice, 30 x 14 x 14 m (Frostkammer)
  wrack            the remains of a Hearthian ship, about 25 m (Wrackkammer)
  notiz            Gneis's floating raft with a note on a stake and a lantern
  herz             the Bramble Heart: a purple seed core in a thorn cage, small enough to carry
  herznest         the nest of roots the heart floats in, about 40 m (Herzkammer)

Coordinates: Blender Z-up -> Unity (-x, z, -y). 1 unit = 1 metre.
Material names are the contract with the DLL: DornRinde, DornEis, Knochen, Holz, Metall, Papier (opaque) and
Kranzlicht, Herzlicht, Laternenlicht (glow), Eisglas (translucent).
"""
import math
import os
import random
import sys

_HELPERS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "verdornt_models.py")
with open(_HELPERS, encoding="utf-8") as _f:
    _src = _f.read()
exec(compile(_src[:_src.index("the bodies\n")].rsplit("\n", 1)[0], _HELPERS, "exec"))  # noqa: S102
# and the export and render helpers (without Verdornt's main)
exec(compile(_src[_src.index("def export("):_src.index("def main():")], _HELPERS, "exec"))  # noqa: S102

import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

BLEND = os.path.join(os.path.dirname(MOD), "Zeki.Dornenlabyrinth.Source", "blender", "Dornenlabyrinth.blend")  # noqa: F821


def mats():
    def glass():
        m = material("Eisglas", (0.7, 0.88, 1.0), 0.0, 0.05)  # noqa: F821
        m.node_tree.nodes["Principled BSDF"].inputs["Alpha"].default_value = 0.3
        m.blend_method = "BLEND"
        return m

    return {
        "bark": material("DornRinde", (0.075, 0.07, 0.045), 0.0, 0.9),  # noqa: F821
        "ice": material("DornEis", (0.55, 0.68, 0.78), 0.1, 0.25),  # noqa: F821
        "bone": material("Knochen", (0.82, 0.78, 0.68), 0.0, 0.7),  # noqa: F821
        "wood": material("Holz", (0.45, 0.3, 0.18), 0.0, 0.8),  # noqa: F821
        "metal": material("Metall", (0.5, 0.52, 0.55), 0.7, 0.4),  # noqa: F821
        "paper": material("Papier", (0.92, 0.88, 0.76), 0.0, 0.9),  # noqa: F821
        "ring": material("Kranzlicht", (0.9, 1.0, 0.9), 0.0, 0.3, (0.9, 1.0, 0.9), 8.0),  # noqa: F821
        "heart": material("Herzlicht", (0.75, 0.3, 1.0), 0.0, 0.3, (0.7, 0.25, 1.0), 10.0),  # noqa: F821
        "lantern": material("Laternenlicht", (1.0, 0.8, 0.45), 0.0, 0.3, (1.0, 0.75, 0.35), 8.0),  # noqa: F821
        "glass": glass(),
    }


def along(d):
    """Rotation matrix turning +z into direction d."""
    return Vector((0, 0, 1)).rotation_difference(Vector(d).normalized()).to_matrix().to_4x4()


def farbkranz(M):
    """Three crossed rings of radius 1 with thorns pointing outwards, so the colour shows from every side."""
    parts = []
    rots = [Matrix.Identity(4), Matrix.Rotation(math.pi / 2, 4, "X"), Matrix.Rotation(math.pi / 2, 4, "Y")]
    for k, rot in enumerate(rots):
        parts.append(torus(f"kranz{k}", 1.0, 0.03, 0.0, M["ring"], seg=48, ring=6, matrix=rot))  # noqa: F821
        for i in range(10):
            a = TAU * (i + 0.5 * k) / 10  # noqa: F821
            d = rot @ Vector((math.cos(a), math.sin(a), 0))
            parts.append(cone_along(f"kranz{k}_dorn{i}", d * 1.0, d, 0.14, 0.035, 0.002, M["ring"], seg=5))  # noqa: F821
    return join("farbkranz", parts, uv_size=1.0)  # noqa: F821


def crystal(name, base, d, length, r, mat):
    """A hexagonal water crystal from base along d, with a pointed tip."""
    shaft = cylinder(name, r, r, 0, length * 0.8, mat, seg=6, matrix=Matrix.Translation(base) @ along(d))  # noqa: F821
    tip = cylinder(name + "_spitze", r, 0.02, length * 0.8, length, mat, seg=6, matrix=Matrix.Translation(base) @ along(d))  # noqa: F821
    return [shaft, tip]


def wasserkristalle(M):
    rnd = random.Random(41)
    parts = [sphere("kristallkern", 5.0, (0, 0, 0), M["ice"], seg=12, rings=8)]  # noqa: F821
    for i in range(26):
        d = random_axis(rnd)  # noqa: F821
        parts += crystal(f"kristall{i}", d * 3.5, d, rnd.uniform(9, 21), rnd.uniform(1.0, 2.8), M["ice"])
    return join("wasserkristalle", parts, uv_size=4.0)  # noqa: F821


def anglerfish_skeleton(M, length=24.0):
    """Bones of an anglerfish along +x: spine, ribs, skull with jaws and teeth, lure, tail fan."""
    b = M["bone"]
    L = length / 24.0
    spine = [Vector((x * L, 0, 0.6 * math.sin(x / 5.0) * L)) for x in range(-8, 13, 2)]
    parts = [tube("wirbelsaeule", spine, 0.35 * L, b, res=4, bevel=2)]
    for i, x in enumerate(range(-5, 9, 2)):
        h = (4.2 - abs(x - 1) * 0.35) * L
        for s in (1, -1):
            rib = [Vector((x * L, 0, 0)) + Vector((-0.4 * t * L, s * math.sin(t * 2.4) * h * 0.85, -math.sin(t * 1.6) * h * 0.7 + t * 0.6))
                   for t in (j / 6 for j in range(7))]
            parts.append(tube(f"rippe{i}{'lr'[s > 0]}", rib, 0.16 * L, b, res=3, bevel=2, taper=True))  # noqa: F821
    # skull: a flat dome over the jaws at the front (-x), closed (an open one flips when the normals are made consistent)
    skull = sphere("schaedel", 4.2 * L, (-11 * L, 0, 1.6 * L), b, scale=(1.3, 1.0, 0.45), seg=16, rings=10)  # noqa: F821
    parts.append(skull)
    for jaw, z, sgn in (("oberkiefer", 0.4, 1), ("unterkiefer", -2.4, -1)):
        pts = [Vector((-11 * L + 5.4 * L * math.cos(a), 4.2 * L * math.sin(a), z * L + sgn * 0.8 * L * math.cos(a)))
               for a in (math.radians(v) for v in range(-80, 260, 30))]
        pts = [p for p in pts if p.x < -8 * L or abs(p.y) > 3.8 * L]
        parts.append(tube(jaw, pts, 0.32 * L, b, res=3, bevel=2))  # noqa: F821
        for t, p in enumerate(pts[1:-1]):
            parts.append(cone_along(f"{jaw}_zahn{t}", p, Vector((0, 0, -sgn)), 1.6 * L, 0.28 * L, 0.02, b, seg=6))  # noqa: F821
    lure = [Vector((-9 * L, 0, 3.6 * L)), Vector((-12 * L, 0, 7 * L)), Vector((-16 * L, 0, 7.5 * L)), Vector((-18 * L, 0, 5 * L))]
    parts.append(tube("angel", lure, 0.12 * L, b, res=4, bevel=2))  # noqa: F821
    parts.append(sphere("koeder", 0.5 * L, lure[-1], b, seg=8, rings=6))  # noqa: F821
    for k in range(5):
        a = math.radians(-40 + 20 * k)
        fan = [Vector((12 * L, 0, 0)), Vector((12 * L + 4 * L * math.cos(a), 0, 4 * L * math.sin(a)))]
        parts.append(tube(f"schwanz{k}", fan, 0.14 * L, b, res=2, bevel=2))  # noqa: F821
    return parts


def eisblock(M):
    parts = anglerfish_skeleton(M, length=24.0)
    parts.append(box("eis", (34, 15, 15), (1, 0, 0), M["glass"], rot=(0.04, 0.02, 0.06)))  # noqa: F821
    return join("eisblock", parts, uv_size=6.0)  # noqa: F821


def wrack(M):
    """Wooden hull plates around a broken hull, the cockpit ring, a landing leg and a thruster."""
    rnd = random.Random(52)
    parts = [cylinder("rumpf", 3.0, 2.6, -5, 4, M["wood"], seg=12, cap=False, matrix=Matrix.Rotation(0.3, 4, "Y"))]  # noqa: F821
    parts.append(torus("cockpitring", 3.2, 0.35, 0.0, M["metal"], seg=32, ring=8,  # noqa: F821
                       matrix=Matrix.Translation((1.5, 0, 5.0)) @ Matrix.Rotation(0.5, 4, "X")))
    for i in range(14):
        d = random_axis(rnd)  # noqa: F821
        at = d * rnd.uniform(5, 12)
        parts.append(box(f"planke{i}", (rnd.uniform(3, 7), rnd.uniform(1.2, 2.2), 0.25), at, M["wood"],  # noqa: F821
                         rot=(rnd.uniform(0, TAU), rnd.uniform(0, TAU), rnd.uniform(0, TAU))))  # noqa: F821
    leg = Matrix.Translation((-6, 4, -3)) @ Matrix.Rotation(1.1, 4, "X")
    parts.append(cylinder("bein", 0.25, 0.25, 0, 6, M["metal"], seg=8, matrix=leg))  # noqa: F821
    parts.append(cylinder("fuss", 1.0, 1.0, 6, 6.3, M["metal"], seg=12, matrix=leg))  # noqa: F821
    parts.append(cylinder("duese", 1.6, 0.6, -8, -5, M["metal"], seg=12, matrix=Matrix.Rotation(0.3, 4, "Y")))  # noqa: F821
    return join("wrack", parts, uv_size=3.0)  # noqa: F821


def notiz(M):
    parts = [cylinder("floss", 1.4, 1.3, -0.15, 0.1, M["wood"], seg=12),  # noqa: F821
             cylinder("pfahl", 0.05, 0.05, 0.1, 1.5, M["wood"], seg=6),  # noqa: F821
             box("zettel", (0.6, 0.02, 0.8), (0, -0.07, 1.15), M["paper"], rot=(0.12, 0, 0)),  # noqa: F821
             cylinder("laternenstab", 0.03, 0.03, 0.1, 1.9, M["metal"], seg=6, at=(0.9, 0.5, 0)),  # noqa: F821
             sphere("laterne", 0.16, (0.9, 0.5, 2.0), M["lantern"], seg=10, rings=6)]  # noqa: F821
    return join("notiz", parts, uv_size=1.0)  # noqa: F821


def herz(M):
    """Small enough to carry (the DLL lets it pulse)."""
    rnd = random.Random(61)
    parts = [sphere("herzkern", 0.3, (0, 0, 0), M["heart"], seg=16, rings=10)]  # noqa: F821
    for k in range(6):
        u, w = basis(random_axis(rnd))  # noqa: F821
        ring = [(u * math.cos(a) + w * math.sin(a)) * 0.46 for a in (TAU * i / 12 for i in range(13))]  # noqa: F821
        parts.append(tube(f"kaefig{k}", ring, 0.028, M["bark"], res=3, bevel=2))  # noqa: F821
        for i in range(0, 12, 3):
            d = ring[i].normalized()
            parts.append(cone_along(f"kaefig{k}_dorn{i}", ring[i], d, 0.14, 0.03, 0.002, M["bark"], seg=5))  # noqa: F821
    return join("herz", parts, uv_size=0.5)  # noqa: F821


def herznest(M):
    """Woven roots around the heart, open towards Unity +z and -z (where one flies in)."""
    rnd = random.Random(73)
    avoid = ((Vector((0, 1, 0)), 0.55), (Vector((0, -1, 0)), 0.55))
    parts = []
    for k in range(26):
        parts += great_circle_vine(f"nestranke{k}", rnd.uniform(15, 20), rnd.uniform(0.5, 1.1), M["bark"], rnd,  # noqa: F821
                                   sink=0.4, waves=rnd.randint(4, 8), amp=0.08, n=40, arc=rnd.uniform(0.4, 0.75), avoid=avoid, res=3)
    return join("herznest", parts, uv_size=6.0)  # noqa: F821


def main():
    reset()  # noqa: F821
    os.makedirs(OUT, exist_ok=True)  # noqa: F821
    for f in os.listdir(OUT):  # noqa: F821
        if f.endswith((".obj", ".mtl")):
            os.remove(os.path.join(OUT, f))  # noqa: F821
    M = mats()
    models = {"farbkranz": farbkranz(M), "wasserkristalle": wasserkristalle(M), "eisblock": eisblock(M), "wrack": wrack(M),
              "notiz": notiz(M), "herz": herz(M), "herznest": herznest(M)}
    print("OBJ export:")
    for key, obj in models.items():
        export(obj, key + ".obj")  # noqa: F821
    if PREVIEWS:  # noqa: F821
        cam = scene_setup()  # noqa: F821
        os.makedirs(PREVIEWS, exist_ok=True)  # noqa: F821
        for k, (key, dist) in enumerate({"farbkranz": 4.5, "wasserkristalle": 75, "eisblock": 55, "wrack": 40, "notiz": 5.5, "herz": 2.0,
                                         "herznest": 70}.items()):
            at = Vector((k * 200, 0, 0))
            models[key].location = at
            render(cam, os.path.join(PREVIEWS, key + ".png"), at + Vector((dist * 0.7, -dist * 0.75, dist * 0.35)), at,  # noqa: F821
                   (800, 600), lens=35, show=[models[key].name])
            models[key].location = (0, 0, 0)
    os.makedirs(os.path.dirname(BLEND), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND, compress=True)
    print("saved", BLEND)


main()
