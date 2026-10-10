# Verdornt 0.2.0 – Planeten und Dornensprache: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The four planets of Dornenkranz are rebuilt as bramble cores whose roots hold the planets' remains. Each gets a station, texts and a node. A new bramble language is learned word by word.

**Architecture:**
- **Blender** (`tools/verdornt_models.py`) builds bodies, stations and language props, and writes anchors.
- **The build script** (`tools/verdornt_build.py` plus its text, ship-log and language modules) turns the anchors into NH configs, `placements.json` and `sprache.json`.
- **The DLL** places the OBJ models (existing `ModelPlacer`) and adds `BrambleScript` for the language window. Its pure logic lives in `Logic/Vocabulary.cs` and is unit-tested.

**Tech Stack:** Blender 4.2 (headless), Python 3, New Horizons configs, C# net48 (OWML 2.15.5, game libs 1.1.16), xunit (net8.0).

**Spec:** `docs/superpowers/specs/2026-10-11-verdornt-planeten-sprache-design.md`, which extends `docs/superpowers/specs/2026-10-10-verdornt-design.md`.

## Global Constraints

**Commands.** Here `S=/tmp/claude-0/-home-user-Adblocker/760f3492-aa30-5b98-8853-56b9a44b1ed2/scratchpad`.

| Step | Command |
|---|---|
| Blender | `$S/blender/blender-4.2.3-linux-x64/blender -b -P tools/verdornt_models.py -- Zeki.Verdornt $S/vdprev` |
| Build | `python3 tools/verdornt_build.py Zeki.Verdornt` |
| Validate | `python3 tools/nh_validate.py <mod> --schemas $S/schemas` must print `0 errors, 0 warnings` for Zeki.Verdornt, Zeki.ISAE and Zeki.Schleiersystem |
| Mesh check | `python3 tools/obj_check.py Zeki.Verdornt/assets/models` must print `0 flipped faces` |
| DLL | `cd Zeki.Verdornt.Source && $S/dotnet/dotnet build -c Release` must print 0 warnings and 0 errors |
| Tests | `$S/dotnet/dotnet test Zeki.Verdornt.Tests` must pass |

**Rules.**
- Blender regenerates every OBJ with a different normal order. After each Blender run, revert the OBJs that the task did not mean to change: `git diff --name-only -- Zeki.Verdornt/assets/models | grep -v -E '<changed names>' | xargs -r git checkout --`.
- All in-game text is German.
- The `ZEKIVD_` prefix applies to all conditions, facts and node names.
- Version 0.2.0.
- Do not change the camp anchors on Erstling: `ERSTLING_LAGER = direction(32, 70)` and `ERSTLING_ANKUNFT = direction(26, 52)`. The camp, the arrival seed and the spawn must stay where they are.
- New persistent conditions:
  - `ZEKIVD_DORNSPRACHE`
  - `ZEKIVD_WORTKERN_<ID>`
  - `ZEKIVD_WORT_<WORT>`
  - `ZEKIVD_GLUTBRUECKE_AUS`, which comes from the marble tube `glutbruecke`, slot `aus`.
- Commit messages end with the two trailer lines from the session (Co-Authored-By, Claude-Session). Push to `claude/laughing-gauss-a21jnq`.

## Review Focus

1. **Landing on Nebelranke:** with `groundSize` removed, the player or ship must land on the islands and not fall into the planet. The core gets a collider too, so whatever falls lies on it. Task 2 checks the colliders; Task 4 checks that `groundSize` is gone and that `placements.json` puts the core model with a collider.
2. **Erstling camp after the crust rework:** the camp, the arrival seed and the tower stand on solid crust, not over a canyon. Task 2 keeps every canyon at least 0.35 rad away from the camp and arrival anchors, and asserts that in the Blender script.
3. **The language window and the translator:** it opens only while the translator is drawn and aimed at a script within 6 m. It closes on stowing, looking away, death and scene change, and never stays on screen. Task 7 owns it: the window is destroyed with the scene and checks tool mode every frame.
4. **A typo in a text** (`{wort}` that does not exist, an unclosed `{`): the build must fail, not the game. Tasks 5 and 6 cover this with `Vocabulary.Validate` (tests) and a validator check in `nh_validate.py`.
5. **Word notifications:** "NEUES WORT" appears once per word, not every loop. Task 5 has a test; Task 7 sets `ZEKIVD_WORT_<WORT>` and only notifies when it was not set before.

