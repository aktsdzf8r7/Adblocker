# -*- coding: utf-8 -*-
"""
Build script for the Zeki.Schleiersystem New Horizons addon.

It regenerates everything that is derived from data instead of written by hand:
  * height maps, colour maps and emission maps of all bodies (seamless 3D noise on the sphere,
    with perfectly flat plazas where Nomai structures stand)
  * every planet / star system JSON config, with props placed exactly on the generated terrain
  * ship log images (entry photos, map mode sprites), projection stone decals

The Nomai texts (planets/text) and ship log XMLs (planets/shiplogs) are written by hand and are
only referenced here.

Usage:  python tools/schleier_build.py [path/to/Zeki.Schleiersystem]
Needs:  Python 3.9+, numpy, Pillow
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

MOD = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "Zeki.Schleiersystem"))
NH = "https://raw.githubusercontent.com/Outer-Wilds-New-Horizons/new-horizons/main/NewHorizons/Schemas/"
SYSTEM = "Schleiersystem"

# --------------------------------------------------------------------------------------------
# Verified scene paths of vanilla props (community prop list + NH docs/examples).
# --------------------------------------------------------------------------------------------
P = {
    "vase_thick": "BrittleHollow_Body/Sector_BH/Sector_NorthHemisphere/Sector_NorthPole/Sector_HangingCity/Sector_HangingCity_BlackHoleForge/BlackHoleForgePivot/Props_BlackHoleForge/Prefab_NOM_VaseThick",
    "vase_thin": "BrittleHollow_Body/Sector_BH/Sector_NorthHemisphere/Sector_NorthPole/Sector_HangingCity/Sector_HangingCity_BlackHoleForge/BlackHoleForgePivot/Props_BlackHoleForge/Prefab_NOM_VaseThin",
    "vase_broken": "BrittleHollow_Body/Sector_BH/Sector_NorthHemisphere/Sector_NorthPole/Sector_HangingCity/Sector_HangingCity_BlackHoleForge/BlackHoleForgePivot/Props_BlackHoleForge/Prefab_NOM_VaseThick_Broken",
    "treepot": "BrittleHollow_Body/Sector_BH/Sector_NorthHemisphere/Sector_NorthPole/Sector_HangingCity/Sector_HangingCity_BlackHoleForge/BlackHoleForgePivot/Props_BlackHoleForge/Prefab_NOM_Treepot",
    "potted_tree": "BrittleHollow_Body/Sector_BH/Sector_NorthHemisphere/Sector_NorthPole/Sector_HangingCity/Sector_HangingCity_BlackHoleForge/BlackHoleForgePivot/Props_BlackHoleForge/Prefab_NOM_NomaiTree_Var_1",
    "potted_tree2": "BrittleHollow_Body/Sector_BH/Sector_NorthHemisphere/Sector_NorthPole/Sector_HangingCity/Sector_HangingCity_BlackHoleForge/BlackHoleForgePivot/Props_BlackHoleForge/Prefab_NOM_NomaiTree_Var_2",
    "dry_tree": "Shuttle_Body/Prefab_NOM_Shuttle/Sector_NomaiShuttleInterior/Props_NomaiShuttleInterior/Prefab_NOM_NomaiTree_VarDRY_3",
    "bench": "BrittleHollow_Body/Sector_BH/Sector_NorthHemisphere/Sector_NorthPole/Sector_HangingCity/Sector_HangingCity_BlackHoleForge/BlackHoleForgePivot/Props_BlackHoleForge/Prefab_NOM_SimpleChair_NoSkeleton (1)",
    "bench_skeleton": "BrittleHollow_Body/Sector_BH/Sector_NorthHemisphere/Sector_NorthPole/Sector_NorthPoleSurface/Props_NorthPoleSurface/OtherComponentsGroup/LowBuilding/Prefab_NOM_SimpleChair",
    "skeleton": "BrittleHollow_Body/Sector_BH/Sector_NorthHemisphere/Sector_NorthPole/Sector_NorthPoleSurface/Props_NorthPoleSurface/OtherComponentsGroup/LowBuilding/Prefab_NOM_Skeleton_Large_Pile_A",
    "shelf": "BrittleHollow_Body/Sector_BH/Sector_NorthHemisphere/Sector_NorthPole/Sector_HangingCity/Sector_HangingCity_BlackHoleForge/BlackHoleForgePivot/Props_BlackHoleForge/Prefab_NOM_Shelf (2)/Strucutre_NOM_Shelf",
    "table": "BrittleHollow_Body/Sector_BH/Sector_NorthHemisphere/Sector_NorthPole/Sector_HangingCity/Sector_HangingCity_BlackHoleForge/BlackHoleForgePivot/Props_BlackHoleForge/Props_NOM_Table",
    "staff": "BrittleHollow_Body/Sector_BH/Sector_NorthHemisphere/Sector_NorthPole/Sector_HangingCity/Sector_HangingCity_BlackHoleForge/BlackHoleForgePivot/Props_BlackHoleForge/Prefab_NOM_Staff",
    "bowl": "BrittleHollow_Body/Sector_BH/Sector_GravityCannon/Props_GravityCannon/OtherComponentsGroup/Prefab_NOM_SmallBowl",
    "toys": "BrittleHollow_Body/Sector_BH/Sector_GravityCannon/Props_GravityCannon/OtherComponentsGroup/Prefab_NOM_Toys",
    "box": "Comet_Body/Sector_CO/Sector_CometInterior/Props_CometInterior/Prefab_NOM_Box",
    "box_broken": "Comet_Body/Sector_CO/Sector_CometInterior/Props_CometInterior/Prefab_NOM_BoxBroken",
    "container": "Comet_Body/Sector_CO/Sector_CometInterior/Props_CometInterior/Prefab_NOM_Container",
    "torch": "CaveTwin_Body/Sector_CaveTwin/Sector_SouthHemisphere/Sector_SouthSurface/Sector_SouthPole/Lighting_SouthPole/Prefab_NOM_Torch",
    "lamp_flare": "BrittleHollow_Body/Sector_BH/Sector_EscapePodCrashSite/Sector_NorthFragment/Interactables_NorthFragment/VisibleFrom_EscapePodCrashSite/Prefab_NOM_Lamp_EscapePodFlare",
    "doorway": "BrittleHollow_Body/Sector_BH/Sector_GravityCannon/Lighting_GravityCannon/Prefab_NOM_Doorway",
    "doorway_fancy": "CaveTwin_Body/Sector_CaveTwin/Sector_SouthHemisphere/Sector_SouthUnderground/Sector_City/Lighting_City/Lights_ForumDistrict/TractorBeamFacadeDoors/Prefab_NOM_Doorway_Fancy",
    "eye_symbol": "CaveTwin_Body/Sector_CaveTwin/Sector_SouthHemisphere/Sector_SouthUnderground/Sector_City/Lighting_City/Lights_EyeDistrict/Props_NOM_EyeSymbolCopper",
    "gateway": "CaveTwin_Body/Sector_CaveTwin/Sector_SouthHemisphere/Sector_SouthUnderground/Sector_City/Interactables_City/CityDoors/Prefab_NOM_Gateway",
    "probe_window": "StatueIsland_Body/Sector_StatueIsland/Interactables_StatueIsland/CenterRuin/Structure_NOM_ProbeFloor_StatueIsland",
    "tractor_large": "StatueIsland_Body/Sector_StatueIsland/Interactables_StatueIsland/ControlledByProxy_StatueIsland/Props_NOM_DockingTractorBeam (1)",
    "gravity_cannon": "CaveTwin_Body/Sector_CaveTwin/Sector_SouthHemisphere/Sector_GravityCannon/Geometry_GravityCannon/ControlledByProxy_Arch/Structure_NOM_GravityCannon_HT",
    "crystal_cracked": "BrittleHollow_Body/Sector_BH/Sector Quantum Pole Path/Fragment QuantumPolePath 2/Interactables_QPP2/Prefab_NOM_GravityCrystal_Cracked",
    "bridge": "BrittleHollow_Body/Sector_BH/Sector_OldSettlement/OldSettlement_Interactables/Structure_NOM_BH_OldSettleBridge_Placements/Structure_NOM_BH_OldSettleBridge16",
    "platform_broken": "BrittleHollow_Body/Sector_BH/Sector_EscapePodCrashSite/Sector_CrashFragment/Interactables_CrashFragment/Platforms/Prefab_NOM_BrokenPlatform",
    "symbols3": "BrittleHollow_Body/Sector_BH/Sector_NorthHemisphere/Sector_NorthPole/Sector_HangingCity/Sector_HangingCity_Entrance/Interactables_HangingCity_Entrance/ModuleSymbol (6)",
    "pottery": "StatueIsland_Body/Sector_StatueIsland/DetailPatches_StatueIsland/Foliage_StatueIsland_TopBits/Clutter_NOM_Pottery (%d)",
    "transponder": "CaveTwin_Body/Sector_CaveTwin/Sector_SouthHemisphere/Sector_EscapePod/Interactables_EscapePod/EscapePod_VisibleFrom_Far/DistressBeaconTransmitter/Props_NOM_Transponder",
    "light_beam": "CaveTwin_Body/Sector_CaveTwin/Sector_SouthHemisphere/Sector_EscapePod/Interactables_EscapePod/EscapePod_VisibleFrom_Far/DistressBeaconTransmitter/LightBeam",
    # base game only: no Echoes of the Eye (DreamWorld/RingWorld) props, so the mod works without the DLC
    "gd_tree": "QuantumMoon_Body/Sector_QuantumMoon/State_GD/Interactables_GDState/GDState_Quantum_Objects/Quantum_TreeClump_1/Rock_Tree",
    "th_sapling": "QuantumMoon_Body/Sector_QuantumMoon/State_TH/Interactables_THState/Crater_3/Crater_3_Sapling/QSapling/Tree_TH_Sapling",
    "alpine_clump": "QuantumMoon_Body/Sector_QuantumMoon/State_TH/Interactables_THState/Crater_Surface/Surface_AlpineClump_S/Surface_AlpineClump_S/BatchedGroup",
    "purple_rock": "QuantumMoon_Body/Sector_QuantumMoon/State_EYE/Interactables_EYEState/EYEState_QuantumObjects/EYE_Q_Arch_B/EYE_Q_ArchB/Rocks_EYE_Arch_B",
    "ice_lump": "BrittleHollow_Body/Sector_BH/Sector Great Southern Triangle/Fragment 71_GreatSouthernTriangle/Core_Fragment_71_GreatSouthernTriangle/Props_Core_Fragment_71_GreatSouthernTriangle/Ice_BH_Lump_B",
    "bh_tree": "BrittleHollow_Body/Sector_BH/Sector_GravityCannon/Props_GravityCannon/OtherComponentsGroup/VisibleFrom_BH/Prefab_Tree_BH_Bristle",
    "cactus": "QuantumMoon_Body/Sector_QuantumMoon/State_HT/Interactables_HTState/Interactables_CTState/CTState_Q_Objects/CTState_QCactus/Q_Cactus/Prefab_HGT_Cactus_Single_A",
}

SCENE_PROPS = set(P.values()) | {P["pottery"] % i for i in range(1, 15)}


# --------------------------------------------------------------------------------------------
# Small vector / rotation helpers (Unity conventions: y is up, Euler(0,yaw,0) turns +z to +x)
# --------------------------------------------------------------------------------------------
def norm(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def from_to(a, b):
    """Rotation matrix of Unity's Quaternion.FromToRotation(a, b)."""
    a, b = norm(a), norm(b)
    v = np.cross(a, b)
    c = float(np.dot(a, b))
    if np.linalg.norm(v) < 1e-9:
        return np.eye(3) if c > 0 else np.diag([1.0, -1.0, -1.0])
    k = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + k + k @ k * (1.0 / (1.0 + c))


