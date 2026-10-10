# -*- coding: utf-8 -*-
"""
Build script for "Die Aussendungseinheit" (Zeki.ISAE), a New Horizons addon for the normal solar system.

The Interstellare Sonden Aussendungseinheit (ISAE) is a huge, menacing descendant of the Orbital Probe Cannon
(Blender model, tools/isae_models.py) that orbits the sun and aims at it. Around its barrel circle three focus
cannons; the real modules of the Orbital Probe Cannon hang on its arms. Everything that exists in the game is
copied from the game. The player has to cut the three phase couplers and pull the main switch before the loop
ends - otherwise the C# part of the mod (Zeki.ISAE.Source) drains the sun instead of the supernova.

Hierarchy inside the ISAE body (the DLL turns and moves these at runtime, see GameProps.cs):
    Sector/ISAE_Ausrichtung                      pivot, +y aims at the sun
        Blender cannon, core chamber             (placements.json)
        ISAE_Modul_Kontrolle/Start/Navigation    copies of the real OPC module, mounted on the arms
        ISAE_Fokuskreis                          turns slowly around the barrel
            Fokus_Alpha/Beta/Gamma               gravity cannon of Ember Twin + Blender emitter frame

Generates: planets/*.json (the ISAE and lore on four vanilla planets), systems/SolarSystem.json,
assets/models/placements.json, ship log images, manifests. Needs assets/models/anchors.json from
isae_models.py. The Nomai texts come from isae_texts.py, the ship log from isae_shiplog.py.

Usage:  python tools/isae_build.py [path/to/Zeki.ISAE]
Needs:  Python 3.9+, numpy, Pillow
"""
import glob
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
VERSION = "1.4.0"
FOCUS_NAMES = (("A", "Alpha"), ("B", "Beta"), ("C", "Gamma"))
MODULES = (("kontrolle", "Kontrolle"), ("start", "Start"), ("navigation", "Navigation"))

PIVOT = "Sector/ISAE_Ausrichtung"
CIRCLE = PIVOT + "/ISAE_Fokuskreis"

# conditions (keep in sync with ZekiISAE.cs)
DEAKTIVIERT = "ZEKISAE_DEAKTIVIERT"      # persistent: the player switched the ISAE off
ENTDECKT = "ZEKISAE_ENTDECKT"            # persistent: the player has been at the ISAE once
ENTZUG = "ZEKISAE_ENTZUG"                # dialogue: set by the DLL while the sun is drained
VORBOTE = "ZEKISAE_VORBOTE"              # dialogue: set by the DLL two minutes before the end of the loop
KOPPLER = "ZEKISAE_KOPPLER_%s"           # persistent: one phase coupler cut
KOPPLER_ALLE = "ZEKISAE_KOPPLER_ALLE"    # persistent: all three cut, the main switch appears

# free spots in the control module of the real Orbital Probe Cannon (used by the published addon EyeWitness);
# the same spots work in our copies of that module. "Up" of the pedestal spot is -z of the module.
SPOT_PEDESTAL = (-8.881, -4.881, 8.7319)
SPOT_RECORDER = (-10.4348, -3.0591, 8.1713)
SPOT_COMPUTER = (-6.8811, -6.9297, 8.7142)
SPOT_ROT = (270, 0, 0)
OPC_MODULE = "Sector_OrbitalProbeCannon/Sector_Module_Intact"

RED = (color(235, 90, 50), color(255, 170, 120))


def rot(e):
    return vec(e, 1)


def placed(path, pos, rotation=(0, 0, 0), **extra):
    d = {"path": path, "position": vec(pos), "rotation": rot(rotation)}
    d.update(extra)
    return d


def relative(parent, pos, rotation=(0, 0, 0), **extra):
    d = {"parentPath": parent, "isRelativeToParent": True, "position": vec(pos), "rotation": rot(rotation)}
    d.update(extra)
    return d


def add(a, b):
    return [a[0] + b[0], a[1] + b[1], a[2] + b[2]]


