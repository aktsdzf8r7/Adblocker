# -*- coding: utf-8 -*-
"""
Blender models of "Verdornt" (Zeki.Verdornt). Run with Blender 4.2 LTS:

    blender -b -P tools/verdornt_models.py -- path/to/Zeki.Verdornt [path/to/previews]

Everything that exists in the game (Nomai computers, lamps, the bramble seed, nodes, vines of Dark Bramble) is
NOT modelled; New Horizons copies those. Modelled here are the bodies of Dornenkranz - each one "like Dark
Bramble, only different" - and the Nomai buildings of the three lost Nomai.

Outputs
  * <mod>/assets/models/*.obj (+.mtl)   loaded by the DLL (Models.cs)
  * <mod>/assets/models/anchors.json    spots on the models (Unity coordinates) for verdornt_build.py
  * <mod>/planets/assets/shiplog/...     ship log pictures rendered with Cycles
  * Zeki.Verdornt.Source/blender/Verdornt.blend
  * previews (optional second argument)

Coordinates: Blender Z-up -> Unity (-x, z, -y), as in tools/isae_models.py. 1 unit = 1 metre.
Material names are the contract with the DLL (Models.cs): DornRinde, DornEis, DornGlut, DornKristall,
NomaiHuelle, NomaiKupfer (opaque) and Keimlicht, Sternlicht, NomaiLeuchten (glow).
"""
import json
import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
MOD = os.path.abspath(ARGS[0] if ARGS else os.path.join(os.path.dirname(__file__), "..", "Zeki.Verdornt"))
PREVIEWS = os.path.abspath(ARGS[1]) if len(ARGS) > 1 else None
OUT = os.path.join(MOD, "assets", "models")
SHIPLOG = os.path.join(MOD, "planets", "assets", "shiplog")
BLEND = os.path.join(os.path.dirname(MOD), "Zeki.Verdornt.Source", "blender", "Verdornt.blend")

TAU = math.tau
ANCHORS = {}

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


def tube(name, points, radius, mat, res=10, bevel=4, taper=False):
    """A round tube along points. taper: thin out to a point at both ends (vines; no end caps needed)."""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = radius
    cu.bevel_resolution = bevel
    cu.resolution_u = res
    cu.use_fill_caps = not taper
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(len(points) - 1)
    n = len(points)
    for i, (bp, p) in enumerate(zip(sp.bezier_points, points)):
        bp.co = p
        bp.handle_left_type = bp.handle_right_type = "AUTO"
        if taper:
            bp.radius = max(0.02, min(1.0, min(i, n - 1 - i) / 3.0))
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
    # sharp edges (thorn bases, vine caps) keep their own normals; averaged normals there point backwards
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(50))
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


def link_multi(name, bm, mats):
    """Mesh with several materials; faces carry their material_index."""
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    for m in mats:
        ob.data.materials.append(m)
    return ob


def cone_along(name, base, direction, length, r1, r2, mat, seg=16):
    """A cone from base along direction (spikes)."""
    d = Vector(direction).normalized()
    rot = Vector((0, 0, 1)).rotation_difference(d).to_matrix().to_4x4()
    return cylinder(name, r1, r2, 0, length, mat, seg, matrix=Matrix.Translation(base) @ rot)