def yaw_for(up, forward):
    """Euler yaw (degrees) so that an alignRadial prop at `up` looks along `forward`."""
    local = from_to([0, 1, 0], up).T @ norm(forward)
    return math.degrees(math.atan2(local[0], local[2])) % 360


def vec(v, nd=3):
    return {"x": round(float(v[0]), nd), "y": round(float(v[1]), nd), "z": round(float(v[2]), nd)}


def color(r, g, b, a=255):
    return {"r": r, "g": g, "b": b, "a": a}


def direction(lat, lon):
    la, lo = math.radians(lat), math.radians(lon)
    return np.array([math.cos(la) * math.cos(lo), math.sin(la), math.cos(la) * math.sin(lo)])


# --------------------------------------------------------------------------------------------
# Seamless gradient noise on the sphere
# --------------------------------------------------------------------------------------------
class Noise:
    def __init__(self, seed):
        rng = np.random.default_rng(seed)
        self.perm = np.concatenate([rng.permutation(256)] * 2)
        g = rng.normal(size=(256, 3))
        self.grad = g / np.linalg.norm(g, axis=1, keepdims=True)

    def __call__(self, p):
        p = np.asarray(p, float)
        pi = np.floor(p).astype(int)
        f = p - pi
        u = f * f * f * (f * (f * 6 - 15) + 10)
        x0, y0, z0 = pi[..., 0] & 255, pi[..., 1] & 255, pi[..., 2] & 255
        perm, grad = self.perm, self.grad

        def g(dx, dy, dz):
            h = perm[perm[perm[x0 + dx] + y0 + dy] + z0 + dz]
            gr = grad[h]
            return gr[..., 0] * (f[..., 0] - dx) + gr[..., 1] * (f[..., 1] - dy) + gr[..., 2] * (f[..., 2] - dz)

        def lerp(a, b, t):
            return a + (b - a) * t

        x1 = lerp(lerp(g(0, 0, 0), g(1, 0, 0), u[..., 0]), lerp(g(0, 1, 0), g(1, 1, 0), u[..., 0]), u[..., 1])
        x2 = lerp(lerp(g(0, 0, 1), g(1, 0, 1), u[..., 0]), lerp(g(0, 1, 1), g(1, 1, 1), u[..., 0]), u[..., 1])
        return lerp(x1, x2, u[..., 2])

    def fbm(self, p, octaves=5, freq=1.0, gain=0.5, lac=2.0):
        total, amp, norm_ = 0.0, 1.0, 0.0
        for o in range(octaves):
            total = total + amp * self(p * freq + o * 17.31)
            norm_ += amp
            amp *= gain
            freq *= lac
        return total / norm_

    def ridged(self, p, octaves=5, freq=1.0, gain=0.5, lac=2.1):
        total, amp, norm_, weight = 0.0, 1.0, 0.0, 1.0
        for o in range(octaves):
            n = 1.0 - np.abs(self(p * freq + o * 9.7))
            n = n * n * weight
            weight = np.clip(n * 2.0, 0, 1)
            total = total + amp * n
            norm_ += amp
            amp *= gain
            freq *= lac
        return total / norm_


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


# --------------------------------------------------------------------------------------------
# Planets with height map terrain
# --------------------------------------------------------------------------------------------
class Site:
    def __init__(self, name, lat, lon, level, r_in, r_out, kind="flat", plaza=True):
        self.name, self.lat, self.lon, self.level = name, lat, lon, level
        self.r_in, self.r_out, self.kind, self.plaza = r_in, r_out, kind, plaza
        self.c = direction(lat, lon)
        self.east = norm(np.cross(self.c, [0, 1, 0]))
        self.north = np.cross(self.east, self.c)


class Planet:
    def __init__(self, key, name, hmin, hmax, seed, W=1024, H=512):
        self.key, self.name, self.hmin, self.hmax, self.seed = key, name, hmin, hmax, seed
        self.W, self.H = W, H
        self.sites = {}
        self.noise = Noise(seed)
        lon = (np.arange(self.W) + 0.5) / self.W * 2 * np.pi
        row = np.arange(self.H)
        lat_nh = (self.H - 1 - row + 0.5) / self.H * np.pi  # NH samples rows bottom-up, 0 = south pole
        phi = lat_nh - np.pi / 2
        LON, PHI = np.meshgrid(lon, phi)
        self.dirs = np.stack([np.cos(PHI) * np.cos(LON), np.sin(PHI), np.cos(PHI) * np.sin(LON)], axis=-1)
        self.phi = PHI

    # -- terrain -------------------------------------------------------------------------
    def radius_of(self, level):
        return self.hmin + level / 255.0 * (self.hmax - self.hmin)

    def add_site(self, site):
        self.sites[site.name] = site
        return site

    def apply_sites(self, h):
        for s in self.sites.values():
            R = self.radius_of(s.level)
            ang = np.arccos(np.clip(self.dirs @ s.c, -1, 1)) * R
            target = s.level / 255.0
            if s.kind == "flat":
                w = 1.0 - smoothstep(s.r_in, s.r_out, ang)
                h = h * (1 - w) + target * w
            else:  # funnel: steep bowl from the rim (r_out) down to a flat floor (r_in)
                t = smoothstep(s.r_in, s.r_out, ang) ** 0.85
                inside = ang < s.r_out
                h = np.where(inside, target * (1 - t) + h * t, h)
        return h

    def finish(self, h):
        h = self.apply_sites(np.clip(h, 0, 1))
        self.height = np.clip(np.round(h * 255), 0, 255).astype(np.uint8)
        # flat sites must be exact after quantisation
        for s in self.sites.values():
            R = self.radius_of(s.level)
            ang = np.arccos(np.clip(self.dirs @ s.c, -1, 1)) * R
            self.height[ang < s.r_in * 0.999] = s.level

    def sample(self, v):
        """Exactly what NH's CubeSphere does for a vertex direction v."""
        v = norm(v)
        lon = math.degrees(math.atan2(v[2], v[0]))
        lat = math.degrees(math.acos(max(-1.0, min(1.0, -v[1]))))
        sx = self.W * lon / 360.0
        if sx > self.W:
            sx -= self.W
        if sx < 0:
            sx += self.W
        sy = self.H * lat / 180.0
        col = min(int(sx), self.W - 1)
        row = self.H - 1 - min(int(sy), self.H - 1)
        return self.hmin + self.height[row, col] / 255.0 * (self.hmax - self.hmin)

    # -- prop placement --------------------------------------------------------------------
    def at(self, site, e=0.0, n=0.0, up=0.0):
        s = self.sites[site]
        R = self.radius_of(s.level)
        d = norm(s.c * R + s.east * e + s.north * n)
        if s.kind == "flat" and math.hypot(e, n) < s.r_in * 0.9:
            r = R
        else:
            r = self.sample(d)
        return d * (r + up)

    def facing(self, site, pos, target=None, toward=True, angle=0.0):
        """Yaw so that a prop at pos faces the site centre (or `target` position)."""
        up = norm(pos)
        tgt = self.at(site) if target is None else np.asarray(target)
        f = tgt - pos if toward else pos - tgt
        f = f - up * np.dot(f, up)
        if np.linalg.norm(f) < 1e-6:
            f = self.sites[site].north - up * np.dot(self.sites[site].north, up)
        return (yaw_for(up, f) + angle) % 360

    def ring(self, site, radius, count, start=0.0):
        return [(radius * math.cos(math.radians(start + i * 360 / count)), radius * math.sin(math.radians(start + i * 360 / count))) for i in range(count)]


# --------------------------------------------------------------------------------------------
# Config builders
# --------------------------------------------------------------------------------------------
class Body:
    def __init__(self, planet=None):
        self.p = planet
        self.details, self.texts, self.volumes = [], [], {}
        self.props = {}

    def prop(self, kind, item):
        self.props.setdefault(kind, []).append(item)

    def vol(self, kind, item):
        self.volumes.setdefault(kind, []).append(item)

    def detail(self, key, pos, yaw=0.0, scale=1.0, rename=None, pitch=0.0, roll=0.0, **extra):
        d = {"path": P[key] if key in P else key, "position": vec(pos), "rotation": vec([pitch, yaw, roll], 1), "alignRadial": True}
        if scale != 1.0:
            d["scale"] = scale
        if rename:
            d["rename"] = rename
        d.update(extra)
        self.details.append(d)
        return d

    def text(self, kind, xml, pos, yaw=0.0, rename=None, normal=None, **extra):
        t = {"type": kind, "xmlFile": "planets/text/" + xml, "position": vec(pos)}
        if kind == "wall":
            t["normal"] = vec(normal if normal is not None else norm(pos), 4)
        else:
            t["rotation"] = vec([0, yaw, 0], 1)
            t["alignRadial"] = True
        if rename:
            t["rename"] = rename
        t.update(extra)
        self.texts.append(t)
        return t