---

### Task 1: Blender helpers for core, roots and crust

**Files:**
- Modify: `tools/verdornt_models.py`, new helpers after `displaced_ball`.

**Interfaces:**
- Produces (Blender, coordinates z-up, radii in metres):
  - `bramble_core(name, R, M, rnd, light) -> list[Object]`: 20–30 thick woven vines (`great_circle_vine` at radii 0.85–1.05 R, thickness 0.08–0.14 R) around a glowing sphere of radius 0.7 R. `light` is the material of the inner sphere: `M["seed"]` or a planet-specific glow.
  - `roots(name, R_core, targets, M, rnd) -> list[Object]`: for each target point (Vector), a tapered tube from the core surface to the target. It bends a little and forks once halfway with a 30–60 % side branch. At the end are 3–5 grip fingers (tapered tubes about 0.25 × root length) curling over the target. Thickness: 0.06 × R_core at the root, 0.02 × R_core at the end.
  - `crust_shard(name, R, centre_dir, ang, thickness, mat, rnd, flats=()) -> Object`: a spherical-shell cap of angular radius `ang` (rad) around `centre_dir`. The top lies at R and is displaced (noise 0.04 R). The bottom lies at R - thickness. The rim is jagged: ±15 % of `ang` per azimuth. `flats` (direction, angle) are kept flat at exactly R.

- [ ] **Step 1:** Add the three helpers.
- [ ] **Step 2:** Run Blender. In a temporary `__main__` probe, build `bramble_core("t", 80, M, rnd, M["seed"])` + `roots` to 5 targets at 200 m + 5 `crust_shard`s, and render the probe to `$S/vdprev/probe.png`. Expected: the PNG shows a vine knot with roots gripping five plates. Remove the probe afterwards.
- [ ] **Step 3:** Run the mesh check. Expected: `0 flipped faces`.
- [ ] **Step 4:** Commit `Verdornt: Blender helpers for bramble cores, roots and crust shards`.

### Task 2: The four planets rebuilt and previewed (delivery 1)

**Files:**
- Modify: `tools/verdornt_models.py`: `erstling`, `glutdorn`, `nebelranke_ranken` (renamed to `nebelranke`, export `nebelranke.obj`; delete the old OBJ), `hohlsamen`; `preview` cameras.

**Interfaces:**
- Consumes: Task 1 helpers.
- Produces anchors in `anchors.json` (all with `position` and `normal` in Unity coordinates, like `surface_anchor`):

| Group | Anchors |
|---|---|
| `erstling` | `ankunft`, `lager` (unchanged), `labor` (station floor at the bottom of the largest canyon), `labor_schrift`, `wortkern1`, `wortkern2`, `radius` |
| `glutdorn` | `werk` (top of the largest slab), `knoten_scholle` (top of the slab across the widest gap from `werk`), `bruecke_ein`, `bruecke_aus` (the two ends of the bridge gap), `schrift1`, `schrift2`, `wortkern1`, `wortkern2`, `knoten`, `radius` |
| `nebelranke` | `station` (largest island), `knoten`, `schrift1`, `schrift2`, `wortkern1`, `wortkern2`, `radius` (outer island radius) |
| `hohlsamen` | `observatorium`, `knoten` (at the crystal core), `schrift1`, `schrift2`, `wortkern1`, `wortkern2`, `radius` |

**The planets (values from spec 2.2):**

