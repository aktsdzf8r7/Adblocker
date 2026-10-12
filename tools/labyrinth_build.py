# -*- coding: utf-8 -*-
"""
Build script for "Das Dornenlabyrinth" (Zeki.Dornenlabyrinth), a New Horizons mod: a drifting bramble seed in the
solar system leads into an infinite, fixed labyrinth of bramble dimensions.
Design: docs/superpowers/specs/2026-10-11-dornenlabyrinth-design.md

New Horizons builds one dimension per room type with a pool of nodes and seeds; the DLL turns them into the infinite
maze (Labyrinth.cs). Every pool node links to the Vorhof here: whatever the DLL fails to set up, the player always
ends up in the Vorhof, and the Vorhof always leads outside.

Generates the Treibsamen, the 15 room dimensions, Gneis's notes, the ship log, assets/labyrinth.json (the node
names per room for the DLL, in the order of MazeGraph.Pool) and assets/models/placements.json.

Usage:  python tools/labyrinth_build.py [path/to/Zeki.Dornenlabyrinth]
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import schleier_build as sb  # noqa: E402
from nh_props import P  # noqa: E402
from schleier_build import NH, color, vec, write_json  # noqa: E402

MOD = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "Zeki.Dornenlabyrinth"))
sb.MOD = MOD

VERSION = "0.1.0"
SYSTEM = "SolarSystem"
ENTRANCE = "ZEKIDL_Treibsamen"
FREQUENCY = "Dornenrufe"

# type -> (radius, fog, fog density, vine prefab, adult nodes, seeds); the pool sizes must match MazeGraph.Pool
ROOMS = {
    "Vorhof": (300, color(95, 120, 90), 4.0, "hub", 3, 2),
    "Dornengang": (350, color(84, 83, 73), 6.0, "hub", 4, 3),
    "Dornenwald": (300, color(66, 80, 52), 7.0, "cluster", 4, 3),
    "Hitzekammer": (250, color(200, 85, 35), 5.0, "smallNest", 1, 6),
    "Frostkammer": (320, color(150, 200, 235), 4.0, "smallNest", 3, 2),
    "Nest": (400, color(80, 14, 14), 7.0, "smallNest", 3, 1),
    "Samenkammer": (280, color(110, 145, 90), 5.0, "smallNest", 1, 8),
    "Nebelkammer": (350, color(185, 185, 172), 18.0, "smallNest", 3, 2),
    "Leere": (700, color(8, 8, 12), 1.0, "none", 1, 0),
    "Stroemung": (350, color(70, 115, 135), 5.0, "smallNest", 3, 2),
    "Echokammer": (300, color(95, 82, 120), 6.0, "smallNest", 3, 2),
    "Wrack": (320, color(82, 76, 60), 6.0, "smallNest", 3, 1),
    "Spiegelkammer": (300, color(165, 175, 195), 4.0, "smallNest", 4, 0),
    "Herzpfad": (320, color(125, 60, 160), 5.0, "hub", 3, 2),
    "Herzkammer": (260, color(150, 60, 195), 3.0, "smallNest", 1, 0),
}
NODE_LIGHT = color(190, 215, 170)
PURPLE = color(190, 110, 255)


def found_fact(room):
    return {"Vorhof": "ZEKIDL_VORHOF_FOUND", "Herzkammer": "ZEKIDL_HERZ_FOUND"}.get(room, f"ZEKIDL_{room.upper()}_FOUND")


def dimension_position(k):
    """Far below the solar system, 12 km apart, out of the way of every other mod's dimensions."""
    return [-84000 + 12000 * (k % 8), -90000, -12000 + 24000 * (k // 8)]


def node_names(room):
    _, _, _, _, nodes, seeds = ROOMS[room]
    return [f"ZEKIDL_{room}_K{i}" for i in range(nodes)], [f"ZEKIDL_{room}_S{i}" for i in range(seeds)]


def sphere_points(n, seed):
    """n directions spread evenly over the sphere (Fibonacci), turned by a seeded rotation."""
    rnd = random.Random(seed)
    a, b = rnd.uniform(0, math.tau), rnd.uniform(0, math.tau)
    pts = []
    for i in range(n):
        y = 1 - 2 * (i + 0.5) / n
        r = math.sqrt(1 - y * y)
        t = math.pi * (3 - math.sqrt(5)) * i + a
        x, z = r * math.cos(t), r * math.sin(t)
        # a turn around y by b keeps the spread
        pts.append([x * math.cos(b) - z * math.sin(b), y, x * math.sin(b) + z * math.cos(b)])
    return pts


def pool_positions(room, R, nodes, seeds):
    """Where the pool's adult nodes and seeds float. Seeds lie further in, so they do not hide in the wall."""
    if room == "Spiegelkammer":  # a tetrahedron: four exits that look alike
        s = 0.55 * R / math.sqrt(3)
        return [[s, s, s], [s, -s, -s], [-s, s, -s], [-s, -s, s]], []
    if room == "Leere":
        return [[0.0, 0.3 * R, 0.8 * R]], []
    if room == "Hitzekammer":  # the way out above, the six seeds in a ring around the glow
        ring = [[0.38 * R * math.cos(math.tau * i / 6), -0.1 * R, 0.38 * R * math.sin(math.tau * i / 6)] for i in range(6)]
        return [[0.0, 0.62 * R, 0.0]], ring
    if room == "Herzkammer":
        return [[0.0, 0.0, 0.7 * R]], []
    seed = sum(map(ord, room))
    k = [[c * 0.55 * R for c in p] for p in sphere_points(nodes, seed)]
    s = [[c * (0.35 if room == "Samenkammer" else 0.42) * R for c in p] for p in sphere_points(seeds, seed + 1)] if seeds else []
    return k, s


def nodes(room, R):
    _, fog, _, _, n, s = ROOMS[room]
    kn, sn = node_names(room)
    kp, sp = pool_positions(room, R, n, s)
    out = []
    for name, pos in zip(kn, kp):
        out.append({"position": vec(pos), "linksTo": "Labyrinth_Vorhof", "name": name, "scale": 0.5, "fogTint": fog, "lightTint": NODE_LIGHT,
                    "preventRecursionCrash": True})
    for name, pos in zip(sn, sp):
        out.append({"position": vec(pos), "linksTo": "Labyrinth_Vorhof", "name": name, "isSeed": True, "scale": 1.0, "fogTint": fog,
                    "lightTint": NODE_LIGHT, "hasFogLight": True, "preventRecursionCrash": True})
    return out


def note(name, pos, rename):
    return {"xmlFile": f"planets/dialogue/{name}.xml", "position": vec([pos[0], pos[1] + 1.2, pos[2]]), "radius": 2.0, "rename": rename}


def room_extra(room, R):
    """The room's rule and contents (spec 5). Models from Blender go to placements.json."""
    props, vols = {}, {}
    if room == "Vorhof":
        props["dialogue"] = [note("Gneis_Farben", NOTES["Vorhof"], "ZEKIDL_Notiz_Farben")]
    elif room == "Hitzekammer":
        vols["hazardVolumes"] = [{"type": "heat", "radius": 0.95 * R, "damagePerSecond": 4, "position": vec([0, 0, 0]), "rename": "ZEKIDL_Hitze"}]
    elif room == "Frostkammer":
        vols["speedLimiterVolumes"] = [{"radius": 0.95 * R, "maxSpeed": 12, "stoppingDistance": 60, "position": vec([0, 0, 0]),
                                        "rename": "ZEKIDL_Kaelte"}]
        vols["visorEffects"] = {"frostEffectVolumes": [{"radius": 0.95 * R, "frostRate": 0.3, "maxFrost": 0.6, "position": vec([0, 0, 0])}]}
        props["details"] = [
            # a copy of a real anglerfish: the DLL freezes it (no AI, no animation) inside a block of ice
            {"path": P["angler"], "position": vec([70, -40, -60]), "rotation": vec([10, 40, 0]), "rename": "ZEKIDL_Eisfisch"},
            {"path": P["skeleton"], "position": vec([-35, 22, 30]), "rotation": vec([30, 0, 20]), "rename": "ZEKIDL_Frostskelett"},
        ]
    elif room == "Nest":
        props["details"] = [{"path": P["angler"], "position": vec([110, -50, 60]), "rotation": vec([0, 200, 0]), "rename": "ZEKIDL_Anglerfisch_A"},
                            {"path": P["angler"], "position": vec([-90, 70, -110]), "rotation": vec([0, 30, 0]), "rename": "ZEKIDL_Anglerfisch_B"}]
    elif room == "Stroemung":
        vols["forces"] = {"directionalVolumes": [{"radius": 0.9 * R, "force": 6, "normal": vec([0.94, 0.34, 0]), "affectsAlignment": False,
                                                  "position": vec([0, 0, 0]), "rename": "ZEKIDL_Stroemung"}]}
    elif room == "Echokammer":
        kp, _ = pool_positions(room, R, ROOMS[room][4], ROOMS[room][5])
        rnd = random.Random(7)
        spots = [kp[0]] + [[c * rnd.uniform(0.3, 0.6) * R for c in p] for p in sphere_points(3, 99)]
        props["signals"] = [{"frequency": FREQUENCY, "name": "Echo", "audio": "DB_Ambience_LP", "position": vec(p), "sourceRadius": 5,
                             "identificationRadius": 15, "rename": f"ZEKIDL_Echo_{i}"} for i, p in enumerate(spots)]
    elif room == "Wrack":
        props["dialogue"] = [note("Gneis_Wrack", NOTES["Wrack"], "ZEKIDL_Notiz_Wrack")]
        props["details"] = [{"path": P["skeleton"], "position": vec([48, -12, -24]), "rotation": vec([0, 0, 25]), "rename": "ZEKIDL_Wrackskelett"}]
    elif room == "Herzpfad":
        props["dialogue"] = [note("Gneis_Herzpfad", NOTES["Herzpfad"], "ZEKIDL_Notiz_Herzpfad")]
    elif room == "Herzkammer":
        # an empty holder as the item; the DLL hangs the heart model into it and lets it pulse
        props["details"] = [{"path": "", "position": vec([0, 0, 0]), "rename": "ZEKIDL_Herz", "keepLoaded": True,
                             "item": {"name": "Bramble-Herz", "itemType": "BrambleHerz", "colliderRadius": 0.55, "interactRange": 3,
                                      "pickupFact": "ZEKIDL_HERZ_GENOMMEN", "holdOffset": vec([0, -0.15, 0.45])}}]
    return props, vols


# where Gneis's rafts float (dimension coordinates)
NOTES = {"Vorhof": [0, -6, 25], "Wrack": [26, -10, -18], "Herzpfad": [0, 0, 0]}


def dimension(room, k):
    R, fog, density, vines, _, _ = ROOMS[room]
    cfg = sb.body_header(f"Labyrinth_{room}", SYSTEM)
    cfg.update({
        "canShowOnTitle": False,
        "Orbit": {"staticPosition": vec(dimension_position(k))},
        "ShipLog": {"mapMode": {"remove": True}},
        # out through the wall: the DLL leads back to the node one came from; NH's default is the outside
        "Bramble": {"dimension": {"radius": R, "fogTint": fog, "fogDensity": density, "linksTo": ENTRANCE, "vinePrefab": vines},
                    "nodes": nodes(room, R)},
    })
    props, vols = room_extra(room, R)
    # the Vorhof also tells of the note and of the rooms behind its nodes (rumors, linked to the Vorhof)
    reveals = [found_fact(room)] + (["ZEKIDL_FARBEN_RUMOR", "ZEKIDL_RAEUME_RUMOR"] if room == "Vorhof" else [])
    vols.setdefault("revealVolumes", []).append({"position": vec([0, 0, 0]), "radius": R, "reveals": reveals})
    if props:
        cfg["Props"] = props
    cfg["Volumes"] = vols
    return cfg


def treibsamen():
    cfg = sb.body_header("Treibsamen", SYSTEM)
    cfg.update({
        "Base": {"surfaceSize": 80, "surfaceGravity": 0, "showMinimap": False},
        # between Giant's Deep and Dark Bramble
        "Orbit": {"primaryBody": "SUN", "semiMajorAxis": 18000, "inclination": 4, "trueAnomaly": 230, "longitudeOfAscendingNode": 40,
                  "isMoon": False},
        "MapMarker": {"enabled": True},
        "ShipLog": {"xmlFile": "planets/shiplogs/Treibsamen.xml", "spriteFolder": "planets/assets/shiplog/entries"},
        "Bramble": {"nodes": [{"position": vec([0, 0, 0]), "linksTo": "Labyrinth_Vorhof", "name": ENTRANCE, "scale": 1.0,
                               "fogTint": color(120, 200, 120), "lightTint": color(150, 255, 160), "hasFogLight": True}]},
        "Props": {
            "signals": [{"frequency": FREQUENCY, "name": "Treibsamen", "audio": "DB_Ambience_LP", "position": vec([0, 0, 0]), "sourceRadius": 80,
                         "identificationRadius": 500, "reveals": "ZEKIDL_TREIBSAMEN_SIGNAL", "rename": "ZEKIDL_Signal"}],
            "entryLocation": [{"id": "ZEKIDL_TREIBSAMEN", "position": vec([0, 0, 0])}],
        },
        "Volumes": {"revealVolumes": [{"position": vec([0, 0, 0]), "radius": 400, "reveals": ["ZEKIDL_TREIBSAMEN_FOUND"]}]},
    })
    return cfg


def placements():
    """assets/models/placements.json: where the DLL puts the Blender models (Models.cs)."""
    body = lambda room: f"Labyrinth_{room}"  # noqa: E731
    props = [{"model": "notiz", "name": f"ZEKIDL_Floss_{room}", "body": body(room), "position": vec(p)} for room, p in NOTES.items()]
    props += [
        {"model": "wrack", "name": "ZEKIDL_Wrack", "body": body("Wrack"), "position": vec([42, -20, -30]), "rotation": vec([20, 50, 10]),
         "collider": True},
        {"model": "eisblock", "name": "ZEKIDL_Eisblock", "body": body("Frostkammer"), "position": vec([-70, 35, 55]), "rotation": vec([5, 120, 15]),
         "collider": True},
        {"model": "herznest", "name": "ZEKIDL_Herznest", "body": body("Herzkammer"), "collider": True, "spin": 1.5},
        {"model": "herz", "name": "ZEKIDL_Herz_Modell", "body": body("Herzkammer"), "parentPath": "Sector/ZEKIDL_Herz", "spin": 20},
    ]
    rnd = random.Random(5)
    for i, p in enumerate(sphere_points(5, 17)):
        props.append({"model": "wasserkristalle", "name": f"ZEKIDL_Kristalle_{i}", "body": body("Frostkammer"),
                      "position": vec([c * rnd.uniform(0.25, 0.4) * ROOMS["Frostkammer"][0] for c in p]),
                      "rotation": vec([rnd.uniform(0, 360) for _ in range(3)]), "scale": rnd.uniform(0.7, 1.3), "collider": True})
    lights = [{"name": f"ZEKIDL_Laterne_{room}", "body": body(room), "position": vec([p[0] + 0.9, p[1] + 2.0, p[2] - 0.5]),
               "color": {"x": 1.0, "y": 0.78, "z": 0.45}, "range": 18, "intensity": 1.6} for room, p in NOTES.items()]
    lights += [{"name": "ZEKIDL_Herzlicht", "body": body("Herzkammer"), "position": vec([0, 0, 0]), "color": {"x": 0.75, "y": 0.35, "z": 1.0},
                "range": 70, "intensity": 3.0},
               {"name": "ZEKIDL_Glut", "body": body("Hitzekammer"), "position": vec([0, -0.1 * ROOMS["Hitzekammer"][0], 0]),
                "color": {"x": 1.0, "y": 0.42, "z": 0.12}, "range": 220, "intensity": 2.2}]
    return {"props": props, "lights": lights}


def labyrinth_json():
    raeume = {}
    for room in ROOMS:
        kn, sn = node_names(room)
        raeume[room] = {"body": f"Labyrinth_{room}", "knoten": kn, "samen": sn}
    return {"eingang": ENTRANCE, "raeume": raeume}


def home_system():
    import labyrinth_shiplog as ls
    return {
        "$schema": NH + "star_system_schema.json",
        "curiosities": [{"id": "ZEKIDL_TREIBSAMEN", "color": color(140, 230, 130), "highlightColor": color(210, 255, 200)}],
        "entryPositions": [{"id": k, "position": {"x": v[0], "y": v[1]}} for k, v in ls.ENTRIES.items()],
    }


def manifests():
    write_json("manifest.json", {
        "$schema": "https://raw.githubusercontent.com/ow-mods/owml/master/schemas/manifest_schema.json",
        "filename": "ZekiDornenlabyrinth.dll",
        "author": "Zeki",
        "name": "Das Dornenlabyrinth",
        "uniqueName": "Zeki.Dornenlabyrinth",
        "version": VERSION,
        "owmlVersion": "2.15.5",
        "dependencies": ["xen.NewHorizons"],
    })
    write_json("default-config.json", {
        "$schema": "https://raw.githubusercontent.com/ow-mods/owml/master/schemas/config_schema.json",
        "enabled": True,
        "settings": {},
    })
    write_json("addon-manifest.json", {
        "$schema": NH + "addon_manifest_schema.json",
        "credits": ["Zeki"],
        "popupMessage": "Das Dornenlabyrinth: Zwischen Giant's Deep und Dark Bramble treibt ein einzelner Dornensamen. Er ruft auf der Frequenz Dornenrufe.",
    })


def main():
    import labyrinth_shiplog
    import labyrinth_texts
    labyrinth_texts.MOD = labyrinth_shiplog.MOD = MOD
    labyrinth_texts.write_all()
    labyrinth_shiplog.main()
    manifests()
    write_json("systems/SolarSystem.json", home_system())
    write_json("planets/Treibsamen.json", treibsamen())
    for k, room in enumerate(ROOMS):
        write_json(f"planets/Labyrinth_{room}.json", dimension(room, k))
    write_json("assets/labyrinth.json", labyrinth_json())
    write_json("assets/models/placements.json", placements())
    print("Dornenlabyrinth gebaut:", MOD)


if __name__ == "__main__":
    main()
