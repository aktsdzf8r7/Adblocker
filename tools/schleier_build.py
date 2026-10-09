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
    # ---- buildings and large structures (paths used by published NH addons) ----
    "shrine": "QuantumMoon_Body/Sector_QuantumMoon/QuantumShrine/Structure_NOM_QuantumShrine",
    "arch": "CaveTwin_Body/Sector_CaveTwin/Sector_SouthHemisphere/Sector_SouthSurface/Sector_WarpReceiver/Geometry_WarpReceiver/OtherComponentsGroup/Prefab_NOM_Arch_B",
    "stairs_l": "BrittleHollow_Body/Sector_BH/Sector Cannon Path/Fragment CannonPath_3/Core_CannonPath_3/Geometry_Core_CannonPath_3/Architecture_CannonPath_3/OtherComponentsGroup/Prefab_NOM_Stairs_Solid_L",
    "stairs_r": "BrittleHollow_Body/Sector_BH/Sector Cannon Path/Fragment CannonPath_3/Core_CannonPath_3/Geometry_Core_CannonPath_3/Architecture_CannonPath_3/OtherComponentsGroup/Prefab_NOM_Stairs_Solid_R",
    "stargazing": "CaveTwin_Body/Sector_CaveTwin/Sector_SouthHemisphere/Sector_SouthSurface/Sector_SouthPole/Interactables_SouthPole/SouthPole_VisibleFromFar/Structure_NOM_StargazingPlatform/StargazingPlatform",
    "cannon_platform": "CaveTwin_Body/Sector_CaveTwin/Sector_SouthHemisphere/Sector_GravityCannon/Geometry_GravityCannon/ControlledByProxy_Arch/Structure_NOM_GravityCannon_HT/Structure_NOM_GravityCannon/Structure_NOM_GravityCannon_LaunchingPlatform",
    "escape_pod": "BrittleHollow_Body/Sector_BH/Sector_EscapePodCrashSite/Sector_CrashFragment/EscapePod_Socket",
    "escape_pod_geo": "DB_EscapePodDimension_Body/Sector_EscapePodDimension/Sector_EscapePodBody/Geometry_EscapePodBody",
    "dead_suit": "Comet_Body/Sector_CO/Sector_CometInterior/Props_CometInterior/Prefab_NOM_Dead_Suit (1)",
    "skeleton_child": "CaveTwin_Body/Sector_CaveTwin/Sector_SouthHemisphere/Sector_SouthUnderground/Sector_FossilCave/Geometry_FossilCave/OtherComponentsGroup/Child Skeletons/Prefab_NOM_Skeleton_Child_Pile_A",
    "opc_module": "OrbitalProbeCannon_Body/Sector_OrbitalProbeCannon/Sector_Module_Broken",
    "nomai_probe": "NomaiProbe_Body/Structure_NOM_Probe_Renderer",
    "sunstation": "SunStation_Body/Sector_SunStation/Geometry_SunStation",
    "statue_head": "SunStation_Body/Sector_SunStation/Sector_ControlModule/Props/OtherComponentsGroup/StatueHead/Prefab_NOM_StatueHead",
    "whs_geo": "WhiteholeStation_Body/Sector_WhiteholeStation/Geometry_WhiteholeStation",
    "vessel_lamp": "DB_VesselDimension_Body/Sector_VesselDimension/Sector_VesselBridge/Interactibles_VesselBridge/UNSORTED/Wall Lamps/Prefab_NOM_Lamp_Glow_Vessel_Wall",
    "warpcore_broken": "CaveTwin_Body/Sector_CaveTwin/Sector_NorthHemisphere/Sector_NorthSurface/Sector_TimeLoopExperiment/WarpCoreWallSockets/WarpCoreSocket/Props_NOM_WarpCoreBroken (1)/Props_NOM_WarpCore_Simple",
    "bramble_seed": "TimberHearth_Body/Sector_TH/Sector_ImpactCrater/Interactables_ImpactCrater/ControlledByProxy_Structures/Terrain_DB_BrambleSphere_Seed_V2",
    "angler": "DB_HubDimension_Body/Sector_HubDimension/Interactables_HubDimension/Anglerfish_Body",
    "wall_lamp": "CaveTwin_Body/Sector_CaveTwin/Sector_SouthHemisphere/Sector_SouthUnderground/Sector_City/Lighting_City/Lights_FossilDistrict/Prefab_NOM_Lamp_Glow_Diamond_Wall",
    "gravity_crystal": "BrittleHollow_Body/Sector_BH/Sector Quantum Pole Path/Fragment QuantumPolePath 2/Interactables_QPP2/Prefab_NOM_GravityCrystal",
}

