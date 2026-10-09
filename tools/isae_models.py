# -*- coding: utf-8 -*-
"""
Blender models of "Die Aussendungseinheit" (Zeki.ISAE). Run with Blender 4.2 LTS:

    blender -b -P tools/isae_models.py -- path/to/Zeki.ISAE [path/to/previews]

The centrepiece is built here: the Orbital Probe Cannon as it would look intact and finished in the style
of the Nomai Vessel - segmented armour around a glowing core, a long barrel with spinning coil rings and a
muzzle crown, swept tail fins, and three walkable modules (control, launch, navigation). Everything that
exists in the game (computers, recorders, crystals, the Vessel interface, the Nomai probe, lamps) is NOT
modelled; New Horizons copies those from the game into the spots this script exports.

Outputs
  * <mod>/assets/models/*.obj (+.mtl)     - the DLL loads them at runtime (Models.cs)
  * <mod>/assets/models/anchors.json      - spots on the models (Unity coordinates) for isae_build.py
  * <mod>/planets/assets/shiplog/...       - ship log photos and the map sprite, rendered with Cycles
  * Zeki.ISAE.Source/blender/ISAE.blend   - the editable scene
  * previews (optional second argument)

Coordinates: Blender is Z-up and right-handed, Unity is Y-up and left-handed. A Blender point (x, y, z)
ends up at Unity (-x, z, -y): the OBJ export (forward -Z, up Y) plus the x-mirror in the DLL's loader.
The cannon fires along Blender +Z = Unity +y, the same axis as the three focus cannons. 1 unit = 1 metre.

Material names are the contract with the DLL: VesselHuelle, VesselKupfer, VesselDunkel, VesselLeuchten.
"""
import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
MOD = os.path.abspath(ARGS[0] if ARGS else os.path.join(os.path.dirname(__file__), "..", "Zeki.ISAE"))
PREVIEWS = os.path.abspath(ARGS[1]) if len(ARGS) > 1 else None
OUT = os.path.join(MOD, "assets", "models")
SHIPLOG = os.path.join(MOD, "planets", "assets", "shiplog")
BLEND = os.path.join(os.path.dirname(MOD), "Zeki.ISAE.Source", "blender", "ISAE.blend")

TAU = math.tau
ANCHORS = {}

# ------------------------------------------------------------------------------------------ dimensions
HUB_R = 16.0
BARREL_START, BARREL_END = 20.0, 150.0
BARREL_R0, BARREL_R1 = 6.6, 5.0
MUZZLE_END = 160.0
TAIL_END = -42.0
MODULE_DIST = 50.0          # hub centre -> module centre
MODULE_R, MODULE_WALL = 9.6, 0.7
FLOOR_Z = -3.6              # floor of a module, relative to its centre
MODULES = (                 # key, name, azimuth (between the tail fins)
    ("kontrolle", "Kontrollmodul", 60.0),
    ("start", "Startmodul", 180.0),
    ("navigation", "Navigationsmodul", 300.0),
)


# ------------------------------------------------------------------------------------------ helpers
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def material(name, color, metallic=0.0, rough=0.5, emission=None, strength=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = rough
    if emission:
        bsdf.inputs["Emission Color"].default_value = (*emission, 1)
        bsdf.inputs["Emission Strength"].default_value = strength
    m.diffuse_color = (*color, 1)
    return m


def materials():
    # preview colours close to the Vessel; in game the DLL uses the Vessel's own materials
    return {
        "hull": material("VesselHuelle", (0.46, 0.36, 0.28), 0.5, 0.45),
        "copper": material("VesselKupfer", (0.72, 0.43, 0.22), 0.8, 0.35),
        "dark": material("VesselDunkel", (0.10, 0.09, 0.10), 0.4, 0.6),
        "glow": material("VesselLeuchten", (0.5, 0.82, 1.0), 0.0, 0.3, (0.4, 0.78, 1.0), 7.0),
    }


def link(name, bm, mat, smooth=True):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    ob.data.materials.append(mat)
    for p in ob.data.polygons:
        p.use_smooth = smooth
    return ob


def cylinder(name, r1, r2, z0, z1, mat, seg=32, at=(0, 0, 0), cap=True, matrix=None):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=cap, segments=seg, radius1=r1, radius2=r2, depth=z1 - z0,
                          matrix=Matrix.Translation((at[0], at[1], at[2] + (z0 + z1) / 2)))
    if matrix is not None:
        bmesh.ops.transform(bm, matrix=matrix, verts=bm.verts)
    return link(name, bm, mat)


