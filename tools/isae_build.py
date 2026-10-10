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
VERSION = "1.5.0"
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
SAMEN_GENOMMEN = "ZEKISAE_SAMEN_GENOMMEN"      # dialogue: the Samenkern was taken out of the seed chamber
SAMEN_EINGESETZT = "ZEKISAE_SAMEN_EINGESETZT"  # dialogue: the Samenkern lies in the Pulskern, the roots grow
ENDE_RISS = "ZEKISAE_ENDE_RISS"                # dialogue: ending 2 (set by the DLL right before the game over)
ENDE_WURZEL = "ZEKISAE_ENDE_WURZEL"            # dialogue: ending 3
UNIVERSUM_ENDET = "ZEKISAE_UNIVERSUM_ENDET"    # dialogue: ending 1

KEIMDORN = "Keimdorn"          # the small bramble seed planet around Dark Bramble
SAMENKAMMER = "Samenkammer"    # the small bramble dimension inside it
KEIM_NODE = "ZEKISAE_Keimdorn_Knoten"
BABY_NODE = "ZEKISAE_Babysamen_Knoten"
SAMENKERN = "Sector/ZEKISAE_Samenkern"
GREEN = (color(110, 255, 140), color(200, 255, 190))

# free spots in the control module of the real Orbital Probe Cannon (used by the published addon EyeWitness);
# the same spots work in our copies of that module. "Up" of the pedestal spot is -z of the module.
SPOT_PEDESTAL = (-8.881, -4.881, 8.7319)
SPOT_RECORDER = (-10.4348, -3.0591, 8.1713)
SPOT_COMPUTER = (-6.8811, -6.9297, 8.7142)
SPOT_ROT = (270, 0, 0)
OPC_MODULE = "Sector_OrbitalProbeCannon/Sector_Module_Intact"

RED = (color(235, 90, 50), color(255, 170, 120))

# projection pools: id -> (decal, where the platform is, where the stones lie); the module pools are the
# pools of the module copies (the DLL moves the NH platforms onto them and switches the copied pools off)
REMOTES = ("KAMMER", "FOKUS", "SAMENKAMMER", "KONTROLLE", "START", "NAVI")


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


def yaw_towards(p, target):
    """Unity yaw that turns +z from p towards target (both Unity points)."""
    return (0, round(math.degrees(math.atan2(target[0] - p[0], target[2] - p[2])) % 360, 1), 0)