def prism(name, profile, zs, az, mats, inner_mat=None, outer_mat=None):
    """Extrude a cross-section (radial, tangential) along z at the given azimuth - used for the rails."""
    a = math.radians(az)
    d, s = Vector((math.cos(a), math.sin(a), 0)), Vector((-math.sin(a), math.cos(a), 0))
    bm = bmesh.new()
    loops = [[bm.verts.new(d * r + s * t + Vector((0, 0, z))) for r, t in profile] for z in zs]
    n = len(profile)
    for i in range(len(zs) - 1):
        for j in range(n):
            f = bm.faces.new((loops[i][j], loops[i][(j + 1) % n], loops[i + 1][(j + 1) % n], loops[i + 1][j]))
            f.material_index = inner_mat if (j == 0 and inner_mat is not None) else (outer_mat if (j == 3 and outer_mat is not None) else 0)
    bm.faces.new(list(reversed(loops[0])))
    bm.faces.new(loops[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return link_multi(name, bm, mats)




# ------------------------------------------------------------------------------------------ materials
def materials():
    """Preview colours; in game the DLL takes the bark from Dark Bramble's vines where it can (Models.cs)."""
    return {
        "bark": material("DornRinde", (0.075, 0.07, 0.045), 0.0, 0.9),
        "ice": material("DornEis", (0.55, 0.68, 0.78), 0.1, 0.25),
        "ember": material("DornGlut", (1.0, 0.3, 0.08), 0.0, 0.4, (1.0, 0.25, 0.05), 6.0),
        "crystal": material("DornKristall", (0.52, 0.35, 0.85), 0.2, 0.15, (0.45, 0.25, 0.9), 0.8),
        "hull": material("NomaiHuelle", (0.46, 0.36, 0.28), 0.5, 0.45),
        "copper": material("NomaiKupfer", (0.72, 0.43, 0.22), 0.8, 0.35),
        "seed": material("Keimlicht", (0.7, 1.0, 0.75), 0.0, 0.3, (0.55, 1.0, 0.6), 8.0),
        "star": material("Sternlicht", (1.0, 0.85, 0.5), 0.0, 0.3, (1.0, 0.8, 0.4), 12.0),
        "nomai_glow": material("NomaiLeuchten", (0.5, 0.82, 1.0), 0.0, 0.3, (0.4, 0.78, 1.0), 7.0),
        "glass": glass_material(),
    }


def glass_material():
    m = material("NomaiGlas", (0.75, 0.9, 1.0), 0.0, 0.05)
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Alpha"].default_value = 0.25
    m.blend_method = "BLEND"
    return m


# ------------------------------------------------------------------------------------------ bramble pieces
def random_axis(rnd):
    z = rnd.uniform(-1, 1)
    a = rnd.uniform(0, TAU)
    s = math.sqrt(1 - z * z)
    return Vector((s * math.cos(a), s * math.sin(a), z))


def thorned_tube(name, points, radius, mat, thorn_every=3, thorn_scale=2.4, rnd=None):
    """A bramble vine through points, with pairs of thorns."""
    parts = [tube(name, points, radius, mat, res=5, bevel=2, taper=True)]
    for i in range(1, len(points) - 1, thorn_every):
        p, q = Vector(points[i]), Vector(points[i + 1])
        side = (q - p).cross(Vector(p).normalized() if Vector(p).length > 0.01 else Vector((0, 0, 1)))
        if side.length < 0.01:
            side = Vector((1, 0, 0))
        side.normalize()
        for sgn in (1, -1):
            d = side * sgn + (q - p).normalized() * 0.4
            parts.append(cone_along(f"{name}_t{i}{sgn}", p + side * sgn * radius * 0.8, d, radius * thorn_scale, radius * 0.45, 0.05, mat, 6))
    return parts


def great_circle_vine(name, R, radius, mat, rnd, sink=0.3, waves=7, amp=0.04, n=64, arc=1.0, avoid=()):
    """A vine along a (partial) great circle around the body, bulging in and out of the surface.
    avoid: (direction, angular radius) areas the circle must stay clear of (camp, arrival seed)."""
    margin = radius / R + 0.05
    for _ in range(200):
        axis = random_axis(rnd)
        if all(abs(math.pi / 2 - axis.angle(d)) > w + margin for d, w in avoid):
            break
    ref = axis.cross(Vector((0, 0, 1)) if abs(axis.z) < 0.9 else Vector((1, 0, 0))).normalized()
    other = axis.cross(ref)
    start = rnd.uniform(0, TAU)
    phase = rnd.uniform(0, TAU)
    pts = []
    for i in range(n + (0 if arc < 1 else 1)):
        u = start + TAU * arc * i / n
        d = ref * math.cos(u) + other * math.sin(u)
        r = R * (1 + amp * math.sin(waves * u + phase)) + radius * (1 - 2 * sink)
        pts.append(d * r)
    return thorned_tube(name, pts, radius, mat, 3)


def surface_thorns(name, R, count, length, mat, rnd, exclude=(), base=0.12):
    parts = []
    for k in range(count):
        d = random_axis(rnd)
        if any(d.angle(e) < w for e, w in exclude):
            continue
        L = length * rnd.uniform(0.5, 1.4)
        parts.append(cone_along(f"{name}{k}", d * R * 0.99, d + random_axis(rnd) * 0.25, L, L * base, 0.08, mat, 7))
    return parts


def displaced_ball(name, R, mat, strength, scale, seed, flats=()):
    """An icosphere with cloudy displacement; areas in flats (direction, angular radius) stay at exactly R."""
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=5, radius=R)
    ob = link(name, bm, mat)
    tex = bpy.data.textures.new(name + "_noise", "CLOUDS")
    tex.noise_scale = scale
    tex.noise_depth = 3
    random.seed(seed)
    m = ob.modifiers.new("disp", "DISPLACE")
    m.texture = tex
    m.strength = strength
    m.mid_level = 0.5
    m.texture_coords = "OBJECT"
    select(ob)
    bpy.ops.object.modifier_apply(modifier="disp")
    for v in ob.data.vertices:
        d = v.co.normalized()
        for f, w in flats:
            a = d.angle(f)
            if a < w * 1.6:
                k = 1.0 if a < w else 1 - (a - w) / (w * 0.6)
                v.co = v.co.lerp(d * R, k)
    return ob


def direction(lat, lon):
    la, lo = math.radians(lat), math.radians(lon)
    return Vector((math.cos(la) * math.cos(lo), math.cos(la) * math.sin(lo), math.sin(la)))


def surface_anchor(group, name, R, d, up=0.0, face=None):
    """A spot on a body's surface, with the outward normal (Unity coordinates)."""
    p = d * (R + up)
    anchor(group, name, p, face=face, normal=d)


# ------------------------------------------------------------------------------------------ the bodies
ERSTLING_R = 260.0
ERSTLING_LAGER = direction(32, 70)
ERSTLING_ANKUNFT = direction(26, 52)


def erstling(M):
    """The arrival planet: ice-armoured and bare, closest to the real Dark Bramble - but ice plates over bark."""
    rnd = random.Random(11)
    flats = ((ERSTLING_LAGER, 0.17), (ERSTLING_ANKUNFT, 0.07))
    parts = [displaced_ball("erstling_kern", ERSTLING_R, M["bark"], 34, ERSTLING_R * 0.16, 11, flats)]
    excl = [(f, w * 1.3) for f, w in flats]
    for k in range(9):
        parts += great_circle_vine(f"vine{k}", ERSTLING_R, rnd.uniform(7, 13), M["bark"], rnd, sink=0.35, arc=rnd.uniform(0.35, 0.8), avoid=excl)
    # ice: clusters of slanted crystal shards growing out of the bark, like the ice crust of Dark Bramble
    for k in range(60):
        c = random_axis(rnd)
        if any(c.angle(e) < w for e, w in excl):
            continue
        for j in range(rnd.randint(4, 9)):
            d = (c + random_axis(rnd) * 0.06).normalized()
            L = rnd.uniform(8, 30)
            lean = (d + random_axis(rnd) * 0.6).normalized()
            parts.append(cone_along(f"eis{k}_{j}", d * (ERSTLING_R - 4), lean, L, L * rnd.uniform(0.25, 0.45), L * 0.03, M["ice"], 5))
    parts += surface_thorns("eisdorn", ERSTLING_R, 70, 38, M["ice"], rnd, excl)
    parts += surface_thorns("dorn", ERSTLING_R, 60, 26, M["bark"], rnd, excl)
    ob = join("Erstling", parts, uv_size=12.0)
    G = "erstling"
    surface_anchor(G, "ankunft", ERSTLING_R, ERSTLING_ANKUNFT)
    surface_anchor(G, "lager", ERSTLING_R, ERSTLING_LAGER)
    ANCHORS[G]["radius"] = ERSTLING_R
    return ob


def glutdorn(M):
    """Glowing red vines around a lava core: bark with ember cracks, glowing thorn tips."""
    rnd = random.Random(23)
    R = 220.0
    parts = [displaced_ball("glut_kern", R, M["bark"], 24, R * 0.18, 23)]
    for k in range(12):
        parts += great_circle_vine(f"vine{k}", R, rnd.uniform(8, 15), M["bark"], rnd, sink=0.2, amp=0.07, arc=rnd.uniform(0.4, 1.0))
    # ember cracks: thin glowing tubes along random walks over the surface
    for k in range(26):
        d = random_axis(rnd)
        pts = []
        heading = random_axis(rnd).cross(d).normalized()
        for i in range(14):
            pts.append(d * (R + 0.5))
            heading = (heading + random_axis(rnd) * 0.35).normalized()
            heading = (heading - d * heading.dot(d)).normalized()
            d = (d + heading * 0.035).normalized()
        parts.append(tube(f"riss{k}", pts, rnd.uniform(1.0, 2.2), M["ember"], res=4, bevel=1))
    for k in range(80):
        d = random_axis(rnd)
        L = rnd.uniform(14, 40)
        parts.append(cone_along(f"glutdorn{k}", d * R * 0.99, d, L, L * 0.13, 0.08, M["bark"], 7))
        parts.append(sphere(f"glutspitze{k}", L * 0.06, d * (R + L * 0.92), M["ember"], seg=8, rings=4))
    ob = join("Glutdorn", parts, uv_size=12.0)
    ANCHORS.setdefault("glutdorn", {})["radius"] = R
    return ob


def nebelranke_ranken(M):
    """The gas giant: green fog (New Horizons) - here only the giant drifting vines that loop through it."""
    rnd = random.Random(37)
    R = 640.0
    parts = []
    for k in range(16):
        parts += great_circle_vine(f"ranke{k}", R * rnd.uniform(0.7, 1.15), rnd.uniform(14, 26), M["bark"], rnd,
                                   sink=0.5, waves=5, amp=0.12, n=72, arc=rnd.uniform(0.3, 0.75))
    for k in range(10):
        c = random_axis(rnd) * R * rnd.uniform(0.6, 1.0)
        parts.append(sphere(f"samenleuchte{k}", rnd.uniform(4, 9), c, M["seed"], seg=12, rings=6))
    ob = join("Nebelranke", parts, uv_size=16.0)
    ANCHORS.setdefault("nebelranke", {})["radius"] = R
    return ob


def hohlsamen(M):
    """A giant seed broken open: a thick shell with a jagged opening, crystal thorns growing inwards."""
    rnd = random.Random(41)
    R = 300.0
    shell = displaced_ball("hohl_schale", R, M["bark"], 14, R * 0.3, 41)
    m = shell.modifiers.new("dicke", "SOLIDIFY")
    m.thickness = 22
    m.offset = -1
    select(shell)
    bpy.ops.object.modifier_apply(modifier="dicke")
    opening = direction(10, 200)
    cutters = [sphere("loch", R * 0.55, opening * R, M["bark"], seg=24, rings=12)]
    for k in range(7):
        jag = (opening + random_axis(rnd) * 0.35).normalized()
        cutters.append(sphere(f"zacke{k}", R * rnd.uniform(0.12, 0.22), jag * R, M["bark"], seg=12, rings=6))
    cut(shell, cutters)
    parts = [shell]
    for k in range(70):
        d = random_axis(rnd)
        if d.angle(opening) < 0.7:
            continue
        L = rnd.uniform(18, 60)
        parts.append(cone_along(f"kristall{k}", d * (R - 20), -d + random_axis(rnd) * 0.3, L, L * 0.12, 0.3, M["crystal"], 6))
    for k in range(40):
        d = random_axis(rnd)
        if d.angle(opening) < 0.8:
            continue
        L = rnd.uniform(16, 36)
        parts.append(cone_along(f"dorn{k}", d * R * 0.99, d, L, L * 0.12, 0.08, M["bark"], 7))
    # the husk of a seed: ridges from pole to pole, broken where the shell burst open
    for k in range(18):
        lon = k * 20.0 + rnd.uniform(-4, 4)
        pts = []
        for i in range(41):
            lat = -88 + 176 * i / 40
            d = direction(lat, lon)
            if d.angle(opening) < 0.75:
                if len(pts) > 2:
                    parts.append(tube(f"rippe{k}_{i}", pts, rnd.uniform(5, 8), M["bark"], res=5, bevel=2, taper=True))
                pts = []
                continue
            pts.append(d * (R + 3))
        if len(pts) > 2:
            parts.append(tube(f"rippe{k}", pts, rnd.uniform(5, 8), M["bark"], res=5, bevel=2, taper=True))
    for k in range(6):
        parts += great_circle_vine(f"vine{k}", R, rnd.uniform(8, 12), M["bark"], rnd, sink=0.3, arc=rnd.uniform(0.3, 0.6))
    ob = join("Hohlsamen", parts, uv_size=12.0)
    G = "hohlsamen"
    surface_anchor(G, "oeffnung", R, opening)
    ANCHORS[G]["radius"] = R
    return ob


HERZ_R = 1100.0


def herzdorn_kaefig(M):
    """The sun-bramble: thick woven vines around the captive star; starlight veins run along some vines."""
    rnd = random.Random(53)
    parts = []
    for k in range(34):
        r = HERZ_R * rnd.uniform(0.93, 1.06)
        thick = rnd.uniform(28, 52)
        parts += great_circle_vine(f"geflecht{k}", r, thick, M["bark"], rnd, sink=0.5, waves=9, amp=0.05, n=80,
                                   arc=rnd.uniform(0.45, 1.0))
    for k in range(10):
        parts += great_circle_vine(f"ader{k}", HERZ_R * 0.9, rnd.uniform(4, 8), M["star"], rnd, sink=0.5, waves=9, amp=0.04, n=64,
                                   arc=rnd.uniform(0.3, 0.7))
    parts += surface_thorns("kronendorn", HERZ_R * 1.05, 60, 260, M["bark"], rnd, base=0.1)
    ob = join("Herzdorn_Kaefig", parts, uv_size=30.0)
    ANCHORS.setdefault("herzdorn", {})["radius"] = HERZ_R
    return ob


AUSGUCK_LANDING = -22.0


def ausguck(M):
    """The Nomai lookout high above the system: a round platform with the system pool, a warp pad and lamps."""
    parts = [
        cylinder("deck", 18, 18, -1.2, 0, M["hull"], 64),
        torus("rand", 18, 0.6, -0.3, M["copper"], 96, 8),
        cylinder("kiel", 1.2, 12, -14, -1.2, M["hull"], 48),
        torus("kiel_licht", 7, 0.3, -7, M["nomai_glow"], 64, 6),
        torus("inlay", 15, 0.12, 0.01, M["nomai_glow"], 96, 6),
    ]
    for k in range(6):
        a = k * 60.0 + 30
        parts.append(tube(f"pfosten{k}", [polar(17, a, 0), polar(17.3, a, 4), polar(16.5, a, 6.5)], 0.25, M["copper"]))
        parts.append(sphere(f"pfosten_licht{k}", 0.5, polar(16.5, a, 6.8), M["nomai_glow"], seg=12, rings=6))
    # the landing below the deck with the warp pad, and the lift shaft between them
    landing = polar(12, 180, AUSGUCK_LANDING)
    parts += [
        cylinder("landung", 6, 6, AUSGUCK_LANDING - 0.8, AUSGUCK_LANDING, M["hull"], 48, at=(landing.x, landing.y, 0)),
        torus("landung_rand", 6, 0.4, 0, M["copper"], 64, 6, matrix=Matrix.Translation(landing + Vector((0, 0, -0.2)))),
        tube("strebe", [landing + Vector((3, 0, -0.8)), polar(4, 180, -8), polar(1, 180, -12)], 0.6, M["hull"]),
    ]
    for k in range(4):
        a = 180 + (k - 1.5) * 9
        parts.append(tube(f"schacht{k}", [polar(15.5, a, AUSGUCK_LANDING), polar(15.5, a, 3)], 0.18, M["copper"]))
    ob = join("Ausguck", parts, uv_size=6.0)
    G = "ausguck"
    anchor(G, "becken", polar(7, 0), face=(0, 0, 0))
    anchor(G, "warp", landing)
    anchor(G, "steinplatz", polar(11, 300), face=(0, 0, 0))
    anchor(G, "lift_unten", polar(15.5, 180, AUSGUCK_LANDING))
    anchor(G, "lift_oben", polar(15.5, 180, 0))
    anchor(G, "landung", landing)
    ANCHORS[G]["deckRadius"] = 18.0
    return ob


# ------------------------------------------------------------------------------------------ Nomai buildings
TUBE_R = 0.55   # inner radius of a marble tube (the marble is 0.45 m)


def record_tube(name, points, slots, frame=None):
    """Anchors of a marble tube: its path (Unity points, in the frame of the model) and the arc length of each slot."""
    lengths = [0.0]
    for a, b in zip(points, points[1:]):
        lengths.append(lengths[-1] + (Vector(b) - Vector(a)).length)
    ANCHORS["roehre_" + name] = {"pfad": [unity(p) for p in points], "mulden": {k: round(lengths[i], 3) for k, i in slots.items()},
                                 "rahmen": frame or "Koerper"}


def marble_tube(name, points, slots, M, frame=None, record_matrix=None):
    """A glass tube with copper rings and a copper cup at every slot (the marble itself is copied from the game).
    record_matrix: the transform the finished model gets (its anchors must be in the exported frame)."""
    record_tube(name, [record_matrix @ Vector(p) for p in points] if record_matrix else points, slots, frame)
    parts = [tube(f"{name}_glas", points, TUBE_R + 0.08, M["glass"], res=8, bevel=3)]
    for i, p in enumerate(points):
        if i % 3 == 0 or i in slots.values():
            q = Vector(points[min(i + 1, len(points) - 1)]) - Vector(points[max(i - 1, 0)])
            rot = q.normalized().to_track_quat("Z", "Y").to_matrix().to_4x4()
            parts.append(torus(f"{name}_ring{i}", TUBE_R + 0.15, 0.07, 0, M["copper"], 24, 6, matrix=Matrix.Translation(p) @ rot))
    for k, i in slots.items():
        p = Vector(points[i])
        parts.append(sphere(f"{name}_mulde_{k}", 0.22, p - Vector((0, 0, TUBE_R + 0.1)), M["nomai_glow"], seg=12, rings=6))
    return parts


def dome(name, at, r, door_az, M):
    """A Nomai hut: a half dome with a copper band and a door facing door_az."""
    at = Vector(at)
    shell = sphere(name, r, at, M["hull"], scale=(1, 1, 0.85), keep=lambda c: c.z > -0.2)  # keep tests before the move
    m = shell.modifiers.new("dicke", "SOLIDIFY")
    m.thickness = 0.4
    select(shell)
    bpy.ops.object.modifier_apply(modifier="dicke")
    door = box(name + "_tuer", (3.0, r * 1.2, 4.2), at + polar(r * 0.8, door_az, 2.0), M["hull"], rot=(0, 0, math.radians(door_az)))
    cut(shell, [door])
    parts = [shell, torus(name + "_band", r * 0.98, 0.18, 1.6, M["copper"], 64, 8, matrix=Matrix.Translation(at)),
             torus(name + "_licht", r * 0.55, 0.08, r * 0.8, M["nomai_glow"], 48, 6, matrix=Matrix.Translation(at))]
    return parts


def lager_frame():
    """Camp frame: local z = the outward normal at the camp spot on Erstling, origin on the surface."""
    d = ERSTLING_LAGER
    return Matrix.Translation(d * ERSTLING_R) @ d.to_track_quat("Z", "Y").to_matrix().to_4x4()


def to_planet(objs, frame):
    for o in objs:
        o.data.transform(frame)
    return objs


def lager(M):
    """The camp of Hyssop, Rue and Tansy on Erstling (built in a local frame, exported in planet coordinates)."""
    F = lager_frame()
    parts = [cylinder("plattform", 26, 26.5, -1.4, 0.0, M["hull"], 96), torus("plattform_rand", 26.2, 0.35, -0.1, M["copper"], 128, 8),
             torus("plattform_inlay", 18, 0.1, 0.01, M["nomai_glow"], 96, 6)]
    for i, az in enumerate((30, 150, 270)):
        parts += dome(f"huette{i}", polar(14, az), 6.0, az + 180, M)
    # walkway from the platform to the core cave, and the cave dome half sunk into the ice
    parts.append(box("steg", (3.2, 10, 0.4), polar(29, 345, -0.2), M["hull"], rot=(0, 0, math.radians(345 - 90))))
    cave = sphere("kernhoehle", 7.5, polar(37, 345, -1.5), M["hull"], scale=(1, 1, 0.7), keep=lambda c: c.z > 1.5)
    m = cave.modifiers.new("dicke", "SOLIDIFY")
    m.thickness = 0.5
    select(cave)
    bpy.ops.object.modifier_apply(modifier="dicke")
    cut(cave, [box("hoehlentuer", (4.0, 6, 5.0), polar(31, 345, 1.5), M["hull"], rot=(0, 0, math.radians(345 - 90)))])
    parts.append(cave)
    parts.append(cylinder("kernsockel", 0.7, 0.9, -1.4, 0.9, M["copper"], 24, at=tuple(polar(39, 345))))
    # the marble tube that opens the gate
    tor_pfad = [polar(21, a, 1.1) for a in range(318, 362, 4)]
    parts += marble_tube("tor", tor_pfad, {"ruhe": 0, "offen": len(tor_pfad) - 1}, M, record_matrix=F)
    for i, p in enumerate(tor_pfad[::3]):
        parts.append(cylinder(f"tor_stuetze{i}", 0.12, 0.12, 0.0, 1.0, M["copper"], 8, at=(p.x, p.y, 0)))
    # the return seed lies in a copper cradle
    parts.append(torus("ruecksamen_wiege", 1.6, 0.2, 0.4, M["copper"], 48, 6, matrix=Matrix.Translation(polar(19, 90))))
    to_planet(parts, F)
    ob = join("Lager", parts, uv_size=4.0)

    G = "lager"
    def a(name, p, face=None):
        world = F @ Vector(p)
        anchor(G, name, world, face=(F @ Vector(face)) if face is not None else None, normal=ERSTLING_LAGER)
    a("mitte", (0, 0, 0))
    a("computer", polar(2.5, 90), face=(0, 0, 0))
    for i, az in enumerate((30, 150, 270)):
        a(f"recorder{i + 1}", polar(9, az), face=(0, 0, 0))
    for i in range(6):
        a(f"lampe{i + 1}", polar(23.5, i * 60 + 15))
    a("becken", polar(11, 210), face=(0, 0, 0))
    a("stein1", polar(12.5, 120), face=(0, 0, 0))
    a("ruecksamen", polar(19, 90, 0.4))
    a("torzu", polar(31, 345))
    a("torauf", polar(31, 345, 6.5))
    a("kern", polar(39, 345, 1.4))
    a("hoehle", polar(37, 345, 0.5))
    a("turm", polar(36, 210))
    ANCHORS[G]["rahmen"] = {"normal": unity_dir(ERSTLING_LAGER)}
    return ob


def lager_tor(M):
    """The gate of the core cave; the DLL lifts it when the marble lies in the slot "offen". Origin = its bottom centre."""
    parts = [box("tor_blatt", (4.4, 0.5, 5.4), (0, 0, 2.7), M["hull"]),
             torus("tor_auge", 1.0, 0.12, 0, M["copper"], 32, 6, matrix=Matrix.Translation((0, -0.3, 3.2)) @ Matrix.Rotation(math.pi / 2, 4, "X")),
             sphere("tor_licht", 0.3, (0, -0.3, 3.2), M["nomai_glow"], seg=12, rings=6)]
    return join("Lager_Tor", parts, uv_size=3.0)


def warpturm(M):
    """A warp tower of the three: a spire with rings on a round base; the warp pad (NH) sits on the base, a marble
    tube winds around the foot. Built upright at the origin; the build script stands it on the surface."""
    parts = [cylinder("sockel", 5.5, 6, -1.0, 0.3, M["hull"], 64), torus("sockel_rand", 5.7, 0.25, 0.2, M["copper"], 64, 6)]
    spire = [Vector((0, 0, 0.3)), Vector((0.6, 0.2, 8)), Vector((-0.5, -0.3, 16)), Vector((0.2, 0.1, 24)), Vector((0, 0, 29))]
    for k in range(3):
        a = k * 120
        parts.append(tube(f"saeule{k}", [polar(4.6, a, 0.3), polar(3.2, a + 20, 9), polar(1.6, a + 40, 19), polar(0.3, a + 60, 28)], 0.35, M["hull"]))
    parts.append(tube("achse", spire, 0.25, M["copper"]))
    for i, z in enumerate((7, 13, 19, 25)):
        parts.append(torus(f"ring{i}", 3.6 - z * 0.11, 0.14, z, M["copper"], 48, 6))
    parts.append(sphere("spitze", 0.9, (0, 0, 29.6), M["nomai_glow"], seg=16, rings=8))
    pfad = [polar(5.1, a, 1.0 + a / 300 * 1.6) for a in range(0, 301, 12)]
    parts += marble_tube("turm", pfad, {"ruhe": 0, "wach": len(pfad) - 1}, M, frame="Turm")
    ob = join("Warpturm", parts, uv_size=3.0)
    G = "turm"
    anchor(G, "warp", (0, 0, 0.35))
    anchor(G, "spitze", (0, 0, 29.6))
    anchor(G, "computer", polar(3.0, 300, 0.3), face=(0, 0, 0))
    return ob


def ausguck_lift(M):
    """The lift platform of the Ausguck with its own marble tube (the DLL moves both). Origin = deck of the lift."""
    parts = [cylinder("liftdeck", 2.4, 2.4, -0.3, 0, M["hull"], 48), torus("liftrand", 2.4, 0.12, 0, M["copper"], 48, 6)]
    pfad = [polar(1.9, a, 1.0) for a in range(60, 121, 10)]
    parts += marble_tube("lift", pfad, {"unten": 0, "oben": len(pfad) - 1}, M, frame="Lift")
    for i, p in enumerate((pfad[0], pfad[-1])):
        parts.append(cylinder(f"lift_stuetze{i}", 0.1, 0.1, 0.0, 1.0, M["copper"], 8, at=(p.x, p.y, 0)))
    return join("Ausguck_Lift", parts, uv_size=2.0)


def strudel(M):
    """The thorn vortex in the middle of the Samenschlund: spiralling vines around a glowing eye."""
    rnd = random.Random(61)
    parts = [sphere("auge", 2.2, (0, 0, 0), M["seed"], seg=24, rings=12)]
    for k in range(7):
        phase = k * TAU / 7
        pts = []
        for i in range(40):
            t = i / 39
            r = 2.8 + 13 * t
            a = phase + t * 4.5
            pts.append(Vector((r * math.cos(a), r * math.sin(a), (t - 0.5) * 6 * math.sin(phase * 2))))
        parts += thorned_tube(f"spirale{k}", pts, 0.9 - 0.4 * (k % 2), M["bark"], 3, rnd=rnd)
    return join("Strudel", parts, uv_size=4.0)


def planetenkern(M, name, mat):
    """A planet core: the heart of a planet's seed (the item the player carries, about 0.8 m)."""
    parts = [sphere("kern", 0.24, (0, 0, 0), mat, seg=24, rings=12)]
    for k in range(8):
        d = direction((k % 2) * 50 - 25, k * 45)
        parts.append(cone_along(f"schuppe{k}", d * 0.2, d, 0.3, 0.1, 0.01, M["bark"], 8))
    parts.append(torus("ring", 0.3, 0.02, 0, mat, 32, 4, matrix=Matrix.Rotation(0.5, 4, "X")))
    return join(name, parts, uv_size=0.5)


def ground_disc(name, r_in, r_out, z, mat, rings, seg):
    """A flat ring on the ground, finely divided so the DLL can bend it onto the terrain. Normals point up."""
    bm = bmesh.new()
    grid = [[bm.verts.new(((r_in + (r_out - r_in) * i / rings) * math.cos(TAU * j / seg),
                           (r_in + (r_out - r_in) * i / rings) * math.sin(TAU * j / seg), z)) for j in range(seg)]
            for i in range(rings + 1)]
    for i in range(rings):
        for j in range(seg):
            bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][(j + 1) % seg], grid[i][(j + 1) % seg]))
    return link(name, bm, mat)