def anchors():
    """Spots on the Blender models (Unity coordinates), written by tools/isae_models.py."""
    with open(os.path.join(MOD, "assets", "models", "anchors.json"), encoding="utf-8") as f:
        return json.load(f)


def at(a, up=0.0):
    p = a["position"]
    return [p["x"], p["y"] + up, p["z"]]


def yaw(a, extra=0.0):
    return (0, round((a.get("yaw", 0) + extra) % 360, 1), 0)


# ==============================================================================================
# the ISAE
# ==============================================================================================
def module_path(name):
    return f"{PIVOT}/ISAE_Modul_{name}"


def focus_path(greek):
    return f"{CIRCLE}/Fokus_{greek}"


def isae_config(A):
    I, K, F = A["isae"], A["kammer"], A["fokus"]
    details = [
        # the pivot the DLL aims at the sun, and the circle of the focus cannons
        placed("", (0, 0, 0), rename="ISAE_Ausrichtung", keepLoaded=True),
        relative(PIVOT, (0, 0, 0), path="", rename="ISAE_Fokuskreis", keepLoaded=True),
    ]
    details += [relative(CIRCLE, at(I[f"fokus_{x}"]), path="", rename=f"Fokus_{greek}", keepLoaded=True) for x, greek in FOCUS_NAMES]
    # the real modules of the Orbital Probe Cannon on the ends of the arms (the DLL poses them like on the real cannon)
    details += [relative(PIVOT, at(I[f"modul_{key}"]), path=P["opc_module_intact"], rename=f"ISAE_Modul_{name}", keepLoaded=True,
                         removeChildren=["Interactables_Module_Intact"]) for key, name in MODULES]
    details += [
        # the lens between the claws glows until the ISAE is switched off; two minutes before the end the
        # muzzle flares up, during the drain a beam leaves the lens towards the sun
        relative(PIVOT, at(I["linse"]), path=P["warp_particles"], scale=9, rename="ISAE_Linsenglut", keepLoaded=True,
                 deactivationCondition=DEAKTIVIERT, blinkWhenActiveChanged=True),
        relative(PIVOT, at(I["muendung"]), path=P["warp_particles"], scale=5, rename="ISAE_Muendungsglut", keepLoaded=True, activationCondition=VORBOTE),
        relative(PIVOT, at(I["linse"]), path=P["light_beam"], scale=10, rename="ISAE_Entzugsstrahl", keepLoaded=True, activationCondition=ENTZUG),
        # core chamber: Sedum's remains in front of the burning heart
        relative(PIVOT, at(K["sedum"]), yaw(K["sedum"]), path=P["skeleton"], rename="Sedums_Ueberreste"),
        relative(PIVOT, at(K["sedum"], 0.05), (0, (K["sedum"]["yaw"] + 70) % 360, 90), path=P["staff"], rename="Sedums_Stab"),
    ]
    details += [relative(PIVOT, at(K[f"lampe{i}"]), path=P["lamp_flare"], rename=f"Kammerlampe_{i}") for i in (1, 2, 3)]

    # inside the modules (frames of the module copies)
    kontrolle, start, navigation = (module_path(n) for _, n in MODULES)
    switch = kontrolle + "/ISAE_Hauptschalter"
    pedestal_up = lambda h: add(SPOT_PEDESTAL, (0, 0, -h))  # noqa: E731
    details += [
        # the main switch, wakes up once all three couplers are cut: the Vessel's coordinate interface with an
        # advanced warp core floating above it (Vessel technology that Sedum copied)
        relative(kontrolle, SPOT_PEDESTAL, SPOT_ROT, path="", rename="ISAE_Hauptschalter", activationCondition=KOPPLER_ALLE,
                 deactivationCondition=DEAKTIVIERT),
        relative(switch, (0, 0, 0), path=P["vessel_interface"], scale=0.7, rename="Hauptschalter_Vessel_Interface"),
        # removeComponents strips the item from the root, so the copy can not be picked up like the real core
        relative(switch, (0, 2.3, 0), path=P["warpcore_vessel"], rename="Hauptschalter_Warpkern", removeComponents=True),
        # the interstellar probe waits in the launch module; the DLL fires it through the barrel in the finale
        relative(start, pedestal_up(1.2), path=P["nomai_probe"], rename="Interstellare_Sonde", keepLoaded=True),
    ]
    texts = [
        relative(kontrolle, SPOT_COMPUTER, SPOT_ROT, type="computer", xmlFile="planets/text/ISAE_Status.xml", rename="Computer_Status"),
        relative(kontrolle, SPOT_RECORDER, SPOT_ROT, type="recorder", xmlFile="planets/text/ISAE_Linum.xml", rename="Recorder_Linum"),
        relative(switch, (2.0, 0, 0), type="trailmarker", xmlFile="planets/text/ISAE_Hauptschalter.xml", rename="Wegmarke_Hauptschalter"),
        relative(start, SPOT_COMPUTER, SPOT_ROT, type="computer", xmlFile="planets/text/Start_Sonde.xml", rename="Computer_Sonde"),
        relative(start, SPOT_RECORDER, SPOT_ROT, type="recorder", xmlFile="planets/text/Start_Bau.xml", rename="Recorder_Bau"),
        relative(navigation, SPOT_COMPUTER, SPOT_ROT, type="computer", xmlFile="planets/text/Navi_Ziel.xml", rename="Computer_Ziel"),
        relative(navigation, SPOT_RECORDER, SPOT_ROT, type="recorder", xmlFile="planets/text/Navi_Pye.xml", rename="Recorder_Pye"),
        relative(PIVOT, at(K["computer"]), yaw(K["computer"]), type="computer", xmlFile="planets/text/Sedum_Abschied.xml", rename="Computer_Sedum"),
        relative(PIVOT, at(K["recorder"]), yaw(K["recorder"]), type="recorder", xmlFile="planets/text/Kammer_Zweifel.xml", rename="Recorder_Zweifel"),
    ]
    volumes = {
        "interactionVolumes": [relative(switch, (0, 1.4, 0), radius=1.6, range=3, prompt="Aussendungseinheit abschalten", condition=DEAKTIVIERT,
                                        persistent=True, reusable=False, audio="NomaiPowerOff", rename="Hauptschalter_Volumen")],
        "revealVolumes": [
            reveal([0, 0, 0], 1300, ["ZEKISAE_FOUND"]),
            reveal([0, 0, 0], 450, ["ZEKISAE_FOKUS_RUMOR"], "observe", maxDistance=4000, maxAngle=25),
            dict(reveal(at(K["boden"], 3), 24, ["ZEKISAE_KERN_FOUND"]), parentPath=PIVOT, isRelativeToParent=True),
        ] + [dict(reveal(SPOT_COMPUTER, 12, [f"ZEKISAE_{fact}_FOUND"]), parentPath=module_path(name), isRelativeToParent=True)
             for (_, name), fact in zip(MODULES, ("KONTROLLE", "START", "NAVI"))],
        "forces": {"directionalVolumes": [
            # Nomai gravity towards the floor of the core chamber
            relative(PIVOT, at(K["boden"], K["hoehe"] / 2), force=9, normal=vec([0, -1, 0]),
                     shape={"type": "cylinder", "radius": K["bodenRadius"] - 0.3, "height": K["hoehe"] - 0.4}, rename="Schwerkraft_Kernkammer"),
        ]},
    }
    entries = [
        relative(PIVOT, at(I["kern"], 80), id="ZEKISAE_ISAE"),
        relative(PIVOT, at(K["boden"], 3), id="ZEKISAE_KERN"),
        relative(PIVOT, at(K["sedum"], 1), id="ZEKISAE_SEDUM"),
    ] + [relative(module_path(name), SPOT_PEDESTAL, id=entry) for (_, name), entry in zip(MODULES, ("ZEKISAE_KONTROLLE", "ZEKISAE_START", "ZEKISAE_NAVI"))]
    for e in entries:
        e.pop("rotation", None)

    # the three focus cannons
    for x, greek in FOCUS_NAMES:
        focus_props(F, x, greek, details, texts, volumes, entries)

    cfg = sb.body_header(NAME, "SolarSystem")
    cfg.update({
        "canShowOnTitle": False,
        # zero-g like the real probe cannon; the core chamber and the focus decks have their own Nomai gravity
        "Base": {"surfaceSize": 500, "surfaceGravity": 0, "showMinimap": False},
        # between the Hourglass Twins (5000 m) and Timber Hearth (8600 m), far out of the planets' plane
        "Orbit": {"primaryBody": "Sun", "semiMajorAxis": 6400, "eccentricity": 0, "inclination": 62, "longitudeOfAscendingNode": 35,
                  "trueAnomaly": 210, "axialTilt": 0, "siderealPeriod": 0, "tint": RED[0]},
        "MapMarker": {"enabled": True},
        "ShipLog": {"xmlFile": "planets/shiplogs/ISAE.xml", "spriteFolder": "planets/assets/shiplog/entries",
                    "mapMode": {"revealedSprite": "planets/assets/shiplog/map/isae.png",
                                "outlineSprite": "planets/assets/shiplog/map/isae_outline.png", "scale": 1.4}},
        "Props": {
            "details": details,
            "translatorText": texts,
            "signals": [{"frequency": "Energiesignaturen", "name": "Aussendungseinheit", "audio": "OW_NM_WhiteHoleAmbienceL",
                         "position": vec([0, 0, 0]), "sourceRadius": 20, "detectionRadius": 9000, "identificationRadius": 900}],
            "entryLocation": entries,
        },
        "Volumes": volumes,
    })
    return cfg