def reveal(pos, radius, facts, on="enter", **extra):
    v = {"position": vec(pos), "radius": radius, "revealOn": on, "reveals": facts}
    v.update(extra)
    return v


def arcs(*types):
    return [{"type": t} for t in types]


def write_json(rel, data):
    path = os.path.join(MOD, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


# ============================================================================================
# 1) TERRAIN
# ============================================================================================
def build_kern():
    p = Planet("kern", "Schleierkern", 480.0, 585.0, 11011)
    d = p.dirs
    base = p.noise.fbm(d, 4, 1.3)
    ridges = p.noise.ridged(d, 6, 2.4)
    detail = p.noise.fbm(d, 4, 9.0)
    h = 0.30 + 0.55 * base + 0.62 * ridges + 0.05 * detail
    h = (h - np.percentile(h, 0.5)) / (np.percentile(h, 99.5) - np.percentile(h, 0.5))
    h = np.clip(h, 0, 1) * 0.92 + 0.03
    p.add_site(Site("observatorium", 22, 38, 205, 62, 125))
    p.add_site(Site("resonanzfeld", -14, 112, 150, 36, 80))
    p.add_site(Site("grat", 26, 6, 175, 9, 22, plaza=False))
    p.finish(h)
    p.ridges = ridges
    return p


def build_see():
    p = Planet("see", "Schleiersee", 640.0, 740.0, 22041)
    d = p.dirs
    cont = p.noise.fbm(d, 5, 1.7)
    detail = p.noise.fbm(d, 4, 7.0)
    h = 0.5 + 0.85 * (cont - 0.06) + 0.10 * detail
    h = np.clip(h, 0.02, 0.98)
    # sea level at 690 m = 0.5; keep the shores gentle so islands look like islands
    p.add_site(Site("archiv", 9, -32, 196, 72, 140))          # 716.9 m, settlement plateau
    p.add_site(Site("ufer", 9, -32 + 150 / 716.9 * 57.2958 / math.cos(math.radians(9)), 135, 26, 80))  # 692.9 m, lower shore
    p.add_site(Site("tiefe", 9, -32 + 206 / 716.9 * 57.2958 / math.cos(math.radians(9)), 112, 16, 40))  # 683.9 m, under water
    p.add_site(Site("yarrow", 31, 22, 150, 22, 58))           # 698.8 m, the children's island
    p.finish(h)
    return p


def build_bruch():
    p = Planet("bruch", "Schleierbruch", 220.0, 350.0, 33033)
    d = p.dirs
    rng = np.random.default_rng(33)
    h = 0.80 + 0.10 * p.noise.fbm(d, 5, 2.0)
    # craters
    for _ in range(55):
        c = norm(rng.normal(size=3))
        rad = rng.uniform(0.05, 0.28)
        depth = rng.uniform(0.05, 0.16) * (rad / 0.28) ** 0.4
        x = np.arccos(np.clip(d @ c, -1, 1)) / rad
        bowl = np.where(x < 1, depth * (x * x - 1), 0)
        rim = 0.35 * depth * np.exp(-((x - 1) / 0.28) ** 2)
        h = h + bowl + rim
    # cracks: the planet is breaking apart
    cracks = 1.0 - np.abs(p.noise.fbm(d, 3, 2.6))
    crack_mask = smoothstep(0.975, 0.996, cracks)
    h = h - 0.10 * crack_mask
    h = (h - np.percentile(h, 0.3)) / (np.percentile(h, 99.7) - np.percentile(h, 0.3))
    h = np.clip(h, 0, 1) * 0.84 + 0.12
    p.add_site(Site("signalturm", 32, 150, 236, 56, 110))   # 340.5 m plateau
    p.add_site(Site("splitterfeld", -6, -158, 208, 44, 82))  # 326.0 m
    p.add_site(Site("herz", -18, 62, 38, 30, 150, kind="funnel"))  # floor at 239.4 m
    p.finish(h)
    p.crack_mask = crack_mask
    return p


def build_moon():
    p = Planet("signal", "Schleiersignal", 60.0, 80.0, 7331, 512, 256)
    d = p.dirs
    rng = np.random.default_rng(71)
    h = 0.62 + 0.12 * p.noise.fbm(d, 5, 2.5)
    for _ in range(30):
        c = norm(rng.normal(size=3))
        rad = rng.uniform(0.08, 0.4)
        depth = rng.uniform(0.08, 0.2)
        x = np.arccos(np.clip(d @ c, -1, 1)) / rad
        h = h + np.where(x < 1, depth * (x * x - 1), 0) + 0.3 * depth * np.exp(-((x - 1) / 0.3) ** 2)
    h = (h - h.min()) / (h.max() - h.min())
    p.add_site(Site("absturz", 18, 10, 150, 16, 34))  # 71.8 m
    p.finish(h)
    return p


# ============================================================================================
# 2) TEXTURES
# ============================================================================================
def slope_of(p):
    hm = p.hmin + p.height.astype(float) / 255 * (p.hmax - p.hmin)
    R = (p.hmin + p.hmax) / 2
    dx = (np.roll(hm, -1, 1) - np.roll(hm, 1, 1)) / (2 * 2 * np.pi * R * np.maximum(np.cos(p.phi), 0.05) / p.W)
    dy = (np.vstack([hm[1:], hm[-1:]]) - np.vstack([hm[:1], hm[:-1]])) / (2 * np.pi * R / p.H)
    return np.degrees(np.arctan(np.hypot(dx, dy)))


def ramp(t, stops):
    t = np.clip(t, 0, 1)
    xs = [s[0] for s in stops]
    out = np.zeros(t.shape + (3,))
    for i in range(3):
        out[..., i] = np.interp(t, xs, [s[1][i] for s in stops])
    return out


def plaza_mask(p):
    m = np.zeros(p.height.shape)
    for s in p.sites.values():
        if not s.plaza or s.kind != "flat":
            continue
        R = p.radius_of(s.level)
        ang = np.arccos(np.clip(p.dirs @ s.c, -1, 1)) * R
        m = np.maximum(m, 1 - smoothstep(s.r_in * 0.75, s.r_in * 1.05, ang))
    return m


def save(img, rel):
    path = os.path.join(MOD, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path, optimize=True)


def textures(p, kind):
    t = p.height.astype(float) / 255
    sl = slope_of(p)
    n = p.noise.fbm(p.dirs, 4, 14.0) * 0.5 + 0.5
    n2 = p.noise.fbm(p.dirs + 3.3, 3, 40.0) * 0.5 + 0.5
    em = np.zeros(t.shape + (3,))
    if kind == "kern":
        col = ramp(t, [(0, (40, 46, 66)), (0.35, (74, 86, 112)), (0.6, (112, 124, 146)), (0.85, (168, 176, 192)), (1, (214, 220, 232))])
        rock = smoothstep(28, 50, sl)[..., None]
        col = col * (1 - rock) + np.array([58, 60, 74]) * rock
        veins = smoothstep(0.972, 0.995, 1 - np.abs(p.noise.fbm(p.dirs * 1.7 + 5.1, 3, 3.0))) * smoothstep(0.62, 0.38, t) * (1 - plaza_mask(p))
        col = col * (1 - 0.6 * veins[..., None]) + np.array([90, 170, 255]) * 0.6 * veins[..., None]
        em = np.array([60, 140, 255]) * veins[..., None] * 0.9
    elif kind == "see":
        sea = 0.5
        col = ramp(t, [(0, (12, 40, 64)), (0.42, (30, 92, 112)), (0.495, (176, 166, 128)), (0.53, (92, 128, 74)), (0.7, (58, 98, 60)), (0.85, (104, 108, 96)), (1, (190, 196, 200))])
        rock = smoothstep(30, 55, sl)[..., None] * (t > sea)[..., None]
        col = col * (1 - rock) + np.array([96, 98, 92]) * rock
        shallow = smoothstep(0.40, 0.49, t) * (t < sea)
        em = np.array([30, 170, 180]) * (shallow * smoothstep(0.58, 0.75, n2))[..., None] * 0.9
    elif kind == "bruch":
        col = ramp(t, [(0, (30, 18, 34)), (0.3, (62, 40, 64)), (0.6, (96, 72, 98)), (0.8, (134, 110, 128)), (1, (176, 156, 166))])
        rock = smoothstep(25, 50, sl)[..., None]
        col = col * (1 - rock) + np.array([46, 34, 52]) * rock
        lava = p.crack_mask * (1 - plaza_mask(p))
        col = col * (1 - lava[..., None]) + np.array([150, 60, 30]) * lava[..., None]
        em = np.array([255, 110, 30]) * (lava ** 1.5)[..., None]
        herz = p.sites["herz"]
        ang = np.arccos(np.clip(p.dirs @ herz.c, -1, 1)) * p.radius_of(herz.level)
        glow = 1 - smoothstep(herz.r_in * 0.6, herz.r_in * 2.2, ang)
        em = em + np.array([170, 90, 255]) * glow[..., None] * 0.7
        col = col * (1 - 0.5 * glow[..., None]) + np.array([120, 80, 170]) * 0.5 * glow[..., None]
    else:  # moon
        col = ramp(t, [(0, (54, 52, 58)), (0.5, (104, 100, 106)), (1, (164, 160, 168))])
    col = col * (0.82 + 0.3 * n[..., None]) * (0.94 + 0.12 * n2[..., None])
    pm = plaza_mask(p)[..., None]
    if kind != "signal":
        tiles = 0.9 + 0.1 * ((np.floor(np.degrees(p.dirs[..., 0] * 40)) + np.floor(np.degrees(p.dirs[..., 2] * 40))) % 2)[..., None]
        col = col * (1 - pm) + np.array([196, 186, 168]) * tiles * pm
    col = np.clip(col, 0, 255).astype(np.uint8)
    save(Image.fromarray(p.height, "L"), f"planets/assets/terrain/{p.key}_height.png")
    save(Image.fromarray(col, "RGB"), f"planets/assets/terrain/{p.key}_color.png")
    has_em = em.max() > 1
    if has_em:
        save(Image.fromarray(np.clip(em, 0, 255).astype(np.uint8), "RGB"), f"planets/assets/terrain/{p.key}_emission.png")
    p.color = col
    return has_em


def heightmap_module(p, has_em, smooth=0.05, metallic=0.0, emission=None):
    m = {
        "heightMap": f"planets/assets/terrain/{p.key}_height.png",
        "textureMap": f"planets/assets/terrain/{p.key}_color.png",
        "minHeight": p.hmin,
        "maxHeight": p.hmax,
        "resolution": p.W // 4,
        "smoothness": smooth,
        "metallic": metallic,
    }
    if has_em:
        m["emissionMap"] = f"planets/assets/terrain/{p.key}_emission.png"
        if emission:
            m["emissionColor"] = emission
    return m


# ============================================================================================
# 3) SHIP LOG IMAGES AND DECALS
# ============================================================================================
def render_planet(p, size=512, light=(-0.45, 0.4, 0.8), view_lat=15, view_lon=0, zoom=1.0, bg=(0, 0, 0, 0), glow=None):
    """Orthographic render of a height-mapped body for ship log sprites."""
    ys, xs = np.mgrid[0:size, 0:size]
    u = (xs + 0.5) / size * 2 - 1
    v = 1 - (ys + 0.5) / size * 2
    u, v = u / zoom, v / zoom
    rr = u * u + v * v
    inside = rr <= 1
    w = np.sqrt(np.clip(1 - rr, 0, 1))
    # camera basis: looking at direction(view_lat, view_lon) from outside
    f = direction(view_lat, view_lon)
    right = norm(np.cross([0, 1, 0], f))
    upv = np.cross(f, right)
    pts = u[..., None] * right + v[..., None] * upv + w[..., None] * f
    lon = np.degrees(np.arctan2(pts[..., 2], pts[..., 0])) % 360
    lat_nh = np.degrees(np.arccos(np.clip(-pts[..., 1], -1, 1)))
    col_ = np.clip((lon / 360 * p.W).astype(int), 0, p.W - 1)
    row_ = np.clip(p.H - 1 - (lat_nh / 180 * p.H).astype(int), 0, p.H - 1)
    rgb = p.color[row_, col_].astype(float)
    lightv = norm(light[0] * right + light[1] * upv + light[2] * f)  # light is given in camera space
    lam = np.clip(pts @ lightv, 0, 1)
    shade = 0.18 + 0.95 * lam
    rgb = rgb * shade[..., None]
    if glow is not None:
        rim = np.clip(1 - w, 0, 1) ** 3
        rgb = rgb + np.array(glow) * rim[..., None] * 0.8
    out = np.zeros((size, size, 4), np.uint8)
    out[..., :3] = np.clip(rgb, 0, 255)
    out[..., 3] = inside * 255
    img = Image.fromarray(out, "RGBA")
    if bg[3]:
        base = Image.new("RGBA", (size, size), bg)
        base.alpha_composite(img)
        img = base
    return img


def starfield(size, seed, tint=(150, 120, 255)):
    rng = np.random.default_rng(seed)
    img = Image.new("RGBA", (size, size), (6, 6, 14, 255))
    dr = ImageDraw.Draw(img)
    for _ in range(260):
        x, y = rng.uniform(0, size, 2)
        b = int(rng.uniform(70, 255))
        r = rng.choice([0.6, 0.9, 1.4], p=[0.7, 0.25, 0.05])
        dr.ellipse([x - r, y - r, x + r, y + r], fill=(b, b, min(255, b + 20), 255))
    veil = Image.new("RGBA", (size, size), tint + (0,))
    a = np.zeros((size, size), np.uint8)
    yy, xx = np.mgrid[0:size, 0:size]
    a[:] = np.clip(60 * np.exp(-((xx - size * 0.5) ** 2 + (yy - size * 0.55) ** 2) / (2 * (size * 0.33) ** 2)), 0, 255).astype(np.uint8)
    veil.putalpha(Image.fromarray(a))
    img.alpha_composite(veil)
    return img


def spiral(draw, cx, cy, r, turns=2.3, width=4, fill=(150, 200, 255, 255), reverse=False):
    pts = []
    for i in range(240):
        t = i / 239
        ang = (t * turns * 2 * math.pi) * (-1 if reverse else 1)
        rr = r * (1 - t) ** 1.3
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    draw.line(pts, fill=fill, width=width, joint="curve")


def nomai_art(title_seed, motif, size=512):
    img = starfield(size, title_seed)
    d = ImageDraw.Draw(img)
    c = size / 2
    if motif == "veil":
        for i in range(9):
            y = size * (0.25 + 0.06 * i)
            pts = [(x, y + 18 * math.sin(x / 41 + i)) for x in range(0, size + 8, 8)]
            d.line(pts, fill=(170, 140, 255, 90 + i * 12), width=3)
        d.ellipse([c - 60, c - 60, c + 60, c + 60], fill=(235, 240, 255, 255))
        d.ellipse([c - 74, c - 74, c + 74, c + 74], outline=(200, 180, 255, 160), width=6)
    elif motif == "eye":
        d.ellipse([c - 170, c - 90, c + 170, c + 90], outline=(190, 160, 255, 255), width=6)
        d.ellipse([c - 62, c - 62, c + 62, c + 62], fill=(120, 80, 220, 255))
        d.ellipse([c - 24, c - 24, c + 24, c + 24], fill=(250, 245, 255, 255))
        spiral(d, c, c, 150, 1.4, 3, (170, 140, 255, 200))
    elif motif == "clan":
        for k, (dx, dy) in enumerate([(-120, 40), (-40, -30), (40, 10), (120, -40), (0, 110)]):
            spiral(d, c + dx, c + dy, 55 + 8 * (k % 2), 2.0, 4, (240, 200, 120, 255), reverse=k % 2 == 1)
    elif motif == "crystal":
        for k in range(7):
            x = c + (k - 3) * 58
            hgt = 110 + 70 * math.sin(k * 1.7) ** 2
            d.polygon([(x, c + 120), (x - 22, c + 60), (x, c + 120 - hgt - 60), (x + 22, c + 60)], fill=(150, 120, 255, 220), outline=(230, 220, 255, 255))
    elif motif == "beam":
        d.polygon([(c - 18, size), (c + 18, size), (c + 6, 0), (c - 6, 0)], fill=(220, 235, 255, 230))
        for k in range(6):
            a = k * math.pi / 3
            d.arc([c - 150, c + 40 - 60, c + 150, c + 40 + 60], math.degrees(a), math.degrees(a) + 40, fill=(140, 190, 255, 255), width=8)
    elif motif == "probe":
        d.line([(c - 140, c + 140), (c + 60, c - 60)], fill=(255, 210, 150, 200), width=3)
        d.polygon([(c + 60, c - 80), (c + 85, c - 55), (c + 60, c - 30), (c + 35, c - 55)], fill=(220, 200, 170, 255))
        for k in range(1, 5):
            d.arc([c + 60 - 30 * k, c - 55 - 30 * k, c + 60 + 30 * k, c - 55 + 30 * k], -80, 10, fill=(255, 200, 120, 255 - 45 * k), width=3)
    elif motif == "shards":
        rng = np.random.default_rng(title_seed)
        for k in range(9):
            x, y = c + rng.uniform(-170, 170), c + rng.uniform(-110, 140)
            a = rng.uniform(-0.5, 0.5)
            hgt = rng.uniform(40, 110)
            pts = [(-14, 0), (0, -hgt), (14, 0), (0, hgt * 0.35)]
            pts = [(x + px * math.cos(a) - py * math.sin(a), y + px * math.sin(a) + py * math.cos(a)) for px, py in pts]
            ghost = k % 3 == 0
            d.polygon(pts, fill=(150, 120, 255, 70 if ghost else 220), outline=(230, 220, 255, 120 if ghost else 255))
    elif motif == "children":
        for k in range(4):
            spiral(d, c - 110 + k * 75, c + (k % 2) * 40 - 20, 38, 1.7, 3, (255, 220, 120, 255), reverse=k % 2 == 0)
        d.ellipse([c - 30, c + 110, c + 30, c + 130], fill=(160, 150, 140, 255))
        d.ellipse([c - 22, c + 92, c + 22, c + 112], fill=(150, 140, 130, 255))
        d.ellipse([c - 14, c + 76, c + 14, c + 94], fill=(140, 130, 120, 255))
    return img


COORDS = {"x": [1, 0, 5, 4], "y": [2, 5, 3], "z": [0, 3, 4, 1]}


def coordinates_image(size=512):
    img = starfield(size, 5, (120, 90, 220))
    d = ImageDraw.Draw(img)
    hexes = [(size * 0.2, size * 0.36), (size * 0.5, size * 0.64), (size * 0.8, size * 0.36)]
    r = size * 0.13
    for (cx, cy), key in zip(hexes, ["x", "y", "z"]):
        # node layout of the Vessel's coordinate panel: 0 top-left, then clockwise
        nodes = [(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))) for a in [240, 300, 0, 60, 120, 180]]
        d.polygon(nodes, outline=(110, 100, 150, 255))
        for nx, ny in nodes:
            d.ellipse([nx - 4, ny - 4, nx + 4, ny + 4], fill=(150, 140, 190, 255))
        pts = [nodes[i] for i in COORDS[key]]
        d.line(pts, fill=(205, 175, 255, 255), width=7, joint="curve")
        sx, sy = pts[0]
        d.ellipse([sx - 9, sy - 9, sx + 9, sy + 9], fill=(255, 245, 255, 255))
    return img


