# -*- coding: utf-8 -*-
"""
Blender models of "Die Aussendungseinheit" (Zeki.ISAE). Run with Blender 4.2 LTS:

    blender -b -P tools/isae_models.py -- path/to/Zeki.ISAE [path/to/renders]

Builds every prop procedurally, then
  * exports one OBJ (+MTL) per prop to <mod>/assets/models/ - the DLL loads them at runtime,
  * writes <mod>/assets/models/anchors.json: points on the props (Unity coordinates) that the
    New Horizons configs use to place texts, crystals, lamps and volumes,
  * saves the editable scene as Zeki.ISAE.Source/blender/ISAE_Props.blend,
  * renders the ship log photo of the focus cannon, and preview pictures if a render folder is given.

Coordinates: Blender is Z-up and right-handed, Unity is Y-up and left-handed.
A Blender point (x, y, z) ends up at Unity (-x, z, -y); this is exactly what the OBJ export
(forward -Z, up Y) plus the x-mirror in the DLL's OBJ loader do. 1 Blender unit = 1 metre.

Material names are the contract with the DLL: NomaiMetall, NomaiDunkel, NomaiLeuchten.
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
RENDERS = os.path.abspath(ARGS[1]) if len(ARGS) > 1 else None
OUT = os.path.join(MOD, "assets", "models")
BLEND = os.path.join(os.path.dirname(MOD), "Zeki.ISAE.Source", "blender", "ISAE_Props.blend")

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


def materials():
    return {
        "metal": material("NomaiMetall", (0.78, 0.74, 0.66), 0.55, 0.38),
        "dark": material("NomaiDunkel", (0.16, 0.15, 0.18), 0.4, 0.55),
        "glow": material("NomaiLeuchten", (0.55, 0.85, 1.0), 0.0, 0.3, (0.45, 0.8, 1.0), 6.0),
    }


def finish(obj, mat, smooth=True):
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    if smooth:
        for p in obj.data.polygons:
            p.use_smooth = True
    return obj


def mesh_obj(name, bm):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    return ob


def cylinder(name, r1, r2, z0, z1, mat, seg=32, at=(0, 0), cap=True):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=cap, segments=seg, radius1=r1, radius2=r2, depth=z1 - z0,
                          matrix=Matrix.Translation((at[0], at[1], (z0 + z1) / 2)))
    return finish(mesh_obj(name, bm), mat)


def torus(name, R, r, z, mat, seg=64, ring=12, arc=TAU, start=0.0, matrix=None):
    """Torus (or an arc of one) around the Z axis, closed with caps when it is only an arc."""
    bm = bmesh.new()
    full = arc >= TAU - 1e-6
    n = seg if full else max(4, int(seg * arc / TAU))
    rings = []
    for i in range(n if full else n + 1):
        a = start + arc * i / n
        c, s = math.cos(a), math.sin(a)
        rings.append([bm.verts.new(((R + r * math.cos(b)) * c, (R + r * math.cos(b)) * s, z + r * math.sin(b)))
                      for b in (TAU * j / ring for j in range(ring))])
    for i in range(len(rings) - (0 if full else 1)):
        A, B = rings[i], rings[(i + 1) % len(rings)]
        for j in range(ring):
            bm.faces.new((A[j], B[j], B[(j + 1) % ring], A[(j + 1) % ring]))
    if not full:
        bm.faces.new(list(reversed(rings[0])))
        bm.faces.new(rings[-1])
    if matrix is not None:
        bmesh.ops.transform(bm, matrix=matrix, verts=bm.verts)
    return finish(mesh_obj(name, bm), mat)


def sphere(name, r, at, mat, scale=(1, 1, 1), keep_below=None, seg=32, rings=16):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=r)
    bmesh.ops.scale(bm, vec=scale, verts=bm.verts)
    bmesh.ops.translate(bm, vec=at, verts=bm.verts)
    if keep_below is not None:
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z > keep_below + 1e-4], context="VERTS")
    return finish(mesh_obj(name, bm), mat)


def box(name, size, at, mat, rot=(0, 0, 0)):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=size, verts=bm.verts)
    m = Matrix.Translation(at) @ (Matrix.Rotation(rot[2], 4, "Z") @ Matrix.Rotation(rot[1], 4, "Y") @ Matrix.Rotation(rot[0], 4, "X"))
    bmesh.ops.transform(bm, matrix=m, verts=bm.verts)
    return finish(mesh_obj(name, bm), mat, smooth=False)


def tube(name, points, radius, mat):
    """A smooth bent pipe through the given points (Nomai arms and struts)."""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = radius
    cu.bevel_resolution = 4
    cu.resolution_u = 12
    cu.use_fill_caps = True
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(len(points) - 1)
    for bp, p in zip(sp.bezier_points, points):
        bp.co = p
        bp.handle_left_type = bp.handle_right_type = "AUTO"
    ob = bpy.data.objects.new(name, cu)
    bpy.context.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    for o in bpy.context.selected_objects:
        o.select_set(False)
    ob.select_set(True)
    bpy.ops.object.convert(target="MESH")
    ob = bpy.context.view_layer.objects.active
    return finish(ob, mat)


def polar(r, a_deg, z=0.0):
    a = math.radians(a_deg)
    return (r * math.cos(a), r * math.sin(a), z)


def unity(p):
    """Blender point -> Unity/New Horizons coordinates (see module docstring)."""
    return {"x": round(-p[0], 3), "y": round(p[2], 3), "z": round(-p[1], 3)}


def anchor(model, name, p, yaw_towards=None):
    a = {"position": unity(p)}
    if yaw_towards is not None:
        # yaw (Unity, degrees around +y) that turns the prop's +z towards the target point
        d = (-(yaw_towards[0] - p[0]), -(yaw_towards[1] - p[1]))
        a["yaw"] = round(math.degrees(math.atan2(d[0], d[1])) % 360, 1)
    ANCHORS.setdefault(model, {})[name] = a


def join(name, objs):
    for o in bpy.context.selected_objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name = name
    ob.data.name = name
    # world-scaled box mapping so the tiling Nomai textures of the game have a sensible size (1 tile = 4 m)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.cube_project(cube_size=4.0, scale_to_bounds=False)
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    return ob


# ------------------------------------------------------------------------------------------ props
def fokuskanone(M):
    """Free-floating focus cannon: walkable deck, Nomai hull underneath, three arms holding the focus rings.
    The deck top is the origin, the cannon fires along +Z (Unity +y)."""
    parts = []
    # deck with rim and inlaid light ring
    parts.append(cylinder("deck", 10.0, 10.0, -0.8, 0.0, M["metal"], 48))
    parts.append(torus("deck_rim", 10.0, 0.35, -0.15, M["dark"], 64, 10))
    parts.append(torus("deck_light", 7.6, 0.12, 0.0, M["glow"], 64, 8))
    for k in range(6):  # spokes inlaid in the floor
        a = math.radians(30 + k * 60)
        parts.append(box(f"spoke{k}", (4.6, 0.35, 0.06), (5.0 * math.cos(a), 5.0 * math.sin(a), 0.0), M["dark"], (0, 0, a)))
    # hull: a flattened Nomai pod below the deck, with three keel fins and a glowing core
    parts.append(sphere("hull", 9.6, (0, 0, -0.8), M["metal"], (1, 1, 0.62), keep_below=-0.8, seg=48, rings=24))
    parts.append(torus("hull_band", 8.2, 0.3, -3.2, M["dark"], 64, 8))
    for k in range(3):
        a = 90 + k * 120
        x, y, _ = polar(5.4, a)
        parts.append(box(f"fin{k}", (6.0, 0.5, 3.4), (x, y, -5.6), M["dark"], (0, math.radians(-28), math.radians(a))))
    parts.append(sphere("core", 1.3, (0, 0, -6.6), M["glow"]))
    # emitter column in the middle
    parts.append(cylinder("plinth", 2.8, 2.4, 0.0, 1.0, M["dark"], 32))
    parts.append(cylinder("column", 1.6, 0.9, 1.0, 12.0, M["metal"], 32))
    parts.append(torus("column_band1", 1.45, 0.18, 4.0, M["glow"], 32, 8))
    parts.append(torus("column_band2", 1.18, 0.16, 8.0, M["glow"], 32, 8))
    parts.append(sphere("emitter", 1.15, (0, 0, 12.7), M["glow"]))
    # three arms rising from the deck edge, bending inwards to the focus rings
    for k in range(3):
        a = 90 + k * 120
        parts.append(tube(f"arm{k}", [polar(8.6, a, 0.0), polar(9.4, a, 6.0), polar(7.6, a, 13.0), polar(6.0, a, 18.0)], 0.5, M["metal"]))
        parts.append(cylinder(f"arm_foot{k}", 1.0, 0.8, 0.0, 0.6, M["dark"], 16, at=polar(8.6, a)[:2]))
    # focus rings stacked along the firing axis, held by struts
    parts.append(torus("ring1", 6.0, 0.7, 18.0, M["metal"], 72, 12))
    parts.append(torus("ring1_light", 5.15, 0.22, 18.0, M["glow"], 72, 8))
    parts.append(torus("ring2", 4.3, 0.5, 23.5, M["metal"], 64, 12))
    parts.append(torus("ring2_light", 3.65, 0.16, 23.5, M["glow"], 64, 8))
    parts.append(torus("ring3", 2.6, 0.35, 27.5, M["metal"], 48, 10))
    for k in range(3):
        a = 30 + k * 120
        parts.append(tube(f"strut_a{k}", [polar(5.6, a, 18.4), polar(4.0, a, 23.3)], 0.22, M["dark"]))
        parts.append(tube(f"strut_b{k}", [polar(4.0, a + 60, 23.8), polar(2.4, a + 60, 27.3)], 0.16, M["dark"]))
    # pedestal of the phase coupler (the crystal itself is the game's gravity crystal, placed by New Horizons)
    kx, ky = 5.4, -3.6
    parts.append(cylinder("coupler_base", 0.9, 0.7, 0.0, 0.35, M["dark"], 24, at=(kx, ky)))
    parts.append(cylinder("coupler_post", 0.45, 0.4, 0.35, 1.3, M["metal"], 24, at=(kx, ky)))
    for k in range(3):
        a = math.radians(k * 120)
        parts.append(box(f"prong{k}", (0.16, 0.16, 0.8), (kx + 0.42 * math.cos(a), ky + 0.42 * math.sin(a), 1.6), M["metal"],
                         (0.35 * math.sin(a), -0.35 * math.cos(a), 0)))
    obj = join("Fokuskanone", parts)

    anchor("fokuskanone", "koppler", (kx, ky, 1.3), yaw_towards=(0, 0))
    anchor("fokuskanone", "computer", (-5.6, -3.4, 0.0), yaw_towards=(0, 0))
    anchor("fokuskanone", "emitter", (0, 0, 12.7))
    anchor("fokuskanone", "muendung", (0, 0, 28.5))
    for k in range(4):
        anchor("fokuskanone", f"lampe{k + 1}", polar(9.0, 45 + 90 * k, 0.0))
    anchor("fokuskanone", "deck", (0, 0, 0.0))
    ANCHORS["fokuskanone"]["deckRadius"] = 10.0
    return obj


def fokusring(M):
    """A segmented energy ring for the barrel of the main cannon (Vessel-style), spins in game."""
    parts = []
    for k in range(6):
        parts.append(torus(f"seg{k}", 16.0, 1.0, 0.0, M["metal"], 96, 12, arc=math.radians(50), start=math.radians(k * 60 + 5)))
        parts.append(sphere(f"node{k}", 1.35, polar(16.0, k * 60), M["glow"]))
        parts.append(torus(f"collar{k}", 1.6, 0.25, 0.0, M["dark"], 24, 8,
                           matrix=Matrix.Translation(polar(16.0, k * 60)) @ Matrix.Rotation(math.radians(k * 60), 4, "Z") @ Matrix.Rotation(math.pi / 2, 4, "Y")))
    parts.append(torus("inner_light", 14.6, 0.18, 0.0, M["glow"], 96, 8))
    return join("Fokusring", parts)


def sonde(M):
    """The interstellar probe that the finale fires out of the main cannon (nose = +Z)."""
    parts = [
        cylinder("body", 0.55, 0.75, -2.0, 1.4, M["metal"], 32),
        cylinder("nose", 0.75, 0.05, 1.4, 3.6, M["metal"], 32),
        cylinder("tail", 0.4, 0.62, -2.6, -2.0, M["dark"], 32),
        torus("band", 0.74, 0.1, 0.4, M["glow"], 32, 8),
        sphere("engine", 0.5, (0, 0, -2.75), M["glow"]),
    ]
    for k in range(3):
        a = 90 + k * 120
        x, y, _ = polar(0.95, a)
        parts.append(box(f"fin{k}", (1.4, 0.1, 1.8), (x, y, -1.5), M["dark"], (0, 0, math.radians(a))))
    return join("Sonde", parts)


def hauptschalter(M):
    """The main switch console that appears in the control module once all couplers are cut (up = +Z)."""
    parts = [
        cylinder("foot", 0.55, 0.45, 0.0, 0.15, M["dark"], 24),
        cylinder("post", 0.22, 0.18, 0.15, 0.95, M["metal"], 24),
        box("plate", (0.9, 0.6, 0.08), (0, 0.05, 1.02), M["metal"], (math.radians(-25), 0, 0)),
        box("slot", (0.08, 0.42, 0.04), (0, 0.05, 1.07), M["dark"], (math.radians(-25), 0, 0)),
        tube("lever", [(0, 0.0, 1.06), (0, -0.12, 1.32), (0, -0.2, 1.45)], 0.04, M["metal"]),
        sphere("knob", 0.09, (0, -0.2, 1.47), M["glow"]),
        torus("ring", 0.5, 0.04, 0.12, M["glow"], 32, 6),
    ]
    obj = join("Hauptschalter", parts)
    anchor("hauptschalter", "griff", (0, -0.2, 1.47))
    return obj


# ------------------------------------------------------------------------------------------ export / render
def export(obj, filename):
    for o in bpy.context.selected_objects:
        o.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.wm.obj_export(filepath=os.path.join(OUT, filename), export_selected_objects=True, forward_axis="NEGATIVE_Z", up_axis="Y",
                          export_triangulated_mesh=True, export_materials=True, export_uv=True, export_normals=True,
                          apply_modifiers=True, export_colors=False, path_mode="STRIP")
    tris = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    print(f"  {filename:22s} {len(obj.data.vertices):6d} verts {tris:6d} tris")


def render(objs, path, cam_loc, target, size=(1024, 768), lens=50):
    scn = bpy.context.scene
    hidden = [o for o in scn.objects if o.type == "MESH" and o not in objs]
    for o in hidden:
        o.hide_render = True
    for o in objs:
        o.hide_render = False
    cam = bpy.data.objects.get("Kamera")
    if cam is None:
        cam = bpy.data.objects.new("Kamera", bpy.data.cameras.new("Kamera"))
        scn.collection.objects.link(cam)
        sun = bpy.data.objects.new("Sonne", bpy.data.lights.new("Sonne", "SUN"))
        sun.data.energy = 4.0
        sun.data.color = (1.0, 0.86, 0.72)
        sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(40))
        scn.collection.objects.link(sun)
        world = bpy.data.worlds.new("All")
        world.use_nodes = True
        world.node_tree.nodes["Background"].inputs[0].default_value = (0.012, 0.01, 0.02, 1)
        world.node_tree.nodes["Background"].inputs[1].default_value = 1.0
        scn.world = world
        scn.camera = cam
        scn.render.engine = "CYCLES"
        scn.cycles.device = "CPU"
        scn.cycles.samples = 48
        scn.cycles.use_denoising = True
        scn.view_settings.view_transform = "AgX"
        scn.render.film_transparent = False
    cam.data.lens = lens
    cam.location = cam_loc
    direction = Vector(target) - Vector(cam_loc)
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    scn.render.resolution_x, scn.render.resolution_y = size
    scn.render.filepath = path
    bpy.ops.render.render(write_still=True)
    for o in hidden:
        o.hide_render = False


def main():
    reset()
    os.makedirs(OUT, exist_ok=True)
    for f in os.listdir(OUT):
        if f.endswith((".obj", ".mtl")):
            os.remove(os.path.join(OUT, f))
    M = materials()
    models = {
        "fokuskanone": fokuskanone(M),
        "fokusring": fokusring(M),
        "sonde": sonde(M),
        "hauptschalter": hauptschalter(M),
    }
    # lay the props out side by side in the .blend (export happens at the origin first)
    print("OBJ export:")
    for key, obj in models.items():
        export(obj, key + ".obj")
    with open(os.path.join(OUT, "anchors.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(ANCHORS, f, ensure_ascii=False, indent=2)
        f.write("\n")

    offsets = {"fokuskanone": (0, 0, 0), "fokusring": (45, 0, 10), "sonde": (-22, 0, 10), "hauptschalter": (-22, -8, 0)}
    for key, obj in models.items():
        obj.location = offsets[key]
    # ship log photo of the focus cannon
    render([models["fokuskanone"]], os.path.join(MOD, "planets", "assets", "shiplog", "entries", "ZEKISAE_FOKUS.png"),
           (40, -46, 12), (0, 0, 11), (512, 512), lens=35)
    if RENDERS:
        os.makedirs(RENDERS, exist_ok=True)
        render([models["fokuskanone"]], os.path.join(RENDERS, "fokuskanone.png"), (46, -56, 26), (0, 0, 10), lens=40)
        render([models["fokusring"]], os.path.join(RENDERS, "fokusring.png"), (45 + 30, -30, 34), (45, 0, 10))
        render([models["sonde"]], os.path.join(RENDERS, "sonde.png"), (-22 + 10, -13, 13), (-22, 0, 10.5))
        render([models["hauptschalter"]], os.path.join(RENDERS, "hauptschalter.png"), (-22 + 2.2, -8 - 3.2, 2.2), (-22, -8, 0.8))
    os.makedirs(os.path.dirname(BLEND), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND, compress=True)
    print("saved", BLEND)


main()