def focus_props(F, letter, greek, details, texts, volumes, entries):
    """A focus cannon: the gravity cannon of Ember Twin (the DLL puts its launch platform at the origin) inside the
    Blender emitter frame. Linum hid the three phase couplers: Alpha's on the deck, Beta's on the small platform
    under the emitter, Gamma's under the keel."""
    path = focus_path(greek)
    cond = KOPPLER % letter
    details += [
        relative(path, (0, 0, 0), path=P["gravity_cannon"], rename=f"Fokuskanone_{greek}_Struktur", keepLoaded=True),
        relative(path, at(F["emitter"]), path=P["light_beam"], scale=3, rename=f"Fokusstrahl_{greek}", keepLoaded=True, activationCondition=ENTZUG),
        relative(path, at(F["emitter"]), path=P["warp_particles"], scale=1.6, rename=f"Emitterglut_{greek}", keepLoaded=True,
                 deactivationCondition=cond, blinkWhenActiveChanged=True),
    ]
    details += [relative(path, at(F[f"tor{i}"]), yaw(F[f"tor{i}"]), path=P["doorway"], rename=f"Fokustor_{greek}_{i}") for i in (1, 2, 3)]
    details += [relative(path, at(F[f"lampe{i}"]), path=P["lamp_flare"], rename=f"Fokuslampe_{greek}_{i}") for i in (1, 2, 3)]
    if letter == "A":
        spot, rotation, up = at(F["koppler_deck"]), yaw(F["koppler_deck"]), 1.0
    elif letter == "B":
        spot, rotation, up = at(F["koppler_oben"]), yaw(F["koppler_oben"]), 1.0
    else:  # hanging under the keel platform, upside down
        spot, rotation, up = at(F["unten"]), (180, 0, 0), -1.0
    details += [
        # the phase coupler: a glowing gravity crystal while connected, a cracked one once cut
        relative(path, spot, rotation, path=P["gravity_crystal"], rename=f"Phasenkoppler_{greek}", deactivationCondition=cond,
                 blinkWhenActiveChanged=True),
        relative(path, spot, rotation, path=P["crystal_cracked"], rename=f"Phasenkoppler_{greek}_getrennt", activationCondition=cond),
        relative(path, add(spot, (0, 2.2 * up, 0)), path=P["warp_particles"], scale=0.3, rename=f"Kopplerlicht_{greek}", deactivationCondition=cond),
    ]
    texts += [
        relative(path, at(F["computer"]), yaw(F["computer"]), type="computer", xmlFile=f"planets/text/Fokus_{greek}.xml", rename=f"Computer_Fokus_{greek}"),
        relative(path, at(F["recorder"]), yaw(F["recorder"]), type="recorder",
                 xmlFile=f"planets/text/Fokus_{greek}_{dict(A='Erica', B='Sedum', C='Linum')[letter]}.xml", rename=f"Recorder_Fokus_{greek}"),
    ]
    volumes["interactionVolumes"].append(relative(path, add(spot, (0, 1.0 * up, 0)), radius=1.6, range=3, prompt="Phasenkoppler trennen",
                                                  condition=cond, persistent=True, reusable=False, audio="NomaiPowerSwitch",
                                                  rename=f"Koppler_{greek}_Volumen"))
    volumes["revealVolumes"].append(dict(reveal([0, 3, 0], 45, ["ZEKISAE_FOKUS_FOUND"]), parentPath=path, isRelativeToParent=True))
    # Nomai gravity over the deck, and over the small platform under the emitter
    volumes["forces"]["directionalVolumes"].append(relative(path, (0, 12, 0), force=9, normal=vec([0, -1, 0]),
                                                            shape={"type": "cylinder", "radius": F["deckRadius"] + 0.5, "height": 24},
                                                            rename=f"Deckschwerkraft_{greek}"))
    top = at(F["oben"])
    volumes["forces"]["directionalVolumes"].append(relative(path, add(top, (0, 2.5, 0)), force=9, normal=vec([0, -1, 0]),
                                                            shape={"type": "cylinder", "radius": 7.5, "height": 5},
                                                            rename=f"Emitterschwerkraft_{greek}"))
    if letter == "A":
        e = relative(path, (0, 3, 0), id="ZEKISAE_FOKUS")
        e.pop("rotation")
        entries.append(e)