def decal(symbol, size=256):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = size / 2
    w = (255, 255, 255, 255)
    if symbol == "kern":
        d.ellipse([c - 90, c - 90, c + 90, c + 90], outline=w, width=14)
        d.ellipse([c - 28, c - 28, c + 28, c + 28], fill=w)
        for k in range(6):
            a = math.radians(k * 60)
            d.line([(c + 40 * math.cos(a), c + 40 * math.sin(a)), (c + 76 * math.cos(a), c + 76 * math.sin(a))], fill=w, width=10)
    elif symbol == "see":
        d.ellipse([c - 90, c - 90, c + 90, c + 90], outline=w, width=14)
        for k in range(3):
            y = c - 40 + k * 40
            d.line([(x, y + 14 * math.sin((x - c) / 18)) for x in range(int(c - 66), int(c + 67), 3)], fill=w, width=10)
    elif symbol == "bruch":
        d.arc([c - 90, c - 90, c + 90, c + 90], 20, 160, fill=w, width=14)
        d.arc([c - 90, c - 90, c + 90, c + 90], 200, 340, fill=w, width=14)
        d.line([(c - 50, c - 70), (c + 10, c - 10), (c - 20, c + 20), (c + 45, c + 75)], fill=w, width=12)
    elif symbol == "herz":
        d.ellipse([c - 100, c - 55, c + 100, c + 55], outline=w, width=12)
        d.ellipse([c - 34, c - 34, c + 34, c + 34], fill=w)
        d.polygon([(c, c - 110), (c - 12, c - 70), (c + 12, c - 70)], fill=w)
        d.polygon([(c, c + 110), (c - 12, c + 70), (c + 12, c + 70)], fill=w)
    return img


