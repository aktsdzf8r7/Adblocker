# -*- coding: utf-8 -*-
"""
Checks the Zeki.Schleiersystem addon without starting the game.

  1. JSON configs against the official New Horizons schemas (unknown keys are errors, because NH
     silently ignores them - that is how "tint"/"density"/"depth" went unnoticed before)
  2. Nomai text / ship log XML against the official XSDs
  3. Consistency: referenced files exist, ship log fact/entry IDs are unique and every revealed
     fact exists, rumor sources exist, curiosities have colours, entries have positions and
     sprites, warp pads come in pairs, projection stones have a platform, recorder/computer
     texts are linear chains, conditions used by props are actually set somewhere
  4. Placement: every surface prop sits on the generated terrain (re-sampled from the PNG the
     same way NH builds its mesh)

Usage:  python tools/schleier_validate.py [path/to/Zeki.Schleiersystem] [--schemas DIR]
Needs:  jsonschema, lxml, numpy, Pillow. Without --schemas the schemas are downloaded.
"""
import glob
import json
import math
import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nh_props import GROUND, P, SCENE_PROPS  # noqa: E402

args = [a for a in sys.argv[1:] if not a.startswith("--")]
MOD = os.path.abspath(args[0] if args else os.path.join(os.path.dirname(__file__), "..", "Zeki.Schleiersystem"))
SCHEMA_DIR = sys.argv[sys.argv.index("--schemas") + 1] if "--schemas" in sys.argv else None
NH = "https://raw.githubusercontent.com/Outer-Wilds-New-Horizons/new-horizons/main/NewHorizons/Schemas/"

errors, warnings = [], []


def err(msg):
    errors.append(msg)


def warn(msg):
    warnings.append(msg)


def rel(p):
    return os.path.relpath(p, MOD).replace(os.sep, "/")


def schema_text(name):
    if SCHEMA_DIR:
        with open(os.path.join(SCHEMA_DIR, name), encoding="utf-8") as f:
            return f.read()
    with urllib.request.urlopen(NH + name, timeout=30) as r:
        return r.read().decode("utf-8")


def strict(schema):
    if isinstance(schema, dict):
        if schema.get("type") == "object" and "properties" in schema and "additionalProperties" not in schema:
            schema["additionalProperties"] = False
        for v in schema.values():
            strict(v)
    elif isinstance(schema, list):
        for v in schema:
            strict(v)
    return schema


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------------- 1 + 2
def check_schemas(bodies, systems):
    import jsonschema
    from lxml import etree

    body_schema = strict(json.loads(schema_text("body_schema.json")))
    system_schema = strict(json.loads(schema_text("star_system_schema.json")))
    for path, data in list(bodies.items()) + list(systems.items()):
        schema = body_schema if path in bodies else system_schema
        for e in jsonschema.Draft7Validator(schema).iter_errors(data):
            err(f"{rel(path)}: {'/'.join(map(str, e.path))}: {e.message[:160]}")
    for name in ("addon-manifest.json", "title-screen.json"):
        path = os.path.join(MOD, name)
        if not os.path.exists(path):
            continue
        sch = json.loads(schema_text(name.replace("-", "_").replace(".json", "_schema.json")))
        for e in jsonschema.Draft7Validator(sch).iter_errors(load_json(path)):
            err(f"{name}: {e.message[:160]}")
    xsds = {root: etree.XMLSchema(etree.fromstring(schema_text(n).encode("utf-8")))
            for root, n in (("NomaiObject", "text_schema.xsd"), ("AstroObjectEntry", "shiplog_schema.xsd"))}
    for path in glob.glob(os.path.join(MOD, "planets", "**", "*.xml"), recursive=True):
        doc = etree.parse(path)
        x = xsds[doc.getroot().tag]
        if not x.validate(doc):
            for e in x.error_log:
                err(f"{rel(path)}:{e.line}: {e.message}")


