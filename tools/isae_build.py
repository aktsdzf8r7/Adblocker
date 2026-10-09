# -*- coding: utf-8 -*-
"""
Build script for "Die Aussendungseinheit" (Zeki.ISAE), a New Horizons addon for the normal solar system.

The Interstellare Sonden Aussendungseinheit (ISAE) is a copy of the Orbital Probe Cannon that orbits the sun,
surrounded by three free-floating focus cannons in triangle formation (the gravity cannon of Ember Twin).
Every prop is taken from the game itself, Vessel-style where the game has one. All four cannons point along
the bodies' +y axis. The player has to cut the three phase couplers and pull the main
switch before the loop ends - otherwise the C# part of the mod (Zeki.ISAE.Source) drains the sun instead of
the supernova and plays the finale.

Generates: planets/*.json, systems/SolarSystem.json, ship log images, manifests. The Nomai texts come from
isae_texts.py, the ship log XML is written by hand.

Usage:  python tools/isae_build.py [path/to/Zeki.ISAE]
Needs:  Python 3.9+, numpy, Pillow
"""
import json
import math
import os
import shutil
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import schleier_build as sb  # noqa: E402
from schleier_build import NH, P, color, reveal, vec, write_json  # noqa: E402

MOD = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "Zeki.ISAE"))
sb.MOD = MOD  # the shared helpers write into this mod

NAME = "Interstellare Sonden Aussendungseinheit"
VERSION = "1.3.0"

# ----------------------------------------------------------------------------------------------
# Aim. Every body here has axialTilt 0 and siderealPeriod 0, so their local axes are the world axes
# and never turn. The main cannon (Blender) and the focus cannons fire along their bodies' +y axis;
# the triangle orbits in the plane perpendicular to it.
# ----------------------------------------------------------------------------------------------
FOCUS_DISTANCE = 340     # metres between the main cannon and each focus cannon
FOCUS_NAMES = (("A", "Alpha", 0), ("B", "Beta", 120), ("C", "Gamma", 240))

# conditions (keep in sync with ZekiISAE.cs)
DEAKTIVIERT = "ZEKISAE_DEAKTIVIERT"      # persistent: the player switched the ISAE off
ENTDECKT = "ZEKISAE_ENTDECKT"            # persistent: the player has been at the ISAE once
ENTZUG = "ZEKISAE_ENTZUG"                # dialogue: set by the DLL while the sun is drained
VORBOTE = "ZEKISAE_VORBOTE"              # dialogue: set by the DLL two minutes before the end of the loop
KOPPLER = "ZEKISAE_KOPPLER_%s"           # persistent: one phase coupler cut
KOPPLER_ALLE = "ZEKISAE_KOPPLER_ALLE"    # persistent: all three cut, the main switch appears

# a free spot in the control module of the real Orbital Probe Cannon (used by the published addon EyeWitness)
OPC_MODULE = "Sector_OrbitalProbeCannon/Sector_Module_Intact"
OPC_COMPUTER = (-6.8811, -6.9297, 8.7142)
OPC_ROT = (270, 0, 0)

RED = (color(235, 90, 50), color(255, 170, 120))


def rot(e):
    return vec(e, 1)


def placed(path, pos, rotation=(0, 0, 0), **extra):
    """A detail placed in the body frame (no radial alignment - the ISAE has no ground)."""
    d = {"path": path, "position": vec(pos), "rotation": rot(rotation)}
    d.update(extra)
    return d


def relative(parent, pos, rotation=(0, 0, 0), **extra):
    d = {"parentPath": parent, "isRelativeToParent": True, "position": vec(pos), "rotation": rot(rotation)}
    d.update(extra)
    return d


# ==============================================================================================
# the main cannon
# ==============================================================================================
def anchors():
    """Spots on the Blender models (Unity coordinates of the ISAE body), written by tools/isae_models.py."""
    with open(os.path.join(MOD, "assets", "models", "anchors.json"), encoding="utf-8") as f:
        return json.load(f)