# ============================================================================================
# 4) BODIES
# ============================================================================================
def ship_log(p_key, xml, sprite_body=None, map_scale=None):
    m = {"xmlFile": f"planets/shiplogs/{xml}", "spriteFolder": "planets/assets/shiplog/entries"}
    mm = {}
    if sprite_body:
        mm["revealedSprite"] = f"planets/assets/shiplog/map/{sprite_body}.png"
        mm["outlineSprite"] = f"planets/assets/shiplog/map/{sprite_body}_outline.png"
    if map_scale:
        mm["scale"] = map_scale
    if mm:
        m["mapMode"] = mm
    return m


def body_header(name, system=SYSTEM):
    return {"$schema": NH + "body_schema.json", "name": name, "starSystem": system}


def kern_config(p, has_em):
    b = Body(p)
    O = "observatorium"
    # ---- Spiegelring / Lichtbündler: ring of glowing arches around a glass dish ----
    centre = p.at(O)
    b.detail("probe_window", p.at(O, up=0.05), 0, 2.2, "Lichtbuendler_Spiegelschale")
    for i, (e, n) in enumerate(p.ring(O, 15, 6, 15)):
        pos = p.at(O, e, n)
        b.detail("doorway_fancy", pos, p.facing(O, pos), 1.6, f"Lichtbuendler_Spiegelbogen_{i + 1}")
    # beam that only burns once the veil is lifted (Tansy's wish)
    b.detail("light_beam", p.at(O, up=1.0), 0, 3.0, "Lichtbuendler_Strahl", activationCondition="ZEKSCHLEIER_SCHLEIER_GEHOBEN", keepLoaded=True)
    for i, (e, n) in enumerate(p.ring(O, 9, 6, 45)):
        b.detail("torch", p.at(O, e, n), 0, 1.0, f"Lichtbuendler_Fackel_{i + 1}", activationCondition="ZEKSCHLEIER_SCHLEIER_GEHOBEN")
    # ---- observatory plaza ----
    pos = p.at(O, -30, 22)
    b.text("whiteboard", "Kern_Beobachtung.xml", pos, p.facing(O, pos), "Whiteboard_Beobachtung", arcInfo=arcs("adult", "adult", "adult", "adult", "child"), seed=101)
    pos = p.at(O, 28, 20)
    b.text("computer", "Kern_Lichtbuendler.xml", pos, p.facing(O, pos), "Computer_Lichtbuendler")
    # Tansy's last watch: skeleton, recorder, a dry tree
    tansy = p.at(O, 34, -26)
    b.detail("skeleton", tansy, p.facing(O, tansy), 1.0, "Tansy")
    b.text("recorder", "Kern_Tansy.xml", p.at(O, 36.5, -23), 0, "Recorder_Tansy")
    b.detail("dry_tree", p.at(O, 30, -31), 40, 1.0, "Tansys_Baum")
    b.detail("staff", p.at(O, 32, -22, 0.1), 0, 1.0, "Tansys_Stab", pitch=85)
    # projection pool of the observatory + stones to the archive and to the signal tower
    pool = p.at(O, -36, -18)
    b.prop("remotes", {"id": "ZEKSCHLEIER_REMOTE_KERN", "decalPath": "planets/assets/decals/kern.png",
                       "platform": {"position": vec(pool), "rotation": vec([0, p.facing(O, pool), 0], 1), "alignRadial": True, "rename": "Projektionsbecken_Kern"}})
    b.prop("remotes", {"id": "ZEKSCHLEIER_REMOTE_SEE", "decalPath": "planets/assets/decals/see.png",
                       "stones": [{"position": vec(p.at(O, -27, -24, 0.15)), "alignRadial": True, "rename": "Projektionsstein_See"}]})
    b.prop("remotes", {"id": "ZEKSCHLEIER_REMOTE_BRUCH", "decalPath": "planets/assets/decals/bruch.png",
                       "stones": [{"position": vec(p.at(O, -25, -21, 0.15)), "alignRadial": True, "rename": "Projektionsstein_Bruch"}]})
    # warp: observatory -> archive (and back via the receiver's return function)
    pad = p.at(O, 0, 40)
    b.prop("warpTransmitters", {"frequency": "ZEKSCHLEIER_KERN_SEE", "position": vec(pad), "rotation": vec([0, p.facing(O, pad), 0], 1),
                                "alignRadial": True, "alignmentWindow": 360, "rename": "Warp_zum_Archiv"})
    # warp receiver for the signal tower on the outer planet
    rec = p.at(O, 0, -40)
    b.prop("warpReceivers", {"frequency": "ZEKSCHLEIER_BRUCH_KERN", "position": vec(rec), "rotation": vec([0, p.facing(O, rec), 0], 1), "alignRadial": True,
                             "detailed": True, "rename": "Warpempfaenger_Observatorium",
                             "computer": {"position": vec(p.at(O, 13, -46)), "rotation": vec([0, p.facing(O, p.at(O, 13, -46)), 0], 1), "alignRadial": True}})
    # furniture & lamps around the plaza
    for i, (e, n) in enumerate([(-48, 6), (48, 4), (-26, -48), (27, -49), (-46, -32), (46, -30)]):
        pos = p.at(O, e, n)
        b.detail("doorway", pos, p.facing(O, pos), 1.0, f"Leuchtbogen_{i + 1}")
    for i, (e, n, k) in enumerate([(-20, 30, "vase_thick"), (-18, 33, "vase_thin"), (22, 28, "potted_tree"), (40, 14, "treepot"),
                                     (-42, -6, "bench"), (-40, -10, "bench"), (-14, -34, "table"), (-11, -37, "container"), (-6, 36, "box")]):
        pos = p.at(O, e, n)
        b.detail(k, pos, p.facing(O, pos), 1.0)
    # ---- ridge cairn on the way up ----
    b.text("cairnCT", "Kern_Wegweiser.xml", p.at("grat"), 0, "Steinmaennchen_Grat")
    # ---- resonance field: giant cracked crystals ----
    R = "resonanzfeld"
    for i, (e, n, s, yw) in enumerate([(0, 0, 4.5, 0), (14, 6, 3.0, 50), (-12, 9, 3.4, 120), (6, -15, 2.6, 200), (-16, -10, 2.2, 290), (24, -8, 2.0, 30)]):
        b.detail("crystal_cracked", p.at(R, e, n), yw, s, "Strahlungsresonator" if i == 0 else f"Resonanzkristall_{i}")
    b.text("trailmarker", "Kern_Resonator.xml", p.at(R, -4, 22), 0, "Wegmarke_Yarrow")
    b.detail("toys", p.at(R, -2, 25), 10, 1.0, "Yarrows_Spielzeug")
    b.prop("signals", {"frequency": "Quantum", "name": "Resonanzkristall", "audio": "NomaiGravCrystalFlickerAmbient_LP",
                       "position": vec(p.at(R, 0, 0, 4)), "sourceRadius": 3, "detectionRadius": 400, "identificationRadius": 40})
    # ---- volumes ----
    b.vol("revealVolumes", reveal(p.at(O, up=8), 60, ["ZEKSCHLEIER_KERN_FOUND"]))
    b.prop("entryLocation", {"id": "ZEKSCHLEIER_KERN", "position": vec(p.at(O, up=4))})
    b.prop("entryLocation", {"id": "ZEKSCHLEIER_KERN_WACHE", "position": vec(tansy)})
    b.prop("entryLocation", {"id": "ZEKSCHLEIER_KERN_RESONANZFELD", "position": vec(p.at(R, up=3))})

    cfg = body_header("Schleierkern")
    cfg.update({
        "Base": {"surfaceSize": 530, "surfaceGravity": 10, "gravityFallOff": "linear"},
        "Orbit": {"primaryBody": "Schleierstern", "semiMajorAxis": 4300, "eccentricity": 0.06, "inclination": 3, "longitudeOfAscendingNode": 20,
                  "trueAnomaly": 35, "siderealPeriod": 5, "axialTilt": 8, "tint": color(130, 170, 255)},
        "Atmosphere": {"size": 660, "atmosphereTint": color(110, 140, 200), "atmosphereSunIntensity": 0.9, "useAtmosphereShader": True,
                       "fogTint": color(120, 140, 185, 255), "fogSize": 640, "fogDensity": 0.35, "hasOxygen": False},
        "HeightMap": heightmap_module(p, has_em, 0.12, 0.05, color(120, 170, 255)),
        "AmbientLights": [{"intensity": 0.35, "tint": color(140, 170, 255), "outerRadius": 700, "innerRadius": 560}],
        "MapMarker": {"enabled": True},
        "ShipLog": ship_log("kern", "Schleierkern.xml", "kern"),
        "Props": {
            "details": b.details,
            "translatorText": b.texts,
            "scatter": [
                {"path": P["crystal_cracked"], "count": 28, "seed": 1101, "minHeight": 505, "maxHeight": 548, "scale": 1.6, "preventOverlap": True},
                {"path": P["purple_rock"], "count": 12, "seed": 1102, "minHeight": 495, "maxHeight": 545, "scale": 1.0, "preventOverlap": True},
            ],
            **b.props,
        },
        "Volumes": b.volumes,
    })
    return cfg