# Vertical correction per prop (metres along the local up axis). Vanilla props do not all have their pivot
# at the base, so small objects are sunk a few centimetres and large structures a bit more: a prop that is
# slightly embedded looks right, a floating one does not. Tune single values here after testing in game.
GROUND = {
    "default": -0.05,
    "doorway": -0.15, "doorway_fancy": -0.15, "gateway": -0.2, "arch": -0.2,
    "shrine": -0.35, "stargazing": -0.2, "cannon_platform": -0.3, "gravity_cannon": -0.5,
    "escape_pod": -0.9, "escape_pod_geo": -0.6, "crystal_cracked": -0.3, "probe_window": -0.1,
    "transponder": -0.2, "bramble_seed": -1.5, "purple_rock": -0.5, "ice_lump": -0.3,
    "stairs_l": -0.1, "stairs_r": -0.1,
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

    def detail(self, key, pos, yaw=0.0, scale=1.0, rename=None, pitch=0.0, roll=0.0, ground=True, **extra):
        pos = np.asarray(pos, float)
        if ground and key in P and np.linalg.norm(pos) > 1:
            pos = pos + norm(pos) * GROUND.get(key, GROUND["default"]) * max(scale, 1.0)
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


def build_dorn():
    p = Planet("dorn", "Schleierdorn", 230.0, 310.0, 44044)
    d = p.dirs
    roots = p.noise.ridged(d, 5, 3.2)
    base = p.noise.fbm(d, 4, 1.6)
    h = 0.45 + 0.35 * base + 0.45 * roots
    h = (h - np.percentile(h, 0.5)) / (np.percentile(h, 99.5) - np.percentile(h, 0.5))
    h = np.clip(h, 0, 1) * 0.9 + 0.05
    p.add_site(Site("schlund", -12, 60, 70, 55, 125, kind="funnel"))   # crater floor at 252 m
    p.add_site(Site("ruine", 10, 92, 196, 34, 70))                     # 291.5 m, at the rim of the maw
    p.add_site(Site("kapsel1", 30, -58, 190, 40, 85))                  # 289.6 m
    p.finish(h)
    p.roots = roots
    return p


def build_rock(key, name, r_min, r_max, seed, site):
    p = Planet(key, name, r_min, r_max, seed, 512, 256)
    d = p.dirs
    h = 0.55 + 0.35 * p.noise.fbm(d, 5, 2.2) + 0.2 * p.noise.ridged(d, 3, 3.0)
    h = (h - h.min()) / (h.max() - h.min())
    p.add_site(Site(site, 15, 20, 175, 13, 24))
    p.finish(h)
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
    elif kind == "dorn":
        col = ramp(t, [(0, (22, 28, 20)), (0.35, (40, 52, 34)), (0.6, (62, 70, 44)), (0.85, (92, 84, 58)), (1, (120, 110, 84))])
        vines = smoothstep(0.55, 0.85, p.roots)[..., None]
        col = col * (1 - 0.7 * vines) + np.array([96, 74, 48]) * 0.7 * vines
        maw = p.sites["schlund"]
        ang = np.arccos(np.clip(p.dirs @ maw.c, -1, 1)) * p.radius_of(maw.level)
        glow = 1 - smoothstep(maw.r_in * 0.4, maw.r_out, ang)
        em = np.array([140, 100, 220]) * glow[..., None] * 0.6 + np.array([60, 160, 70]) * (smoothstep(0.9, 0.98, p.roots) * 0.35)[..., None]
    elif kind == "wacht":
        col = ramp(t, [(0, (70, 40, 30)), (0.5, (140, 96, 70)), (1, (210, 180, 150))])
        em = np.array([255, 120, 40]) * (smoothstep(0.0, 0.25, 0.3 - t) * 0.5)[..., None]
    else:  # moon and the wreck rock
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
    elif motif in ("vines", "pod_vines"):
        rng = np.random.default_rng(title_seed)
        for k in range(14):
            x0, y0 = rng.uniform(0, size), rng.uniform(0, size)
            pts = [(x0 + 60 * math.sin(t / 3 + k) + t * 9 * math.cos(k), y0 + t * 9 * math.sin(k) + 40 * math.cos(t / 4)) for t in range(40)]
            d.line(pts, fill=(70, 110, 60, 255), width=int(rng.uniform(6, 16)), joint="curve")
            for t in range(4, 40, 6):
                px, py = pts[t]
                d.polygon([(px, py), (px + 10, py - 18), (px + 4, py)], fill=(110, 140, 80, 255))
        for k, col in enumerate([(255, 190, 70), (80, 140, 255), (255, 60, 50)]):
            cx, cy = size * (0.25 + 0.25 * k), size * (0.3 + 0.2 * (k % 2))
            for r, a in ((46, 60), (30, 120), (14, 255)):
                d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col + (a,))
        if motif == "pod_vines":
            d.ellipse([c - 70, c + 20, c + 70, c + 120], fill=(200, 190, 170, 255), outline=(120, 110, 100, 255), width=4)
            d.ellipse([c - 30, c + 45, c + 30, c + 95], fill=(90, 150, 200, 255))
    elif motif == "vessel":
        d.polygon([(c - 190, c + 30), (c - 40, c - 50), (c + 170, c - 40), (c + 200, c + 10), (c + 40, c + 70), (c - 150, c + 70)],
                  fill=(170, 160, 140, 255), outline=(230, 220, 200, 255))
        for k in range(5):
            d.ellipse([c - 120 + k * 60, c - 10, c - 104 + k * 60, c + 6], fill=(120, 230, 220, 255))
        d.ellipse([c + 150, c - 30, c + 210, c + 30], outline=(120, 230, 220, 200), width=5)
        for k in range(6):
            a = k * math.pi / 3
            d.line([(c + 180, c), (c + 180 + 70 * math.cos(a), 70 * math.sin(a) + c)], fill=(60, 110, 60, 180), width=6)
    elif motif == "pod":
        d.ellipse([c - 110, c - 70, c + 110, c + 90], fill=(200, 190, 170, 255), outline=(240, 230, 210, 255), width=5)
        d.ellipse([c - 55, c - 25, c + 55, c + 55], fill=(80, 140, 200, 255))
        d.line([(c + 80, c - 60), (c + 160, c - 150)], fill=(255, 210, 150, 220), width=4)
        for k in range(1, 4):
            d.arc([c + 160 - 25 * k, c - 150 - 25 * k, c + 160 + 25 * k, c - 150 + 25 * k], -100, 10, fill=(255, 200, 120, 255 - 50 * k), width=3)
    elif motif == "camp":
        d.rectangle([c - 90, c + 40, c - 30, c + 90], fill=(170, 150, 120, 255))
        d.rectangle([c - 20, c + 50, c + 40, c + 90], fill=(150, 130, 110, 255))
        for r, a in ((70, 50), (40, 120), (16, 255)):
            d.ellipse([c + 70 - r, c - 20 - r, c + 70 + r, c - 20 + r], fill=(120, 200, 255, a))
        spiral(d, c - 60, c - 60, 50, 1.8, 3, (150, 200, 255, 255))
    elif motif == "angler":
        d.ellipse([c - 200, c - 120, c + 160, c + 140], fill=(40, 30, 40, 255))
        d.polygon([(c - 120, c + 10), (c + 120, c - 40), (c + 120, c + 60)], fill=(10, 8, 10, 255))
        for k in range(9):
            x = c - 100 + k * 26
            d.polygon([(x, c - 10 + k * 3), (x + 10, c + 20), (x + 20, c - 6 + k * 3)], fill=(230, 220, 200, 255))
        d.line([(c - 60, c - 110), (c + 10, c - 200)], fill=(80, 70, 80, 255), width=6)
        for r, a in ((40, 70), (20, 160), (8, 255)):
            d.ellipse([c + 10 - r, c - 200 - r, c + 10 + r, c - 200 + r], fill=(255, 140, 120, a))
    elif motif == "station":
        for r, a in ((260, 40), (200, 70), (150, 255)):
            d.ellipse([c - r - 120, c - r + 140, c + r - 120, c + r + 140], fill=(255, 190, 120, a))
        d.line([(c + 40, c - 200), (c + 140, c + 120)], fill=(200, 190, 170, 255), width=14)
        d.rectangle([c + 60, c - 120, c + 150, c - 60], fill=(190, 180, 160, 255))
        d.ellipse([c + 90, c + 60, c + 190, c + 160], fill=(150, 120, 100, 255))
        spiral(d, c + 100, c - 90, 26, 1.5, 3, (120, 200, 255, 255))
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


def floor_text(b, xml, pos, rename, **extra):
    """Nomai text lying on a flat plaza (NH lays the arcs out in a 5.4 x 3.6 m field - keep 4 m clear)."""
    up = norm(pos)
    return b.text("wall", xml, np.asarray(pos) + up * 0.08, rename=rename, normal=up, **extra)


def house(b, p, site, e, n, name, scale=1.0, angle=0.0):
    """A Nomai building (walls, roof, doorway) from the Quantum Moon shrine, turned towards the plaza."""
    pos = p.at(site, e, n)
    return b.detail("shrine", pos, p.facing(site, pos, angle=angle), scale, name)


def escape_pod(b, pos, yaw, name, pitch=14.0, roll=6.0):
    """Escape pod 1 from Brittle Hollow, without its vanilla computer (our own text stands next to it)."""
    return b.detail("escape_pod", pos, yaw, 1.0, name, pitch=pitch, roll=roll,
                    removeChildren=["Interactibles_EscapePod/Prefab_NOM_Vessel_Computer", "Proxy_EscapePod"])


def remote(b, rid, decal, platform=None, stones=(), reveals=None):
    r = {"id": rid, "decalPath": f"planets/assets/decals/{decal}.png"}
    if platform is not None:
        pos, yaw, name = platform
        r["platform"] = {"position": vec(pos), "rotation": vec([0, yaw, 0], 1), "alignRadial": True, "rename": name}
        if reveals:
            r["platform"]["reveals"] = reveals
    if stones:
        r["stones"] = [{"position": vec(pos), "alignRadial": True, "rename": name} for pos, name in stones]
    b.prop("remotes", r)