def towards(p, target, distance):
    """The point distance metres from p towards target, in the horizontal plane."""
    dx, dz = target[0] - p[0], target[2] - p[2]
    n = math.hypot(dx, dz) or 1.0
    return [p[0] + dx / n * distance, p[1], p[2] + dz / n * distance]


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
    details += [
        # the main switch, wakes up once all three couplers are cut: the Vessel's coordinate interface with an
        # advanced warp core floating above it (Vessel technology that Sedum copied)
        relative(kontrolle, SPOT_PEDESTAL, SPOT_ROT, path="", rename="ISAE_Hauptschalter", activationCondition=KOPPLER_ALLE,
                 deactivationCondition=DEAKTIVIERT),
        relative(switch, (0, 0, 0), path=P["vessel_interface"], scale=0.7, rename="Hauptschalter_Vessel_Interface"),
        # removeComponents strips the item from the root, so the copy can not be picked up like the real core
        relative(switch, (0, 2.3, 0), path=P["warpcore_vessel"], rename="Hauptschalter_Warpkern", removeComponents=True),
        # the interstellar probe waits in its cradle between the claws, in front of the lens (the DLL turns it
        # along the barrel and fires it in the finale)
        relative(PIVOT, at(I["sonde"]), path=P["nomai_probe"], scale=4, rename="Interstellare_Sonde", keepLoaded=True),
        relative(PIVOT, at(I["sonde"]), path=P["warp_particles"], scale=1.5, rename="Sondenglut", keepLoaded=True, deactivationCondition=DEAKTIVIERT),
    ]
    details += pulskern_props(K)
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
    puls = at(K["pulskern"])
    spot = towards(puls, at(K["boden"]), 4.2)
    texts.append(relative(PIVOT, spot, yaw_towards(spot, puls), type="computer", xmlFile="planets/text/Pulskern.xml", rename="Computer_Pulskern"))
    volumes = {
        "interactionVolumes": [relative(switch, (0, 1.4, 0), radius=1.6, range=3, prompt="Aussendungseinheit abschalten", condition=DEAKTIVIERT,
                                        persistent=True, reusable=False, audio="NomaiPowerOff", rename="Hauptschalter_Volumen")],
        "revealVolumes": [
            reveal([0, 0, 0], 1300, ["ZEKISAE_FOUND"]),
            reveal([0, 0, 0], 450, ["ZEKISAE_FOKUS_RUMOR"], "observe", maxDistance=4000, maxAngle=25),
            dict(reveal(at(K["boden"], 3), 24, ["ZEKISAE_KERN_FOUND"]), parentPath=PIVOT, isRelativeToParent=True),
            dict(reveal(at(K["pulskern"], 2), 7, ["ZEKISAE_PULSKERN_FOUND"]), parentPath=PIVOT, isRelativeToParent=True),
        ] + [dict(reveal(SPOT_COMPUTER, 12, [f"ZEKISAE_{fact}_FOUND"]), parentPath=module_path(name), isRelativeToParent=True)
             for (_, name), fact in zip(MODULES, ("KONTROLLE", "START", "NAVI"))],
        "forces": {"directionalVolumes": [
            # Nomai gravity towards the floor of the core chamber
            relative(PIVOT, at(K["boden"], K["hoehe"] / 2), force=9, normal=vec([0, -1, 0]),
                     shape={"type": "cylinder", "radius": K["bodenRadius"] - 0.3, "height": K["hoehe"] - 0.4}, rename="Schwerkraft_Kernkammer"),
        ]},
        # the seedling over the Pulskern burns: energy and heat of the core (only there once the Samenkern is in)
        "hazardVolumes": [relative(PIVOT + "/ISAE_Keimling_Hitze", (0, 0, 0), type="heat", damagePerSecond=30, radius=2.8,
                                   firstContactDamageType="electrical", firstContactDamage=10, rename="Keimling_Hitze")],
    }
    entries = [
        relative(PIVOT, at(I["kern"], 80), id="ZEKISAE_ISAE"),
        relative(PIVOT, at(K["boden"], 3), id="ZEKISAE_KERN"),
        relative(PIVOT, at(K["sedum"], 1), id="ZEKISAE_SEDUM"),
        relative(PIVOT, at(K["pulskern"], 2), id="ZEKISAE_PULSKERN"),
        relative(PIVOT, at(I["kern"], 120), id="ZEKISAE_WURZELN"),
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
            "remotes": isae_remotes(K, F),
        },
        "Volumes": volumes,
    })
    return cfg


KEIMLING_UP = 4.6  # the seedling over the Pulskern, metres above the socket


def pulskern_props(K):
    """The Pulskern on the chamber floor (Blender model, placements.json) takes the Samenkern. The socket is an
    empty NH detail; the DLL makes the seedling over it grow and the roots swallow the cannon."""
    socket = at(K["pulskern_mitte"])
    return [
        relative(PIVOT, socket, path="", rename="ISAE_Pulskern_Fassung", keepLoaded=True,
                 itemSocket={"itemType": "Samenkern", "insertCondition": SAMEN_EINGESETZT, "clearInsertConditionOnRemoval": False,
                             "insertFact": "ZEKISAE_PULSKERN_GEFUETTERT", "colliderRadius": 1.3, "interactRange": 3.5}),
        # heat around the seedling (the hazard volume hangs below this container)
        relative(PIVOT, add(socket, (0, KEIMLING_UP, 0)), path="", rename="ISAE_Keimling_Hitze", activationCondition=SAMEN_EINGESETZT),
        relative(PIVOT, add(socket, (0, KEIMLING_UP, 0)), path=P["warp_particles"], scale=1.2, rename="ISAE_Keimling_Glut",
                 activationCondition=SAMEN_EINGESETZT),
    ]


def remote(rid, platform=None, stones=(), **platform_extra):
    r = {"id": "ZEKISAE_" + rid, "decalPath": f"planets/assets/remotes/{rid.lower()}.png"}
    if platform is not None:
        platform.update(platform_extra)
        r["platform"] = platform
    if stones:
        r["stones"] = list(stones)
    return r