def at(a, up=0.0):
    p = a["position"]
    return [p["x"], p["y"] + up, p["z"]]


def text_at(kind, xml, a, rename, **extra):
    t = {"type": kind, "xmlFile": "planets/text/" + xml, "position": vec(at(a)), "rename": rename}
    if kind == "wall":
        t["normal"] = a["normal"]
    else:
        t["rotation"] = rot((0, a.get("yaw", 0), 0))
    t.update(extra)
    return t


# what stands in which module: (prop key or text, xml, anchor, rename)
MODULE_TEXTS = {
    "kontrolle": [("preCrashComputer", "ISAE_Status.xml", "links", "Computer_Status"),
                  ("preCrashRecorder", "ISAE_Linum.xml", "rechts", "Recorder_Linum"),
                  ("wall", "Sedum_Abschied.xml", "wand", "Wandschrift_Sedum")],
    "start": [("wall", "Start_Bau.xml", "wand", "Wandschrift_Bau"),
              ("preCrashComputer", "Start_Sonde.xml", "links", "Computer_Sonde")],
    "navigation": [("preCrashComputer", "Navi_Ziel.xml", "links", "Computer_Ziel"),
                   ("preCrashRecorder", "Navi_Pye.xml", "rechts", "Recorder_Pye"),
                   ("wall", "Navi_Wand.xml", "wand", "Wandschrift_Ziel")],
}
MODULE_FACTS = {"kontrolle": ("ZEKISAE_KONTROLLE_FOUND", "ZEKISAE_KONTROLLE"), "start": ("ZEKISAE_START_FOUND", "ZEKISAE_START"),
                "navigation": ("ZEKISAE_NAVI_FOUND", "ZEKISAE_NAVI")}