def receiver(b, p, site, e, n, freq, name, computer=None):
    pos = p.at(site, e, n)
    r = {"frequency": freq, "position": vec(pos), "rotation": vec([0, p.facing(site, pos), 0], 1), "alignRadial": True, "detailed": True, "rename": name}
    if computer:
        cpos = p.at(site, *computer)
        r["computer"] = {"position": vec(cpos), "rotation": vec([0, p.facing(site, cpos), 0], 1), "alignRadial": True}
    b.prop("warpReceivers", r)


def transmitter(b, p, site, e, n, freq, name):
    pos = p.at(site, e, n)
    b.prop("warpTransmitters", {"frequency": freq, "position": vec(pos), "rotation": vec([0, p.facing(site, pos), 0], 1),
                                "alignRadial": True, "alignmentWindow": 360, "rename": name})


def furnish(b, p, site, items):
    for e, n, k in items:
        pos = p.at(site, e, n)
        b.detail(k, pos, p.facing(site, pos), 1.0)


def kern_config(p, has_em):
    b = Body(p)
    O, R = "observatorium", "resonanzfeld"
    # ---- Spiegelring / Lichtbündler: ring of glowing arches around a glass dish ----
    b.detail("probe_window", p.at(O), 0, 2.2, "Lichtbuendler_Spiegelschale")
    for i, (e, n) in enumerate(p.ring(O, 15, 6, 15)):
        pos = p.at(O, e, n)
        b.detail("doorway_fancy", pos, p.facing(O, pos), 1.6, f"Lichtbuendler_Spiegelbogen_{i + 1}")
    # beam and torches that only burn once the veil is lifted (Tansy's wish)
    b.detail("light_beam", p.at(O, up=1.0), 0, 3.0, "Lichtbuendler_Strahl", ground=False, activationCondition="ZEKSCHLEIER_SCHLEIER_GEHOBEN", keepLoaded=True)
    for i, (e, n) in enumerate(p.ring(O, 9, 6, 45)):
        b.detail("torch", p.at(O, e, n), 0, 1.0, f"Lichtbuendler_Fackel_{i + 1}", activationCondition="ZEKSCHLEIER_SCHLEIER_GEHOBEN")
    # ---- buildings ----
    house(b, p, O, 42, -12, "Tansys_Werkstatt")
    house(b, p, O, -44, 8, "Sternwarte")
    pos = p.at(O, 30, -6)
    b.text("whiteboard", "Kern_Werkstatt.xml", pos, p.facing(O, pos), "Whiteboard_Werkstatt", seed=111)
    # ---- texts on the plaza ----
    floor_text(b, "Kern_Beobachtung.xml", p.at(O, -28, 26), "Bodenschrift_Beobachtung", seed=101, arcInfo=arcs("adult", "adult", "adult", "adult", "child"))
    pos = p.at(O, 28, 20)
    b.text("computer", "Kern_Lichtbuendler.xml", pos, p.facing(O, pos), "Computer_Lichtbuendler")
    # Tansy's last watch: skeleton, recorder, a dry tree
    tansy = p.at(O, 22, -34)
    b.detail("skeleton", tansy, p.facing(O, tansy), 1.0, "Tansy")
    b.text("recorder", "Kern_Tansy.xml", p.at(O, 24.5, -31), 0, "Recorder_Tansy")
    b.detail("dry_tree", p.at(O, 18, -38), 40, 1.0, "Tansys_Baum")
    b.detail("staff", p.at(O, 20, -30, 0.1), 0, 1.0, "Tansys_Stab", pitch=85)
    # projection pool + stones to the archive and the signal tower
    pool = p.at(O, -36, -18)
    remote(b, "ZEKSCHLEIER_REMOTE_KERN", "kern", platform=(pool, p.facing(O, pool), "Projektionsbecken_Kern"))
    remote(b, "ZEKSCHLEIER_REMOTE_SEE", "see", stones=[(p.at(O, -27, -24, 0.15), "Projektionsstein_See")])
    remote(b, "ZEKSCHLEIER_REMOTE_BRUCH", "bruch", stones=[(p.at(O, -25, -21, 0.15), "Projektionsstein_Bruch")])
    # warps: observatory -> archive; receiver for the signal tower
    transmitter(b, p, O, 0, 40, "ZEKSCHLEIER_KERN_SEE", "Warp_zum_Archiv")
    receiver(b, p, O, 0, -40, "ZEKSCHLEIER_BRUCH_KERN", "Warpempfaenger_Observatorium", computer=(13, -46))
    for i, (e, n) in enumerate([(-50, 22), (50, 22), (-26, -50), (27, -50), (52, -32), (-50, -36)]):
        pos = p.at(O, e, n)
        b.detail("doorway", pos, p.facing(O, pos), 1.0, f"Leuchtbogen_{i + 1}")
    furnish(b, p, O, [(-16, 34, "vase_thick"), (-13, 36, "vase_thin"), (20, 30, "potted_tree"), (40, 12, "treepot"),
                      (6, -24, "bench"), (10, -22, "bench"), (-14, -34, "table"), (-11, -37, "container"), (-6, 36, "box")])
    # ---- ridge cairn on the way up ----
    b.text("cairnCT", "Kern_Wegweiser.xml", p.at("grat"), 0, "Steinmaennchen_Grat")
    # ---- resonance field: giant cracked crystals, and the warp up to the sun watch ----
    for i, (e, n, s, yw) in enumerate([(0, 0, 4.5, 0), (14, 6, 3.0, 50), (-12, 9, 3.4, 120), (6, -15, 2.6, 200), (-16, -10, 2.2, 290), (24, -8, 2.0, 30)]):
        b.detail("crystal_cracked", p.at(R, e, n), yw, s, "Strahlungsresonator" if i == 0 else f"Resonanzkristall_{i}")
    b.text("trailmarker", "Kern_Resonator.xml", p.at(R, -4, 22), 0, "Wegmarke_Yarrow")
    b.detail("toys", p.at(R, -2, 25), 10, 1.0, "Yarrows_Spielzeug")
    transmitter(b, p, R, 2, -28, "ZEKSCHLEIER_KERN_WACHT", "Warp_zur_Sonnenwacht")
    pos = p.at(R, 2, -18)
    b.detail("arch", pos, p.facing(R, pos), 1.0, "Bogen_Sonnenwacht")
    b.prop("signals", {"frequency": "Quantum", "name": "Resonanzkristall", "audio": "NomaiGravCrystalFlickerAmbient_LP",
                       "position": vec(p.at(R, 0, 0, 4)), "sourceRadius": 3, "detectionRadius": 400, "identificationRadius": 40})
    # ---- volumes / entry locations ----
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
    A, U, Y = "archiv", "ufer", "yarrow"
    # ---- the settlement: houses, gate, ring of arches ----
    b.detail("gateway", p.at(A, 0, -60), p.facing(A, p.at(A, 0, -60)), 1.0, "Tor_der_Siedlung")
    house(b, p, A, 0, 48, "Sorrels_Archivhaus", 1.2)
    house(b, p, A, -46, 26, "Wohnhaus_West")
    house(b, p, A, 46, 26, "Wohnhaus_Ost")
    for i, (e, n) in enumerate(p.ring(A, 56, 9, 200)):
        if n > 10:
            continue
        pos = p.at(A, e, n)
        b.detail("doorway", pos, p.facing(A, pos), 1.2, f"Siedlungsbogen_{i + 1}")
    # archive core: shelves, computer, the story of the two clans
    for i, (e, n) in enumerate([(-14, 10), (-10, 14), (-6, 17), (6, 17), (10, 14), (14, 10)]):
        pos = p.at(A, e, n)
        b.detail("shelf", pos, p.facing(A, pos), 1.0, f"Archivregal_{i + 1}")
    pos = p.at(A, 0, 12)
    b.text("computer", "See_Archiv.xml", pos, p.facing(A, pos), "Computer_Archiv")
    pos = p.at(A, 0, 26)
    b.text("whiteboard", "See_Geschwister.xml", pos, p.facing(A, pos), "Whiteboard_Geschwister", seed=203)
    floor_text(b, "See_Ankunft.xml", p.at(A, -26, -12), "Bodenschrift_Ankunft", seed=202, arcInfo=arcs("adult", "adult", "adult", "adult", "child"))
    # escape pod 2 at the edge of the plateau
    pod = p.at(A, -50, -38)
    escape_pod(b, pod, p.facing(A, pod, angle=90), "Kapsel_2")
    pos = p.at(A, -36, -30)
    b.text("whiteboard", "See_Kapsel.xml", pos, p.facing(A, pos), "Whiteboard_Kapsel", seed=204)
    # gardens, everyday things
    furnish(b, p, A, [(-36, 4, "potted_tree"), (-38, -2, "potted_tree2"), (36, 2, "potted_tree"), (38, -6, "potted_tree2"),
                      (-20, -40, "bench"), (-16, -42, "bench"), (20, -34, "table"), (24, -30, "bowl"), (16, -38, "vase_thick"),
                      (-30, 22, "vase_thin"), (30, 22, "vase_thick"), (0, -26, "treepot"), (-44, -16, "box"), (46, -20, "container")])
    for i, (e, n) in enumerate(p.ring(A, 24, 6, 0)):
        b.detail("torch", p.at(A, e, n), 0, 1.0, f"Archivfackel_{i + 1}", activationCondition="ZEKSCHLEIER_SCHLEIER_GEHOBEN")
    pool = p.at(A, 28, -12)
    remote(b, "ZEKSCHLEIER_REMOTE_SEE", "see", platform=(pool, p.facing(A, pool), "Projektionsbecken_Archiv"))
    remote(b, "ZEKSCHLEIER_REMOTE_KERN", "kern", stones=[(p.at(A, 19, -18, 0.15), "Projektionsstein_Kern")])
    remote(b, "ZEKSCHLEIER_REMOTE_HERZ", "herz", stones=[(p.at(A, 21, -21, 0.15), "Projektionsstein_Herz")])
    receiver(b, p, A, -8, -46, "ZEKSCHLEIER_KERN_SEE", "Warpempfaenger_Observatorium", computer=(4, -48))
    receiver(b, p, A, 22, -50, "ZEKSCHLEIER_DORN_SEE", "Warpempfaenger_Dorn")
    # ---- lower shore: the warp into the heart and Ilex' message ----
    transmitter(b, p, U, 0, 0, "ZEKSCHLEIER_SEE_HERZ", "Warp_zum_Herz")
    for i, (e, n) in enumerate(p.ring(U, 10, 4, 45)):
        b.detail("lamp_flare", p.at(U, e, n), 0, 1.0, f"Uferlampe_{i + 1}")
    b.detail("eye_symbol", p.at(U, -16, 0, 0.1), p.facing(U, p.at(U, -16, 0)), 1.5, "Augensymbol_Ufer")
    floor_text(b, "See_Augenlid.xml", p.at(U, 4, 17), "Bodenschrift_Augenlid", seed=303)
    # ---- Yarrow's island ----
    floor_text(b, "See_Kinder.xml", p.at(Y, 0, 0), "Bodenschrift_Kinder", seed=404, arcInfo=arcs("child", "child", "child", "child", "child"))
    b.text("cairnTH", "See_Steinturm.xml", p.at(Y, 9, 6), 0, "Yarrows_Steinturm")
    b.detail("toys", p.at(Y, -7, 5), 0, 1.0, "Spielzeug_1")
    b.detail("toys", p.at(Y, 7, -7), 140, 1.0, "Spielzeug_2")
    b.detail("bowl", p.at(Y, -9, -5), 0, 1.0, "Schale")
    b.detail("potted_tree2", p.at(Y, 13, -10), 0, 1.0, "Inselbaum")
    # ---- epilogue: text that only becomes observable once the veil lifts ----
    epilog = p.at(A, 0, -4)
    b.detail("", epilog, 0, 1.0, "Epilog", ground=False, activationCondition="ZEKSCHLEIER_SCHLEIER_GEHOBEN")
    b.details[-1].pop("path")  # no path: NH creates an empty object that the epilogue text hangs off
    # NH reads `normal` in planet space even for parented text, so it is the radial direction here
    b.text("wall", "See_Epilog.xml", [0, 0.12, 0], rename="Bodenschrift_Epilog", seed=505, parentPath="Sector/Epilog", isRelativeToParent=True,
           arcInfo=arcs("adult", "adult", "adult", "child"), normal=norm(epilog))
    # ---- volumes ----
    b.vol("revealVolumes", reveal(p.at(A, up=6), 75, ["ZEKSCHLEIER_SEE_FOUND"]))
    b.vol("revealVolumes", reveal(pod, 10, ["ZEKSCHLEIER_KAPSEL2_FOUND"]))
    b.prop("entryLocation", {"id": "ZEKSCHLEIER_SEE", "position": vec(p.at(A, up=4))})
    b.prop("entryLocation", {"id": "ZEKSCHLEIER_SEE_INSEL", "position": vec(p.at(Y, up=3))})
    b.prop("entryLocation", {"id": "ZEKSCHLEIER_KAPSEL2", "position": vec(pod)})
    b.prop("entryLocation", {"id": "ZEKSCHLEIER_KOORDINATEN", "position": vec(p.at(A, 0, -4, 2))})

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
    # ---- signal tower: transmitter in the centre, the probe launcher and Borago's workshop ----
    b.detail("transponder", p.at(S), 0, 4.0, "Signalturm_Sender")
    b.detail("light_beam", p.at(S, 0, 0, 2), 0, 1.5, "Signalturm_Strahl", ground=False, activationCondition="ZEKSCHLEIER_SCHLEIER_GEHOBEN", keepLoaded=True)
    b.prop("signals", {"frequency": "Schleier-Echo", "name": "Signalturm", "audio": "NomaiEscapePodDistressSignal_LP",
                       "position": vec(p.at(S, 0, 0, 6)), "sourceRadius": 4, "detectionRadius": 6000, "identificationRadius": 120,
                       "reveals": "ZEKSCHLEIER_BRUCH_FOUND"})
    cannon = p.at(S, 4, 34)
    b.detail("gravity_cannon", cannon, p.facing(S, cannon, toward=False), 1.0, "Sondenkatapult")
    house(b, p, S, -40, 6, "Boragos_Werkstatt")
    floor_text(b, "Bruch_Signalturm.xml", p.at(S, 16, -18), "Bodenschrift_Sonden", seed=606)
    floor_text(b, "Bruch_Abschied.xml", p.at(S, -10, -30), "Bodenschrift_Abschied", seed=707)
    furnish(b, p, S, [(30, 4, "box_broken"), (32, 8, "box"), (28, 10, "container"), (-30, -10, "platform_broken"),
                      (-34, -20, "vase_broken"), (12, -38, "bench")])
    for i, ang in enumerate((200, 235, 270, 300, 340)):
        pos = p.at(S, 48 * math.cos(math.radians(ang)), 48 * math.sin(math.radians(ang)))
        b.detail("doorway", pos, p.facing(S, pos), 1.0, f"Turmbogen_{i + 1}")
    pool = p.at(S, 32, -26)
    remote(b, "ZEKSCHLEIER_REMOTE_BRUCH", "bruch", platform=(pool, p.facing(S, pool), "Projektionsbecken_Signalturm"))
    remote(b, "ZEKSCHLEIER_REMOTE_SEE", "see", stones=[(p.at(S, 24, -32, 0.15), "Projektionsstein_See_2")])
    transmitter(b, p, S, -34, 24, "ZEKSCHLEIER_BRUCH_KERN", "Warp_zum_Observatorium")
    # ---- shard field: quantum shards that wander when nobody looks ----
    sockets = []
    for i, (e, n) in enumerate([(0, 0), (16, 8), (-14, 12), (8, -18), (-20, -8), (26, -10), (-4, 26), (-28, 16)]):
        sockets.append({"position": vec(p.at(F, e, n)), "rotation": vec([0, (i * 47) % 360, 0], 1), "alignRadial": True, "probability": 1})
    b.prop("socketQuantumGroups", {"rename": "Wandernde_Splitter", "sockets": sockets, "details": [
        {"path": P["crystal_cracked"], "rename": f"Splitter_{k + 1}", "scale": 2.4, "keepLoaded": True, "alignWithGravity": True} for k in range(4)]})
    b.text("trailmarker", "Bruch_Splitter.xml", p.at(F, 6, -34), 0, "Wegmarke_Splitter")
    b.prop("signals", {"frequency": "Quantum", "name": "Wandernde Splitter", "audio": "QuantumAmbience_LP", "position": vec(p.at(F, 0, 0, 3)),
                       "sourceRadius": 30, "detectionRadius": 500, "identificationRadius": 60})
    b.vol("revealVolumes", reveal(p.at(F, up=4), 30, ["ZEKSCHLEIER_SPLITTER_GESEHEN"], "observe", maxDistance=90, maxAngle=50))
    # ---- the maw and the heart at its floor ----
    hs = p.sites[H]
    rim = norm(hs.c * p.radius_of(hs.level) + hs.north * 170)
    rim = rim * p.sample(rim)
    b.text("cairnBH", "Bruch_Warnung.xml", rim, p.facing(H, rim), "Steinmaennchen_Schlund")
    b.vol("revealVolumes", reveal(p.at(H, up=20), 60, ["ZEKSCHLEIER_SCHLUND"], "observe", maxDistance=320, maxAngle=35))
    b.detail("crystal_cracked", p.at(H), 0, 9.0, "Herzsplitter")
    for i, (e, n) in enumerate(p.ring(H, 25, 5, 18)):
        pos = p.at(H, e, n)
        b.detail("doorway_fancy", pos, p.facing(H, pos), 1.3, f"Herzbogen_{i + 1}")
    ilex = p.at(H, 0, -8)
    b.detail("bench_skeleton", ilex, p.facing(H, ilex), 1.0, "Ilex")
    b.text("recorder", "Herz_Ilex.xml", p.at(H, 2.5, -9), 0, "Recorder_Ilex")
    receiver(b, p, H, -10, 11, "ZEKSCHLEIER_SEE_HERZ", "Warpempfaenger_Herz", computer=(-17, 3))
    pool = p.at(H, 11, 10)
    remote(b, "ZEKSCHLEIER_REMOTE_HERZ", "herz", platform=(pool, p.facing(H, pool), "Projektionsbecken_Herz"), reveals="ZEKSCHLEIER_HERZ_GESEHEN")
    for i, (e, n) in enumerate(p.ring(H, 28, 5, 54)):
        b.detail("lamp_flare", p.at(H, e, n), 0, 1.0, f"Herzlampe_{i + 1}")
    b.vol("revealVolumes", reveal(p.at(H, up=6), 28, ["ZEKSCHLEIER_HERZ_FOUND"]))
    b.prop("signals", {"frequency": "Schleier-Echo", "name": "Herz des Bruchs", "audio": "NomaiRecorderAmbient_LP", "position": vec(p.at(H, up=4)),
                       "sourceRadius": 6, "detectionRadius": 0, "identificationRadius": 40})
    # ---- volcanoes far away from all sites ----
    b.props["volcanoes"] = [{"position": vec(direction(lat, lon) * (p.sample(direction(lat, lon)) - 1)), "alignRadial": True, "minInterval": 6, "maxInterval": 16,
                             "minLaunchSpeed": 40, "maxLaunchSpeed": 70, "lavaTint": color(255, 120, 40), "stoneTint": color(70, 50, 70)}
                            for lat, lon in [(55, -40), (-48, -70), (5, -95), (-60, 160)]]
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