def module_pool(name):
    """Fallback spot of a module's pool platform; the DLL moves it onto the pool of the module copy."""
    return relative(module_path(name), add(SPOT_RECORDER, (2.6, 2.6, -0.2)), SPOT_ROT, rename=f"ISAE_Becken_{name}")


def module_stone(name, rid):
    return relative(module_path(name), add(SPOT_COMPUTER, (1.2, -1.2, -0.4)), SPOT_ROT, rename=f"ISAE_Stein_{name}_{rid}")


def isae_remotes(K, F):
    """Projection pools: the three module pools show the core chamber, a focus cannon and the seed chamber."""
    deck = [12.0, 0.0, 14.0]
    return [
        remote("KAMMER", relative(PIVOT, at(K["projektion"]), yaw(K["projektion"]), rename="ISAE_Becken_Kammer"),
               [module_stone("Kontrolle", "KAMMER")], reveals="ZEKISAE_KERN_FOUND"),
        remote("FOKUS", relative(focus_path("Alpha"), deck, yaw_towards(deck, [0, 0, 0]), rename="ISAE_Becken_Fokus"),
               [module_stone("Start", "FOKUS")], reveals="ZEKISAE_FOKUS_FOUND"),
        remote("SAMENKAMMER", None, [module_stone("Navigation", "SAMENKAMMER"),
                                     relative(PIVOT, at(K["stein"], 0.3), rename="ISAE_Stein_Kammer_SAMENKAMMER")]),
        remote("KONTROLLE", module_pool("Kontrolle"), reveals="ZEKISAE_KONTROLLE_FOUND"),
        remote("START", module_pool("Start"), reveals="ZEKISAE_START_FOUND"),
        remote("NAVI", module_pool("Navigation"), reveals="ZEKISAE_NAVI_FOUND"),
    ]


# ==============================================================================================
# the Keimdorn (a small bramble seed around Dark Bramble) and its seed chamber
# ==============================================================================================
def keimdorn_config(A):
    T = A.get("keimdorn", {})
    details = []
    # Nomai beacons on the tips of some thorns (the thorns are the Blender model "sternwurzeln", scaled)
    for k in range(0, 18, 3):
        tip = T.get(f"spitze{k}")
        if tip:
            details.append(placed(P["lamp_flare"], [c * KEIMDORN_SCALE for c in at(tip)], rename=f"Keimdorn_Leuchtfeuer_{k}"))
    cfg = sb.body_header(KEIMDORN, "SolarSystem")
    cfg.update({
        "canShowOnTitle": False,
        "Base": {"surfaceSize": 140, "surfaceGravity": 0, "showMinimap": False},
        # a small moon of Dark Bramble, out of the plane of the planets
        "Orbit": {"primaryBody": "DARK_BRAMBLE", "isMoon": True, "semiMajorAxis": 2600, "eccentricity": 0, "inclination": 24,
                  "longitudeOfAscendingNode": 70, "trueAnomaly": 40, "axialTilt": 0, "siderealPeriod": 0, "tint": GREEN[0]},
        "MapMarker": {"enabled": True},
        "ShipLog": {"xmlFile": "planets/shiplogs/Keimdorn.xml", "spriteFolder": "planets/assets/shiplog/entries",
                    "mapMode": {"revealedSprite": "planets/assets/shiplog/map/keimdorn.png",
                                "outlineSprite": "planets/assets/shiplog/map/isae_outline.png", "scale": 0.8}},
        "Bramble": {"nodes": [{"position": vec([0, 0, 0]), "rotation": vec([0, 0, 0]), "linksTo": SAMENKAMMER, "name": KEIM_NODE, "scale": 0.6,
                               "fogTint": color(120, 255, 150), "lightTint": color(150, 255, 170)}]},
        "Props": {"details": details,
                  "entryLocation": [{"id": "ZEKISAE_KEIMDORN", "position": vec([0, 60, 0])}]},
        "Volumes": {"revealVolumes": [reveal([0, 0, 0], 420, ["ZEKISAE_KEIMDORN_FOUND"])]},
    })
    return cfg


KEIMDORN_SCALE = 30.0   # the thorns of the Keimdorn (sternwurzeln.obj is unit size)
SAMENKAMMER_AT = (-26000, 21000, 33000)