def isae_config(A):
    I = A["isae"]
    switch = "Sector/ISAE_Hauptschalter"
    details = [
        # the hub's energy core glows until the ISAE is switched off
        placed(P["warp_particles"], at(I["kern"]), scale=6, rename="ISAE_Energiekern", keepLoaded=True,
               deactivationCondition=DEAKTIVIERT, blinkWhenActiveChanged=True),
        # two minutes before the end the muzzle starts to glow, during the drain a beam leaves it
        placed(P["warp_particles"], at(I["muendung"]), scale=2.5, rename="ISAE_Muendungsglut", keepLoaded=True, activationCondition=VORBOTE),
        placed(P["light_beam"], at(I["muendung"]), scale=6, rename="ISAE_Entzugsstrahl", keepLoaded=True, activationCondition=ENTZUG),
    ]
    texts, volumes = [], {"interactionVolumes": [], "revealVolumes": [], "forces": {"directionalVolumes": []}}
    entries = [{"id": "ZEKISAE_ISAE", "position": vec(at(I["kern"], 20))}]
    for key, m in ((k, A[k]) for k in ("kontrolle", "start", "navigation")):
        for kind, xml, spot, rename in MODULE_TEXTS[key]:
            texts.append(text_at(kind, xml, m[spot], rename, **({"seed": 4100 + len(texts)} if kind == "wall" else {})))
        fact, entry = MODULE_FACTS[key]
        volumes["revealVolumes"].append(reveal(at(m["boden"], 2), 8, [fact]))
        entries.append({"id": entry, "position": vec(at(m["boden"], 2))})
        # Nomai artificial gravity towards the floor of the module
        volumes["forces"]["directionalVolumes"].append({
            "force": 9, "normal": vec([0, -1, 0]), "position": vec(at(m["boden"], m["hoehe"] / 2)),
            "shape": {"type": "cylinder", "radius": m["bodenRadius"] - 0.3, "height": m["hoehe"] - 0.4},
            "rename": f"Schwerkraft_{m['name']}"})
    K, S = A["kontrolle"], A["start"]
    details += [
        # Sedum's remains in front of his last words
        placed(P["skeleton"], at(K["hinten_links"]), (0, K["hinten_links"]["yaw"], 0), rename="Sedums_Ueberreste"),
        placed(P["staff"], at(K["hinten_links"], 0.05), (0, K["hinten_links"]["yaw"] + 70, 90), rename="Sedums_Stab"),
        # the main switch on the dais, wakes up once all three couplers are cut: the Vessel's coordinate
        # interface with an advanced warp core floating above it
        placed("", at(K["schalter"]), (0, K["schalter"]["yaw"], 0), rename="ISAE_Hauptschalter",
               activationCondition=KOPPLER_ALLE, deactivationCondition=DEAKTIVIERT),
        dict(relative(switch, (0, 0, 0)), path=P["vessel_interface"], rename="Hauptschalter_Vessel_Interface"),
        # removeComponents strips the item from the root, so the copy can not be picked up like the real core
        dict(relative(switch, (0, 3.2, 0)), path=P["warpcore_vessel"], rename="Hauptschalter_Warpkern", removeComponents=True),
        # the interstellar probe waits in the launch cradle; the DLL fires it through the barrel in the finale
        placed(P["nomai_probe"], at(S["wiege"]), rename="Interstellare_Sonde", keepLoaded=True),
    ]
    texts.append(dict(relative(switch, (2.6, 0, 0)), type="trailmarker", xmlFile="planets/text/ISAE_Hauptschalter.xml", rename="Wegmarke_Hauptschalter"))
    volumes["interactionVolumes"].append(dict(relative(switch, (0, 1.6, 0)), radius=1.6, range=3, prompt="Aussendungseinheit abschalten",
                                              condition=DEAKTIVIERT, persistent=True, reusable=False, audio="NomaiPowerOff",
                                              rename="Hauptschalter_Volumen"))
    volumes["revealVolumes"] += [
        reveal([0, 0, 0], 320, ["ZEKISAE_FOUND"]),
        reveal([0, 0, 0], 120, ["ZEKISAE_FOKUS_RUMOR"], "observe", maxDistance=2500, maxAngle=25),
    ]
    cfg = sb.body_header(NAME, "SolarSystem")
    cfg.update({
        "canShowOnTitle": False,
        "Base": {"surfaceSize": 120, "surfaceGravity": 0.6, "gravityFallOff": "linear", "showMinimap": False},
        # between the Hourglass Twins (5000 m) and Timber Hearth (8600 m), far out of the planets' plane
        "Orbit": {"primaryBody": "Sun", "semiMajorAxis": 6200, "eccentricity": 0, "inclination": 62, "longitudeOfAscendingNode": 35,
                  "trueAnomaly": 210, "axialTilt": 0, "siderealPeriod": 0, "tint": RED[0]},
        "MapMarker": {"enabled": True},
        "ShipLog": {"xmlFile": "planets/shiplogs/ISAE.xml", "spriteFolder": "planets/assets/shiplog/entries",
                    "mapMode": {"revealedSprite": "planets/assets/shiplog/map/isae.png",
                                "outlineSprite": "planets/assets/shiplog/map/isae_outline.png", "scale": 0.9}},
        "Props": {
            "details": details,
            "translatorText": texts,
            "signals": [{"frequency": "Energiesignaturen", "name": "Aussendungseinheit", "audio": "OW_NM_WhiteHoleAmbienceL",
                         "position": vec(at(I["kern"])), "sourceRadius": 5, "detectionRadius": 7000, "identificationRadius": 400}],
            "entryLocation": entries + [{"id": "ZEKISAE_SEDUM", "position": vec(at(K["hinten_links"], 1))}],
        },
        "Volumes": volumes,
    })
    return cfg


