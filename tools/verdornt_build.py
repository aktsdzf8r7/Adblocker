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
import random
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


TH_SITE = "Sector_TH/VD_Absturzstelle"   # vanilla bodies: details land in their main sector


def bramble_templates(sector="Sector"):
    """Hidden copies of the real Dark Bramble vines and the bramble seed; the DLL clones them along paths (Bramble.cs).
    One set per system: on Erstling, and on Timber Hearth for the Samenschlund."""
    container = sector + "/VD_Rankenvorlagen"
    details = [{"path": "", "position": vec([0, 0, 0]), "rename": "VD_Rankenvorlagen", "keepLoaded": True}]
    details += [{"path": P["db_vine"].format(n=n), "parentPath": container, "isRelativeToParent": True, "position": vec([0, 0, 0]),
                 "rename": f"Ranke_{n}", "keepLoaded": True} for n in range(1, 6)]
    details.append({"path": P["bramble_seed"], "parentPath": container, "isRelativeToParent": True, "position": vec([0, 0, 0]),
                    "rename": "Samen", "keepLoaded": True})
    return details


def unity_direction(lat, lon):
    """A direction like Blender's direction(lat, lon) in tools/verdornt_models.py, converted to Unity (-x, z, -y)."""
    la, lo = math.radians(lat), math.radians(lon)
    x, y, z = math.cos(la) * math.cos(lo), math.cos(la) * math.sin(lo), math.sin(la)
    return [-x, z, -y]


ERSTLING_NODE = unity_direction(-24, 205)   # the planet node into the Eispforte, far from the camp


def vine_paths(seed, radius, count, thick=(4, 9)):
    """Random root paths inside a dimension: from the wall of thorns curling inwards (Unity coordinates)."""
    rnd = random.Random(seed)
    paths = []
    for _ in range(count):
        z = rnd.uniform(-1, 1)
        a = rnd.uniform(0, math.tau)
        d = [math.sqrt(1 - z * z) * math.cos(a), z, math.sqrt(1 - z * z) * math.sin(a)]
        p = [c * radius * 0.92 for c in d]
        heading = [-c for c in d]
        pts = [p]
        for _ in range(rnd.randint(7, 12)):
            heading = [h + rnd.uniform(-0.6, 0.6) for h in heading]
            n = math.sqrt(sum(h * h for h in heading)) or 1
            heading = [h / n for h in heading]
            step = radius * rnd.uniform(0.07, 0.13)
            p = [p[i] + heading[i] * step for i in range(3)]
            if math.sqrt(sum(c * c for c in p)) > radius * 0.95:
                break
            pts.append(p)
        if len(pts) > 2:
            paths.append({"punkte": [vec([round(c, 2) for c in q]) for q in pts], "dicke": round(rnd.uniform(*thick), 2)})
    return paths


def tangent(a, metres):
    """A point beside an anchor on the surface: metres along a direction perpendicular to its normal."""
    n = a["normal"]
    side = [n["z"], 0.0, -n["x"]]
    length = math.hypot(side[0], side[2]) or 1.0
    p = at(a)
    return [p[0] + side[0] / length * metres, p[1], p[2] + side[2] / length * metres]


LAGERKERN = (("Lagerkern_Start", 0, []), ("Lagerkern_Ankunft", 1, ["fact:ZEKIVD_ANKUNFT"]),
             ("Lagerkern_Turm", 2, ["persistent:ZEKIVD_TURM_WACH"]), ("Lagerkern_Kern", 3, ["fact:ZEKIVD_KERN_ERSTLING_GENOMMEN"]))


def lagerkern_texts(L):
    """The reactive core computer of the camp: one NH computer per state at the same spot (ReactiveComputers.cs)."""
    spot = L["computer"]
    return [{"type": "computer", "xmlFile": f"planets/text/{name}.xml", "position": vec(at(spot)), "alignRadial": True,
             "rename": name} for name, _, _ in LAGERKERN]


def computers():
    return [{"body": "Erstling", "name": "Lagerkern",
             "states": [{"object": name, "priority": prio, "conditions": cond} for name, prio, cond in LAGERKERN]}]