def samenkammer_config(A):
    G = A["keim"]
    plat = at(G["plattform"])
    herz = at(G["herz"])
    details = [
        # the heart of every seed, floating in the Nomai frame (the frame and the heart itself are Blender models)
        placed("", herz, rename="ZEKISAE_Samenkern", keepLoaded=True,
               item={"name": "Samenkern", "itemType": "Samenkern", "colliderRadius": 0.7, "interactRange": 3.5,
                     "pickupCondition": SAMEN_GENOMMEN, "clearPickupConditionOnDrop": False, "pickupFact": "ZEKISAE_SAMENKERN_GENOMMEN",
                     "holdOffset": vec([0, -0.1, 0.25]), "socketOffset": vec([0, 0, 0])}),
        placed(P["warp_particles"], herz, scale=0.7, rename="Samenkern_Glut", deactivationCondition=SAMEN_GENOMMEN, blinkWhenActiveChanged=True),
        # the research building: a Nomai shrine on the platform, Nomai technology around it
        placed(P["shrine"], at(G["schrein"], -0.35), yaw(G["schrein"]), rename="Forschungsschrein"),
        placed(P["eye_symbol"], at(G["schrein"], 9.5), yaw(G["schrein"]), rename="Forschungsschrein_Auge"),
        placed(P["warpcore_vessel"], at(G["technik1"], 1.2), rename="Forschung_Warpkern", removeComponents=True),
        placed(P["gravity_crystal"], at(G["technik2"]), yaw(G["technik2"]), rename="Forschung_Kristall"),
        placed(P["transponder"], at(G["technik3"], -0.2), yaw(G["technik3"]), rename="Forschung_Sender"),
        placed(P["skeleton"], towards(at(G["recorder"]), plat, 2.2), yaw(G["recorder"]), rename="Tamarisks_Ueberreste"),
        placed(P["staff"], add(towards(at(G["recorder"]), plat, 3.2), (0, 0.05, 0)), (0, 40, 90), rename="Tamarisks_Stab"),
    ]
    details += [placed(P["lamp_flare"], at(G[f"lampe{i}"]), rename=f"Forschungslampe_{i}") for i in range(1, 7)]
    texts = [
        placed("", at(G["computer"]), yaw(G["computer"]), type="computer", xmlFile="planets/text/Keim_Forschung.xml", rename="Computer_Forschung"),
        placed("", at(G["recorder"]), yaw(G["recorder"]), type="recorder", xmlFile="planets/text/Keim_Tamarisk.xml", rename="Recorder_Tamarisk"),
        placed("", at(G["tafel"]), yaw(G["tafel"]), type="whiteboard", xmlFile="planets/text/Keim_Tafel.xml", rename="Tafel_Samenkern"),
    ]
    for t in texts:
        t.pop("path")
    cfg = sb.body_header(SAMENKAMMER, "SolarSystem")
    cfg.update({
        "canShowOnTitle": False,
        "Orbit": {"staticPosition": vec(SAMENKAMMER_AT)},
        "ShipLog": {"mapMode": {"remove": True}},
        "Bramble": {
            "dimension": {"radius": 320, "fogTint": color(70, 200, 105), "fogDensity": 2.2, "linksTo": KEIM_NODE, "vinePrefab": "smallNest"},
            # a baby seed at the edge of the chamber: the DLL links it to the dimension of the Vessel
            "nodes": [{"position": vec(at(G["babysamen"])), "rotation": vec([0, 0, 0]), "linksTo": SAMENKAMMER, "name": BABY_NODE,
                       "scale": 0.16, "preventRecursionCrash": True, "fogTint": color(255, 230, 170), "lightTint": color(255, 220, 160)}],
        },
        "Props": {
            "details": details,
            "translatorText": texts,
            "remotes": [
                remote("SAMENKAMMER", placed("", at(G["projektion"]), yaw(G["projektion"]), rename="Keim_Becken"), reveals="ZEKISAE_SAMENKAMMER_FOUND"),
                remote("KAMMER", None, [placed("", at(G["stein"], 0.3), rename="Keim_Stein_KAMMER")]),
            ],
            "signals": [{"frequency": "Energiesignaturen", "name": "Samenkern", "audio": "OW_NM_WhiteHoleAmbienceL",
                         "position": vec(herz), "sourceRadius": 2, "detectionRadius": 600, "identificationRadius": 120}],
            "entryLocation": [{"id": "ZEKISAE_SAMENKAMMER", "position": vec(add(plat, (0, 4, 0)))},
                              {"id": "ZEKISAE_SAMENKERN", "position": vec(herz)}],
        },
        "Volumes": {
            "revealVolumes": [reveal(herz, 300, ["ZEKISAE_SAMENKAMMER_FOUND"]),
                              reveal(herz, 12, ["ZEKISAE_SAMENKERN_FOUND"])],
            "forces": {"directionalVolumes": [
                {"position": vec(add(plat, (0, 9, 0))), "force": 9, "normal": vec([0, -1, 0]),
                 "shape": {"type": "cylinder", "radius": G["deckRadius"] + 0.5, "height": 18}, "rename": "Forschungsschwerkraft"}]},
        },
    })
    for r in cfg["Props"]["remotes"]:
        for st in r.get("stones", []):
            st.pop("path", None)
        if "platform" in r:
            r["platform"].pop("path", None)
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
                                                  condition=cond, persistent=True, reusable=False, audio="NomaiPowerOff",
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
    props += [
        # the Pulskern on the chamber floor; its heart pulses (the DLL), the Samenkern goes into the socket above it
        {"model": "pulskern", "name": "ISAE_Pulskern", "parentPath": PIVOT, "collider": True, "position": K["pulskern"]["position"]},
        {"model": "pulsglut", "name": "ISAE_Pulsglut", "parentPath": PIVOT, "position": K["pulskern_mitte"]["position"]},
        # Verwurzelt: hidden until the Samenkern lies in the Pulskern, then the DLL lets them grow
        {"model": "babysamen", "name": "ISAE_Keimling", "parentPath": PIVOT, "hidden": True,
         "position": vec(add(at(K["pulskern_mitte"]), (0, KEIMLING_UP, 0)))},
        {"model": "wurzeln", "name": "ISAE_Wurzeln", "parentPath": PIVOT, "hidden": True},
    ]
    lights = [{"name": "Licht_Kernkammer", "body": NAME, "parentPath": PIVOT, "position": K["licht"]["position"],
               "color": {"x": 1.0, "y": 0.42, "z": 0.2}, "range": 45, "intensity": 2.2}]
    lights += [{"name": f"Licht_Emitter_{greek}", "body": NAME, "parentPath": focus_path(greek), "position": F["emitter"]["position"],
                "color": {"x": 1.0, "y": 0.4, "z": 0.18}, "range": 70, "intensity": 1.6} for _, greek in FOCUS_NAMES]
    points = {k: I[k]["position"] for k in ("kern", "linse", "muendung", "heck")}
    points.update({f"modul_{key}": I[f"modul_{key}"]["position"] for key, _ in MODULES})
    points.update({f"fokus_{x}": I[f"fokus_{x}"]["position"] for x, _ in FOCUS_NAMES})
    points["fokus_emitter"] = F["emitter"]["position"]
    points["sonde"] = I["sonde"]["position"]
    points["pulskern"] = K["pulskern_mitte"]["position"]
    points["keimling"] = vec(add(at(K["pulskern_mitte"]), (0, KEIMLING_UP, 0)))

    # the Keimdorn and the seed chamber
    G = A["keim"]
    keim = [
        {"model": "sternwurzeln", "name": "Keimdorn_Dornen", "body": KEIMDORN, "collider": True, "scale": KEIMDORN_SCALE},
        {"model": "forschungsplattform", "name": "Forschungsplattform", "body": SAMENKAMMER, "collider": True, "position": G["plattform"]["position"]},
        {"model": "herzgeruest", "name": "Herzgeruest", "body": SAMENKAMMER, "spin": 5, "position": G["herz"]["position"]},
        # the heart itself hangs below the NH item, so it travels with the player
        {"model": "samenkern", "name": "Samenkern_Modell", "body": SAMENKAMMER, "parentPath": SAMENKERN, "spin": 40},
    ]
    for p in props + keim:
        p.setdefault("body", NAME)
        p.setdefault("position", {"x": 0, "y": 0, "z": 0})
        p.setdefault("rotation", {"x": 0, "y": 0, "z": 0})
        p.setdefault("scale", 1)
    lights += [
        {"name": "Licht_Pulskern", "body": NAME, "parentPath": PIVOT, "position": K["pulskern_mitte"]["position"],
         "color": {"x": 1.0, "y": 0.5, "z": 0.22}, "range": 14, "intensity": 2.0},
        {"name": "Licht_Samenkern", "body": SAMENKAMMER, "parentPath": SAMENKERN, "position": {"x": 0, "y": 0, "z": 0},
         "color": {"x": 0.45, "y": 1.0, "z": 0.55}, "range": 30, "intensity": 2.4},
        {"name": "Licht_Forschung", "body": SAMENKAMMER, "position": vec(add(at(G["plattform"]), (0, 12, 0))),
         "color": {"x": 0.7, "y": 1.0, "z": 0.75}, "range": 45, "intensity": 1.3},
        {"name": "Licht_Keimdorn", "body": KEIMDORN, "position": {"x": 0, "y": 0, "z": 0},
         "color": {"x": 0.5, "y": 1.0, "z": 0.6}, "range": 260, "intensity": 1.6},
    ]
    return {
        # exact names of game materials for the Blender material slots; empty = taken from the game
        "materials": {"VesselHuelle": "", "VesselKupfer": "", "VesselDunkel": "", "VesselGlut": "", "VesselLeuchten": "",
                      "Dornranke": "", "Keimlicht": ""},
        "props": props + keim,
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
               "ZEKISAE_NAVI": (2500, 470), "ZEKISAE_FOKUS": (1650, 880), "ZEKISAE_SEDUM": (1650, 30), "ZEKISAE_SPUREN": (1220, 450),
               "ZEKISAE_PULSKERN": (2500, 160), "ZEKISAE_WURZELN": (2080, -60),
               "ZEKISAE_KEIMDORN": (2950, 450), "ZEKISAE_SAMENKAMMER": (3380, 620), "ZEKISAE_SAMENKERN": (3380, 260)}
    checks = [
        {"check": {"allFactsRevealed": ["ZEKISAE_FOUND"]}, "then": {"setPersistentConditions": [ENTDECKT]}},
        {"check": {"allPersistentConditionsSet": [KOPPLER % x for x, _ in FOCUS_NAMES]}, "then": {"setPersistentConditions": [KOPPLER_ALLE]}},
    ]
    checks += [{"check": {"allPersistentConditionsSet": [KOPPLER % x]}, "then": {"revealFacts": [f"ZEKISAE_KOPPLER_{x}_FACT"]}} for x, _ in FOCUS_NAMES]
    checks.append({"check": {"allPersistentConditionsSet": [DEAKTIVIERT]}, "then": {"revealFacts": ["ZEKISAE_ABGESCHALTET"]}})
    checks.append({"check": {"allConditionsSet": [SAMEN_EINGESETZT]}, "then": {"revealFacts": ["ZEKISAE_WURZELN_FOUND"]}})
    return {
        "$schema": NH + "star_system_schema.json",
        "initialReveal": ["ZEKISAE_SIGNATUR"],
        "curiosities": [{"id": "ZEKISAE_ISAE", "color": RED[0], "highlightColor": RED[1]},
                        {"id": "ZEKISAE_KEIMDORN", "color": GREEN[0], "highlightColor": GREEN[1]}],
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
    elif motif == "keimdorn":
        # the small seed planet: a glowing node with thorns, Dark Bramble behind it
        d.ellipse([c + 60, c - 240, c + 420, c + 120], fill=(70, 80, 70, 255), outline=(150, 170, 150, 255), width=4)
        for k in range(18):
            a = math.radians(k * 137.5)
            r1, r2 = 70, 150 + (k * 29) % 90
            d.line([(c + r1 * math.cos(a), c + r1 * math.sin(a)), (c + r2 * math.cos(a + 0.25), c + r2 * math.sin(a + 0.25))],
                   fill=(70, 55, 40, 255), width=9 - k % 4)
        d.ellipse([c - 75, c - 75, c + 75, c + 75], fill=(150, 255, 170, 255), outline=(230, 255, 220, 255), width=6)
        d.ellipse([c - 30, c - 30, c + 30, c + 30], fill=(255, 255, 230, 255))
    elif motif == "spuren":
        d.ellipse([c - 40, c - 40, c + 40, c + 40], fill=(255, 150, 70, 255))
        planets = [(150, 30, (210, 120, 80)), (230, 140, (140, 160, 110)), (300, 250, (90, 140, 180)), (205, 320, (120, 100, 150))]
        for k, (r, a, col) in enumerate(planets):
            x, y = c + r * math.cos(math.radians(a)), c + r * math.sin(math.radians(a))
            d.ellipse([c - r, c - r, c + r, c + r], outline=(120, 70, 50, 255), width=2)
            d.ellipse([x - 16, y - 16, x + 16, y + 16], fill=col + (255,))
            sb.spiral(d, x + 26, y - 22, 12, 1.6, 2, (255, 200, 140, 255), reverse=k % 2 == 1)
    return img


def map_sprite(size=256):
    """Map sprite of the Keimdorn: a green node with thorns."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = size / 2
    for k in range(14):
        a = math.radians(k * 137.5)
        d.line([(c + 40 * math.cos(a), c + 40 * math.sin(a)), (c + 118 * math.cos(a + 0.2), c + 118 * math.sin(a + 0.2))],
               fill=(95, 75, 55, 255), width=8)
    d.ellipse([c - 62, c - 62, c + 62, c + 62], fill=(120, 230, 140, 255), outline=(220, 255, 220, 255), width=5)
    return img


def decal(rid, size=256):
    """Icon of a projection pool on its stones and pedestal (white on transparent, like the game's decals)."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c, w = size / 2, (255, 255, 255, 255)
    d.ellipse([12, 12, size - 12, size - 12], outline=w, width=10)
    if rid == "KAMMER":      # the burning heart in its rings
        for r in (70, 45):
            d.ellipse([c - r, c - r * 0.45, c + r, c + r * 0.45], outline=w, width=8)
        d.ellipse([c - 24, c - 24, c + 24, c + 24], fill=w)
    elif rid == "FOKUS":     # three emitters around a triangle
        pts = [(c + 75 * math.cos(math.radians(a)), c + 75 * math.sin(math.radians(a))) for a in (-90, 30, 150)]
        d.polygon(pts, outline=w, width=8)
        for x, y in pts:
            d.ellipse([x - 16, y - 16, x + 16, y + 16], fill=w)
    elif rid == "SAMENKAMMER":  # a seed with thorns
        d.ellipse([c - 38, c - 38, c + 38, c + 38], fill=w)
        for k in range(8):
            a = math.radians(k * 45)
            d.line([(c + 38 * math.cos(a), c + 38 * math.sin(a)), (c + 85 * math.cos(a + 0.3), c + 85 * math.sin(a + 0.3))], fill=w, width=9)
    elif rid == "KONTROLLE":  # interface with the core above it
        d.rectangle([c - 55, c + 20, c + 55, c + 45], fill=w)
        d.ellipse([c - 28, c - 75, c + 28, c - 19], outline=w, width=9)
    elif rid == "START":      # the probe in its cradle
        d.polygon([(c, c - 85), (c - 26, c + 30), (c, c + 60), (c + 26, c + 30)], fill=w)
        d.arc([c - 70, c - 10, c + 70, c + 90], 200, 340, fill=w, width=9)
    else:                     # NAVI: star chart
        for r in (40, 80):
            d.ellipse([c - r, c - r * 0.5, c + r, c + r * 0.5], outline=w, width=7)
        d.ellipse([c - 14, c - 14, c + 14, c + 14], fill=w)
    return img


def crack_overlay(size=1024, seed=7):
    """Cracks in reality (Ende 2): white branching lines on transparent, the DLL fades it in over the screen."""
    import random
    rnd = random.Random(seed)
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    def branch(x, y, a, length, width, depth):
        while length > 8 and width >= 1:
            step = rnd.uniform(14, 34)
            a += rnd.uniform(-0.45, 0.45)
            nx, ny = x + math.cos(a) * step, y + math.sin(a) * step
            d.line([(x, y), (nx, ny)], fill=(255, 255, 255, 235), width=int(width))
            d.line([(x, y), (nx, ny)], fill=(180, 255, 200, 90), width=int(width) + 6)
            x, y, length = nx, ny, length - step
            if depth < 4 and rnd.random() < 0.16:
                branch(x, y, a + rnd.choice((-1, 1)) * rnd.uniform(0.5, 1.1), length * 0.6, width * 0.7, depth + 1)
            width *= 0.985

    c = size / 2
    for k in range(9):
        a = k / 9 * math.tau + rnd.uniform(-0.2, 0.2)
        branch(c + math.cos(a) * 30, c + math.sin(a) * 30, a, size * 0.75, 7, 0)
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
            "wreckSeconds": {"type": "slider", "value": 300, "min": 60, "max": 600, "title": "Ende 3: Zeit im Wrack (Sekunden)",
                             "tooltip": "Wie lange du im Ende \"Verwurzelt\" nach der Explosion noch lebst, bevor der Energiekern instabil wird."},
            "endingKeys": {"type": "selector", "value": "Strg + 1/2/3", "options": ["Strg + 1/2/3", "1/2/3", "Aus"],
                           "title": "Skip-Tasten für die Enden",
                           "tooltip": "Springt sofort zu einem Ende: 1 = Aussendung, 2 = Riss, 3 = Verwurzelt."},
        },
    })
    write_json("addon-manifest.json", {
        "$schema": NH + "addon_manifest_schema.json",
        "credits": ["Zeki"],
        "popupMessage": "Die Aussendungseinheit: Zwischen der Sonne und Timber Hearth zielt eine riesige Nomai-Kanone auf die Sonne. "
                        "Wenn du nichts tust, endet diese Schleife nicht mit einer Supernova.",
        # custom = the credits roll with the game's final music, but without the Big Bang epilogue
        "gameOver": [
            # Ende 1 "Aussendung": the ISAE drains the sun and fires its probe
            {"text": "Das Universum endet, aber du endest vor ihm...", "condition": UNIVERSUM_ENDET,
             "colour": color(255, 120, 70), "creditsType": "custom", "audio": "FinalCredits", "length": 110},
            # Ende 2 "Riss": the rooted ISAE fires a broken seed into the sun and reality breaks
            {"text": "Das Universum hätte noch lange gelebt, wenn du nicht wärst...", "condition": ENDE_RISS,
             "colour": color(190, 255, 200), "creditsType": "custom", "audio": "FinalCredits", "length": 110},
            # Ende 3 "Verwurzelt": the switched-off ISAE shoots its rooted probe into the sun, the sun dissolves into a seed
            {"text": "Das Universum endet, aber du pflanzt invasive Pflanzen in Sternen", "condition": ENDE_WURZEL,
             "colour": color(130, 255, 150), "creditsType": "custom", "audio": "FinalCredits", "length": 110},
        ],
    })