def see_config(p, has_em):
    b = Body(p)
    A, U, T, Y = "archiv", "ufer", "tiefe", "yarrow"
    # ---- the settlement on the plateau: an arc of buildings around the archive ----
    b.detail("gateway", p.at(A, 0, -60), p.facing(A, p.at(A, 0, -60)), 1.0, "Tor_der_Siedlung")
    for i, (e, n) in enumerate(p.ring(A, 52, 9, 200)):
        if -20 < e < 40 and n > 0:
            continue
        pos = p.at(A, e, n)
        b.detail("doorway", pos, p.facing(A, pos), 1.2, f"Siedlungsbogen_{i + 1}")
    # archive core: shelves, computer, scroll, the projection pool
    for i, (e, n) in enumerate([(-14, 10), (-10, 14), (-6, 17), (6, 17), (10, 14), (14, 10)]):
        pos = p.at(A, e, n)
        b.detail("shelf", pos, p.facing(A, pos), 1.0, f"Archivregal_{i + 1}")
    pos = p.at(A, 0, 12)
    b.text("computer", "See_Archiv.xml", pos, p.facing(A, pos), "Computer_Archiv")
    b.text("scroll", "See_Geschwister.xml", p.at(A, -8, 9, 0.2), 30, "Schriftrolle_Geschwister")
    pos = p.at(A, -26, -14)
    b.text("whiteboard", "See_Ankunft.xml", pos, p.facing(A, pos), "Whiteboard_Ankunft", arcInfo=arcs("adult", "adult", "adult", "adult", "child"), seed=202)
    # gardens, homes, everyday things
    for i, (e, n, k) in enumerate([(-36, 4, "potted_tree"), (-38, -2, "potted_tree2"), (36, 2, "potted_tree"), (38, -6, "potted_tree2"),
                                     (-20, -36, "bench"), (-16, -38, "bench"), (20, -34, "table"), (24, -30, "bowl"), (18, -38, "vase_thick"),
                                     (-30, 24, "vase_thin"), (30, 24, "vase_thick"), (0, -24, "treepot"), (-44, -20, "box"), (44, -24, "container")]):
        pos = p.at(A, e, n)
        b.detail(k, pos, p.facing(A, pos), 1.0)
    for i, (e, n) in enumerate(p.ring(A, 24, 6, 0)):
        b.detail("torch", p.at(A, e, n), 0, 1.0, f"Archivfackel_{i + 1}", activationCondition="ZEKSCHLEIER_SCHLEIER_GEHOBEN")
    pool = p.at(A, 28, -12)
    b.prop("remotes", {"id": "ZEKSCHLEIER_REMOTE_SEE", "decalPath": "planets/assets/decals/see.png",
                       "platform": {"position": vec(pool), "rotation": vec([0, p.facing(A, pool), 0], 1), "alignRadial": True, "rename": "Projektionsbecken_Archiv"}})
    b.prop("remotes", {"id": "ZEKSCHLEIER_REMOTE_KERN", "decalPath": "planets/assets/decals/kern.png",
                       "stones": [{"position": vec(p.at(A, 19, -18, 0.15)), "alignRadial": True, "rename": "Projektionsstein_Kern"}]})
    b.prop("remotes", {"id": "ZEKSCHLEIER_REMOTE_HERZ", "decalPath": "planets/assets/decals/herz.png",
                       "stones": [{"position": vec(p.at(A, 21, -21, 0.15)), "alignRadial": True, "rename": "Projektionsstein_Herz"}]})
    # warp receiver from the observatory, with a computer that logs arrivals
    rec = p.at(A, -8, -44)
    b.prop("warpReceivers", {"frequency": "ZEKSCHLEIER_KERN_SEE", "position": vec(rec), "rotation": vec([0, p.facing(A, rec), 0], 1), "alignRadial": True,
                             "detailed": True, "rename": "Warpempfaenger_Archiv",
                             "computer": {"position": vec(p.at(A, 4, -46)), "rotation": vec([0, p.facing(A, p.at(A, 4, -46)), 0], 1), "alignRadial": True}})
    # ---- lower shore: the warp into the heart ----
    pad = p.at(U)
    b.prop("warpTransmitters", {"frequency": "ZEKSCHLEIER_SEE_HERZ", "position": vec(pad), "rotation": vec([0, p.facing(U, pad, p.at(A)), 0], 1),
                                "alignRadial": True, "alignmentWindow": 360, "rename": "Warp_zum_Herz"})
    for i, (e, n) in enumerate(p.ring(U, 12, 4, 45)):
        b.detail("lamp_flare", p.at(U, e, n), 0, 1.0, f"Uferlampe_{i + 1}")
    b.detail("eye_symbol", p.at(U, -16, 0, 0.1), p.facing(U, p.at(U, -16, 0)), 1.5, "Augensymbol_Ufer")
    # ---- under water: Ilex' message on the sea floor ----
    b.text("wall", "See_Augenlid.xml", p.at(T, up=0.15), rename="Bodenschrift_Augenlid", seed=303)
    b.detail("lamp_flare", p.at(T, 6, 0), 0, 1.0, "Unterwasserlampe")
    # ---- Yarrow's island ----
    b.text("wall", "See_Kinder.xml", p.at(Y, 0, 0, 0.12), rename="Bodenschrift_Kinder", seed=404, arcInfo=arcs("child", "child", "child", "child", "child"))
    b.text("cairnTH", "See_Steinturm.xml", p.at(Y, 9, 6), 0, "Yarrows_Steinturm")
    b.detail("toys", p.at(Y, -6, 5), 0, 1.0, "Spielzeug_1")
    b.detail("toys", p.at(Y, 7, -6), 140, 1.0, "Spielzeug_2")
    b.detail("bowl", p.at(Y, -8, -4), 0, 1.0, "Schale")
    b.detail("potted_tree2", p.at(Y, 12, -10), 0, 1.0, "Inselbaum")
    # ---- epilogue: text that only becomes observable once the veil lifts ----
    epilog = p.at(A, 0, -10)
    b.detail("", epilog, 0, 1.0, "Epilog", activationCondition="ZEKSCHLEIER_SCHLEIER_GEHOBEN")
    b.details[-1].pop("path")  # no path: NH creates an empty object that the epilogue text hangs off
    # NH reads `normal` in planet space even for parented text, so it is the radial direction here
    b.text("wall", "See_Epilog.xml", [0, 0.12, 0], rename="Bodenschrift_Epilog", seed=505, parentPath="Sector/Epilog", isRelativeToParent=True,
           arcInfo=arcs("adult", "adult", "adult", "child"), normal=norm(epilog))
    # ---- volumes ----
    b.vol("revealVolumes", reveal(p.at(A, up=6), 75, ["ZEKSCHLEIER_SEE_FOUND"]))
    b.prop("entryLocation", {"id": "ZEKSCHLEIER_SEE", "position": vec(p.at(A, up=4))})
    b.prop("entryLocation", {"id": "ZEKSCHLEIER_SEE_INSEL", "position": vec(p.at(Y, up=3))})
    b.prop("entryLocation", {"id": "ZEKSCHLEIER_KOORDINATEN", "position": vec(p.at(A, 0, -10, 2))})

    cfg = body_header("Schleiersee")
    cfg.update({
        "Base": {"surfaceSize": 700, "surfaceGravity": 7, "gravityFallOff": "linear"},
        "Orbit": {"primaryBody": "Schleierstern", "semiMajorAxis": 7200, "eccentricity": 0.12, "inclination": -4, "longitudeOfAscendingNode": 140,
                  "trueAnomaly": 190, "siderealPeriod": 7, "axialTilt": 14, "tint": color(90, 200, 220)},
        "Atmosphere": {"size": 870, "atmosphereTint": color(90, 170, 210), "atmosphereSunIntensity": 1.0, "useAtmosphereShader": True,
                       "fogTint": color(150, 190, 210, 255), "fogSize": 820, "fogDensity": 0.45, "hasOxygen": True, "hasTrees": True},
        "Water": {"size": 690, "tint": color(35, 105, 150, 210)},
        "HeightMap": heightmap_module(p, has_em, 0.18, 0.0, color(80, 220, 230)),
        "MapMarker": {"enabled": True},
        "ShipLog": ship_log("see", "Schleiersee.xml", "see"),
        "Props": {
            "details": b.details,
            "translatorText": b.texts,
            "scatter": [
                {"path": P["gd_tree"], "count": 40, "seed": 2201, "minHeight": 693, "maxHeight": 713, "scale": 1.0, "preventOverlap": True},
                {"path": P["th_sapling"], "count": 30, "seed": 2202, "minHeight": 694, "maxHeight": 712, "scale": 1.3, "preventOverlap": True},
                {"path": P["alpine_clump"], "count": 10, "seed": 2203, "minHeight": 700, "maxHeight": 714, "scale": 1.0, "preventOverlap": True},
                {"path": P["pottery"] % 3, "count": 14, "seed": 2204, "minHeight": 691, "maxHeight": 714, "scale": 1.0, "preventOverlap": True},
            ],
            **b.props,
        },
        "Volumes": b.volumes,
    })
    return cfg