| Planet | Build |
|---|---|
| **Erstling** (R 260) | Core R 100, ice glow `M["ice"]`. Crust as one `crust_shard` per region: the sphere is divided into 9 regions, with 6 canyons 20–60 m wide between them, cut down to the core. No canyon closer than 0.35 rad to `ERSTLING_LAGER` or `ERSTLING_ANKUNFT` (assert in code). Roots grip over each canyon rim. Ice crystals and thorns stay as before, but only on the crust. |
| **Glutdorn** (R 220) | Core R 90 around a lava sphere R 55 (`M["ember"]`). 14 slabs: `crust_shard` with ang 0.18–0.32 and gaps of 15–40 m. Root bridges: tubes of radius 2.5 between 6 slab pairs, flattened on top. The ember cracks are random walks restricted to the slabs. |
| **Nebelranke** (R 640) | Core R 220. 12 islands: `crust_shard` with thickness 25–40 and ang chosen for 60–120 m across, at radius 420–560, inclined in a ring plane 25° to the orbit plane. The existing drifting vines and the seed-light spheres stay. |
| **Hohlsamen** (R 300) | Crystal core R 110 (`M["crystal"]` inner sphere). 10 husk splinters: `crust_shard` with ang 0.12–0.25, thickness 22, plus 6 broken ribs. A dense root net of 40 targets: 10 on the splinters, 30 free and ending in thorns. Crystal thorns grow outwards from the core. |

- [ ] **Step 1:** Rebuild the four functions.
- [ ] **Step 2:** In `erstling`, assert that the canyon-to-camp distance is at least 0.35 rad (Review Focus 2). Expected: the Blender run does not raise.
- [ ] **Step 3:** Run Blender, revert the unrelated OBJs, and run the mesh check. Expected: `0 flipped faces`, plus `erstling.obj`, `glutdorn.obj`, `nebelranke.obj` and `hohlsamen.obj` written.
- [ ] **Step 4:** Render a far view and a near view of each planet into `$S/vdprev/planet_<name>_{fern,nah}.png`. Check each image: core visible, roots visible, remains separated as specified.
- [ ] **Step 5:** In `verdornt_build.py`:
  - `placements.json` model name `nebelranke_ranken` becomes `nebelranke`, with collider.
  - Nebelranke: delete `groundSize` and set `surfaceSize` 560.
  - The `surfaceSize` of the other planets follows the `radius` anchor.
- [ ] **Step 6:** Run build and validation. Expected: `0 errors, 0 warnings`.
- [ ] **Step 7:** Commit `Verdornt: planets rebuilt as bramble cores holding their remains`, then send the 8 previews to the user (delivery 1) and continue without waiting.

### Task 3: Station models

**Files:**
- Modify: `tools/verdornt_models.py` (new functions, added to `buildings`), `tools/verdornt_build.py` (`placements()` props).

**Interfaces:**
- Produces OBJs. Each has its origin on the floor centre, +z up in Blender, and anchors in the group of the same name:

| OBJ | Anchors |
|---|---|
| `wurzellabor` | `computer1..3`, `uebersetzer`, `schrift` |
| `glutwerk` | `computer1..2`, `recorder1`, `schrift`, plus tube `roehre_glutbruecke` via `record_tube` with slots `ein`, `aus` |
| `glutbruecke` | separate model, so it can move; length = the `bruecke_ein`→`bruecke_aus` distance from Task 2 |
| `treibstation` | `computer1..2`, `recorder1`, `laterne1..3` |
| `kristallobservatorium` | `computer1..4`, `becken` |

- Station anchors are local to the station. The build script converts them to planet coordinates with the station's placement (the same pattern as `lager`/`to_planet`).
- The look follows the Nomai style of the existing models (`hull`, `copper`, `nomai_glow`):
  - **Wurzellabor:** a half-dome grown into by roots, with a workbench and the root holding the translator.
  - **Glutwerk:** a tower with heat fins and a copper boiler.
  - **Treibstation:** a platform on stilts with lanterns.
  - **Kristallobservatorium:** a ring hall with an open roof.