def placements(A):
    """assets/models/placements.json: where the DLL puts the Blender models (all in the ISAE body's frame)."""
    props = [{"model": "hauptkanone", "name": "ISAE_Hauptkanone", "collider": True},
             {"model": "laufringe", "name": "ISAE_Laufringe", "spin": 10},
             {"model": "sternkarte", "name": "ISAE_Sternkarte", "spin": 7, "position": A["navigation"]["karte"]["position"]}]
    props += [{"model": f"modul_{k}", "name": f"ISAE_{A[k]['name']}", "collider": True} for k in ("kontrolle", "start", "navigation")]
    for p in props:
        p["body"] = NAME
        p.setdefault("position", {"x": 0, "y": 0, "z": 0})
        p.setdefault("rotation", {"x": 0, "y": 0, "z": 0})
        p.setdefault("scale", 1)
    lights = []
    for k in ("kontrolle", "start", "navigation"):
        lights.append({"name": f"Licht_{A[k]['name']}", "body": NAME, "position": A[k]["licht1"]["position"],
                       "color": {"x": 0.75, "y": 0.9, "z": 1.0}, "range": 15, "intensity": 1.5})
        lights.append({"name": f"Licht_{A[k]['name']}_Tuer", "body": NAME, "position": A[k]["licht2"]["position"],
                       "color": {"x": 1.0, "y": 0.8, "z": 0.6}, "range": 8, "intensity": 0.8})
    return {
        # exact names of game materials for the Blender material slots; empty = taken from the Vessel
        "materials": {"VesselHuelle": "", "VesselKupfer": "", "VesselDunkel": "", "VesselLeuchten": ""},
        "props": props,
        "lights": lights,
        "points": {"muendung": A["isae"]["muendung"]["position"], "kern": A["isae"]["kern"]["position"]},
    }


# ==============================================================================================
# the three focus cannons
# ==============================================================================================
# Spots on the launch platform of the focus cannon. The DLL moves the gravity cannon so that the top of its
# platform lies exactly at the body origin, so y = 0 is the floor here.
COUPLER = (-3.6, 0.0, 2.4)
COMPUTER = (3.6, 0.0, 2.4)
LAMPS = [(5.2 * math.cos(math.radians(a)), 0.0, 5.2 * math.sin(math.radians(a))) for a in (135, 225, 315, 45)]


def yaw_to_centre(p):
    """Yaw (degrees around +y) that turns a prop's +z towards the middle of the platform."""
    return round(math.degrees(math.atan2(-p[0], -p[2])) % 360, 1)