def ground_strip(name, a_deg, r0, r1, w0, w1, z, mat, steps=16):
    """A tapering streak on the ground from radius r0 to r1 in direction a_deg, divided along its length."""
    bm = bmesh.new()
    d = polar(1, a_deg)
    side = Vector((-d.y, d.x, 0))
    rows = []
    for k in range(steps + 1):
        t = k / steps
        c = d * (r0 + (r1 - r0) * t) + Vector((0, 0, z))
        w = w0 + (w1 - w0) * t
        rows.append((bm.verts.new(c + side * w), bm.verts.new(c - side * w)))
    for k in range(steps):
        (l0, r_0), (l1, r_1) = rows[k], rows[k + 1]
        bm.faces.new((l0, r_0, r_1, l1))
    return link(name, bm, mat, smooth=False)


def krater(M):
    """
    The crater the seed tore into Timber Hearth (origin = crater floor centre, about 75 m across with its ejecta):
    a torn rim of earth about 6 m high, a scorched floor with glowing cracks, peeled-up slabs, rubble, splinters and
    dark streaks of thrown earth. The ground parts are finely divided: in game the DLL bends the whole crater onto
    the terrain it measured (CrashSite.cs), so it lies on slopes instead of floating or vanishing in them.
    """
    rnd = random.Random(71)
    earth = material("Erdreich", (0.25, 0.18, 0.11), 0.0, 0.95)
    burnt = material("Brandspur", (0.06, 0.05, 0.045), 0.0, 1.0)
    parts = []
    # the rim: a real crater profile (steep inside, a long slope outside) swept around, its crest radius and height
    # wobbling so it looks torn, not turned. Profile order like torus(): outward, over the crest, inward, under.
    profile = [(17, -2.5), (17, -0.2), (13, 0.8), (9, 2.2), (5, 4.2), (2, 6.2), (0, 6.8), (-2, 6.0), (-5, 3.5),
               (-8, 0.5), (-10, -1.5), (-10, -2.5)]
    bm = bmesh.new()
    seg = 144
    ph = [rnd.uniform(0, TAU) for _ in range(4)]
    rows = []
    for i in range(seg):
        a = TAU * i / seg
        R = 30 + 1.8 * math.sin(3 * a + ph[0]) + 0.9 * math.sin(7 * a + ph[1])
        tall = 1 + 0.22 * math.sin(4 * a + ph[2]) + 0.12 * math.sin(13 * a + ph[3])
        row = []
        for dr, z in profile:
            z = z * tall + (rnd.uniform(-0.35, 0.35) if z > 0 else 0)
            rr = R + dr + (rnd.uniform(-0.4, 0.4) if -10 < dr < 17 else 0)
            row.append(bm.verts.new((rr * math.cos(a), rr * math.sin(a), z)))
        rows.append(row)
    ring = len(profile)
    for i in range(seg):
        A, B = rows[i], rows[(i + 1) % seg]
        for j in range(ring):
            bm.faces.new((A[j], B[j], B[(j + 1) % ring], A[(j + 1) % ring]))
    parts.append(link("rand", bm, earth))
    # the scorched floor and the glowing cracks running out from the seed
    parts.append(ground_disc("boden", 0.5, 27, 0.15, burnt, 26, 96))
    for k in range(9):
        a = k * 40 + rnd.uniform(-12, 12)
        parts.append(ground_strip(f"riss{k}", a, 15, rnd.uniform(22, 26), 0.45, 0.08, 0.3, M["seed"], 10))
    # thrown earth outside the rim
    for k in range(18):
        a = k * 20 + rnd.uniform(-8, 8)
        parts.append(ground_strip(f"streifen{k}", a, 34, rnd.uniform(52, 68), rnd.uniform(3, 5), 0.4, 0.12, burnt, 20))
    # slabs of ground, peeled up and leaning outwards
    for k in range(12):
        a = k * 30 + rnd.uniform(-10, 10)
        p = polar(rnd.uniform(33, 38), a, 1.5)
        parts.append(box(f"scholle{k}", (rnd.uniform(5, 9), rnd.uniform(3, 5), 1.2), p, earth,
                         rot=(0, math.radians(rnd.uniform(25, 50)), math.radians(a))))
    for k in range(110):
        a = rnd.uniform(0, 360)
        size = rnd.uniform(1.0, 5.0)
        parts.append(box(f"brocken{k}", (size, size * rnd.uniform(0.5, 1), size * rnd.uniform(0.4, 0.9)),
                         polar(rnd.uniform(26, 52), a, rnd.uniform(0, 1.5)), earth if k % 3 else M["bark"],
                         rot=(rnd.uniform(0, 1), rnd.uniform(0, 1), rnd.uniform(0, 6))))
    for k in range(20):
        a = rnd.uniform(0, 360)
        d = (polar(1, a, 0) + Vector((0, 0, rnd.uniform(0.4, 1.4)))).normalized()
        parts.append(cone_along(f"splitter{k}", polar(rnd.uniform(18, 34), a, 0), d, rnd.uniform(5, 12), 0.8, 0.05, M["bark"], 6))
    return join("Krater", parts, uv_size=4.0)