def bruch_config(p, has_em):
    b = Body(p)
    S, F, H = "signalturm", "splitterfeld", "herz"
    # ---- signal tower: the probe launcher (a Nomai cannon structure) and the transmitter ----
    cannon = p.at(S, 4, 34)
    b.detail("gravity_cannon", cannon, p.facing(S, cannon, toward=False), 1.0, "Sondenkatapult")
    tower = p.at(S)
    b.detail("transponder", tower, 0, 4.0, "Signalturm_Sender")
    b.detail("light_beam", p.at(S, 0, 0, 2), 0, 1.5, "Signalturm_Strahl", activationCondition="ZEKSCHLEIER_SCHLEIER_GEHOBEN", keepLoaded=True)
    b.prop("signals", {"frequency": "Schleier-Echo", "name": "Signalturm", "audio": "NomaiEscapePodDistressSignal_LP",
                       "position": vec(p.at(S, 0, 0, 6)), "sourceRadius": 4, "detectionRadius": 6000, "identificationRadius": 120,
                       "reveals": "ZEKSCHLEIER_BRUCH_FOUND"})
    pos = p.at(S, 16, -20)
    b.text("whiteboard", "Bruch_Signalturm.xml", pos, p.facing(S, pos), "Whiteboard_Sonden", seed=606)
    pos = p.at(S, -4, -30)
    b.text("whiteboard", "Bruch_Abschied.xml", pos, p.facing(S, pos), "Whiteboard_Abschied", seed=707)
    for i, (e, n, k) in enumerate([(30, 4, "box_broken"), (32, 8, "box"), (28, 10, "container"), (-30, -6, "platform_broken"),
                                     (-34, -18, "vase_broken"), (10, -36, "bench")]):
        pos = p.at(S, e, n)
        b.detail(k, pos, p.facing(S, pos), 1.0)
    for i, ang in enumerate((200, 235, 270, 300, 340)):
        e, n = 46 * math.cos(math.radians(ang)), 46 * math.sin(math.radians(ang))
        pos = p.at(S, e, n)
        b.detail("doorway", pos, p.facing(S, pos), 1.0, f"Turmbogen_{i + 1}")
    pool = p.at(S, 30, -26)
    b.prop("remotes", {"id": "ZEKSCHLEIER_REMOTE_BRUCH", "decalPath": "planets/assets/decals/bruch.png",
                       "platform": {"position": vec(pool), "rotation": vec([0, p.facing(S, pool), 0], 1), "alignRadial": True, "rename": "Projektionsbecken_Signalturm"}})
    b.prop("remotes", {"id": "ZEKSCHLEIER_REMOTE_SEE", "decalPath": "planets/assets/decals/see.png",
                       "stones": [{"position": vec(p.at(S, 22, -30, 0.15)), "alignRadial": True, "rename": "Projektionsstein_See_2"}]})
    pad = p.at(S, -36, 22)
    b.prop("warpTransmitters", {"frequency": "ZEKSCHLEIER_BRUCH_KERN", "position": vec(pad), "rotation": vec([0, p.facing(S, pad), 0], 1),
                                "alignRadial": True, "alignmentWindow": 360, "rename": "Warp_zum_Observatorium"})
    # ---- shard field: quantum shards that wander when nobody looks ----
    sockets = []
    for i, (e, n) in enumerate([(0, 0), (16, 8), (-14, 12), (8, -18), (-20, -8), (26, -10), (-4, 26), (-28, 16)]):
        pos = p.at(F, e, n)
        sockets.append({"position": vec(pos), "rotation": vec([0, (i * 47) % 360, 0], 1), "alignRadial": True, "probability": 1})
    b.prop("socketQuantumGroups", {"rename": "Wandernde_Splitter", "sockets": sockets, "details": [
        {"path": P["crystal_cracked"], "rename": f"Splitter_{k + 1}", "scale": 2.4, "keepLoaded": True, "alignWithGravity": True} for k in range(4)]})
    b.text("trailmarker", "Bruch_Splitter.xml", p.at(F, 6, -34), 0, "Wegmarke_Splitter")
    b.prop("signals", {"frequency": "Quantum", "name": "Wandernde Splitter", "audio": "QuantumAmbience_LP", "position": vec(p.at(F, 0, 0, 3)),
                       "sourceRadius": 30, "detectionRadius": 500, "identificationRadius": 60})
    b.vol("revealVolumes", reveal(p.at(F, up=4), 30, ["ZEKSCHLEIER_SPLITTER_GESEHEN"], "observe", maxDistance=90, maxAngle=50))
    # ---- the maw and the heart at its floor ----
    hs = p.sites[H]
    floor = p.at(H)
    rim = norm(hs.c * p.radius_of(hs.level) + hs.north * 170)
    rim = rim * p.sample(rim)
    b.text("cairnBH", "Bruch_Warnung.xml", rim, p.facing(H, rim), "Steinmaennchen_Schlund")
    b.vol("revealVolumes", reveal(p.at(H, up=20), 60, ["ZEKSCHLEIER_SCHLUND"], "observe", maxDistance=320, maxAngle=35))
    b.detail("crystal_cracked", p.at(H, up=-0.5), 0, 9.0, "Herzsplitter")
    for i, (e, n) in enumerate(p.ring(H, 25, 5, 18)):
        pos = p.at(H, e, n)
        b.detail("doorway_fancy", pos, p.facing(H, pos), 1.3, f"Herzbogen_{i + 1}")
    ilex = p.at(H, 0, -8)
    b.detail("bench_skeleton", ilex, p.facing(H, ilex), 1.0, "Ilex")
    b.text("recorder", "Herz_Ilex.xml", p.at(H, 2.5, -9), 0, "Recorder_Ilex")
    rec = p.at(H, -10, 11)
    b.prop("warpReceivers", {"frequency": "ZEKSCHLEIER_SEE_HERZ", "position": vec(rec), "rotation": vec([0, p.facing(H, rec), 0], 1), "alignRadial": True,
                             "detailed": True, "rename": "Warpempfaenger_Herz",
                             "computer": {"position": vec(p.at(H, -17, 3)), "rotation": vec([0, p.facing(H, p.at(H, -17, 3)), 0], 1), "alignRadial": True}})
    pool = p.at(H, 11, 10)
    b.prop("remotes", {"id": "ZEKSCHLEIER_REMOTE_HERZ", "decalPath": "planets/assets/decals/herz.png",
                       "platform": {"position": vec(pool), "rotation": vec([0, p.facing(H, pool), 0], 1), "alignRadial": True,
                                    "rename": "Projektionsbecken_Herz", "reveals": "ZEKSCHLEIER_HERZ_GESEHEN"}})
    for i, (e, n) in enumerate(p.ring(H, 28, 5, 54)):
        b.detail("lamp_flare", p.at(H, e, n), 0, 1.0, f"Herzlampe_{i + 1}")
    b.vol("revealVolumes", reveal(p.at(H, up=6), 28, ["ZEKSCHLEIER_HERZ_FOUND"]))
    b.prop("signals", {"frequency": "Schleier-Echo", "name": "Herz des Bruchs", "audio": "NomaiRecorderAmbient_LP", "position": vec(p.at(H, up=4)),
                       "sourceRadius": 6, "detectionRadius": 0, "identificationRadius": 40})
    # ---- volcanoes far away from all sites ----
    volcanoes = []
    for lat, lon in [(55, -40), (-48, -70), (5, -95), (-60, 160)]:
        pos = direction(lat, lon) * (p.sample(direction(lat, lon)) - 1)
        volcanoes.append({"position": vec(pos), "alignRadial": True, "minInterval": 6, "maxInterval": 16, "minLaunchSpeed": 40, "maxLaunchSpeed": 70,
                          "lavaTint": color(255, 120, 40), "stoneTint": color(70, 50, 70)})
    b.props["volcanoes"] = volcanoes
    b.prop("entryLocation", {"id": "ZEKSCHLEIER_BRUCH", "position": vec(p.at(S, up=4))})
    b.prop("entryLocation", {"id": "ZEKSCHLEIER_SPLITTERFELD", "position": vec(p.at(F, up=4))})
    b.prop("entryLocation", {"id": "ZEKSCHLEIER_HERZ", "position": vec(p.at(H, up=4))})
    b.vol("revealVolumes", reveal(p.at(S, up=6), 60, ["ZEKSCHLEIER_BRUCH_FOUND"]))

    cfg = body_header("Schleierbruch")
    cfg.update({
        "Base": {"surfaceSize": 335, "surfaceGravity": 4, "gravityFallOff": "linear"},
        "Orbit": {"primaryBody": "Schleierstern", "semiMajorAxis": 10400, "eccentricity": 0.2, "inclination": 7, "longitudeOfAscendingNode": 250,
                  "trueAnomaly": 275, "siderealPeriod": 4, "axialTilt": 22, "tint": color(200, 120, 255)},
        "Atmosphere": {"size": 430, "atmosphereTint": color(155, 100, 175), "atmosphereSunIntensity": 0.8, "useAtmosphereShader": True, "hasOxygen": False},
        "HeightMap": heightmap_module(p, has_em, 0.06, 0.1, color(255, 150, 90)),
        "AmbientLights": [{"position": vec(p.at(H, up=10)), "intensity": 1.2, "tint": color(170, 120, 255), "innerRadius": 25, "outerRadius": 95}],
        "MapMarker": {"enabled": True},
        "ShipLog": ship_log("bruch", "Schleierbruch.xml", "bruch"),
        "Props": {
            "details": b.details,
            "translatorText": b.texts,
            "scatter": [
                {"path": P["vase_broken"], "count": 16, "seed": 3301, "minHeight": 318, "maxHeight": 336, "scale": 1.0, "preventOverlap": True},
                {"path": P["crystal_cracked"], "count": 22, "seed": 3302, "minHeight": 290, "maxHeight": 320, "scale": 1.3, "preventOverlap": True},
                {"path": P["ice_lump"], "count": 18, "seed": 3303, "minHeight": 300, "maxHeight": 334, "scale": 1.0, "preventOverlap": True},
            ],
            **b.props,
        },
        "Volumes": b.volumes,
    })
    return cfg


def star_config():
    cfg = body_header("Schleierstern")
    spawn = [0, 2600, 9300]
    cfg.update({
        "Base": {"centerOfSolarSystem": True, "surfaceSize": 2000, "surfaceGravity": 60, "gravityFallOff": "inverseSquared"},
        "Star": {"size": 2000, "solarLuminosity": 1.05, "tint": color(220, 228, 255), "lightTint": color(200, 215, 255),
                 "stellarDeathType": "none", "stellarRemnantType": "none"},
        "Spawn": {"shipSpawnPoints": [{"id": "ZEKSCHLEIER_WARP_ANKUNFT", "isDefault": True, "position": vec(spawn),
                                       "rotation": vec([math.degrees(math.atan2(2600, 9300)), 180, 0], 2), "rename": "Warp-Ankunft"}]},
        "ShipLog": {"xmlFile": "planets/shiplogs/Schleierstern.xml", "spriteFolder": "planets/assets/shiplog/entries"},
        "Volumes": {"notificationVolumes": [{"position": vec(spawn), "radius": 400, "target": "all",
                                             "entryNotification": {"displayMessage": "DER SCHLEIER HÄLT DEIN SCHIFF FEST", "duration": 6}}]},
    })
    return cfg