def dorn_config(p, has_em):
    b = Body(p)
    K, R, Sch = "kapsel1", "ruine", "schlund"
    # ---- the maw: a bramble node in the crater floor leads into the labyrinth ----
    node_pos = p.at(Sch, up=26)
    b.props.setdefault("_bramble", []).append({"position": vec(node_pos), "rotation": vec([0, 0, 0]), "alignRadial": True, "scale": 1.2,
                                               "linksTo": "ZS_Dornenhalle", "name": "ZS_Dornenschlund",
                                               "fogTint": color(120, 90, 160), "lightTint": color(180, 140, 255)})
    b.vol("revealVolumes", reveal(node_pos, 120, ["ZEKSCHLEIER_DORN_FOUND"], "observe", maxDistance=900, maxAngle=30))
    # ---- crash site of escape pod 1 and the camp of its survivors ----
    pod = p.at(K, 0, 0)
    escape_pod(b, pod, 30, "Kapsel_1", pitch=22, roll=10)
    pos = p.at(K, 9, 6)
    b.text("preCrashComputer", "Dorn_Kapsel1.xml", pos, p.facing(K, pos, pod), "Computer_Kapsel_1")
    pos = p.at(K, -14, 10)
    b.text("whiteboard", "Dorn_Lager.xml", pos, p.facing(K, pos), "Whiteboard_Lager", seed=801)
    house(b, p, K, -24, -16, "Hysops_Unterstand")
    transmitter(b, p, K, 20, -18, "ZEKSCHLEIER_DORN_SEE", "Warp_zum_Archiv")
    furnish(b, p, K, [(14, 12, "box_broken"), (17, 10, "container"), (-6, -20, "warpcore_broken"), (-30, 6, "vase_broken"), (6, -26, "bench")])
    for i, (e, n) in enumerate(p.ring(K, 30, 5, 70)):
        b.detail("lamp_flare", p.at(K, e, n), 0, 1.0, f"Notlicht_{i + 1}")
    b.prop("signals", {"frequency": "EscapePod", "name": "Kapsel 1", "audio": "NomaiEscapePodDistressSignal_LP", "position": vec(p.at(K, up=3)),
                       "sourceRadius": 3, "detectionRadius": 4000, "identificationRadius": 80, "reveals": "ZEKSCHLEIER_KAPSEL1_FOUND"})
    b.vol("revealVolumes", reveal(p.at(K, up=4), 25, ["ZEKSCHLEIER_KAPSEL1_FOUND", "ZEKSCHLEIER_DORN_FOUND"]))
    # ---- Kerria's research station at the rim of the maw ----
    house(b, p, R, 0, 22, "Kerrias_Forschungsstation", 1.2)
    floor_text(b, "Dorn_Forschung.xml", p.at(R, 0, 0), "Bodenschrift_Forschung", seed=802)
    toward_maw = p.at(Sch)
    b.detail("stargazing", p.at(R, -24, -12), p.facing(R, p.at(R, -24, -12), toward_maw), 1.0, "Aussichtsplattform")
    rim = p.at(R, -18, -26)
    b.text("cairnTH", "Dorn_Abschied.xml", rim, p.facing(R, rim, toward_maw), "Steinmaennchen_Kerria")
    for i, (e, n) in enumerate([(-20, 14), (20, 14), (24, -10)]):
        pos = p.at(R, e, n)
        b.detail("arch", pos, p.facing(R, pos), 1.0, f"Ruinenbogen_{i + 1}")
    furnish(b, p, R, [(12, 10, "table"), (15, 12, "box"), (-12, 8, "vase_thick"), (10, -16, "shelf")])
    b.prop("entryLocation", {"id": "ZEKSCHLEIER_DORN", "position": vec(p.at(R, up=3))})
    b.prop("entryLocation", {"id": "ZEKSCHLEIER_KAPSEL1", "position": vec(p.at(K, up=3))})
    b.prop("entryLocation", {"id": "ZEKSCHLEIER_LABYRINTH", "position": vec(node_pos)})

    bramble = b.props.pop("_bramble")
    cfg = body_header("Schleierdorn")
    cfg.update({
        "Base": {"surfaceSize": 270, "surfaceGravity": 8, "gravityFallOff": "linear"},
        "Orbit": {"primaryBody": "Schleierstern", "semiMajorAxis": 15200, "eccentricity": 0.05, "inclination": -6, "longitudeOfAscendingNode": 300,
                  "trueAnomaly": 120, "siderealPeriod": 6, "axialTilt": 30, "tint": color(130, 190, 120)},
        "Atmosphere": {"size": 340, "atmosphereTint": color(90, 120, 90), "atmosphereSunIntensity": 0.6, "useAtmosphereShader": True,
                       "fogTint": color(70, 90, 70, 255), "fogSize": 330, "fogDensity": 0.7, "hasOxygen": False},
        "HeightMap": heightmap_module(p, has_em, 0.1, 0.0, color(150, 255, 160)),
        "AmbientLights": [{"intensity": 0.4, "tint": color(140, 200, 140), "outerRadius": 360, "innerRadius": 270}],
        "MapMarker": {"enabled": True},
        "ShipLog": ship_log("dorn", "Schleierdorn.xml", "dorn"),
        "Bramble": {"nodes": bramble},
        "Props": {
            "details": b.details,
            "translatorText": b.texts,
            "scatter": [
                {"path": P["bramble_seed"], "count": 18, "seed": 4401, "minHeight": 258, "maxHeight": 292, "scale": 1.0, "preventOverlap": True},
                {"path": P["bh_tree"], "count": 34, "seed": 4402, "minHeight": 256, "maxHeight": 294, "scale": 1.4, "preventOverlap": True},
                {"path": P["purple_rock"], "count": 8, "seed": 4403, "minHeight": 250, "maxHeight": 290, "scale": 0.8, "preventOverlap": True},
            ],
            **b.props,
        },
        "Volumes": b.volumes,
    })
    return cfg