def placements(A):
    """assets/models/placements.json: where the DLL puts the Blender models."""
    F, K, I = A["fokus"], A["kammer"], A["isae"]
    props = [
        {"model": "hauptkanone", "name": "ISAE_Hauptkanone", "parentPath": PIVOT, "collider": True},
        {"model": "laufringe", "name": "ISAE_Laufringe", "parentPath": PIVOT, "spin": 6},
        {"model": "kernkammer", "name": "ISAE_Kernkammer", "parentPath": PIVOT, "collider": True},
        {"model": "kernringe", "name": "ISAE_Kernringe", "parentPath": PIVOT, "spin": 24},
        {"model": "sternkarte", "name": "ISAE_Sternkarte", "parentPath": module_path("Navigation"), "spin": 7,
         "position": vec(add(SPOT_PEDESTAL, (0, 0, -1.8)))},
    ]
    props += [{"model": "fokusgeruest", "name": f"Fokus_{greek}_Geruest", "parentPath": focus_path(greek), "collider": True} for _, greek in FOCUS_NAMES]
    for p in props:
        p["body"] = NAME
        p.setdefault("position", {"x": 0, "y": 0, "z": 0})
        p.setdefault("rotation", {"x": 0, "y": 0, "z": 0})
        p.setdefault("scale", 1)
    lights = [{"name": "Licht_Kernkammer", "body": NAME, "parentPath": PIVOT, "position": K["licht"]["position"],
               "color": {"x": 1.0, "y": 0.42, "z": 0.2}, "range": 45, "intensity": 2.2}]
    lights += [{"name": f"Licht_Emitter_{greek}", "body": NAME, "parentPath": focus_path(greek), "position": F["emitter"]["position"],
                "color": {"x": 1.0, "y": 0.4, "z": 0.18}, "range": 70, "intensity": 1.6} for _, greek in FOCUS_NAMES]
    points = {k: I[k]["position"] for k in ("kern", "linse", "muendung", "heck")}
    points.update({f"modul_{key}": I[f"modul_{key}"]["position"] for key, _ in MODULES})
    points.update({f"fokus_{x}": I[f"fokus_{x}"]["position"] for x, _ in FOCUS_NAMES})
    points["fokus_emitter"] = F["emitter"]["position"]
    return {
        # exact names of game materials for the Blender material slots; empty = taken from the Vessel
        "materials": {"VesselHuelle": "", "VesselKupfer": "", "VesselDunkel": "", "VesselGlut": "", "VesselLeuchten": ""},
        "props": props,
        "lights": lights,
        "points": points,
    }


