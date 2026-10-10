# -*- coding: utf-8 -*-
"""
Build script for "Verdornt" (Zeki.Verdornt), a New Horizons mod: a bramble seed crashed on Timber Hearth leads
into Dornenkranz, the overgrown home system of Dark Bramble. Design: docs/superpowers/specs/2026-10-10-verdornt-design.md

Generates the star system, all bodies and dimensions, placements.json for the DLL, pictures and manifests.
Needs assets/models/anchors.json from tools/verdornt_models.py; texts come from verdornt_texts.py and the ship
log from verdornt_shiplog.py.

Usage:  python tools/verdornt_build.py [path/to/Zeki.Verdornt]
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import schleier_build as sb  # noqa: E402
from nh_props import P  # noqa: E402
from schleier_build import NH, color, vec, write_json  # noqa: E402

MOD = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "Zeki.Verdornt"))
sb.MOD = MOD

VERSION = "0.1.0"
SYSTEM = "Verdornt"


GREEN = (color(120, 230, 140), color(200, 255, 200))
BODIES = ("Herzdorn", "Erstling", "Glutdorn", "Nebelranke", "Hohlsamen", "Ausguck", "Fernlager")
# orbits around Herzdorn (spec 2 / plan task 4)
ORBITS = {"Erstling": (4200, 4, 30), "Glutdorn": (6500, 9, 150), "Nebelranke": (9800, 3, 260), "Hohlsamen": (13500, 12, 330)}
AUSGUCK_AT = (0, 9000, 2500)
FERNLAGER_AT = (60000, -4000, 0)


def anchors():
    with open(os.path.join(MOD, "assets", "models", "anchors.json"), encoding="utf-8") as f:
        return json.load(f)


def at(a, up=0.0):
    """Position of an anchor, moved along its normal (or +y) by up."""
    p = a["position"]
    n = a.get("normal", {"x": 0, "y": 1, "z": 0})
    return [p["x"] + n["x"] * up, p["y"] + n["y"] * up, p["z"] + n["z"] * up]


def header(name):
    return sb.body_header(name, SYSTEM)


def herzdorn():
    cfg = header("Herzdorn")
    cfg.update({
        "Base": {"surfaceSize": 1100, "surfaceGravity": 12, "centerOfSolarSystem": True, "gravityFallOff": "inverseSquared", "showMinimap": False},
        # the captive star: dim, warm, its light falls through the gaps of the Blender cage (placements.json)
        "Star": {"size": 650, "tint": color(255, 196, 120), "lightTint": color(255, 214, 160), "solarLuminosity": 0.35,
                 "lightRadius": 60000, "supernovaTint": color(200, 255, 190)},
        "Orbit": {"isStatic": True, "showOrbitLine": False},
        "MapMarker": {"enabled": True},
    })
    return cfg


def planet(name, surface, gravity, extra=None):
    a, inc, anomaly = ORBITS[name]
    cfg = header(name)
    cfg.update({
        "Base": {"surfaceSize": surface, "surfaceGravity": gravity, "showMinimap": False},
        "Orbit": {"primaryBody": "Herzdorn", "semiMajorAxis": a, "inclination": inc, "trueAnomaly": anomaly, "eccentricity": 0,
                  "siderealPeriod": 0, "tint": GREEN[0]},
        "MapMarker": {"enabled": True},
    })
    cfg.update(extra or {})
    return cfg


def material_templates():
    """Hidden copies of game props inside Erstling: the DLL takes the bark of the real Dark Bramble vine and the
    hull and copper of real Nomai structures for the Blender models (Models.cs), since Dornenkranz has no stock planets."""
    container = "Sector/VD_Materialvorlagen"
    details = [{"path": "", "position": vec([0, 0, 0]), "rename": "VD_Materialvorlagen", "keepLoaded": True}]
    for name, path in (("Ranke_1", P["db_vine"].format(n=1)), ("Nomai_Tor", P["gateway"]), ("Nomai_Schrein", P["shrine"])):
        details.append({"path": path, "parentPath": container, "isRelativeToParent": True, "position": vec([0, 0, 0]),
                        "rename": name, "keepLoaded": True})
    return details


def erstling(A):
    E = A["erstling"]
    spawn = at(E["ankunft"], 2.0)
    return planet("Erstling", 260, 10, {
        "Spawn": {"playerSpawnPoints": [{"position": vec(spawn), "alignRadial": True, "isDefault": True, "startWithSuit": True}]},
        "Props": {"details": material_templates()},
    })


def nebelranke():
    return planet("Nebelranke", 640, 12, {
        "Base": {"surfaceSize": 640, "surfaceGravity": 12, "groundSize": 120, "showMinimap": False},
        "Atmosphere": {"size": 820, "fogTint": color(70, 160, 90), "fogDensity": 0.55, "fogSize": 820, "useAtmosphereShader": True,
                       "atmosphereTint": color(90, 200, 120), "atmosphereSunIntensity": 0.6},
    })


def ausguck():
    cfg = header("Ausguck")
    cfg.update({
        "Base": {"surfaceSize": 25, "surfaceGravity": 0, "showMinimap": False},
        "Orbit": {"staticPosition": vec(AUSGUCK_AT), "showOrbitLine": False},
        "MapMarker": {"enabled": True},
        # Nomai gravity on the deck, the landing and the lift shaft
        "Volumes": {"forces": {"directionalVolumes": [
            {"position": vec([0, -8, 0]), "force": 9, "normal": vec([0, -1, 0]), "shape": {"type": "cylinder", "radius": 20, "height": 34},
             "rename": "Ausguck_Schwerkraft"}]}},
    })
    return cfg


def fernlager():
    """Where the ship waits during the first journeys (spec 4.6): far out, no marker, out of reach."""
    cfg = header("Fernlager")
    cfg.update({
        "Base": {"surfaceSize": 10, "surfaceGravity": 0, "showMinimap": False},
        "Orbit": {"staticPosition": vec(FERNLAGER_AT), "showOrbitLine": False},
        "MapMarker": {"enabled": False},
        "ShipLog": {"mapMode": {"remove": True}},
        "Spawn": {"shipSpawnPoints": [{"position": vec([0, 0, 0]), "isDefault": True}]},
    })
    return cfg


def placements(A):
    """assets/models/placements.json: where the DLL puts the Blender models (see Models.cs)."""
    props = [
        {"model": "herzdorn_kaefig", "body": "Herzdorn", "collider": True, "spin": 0.4},
        {"model": "erstling", "body": "Erstling", "collider": True},
        {"model": "lager", "body": "Erstling", "collider": True},
        {"model": "glutdorn", "body": "Glutdorn", "collider": True},
        {"model": "nebelranke_ranken", "body": "Nebelranke", "collider": True, "spin": 0.6},
        {"model": "hohlsamen", "body": "Hohlsamen", "collider": True},
        {"model": "ausguck", "body": "Ausguck", "collider": True},
    ]
    for p in props:
        p.setdefault("name", p["model"].capitalize())
        p.setdefault("position", vec([0, 0, 0]))
        p.setdefault("rotation", vec([0, 0, 0]))
        p.setdefault("scale", 1)
    lights = [
        {"name": "Licht_Lager", "body": "Erstling", "position": vec(at(A["lager"]["mitte"], 14)), "color": vec([0.75, 0.9, 1.0]),
         "range": 60, "intensity": 1.4},
        {"name": "Licht_Ausguck", "body": "Ausguck", "position": vec([0, 8, 0]), "color": vec([0.75, 0.9, 1.0]), "range": 45, "intensity": 1.2},
    ]
    return {"props": props, "lights": lights}


def system():
    """systems/Verdornt.json: the system Dornenkranz. Only reachable through the crashed seed (no warp drive in)."""
    return {
        "$schema": NH + "star_system_schema.json",
        "enableTimeLoop": True,
        "loopDuration": 22,
        "canEnterViaWarpDrive": False,
        "canExitViaWarpDrive": True,
        "destroyStockPlanets": True,
        "respawnHere": False,
        "startHere": False,
    }


def manifests():
    write_json("manifest.json", {
        "$schema": "https://raw.githubusercontent.com/ow-mods/owml/master/schemas/manifest_schema.json",
        "filename": "ZekiVerdornt.dll",
        "author": "Zeki",
        "name": "Verdornt",
        "uniqueName": "Zeki.Verdornt",
        "version": VERSION,
        "owmlVersion": "2.15.5",
        "dependencies": ["xen.NewHorizons"],
    })
    write_json("default-config.json", {
        "$schema": "https://raw.githubusercontent.com/ow-mods/owml/master/schemas/config_schema.json",
        "enabled": True,
        "settings": {
            "cinematic": {"type": "toggle", "value": True, "title": "Filmische Übergänge",
                          "tooltip": "Nebel-Übergang beim Durchqueren des Samens."},
        },
    })
    write_json("addon-manifest.json", {
        "$schema": NH + "addon_manifest_schema.json",
        "credits": ["Zeki"],
        "popupMessage": "Verdornt: Zu Beginn der Schleife ist ein riesiger Dornensamen auf Timber Hearth eingeschlagen.",
    })


def main():
    A = anchors()
    manifests()
    write_json(f"systems/{SYSTEM}.json", system())
    write_json("planets/Herzdorn.json", herzdorn())
    write_json("planets/Erstling.json", erstling(A))
    write_json("planets/Glutdorn.json", planet("Glutdorn", 220, 9))
    write_json("planets/Nebelranke.json", nebelranke())
    write_json("planets/Hohlsamen.json", planet("Hohlsamen", 300, 8))
    write_json("planets/Ausguck.json", ausguck())
    write_json("planets/Fernlager.json", fernlager())
    write_json("assets/models/placements.json", placements(A))


if __name__ == "__main__":
    main()