def focus_config(letter, greek, anomaly):
    """A free-floating focus cannon: the gravity cannon of Ember Twin with its launch platform - no rock.
    A directional gravity field over the platform lets the player land and walk on it."""
    cond = KOPPLER % letter
    up = lambda p, h: [p[0], p[1] + h, p[2]]  # noqa: E731
    details = [
        placed(P["gravity_cannon"], (0, 0, 0), rename=f"Fokuskanone_{greek}_Struktur", keepLoaded=True),
        placed(P["light_beam"], (0, 0.5, 0), scale=2.5, rename=f"Fokusstrahl_{greek}", keepLoaded=True, activationCondition=ENTZUG),
        # the phase coupler: a glowing gravity crystal while connected, a cracked one once cut
        placed(P["gravity_crystal"], COUPLER, (0, yaw_to_centre(COUPLER), 0), rename=f"Phasenkoppler_{greek}",
               deactivationCondition=cond, blinkWhenActiveChanged=True),
        placed(P["crystal_cracked"], COUPLER, (0, yaw_to_centre(COUPLER), 0), rename=f"Phasenkoppler_{greek}_getrennt", activationCondition=cond),
        placed(P["warp_particles"], up(COUPLER, 2.2), scale=0.3, rename=f"Kopplerlicht_{greek}", deactivationCondition=cond),
    ]
    details += [placed(P["lamp_flare"], lamp, rename=f"Fokuslampe_{greek}_{i + 1}") for i, lamp in enumerate(LAMPS)]
    texts = [{"type": "preCrashComputer", "xmlFile": f"planets/text/Fokus_{greek}.xml", "position": vec(COMPUTER),
              "rotation": rot((0, yaw_to_centre(COMPUTER), 0)), "rename": f"Computer_Fokus_{greek}"}]
    volumes = {
        "interactionVolumes": [{"position": vec(up(COUPLER, 1.0)), "radius": 1.5, "range": 3, "prompt": "Phasenkoppler trennen",
                                "condition": cond, "persistent": True, "reusable": False, "audio": "NomaiPowerSwitch",
                                "rename": f"Koppler_{greek}_Volumen"}],
        "revealVolumes": [reveal([0, 3, 0], 40, ["ZEKISAE_FOKUS_FOUND"])],
        # Nomai artificial gravity over the platform (pulls along -y, the cannon fires along +y). It is tall on
        # purpose: whatever the exact height of the platform, everything above it falls onto it.
        "forces": {"directionalVolumes": [{"force": 9, "normal": vec([0, -1, 0]), "position": vec([0, 9, 0]),
                                           "shape": {"type": "cylinder", "radius": 12, "height": 20},
                                           "rename": f"Deckschwerkraft_{greek}"}]},
    }
    props = {"details": details, "translatorText": texts}
    if letter == "A":
        props["entryLocation"] = [{"id": "ZEKISAE_FOKUS", "position": vec([0, 3, 0])}]
    cfg = sb.body_header(f"Fokuskanone {greek}", "SolarSystem")
    cfg.update({
        "canShowOnTitle": False,
        "Base": {"surfaceSize": 25, "surfaceGravity": 0, "showMinimap": False},
        # same circle, 120 degrees apart: the triangle keeps its shape while it turns around the main cannon
        "Orbit": {"primaryBody": NAME, "isMoon": True, "semiMajorAxis": FOCUS_DISTANCE, "eccentricity": 0, "inclination": 0,
                  "longitudeOfAscendingNode": 0, "argumentOfPeriapsis": 0, "trueAnomaly": anomaly, "axialTilt": 0, "siderealPeriod": 0,
                  "dottedOrbitLine": True, "tint": RED[1]},
        "MapMarker": {"enabled": True},
        "ShipLog": {"mapMode": {"remove": True}},
        "Props": props,
        "Volumes": volumes,
    })
    return cfg


# ==============================================================================================
# the hint inside the real Orbital Probe Cannon
# ==============================================================================================
def opc_config():
    cfg = sb.body_header("ORBITAL_PROBE_CANNON", "SolarSystem")
    cfg["Props"] = {"translatorText": [dict(relative(OPC_MODULE, OPC_COMPUTER, OPC_ROT), type="computer",
                                            xmlFile="planets/text/OPC_Sedum.xml", rename="Computer_Sedum")]}
    return cfg


def solar_system():
    entries = {"ZEKISAE_ISAE": (1650, 450), "ZEKISAE_KONTROLLE": (2080, 450), "ZEKISAE_START": (2500, 720),
               "ZEKISAE_NAVI": (2500, 180), "ZEKISAE_FOKUS": (2080, 880), "ZEKISAE_SEDUM": (2080, 20)}
    checks = [
        {"check": {"allFactsRevealed": ["ZEKISAE_FOUND"]}, "then": {"setPersistentConditions": [ENTDECKT]}},
        {"check": {"allPersistentConditionsSet": [KOPPLER % x for x, _, _ in FOCUS_NAMES]}, "then": {"setPersistentConditions": [KOPPLER_ALLE]}},
        {"check": {"allPersistentConditionsSet": [DEAKTIVIERT]}, "then": {"revealFacts": ["ZEKISAE_ABGESCHALTET"]}},
    ]
    checks[2:2] = [{"check": {"allPersistentConditionsSet": [KOPPLER % x]}, "then": {"revealFacts": [f"ZEKISAE_KOPPLER_{x}_FACT"]}}
                   for x, _, _ in FOCUS_NAMES]
    return {
        "$schema": NH + "star_system_schema.json",
        "initialReveal": ["ZEKISAE_SIGNATUR"],
        "curiosities": [{"id": "ZEKISAE_ISAE", "color": RED[0], "highlightColor": RED[1]}],
        "entryPositions": [{"id": k, "position": {"x": v[0], "y": v[1]}} for k, v in entries.items()],
        "conditionalChecks": checks,
    }