- [ ] **Step 1:** Add the five models and their anchors.
- [ ] **Step 2:** Run Blender, revert the unrelated OBJs, run the mesh check, and render the station previews. Expected: `0 flipped faces`.
- [ ] **Step 3:** Commit `Verdornt: Nomai stations for all four planets`.

### Task 4: Planets in the game: stations, texts, nodes, gates, bridge

**Files:**
- Modify:
  - `tools/verdornt_build.py`: `erstling`, a new `glutdorn()`, `nebelranke()`, a new `hohlsamen()`, `dimensions()`, `placements()`, `tubes()`, `setsConditions`
  - `tools/verdornt_texts.py`: 15 new texts
  - `tools/verdornt_shiplog.py`: entries `ZEKIVD_LABOR`, `ZEKIVD_GLUTWERK`, `ZEKIVD_TREIBSTATION`, `ZEKIVD_OBSERVATORIUM`, each with one explore fact `<ID>_FOUND` and one rumour from a text on another planet
  - `Zeki.Verdornt/README.md`

**Interfaces:**
- Consumes: the Task 2 and Task 3 anchors.
- Produces:
  - NH nodes `ZEKIVD_Glutdorn_Knoten` → `Glutpforte`, `ZEKIVD_Nebelranke_Knoten` → `Nebelpforte`, `ZEKIVD_Hohlsamen_Knoten` → `Hohlpforte`, each scale 0.5 and `alignRadial`.
  - The dimensions `Glutpforte`, `Nebelpforte` and `Hohlpforte` via `dimension(...)`:
    - radius 300,
    - fog in the planet colour: Glut `color(200,90,40)`, Nebel `color(70,160,90)`, Hohl `color(140,90,210)`,
    - exit node = the planet node,
    - a `vine_paths` plan,
    - reveal facts `ZEKIVD_GLUTPFORTE_FOUND`, `ZEKIVD_NEBELPFORTE_FOUND` and `ZEKIVD_HOHLPFORTE_FOUND`,
    - static positions far apart, more than 40 km from all existing ones.
  - Projection pool in the Kristallobservatorium:
    - an NH remote `ZEKIVD_OBSERVATORIUM` with its platform at the `becken` anchor,
    - an NH remote `ZEKIVD_HERZ` with its platform on Herzdorn: at local position `(0, 1180, 0)` (the outside of the cage), plus one stone in the observatory,
    - placing that stone shows Herzdorn from close up; this reveals `ZEKIVD_HERZ_BLICK`.
  - Tube `glutbruecke` on Glutdorn: action on `VD_Glutbruecke` with offset `aus` = the extension vector, 4 seconds, `traegt` 3.0.

Text content (German, characters as in spec 3.1, one Yarrow line per planet via `yarrow()`):

| Station | Texts | Content |
|---|---|---|
| Wurzellabor | 3 computers (Hyssop) | They tried to listen to the vines. The translator was grown into a root to hear them. The roots answered. |
| Glutwerk | 2 computers + 1 recorder (Hyssop, Rue) | The heat of the slabs comes from the core, not from the sun. The bridge was for the node. |
| Treibstation | 2 computers + 1 recorder (Rue) | The guardians (anglerfish) obey the vines. Rue heard "a fish that talks", which is the Ernesto hint. |
| Kristallobservatorium | 4 computers (Tansy) | Studying the language. Each text reveals one fact `ZEKIVD_SPRACHE_<N>` (N = 1..4) through `ShipLogConditions`; Task 6 uses these as word sources. |
| Glutpforte, Nebelpforte, Hohlpforte | 1 computer each | A short note of who was here, plus a hint at the deeper network |