# ==============================================================================================
# lore on other planets: free-standing recorders on spots that the published addon "fretsquest" uses,
# moved 1.6 m to the side so both mods can be installed together
# ==============================================================================================
PLANET_TEXTS = (
    ("CAVE_TWIN", "EmberTwin.json", "ET_Erica.xml", (29.72448, 74.84678, -103.482307), (35.5034676, 223.8678, 50.4576759)),
    ("TIMBER_MOON", "Attlerock.json", "Attlerock_Linum.xml", (67.47436, -14.0237, -2.56409764), (63.88444, 2.44039726, 242.222137)),
    ("GIANTS_DEEP", "GiantsDeep.json", "GD_Linum.xml", (-18.2838669, -12.0357161, -20.678772), (316.378784, 295.374451, 3.15194845)),
    ("BRITTLE_HOLLOW", "BrittleHollow.json", "BH_Pye.xml", (103.556, 283.8265, -29.1108), (9.3106, 163.9927, 17.8658)),
)


def euler_x_axis(e):
    """Local x axis of a Unity Euler rotation (applied z, x, y)."""
    x, y, z = (math.radians(a) for a in e)
    # R = Ry * Rx * Rz applied to (1, 0, 0)
    v = (math.cos(z), math.sin(z), 0.0)
    v = (v[0], v[1] * math.cos(x) - v[2] * math.sin(x), v[1] * math.sin(x) + v[2] * math.cos(x))
    return (v[0] * math.cos(y) + v[2] * math.sin(y), v[1], -v[0] * math.sin(y) + v[2] * math.cos(y))


