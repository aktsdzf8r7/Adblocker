# -*- coding: utf-8 -*-
"""
Build script for "Verdornt" (Zeki.Verdornt), a New Horizons mod: a bramble seed crashed on Timber Hearth leads
into Dornenkranz, the overgrown home system of Dark Bramble. Design: docs/superpowers/specs/2026-10-10-verdornt-design.md

Generates the star system, all bodies and dimensions, placements.json for the DLL, pictures and manifests.
Needs assets/models/anchors.json from tools/verdornt_models.py; texts come from verdornt_texts.py and the ship
log from verdornt_shiplog.py.

Usage:  python tools/verdornt_build.py [path/to/Zeki.Verdornt]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import schleier_build as sb  # noqa: E402
from schleier_build import NH, write_json  # noqa: E402

MOD = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "Zeki.Verdornt"))
sb.MOD = MOD

VERSION = "0.1.0"
SYSTEM = "Verdornt"


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
    manifests()
    write_json(f"systems/{SYSTEM}.json", system())


if __name__ == "__main__":
    main()