def erstling(A):
    E, L = A["erstling"], A["lager"]
    # the player comes to beside the arrival seed, outside its warp sphere
    spawn = tangent(E["ankunft"], 14.0)
    seed = at(E["ankunft"], 3.0)
    home = at(L["ruecksamen"], 0.6)
    return planet("Erstling", 260, 10, {
        "Spawn": {"playerSpawnPoints": [{"position": vec(spawn), "alignRadial": True, "isDefault": True, "startWithSuit": True}]},
        "Bramble": {"nodes": [
            {"position": vec(seed), "alignRadial": True, "linksTo": "Ankunftskammer", "name": "ZEKIVD_Ankunftssamen", "scale": 0.12,
             "fogTint": color(160, 255, 170), "lightTint": color(170, 255, 180)},
            # the great node of Erstling: into the Eispforte
            {"position": vec([c * 285 for c in ERSTLING_NODE]), "alignRadial": True, "linksTo": "Eispforte", "name": "ZEKIVD_Erstling_Knoten",
             "scale": 0.5, "fogTint": color(150, 200, 255), "lightTint": color(170, 210, 255)}]},
        "Props": {"details": material_templates() + bramble_templates() + [
            # the return seed in its copper cradle: the real bramble seed, small
            {"path": P["bramble_seed"], "position": vec(home), "alignRadial": True, "scale": 0.12, "rename": "VD_Ruecksamen"},
            # the planet core of Erstling in the cave behind the gate (an NH item; the Blender model hangs below it)
            {"path": "", "position": vec(at(L["kern"])), "alignRadial": True, "rename": "VD_Kern_Erstling", "keepLoaded": True,
             "item": {"name": "Planetenkern Erstling", "itemType": "Planetenkern", "colliderRadius": 0.6, "interactRange": 3,
                      "pickupFact": "ZEKIVD_KERN_ERSTLING_GENOMMEN", "holdOffset": vec([0, -0.1, 0.25])}},
        ], "translatorText": lagerkern_texts(L),
           "entryLocation": [{"id": "ZEKIVD_LAGER", "position": vec(at(L["mitte"], 6))}, {"id": "ZEKIVD_KERNE", "position": vec(at(L["kern"]))}]},
        "ShipLog": {"xmlFile": "planets/shiplogs/Verdornt.xml", "spriteFolder": "planets/assets/shiplog/entries"},
        "Volumes": {"revealVolumes": [{"position": vec(at(L["mitte"], 4)), "radius": 32, "reveals": ["ZEKIVD_LAGER_FOUND"]}],
                    "interactionVolumes": [
            {"position": vec(home), "radius": 2.5, "range": 3.5, "prompt": "Durch den Rücksamen heimkehren", "condition": "ZEKIVD_HEIMREISE",
             "persistent": False, "reusable": True, "rename": "VD_Ruecksamen_Volumen"}]},
    })


SAMENSCHLUND_AT = (24000, 41000, -33000)
ANKUNFTSKAMMER_AT = (-31000, 26000, 42000)


def timber_hearth():
    """The crash site on Timber Hearth (system SolarSystem). One container; the DLL moves it beside the vanilla
    impact crater onto the ground (Crossing.cs), so everything inside is relative to it, +y up."""
    site = TH_SITE
    cfg = sb.body_header("TIMBER_HEARTH", "SolarSystem")
    cfg["Props"] = {"details": [
        {"path": "", "position": vec([0, 400, 0]), "rename": "VD_Absturzstelle", "keepLoaded": True},
        {"path": P["smoke_crash"], "parentPath": site, "isRelativeToParent": True, "position": vec([4, 8, 3]), "rename": "VD_Rauch"},
    ] + bramble_templates("Sector_TH")}
    cfg["Volumes"] = {"revealVolumes": [{"parentPath": site, "isRelativeToParent": True, "position": vec([0, 10, 0]), "radius": 70,
                                         "reveals": ["ZEKIVD_ABSTURZ_FOUND"]}]}
    cfg["Bramble"] = {"nodes": [
        # the seed itself: large enough to walk into, half sunk into the crater
        {"parentPath": site, "isRelativeToParent": True, "position": vec([0, 10, 0]), "linksTo": "Samenschlund", "name": "ZEKIVD_Absturzsamen",
         "scale": 0.25, "fogTint": color(120, 255, 150), "lightTint": color(150, 255, 170)}]}
    return cfg