def planet_config(body, xml, pos, rotation):
    side = euler_x_axis(rotation)
    cfg = sb.body_header(body, "SolarSystem")
    cfg["Props"] = {"translatorText": [{"type": "recorder", "xmlFile": "planets/text/" + xml,
                                        "position": vec([pos[i] + side[i] * 1.6 for i in range(3)]), "rotation": rot(rotation),
                                        "rename": "Aussendungseinheit_" + xml[:-4]}]}
    return cfg


def opc_config():
    cfg = sb.body_header("ORBITAL_PROBE_CANNON", "SolarSystem")
    cfg["Props"] = {"translatorText": [relative(OPC_MODULE, SPOT_COMPUTER, SPOT_ROT, type="computer", xmlFile="planets/text/OPC_Sedum.xml",
                                                rename="Computer_Sedum")]}
    return cfg


def solar_system():
    entries = {"ZEKISAE_ISAE": (1650, 450), "ZEKISAE_KONTROLLE": (2080, 640), "ZEKISAE_KERN": (2080, 260), "ZEKISAE_START": (2500, 780),
               "ZEKISAE_NAVI": (2500, 470), "ZEKISAE_FOKUS": (1650, 880), "ZEKISAE_SEDUM": (1650, 30), "ZEKISAE_SPUREN": (1220, 450)}
    checks = [
        {"check": {"allFactsRevealed": ["ZEKISAE_FOUND"]}, "then": {"setPersistentConditions": [ENTDECKT]}},
        {"check": {"allPersistentConditionsSet": [KOPPLER % x for x, _ in FOCUS_NAMES]}, "then": {"setPersistentConditions": [KOPPLER_ALLE]}},
    ]
    checks += [{"check": {"allPersistentConditionsSet": [KOPPLER % x]}, "then": {"revealFacts": [f"ZEKISAE_KOPPLER_{x}_FACT"]}} for x, _ in FOCUS_NAMES]
    checks.append({"check": {"allPersistentConditionsSet": [DEAKTIVIERT]}, "then": {"revealFacts": ["ZEKISAE_ABGESCHALTET"]}})
    return {
        "$schema": NH + "star_system_schema.json",
        "initialReveal": ["ZEKISAE_SIGNATUR"],
        "curiosities": [{"id": "ZEKISAE_ISAE", "color": RED[0], "highlightColor": RED[1]}],
        "entryPositions": [{"id": k, "position": {"x": v[0], "y": v[1]}} for k, v in entries.items()],
        "conditionalChecks": checks,
    }