# ---------------------------------------------------------------------------------- 3
def walk(obj, key=None):
    """Yield (key, value) for every nested key."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k, v
            yield from walk(v, k)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk(v, key)


FILE_KEYS = {"xmlFile", "heightMap", "textureMap", "emissionMap", "smoothnessMap", "normalMap", "decalPath", "revealedSprite", "outlineSprite"}


def check_consistency(bodies, systems):
    manifest = load_json(os.path.join(MOD, "manifest.json"))
    if not os.path.exists(os.path.join(MOD, manifest["filename"])):
        err(f"manifest.json: {manifest['filename']} is missing")

    # ---- referenced files ----
    for path, data in bodies.items():
        for k, v in walk(data):
            if k in FILE_KEYS and isinstance(v, str) and not os.path.exists(os.path.join(MOD, v)):
                err(f"{rel(path)}: {k} -> missing file {v}")
            if k == "spriteFolder" and not os.path.isdir(os.path.join(MOD, v)):
                err(f"{rel(path)}: spriteFolder {v} is missing")
            if k == "path" and isinstance(v, str) and v and v not in SCENE_PROPS:
                err(f"{rel(path)}: prop path is not in the verified prop list: {v}")
            if k == "path" and isinstance(v, str) and v.startswith(("DreamWorld_Body", "RingWorld_Body")):
                err(f"{rel(path)}: prop needs the Echoes of the Eye DLC: {v}")

    # ---- ship logs per star system ----
    per_system = {}
    for path, data in bodies.items():
        sysname = data.get("starSystem", "SolarSystem")
        s = per_system.setdefault(sysname, {"entries": {}, "facts": {}, "rumor_sources": [], "curiosity_refs": [], "curiosities": set(), "bodies": [],
                                            "sprites": set()})
        s["bodies"].append((path, data))
        sl = data.get("ShipLog")
        if not sl or not sl.get("xmlFile"):
            continue
        if sl.get("spriteFolder"):
            s["sprites"].add(sl["spriteFolder"])
        xml_path = os.path.join(MOD, sl["xmlFile"])
        root = ET.parse(xml_path).getroot()
        for entry in root.iter("Entry"):
            eid = entry.findtext("ID")
            if eid in s["entries"]:
                err(f"{rel(xml_path)}: duplicate entry id {eid}")
            s["entries"][eid] = xml_path
            if entry.find("IsCuriosity") is not None:
                s["curiosities"].add(eid)
                if entry.findtext("Curiosity") == eid:
                    err(f"{rel(xml_path)}: curiosity {eid} must not reference itself as <Curiosity>")
            if entry.findtext("Curiosity"):
                s["curiosity_refs"].append((xml_path, entry.findtext("Curiosity")))
            for tag in ("RumorFact", "ExploreFact"):
                for fact in entry.findall(tag):
                    fid = fact.findtext("ID")
                    if fid in s["facts"]:
                        err(f"{rel(xml_path)}: duplicate fact id {fid} (also in {rel(s['facts'][fid])})")
                    s["facts"][fid] = xml_path
                    if fact.findtext("SourceID"):
                        s["rumor_sources"].append((xml_path, fact.findtext("SourceID")))
    # facts are saved by ID across all systems, so an ID may only exist once in the whole addon
    seen = {}
    for sysname, s in per_system.items():
        for fid in s["facts"]:
            if fid in seen and seen[fid] != sysname:
                err(f"fact {fid} exists in both {seen[fid]} and {sysname}")
            seen[fid] = sysname

    revealed_somewhere = set()
    conditions_set = set(code_conditions())

    for sysname, s in per_system.items():
        for xml_path, src in s["rumor_sources"]:
            if src not in s["entries"]:
                err(f"{rel(xml_path)}: rumor SourceID {src} is not an entry of {sysname}")
        for xml_path, cur in s["curiosity_refs"]:
            if cur not in s["curiosities"]:
                err(f"{rel(xml_path)}: <Curiosity>{cur}</Curiosity> is not a curiosity entry")
        sysfile = os.path.join(MOD, "systems", sysname + ".json")
        sysdata = systems.get(sysfile, {})
        colours = {c["id"] for c in sysdata.get("curiosities", [])}
        for c in s["curiosities"]:
            if c not in colours:
                err(f"systems/{sysname}.json: curiosity {c} has no colour")
        positions = {p["id"] for p in sysdata.get("entryPositions", [])}
        for e in s["entries"]:
            if e not in positions:
                err(f"systems/{sysname}.json: entry {e} has no rumor mode position")
        for p in positions - set(s["entries"]):
            err(f"systems/{sysname}.json: entryPositions references unknown entry {p}")
        for e in s["entries"]:
            if not any(os.path.exists(os.path.join(MOD, folder, e + ".png")) for folder in s["sprites"]):
                warn(f"{sysname}: entry {e} has no ship log picture")

        def need_fact(where, fid):
            revealed_somewhere.add(fid)
            if fid not in s["facts"]:
                err(f"{where}: fact {fid} does not exist in the ship log of {sysname}")

        for fid in sysdata.get("initialReveal", []):
            need_fact(f"systems/{sysname}.json initialReveal", fid)
        for key in ("factRequiredToExitViaWarpDrive",):
            if sysdata.get(key):
                need_fact(f"systems/{sysname}.json {key}", sysdata[key])
        for chk in sysdata.get("conditionalChecks", []):
            for fid in chk["check"].get("allFactsRevealed", []) + chk["check"].get("anyFactsRevealed", []):
                need_fact(f"systems/{sysname}.json conditionalChecks", fid)
            for fid in chk["then"].get("revealFacts", []):
                need_fact(f"systems/{sysname}.json conditionalChecks", fid)
            conditions_set.update(chk["then"].get("setPersistentConditions", []) + chk["then"].get("setConditions", []))

        # ---- bodies of this system ----
        for path, data in s["bodies"]:
            props = data.get("Props", {})
            vols = data.get("Volumes", {})
            for v in vols.get("interactionVolumes", []) + vols.get("conditionTriggerVolumes", []):
                if v.get("condition"):
                    conditions_set.add(v["condition"])
            for v in vols.get("revealVolumes", []):
                for fid in v["reveals"]:
                    need_fact(rel(path) + " revealVolume", fid)
            for sig in props.get("signals", []):
                if sig.get("reveals"):
                    need_fact(rel(path) + " signal", sig["reveals"])
            for r in props.get("remotes", []):
                if r.get("platform", {}).get("reveals"):
                    need_fact(rel(path) + " remote platform", r["platform"]["reveals"])
            for loc in props.get("entryLocation", []):
                if loc["id"] not in s["entries"]:
                    err(f"{rel(path)}: entryLocation {loc['id']} is not an entry")
            for t in props.get("translatorText", []):
                check_text(path, t, need_fact)
            for d in props.get("details", []):
                for k in ("activationCondition", "deactivationCondition"):
                    if d.get(k):
                        conditions_used.append((path, d[k]))
                # items and item sockets reveal facts and set dialogue conditions
                item, socket = d.get("item") or {}, d.get("itemSocket") or {}
                for fid in (item.get("pickupFact"), socket.get("insertFact"), socket.get("removalFact")):
                    if fid:
                        need_fact(rel(path) + " item", fid)
                conditions_set.update(c for c in (item.get("pickupCondition"), socket.get("insertCondition"), socket.get("removalCondition")) if c)
            for v in vols.get("interactionVolumes", []) + vols.get("audioVolumes", []):
                audio = v.get("audio")
                if audio and AUDIO_TYPES and audio not in AUDIO_TYPES and not os.path.exists(os.path.join(MOD, audio)):
                    err(f"{rel(path)}: audio {audio} is neither an AudioType nor a file of the mod")

        # warp pads and remotes are global, but every pair should live in one system
        tx, rx, stones, platforms = {}, {}, {}, {}
        for path, data in s["bodies"]:
            props = data.get("Props", {})
            for w in props.get("warpTransmitters", []):
                tx.setdefault(w["frequency"], []).append(path)
            for w in props.get("warpReceivers", []):
                rx.setdefault(w["frequency"], []).append(path)
            for r in props.get("remotes", []):
                if "platform" in r:
                    platforms.setdefault(r["id"], []).append(path)
                if r.get("stones"):
                    stones.setdefault(r["id"], []).append(path)
        for f, where in tx.items():
            if len(rx.get(f, [])) != 1:
                err(f"{sysname}: warp transmitter frequency {f} needs exactly one receiver (has {len(rx.get(f, []))})")
        for f in rx:
            if f not in tx:
                warn(f"{sysname}: warp receiver {f} has no transmitter")
        for rid in stones:
            if len(platforms.get(rid, [])) != 1:
                err(f"{sysname}: projection stones {rid} need exactly one platform")

        # bramble: nodes link to dimensions, dimensions exit through named nodes, no recursion
        dims = {d["name"]: d for _, d in s["bodies"] if d.get("Bramble", {}).get("dimension")}
        node_names, edges = {}, {}
        for path, d in s["bodies"]:
            for nd in d.get("Bramble", {}).get("nodes", []):
                if nd.get("name"):
                    if nd["name"] in node_names:
                        err(f"{rel(path)}: bramble node name {nd['name']} is used twice")
                    node_names[nd["name"]] = d["name"]
                if nd["linksTo"] not in dims:
                    err(f"{rel(path)}: bramble node links to {nd['linksTo']}, which is not a dimension of {sysname}")
                if not nd.get("preventRecursionCrash"):
                    edges.setdefault(d["name"], []).append(nd["linksTo"])
        for name, d in dims.items():
            exit_node = d["Bramble"]["dimension"].get("linksTo")
            if exit_node not in node_names:
                err(f"{name}: dimension exit node {exit_node} does not exist")
            if "staticPosition" not in d.get("Orbit", {}):
                err(f"{name}: bramble dimensions need Orbit.staticPosition")

        def cycle(n, stack):
            if n in stack:
                return True
            return any(cycle(m, stack | {n}) for m in edges.get(n, []))
        for name in dims:
            if cycle(name, frozenset()):
                err(f"{name}: dimensions link to each other in a loop - this hard-crashes the game unless preventRecursionCrash is set")
        vparent = sysdata.get("Vessel", {}).get("vesselSpawn", {}).get("parentBody")
        if vparent and vparent not in {d["name"] for _, d in s["bodies"]}:
            err(f"systems/{sysname}.json: Vessel parentBody {vparent} does not exist")
        if sysdata.get("Vessel", {}).get("promptFact"):
            need_fact(f"systems/{sysname}.json Vessel.promptFact", sysdata["Vessel"]["promptFact"])

        spawn_ids = {sp.get("id") for _, d in s["bodies"] for sp in d.get("Spawn", {}).get("shipSpawnPoints", [])}
        if sysdata.get("warpDriveSpawnPointID") and sysdata["warpDriveSpawnPointID"] not in spawn_ids:
            err(f"systems/{sysname}.json: warpDriveSpawnPointID {sysdata['warpDriveSpawnPointID']} does not exist")

        unrevealed = set(s["facts"]) - revealed_somewhere
        for fid in sorted(unrevealed):
            err(f"{sysname}: fact {fid} can never be revealed")

    for path, cond in conditions_used:
        if cond not in conditions_set:
            err(f"{rel(path)}: condition {cond} is never set")
    return per_system


conditions_used = []


def check_text(body_path, t, need_fact):
    path = os.path.join(MOD, t["xmlFile"])
    root = ET.parse(path).getroot()
    blocks = root.findall("TextBlock")
    ids = [int(b.findtext("ID")) for b in blocks]
    if len(set(ids)) != len(ids):
        err(f"{rel(path)}: duplicate TextBlock IDs")
    for b in blocks:
        pid = b.findtext("ParentID")
        if pid and int(pid) not in ids:
            err(f"{rel(path)}: ParentID {pid} does not exist")
    if t["type"] in ("recorder", "computer", "preCrashRecorder", "preCrashComputer"):
        for i, b in enumerate(blocks):
            want = None if i == 0 else str(ids[i - 1])
            if b.findtext("ParentID") != want:
                err(f"{rel(path)}: {t['type']} text must be a linear chain (block {ids[i]})")
    if t["type"].startswith("cairn") or t["type"] == "trailmarker":
        if len(blocks) != 1:
            err(f"{rel(path)}: {t['type']} supports exactly one text block")
    # NH refuses to build a text whose arcInfo count differs from its block count
    if "arcInfo" in t and len(t["arcInfo"]) != len(blocks):
        err(f"{rel(body_path)}: arcInfo of {t['xmlFile']} has {len(t['arcInfo'])} entries but the text has {len(blocks)} blocks")
    limits = {"whiteboard": 3, "wall": 6, "preCrashComputer": 5, "scroll": 3}
    if t["type"] in limits and len(blocks) > limits[t["type"]]:
        err(f"{rel(path)}: {len(blocks)} blocks do not fit on a {t['type']} (max {limits[t['type']]}) - the arcs run over the edge")
    if t["type"] == "scroll":
        err(f"{rel(body_path)}: loose scroll {t['xmlFile']} can only be read inside a whiteboard socket - use a whiteboard with text instead")
    for rf in root.iter("RevealFact"):
        need_fact(rel(path), rf.findtext("FactID"))
        for c in rf.findtext("Condition").split(","):
            if int(c) not in ids:
                err(f"{rel(path)}: reveal condition uses unknown block {c}")


# ---------------------------------------------------------------------------------- 4
def check_placement(bodies):
    for path, data in bodies.items():
        hm = data.get("HeightMap")
        if not hm:
            continue
        img = np.array(Image.open(os.path.join(MOD, hm["heightMap"])).convert("L"))
        H, W = img.shape
        if hm.get("resolution") != W // 4:
            warn(f"{rel(path)}: HeightMap.resolution {hm.get('resolution')} does not match the texture width ({W}); NH wants width/4")
        lo, hi = hm["minHeight"], hm["maxHeight"]
        water = data.get("Water", {}).get("size")

        def terrain(v):
            v = v / np.linalg.norm(v)
            lon = math.degrees(math.atan2(v[2], v[0]))
            lat = math.degrees(math.acos(max(-1, min(1, -v[1]))))
            sx = W * lon / 360
            sx = sx + W if sx < 0 else sx
            col = min(int(sx), W - 1)
            row = H - 1 - min(int(H * lat / 180), H - 1)
            # the mesh interpolates between vertices; use the local min/max as tolerance band
            win = img[max(0, row - 2):row + 3, [(col + d) % W for d in range(-2, 3)]]
            return lo + win.min() / 255 * (hi - lo), lo + win.max() / 255 * (hi - lo)

        props = data.get("Props", {})
        items = []
        path_key = {v: k for k, v in P.items()}
        for d in props.get("details", []):
            if d.get("alignRadial") and not d.get("isRelativeToParent") and d.get("rename") not in FLOATING_OK and d.get("path") not in EFFECTS:
                sink = abs(GROUND.get(path_key.get(d.get("path")), GROUND["default"])) * max(d.get("scale", 1.0), 1.0)
                items.append((d.get("rename") or d.get("path", "")[-40:], d["position"], sink))
        for t in props.get("translatorText", []):
            if not t.get("isRelativeToParent"):
                items.append((t.get("rename", t["xmlFile"]), t["position"], 0))
        for key in ("warpReceivers", "warpTransmitters"):
            for w in props.get(key, []):
                items.append((w.get("rename", key), w["position"], 0))
        for r in props.get("remotes", []):
            if "platform" in r:
                items.append((r["platform"].get("rename", r["id"]), r["platform"]["position"], 0))
            for st in r.get("stones", []):
                items.append((st.get("rename", r["id"]), st["position"], 0))
        for g in props.get("socketQuantumGroups", []):
            for i, sck in enumerate(g["sockets"]):
                items.append((f"{g.get('rename')} socket {i}", sck["position"], 0))
        for name, pos, sink in items:
            v = np.array([pos["x"], pos["y"], pos["z"]], float)
            r = np.linalg.norm(v)
            tmin, tmax = terrain(v)
            if r < tmin - 1.0 - sink:
                err(f"{rel(path)}: '{name}' is buried {tmin - r:.1f} m below the terrain")
            elif r > tmax + 2.5:
                err(f"{rel(path)}: '{name}' floats {r - tmax:.1f} m above the terrain")
            if water and r < water - 0.5:
                warn(f"{rel(path)}: '{name}' is under water ({water - r:.1f} m deep)")
        # floor text needs its 5.4 x 3.6 m field free of other objects
        floors = [(t.get("rename"), np.array([t["position"][k] for k in "xyz"])) for t in props.get("translatorText", [])
                  if t["type"] == "wall" and not t.get("isRelativeToParent")]
        for fname, fpos in floors:
            for name, pos, _ in items:
                if name == fname:
                    continue
                dist = np.linalg.norm(np.array([pos[k] for k in "xyz"]) - fpos)
                if dist < 3.5:
                    err(f"{rel(path)}: '{name}' stands {dist:.1f} m from the floor text '{fname}' (needs 3.5 m)")


# structures that are placed above the ground on purpose (station and wreck hang next to their rock)
FLOATING_OK = {"Sondenkanone_Wrack", "Sonnenwacht_Station"}
# light effects that may hang in the air
EFFECTS = {P["light_beam"], P["warp_particles"]}


def audio_types():
    """AudioType names from the New Horizons docs next to the schemas (empty if they are not there)."""
    if not SCHEMA_DIR:
        return set()
    doc = os.path.join(SCHEMA_DIR, "nhsrc", "docs", "src", "content", "docs", "reference", "audio-enum.md")
    if not os.path.exists(doc):
        return set()
    names = set()
    with open(doc, encoding="utf-8") as f:
        for line in f:
            cells = [c.strip(" *") for c in line.strip().strip("|").split("|")]
            if len(cells) == 2 and cells[1].strip().isdigit():
                names.add(cells[0].strip())
    return names


AUDIO_TYPES = audio_types()


def code_conditions():
    """Conditions a C# part of the addon sets itself (string constants in <mod>.Source/*.cs)."""
    found = set()
    for path in glob.glob(MOD.rstrip(os.sep) + ".Source/**/*.cs", recursive=True):
        with open(path, encoding="utf-8") as f:
            found.update(re.findall(r'"([A-Z][A-Z0-9_]{3,})"', f.read()))
    return found


def main():
    bodies = {p: load_json(p) for p in glob.glob(os.path.join(MOD, "planets", "**", "*.json"), recursive=True)}
    systems = {p: load_json(p) for p in glob.glob(os.path.join(MOD, "systems", "*.json"))}
    check_schemas(bodies, systems)
    check_consistency(bodies, systems)
    check_placement(bodies)
    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"{len(errors)} errors, {len(warnings)} warnings")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