def absperrung(M):
    """A Hearthian barrier with a sign: wooden posts, a rope, a board. Origin = ground centre."""
    wood = material("HolzHearth", (0.45, 0.3, 0.18), 0.0, 0.8)
    parts = []
    posts = [polar(4.5, a) for a in (-40, -15, 15, 40)]
    for i, p in enumerate(posts):
        parts.append(cylinder(f"pfosten{i}", 0.12, 0.12, 0, 1.3, wood, 12, at=(p.x, p.y, 0)))
    parts.append(tube("seil", [p + Vector((0, 0, 1.1)) for p in posts], 0.03, wood))
    parts.append(box("schild", (1.6, 0.08, 0.9), polar(4.6, 0, 1.6), wood, rot=(0, 0, math.radians(90))))
    parts.append(cylinder("schildpfahl", 0.07, 0.07, 0, 1.2, wood, 8, at=tuple(polar(4.6, 0))))
    ob = join("Absperrung", parts, uv_size=1.0)
    anchor("absperrung", "schild", polar(4.6, 0, 1.6), face=(0, 0, 1.6))
    return ob


def eiszapfen(M):
    """A cluster of ice thorns for the Splittergang dimension (about 30 m). Origin = root."""
    rnd = random.Random(83)
    parts = [sphere("wurzel", 3.5, (0, 0, 0), M["bark"], scale=(1, 1, 0.7), seg=16, rings=8)]
    for k in range(16):
        d = random_axis(rnd)
        L = rnd.uniform(8, 26)
        parts.append(cone_along(f"zapfen{k}", d * 2.5, d, L, L * 0.14, 0.05, M["ice"], 6))
    return join("Eiszapfen", parts, uv_size=4.0)