def torus(name, R, r, z, mat, seg=64, ring=12, matrix=None):
    bm = bmesh.new()
    rings = []
    for i in range(seg):
        a = TAU * i / seg
        c, s = math.cos(a), math.sin(a)
        rings.append([bm.verts.new(((R + r * math.cos(b)) * c, (R + r * math.cos(b)) * s, z + r * math.sin(b)))
                      for b in (TAU * j / ring for j in range(ring))])
    for i in range(seg):
        A, B = rings[i], rings[(i + 1) % seg]
        for j in range(ring):
            bm.faces.new((A[j], B[j], B[(j + 1) % ring], A[(j + 1) % ring]))
    if matrix is not None:
        bmesh.ops.transform(bm, matrix=matrix, verts=bm.verts)
    return link(name, bm, mat)


def sphere(name, r, at, mat, scale=(1, 1, 1), seg=32, rings=16, keep=None):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=r)
    bmesh.ops.scale(bm, vec=scale, verts=bm.verts)
    if keep is not None:
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if not keep(f.calc_center_median())], context="FACES")
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    bmesh.ops.translate(bm, vec=at, verts=bm.verts)
    return link(name, bm, mat)


def box(name, size, at, mat, rot=(0, 0, 0)):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=size, verts=bm.verts)
    m = Matrix.Translation(at) @ (Matrix.Rotation(rot[2], 4, "Z") @ Matrix.Rotation(rot[1], 4, "Y") @ Matrix.Rotation(rot[0], 4, "X"))
    bmesh.ops.transform(bm, matrix=m, verts=bm.verts)
    return link(name, bm, mat, smooth=False)


def tube(name, points, radius, mat):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = radius
    cu.bevel_resolution = 4
    cu.resolution_u = 10
    cu.use_fill_caps = True
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(len(points) - 1)
    for bp, p in zip(sp.bezier_points, points):
        bp.co = p
        bp.handle_left_type = bp.handle_right_type = "AUTO"
    ob = bpy.data.objects.new(name, cu)
    bpy.context.collection.objects.link(ob)
    select(ob)
    bpy.ops.object.convert(target="MESH")
    ob = bpy.context.view_layer.objects.active
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    for p in ob.data.polygons:
        p.use_smooth = True
    return ob