def main():
    A = anchors()
    write_json("planets/ISAE.json", isae_config(A))
    write_json("planets/OrbitalProbeCannon.json", opc_config())
    for body, filename, xml, pos, rotation in PLANET_TEXTS:
        write_json("planets/" + filename, planet_config(body, xml, pos, rotation))
    write_json("planets/Keimdorn.json", keimdorn_config(A))
    write_json("planets/Samenkammer.json", samenkammer_config(A))
    write_json("systems/SolarSystem.json", solar_system())
    write_json("assets/models/placements.json", placements(A))
    manifests()

    E = "planets/assets/shiplog/entries/"
    for entry, motif, seed in (("ZEKISAE_SEDUM", "sedum", 33), ("ZEKISAE_SPUREN", "spuren", 34), ("ZEKISAE_KONTROLLE", "kontrolle", 35),
                               ("ZEKISAE_START", "start", 36), ("ZEKISAE_NAVI", "navi", 37), ("ZEKISAE_KEIMDORN", "keimdorn", 38)):
        sb.save(art(seed, motif), E + entry + ".png")
    sb.save(outline_sprite(), "planets/assets/shiplog/map/isae_outline.png")
    sb.save(map_sprite(), "planets/assets/shiplog/map/keimdorn.png")
    for rid in REMOTES:
        sb.save(decal(rid), f"planets/assets/remotes/{rid.lower()}.png")
    sb.save(crack_overlay(), "assets/riss.png")
    # left-overs of older versions: rocks (1.0) and separate focus cannon bodies (1.0 - 1.3)
    terrain = os.path.join(MOD, "planets", "assets", "terrain")
    if os.path.isdir(terrain):
        shutil.rmtree(terrain)
    for old in glob.glob(os.path.join(MOD, "planets", "Fokuskanone_*.json")):
        os.remove(old)


if __name__ == "__main__":
    main()