- [ ] **Step 1:** Write the 15 texts.
- [ ] **Step 2:** Write the planet configs, the gates, the stations in `placements.json`, the bridge and its tube.
- [ ] **Step 3:** Write the ship log entries and add `ZEKIVD_GLUTBRUECKE_AUS` to `setsConditions`.
- [ ] **Step 4:** Run the build and validate all three mods. Expected: `0 errors, 0 warnings` for each. The Schleier regression must stay byte-identical: copy to scratch, run `schleier_build`, then `diff -rq`.
- [ ] **Step 5:** Build the DLL and run the tests. Expected: 0 warnings; all tests pass.
- [ ] **Step 6:** Commit `Verdornt: stations, texts, nodes and gates on every planet`.

### Task 5: Vocabulary logic (TDD)

**Files:**
- Create: `Zeki.Verdornt.Source/Logic/Vocabulary.cs`
- Test: `Zeki.Verdornt.Tests/VocabularyTests.cs`

**Interfaces:**
- Produces, in namespace `ZekiVerdornt`, with no Unity types (Newtonsoft field names match `sprache.json`):
  - `public class Word { public string id, de, laut; public bool grund; public List<string> quellen = new(); }`
  - `public class ScriptText { public string id, titel; public List<string> zeilen = new(); }`
  - `public class Language { public List<Word> woerter = new(); public List<ScriptText> texte = new(); }`
  - `public readonly struct Token { public readonly string Text; public readonly string WordId; }`, where `WordId == null` means fixed text
  - `public readonly struct Piece { public readonly string Text; public readonly bool Known; public readonly bool IsWord; }`
  - `public static class Vocabulary`:
    - `const string LanguageCondition = "ZEKIVD_DORNSPRACHE"`
    - `static string WordCondition(string id)` returns `"ZEKIVD_WORT_" + id.ToUpperInvariant()`
    - `static string KernCondition(string id)` returns `"ZEKIVD_WORTKERN_" + id.ToUpperInvariant()`
    - `static List<Token> Parse(string line)`: throws `FormatException` on an unclosed `{` or an empty `{}`
    - `static bool Learnable(Word w, Func<string,bool> condition, Func<string,bool> fact)`: true when `grund && condition(LanguageCondition)`, or when any source holds (`fact:X` → `fact(X)`, `kern:X` → `condition(KernCondition(X))`)
    - `static List<Piece> Render(string line, IReadOnlyDictionary<string,Word> words, Func<string,bool> known, bool canTranslate)`
    - `static void Validate(Language lang)`: throws `FormatException` naming the text and word for an unknown `{id}`, a duplicate word id, or a source without a `fact:`/`kern:` prefix

- [ ] **Step 1:** Write the failing tests:
  - `ParseSplitsWordsAndText`: `"{wir} tragen {licht}."` gives 4 tokens with WordIds `wir`, null, `licht`, null and the texts `" tragen "` and `"."`.
  - `ParseRejectsUnclosedBrace`: `"{wir tragen"` throws `FormatException`.
  - `ParseRejectsEmptyBraces`: `"a {} b"` throws.
  - `BaseWordsNeedTheTranslator`: grund word, condition false gives `Learnable == false`; condition true gives true.
  - `FactSourceTeaches`: `quellen ["fact:ZEKIVD_SPRACHE_1"]` is learnable when only that fact is revealed.
  - `KernSourceTeaches`: `"kern:NEBEL_1"` is learnable when condition `ZEKIVD_WORTKERN_NEBEL_1` is set.
  - `RenderShowsSoundsForUnknownWords`: words `wir` (laut `krrh`) and `licht` (de `Licht`), known = {licht}, so `"{wir} tragen {licht}."` renders as the pieces `("krrh", false, word)`, `(" tragen ", true, text)`, `("Licht", true, word)`, `(".", true, text)`.
  - `RenderWithoutTranslatorShowsOnlySounds`: with `canTranslate = false`, every word piece shows its `laut`, even if known.
  - `ValidateRejectsUnknownWord`: a text with `{nebel}` and no such word throws, with the message containing `nebel`.
  - `ValidateRejectsDuplicateIds`: two words `licht` throw.
  - `WordConditionIsUpperCase`: `WordCondition("licht") == "ZEKIVD_WORT_LICHT"`. This is the persistence key, so the word is announced once (Review Focus 5).