def fin(name, profile, thickness, azimuth, mat):
    """A flat blade: profile is a list of (radius, z) points, extruded around the azimuth direction."""
    bm = bmesh.new()
    a = math.radians(azimuth)
    d, s = Vector((math.cos(a), math.sin(a), 0)), Vector((-math.sin(a), math.cos(a), 0))
    front = [bm.verts.new(d * r + Vector((0, 0, z)) + s * thickness / 2) for r, z in profile]
    back = [bm.verts.new(d * r + Vector((0, 0, z)) - s * thickness / 2) for r, z in profile]
    bm.faces.new(front)
    bm.faces.new(list(reversed(back)))
    n = len(profile)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((front[j], front[i], back[i], back[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return link(name, bm, mat, smooth=False)


def select(ob):
    for o in bpy.context.selected_objects:
        o.select_set(False)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob


def modifier(ob, kind, **settings):
    select(ob)
    m = ob.modifiers.new(kind.lower(), kind)
    for k, v in settings.items():
        setattr(m, k, v)
    bpy.ops.object.modifier_apply(modifier=m.name)


def cut(ob, cutters):
    for c in cutters:
        modifier(ob, "BOOLEAN", object=c, operation="DIFFERENCE", solver="EXACT")
        bpy.data.objects.remove(c, do_unlink=True)


def join(name, objs, uv_size=6.0):
    for o in bpy.context.selected_objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    if len(objs) > 1:
        bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name = ob.data.name = name
    # world-scaled box mapping, so the tiling textures of the game's Vessel materials keep a sensible size
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.cube_project(cube_size=uv_size, scale_to_bounds=False)
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    return ob


def polar(r, a_deg, z=0.0):
    a = math.radians(a_deg)
    return Vector((r * math.cos(a), r * math.sin(a), z))


def unity(p):
    return {"x": round(-p[0], 3), "y": round(p[2], 3), "z": round(-p[1], 3)}


def unity_dir(d):
    return {"x": round(-d[0], 4), "y": round(d[2], 4), "z": round(-d[1], 4)}


def yaw_to(p, target):
    """Unity yaw (degrees around +y) that turns a prop's +z from p towards target (Blender points)."""
    dx, dz = -(target[0] - p[0]), -(target[1] - p[1])
    return round(math.degrees(math.atan2(dx, dz)) % 360, 1)


def anchor(group, name, p, face=None, normal=None, **extra):
    a = {"position": unity(p)}
    if face is not None:
        a["yaw"] = yaw_to(p, face)
    if normal is not None:
        a["normal"] = unity_dir(normal)
    a.update(extra)
    ANCHORS.setdefault(group, {})[name] = a


# ------------------------------------------------------------------------------------------ the cannon
def hauptkanone(M):
    parts = []
    # hub: a glowing core inside six armour shells; the seams between the shells glow
    parts.append(sphere("core", HUB_R - 0.9, (0, 0, 0), M["glow"], (1, 1, 0.86), 48, 24))
    gap = 7.0

    def shell(c):
        az = math.degrees(math.atan2(c.y, c.x)) % 60.0
        return gap / 2 < az < 60 - gap / 2 and abs(c.z) < HUB_R * 0.74

    parts.append(sphere("shells", HUB_R, (0, 0, 0), M["hull"], (1, 1, 0.86), 96, 48, keep=shell))
    modifier(parts[-1], "SOLIDIFY", thickness=0.6, offset=1.0)
    for z, r in ((0.0, HUB_R + 0.2), (7.5, HUB_R * 0.86), (-7.5, HUB_R * 0.86)):
        parts.append(torus(f"hub_band{z}", r, 0.7, z, M["copper"], 96, 10))
    # poles: collar into the barrel and into the tail
    parts.append(cylinder("collar_top", 10.5, 7.6, 11.0, BARREL_START, M["hull"], 48))
    parts.append(torus("collar_top_ring", 9.4, 0.9, 14.0, M["copper"], 64, 10))
    parts.append(cylinder("collar_bottom", 7.5, 10.5, -12.5, -11.0, M["hull"], 48))
    # barrel with three ribs
    parts.append(cylinder("barrel", BARREL_R0, BARREL_R1, BARREL_START, BARREL_END, M["hull"], 48))
    for k in range(3):
        a = 30 + k * 120
        parts.append(tube(f"rib{k}", [polar(BARREL_R0 + 0.4, a, BARREL_START), polar(BARREL_R1 + 0.4, a, BARREL_END)], 0.55, M["dark"]))
    for z in range(30, int(BARREL_END), 15):  # glowing coil lines under the spinning rings
        r = BARREL_R0 + (BARREL_R1 - BARREL_R0) * (z - BARREL_START) / (BARREL_END - BARREL_START)
        parts.append(torus(f"coil{z}", r + 0.05, 0.22, z, M["glow"], 48, 6))
    # muzzle: flared mouth, dark throat, glowing lens and a crown of six Vessel fins
    parts.append(cylinder("muzzle", BARREL_R1, 7.6, BARREL_END, MUZZLE_END, M["hull"], 48, cap=False))
    parts.append(cylinder("throat", 4.4, 4.4, BARREL_END - 6, MUZZLE_END - 0.6, M["dark"], 32))
    parts.append(cylinder("lens", 4.0, 4.0, MUZZLE_END - 0.6, MUZZLE_END - 0.4, M["glow"], 32))
    parts.append(torus("muzzle_ring", 7.6, 0.6, MUZZLE_END, M["copper"], 64, 10))
    for k in range(6):
        a = k * 60
        parts.append(fin(f"crown{k}", [(6.4, BARREL_END - 4), (9.6, MUZZLE_END + 2), (10.8, MUZZLE_END + 9), (8.2, MUZZLE_END + 3)], 0.6, a, M["hull"]))
    # tail: cone, glowing exhaust ring and three swept fins
    parts.append(cylinder("tail", 9.0, 3.0, TAIL_END + 4, -12.5, M["hull"], 48))
    parts.append(torus("tail_ring", 6.4, 0.5, -22.0, M["copper"], 64, 8))
    parts.append(torus("tail_glow", 3.2, 0.4, TAIL_END + 4, M["glow"], 32, 8))
    for k in range(3):
        a = k * 120
        parts.append(fin(f"tailfin{k}", [(8.0, -8.0), (24.0, -26.0), (32.0, -46.0), (26.0, -50.0), (14.0, -38.0), (7.0, -30.0)], 1.4, a, M["hull"]))
        parts.append(fin(f"tailfin_edge{k}", [(24.0, -26.0), (32.0, -46.0), (31.0, -47.0), (23.4, -27.2)], 1.7, a, M["copper"]))
    # arms to the three modules (between the tail fins)
    for key, _, az in MODULES:
        parts.append(tube(f"arm_{key}", [polar(HUB_R - 1, az, 0), polar(MODULE_DIST - MODULE_R + 0.5, az, 0)], 1.7, M["hull"]))
        for dz in (-3.4, 3.4):
            parts.append(tube(f"strut_{key}{dz}", [polar(HUB_R - 2, az, dz * 0.6), polar(30, az, dz), polar(MODULE_DIST - MODULE_R + 1, az, dz * 0.5)], 0.6, M["dark"]))
        parts.append(torus(f"joint_{key}", 2.6, 0.6, 0, M["copper"], 32, 8,
                           matrix=Matrix.Translation(polar(MODULE_DIST - MODULE_R - 1.0, az)) @ Matrix.Rotation(math.radians(az), 4, "Z") @ Matrix.Rotation(math.pi / 2, 4, "Y")))
    obj = join("Hauptkanone", parts)

    anchor("isae", "kern", (0, 0, 0))
    anchor("isae", "muendung", (0, 0, MUZZLE_END + 1.0))
    anchor("isae", "heck", (0, 0, TAIL_END + 3))
    ANCHORS["isae"]["laenge"] = MUZZLE_END - TAIL_END
    return obj


def laufringe(M):
    """Coil rings around the barrel - a separate object so the DLL can spin it around the firing axis."""
    parts = []
    for i, z in enumerate(range(30, int(BARREL_END), 15)):
        r = BARREL_R0 + (BARREL_R1 - BARREL_R0) * (z - BARREL_START) / (BARREL_END - BARREL_START)
        parts.append(torus(f"ring{i}", r + 2.6, 0.95, z, M["copper"], 64, 10))
        parts.append(torus(f"ring_light{i}", r + 1.5, 0.22, z, M["glow"], 64, 6))
        for k in range(3):
            a = math.radians(k * 120 + i * 20)
            parts.append(box(f"clamp{i}_{k}", (2.2, 0.7, 1.6), ((r + 1.4) * math.cos(a), (r + 1.4) * math.sin(a), z), M["dark"], (0, 0, a)))
    return join("Laufringe", parts)


def module(M, key, name, az):
    """A walkable module: hollow armoured sphere with a door facing away from the hub, round windows,
    a floor, a ceiling light and the furniture of its room. Gravity (New Horizons) pulls towards the floor."""
    c = polar(MODULE_DIST, az)
    out = polar(1, az)                      # horizontal, away from the hub
    side = Vector((-out.y, out.x, 0))
    shell = sphere(f"{key}_shell", MODULE_R, c, M["hull"], (1, 1, 1), 64, 32)
    modifier(shell, "SOLIDIFY", thickness=MODULE_WALL, offset=-1.0)
    cutters = []
    door = box(f"{key}_door", (4.0, 3.4, 3.8), c + out * (MODULE_R - 0.2) + Vector((0, 0, FLOOR_Z + 1.9)), M["dark"], (0, 0, math.radians(az)))
    cutters.append(door)
    for k, wa in enumerate((-110, -60, 60, 110, 180)):
        d = polar(1, az + wa)
        w = cylinder(f"{key}_window{k}", 1.2, 1.2, -2.0, 2.0, M["dark"], 24,
                     matrix=Matrix.Translation(c + d * (MODULE_R - 0.3) + Vector((0, 0, 1.2))) @ Matrix.Rotation(math.radians(az + wa), 4, "Z") @ Matrix.Rotation(math.pi / 2, 4, "Y"))
        cutters.append(w)
    cut(shell, cutters)
    parts = [shell]
    inner = MODULE_R - MODULE_WALL
    floor_r = math.sqrt(inner ** 2 - FLOOR_Z ** 2) + 0.2
    parts.append(cylinder(f"{key}_floor", floor_r, floor_r, FLOOR_Z - 0.5, FLOOR_Z, M["dark"], 48, at=c))
    parts.append(torus(f"{key}_floor_light", floor_r - 1.2, 0.08, FLOOR_Z + 0.01, M["glow"], 64, 6, matrix=Matrix.Translation(c)))
    parts.append(torus(f"{key}_ceiling_light", 3.2, 0.18, 6.6, M["glow"], 48, 6, matrix=Matrix.Translation(c)))
    parts.append(torus(f"{key}_band", MODULE_R + 0.1, 0.5, 0.0, M["copper"], 96, 8, matrix=Matrix.Translation(c)))
    parts.append(torus(f"{key}_door_frame", 2.4, 0.3, 0, M["copper"], 32, 6,
                       matrix=Matrix.Translation(c + out * (MODULE_R - 0.1) + Vector((0, 0, FLOOR_Z + 2.0))) @ Matrix.Rotation(math.radians(az), 4, "Z") @ Matrix.Rotation(math.pi / 2, 4, "Y")))

    floor = lambda v: c + v + Vector((0, 0, FLOOR_Z))  # noqa: E731
    centre = floor(Vector((0, 0, 0)))
    A = ANCHORS.setdefault(key, {})
    A["name"] = name
    anchor(key, "boden", centre)
    anchor(key, "tuer", c + out * (MODULE_R + 2.5) + Vector((0, 0, FLOOR_Z + 1.0)))
    anchor(key, "licht1", c + Vector((0, 0, 4.5)))
    anchor(key, "licht2", floor(out * 4.5 + Vector((0, 0, 2.2))))
    A["bodenRadius"] = round(floor_r, 2)
    A["hoehe"] = round(inner - FLOOR_Z, 2)

    # a flat wall slab for Nomai wall writing, opposite the door
    slab_c = floor(-out * 5.4 + Vector((0, 0, 2.5)))
    parts.append(box(f"{key}_slab", (0.35, 6.8, 4.6), slab_c, M["hull"], (0, 0, math.radians(az))))
    parts.append(box(f"{key}_slab_frame", (0.2, 7.2, 0.25), slab_c + Vector((0, 0, 2.35)), M["copper"], (0, 0, math.radians(az))))
    anchor(key, "wand", slab_c + out * 0.2, normal=out)
    # spots at the sides
    anchor(key, "links", floor(side * 5.0 + out * 0.8), face=centre)
    anchor(key, "rechts", floor(-side * 5.0 + out * 0.8), face=centre)
    anchor(key, "mitte", centre, face=c + out * 10 + Vector((0, 0, FLOOR_Z)))
    anchor(key, "hinten_links", floor(side * 3.2 - out * 3.6), face=centre)
    anchor(key, "hinten_rechts", floor(-side * 3.2 - out * 3.6), face=centre)

    if key == "kontrolle":
        # raised dais where the main switch (the Vessel's coordinate interface) appears
        parts.append(cylinder("dais", 2.9, 2.6, FLOOR_Z, FLOOR_Z + 0.35, M["copper"], 48, at=c))
        parts.append(torus("dais_light", 2.75, 0.07, FLOOR_Z + 0.36, M["glow"], 48, 6, matrix=Matrix.Translation(c)))
        anchor(key, "schalter", floor(Vector((0, 0, 0.35))), face=c + out * 10)
    elif key == "start":
        # launch cradle that holds the interstellar probe until the finale
        parts.append(cylinder("cradle_base", 2.2, 1.6, FLOOR_Z, FLOOR_Z + 0.6, M["copper"], 32, at=c))
        for k in range(3):
            a = az + 90 + k * 120
            parts.append(tube(f"cradle_arm{k}", [floor(polar(1.4, a, 0.5)), floor(polar(1.9, a, 1.6)), floor(polar(1.2, a, 2.6))], 0.18, M["dark"]))
        anchor(key, "wiege", floor(Vector((0, 0, 2.3))))
    else:
        # star chart pedestal; the hologram above it is the separate, spinning "sternkarte" model
        parts.append(cylinder("chart_base", 1.6, 1.0, FLOOR_Z, FLOOR_Z + 1.1, M["copper"], 32, at=c))
        parts.append(torus("chart_rim", 1.05, 0.1, FLOOR_Z + 1.1, M["glow"], 32, 6, matrix=Matrix.Translation(c)))
        anchor(key, "karte", floor(Vector((0, 0, 3.4))))
    return join(f"Modul_{key}", parts)


def sternkarte(M):
    """Hologram of the target star and the stars around it (navigation module), spins in game."""
    parts = [sphere("target", 0.32, (0, 0, 0), M["glow"])]
    for k, (r, tilt) in enumerate(((0.9, 0.0), (1.4, 0.5), (1.9, -0.35))):
        parts.append(torus(f"orbit{k}", r, 0.025, 0, M["glow"], 64, 4, matrix=Matrix.Rotation(tilt, 4, "X")))
    for k in range(14):
        a, z = k * 137.5, math.sin(k * 1.7) * 0.9
        r = 1.0 + (k % 5) * 0.28
        parts.append(sphere(f"star{k}", 0.07 + 0.03 * (k % 3), polar(r, a, z), M["glow"], seg=8, rings=4))
    parts.append(tube("path", [(0, 0, 0), (0.8, 0.4, 0.6), (1.6, 1.2, 0.9), (2.3, 2.0, 0.6)], 0.03, M["copper"]))
    return join("Sternkarte", parts, uv_size=1.0)


# ------------------------------------------------------------------------------------------ export / render
def export(obj, filename):
    select(obj)
    bpy.ops.wm.obj_export(filepath=os.path.join(OUT, filename), export_selected_objects=True, forward_axis="NEGATIVE_Z", up_axis="Y",
                          export_triangulated_mesh=True, export_materials=True, export_uv=True, export_normals=True,
                          apply_modifiers=True, export_colors=False, path_mode="STRIP")
    tris = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    print(f"  {filename:24s} {len(obj.data.vertices):7d} verts {tris:7d} tris")


def scene_setup():
    scn = bpy.context.scene
    cam = bpy.data.objects.new("Kamera", bpy.data.cameras.new("Kamera"))
    scn.collection.objects.link(cam)
    sun = bpy.data.objects.new("Sonne", bpy.data.lights.new("Sonne", "SUN"))
    sun.data.energy = 4.5
    sun.data.color = (1.0, 0.82, 0.66)
    sun.rotation_euler = (math.radians(55), math.radians(15), math.radians(-30))
    scn.collection.objects.link(sun)
    fill = bpy.data.objects.new("Fuelllicht", bpy.data.lights.new("Fuelllicht", "SUN"))
    fill.data.energy = 1.2
    fill.data.color = (0.6, 0.75, 1.0)
    fill.rotation_euler = (math.radians(-60), math.radians(-20), math.radians(150))
    scn.collection.objects.link(fill)
    world = bpy.data.worlds.new("All")
    world.use_nodes = True
    nodes, links = world.node_tree.nodes, world.node_tree.links
    bg = nodes["Background"]
    bg.inputs[1].default_value = 1.0
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 900.0
    noise.inputs["Detail"].default_value = 0.0
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.8
    ramp.color_ramp.elements[0].color = (0.006, 0.005, 0.012, 1)
    ramp.color_ramp.elements[1].position = 0.83
    ramp.color_ramp.elements[1].color = (1.4, 1.4, 1.6, 1)
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], bg.inputs["Color"])
    scn.world = world
    scn.camera = cam
    scn.render.engine = "CYCLES"
    scn.cycles.device = "CPU"
    scn.cycles.samples = 40
    scn.cycles.use_denoising = True
    scn.view_settings.view_transform = "AgX"
    scn.view_settings.look = "AgX - Punchy"
    return cam


def render(cam, path, cam_loc, target, size=(512, 512), lens=35, hide=(), key_light=False):
    sun = bpy.data.objects["Sonne"]
    if key_light:  # light from over the camera's shoulder
        d = Vector(target) - (Vector(cam_loc) + Vector((0, 0, 25)) + (Vector(cam_loc) - Vector(target)).cross(Vector((0, 0, 1))).normalized() * 15)
        sun.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    else:
        sun.rotation_euler = (math.radians(55), math.radians(15), math.radians(-30))
    for o in bpy.context.scene.objects:
        if o.type == "MESH":
            o.hide_render = o.name in hide
    cam.data.lens = lens
    cam.data.clip_end = 5000
    cam.location = cam_loc
    cam.rotation_euler = (Vector(target) - Vector(cam_loc)).to_track_quat("-Z", "Y").to_euler()
    scn = bpy.context.scene
    scn.render.resolution_x, scn.render.resolution_y = size
    scn.render.filepath = path
    scn.render.film_transparent = False
    bpy.ops.render.render(write_still=True)


def main():
    reset()
    os.makedirs(OUT, exist_ok=True)
    for f in os.listdir(OUT):
        if f.endswith((".obj", ".mtl")):
            os.remove(os.path.join(OUT, f))
    M = materials()
    models = {"hauptkanone": hauptkanone(M), "laufringe": laufringe(M)}
    for key, name, az in MODULES:
        models["modul_" + key] = module(M, key, name, az)
    chart = sternkarte(M)
    models["sternkarte"] = chart
    print("OBJ export:")
    for key, obj in models.items():
        export(obj, key + ".obj")
    with open(os.path.join(OUT, "anchors.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(ANCHORS, f, ensure_ascii=False, indent=2)
        f.write("\n")

    # the chart hovers over its pedestal (the DLL puts it there in game, here only for the pictures)
    k = ANCHORS["navigation"]["karte"]["position"]
    chart.location = (-k["x"], -k["z"], k["y"])

    cam = scene_setup()
    E = os.path.join(SHIPLOG, "entries")
    os.makedirs(E, exist_ok=True)
    render(cam, os.path.join(E, "ZEKISAE_ISAE.png"), (150, -120, 95), (0, 0, 55), lens=34)

    def module_view(key, az, dist=30, height=7):
        c = polar(MODULE_DIST, az)
        return c + polar(dist, az + 22, height), c + polar(2, az, -1)
    for key, entry in (("kontrolle", "ZEKISAE_KONTROLLE"), ("start", "ZEKISAE_START"), ("navigation", "ZEKISAE_NAVI")):
        az = dict((m[0], m[2]) for m in MODULES)[key]
        loc, target = module_view(key, az)
        render(cam, os.path.join(E, entry + ".png"), loc, target, lens=35, key_light=True)
    # map sprite: the cannon seen from the side, on transparent background
    scn = bpy.context.scene
    scn.render.film_transparent = True
    os.makedirs(os.path.join(SHIPLOG, "map"), exist_ok=True)
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = 230
    cam.location, cam.rotation_euler = (0, -600, 55), (math.radians(90), 0, 0)
    scn.render.resolution_x = scn.render.resolution_y = 256
    scn.render.filepath = os.path.join(SHIPLOG, "map", "isae.png")
    bpy.ops.render.render(write_still=True)
    cam.data.type = "PERSP"
    scn.render.film_transparent = False
    if PREVIEWS:
        os.makedirs(PREVIEWS, exist_ok=True)
        render(cam, os.path.join(PREVIEWS, "isae_total.png"), (260, -200, 140), (0, 0, 55), (1280, 800), lens=32)
        render(cam, os.path.join(PREVIEWS, "isae_naben.png"), (70, -60, 30), (0, 0, 5), (1280, 800), lens=30)
        c = polar(MODULE_DIST, 60)
        render(cam, os.path.join(PREVIEWS, "kontrollmodul_innen.png"), c + polar(5.5, 60 + 25, FLOOR_Z + 2.4), c + polar(4, 60 + 180, FLOOR_Z + 2.0),
               (1280, 800), lens=18)

    os.makedirs(os.path.dirname(BLEND), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND, compress=True)
    print("saved", BLEND)


main()