def rock_config(p, has_em, name, orbit, xml, map_sprite, build):
    """Small asteroid used as a foundation for a station or a wreck (walkable ground with a known surface)."""
    b = Body(p)
    build(b, p)
    cfg = body_header(name)
    cfg.update({
        "Base": {"surfaceSize": p.hmax, "surfaceGravity": 1.5, "gravityFallOff": "linear"},
        "Orbit": orbit,
        "HeightMap": heightmap_module(p, has_em, 0.05),
        "MapMarker": {"enabled": True},
        "ShipLog": ship_log(p.key, xml, map_sprite),
        "Props": {"details": b.details, "translatorText": b.texts, **b.props},
        "Volumes": b.volumes,
    })
    return cfg


def build_wrack_props(b, p):
    W = "wrack"
    wreck_pos = norm(p.sites[W].c * -1 + p.sites[W].north * 0.4) * (p.hmax + 30)
    b.detail("opc_module", wreck_pos, 0, 1.0, "Sondenkanone_Wrack", ground=False, pitch=35, roll=70, keepLoaded=True,
             removeChildren=["Interactables_Module_Broken"])
    b.detail("nomai_probe", p.at(W, 0, -6, -0.4), 20, 1.0, "Zurueckgeschossene_Sonde", pitch=62)
    pos = p.at(W, 6, 4)
    b.text("computer", "Wrack_Protokoll.xml", pos, p.facing(W, pos), "Computer_Kanone")
    pos = p.at(W, -6, 5)
    b.text("whiteboard", "Wrack_Tafel.xml", pos, p.facing(W, pos), "Whiteboard_Spiegel", seed=901)
    for i, (e, n) in enumerate(p.ring(W, 9, 4, 20)):
        b.detail("lamp_flare", p.at(W, e, n), 0, 1.0, f"Wracklampe_{i + 1}")
    furnish(b, p, W, [(-2, 9, "box_broken"), (3, -10, "platform_broken")])
    b.vol("revealVolumes", reveal(p.at(W, up=3), 14, ["ZEKSCHLEIER_WRACK_FOUND"]))
    b.vol("revealVolumes", reveal([0, 0, 0], 60, ["ZEKSCHLEIER_WRACK_RUMOR"], "observe", maxDistance=3000, maxAngle=20))
    b.prop("entryLocation", {"id": "ZEKSCHLEIER_WRACK", "position": vec(p.at(W, up=3))})