DIMENSION_FACTS = {"Samenschlund": "ZEKIVD_ABSTURZ_SCHLUND", "Eispforte": "ZEKIVD_EISPFORTE_FOUND", "Splittergang": "ZEKIVD_SPLITTER_FOUND",
                   "Kaeltenest": "ZEKIVD_KAELTE_FOUND"}


def dimension(name, at_, radius, fog, density, exit_node, vines="smallNest", nodes=None, extra=None, system=SYSTEM):
    cfg = sb.body_header(name, system)
    cfg.update({
        "canShowOnTitle": False,
        "Orbit": {"staticPosition": vec(at_)},
        "ShipLog": {"mapMode": {"remove": True}},
        "Bramble": {"dimension": {"radius": radius, "fogTint": fog, "fogDensity": density, "linksTo": exit_node, "vinePrefab": vines}},
        "Volumes": {"revealVolumes": [{"position": vec([0, 0, 0]), "radius": radius, "reveals": [DIMENSION_FACTS[name]]}]}
        if name in DIMENSION_FACTS else {},
    })
    if nodes:
        cfg["Bramble"]["nodes"] = nodes
    cfg.update(extra or {})
    return cfg


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
        "Props": {"entryLocation": [{"id": "ZEKIVD_AUSGUCK", "position": vec([0, 4, 0])}]},
        # Nomai gravity on the deck, the landing and the lift shaft
        "Volumes": {"revealVolumes": [{"position": vec([0, 2, 0]), "radius": 40, "reveals": ["ZEKIVD_AUSGUCK_FOUND", "ZEKIVD_SYSTEM_BLICK"]}],
                    "forces": {"directionalVolumes": [
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


# dimensions 2-4 of the thorn network (spec section 5)
EISPFORTE_AT = (-52000, -18000, 30000)
SPLITTERGANG_AT = (-60000, 33000, -24000)
KAELTENEST_AT = (47000, -36000, 51000)


def dimensions():
    node = lambda pos, to, name, scale, fog: {"position": vec(pos), "rotation": vec([0, 0, 0]), "linksTo": to, "name": name, "scale": scale,  # noqa: E731
                                              "fogTint": fog, "lightTint": fog}
    return {
        "Eispforte": dimension("Eispforte", EISPFORTE_AT, 420, color(110, 170, 215), 3.0, "ZEKIVD_Erstling_Knoten", vines="hub", nodes=[
            node([160, 60, -120], "Splittergang", "ZEKIVD_Zu_Splittergang", 0.6, color(190, 235, 255)),
            node([-150, -80, 140], "Kaeltenest", "ZEKIVD_Zu_Kaeltenest", 0.6, color(90, 120, 220)),
        ]),
        "Splittergang": dimension("Splittergang", SPLITTERGANG_AT, 320, color(170, 220, 235), 2.4, "ZEKIVD_Zu_Splittergang", vines="cluster"),
        "Kaeltenest": dimension("Kaeltenest", KAELTENEST_AT, 280, color(40, 60, 120), 4.0, "ZEKIVD_Zu_Kaeltenest", extra={
            # a real anglerfish lives here
            "Props": {"details": [{"path": P["angler"], "position": vec([60, -40, 30]), "rename": "VD_Anglerfisch"}]}}),
    }


def gate_rotation(L):
    """Euler angles that stand the gate upright on the camp's surface, facing the cave (Unity: Euler zxy)."""
    n = L["torzu"]["normal"]
    up = [n["x"], n["y"], n["z"]]
    a, b = at(L["torzu"]), at(L["hoehle"])
    fwd = [b[i] - a[i] for i in range(3)]
    dot = sum(fwd[i] * up[i] for i in range(3))
    fwd = [fwd[i] - up[i] * dot for i in range(3)]
    return look_rotation(fwd, up)


def look_rotation(fwd, up):
    """Unity Euler angles (degrees) of Quaternion.LookRotation(fwd, up)."""
    def norm(v):
        n = math.sqrt(sum(c * c for c in v)) or 1.0
        return [c / n for c in v]

    def cross(a, b):
        return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]
    z = norm(fwd)
    x = norm(cross(up, z))
    y = cross(z, x)
    # rotation matrix columns x, y, z -> Euler (Unity order: z, then x, then y)
    pitch = math.asin(max(-1.0, min(1.0, -z[1])))
    yaw_ = math.atan2(z[0], z[2])
    roll = math.atan2(x[1], y[1])
    return [round(math.degrees(pitch), 3), round(math.degrees(yaw_), 3), round(math.degrees(roll), 3)]


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
    props += [
        {"model": "krater", "name": "VD_Krater", "body": "TIMBER_HEARTH", "parentPath": TH_SITE, "collider": True},
        {"model": "absperrung", "name": "VD_Absperrung", "body": "TIMBER_HEARTH", "parentPath": TH_SITE, "collider": True,
         "position": vec([0, 0.4, 41]), "rotation": vec([0, 180, 0])},
        {"model": "strudel", "name": "VD_Strudel", "body": "Samenschlund", "spin": 14},
        {"model": "planetenkern_erstling", "name": "VD_Kern_Erstling_Modell", "body": "Erstling", "parentPath": "Sector/VD_Kern_Erstling", "spin": 25},
        {"model": "lager_tor", "name": "VD_Lager_Tor", "body": "Erstling", "collider": True, "position": vec(at(A["lager"]["torzu"])),
         "rotation": vec(gate_rotation(A["lager"]))},
    ]
    rnd = random.Random(5)
    for k in range(7):  # ice thorns in the Splittergang
        props.append({"model": "eiszapfen", "name": f"VD_Eiszapfen_{k}", "body": "Splittergang", "collider": True,
                      "position": vec([rnd.uniform(-180, 180), rnd.uniform(-120, 120), rnd.uniform(-180, 180)]),
                      "rotation": vec([rnd.uniform(0, 360), rnd.uniform(0, 360), 0]), "scale": rnd.uniform(1.0, 2.2)})
    for p in props:
        p.setdefault("name", p["model"].capitalize())
        p.setdefault("position", vec([0, 0, 0]))
        p.setdefault("rotation", vec([0, 0, 0]))
        p.setdefault("scale", 1)
    lights = [
        {"name": "Licht_Strudel", "body": "Samenschlund", "position": vec([0, 0, 0]), "color": vec([0.6, 1.0, 0.65]), "range": 70, "intensity": 2.0},
        {"name": "Licht_Lager", "body": "Erstling", "position": vec(at(A["lager"]["mitte"], 14)), "color": vec([0.75, 0.9, 1.0]),
         "range": 60, "intensity": 1.4},
        {"name": "Licht_Ausguck", "body": "Ausguck", "position": vec([0, 8, 0]), "color": vec([0.75, 0.9, 1.0]), "range": 45, "intensity": 1.2},
    ]
    bramble = {
        "Ankunftskammer": {"pfade": vine_paths(1, 160, 7, (3, 6))},
        "Eispforte": {"pfade": vine_paths(2, 420, 10, (6, 12))},
        "Splittergang": {"pfade": vine_paths(3, 320, 8, (4, 9))},
        "Kaeltenest": {"pfade": vine_paths(4, 280, 9, (4, 8)), "samen": [{"position": vec([-40, 70, -50]), "groesse": 14}]},
        "Samenschlund": {"pfade": vine_paths(5, 220, 6, (3, 7))},
    }
    return {"props": props, "lights": lights, "bramble": bramble, "computers": computers()}


# ship log layout (rumor mode)
ENTRIES_HOME = {"ZEKIVD_ABSTURZ": (2900, -400)}
ENTRIES = {"ZEKIVD_LAGER": (0, 0), "ZEKIVD_AUSGUCK": (420, 220), "ZEKIVD_NETZ": (420, -220), "ZEKIVD_KERNE": (-500, 0)}
ORANGE = (color(150, 230, 120), color(220, 255, 200))


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
        "curiosities": [{"id": "ZEKIVD_LAGER", "color": GREEN[0], "highlightColor": GREEN[1]},
                        {"id": "ZEKIVD_KERNE", "color": color(150, 200, 255), "highlightColor": color(210, 235, 255)}],
        "entryPositions": [{"id": k, "position": {"x": v[0], "y": v[1]}} for k, v in ENTRIES.items()],
    }


def home_system():
    """systems/SolarSystem.json of this mod: the curiosity of the crashed seed."""
    return {
        "$schema": NH + "star_system_schema.json",
        "curiosities": [{"id": "ZEKIVD_ABSTURZ", "color": GREEN[0], "highlightColor": GREEN[1]}],
        "entryPositions": [{"id": k, "position": {"x": v[0], "y": v[1]}} for k, v in ENTRIES_HOME.items()],
    }


def entry_art(entry, seed):
    """Ship log pictures for stage 1 (a thorn ball with the entry's own tint; renders follow later)."""
    from PIL import ImageDraw
    rnd = random.Random(seed)
    tint = {"ZEKIVD_ABSTURZ": (150, 230, 120), "ZEKIVD_LAGER": (150, 200, 255), "ZEKIVD_AUSGUCK": (255, 210, 140),
            "ZEKIVD_NETZ": (120, 190, 255), "ZEKIVD_KERNE": (190, 230, 255)}[entry]
    img = sb.starfield(512, seed, tint=tint)
    d = ImageDraw.Draw(img)
    c = 256
    for k in range(22):
        a = rnd.uniform(0, math.tau)
        r1, r2 = rnd.uniform(40, 90), rnd.uniform(150, 240)
        d.line([(c + r1 * math.cos(a), c + r1 * math.sin(a)), (c + r2 * math.cos(a + 0.3), c + r2 * math.sin(a + 0.3))],
               fill=(70, 55, 40, 255), width=rnd.randint(5, 12))
    d.ellipse([c - 70, c - 70, c + 70, c + 70], fill=tint + (255,), outline=(255, 255, 240, 255), width=5)
    return img


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
    import verdornt_shiplog  # the Nomai texts and the ship log the configs point to
    import verdornt_texts
    verdornt_texts.MOD = verdornt_shiplog.MOD = MOD
    verdornt_texts.write_all()
    verdornt_shiplog.main()
    manifests()
    write_json(f"systems/{SYSTEM}.json", system())
    write_json("planets/Herzdorn.json", herzdorn())
    write_json("planets/Erstling.json", erstling(A))
    write_json("planets/Glutdorn.json", planet("Glutdorn", 220, 9))
    write_json("planets/Nebelranke.json", nebelranke())
    write_json("planets/Hohlsamen.json", planet("Hohlsamen", 300, 8))
    write_json("planets/Ausguck.json", ausguck())
    write_json("planets/Fernlager.json", fernlager())
    write_json("planets/TimberHearth.json", timber_hearth())
    schlund = dimension("Samenschlund", SAMENSCHLUND_AT, 220, color(40, 95, 55), 3.0, "ZEKIVD_Absturzsamen", system="SolarSystem")
    schlund["ShipLog"] = {"xmlFile": "planets/shiplogs/Absturz.xml", "spriteFolder": "planets/assets/shiplog/entries", "mapMode": {"remove": True}}
    write_json("planets/Samenschlund.json", schlund)
    write_json("systems/SolarSystem.json", home_system())
    for k, entry in enumerate(list(ENTRIES_HOME) + list(ENTRIES)):
        sb.save(entry_art(entry, 100 + k), f"planets/assets/shiplog/entries/{entry}.png")
    write_json("planets/Ankunftskammer.json", dimension("Ankunftskammer", ANKUNFTSKAMMER_AT, 160, color(150, 230, 160), 2.0, "ZEKIVD_Ankunftssamen"))
    for name, cfg in dimensions().items():
        write_json(f"planets/{name}.json", cfg)
    write_json("assets/models/placements.json", placements(A))


if __name__ == "__main__":
    main()