def buildings(M):
    return {
        "lager": lager(M),
        "lager_tor": lager_tor(M),
        "warpturm": warpturm(M),
        "ausguck_lift": ausguck_lift(M),
        "strudel": strudel(M),
        "planetenkern_erstling": planetenkern(M, "Planetenkern_Erstling", M["ice"]),
        "krater": krater(M),
        "absperrung": absperrung(M),
        "eiszapfen": eiszapfen(M),
    }


def preview_buildings(cam, models):
    F = lager_frame()
    centre = F @ Vector((0, 0, 0))
    up = ERSTLING_LAGER
    side = up.cross(Vector((0, 0, 1))).normalized()
    render(cam, os.path.join(PREVIEWS, "lager.png"), centre + up * 28 + side * 42, centre + up * 2, (1200, 800), lens=30,
           show=[models["lager"].name, models["erstling"].name, models["lager_tor"].name])
    for key, loc, dist in (("warpturm", (40000, 0, 0), 30), ("strudel", (41000, 0, 0), 32), ("krater", (42000, 0, 0), 70),
                           ("absperrung", (43000, 0, 0), 9), ("eiszapfen", (44000, 0, 0), 55), ("ausguck_lift", (45000, 0, 0), 7),
                           ("planetenkern_erstling", (46000, 0, 0), 1.6)):
        models[key].location = loc
        target = Vector(loc) + Vector((0, 0, 12 if key == "warpturm" else 0))
        render(cam, os.path.join(PREVIEWS, key + ".png"), target + Vector((dist * 0.8, -dist * 0.9, dist * 0.45)), target, (900, 600),
               lens=35, show=[models[key].name])
        models[key].location = (0, 0, 0)




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
    scn.collection.objects.link(sun)
    fill = bpy.data.objects.new("Fuelllicht", bpy.data.lights.new("Fuelllicht", "SUN"))
    fill.data.energy = 1.0
    fill.data.color = (0.6, 0.72, 1.0)
    fill.rotation_euler = (math.radians(-60), math.radians(-20), math.radians(150))
    scn.collection.objects.link(fill)
    world = bpy.data.worlds.new("All")
    world.use_nodes = True
    nodes, links = world.node_tree.nodes, world.node_tree.links
    bg = nodes["Background"]
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