def build_wacht_props(b, p):
    W = "wacht"
    station_pos = norm(p.sites[W].c * -1) * (p.hmax + 45)
    b.detail("sunstation", station_pos, 0, 1.0, "Sonnenwacht_Station", ground=False, pitch=90, keepLoaded=True, removeComponents=True)
    b.detail("statue_head", p.at(W, -6, -4), p.facing(W, p.at(W, -6, -4)), 1.0, "Nomai_Statuenkopf")
    receiver(b, p, W, 0, 0, "ZEKSCHLEIER_KERN_WACHT", "Warpempfaenger_Sonnenwacht", computer=(7, -3))
    pos = p.at(W, 6, 6)
    b.text("computer", "Wacht_Messung.xml", pos, p.facing(W, pos), "Computer_Messreihe")
    b.text("recorder", "Wacht_Ilex.xml", p.at(W, -7, 5), 0, "Recorder_Ilex_Wacht")
    for i, (e, n) in enumerate(p.ring(W, 11, 4, 0)):
        b.detail("lamp_flare", p.at(W, e, n), 0, 1.0, f"Wachtlampe_{i + 1}")
    b.vol("revealVolumes", reveal(p.at(W, up=3), 14, ["ZEKSCHLEIER_WACHT_FOUND"]))
    b.prop("entryLocation", {"id": "ZEKSCHLEIER_WACHT", "position": vec(p.at(W, up=3))})