# ==============================================================================================
# images
# ==============================================================================================
def cannon(d, x, y, length, width, fill, outline):
    """A Nomai cannon seen from the side, firing upwards."""
    d.rounded_rectangle([x - width / 2, y - length, x + width / 2, y], radius=width / 3, fill=fill, outline=outline, width=3)
    d.ellipse([x - width, y - width * 0.6, x + width, y + width * 1.2], fill=fill, outline=outline, width=3)
    d.ellipse([x - width * 0.35, y - length - width * 0.2, x + width * 0.35, y - length + width * 0.3], fill=(255, 200, 150, 255))


def art(seed, motif, size=512):
    img = sb.starfield(size, seed, tint=(255, 110, 70))
    d = ImageDraw.Draw(img)
    c = size / 2
    metal, edge = (120, 112, 120, 255), (225, 205, 190, 255)
    if motif == "isae":
        d.polygon([(c - 10, 0), (c + 10, 0), (c + 4, c - 80), (c - 4, c - 80)], fill=(255, 150, 90, 150))
        d.ellipse([c - 175, c, c + 175, c + 140], outline=(255, 140, 90, 140), width=3)
        spots = [(c + 175 * math.cos(math.radians(a)), c + 70 + 70 * math.sin(math.radians(a))) for a in (250, 10, 130)]
        cannon(d, spots[0][0], spots[0][1] + 40, 80, 18, metal, edge)  # behind the main cannon
        cannon(d, c, c + 120, 210, 44, metal, edge)
        for x, y in spots[1:]:
            cannon(d, x, y + 40, 80, 18, metal, edge)
    elif motif == "fokus":
        pts = []
        for k in range(3):
            a = math.radians(-90 + k * 120)
            pts.append((c + 160 * math.cos(a), c + 30 + 160 * math.sin(a)))
        d.polygon(pts, outline=(255, 150, 90, 220), width=5)
        for x, y in pts:
            cannon(d, x, y + 40, 90, 22, metal, edge)
            d.ellipse([x - 12, y + 50, x + 12, y + 74], fill=(170, 220, 255, 255))
    elif motif == "sedum":
        for k, r in enumerate((150, 110, 70)):
            col = (255, 190 - k * 50, 90 - k * 25, 255)
            d.ellipse([c - r, c - r, c + r, c + r], outline=col, width=6)
        d.ellipse([c - 30, c - 30, c + 30, c + 30], fill=(40, 20, 20, 255), outline=(255, 120, 70, 255), width=4)
        sb.spiral(d, c - 120, c + 150, 55, 2.0, 4, (240, 200, 120, 255))
        sb.spiral(d, c + 120, c + 150, 55, 2.0, 4, (170, 210, 255, 255), reverse=True)
    return img


def map_sprite(size=256):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = size / 2
    d.ellipse([12, 12, size - 12, size - 12], fill=(40, 22, 26, 255))
    metal, edge = (150, 140, 150, 255), (255, 220, 200, 255)
    spots = [(c + 85 * math.cos(math.radians(a)), c + 40 + 40 * math.sin(math.radians(a))) for a in (250, 10, 130)]
    cannon(d, spots[0][0], spots[0][1] + 10, 40, 10, metal, edge)
    cannon(d, c, c + 70, 130, 30, metal, edge)
    for x, y in spots[1:]:
        cannon(d, x, y + 10, 40, 10, metal, edge)
    outline = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(outline).ellipse([3, 3, size - 4, size - 4], outline=(255, 255, 255, 255), width=5)
    return img, outline


