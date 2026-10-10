# -*- coding: utf-8 -*-
"""
Blender models of "Die Aussendungseinheit" (Zeki.ISAE). Run with Blender 4.2 LTS:

    blender -b -P tools/isae_models.py -- path/to/Zeki.ISAE [path/to/previews]

The centrepiece is built here: a huge, menacing descendant of the Orbital Probe Cannon in the style of the
Nomai Vessel - an armoured core whose plates glow at the seams, a 1.2 km railgun of three serrated rails
around a glowing core beam, spiked accelerator rings, pincer claws at the muzzle and swept tail blades.
Inside the core sits a walkable chamber. The three side modules are NOT modelled: New Horizons copies the
real modules of the Orbital Probe Cannon onto the ends of the arms. The emitter frame of the focus cannons
is modelled; the gravity cannon inside it is the game's own.

Everything that exists in the game (modules, computers, recorders, crystals, the Vessel interface, the Nomai
probe, lamps, archways) is NOT modelled; New Horizons copies those into the spots this script exports.

Outputs
  * <mod>/assets/models/*.obj (+.mtl)     - the DLL loads them at runtime (Models.cs), also on the title screen
  * <mod>/assets/models/anchors.json      - spots on the models (Unity coordinates) for isae_build.py
  * <mod>/planets/assets/shiplog/...       - ship log photos and the map sprite, rendered with Cycles
  * Zeki.ISAE.Source/blender/ISAE.blend   - the editable scene
  * previews (optional second argument)

Coordinates: Blender is Z-up and right-handed, Unity is Y-up and left-handed. A Blender point (x, y, z)
ends up at Unity (-x, z, -y): the OBJ export (forward -Z, up Y) plus the x-mirror in the DLL's loader.
The cannon fires along Blender +Z = Unity +y; the DLL turns that axis towards the sun. 1 unit = 1 metre.

Material names are the contract with the DLL: VesselHuelle, VesselKupfer, VesselDunkel (opaque, taken from
the Vessel in game), VesselGlut (red-orange glow) and VesselLeuchten (blue glow).
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
HUB_R = 70.0                       # armoured core
RAIL_AZ = (90.0, 210.0, 330.0)     # the three rails
ARM_AZ = (30.0, 150.0, 270.0)      # arms to the three modules (between the rails)
RAIL_START, RAIL_END = 40.0, 700.0
LENS_Z = 770.0                     # the focus lens between the claws
MUZZLE_Z = 960.0
TAIL_Z = -300.0
ARM_END = 150.0                    # radius where a module is mounted
RINGS_Z = (140, 230, 320, 410, 500, 590)
CHAMBER_R, CHAMBER_FLOOR = 34.0, -14.0
TUNNEL_AZ, TUNNEL_Z = 90.0, -10.0
FOCUS_RADIUS, FOCUS_Z = 420.0, 300.0
MODULES = (("kontrolle", "Kontrollmodul", 30.0), ("start", "Startmodul", 150.0), ("navigation", "Navigationsmodul", 270.0))
FOCUS = (("A", "Alpha", 0.0), ("B", "Beta", 120.0), ("C", "Gamma", 240.0))

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
    # preview colours close to the Vessel; in game the DLL uses the Vessel's own materials for the opaque ones
    return {
        "hull": material("VesselHuelle", (0.46, 0.36, 0.28), 0.5, 0.45),
        "copper": material("VesselKupfer", (0.72, 0.43, 0.22), 0.8, 0.35),
        "dark": material("VesselDunkel", (0.10, 0.09, 0.10), 0.4, 0.6),
        "glow": material("VesselLeuchten", (0.5, 0.82, 1.0), 0.0, 0.3, (0.4, 0.78, 1.0), 7.0),
        "ember": material("VesselGlut", (1.0, 0.35, 0.12), 0.0, 0.3, (1.0, 0.28, 0.06), 9.0),
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


# ------------------------------------------------------------------------------------------ the cannon
def armoured_core(M):
    """Faceted armour plates around the core; the seams between the plates glow red."""
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=3, radius=HUB_R)
    hole = (polar(1, TUNNEL_AZ, 0) + Vector((0, 0, TUNNEL_Z / HUB_R))).normalized()
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.calc_center_median().normalized().dot(hole) > math.cos(math.radians(7.5))], context="FACES")
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    rim = set(bmesh.ops.inset_individual(bm, faces=list(bm.faces), thickness=1.2, depth=0.0, use_even_offset=True)["faces"])
    plates = [f for f in bm.faces if f not in rim]
    tops = bmesh.ops.extrude_discrete_faces(bm, faces=plates)["faces"]
    for f in tops:
        n = f.calc_center_median().normalized()
        for v in f.verts:
            v.co += n * 2.8
    tops = set(tops)
    for f in bm.faces:
        f.material_index = 0 if f in tops else (3 if f in rim else 2)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return link_multi("core_armour", bm, [M["hull"], M["copper"], M["dark"], M["ember"]])


def hauptkanone(M):
    parts = [armoured_core(M)]
    # spikes around the core: six backwards along the equator, three forwards over the arms
    for k in range(6):
        a = k * 60.0
        base = polar(HUB_R - 3, a, 0)
        parts.append(cone_along(f"spike{k}", base, polar(1, a, 0) + Vector((0, 0, -0.45)), 75, 9, 0.4, M["dark"]))
    for k, a in enumerate(ARM_AZ):
        base = polar(HUB_R * 0.8, a, 40)
        parts.append(cone_along(f"spike_front{k}", base, polar(1, a, 0) + Vector((0, 0, 1.1)), 60, 7, 0.3, M["dark"]))
    # hatch of the tunnel into the core chamber
    hatch = polar(HUB_R + 2.0, TUNNEL_AZ, TUNNEL_Z)
    parts.append(torus("hatch", 9.5, 1.6, 0, M["copper"], 48, 10,
                       matrix=Matrix.Translation(hatch) @ Matrix.Rotation(math.radians(TUNNEL_AZ), 4, "Z") @ Matrix.Rotation(math.pi / 2, 4, "Y")))
    # the railgun: core beam and three serrated rails
    parts.append(cylinder("beam", 7.0, 6.0, 20, LENS_Z - 10, M["ember"], 32))
    for z in range(90, int(RAIL_END), 70):
        parts.append(torus(f"beam_band{z}", 8.2, 0.9, z, M["dark"], 32, 8))
    profile = [(13, -3.5), (13, 3.5), (24, 6.5), (36, 2.8), (36, -2.8), (24, -6.5)]
    for k, az in enumerate(RAIL_AZ):
        parts.append(prism(f"rail{k}", profile, [RAIL_START, 200, 400, 600, RAIL_END], az, [M["hull"], M["ember"], M["copper"]], inner_mat=1, outer_mat=2))
        for i, z in enumerate(range(80, int(RAIL_END) - 20, 40)):
            parts.append(box(f"tooth{k}_{i}", (8.0, 2.4, 11.0), polar(39.5, az, z), M["dark"], (0, math.radians(-25), math.radians(az))))
        # pincer claws at the muzzle
        parts.append(fin(f"claw{k}", [(14, 660), (36, 660), (54, 760), (46, 870), (12, 958), (5, 944), (28, 862), (24, 760)], 10, az, M["hull"]))
        parts.append(fin(f"claw_edge{k}", [(36, 662), (54, 760), (46, 870), (12, 958), (10.6, 954), (44.2, 867), (52.4, 761), (34.8, 664)], 11, az, M["copper"]))
        # tail blades
        parts.append(fin(f"blade{k}", [(28, -55), (95, -170), (120, -290), (96, -322), (56, -250), (30, -180)], 7, az, M["hull"]))
        parts.append(fin(f"blade_edge{k}", [(95, -170), (120, -290), (118, -294), (93, -174)], 8, az, M["copper"]))
    parts.append(torus("claw_ring", 30, 3, 700, M["hull"], 72, 10))
    parts.append(sphere("lens", 12, (0, 0, LENS_Z), M["ember"], seg=40, rings=20))
    parts.append(torus("lens_halo", 20, 1.4, LENS_Z, M["ember"], 72, 8))
    # tail spine and exhaust
    parts.append(cylinder("spine", 34, 7, -60, TAIL_Z + 20, M["hull"], 48))
    for z in (-110, -170, -230):
        r = 34 + (7 - 34) * (z + 60) / (TAIL_Z + 80)
        parts.append(torus(f"spine_band{z}", r + 0.6, 1.2, z, M["ember"], 64, 8))
    parts.append(torus("exhaust", 9, 1.6, TAIL_Z + 20, M["ember"], 48, 8))
    # arms to the three modules: two beams with zigzag braces and a mounting collar
    for key, _, az in MODULES:
        for dz in (-7, 7):
            parts.append(tube(f"arm_{key}{dz}", [polar(HUB_R - 8, az, dz), polar(ARM_END - 3, az, dz)], 3.2, M["hull"]))
        for i in range(int((ARM_END - HUB_R) / 14)):
            r0 = HUB_R + i * 14
            parts.append(tube(f"brace_{key}{i}", [polar(r0, az, -7), polar(r0 + 14, az, 7)], 1.1, M["dark"]))
        parts.append(torus(f"collar_{key}", 13, 2.6, 0, M["copper"], 48, 10,
                           matrix=Matrix.Translation(polar(ARM_END - 3, az)) @ Matrix.Rotation(math.radians(az), 4, "Z") @ Matrix.Rotation(math.pi / 2, 4, "Y")))
        anchor("isae", f"modul_{key}", polar(ARM_END, az), normal=polar(1, az))
    obj = join("Hauptkanone", parts, uv_size=12.0)

    anchor("isae", "kern", (0, 0, 0))
    anchor("isae", "linse", (0, 0, LENS_Z))
    anchor("isae", "muendung", (0, 0, LENS_Z + 25))
    anchor("isae", "heck", (0, 0, TAIL_Z + 15))
    anchor("isae", "luke", polar(HUB_R + 14, TUNNEL_AZ, TUNNEL_Z))
    for letter, _, az in FOCUS:
        anchor("isae", f"fokus_{letter}", polar(FOCUS_RADIUS, az, FOCUS_Z))
    ANCHORS["isae"]["laenge"] = MUZZLE_Z - TAIL_Z
    return obj


def laufringe(M):
    """Spiked accelerator rings around the rails - spun by the DLL around the firing axis."""
    parts = []
    for i, z in enumerate(RINGS_Z):
        parts.append(torus(f"ring{i}", 52, 4.5, z, M["hull"], 96, 12))
        parts.append(torus(f"ring_glow{i}", 46.6, 1.3, z, M["ember"], 96, 8))
        for k in range(6):
            a = k * 60 + 15 + i * 10
            parts.append(cone_along(f"ring_spike{i}_{k}", polar(55, a, z), polar(1, a, 0) + Vector((0, 0, 0.25)), 26, 3.4, 0.2, M["dark"], 12))
    return join("Laufringe", parts, uv_size=12.0)


def kernkammer(M):
    """The walkable chamber inside the core: the burning heart of the unit and Sedum's last place."""
    door_dir = polar(1, TUNNEL_AZ)
    shell = sphere("chamber", CHAMBER_R, (0, 0, 0), M["hull"], seg=64, rings=32)
    modifier(shell, "SOLIDIFY", thickness=2.0, offset=-1.0)
    cut(shell, [box("door", (10, 13, 13), door_dir * (CHAMBER_R - 1) + Vector((0, 0, TUNNEL_Z)), M["dark"], (0, 0, math.radians(TUNNEL_AZ)))])
    parts = [shell]
    floor_r = math.sqrt((CHAMBER_R - 2) ** 2 - CHAMBER_FLOOR ** 2) + 0.3
    parts.append(cylinder("floor", floor_r, floor_r, CHAMBER_FLOOR - 1.2, CHAMBER_FLOOR, M["dark"], 64))
    parts.append(torus("floor_glow", floor_r - 2, 0.15, CHAMBER_FLOOR + 0.02, M["ember"], 96, 6))
    parts.append(cylinder("pillar", 4.0, 2.2, CHAMBER_FLOOR, -6.5, M["copper"], 32))
    parts.append(sphere("heart", 7, (0, 0, 0), M["ember"], seg=40, rings=20))
    # tunnel from the chamber to the hatch in the armour
    tunnel = cylinder("tunnel", 6.5, 6.5, 0, HUB_R + 3 - (CHAMBER_R - 1.5), M["hull"], 32, cap=False,
                      matrix=Matrix.Translation(door_dir * (CHAMBER_R - 1.5) + Vector((0, 0, TUNNEL_Z))) @ Matrix.Rotation(math.radians(TUNNEL_AZ), 4, "Z") @ Matrix.Rotation(math.pi / 2, 4, "Y"))
    modifier(tunnel, "SOLIDIFY", thickness=0.8, offset=1.0)
    parts.append(tunnel)
    obj = join("Kernkammer", parts, uv_size=6.0)

    floor = lambda r, a: polar(r, a, CHAMBER_FLOOR)  # noqa: E731
    centre = Vector((0, 0, CHAMBER_FLOOR))
    anchor("kammer", "boden", centre)
    anchor("kammer", "sedum", floor(19, 205), face=centre)
    anchor("kammer", "computer", floor(19, 160), face=centre)
    anchor("kammer", "recorder", floor(19, 250), face=centre)
    for i, a in enumerate((300, 20, 130)):
        anchor("kammer", f"lampe{i + 1}", floor(26, a))
    anchor("kammer", "licht", (0, 0, -5))
    ANCHORS["kammer"]["bodenRadius"] = round(floor_r, 2)
    ANCHORS["kammer"]["hoehe"] = round(CHAMBER_R - 2 - CHAMBER_FLOOR, 2)
    return obj