- [ ] **Step 2:** Run the tests. Expected: FAIL (`Vocabulary` does not exist).
- [ ] **Step 3:** Implement `Vocabulary.cs`.
- [ ] **Step 4:** Run the tests. Expected: all pass.
- [ ] **Step 5:** Commit `Verdornt: vocabulary logic of the bramble language`.

### Task 6: Language data, script and word-core models, validator check

**Files:**
- Create: `tools/verdornt_sprache.py` with `write_all(mod)` → `Zeki.Verdornt/assets/sprache.json`
- Modify:
  - `tools/verdornt_build.py`: call `verdornt_sprache.write_all`; `placements.json` gets `"schriften"` and `"wortkerne"`; NH `interactionVolumes` for the word cores and the translator
  - `tools/verdornt_models.py`: models `dornenschrift` (standing, about 2.2 × 1.6 m), `dornenschrift_boden` (flat, about 2 m), `verbrambelter_uebersetzer` (the Nomai translator shape overgrown by thin vines, about 0.6 m) and `wortkern` (a seed of about 0.35 m with `M["seed"]` glow)
  - `tools/nh_validate.py`: `check_language()` when `assets/sprache.json` exists
  - `Zeki.Verdornt/README.md`

**Interfaces:**
- Consumes: the Task 5 JSON shape (`woerter`/`texte`); the facts `ZEKIVD_SPRACHE_1..4` from Task 4; the anchors `schrift*`, `wortkern*`, `labor_schrift` and `uebersetzer`.
- Produces:
  - `sprache.json` with about 40 words, about 10 of them `grund`, and 12 texts. The content follows spec 4.5.
  - Word cores with IDs `ERSTLING_1`, `ERSTLING_2`, `GLUT_1`, `GLUT_2`, `NEBEL_1`, `NEBEL_2`, `HOHL_1`, `HOHL_2`, and one each in the three gates: `GLUTPFORTE`, `NEBELPFORTE`, `HOHLPFORTE`. Each is an NH interaction volume with prompt "Wortkern berühren", condition `ZEKIVD_WORTKERN_<ID>`, persistent, not reusable.
  - The translator: an interaction volume with prompt "Verbrambelten Übersetzer berühren", condition `ZEKIVD_DORNSPRACHE`, persistent, not reusable. The reveal fact `ZEKIVD_DORNSPRACHE_FAKT` goes in the ship-log entry `ZEKIVD_LABOR`.
  - `placements.json` entries:
    - `"schriften": [{"name", "body", "parentPath", "position", "rotation", "text", "boden": bool}]`
    - `"wortkerne": [{"id", "body", "position"}]`, which the DLL draws as models
  - `setsConditions` gains `ZEKIVD_WORT_<WORT>` for every word.
  - Every non-grund word has at least one source. Every text references only existing words, and every `schriften[].text` exists.

- [ ] **Step 1:** Write the validator check first, then run the validator on a hand-written broken `sprache.json` (a text with `{nebel}` and no such word). Expected: `ERROR ... sprache.json: text X uses unknown word nebel`. This is Review Focus 4.
- [ ] **Step 2:** Write `verdornt_sprache.py` with the vocabulary and the 12 texts.
- [ ] **Step 3:** Add the models, run Blender, revert the unrelated OBJs, run the mesh check. Expected: `0 flipped faces`.
- [ ] **Step 4:** Wire everything into the build, then build and validate all three mods. Expected: `0 errors, 0 warnings`.
- [ ] **Step 5:** Commit `Verdornt: the bramble language: words, texts, scripts and word cores`.