def render(cam, path, cam_loc, target, size=(512, 512), lens=35, show=None, key_light=True):
    sun = bpy.data.objects["Sonne"]
    if key_light:  # light from over the camera's shoulder
        d = Vector(target) - (Vector(cam_loc) + Vector((0, 0, 0.3)) * (Vector(cam_loc) - Vector(target)).length
                              + (Vector(cam_loc) - Vector(target)).cross(Vector((0, 0, 1))).normalized() * 0.3 * (Vector(cam_loc) - Vector(target)).length)
        sun.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    for o in bpy.context.scene.objects:
        if o.type == "MESH":
            o.hide_render = show is not None and o.name not in show
    cam.data.lens = lens
    cam.data.clip_start = 0.5
    cam.data.clip_end = 20000
    cam.location = cam_loc
    cam.rotation_euler = (Vector(target) - Vector(cam_loc)).to_track_quat("-Z", "Y").to_euler()
    scn = bpy.context.scene
    scn.render.resolution_x, scn.render.resolution_y = size
    scn.render.filepath = path
    bpy.ops.render.render(write_still=True)



def main():
    reset()
    os.makedirs(OUT, exist_ok=True)
    for f in os.listdir(OUT):
        if f.endswith((".obj", ".mtl")):
            os.remove(os.path.join(OUT, f))
    M = materials()
    models = {
        "erstling": erstling(M),
        "glutdorn": glutdorn(M),
        "nebelranke_ranken": nebelranke_ranken(M),
        "hohlsamen": hohlsamen(M),
        "herzdorn_kaefig": herzdorn_kaefig(M),
        "ausguck": ausguck(M),
    }
    models.update(buildings(M))
    print("OBJ export:")
    for key, obj in models.items():
        export(obj, key + ".obj")
    with open(os.path.join(OUT, "anchors.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(ANCHORS, f, ensure_ascii=False, indent=2)
        f.write("\n")
    # spread the bodies out for the pictures
    layout = {"erstling": (0, 0, 0), "glutdorn": (5000, 0, 0), "nebelranke_ranken": (10000, 0, 0), "hohlsamen": (15000, 0, 0),
              "herzdorn_kaefig": (25000, 0, 0), "ausguck": (32000, 0, 0)}
    for key, at in layout.items():
        models[key].location = at
    cam = scene_setup()
    if PREVIEWS:
        os.makedirs(PREVIEWS, exist_ok=True)
        for key, (dist, size) in {"erstling": (900, 260), "glutdorn": (780, 220), "nebelranke_ranken": (2200, 640), "hohlsamen": (1000, 300),
                                  "herzdorn_kaefig": (3600, 1100), "ausguck": (45, 18)}.items():
            at = Vector(layout[key])
            view = Vector((dist * 0.7, -dist * 0.75, dist * 0.35))
            if key == "hohlsamen":  # look into the opening
                view = direction(10, 200) * dist + Vector((0, 0, dist * 0.15))
            render(cam, os.path.join(PREVIEWS, key + ".png"), at + view, at, (1200, 800), lens=35, show=[models[key].name])
        preview_buildings(cam, models)
    for key in layout:
        models[key].location = (0, 0, 0)
    os.makedirs(os.path.dirname(BLEND), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND, compress=True)
    print("saved", BLEND)


main()