# ---------------------------------------------------------------------------------- labyrinth
def dimension(name, radius, vines, fog, exit_node, static_pos, nodes=(), details=(), texts=(), signals=(), volumes=()):
    cfg = body_header(name)
    cfg.update({
        "canShowOnTitle": False,
        "Orbit": {"staticPosition": vec(static_pos)},
        "Bramble": {"dimension": {"radius": radius, "vinePrefab": vines, "fogTint": fog, "fogDensity": 4.5, "linksTo": exit_node}},
        "ShipLog": {"mapMode": {"remove": True}},
    })
    if nodes:
        cfg["Bramble"]["nodes"] = list(nodes)
    props = {}
    if details:
        props["details"] = list(details)
    if texts:
        props["translatorText"] = list(texts)
    if signals:
        props["signals"] = list(signals)
    if props:
        cfg["Props"] = props
    if volumes:
        cfg["Volumes"] = {"revealVolumes": list(volumes)}
    return cfg


GOLD_FOG, BLUE_FOG, RED_FOG = color(255, 190, 70), color(80, 140, 255), color(255, 60, 50)


def node(pos, links, name, fog, scale=1.0):
    return {"position": vec(pos), "rotation": vec([0, 0, 0]), "linksTo": links, "name": name, "fogTint": fog, "lightTint": fog, "scale": scale}


def floating(key, pos, rot, name, scale=1.0, **extra):
    d = {"path": P[key], "position": vec(pos), "rotation": vec(rot, 1), "rename": name}
    if scale != 1.0:
        d["scale"] = scale
    d.update(extra)
    return d


def floating_text(kind, xml, pos, rot, name):
    return {"type": kind, "xmlFile": "planets/text/" + xml, "position": vec(pos), "rotation": vec(rot, 1), "rename": name}


def labyrinth_configs():
    halle = dimension(
        "ZS_Dornenhalle", 750, "hub", color(70, 50, 90), "ZS_Dornenschlund", [42000, 6000, 0],
        nodes=[node([260, 120, -180], "ZS_Kapselgrund", "ZS_Knoten_Gold", GOLD_FOG),
               node([-280, 60, 200], "ZS_Rankengarten", "ZS_Knoten_Blau", BLUE_FOG),
               node([60, -300, 220], "ZS_Echokammer", "ZS_Knoten_Rot", RED_FOG)],
        details=[floating("vessel_lamp", [0, -30, 0], [0, 0, 0], "Kerrias_Lampe")],
        texts=[floating_text("trailmarker", "Lab_Halle.xml", [0, -34, 0], [0, 0, 0], "Wegmarke_Farben")],
        volumes=[reveal([0, 0, 0], 600, ["ZEKSCHLEIER_LAB_FOUND"])])
    kapselgrund = dimension(
        "ZS_Kapselgrund", 500, "cluster", color(110, 80, 30), "ZS_Knoten_Gold", [-42000, 6000, 0],
        nodes=[node([-200, -60, 180], "ZS_Laternenkammer", "ZS_Knoten_Laterne", GOLD_FOG, 0.8)],
        details=[floating("escape_pod_geo", [40, 10, -30], [339, 171, 314], "Kapsel_3"),
                 floating("dead_suit", [30, 14, -18], [20, 80, 160], "Melisse")],
        texts=[floating_text("preCrashRecorder", "Lab_Melisse.xml", [34, 12, -22], [0, 40, 0], "Aufzeichnung_Melisse")],
        signals=[{"frequency": "EscapePod", "name": "Kapsel 3", "audio": "NomaiEscapePodDistressSignal_LP", "position": vec([40, 10, -30]),
                  "sourceRadius": 3, "detectionRadius": 2000, "identificationRadius": 60, "reveals": "ZEKSCHLEIER_KAPSEL3_FOUND"}],
        volumes=[reveal([40, 10, -30], 40, ["ZEKSCHLEIER_KAPSEL3_FOUND"])])
    rankengarten = dimension(
        "ZS_Rankengarten", 500, "smallNest", color(40, 60, 110), "ZS_Knoten_Blau", [0, 6000, 42000],
        details=[floating("box", [0, -12, 0], [0, 0, 0], "Kerrias_Kiste"), floating("container", [3, -12, 2], [0, 40, 0], "Kerrias_Behaelter"),
                 floating("vessel_lamp", [-3, -10, 1], [0, 0, 0], "Kerrias_Lagerlicht"), floating("vase_thin", [2, -11, -3], [10, 0, 0], "Kerrias_Vase")],
        texts=[floating_text("recorder", "Lab_Rankengarten.xml", [-1, -11, -2], [0, 0, 0], "Recorder_Kerria_Lager")])
    echokammer = dimension(
        "ZS_Echokammer", 500, "cluster", color(90, 20, 20), "ZS_Knoten_Rot", [0, 6000, -42000],
        details=[floating("angler", [-150, 40, 120], [0, 140, 0], "Blindes_Wesen")],
        texts=[floating_text("recorder", "Lab_Echokammer.xml", [0, -6, 0], [0, 0, 0], "Recorder_Warnung")])
    laternenkammer = dimension(
        "ZS_Laternenkammer", 600, "hub", color(30, 80, 80), "ZS_Knoten_Laterne", [30000, -25000, 30000],
        details=[floating("dead_suit", [26, -60, 18], [0, 210, 30], "Kerria"),
                 floating("vessel_lamp", [22, -62, 14], [0, 0, 0], "Kerrias_letztes_Licht")],
        texts=[floating_text("preCrashComputer", "Lab_Laterne.xml", [30, -64, 10], [0, 220, 0], "Logbuch_Laterne"),
               floating_text("preCrashRecorder", "Lab_Kerria.xml", [24, -63, 20], [0, 200, 0], "Aufzeichnung_Kerria")],
        volumes=[reveal([0, -60, 0], 160, ["ZEKSCHLEIER_LATERNE_FOUND"])])
    return [halle, kapselgrund, rankengarten, echokammer, laternenkammer]


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
    b.detail("transponder", probe, 35, 2.2, "Sonde_Elf", pitch=24, roll=8, ground=False)
    b.detail("light_beam", p.at(A, 0, 0, 1.5), 0, 1.2, "Sonde_Leuchtfeuer", ground=False, keepLoaded=True)
    b.detail("box_broken", p.at(A, 5, 3), 80, 1.0, "Sondentruemmer_1")
    b.detail("platform_broken", p.at(A, -6, 6, -0.3), 200, 0.6, "Sondentruemmer_2", pitch=12)
    b.text("recorder", "Sonde_Aufzeichnung.xml", p.at(A, 3, -3), 0, "Beschaedigter_Nomai_Recorder")
    pos = p.at(A, -5, -4)
    b.text("whiteboard", "Sonde_Protokoll.xml", pos, p.facing(A, pos), "Whiteboard_Startprotokoll", seed=71)
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
TEAL = (color(60, 190, 180), color(140, 255, 240))


def curiosity(cid, pair):
    return {"id": cid, "color": pair[0], "highlightColor": pair[1]}