def moon_config(p, has_em):
    b = Body(p)
    A = "absturz"
    probe = p.at(A, 0, 0, 0.6)
    b.detail("transponder", probe, 35, 2.2, "Sonde_Elf", pitch=24, roll=8)
    b.detail("light_beam", p.at(A, 0, 0, 1.5), 0, 1.2, "Sonde_Leuchtfeuer", keepLoaded=True)
    b.detail("box_broken", p.at(A, 5, 3), 80, 1.0, "Sondentruemmer_1")
    b.detail("platform_broken", p.at(A, -6, 6, -0.3), 200, 0.6, "Sondentruemmer_2", pitch=12)
    b.text("recorder", "Sonde_Aufzeichnung.xml", p.at(A, 3, -3), 0, "Beschaedigter_Nomai_Recorder")
    b.text("scroll", "Sonde_Protokoll.xml", p.at(A, -3.5, -2.5, 0.2), 60, "Schriftrolle_Startprotokoll")
    b.prop("signals", {"frequency": "Schleier-Echo", "name": "Nomai-Sonde", "audio": "NomaiEscapePodDistressSignal_LP", "position": vec(p.at(A, up=3)),
                       "sourceRadius": 2, "detectionRadius": 1500, "identificationRadius": 180, "reveals": "ZEKSCHLEIER_ECHO_RUMOR"})
    b.vol("revealVolumes", reveal(p.at(A, up=3), 22, ["ZEKSCHLEIER_SONDE"]))
    b.vol("revealVolumes", reveal([0, 0, 0], 90, ["ZEKSCHLEIER_ECHO_RUMOR"], "observe", maxDistance=3500, maxAngle=25))
    b.prop("entryLocation", {"id": "ZEKSCHLEIER_SIGNAL", "position": vec(p.at(A, up=3))})
    cfg = body_header("Schleiersignal", "SolarSystem")
    cfg.update({
        "canShowOnTitle": False,
        "Base": {"surfaceSize": 72, "surfaceGravity": 3, "gravityFallOff": "linear"},
        "Orbit": {"primaryBody": "TIMBER_HEARTH", "isMoon": True, "semiMajorAxis": 2100, "eccentricity": 0, "inclination": 18,
                  "longitudeOfAscendingNode": 60, "trueAnomaly": 120, "siderealPeriod": 6, "tint": color(190, 160, 255)},
        "HeightMap": heightmap_module(p, has_em, 0.02),
        "MapMarker": {"enabled": True},
        "ShipLog": {"xmlFile": "planets/shiplogs/Schleiersignal.xml", "spriteFolder": "planets/assets/shiplog/entries"},
        "Props": {"details": b.details, "translatorText": b.texts, **b.props},
        "Volumes": b.volumes,
    })
    return cfg


# ============================================================================================
# 5) STAR SYSTEMS
# ============================================================================================
VIOLET = (color(150, 110, 255), color(205, 180, 255))
GOLD = (color(220, 160, 60), color(255, 215, 130))


def curiosity(cid, pair):
    return {"id": cid, "color": pair[0], "highlightColor": pair[1]}


def system_configs():
    entries = {
        "ZEKSCHLEIER_SYSTEM": (0, 300), "ZEKSCHLEIER_KOORDINATEN": (0, 720),
        "ZEKSCHLEIER_KERN": (-760, 480), "ZEKSCHLEIER_KERN_WACHE": (-1180, 760), "ZEKSCHLEIER_KERN_RESONANZFELD": (-1220, 300),
        "ZEKSCHLEIER_HERZ": (760, 480),
        "ZEKSCHLEIER_EXPEDITION": (0, -420), "ZEKSCHLEIER_SEE": (-680, -360), "ZEKSCHLEIER_SEE_INSEL": (-1100, -640),
        "ZEKSCHLEIER_BRUCH": (680, -360), "ZEKSCHLEIER_SPLITTERFELD": (1100, -640),
    }
    system = {
        "$schema": NH + "star_system_schema.json",
        "name": SYSTEM,
        "canEnterViaWarpDrive": True,
        "factRequiredForWarp": "ZEKSCHLEIER_WARP_UNLOCKED",
        "canExitViaWarpDrive": True,
        "factRequiredToExitViaWarpDrive": "ZEKSCHLEIER_FINALE",
        "warpDriveSpawnPointID": "ZEKSCHLEIER_WARP_ANKUNFT",
        "destroyStockPlanets": True,
        "enableTimeLoop": False,
        "respawnHere": False,
        "mapRestricted": False,
        "farClipPlaneOverride": 50000,
        "shipLogStartingPlanetID": "SCHLEIERSEE",
        "StarChart": {"position": {"x": 7, "y": -5}, "color": color(170, 140, 255)},
        "GlobalMusic": {"travelAudio": "TravelerNomai"},
        "Vessel": {
            "coords": COORDS,
            "vesselSpawn": {"position": vec([-6500, -3200, -15500])},
        },
        "initialReveal": ["ZEKSCHLEIER_ANKUNFT"],
        "curiosities": [curiosity("ZEKSCHLEIER_SYSTEM", VIOLET), curiosity("ZEKSCHLEIER_EXPEDITION", GOLD)],
        "entryPositions": [{"id": k, "position": {"x": v[0], "y": v[1]}} for k, v in entries.items()],
        "conditionalChecks": [
            {"check": {"allFactsRevealed": ["ZEKSCHLEIER_FINALE"]},
             "then": {"setPersistentConditions": ["ZEKSCHLEIER_SCHLEIER_GEHOBEN"]}},
            {"check": {"allPersistentConditionsSet": ["ZEKSCHLEIER_SCHLEIER_GEHOBEN"]},
             "then": {"revealFacts": ["ZEKSCHLEIER_KERN_LICHT"]}},
        ],
    }
    solar = {
        "$schema": NH + "star_system_schema.json",
        "curiosities": [curiosity("ZEKSCHLEIER_SIGNAL", VIOLET)],
        "entryPositions": [{"id": "ZEKSCHLEIER_SIGNAL", "position": {"x": 1650, "y": -350}}],
    }
    return system, solar


# ============================================================================================
def main():
    kern, see, bruch, moon = build_kern(), build_see(), build_bruch(), build_moon()
    em = {p.key: textures(p, p.key) for p in (kern, see, bruch, moon)}

    write_json("planets/Schleierstern.json", star_config())
    write_json("planets/Schleierkern.json", kern_config(kern, em["kern"]))
    write_json("planets/Schleiersee.json", see_config(see, em["see"]))
    write_json("planets/Schleierbruch.json", bruch_config(bruch, em["bruch"]))
    write_json("planets/Schleiersignal.json", moon_config(moon, em["signal"]))
    system, solar = system_configs()
    write_json(f"systems/{SYSTEM}.json", system)
    write_json("systems/SolarSystem.json", solar)

    # ship log: map mode sprites
    for p, glow in ((kern, (90, 140, 255)), (see, (90, 200, 230)), (bruch, (200, 110, 255)), (moon, (200, 180, 255))):
        img = render_planet(p, 256, glow=glow)
        save(img, f"planets/assets/shiplog/map/{p.key}.png")
        outline = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(outline).ellipse([3, 3, 252, 252], outline=(255, 255, 255, 255), width=5)
        save(outline, f"planets/assets/shiplog/map/{p.key}_outline.png")

    # ship log: entry photos
    def photo(p, lat, lon, zoom, seed, glow=None):
        img = starfield(512, seed)
        img.alpha_composite(render_planet(p, 512, view_lat=lat, view_lon=lon, zoom=zoom, glow=glow))
        return img
    E = "planets/assets/shiplog/entries/"
    k, s, b, m = kern.sites, see.sites, bruch.sites, moon.sites
    save(photo(kern, k["observatorium"].lat, k["observatorium"].lon, 1.05, 1, (90, 140, 255)), E + "ZEKSCHLEIER_KERN.png")
    save(nomai_art(2, "beam"), E + "ZEKSCHLEIER_KERN_WACHE.png")
    save(nomai_art(3, "crystal"), E + "ZEKSCHLEIER_KERN_RESONANZFELD.png")
    save(photo(see, s["archiv"].lat, s["archiv"].lon, 1.05, 4, (90, 200, 230)), E + "ZEKSCHLEIER_SEE.png")
    save(nomai_art(5, "children"), E + "ZEKSCHLEIER_SEE_INSEL.png")
    save(photo(bruch, b["signalturm"].lat, b["signalturm"].lon, 1.05, 6, (200, 110, 255)), E + "ZEKSCHLEIER_BRUCH.png")
    save(nomai_art(7, "shards"), E + "ZEKSCHLEIER_SPLITTERFELD.png")
    save(nomai_art(8, "eye"), E + "ZEKSCHLEIER_HERZ.png")
    save(nomai_art(9, "veil"), E + "ZEKSCHLEIER_SYSTEM.png")
    save(nomai_art(10, "clan"), E + "ZEKSCHLEIER_EXPEDITION.png")
    save(coordinates_image(), E + "ZEKSCHLEIER_KOORDINATEN.png")
    save(nomai_art(11, "probe"), E + "ZEKSCHLEIER_SIGNAL.png")

    for sym in ("kern", "see", "bruch", "herz"):
        save(decal(sym), f"planets/assets/decals/{sym}.png")

    # site report for the README / debugging
    for p in (kern, see, bruch, moon):
        for st in p.sites.values():
            print(f"{p.name:15s} {st.name:14s} lat {st.lat:6.1f} lon {st.lon:7.1f} radius {p.radius_of(st.level):7.2f} m")


if __name__ == "__main__":
    main()