# ==============================================================================================
# images (ZEKISAE_ISAE, _FOKUS, _KERN and the map sprite are Blender renders, see isae_models.py)
# ==============================================================================================
def art(seed, motif, size=512):
    img = sb.starfield(size, seed, tint=(255, 110, 70))
    d = ImageDraw.Draw(img)
    c = size / 2
    if motif == "sedum":
        for k, r in enumerate((150, 110, 70)):
            col = (255, 190 - k * 50, 90 - k * 25, 255)
            d.ellipse([c - r, c - r, c + r, c + r], outline=col, width=6)
        d.ellipse([c - 30, c - 30, c + 30, c + 30], fill=(40, 20, 20, 255), outline=(255, 120, 70, 255), width=4)
        sb.spiral(d, c - 120, c + 150, 55, 2.0, 4, (240, 200, 120, 255))
        sb.spiral(d, c + 120, c + 150, 55, 2.0, 4, (170, 210, 255, 255), reverse=True)
    elif motif == "kontrolle":
        # the module with the Vessel interface and the warp core above it
        d.ellipse([c - 170, c - 120, c + 170, c + 150], fill=(70, 52, 44, 255), outline=(200, 130, 80, 255), width=6)
        d.ellipse([c - 40, c - 120, c + 40, c - 40], fill=(255, 245, 235, 255), outline=(170, 220, 255, 255), width=6)
        for k in range(3):
            a = math.radians(90 + k * 120)
            d.line([(c, c + 60), (c + 90 * math.cos(a), c + 60 + 50 * math.sin(a))], fill=(200, 160, 110, 255), width=10)
        d.ellipse([c - 30, c + 30, c + 30, c + 90], fill=(150, 110, 80, 255), outline=(255, 200, 150, 255), width=4)
    elif motif == "start":
        # the probe waiting for the shot, the barrel above it
        d.rectangle([c - 26, 0, c + 26, c - 70], fill=(255, 120, 60, 200))
        d.polygon([(c, c - 70), (c - 34, c + 30), (c - 22, c + 120), (c + 22, c + 120), (c + 34, c + 30)], fill=(190, 180, 175, 255), outline=(255, 230, 210, 255))
        for dx in (-60, 60):
            d.polygon([(c + dx * 0.5, c + 60), (c + dx, c + 140), (c + dx * 0.4, c + 120)], fill=(120, 110, 110, 255))
        d.ellipse([c - 18, c + 110, c + 18, c + 146], fill=(255, 170, 90, 255))
    elif motif == "navi":
        # the star chart: the target star behind the nebula of the Eye
        for k, (r, tilt) in enumerate(((90, 0.35), (140, 0.5), (190, 0.25))):
            d.ellipse([c - r, c - r * tilt * 2, c + r, c + r * tilt * 2], outline=(150, 210, 255, 220), width=3)
        d.ellipse([c - 16, c - 16, c + 16, c + 16], fill=(200, 235, 255, 255))
        for k in range(18):
            a, r = math.radians(k * 137.5), 60 + (k * 37) % 170
            x, y = c + r * math.cos(a), c + r * math.sin(a) * 0.5
            d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=(170, 220, 255, 255))
        d.line([(c, c), (c + 150, c - 110), (c + 210, c - 190)], fill=(255, 190, 120, 255), width=4)
    elif motif == "spuren":
        d.ellipse([c - 40, c - 40, c + 40, c + 40], fill=(255, 150, 70, 255))
        planets = [(150, 30, (210, 120, 80)), (230, 140, (140, 160, 110)), (300, 250, (90, 140, 180)), (205, 320, (120, 100, 150))]
        for k, (r, a, col) in enumerate(planets):
            x, y = c + r * math.cos(math.radians(a)), c + r * math.sin(math.radians(a))
            d.ellipse([c - r, c - r, c + r, c + r], outline=(120, 70, 50, 255), width=2)
            d.ellipse([x - 16, y - 16, x + 16, y + 16], fill=col + (255,))
            sb.spiral(d, x + 26, y - 22, 12, 1.6, 2, (255, 200, 140, 255), reverse=k % 2 == 1)
    return img