def kernringe(M):
    parts = []
    for k, (R, tilt) in enumerate(((10.5, 0.45), (13.0, -0.6), (15.5, 1.1))):
        parts.append(torus(f"gyro{k}", R, 0.6, 0, M["copper"], 72, 8, matrix=Matrix.Rotation(tilt, 4, "X") @ Matrix.Rotation(k * 1.3, 4, "Y")))
    return join("Kernringe", parts, uv_size=3.0)


def fokusgeruest(M):
    """The emitter frame of a focus cannon. Origin = top of the gravity cannon's launch platform (the DLL
    shifts the game's gravity cannon there). Three spiked prongs carry the emitter that aims at the sun."""
    parts = [
        cylinder("disk", 40, 40, -1.4, -0.2, M["hull"], 72),
        torus("disk_rim", 40, 1.6, -0.8, M["copper"], 96, 10),
        torus("disk_glow", 37, 0.25, -0.18, M["ember"], 96, 6),
        # keel underneath: an inverted spire, so the floating cannon is not bare from below
        cylinder("keel", 0.8, 24, -66, -1.4, M["hull"], 48),
        torus("keel_glow", 16.5, 1.0, -22, M["ember"], 64, 8),
        cylinder("keel_platform", 6, 6, -67.4, -66.2, M["hull"], 32),
        torus("keel_platform_glow", 6, 0.2, -67.4, M["ember"], 48, 6),
        # emitter at the top, with a small platform below it
        sphere("emitter", 5, (0, 0, 113), M["ember"], seg=32, rings=16),
        torus("emitter_crown", 9, 1.1, 112, M["copper"], 48, 8),
        torus("emitter_halo", 12, 0.4, 112, M["ember"], 64, 6),
        cylinder("top_platform", 7, 7, 99.2, 100.0, M["hull"], 32),
        torus("top_platform_glow", 7, 0.2, 100.0, M["ember"], 48, 6),
    ]
    for k in range(3):
        a = k * 120.0
        parts.append(tube(f"prong{k}", [polar(40, a, -0.5), polar(48, a, 40), polar(30, a, 85), polar(8, a, 108)], 2.6, M["dark"]))
        parts.append(cone_along(f"prong_spike{k}", polar(49, a, 40), polar(1, a, 0) + Vector((0, 0, 0.3)), 22, 2.6, 0.2, M["dark"], 12))
        parts.append(tube(f"top_strut{k}", [polar(6.5, a, 99.6), polar(16, a, 100.4)], 0.6, M["copper"]))
        parts.append(fin(f"keel_fin{k}", [(10, -8), (30, -20), (26, -45), (6, -56)], 2.0, a + 60, M["dark"]))
    obj = join("Fokusgeruest", parts, uv_size=8.0)

    centre = Vector((0, 0, 0))
    A = "fokus"
    anchor(A, "deck", centre)
    anchor(A, "koppler_deck", polar(26, 300), face=centre)
    anchor(A, "computer", polar(29, 60), face=centre)
    anchor(A, "recorder", polar(29, 180), face=centre)
    for i, a in enumerate((90, 210, 330)):
        anchor(A, f"tor{i + 1}", polar(36, a), face=centre)
    for i, a in enumerate((30, 150, 270)):
        anchor(A, f"lampe{i + 1}", polar(33, a))
    anchor(A, "emitter", (0, 0, 113))
    anchor(A, "oben", (0, 0, 100.0))
    anchor(A, "koppler_oben", polar(3.0, 0, 100.0), face=(0, 0, 100.0))
    anchor(A, "unten", (0, 0, -67.4))
    ANCHORS[A]["deckRadius"] = 40.0
    return obj


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
        "hauptkanone": hauptkanone(M),
        "laufringe": laufringe(M),
        "kernkammer": kernkammer(M),
        "kernringe": kernringe(M),
        "fokusgeruest": fokusgeruest(M),
        "sternkarte": sternkarte(M),
    }
    print("OBJ export:")
    for key, obj in models.items():
        export(obj, key + ".obj")
    with open(os.path.join(OUT, "anchors.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(ANCHORS, f, ensure_ascii=False, indent=2)
        f.write("\n")

    # pictures: the whole ensemble with the three focus cannons at their places
    focus = models["fokusgeruest"]
    copies = []
    for letter, _, az in FOCUS:
        c = focus.copy()
        c.location = polar(FOCUS_RADIUS, az, FOCUS_Z)
        bpy.context.collection.objects.link(c)
        copies.append(c)
    models["sternkarte"].location = (5000, 5000, 5000)
    ensemble = [models["hauptkanone"].name, models["laufringe"].name] + [c.name for c in copies]
    cam = scene_setup()
    E = os.path.join(SHIPLOG, "entries")
    os.makedirs(E, exist_ok=True)
    render(cam, os.path.join(E, "ZEKISAE_ISAE.png"), (1500, -1300, 900), (0, 0, 280), lens=38, show=ensemble)
    render(cam, os.path.join(E, "ZEKISAE_FOKUS.png"), (120, -150, 70), (0, 0, 30), lens=35, show=[focus.name])
    render(cam, os.path.join(E, "ZEKISAE_KERN.png"), polar(25, TUNNEL_AZ - 25, CHAMBER_FLOOR + 6), (0, 0, -2), lens=20,
           show=[models["kernkammer"].name, models["kernringe"].name], key_light=False)
    # the modules are copies of the real OPC module (not modelled here); their ship log pictures are drawn by isae_build.py
    scn = bpy.context.scene
    scn.render.film_transparent = True
    os.makedirs(os.path.join(SHIPLOG, "map"), exist_ok=True)
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = 1300
    cam.location, cam.rotation_euler = (0, -3000, 330), (math.radians(90), 0, 0)
    for o in scn.objects:
        if o.type == "MESH":
            o.hide_render = o.name not in ensemble[:2]
    scn.render.resolution_x = scn.render.resolution_y = 256
    scn.render.filepath = os.path.join(SHIPLOG, "map", "isae.png")
    bpy.ops.render.render(write_still=True)
    cam.data.type = "PERSP"
    scn.render.film_transparent = False
    if PREVIEWS:
        os.makedirs(PREVIEWS, exist_ok=True)
        render(cam, os.path.join(PREVIEWS, "isae_gesamt.png"), (1700, -1500, 1000), (0, 0, 300), (1600, 1000), lens=36, show=ensemble)
        render(cam, os.path.join(PREVIEWS, "isae_kern_aussen.png"), (260, -230, 120), (0, 0, 20), (1600, 1000), lens=32, show=ensemble[:2])
        render(cam, os.path.join(PREVIEWS, "isae_muendung.png"), (200, -260, 1000), (0, 0, 780), (1600, 1000), lens=32, show=ensemble[:2])
        render(cam, os.path.join(PREVIEWS, "fokuskanone.png"), (130, -160, 80), (0, 0, 30), (1600, 1000), lens=32, show=[focus.name])
        render(cam, os.path.join(PREVIEWS, "kernkammer.png"), polar(25, TUNNEL_AZ - 25, CHAMBER_FLOOR + 6), (0, 0, -2), (1600, 1000), lens=20,
               show=[models["kernkammer"].name, models["kernringe"].name], key_light=False)
    for c in copies:
        bpy.data.objects.remove(c, do_unlink=True)
    models["sternkarte"].location = (0, 0, 0)
    os.makedirs(os.path.dirname(BLEND), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND, compress=True)
    print("saved", BLEND)


main()