# ==============================================================================================
def manifests():
    write_json("manifest.json", {
        "$schema": "https://raw.githubusercontent.com/ow-mods/owml/master/schemas/manifest_schema.json",
        "filename": "ZekiISAE.dll",
        "author": "Zeki",
        "name": "Die Aussendungseinheit",
        "uniqueName": "Zeki.ISAE",
        "version": VERSION,
        "owmlVersion": "2.15.5",
        "dependencies": ["xen.NewHorizons"],
    })
    write_json("default-config.json", {
        "$schema": "https://raw.githubusercontent.com/ow-mods/owml/master/schemas/config_schema.json",
        "enabled": True,
        "settings": {
            "onlyAfterDiscovery": {"type": "toggle", "value": False, "title": "Erst nach der Entdeckung scharf",
                                   "tooltip": "Die Sonne wird erst entzogen, wenn du die Aussendungseinheit einmal besucht hast."},
            "drainSeconds": {"type": "slider", "value": 60, "min": 20, "max": 180, "title": "Dauer des Energieentzugs (Sekunden)",
                             "tooltip": "Wie lange die Sonne am Ende der Schleife schrumpft, bevor sie erlischt."},
            "cinematic": {"type": "toggle", "value": True, "title": "Filmische Kamera im Finale",
                          "tooltip": "Im Finale dreht sich die Kamera zur Sonne und folgt dem Schuss. Aus: Du behältst die Steuerung."},
            "materialSource": {"type": "selector", "value": "Vessel", "options": ["Vessel", "Sondenkanone", "Einfach"],
                               "title": "Materialien der Hauptkanone",
                               "tooltip": "Vessel: die Materialien des Vessels. Sondenkanone: die der echten Sondenkanone. Einfach: schlichte Farben."},
        },
    })
    write_json("addon-manifest.json", {
        "$schema": NH + "addon_manifest_schema.json",
        "credits": ["Zeki"],
        "popupMessage": "Die Aussendungseinheit: Irgendwo zwischen der Sonne und Timber Hearth erwacht eine Nomai-Maschine. "
                        "Wenn du nichts tust, endet diese Schleife nicht mit einer Supernova.",
        "gameOver": [{"text": "Das Universum endet, aber du endest vor ihm...", "condition": "ZEKISAE_UNIVERSUM_ENDET",
                      "colour": color(255, 120, 70),
                      # custom = the credits roll with the game's final music, but without the Big Bang epilogue
                      "creditsType": "custom", "audio": "FinalCredits", "length": 110}],
    })


def main():
    A = anchors()
    write_json("planets/ISAE.json", isae_config(A))
    for x, greek, anomaly in FOCUS_NAMES:
        write_json(f"planets/Fokuskanone_{greek}.json", focus_config(x, greek, anomaly))
    write_json("planets/OrbitalProbeCannon.json", opc_config())
    write_json("systems/SolarSystem.json", solar_system())
    write_json("assets/models/placements.json", placements(A))
    manifests()

    # ZEKISAE_ISAE, _KONTROLLE, _START, _NAVI and the map sprite are Blender renders (tools/isae_models.py)
    E = "planets/assets/shiplog/entries/"
    for entry, motif, seed in (("ZEKISAE_FOKUS", "fokus", 32), ("ZEKISAE_SEDUM", "sedum", 33)):
        sb.save(art(seed, motif), E + entry + ".png")
    _, outline = map_sprite()
    sb.save(outline, "planets/assets/shiplog/map/isae_outline.png")
    terrain = os.path.join(MOD, "planets", "assets", "terrain")
    if os.path.isdir(terrain):  # the focus cannons stood on rocks in version 1.0
        shutil.rmtree(terrain)


if __name__ == "__main__":
    main()