def outline_sprite(size=256):
    outline = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(outline).ellipse([3, 3, size - 4, size - 4], outline=(255, 255, 255, 255), width=5)
    return outline


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
            "showOnTitle": {"type": "toggle", "value": True, "title": "Kanone im Hauptmenü",
                            "tooltip": "Zeigt die Aussendungseinheit am Himmel des Titelbildschirms."},
            "materialSource": {"type": "selector", "value": "Vessel", "options": ["Vessel", "Sondenkanone", "Einfach"],
                               "title": "Materialien der Hauptkanone",
                               "tooltip": "Vessel: die Materialien des Vessels. Sondenkanone: die der echten Sondenkanone. Einfach: schlichte Farben."},
        },
    })
    write_json("addon-manifest.json", {
        "$schema": NH + "addon_manifest_schema.json",
        "credits": ["Zeki"],
        "popupMessage": "Die Aussendungseinheit: Zwischen der Sonne und Timber Hearth zielt eine riesige Nomai-Kanone auf die Sonne. "
                        "Wenn du nichts tust, endet diese Schleife nicht mit einer Supernova.",
        "gameOver": [{"text": "Das Universum endet, aber du endest vor ihm...", "condition": "ZEKISAE_UNIVERSUM_ENDET",
                      "colour": color(255, 120, 70),
                      # custom = the credits roll with the game's final music, but without the Big Bang epilogue
                      "creditsType": "custom", "audio": "FinalCredits", "length": 110}],
    })


def main():
    A = anchors()
    write_json("planets/ISAE.json", isae_config(A))
    write_json("planets/OrbitalProbeCannon.json", opc_config())
    for body, filename, xml, pos, rotation in PLANET_TEXTS:
        write_json("planets/" + filename, planet_config(body, xml, pos, rotation))
    write_json("systems/SolarSystem.json", solar_system())
    write_json("assets/models/placements.json", placements(A))
    manifests()

    E = "planets/assets/shiplog/entries/"
    for entry, motif, seed in (("ZEKISAE_SEDUM", "sedum", 33), ("ZEKISAE_SPUREN", "spuren", 34), ("ZEKISAE_KONTROLLE", "kontrolle", 35),
                               ("ZEKISAE_START", "start", 36), ("ZEKISAE_NAVI", "navi", 37)):
        sb.save(art(seed, motif), E + entry + ".png")
    sb.save(outline_sprite(), "planets/assets/shiplog/map/isae_outline.png")
    # left-overs of older versions: rocks (1.0) and separate focus cannon bodies (1.0 - 1.3)
    terrain = os.path.join(MOD, "planets", "assets", "terrain")
    if os.path.isdir(terrain):
        shutil.rmtree(terrain)
    for old in glob.glob(os.path.join(MOD, "planets", "Fokuskanone_*.json")):
        os.remove(old)


if __name__ == "__main__":
    main()
