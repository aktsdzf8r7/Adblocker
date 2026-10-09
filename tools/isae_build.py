# -*- coding: utf-8 -*-
"""
Build script for "Die Aussendungseinheit" (Zeki.ISAE), a New Horizons addon for the normal solar system.

The Interstellare Sonden Aussendungseinheit (ISAE) is a copy of the Orbital Probe Cannon that orbits the sun,
surrounded by three small gravity cannons ("Fokuskanonen") in triangle formation. All four point along the
same axis (CANNON_AXIS). The player has to cut the three phase couplers and pull the main switch before the
loop ends - otherwise the C# part of the mod (Zeki.ISAE.Source) drains the sun instead of the supernova.

Generates: planets/*.json, systems/SolarSystem.json, terrain of the three focus rocks, ship log images,
manifests. The Nomai texts come from isae_texts.py, the ship log XML is written by hand.

Usage:  python tools/isae_build.py [path/to/Zeki.ISAE]
Needs:  Python 3.9+, numpy, Pillow
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import schleier_build as sb  # noqa: E402
from schleier_build import NH, P, Body, Planet, Site, color, norm, reveal, vec, write_json  # noqa: E402

MOD = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "Zeki.ISAE"))
sb.MOD = MOD  # the shared helpers write into this mod

NAME = "Interstellare Sonden Aussendungseinheit"
VERSION = "1.0.0"

# ----------------------------------------------------------------------------------------------
# Aim. Every body here has axialTilt 0 and siderealPeriod 0, so their local axes are the world axes
# and never turn. The focus cannons stand on the north pole of their rocks and therefore fire along
# world +y; the triangle orbits in the plane perpendicular to it.
# AIM_OPC turns the copied cannon so that its barrel points along +y as well. The barrel axis of the
# vanilla Orbital Probe Cannon in its own frame is not documented - if it points elsewhere in game,
# change these Euler angles (degrees, Unity order z-x-y) and rebuild, or edit the rotation of
# "ISAE_Hauptkanone" in planets/ISAE.json directly.
# ----------------------------------------------------------------------------------------------
AIM_OPC = (0.0, 0.0, 0.0)
AIM_GRAV_YAW = 0.0       # turns the gravity cannons around the firing axis
FOCUS_DISTANCE = 340     # metres between the main cannon and each focus cannon
FOCUS_NAMES = (("A", "Alpha", 0), ("B", "Beta", 120), ("C", "Gamma", 240))

# conditions (keep in sync with ZekiISAE.cs)
DEAKTIVIERT = "ZEKISAE_DEAKTIVIERT"      # persistent: the player switched the ISAE off
ENTDECKT = "ZEKISAE_ENTDECKT"            # persistent: the player has been at the ISAE once
ENTZUG = "ZEKISAE_ENTZUG"                # dialogue: set by the DLL while the sun is drained
KOPPLER = "ZEKISAE_KOPPLER_%s"           # persistent: one phase coupler cut
KOPPLER_ALLE = "ZEKISAE_KOPPLER_ALLE"    # persistent: all three cut, the main switch appears

# the control module of the Orbital Probe Cannon; spots inside it that are known to be free
# (the same ones the published addon "EyeWitness" uses in the vanilla cannon)
MODULE = "Sector_OrbitalProbeCannon/Sector_Module_Intact"
SPOT_PEDESTAL = (-8.881, -4.881, 8.7319)
SPOT_RECORDER = (-10.4348, -3.0591, 8.1713)
SPOT_COMPUTER = (-6.8811, -6.9297, 8.7142)
SPOT_ROT = (270, 0, 0)

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
def isae_config():
    hub = "Sector/ISAE_Hauptkanone"
    module = hub + "/Sector_Module_Intact"
    switch = module + "/ISAE_Hauptschalter"
    details = [
        # the whole cannon (hub, barrel, control and launch module). Components are stripped: only meshes and
        # colliders stay, so the copy cannot launch the real Nomai probe or fight the vanilla cannon's sectors.
        placed(P["opc_sector"], (0, 0, 0), AIM_OPC, rename="ISAE_Hauptkanone", keepLoaded=True, removeComponents=True,
               removeChildren=["Sector_Module_Intact/Interactables_Module_Intact", "Sector_Module_Broken/Interactables_Module_Broken"]),
        # its glowing heart - goes out when the ISAE is switched off
        placed(P["warp_particles"], (0, 0, 0), scale=5, rename="ISAE_Energiekern", keepLoaded=True,
               deactivationCondition=DEAKTIVIERT, blinkWhenActiveChanged=True),
        # the beam along the firing axis that appears when the drain begins
        placed(P["light_beam"], (0, 0, 0), scale=5, rename="ISAE_Entzugsstrahl", keepLoaded=True, activationCondition=ENTZUG),
        # the main switch inside the control module, wakes up once all three couplers are cut
        dict(relative(module, SPOT_PEDESTAL, SPOT_ROT), path="", rename="ISAE_Hauptschalter",
             activationCondition=KOPPLER_ALLE, deactivationCondition=DEAKTIVIERT),
        dict(relative(switch, (0, 1.2, 0)), path=P["warp_particles"], scale=0.35, rename="Schalterlicht"),
        dict(relative(switch, (0, 0, 0)), path=P["vessel_lamp"], rename="Schalterlampe"),
    ]
    texts = [
        dict(relative(module, SPOT_RECORDER, SPOT_ROT), type="recorder",
             xmlFile="planets/text/ISAE_Linum.xml", rename="Recorder_Linum"),
        dict(relative(module, SPOT_COMPUTER, SPOT_ROT), type="computer",
             xmlFile="planets/text/ISAE_Status.xml", rename="Computer_Status"),
        dict(relative(switch, (1.3, 0, 0)), type="trailmarker", xmlFile="planets/text/ISAE_Hauptschalter.xml", rename="Wegmarke_Hauptschalter"),
    ]
    volumes = {
        "interactionVolumes": [dict(relative(switch, (0, 1.2, 0)), radius=1.2, range=3, prompt="Aussendungseinheit abschalten",
                                    condition=DEAKTIVIERT, persistent=True, reusable=False, audio="NomaiPowerOff",
                                    rename="Hauptschalter_Volumen")],
        "revealVolumes": [
            reveal([0, 0, 0], 260, ["ZEKISAE_FOUND"]),
            reveal([0, 0, 0], 120, ["ZEKISAE_FOKUS_RUMOR"], "observe", maxDistance=2500, maxAngle=25),
        ],
    }
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
                         "position": vec([0, 0, 0]), "sourceRadius": 5, "detectionRadius": 7000, "identificationRadius": 400}],
            "entryLocation": [{"id": "ZEKISAE_ISAE", "position": vec([0, 0, 0])}, {"id": "ZEKISAE_SEDUM", "position": vec([0, 6, 0])}],
        },
        "Volumes": volumes,
    })
    return cfg


# ==============================================================================================
# the three focus cannons
# ==============================================================================================
def build_focus_rock(letter, greek, seed):
    p = Planet("fokus_" + letter.lower(), "Fokuskanone " + greek, 22.0, 27.0, seed, 512, 256)
    d = p.dirs
    h = 0.55 + 0.35 * p.noise.fbm(d, 5, 2.2) + 0.2 * p.noise.ridged(d, 3, 3.0)
    h = (h - h.min()) / (h.max() - h.min())
    p.add_site(Site("pad", 89.0, 0.0, 175, 12, 20))  # north pole = firing axis
    p.finish(h)
    return p


def focus_config(p, has_em, letter, greek, anomaly):
    b = Body(p)
    S = "pad"
    cond = KOPPLER % letter
    centre = p.at(S)
    b.detail("grav_cannon_bh", centre, AIM_GRAV_YAW, 0.55, f"Fokuskanone_{greek}_Struktur", keepLoaded=True)
    b.detail("light_beam", p.at(S, 0, 0, 4), 0, 2.5, f"Fokusstrahl_{greek}", ground=False, keepLoaded=True, activationCondition=ENTZUG)
    # the phase coupler: a glowing crystal while connected, a cracked one once cut
    kpos = p.at(S, -7, -3)
    yaw = p.facing(S, kpos)
    b.detail("gravity_crystal", kpos, yaw, 1.0, f"Phasenkoppler_{greek}", deactivationCondition=cond, blinkWhenActiveChanged=True)
    b.detail("crystal_cracked", kpos, yaw, 1.0, f"Phasenkoppler_{greek}_getrennt", activationCondition=cond)
    b.detail("warp_particles", kpos + norm(kpos) * 2.2, 0, 0.3, f"Kopplerlicht_{greek}", ground=False, deactivationCondition=cond)
    pos = p.at(S, 7, 3)
    b.text("computer", f"Fokus_{greek}.xml", pos, p.facing(S, pos), f"Computer_Fokus_{greek}")
    for i, (e, n) in enumerate(p.ring(S, 12, 4, 45)):
        b.detail("lamp_flare", p.at(S, e, n), 0, 1.0, f"Fokuslampe_{greek}_{i + 1}")
    b.vol("interactionVolumes", {"position": vec(kpos + norm(kpos) * 1.2), "radius": 1.5, "range": 3, "prompt": "Phasenkoppler trennen",
                                 "condition": cond, "persistent": True, "reusable": False, "audio": "NomaiPowerSwitch",
                                 "rename": f"Koppler_{greek}_Volumen"})
    b.vol("revealVolumes", reveal(p.at(S, up=3), 30, ["ZEKISAE_FOKUS_FOUND"]))
    if letter == "A":
        b.prop("entryLocation", {"id": "ZEKISAE_FOKUS", "position": vec(p.at(S, up=3))})
    cfg = sb.body_header(p.name, "SolarSystem")
    cfg.update({
        "canShowOnTitle": False,
        "Base": {"surfaceSize": p.hmax, "surfaceGravity": 4, "gravityFallOff": "linear", "showMinimap": False},
        # same circle, 120 degrees apart: the triangle keeps its shape while it turns around the main cannon
        "Orbit": {"primaryBody": NAME, "isMoon": True, "semiMajorAxis": FOCUS_DISTANCE, "eccentricity": 0, "inclination": 0,
                  "longitudeOfAscendingNode": 0, "argumentOfPeriapsis": 0, "trueAnomaly": anomaly, "axialTilt": 0, "siderealPeriod": 0,
                  "dottedOrbitLine": True, "tint": RED[1]},
        "HeightMap": sb.heightmap_module(p, has_em, 0.1, 0.2),
        "MapMarker": {"enabled": True},
        "ShipLog": {"mapMode": {"remove": True}},
        "Props": {"details": b.details, "translatorText": b.texts, **b.props},
        "Volumes": b.volumes,
    })
    return cfg


# ==============================================================================================
# the hint inside the real Orbital Probe Cannon
# ==============================================================================================
def opc_config():
    cfg = sb.body_header("ORBITAL_PROBE_CANNON", "SolarSystem")
    cfg["Props"] = {"translatorText": [dict(relative(MODULE, SPOT_COMPUTER, SPOT_ROT), type="computer",
                                            xmlFile="planets/text/OPC_Sedum.xml", rename="Computer_Sedum")]}
    return cfg


def solar_system():
    entries = {"ZEKISAE_ISAE": (1650, 450), "ZEKISAE_FOKUS": (2100, 700), "ZEKISAE_SEDUM": (2100, 200)}
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
            "drainSeconds": {"type": "slider", "value": 45, "min": 10, "max": 180, "title": "Dauer des Energieentzugs (Sekunden)",
                             "tooltip": "Wie lange die Sonne am Ende der Schleife schrumpft, bevor sie erlischt."},
        },
    })
    write_json("addon-manifest.json", {
        "$schema": NH + "addon_manifest_schema.json",
        "credits": ["Zeki"],
        "popupMessage": "Die Aussendungseinheit: Irgendwo zwischen der Sonne und den Sanduhr-Zwillingen erwacht eine Nomai-Maschine. "
                        "Wenn du nichts tust, endet diese Schleife nicht mit einer Supernova.",
        "gameOver": [{"text": "Das Universum endet, aber du endest vor ihm...", "condition": "ZEKISAE_UNIVERSUM_ENDET",
                      "colour": color(255, 120, 70), "creditsType": "fast"}],
    })


def main():
    rocks = {x: build_focus_rock(x, greek, 7100 + i) for i, (x, greek, _) in enumerate(FOCUS_NAMES)}
    em = {x: sb.textures(p, "fokus") for x, p in rocks.items()}

    write_json("planets/ISAE.json", isae_config())
    for x, greek, anomaly in FOCUS_NAMES:
        write_json(f"planets/Fokuskanone_{greek}.json", focus_config(rocks[x], em[x], x, greek, anomaly))
    write_json("planets/OrbitalProbeCannon.json", opc_config())
    write_json("systems/SolarSystem.json", solar_system())
    manifests()

    E = "planets/assets/shiplog/entries/"
    for entry, motif, seed in (("ZEKISAE_ISAE", "isae", 31), ("ZEKISAE_FOKUS", "fokus", 32), ("ZEKISAE_SEDUM", "sedum", 33)):
        sb.save(art(seed, motif), E + entry + ".png")
    img, outline = map_sprite()
    sb.save(img, "planets/assets/shiplog/map/isae.png")
    sb.save(outline, "planets/assets/shiplog/map/isae_outline.png")

    for x, p in rocks.items():
        s = p.sites["pad"]
        print(f"{p.name:22s} pad radius {p.radius_of(s.level):6.2f} m")


if __name__ == "__main__":
    main()