### Task 7: BrambleScript: placing, reading window, learning

**Files:**
- Create: `Zeki.Verdornt.Source/BrambleScript.cs`
- Modify:
  - `Zeki.Verdornt.Source/Models.cs`: `Placements` gains `List<ScriptPlacement> schriften` and `List<KernPlacement> wortkerne`
  - `Zeki.Verdornt.Source/ZekiVerdornt.cs`: `Guard("Dornensprache", () => BrambleScript.Setup(this))` in `Build` for the Verdornt system

**Interfaces:**
- Consumes: `Vocabulary`, `Language`, `Word` (Task 5); `ModelPlacer.Build(mod, PropPlacement, parent)` and `ModelPlacer.Parent` (existing); `sprache.json` (Task 6).
- Produces:
  - `public static void BrambleScript.Setup(ZekiVerdornt mod)`: loads `assets/sprache.json` and validates it (on error: log and return); places the `schriften` and `wortkerne` models; creates one `BrambleScript` reader object for the scene.
  - Every placed script gets a `ScriptMarker : MonoBehaviour { public string TextId; }`.

Behaviour (spec 4.2, 4.3):
- **Opening.** Each frame, the reader opens when all three hold:
  - `Locator.GetToolModeSwapper()?.IsInToolMode(ToolMode.Translator)` is true,
  - a `ScriptMarker` lies within 6 m of the camera,
  - its angle to the camera's forward direction is under 12°.
- **Closing.** Otherwise the window is hidden. The window is a `Canvas` (ScreenSpaceOverlay) child of the reader object, so it dies with the scene (Review Focus 3).
- **Window.**
  - The title is "UNBEKANNTE SPRACHE" without `ZEKIVD_DORNSPRACHE`, otherwise "DORNENSPRACHE – <titel>".
  - The rendered lines are joined with rich text: known words in white `#E8FFE8`, unknown sounds in green italics `<i><color=#7FD88A>…</color></i>`.
  - The font is `Resources.GetBuiltinResource<Font>("Arial.ttf")`, or the font of the game's `NomaiTranslatorProp` if found.
- **Learning.** Every 0.5 s, for each word that is not yet known: if `Learnable` holds with `PlayerData.GetPersistentCondition` and `Locator.GetShipLogManager().IsFactRevealed`, then the reader:
  1. sets `PlayerData.SetPersistentCondition(WordCondition(id), true)`,
  2. notifies `"NEUES WORT: <de>"`, but only when `ZEKIVD_DORNSPRACHE` is set,
  3. marks the word known.
- **Known.** `known(id)` = `GetPersistentCondition(WordCondition(id))`.

- [ ] **Step 1:** Implement `BrambleScript.cs` and the `Placements` fields.
- [ ] **Step 2:** Build the DLL. Expected: 0 warnings, 0 errors.
- [ ] **Step 3:** Run the tests. Expected: all pass.
- [ ] **Step 4:** Commit `Verdornt: reading and learning the bramble language`.

### Task 8: Release 0.2.0

**Files:**
- Modify:
  - `tools/verdornt_build.py`: `VERSION = "0.2.0"`
  - `Zeki.Verdornt/README.md`: new section "Neu in 0.2.0", the walkthrough per planet, the test list
  - the spec component table (`BrambleScript.cs`, `Vocabulary.cs`)
- Create: `releases/Zeki.Verdornt_v0.2.0.zip` (replaces the 0.1.1 zip)

- [ ] **Step 1:** Run every Global Constraints command. Expected: all green, and the Schleier regression is byte-identical.
- [ ] **Step 2:** Get a whole-branch review from a fresh reviewer and fix its findings.
- [ ] **Step 3:** Build the zip from the `Zeki.Verdornt` folder, as for 0.1.1. Commit `Verdornt 0.2.0: planets and the bramble language`, push, and update the PR description.