def system_configs():
    entries = {
        # the veil (violet)
        "ZEKSCHLEIER_SYSTEM": (0, 350), "ZEKSCHLEIER_KOORDINATEN": (0, 760),
        "ZEKSCHLEIER_KERN": (-760, 520), "ZEKSCHLEIER_KERN_WACHE": (-1180, 800), "ZEKSCHLEIER_KERN_RESONANZFELD": (-1220, 360),
        "ZEKSCHLEIER_WACHT": (-420, 940), "ZEKSCHLEIER_HERZ": (760, 520),
        # the clan (gold)
        "ZEKSCHLEIER_EXPEDITION": (0, -250), "ZEKSCHLEIER_SEE": (-700, -200), "ZEKSCHLEIER_KAPSEL2": (-1150, -60), "ZEKSCHLEIER_SEE_INSEL": (-1150, -420),
        "ZEKSCHLEIER_BRUCH": (700, -200), "ZEKSCHLEIER_SPLITTERFELD": (1150, -60), "ZEKSCHLEIER_WRACK": (1150, -420),
        # the lost ship (teal)
        "ZEKSCHLEIER_LATERNE_SCHIFF": (0, -1250), "ZEKSCHLEIER_DORN": (-650, -900), "ZEKSCHLEIER_KAPSEL1": (-1100, -1060),
        "ZEKSCHLEIER_LABYRINTH": (650, -900), "ZEKSCHLEIER_KERRIAS_LAGER": (1100, -760), "ZEKSCHLEIER_KAPSEL3": (1100, -1100),
        "ZEKSCHLEIER_ECHOKAMMER_ENTRY": (650, -1380),
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
            # the clan's ship "Laterne" drifts deep inside the thorn labyrinth - it is still powered
            "coords": COORDS,
            "alwaysPresent": True,
            "promptFact": "ZEKSCHLEIER_LATERNE_KERRIA",
            "vesselSpawn": {"parentBody": "ZS_Laternenkammer", "isRelativeToParent": True, "position": vec([0, -80, 0]), "rotation": vec([0, 30, 0])},
        },
        "initialReveal": ["ZEKSCHLEIER_ANKUNFT"],
        "curiosities": [curiosity("ZEKSCHLEIER_SYSTEM", VIOLET), curiosity("ZEKSCHLEIER_EXPEDITION", GOLD), curiosity("ZEKSCHLEIER_LATERNE_SCHIFF", TEAL)],
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
    kern, see, bruch, moon, dorn = build_kern(), build_see(), build_bruch(), build_moon(), build_dorn()
    wrack = build_rock("wrack", "Kanonenwrack", 26.0, 34.0, 5505, "wrack")
    wacht = build_rock("wacht", "Sonnenwacht", 22.0, 30.0, 6606, "wacht")
    bodies = (kern, see, bruch, moon, dorn, wrack, wacht)
    em = {p.key: textures(p, p.key) for p in bodies}

    write_json("planets/Schleierstern.json", star_config())
    write_json("planets/Schleierkern.json", kern_config(kern, em["kern"]))
    write_json("planets/Schleiersee.json", see_config(see, em["see"]))
    write_json("planets/Schleierbruch.json", bruch_config(bruch, em["bruch"]))
    write_json("planets/Schleierdorn.json", dorn_config(dorn, em["dorn"]))
    write_json("planets/Kanonenwrack.json", rock_config(
        wrack, em["wrack"], "Kanonenwrack",
        {"primaryBody": "Schleierdorn", "isMoon": True, "semiMajorAxis": 1250, "eccentricity": 0.02, "inclination": 25, "trueAnomaly": 40,
         "siderealPeriod": 3, "tint": color(200, 200, 210)},
        "Kanonenwrack.xml", "wrack", build_wrack_props))
    write_json("planets/Sonnenwacht.json", rock_config(
        wacht, em["wacht"], "Sonnenwacht",
        {"primaryBody": "Schleierstern", "semiMajorAxis": 3000, "eccentricity": 0, "inclination": 2, "trueAnomaly": 250,
         "isTidallyLocked": True, "alignmentAxis": vec([-1, 0, 0]), "tint": color(255, 200, 150)},
        "Sonnenwacht.xml", "wacht", build_wacht_props))
    for dim in labyrinth_configs():
        write_json(f"planets/Labyrinth/{dim['name']}.json", dim)
    write_json("planets/Schleiersignal.json", moon_config(moon, em["signal"]))
    system, solar = system_configs()
    write_json(f"systems/{SYSTEM}.json", system)
    write_json("systems/SolarSystem.json", solar)

    # ship log: map mode sprites
    glows = {"kern": (90, 140, 255), "see": (90, 200, 230), "bruch": (200, 110, 255), "signal": (200, 180, 255),
             "dorn": (120, 200, 120), "wrack": (180, 180, 200), "wacht": (255, 170, 90)}
    for p in bodies:
        img = render_planet(p, 256, glow=glows[p.key])
        save(img, f"planets/assets/shiplog/map/{p.key}.png")
        outline = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(outline).ellipse([3, 3, 252, 252], outline=(255, 255, 255, 255), width=5)
        save(outline, f"planets/assets/shiplog/map/{p.key}_outline.png")

    # ship log: entry photos
    def photo(p, site, seed, zoom=1.05):
        st = p.sites[site]
        img = starfield(512, seed)
        img.alpha_composite(render_planet(p, 512, view_lat=st.lat, view_lon=st.lon, zoom=zoom, glow=glows[p.key]))
        return img
    E = "planets/assets/shiplog/entries/"
    for f in os.listdir(os.path.join(MOD, E)) if os.path.isdir(os.path.join(MOD, E)) else []:
        os.remove(os.path.join(MOD, E, f))
    shots = {
        "ZEKSCHLEIER_KERN": photo(kern, "observatorium", 1), "ZEKSCHLEIER_KERN_WACHE": nomai_art(2, "beam"),
        "ZEKSCHLEIER_KERN_RESONANZFELD": nomai_art(3, "crystal"), "ZEKSCHLEIER_SEE": photo(see, "archiv", 4),
        "ZEKSCHLEIER_SEE_INSEL": nomai_art(5, "children"), "ZEKSCHLEIER_BRUCH": photo(bruch, "signalturm", 6),
        "ZEKSCHLEIER_SPLITTERFELD": nomai_art(7, "shards"), "ZEKSCHLEIER_HERZ": nomai_art(8, "eye"),
        "ZEKSCHLEIER_SYSTEM": nomai_art(9, "veil"), "ZEKSCHLEIER_EXPEDITION": nomai_art(10, "clan"),
        "ZEKSCHLEIER_KOORDINATEN": coordinates_image(), "ZEKSCHLEIER_SIGNAL": nomai_art(11, "probe"),
        "ZEKSCHLEIER_DORN": photo(dorn, "schlund", 12), "ZEKSCHLEIER_LABYRINTH": nomai_art(13, "vines"),
        "ZEKSCHLEIER_LATERNE_SCHIFF": nomai_art(14, "vessel"), "ZEKSCHLEIER_KAPSEL1": nomai_art(15, "pod"),
        "ZEKSCHLEIER_KAPSEL2": nomai_art(16, "pod"), "ZEKSCHLEIER_KAPSEL3": nomai_art(17, "pod_vines"),
        "ZEKSCHLEIER_KERRIAS_LAGER": nomai_art(18, "camp"), "ZEKSCHLEIER_ECHOKAMMER_ENTRY": nomai_art(19, "angler"),
        "ZEKSCHLEIER_WRACK": photo(wrack, "wrack", 20, 0.9), "ZEKSCHLEIER_WACHT": nomai_art(21, "station"),
    }
    for entry, img in shots.items():
        save(img, E + entry + ".png")

    for sym in ("kern", "see", "bruch", "herz"):
        save(decal(sym), f"planets/assets/decals/{sym}.png")

    # site report for the README / debugging
    for p in bodies:
        for st in p.sites.values():
            print(f"{p.name:15s} {st.name:14s} lat {st.lat:6.1f} lon {st.lon:7.1f} radius {p.radius_of(st.level):7.2f} m")


if __name__ == "__main__":
    main()
