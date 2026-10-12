# Das Dornenlabyrinth Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A new NH mod in which a drifting bramble seed leads into an infinite, fixed, colour-coded labyrinth of bramble dimensions, with room types and a Bramble Heart.

**Architecture:**
- Every room type is exactly one NH dimension with a pool of nodes.
- A pure C# graph (`MazeGraph`) defines the infinite maze.
- Before each warp, the DLL retargets, recolours and shows or hides the nodes of the target room. This is a Harmony prefix on `FogWarpVolume.WarpDetector`.

**Tech Stack:** Python 3 (NH configs), Blender 4.2 headless (OBJ), C# net48 (OWML 2.15.5, game libs 1.1.16, HarmonyLib), xunit net8.0.

**Spec:** `docs/superpowers/specs/2026-10-11-dornenlabyrinth-design.md`

## Global Constraints

- **Mod:** folder `Zeki.Dornenlabyrinth`, uniqueName `Zeki.Dornenlabyrinth`, name "Das Dornenlabyrinth", DLL `ZekiDornenlabyrinth.dll`, version 0.1.0. It depends on `xen.NewHorizons`. All in-game text is German.
- **Prefixes:** facts and conditions use `ZEKIDL_`; dimension bodies are named `Labyrinth_<Typ>` (the RoomType name).
- **Nodes:** names are `ZEKIDL_<Typ>_K<i>` for adult nodes (scale 0.5) and `ZEKIDL_<Typ>_S<i>` for baby seeds (`isSeed`, scale 1). The entrance node is `ZEKIDL_Treibsamen` (scale 1). The Vorhof has its exit to the outside through its outer boundary; its `linksTo` is `ZEKIDL_Treibsamen`.
- **Commands.** Here `S=/tmp/claude-0/-home-user-Adblocker/760f3492-aa30-5b98-8853-56b9a44b1ed2/scratchpad`.

  | Step | Command | Pass condition |
  |---|---|---|
  | Validate | `python3 tools/nh_validate.py Zeki.Dornenlabyrinth --schemas $S/schemas` | 0 errors, 0 warnings |
  | Mesh check | `python3 tools/obj_check.py Zeki.Dornenlabyrinth/assets/models` | 0 flipped faces |
  | DLL | `cd Zeki.Dornenlabyrinth.Source && $S/dotnet/dotnet build -c Release` | 0 warnings |
  | Tests | `$S/dotnet/dotnet test Zeki.Dornenlabyrinth.Tests` | all pass |
  | Blender | `$S/blender/blender-4.2.3-linux-x64/blender -b -P tools/labyrinth_models.py -- Zeki.Dornenlabyrinth $S/dlprev` | |

- Commits end with the session's two trailer lines. Push to `claude/laughing-gauss-a21jnq`.

## Review Focus

1. **Stuck:** the player must never be stuck. Whatever the DLL fails to set up, the NH default targets (the Vorhof) and the Vorhof's way out keep working. Task 5 configures every pool node with `linksTo` set to the Vorhof; Task 6 logs every failed lookup and leaves the node's NH target in place.
2. **Probe or ship through a node:** the maze must not desync. Only the player's detector advances the walk; other detectors use the links as they are. Task 6 tests this through `MazeWalk` (a non-player entry does not push).
3. **Flying back out through the wall:** this returns to the instance the player came from, even many rooms deep, and at the Vorhof it leads outside. Task 3 tests the back stack, its cap of 64 and an empty stack.
4. **The heat chamber:** damage only grows while the player stays in the heat chamber and resets on leaving. Task 3 tests `HeatAfter`.
5. **After taking the heart:** green stays green so the player can escape; all other exits are red. Task 2 tests `bleeding`.

---

### Task 1: Scaffold (mod folder, DLL project, test project)

**Files:**
- Create:
  - `Zeki.Dornenlabyrinth.Source/ZekiDornenlabyrinth.csproj`
  - `Zeki.Dornenlabyrinth.Source/ZekiDornenlabyrinth.cs`
  - `Zeki.Dornenlabyrinth.Source/INewHorizons.cs` (copy of Verdornt's)
  - `Zeki.Dornenlabyrinth.Tests/ZekiDornenlabyrinth.Tests.csproj`
  - `Zeki.Dornenlabyrinth.Tests/ScaffoldTests.cs`
- Pattern: copy `Zeki.Verdornt.Source/ZekiVerdornt.csproj` (with AssemblyName and namespace `ZekiDornenlabyrinth`) and `Zeki.Verdornt.Tests` (it links `..\Zeki.Dornenlabyrinth.Source\Logic\*.cs`).

**Produces:**
- `public class ZekiDornenlabyrinth : ModBehaviour` with:
  - `static Instance`, `INewHorizons NewHorizons`;
  - `Log(string, bool warning=false)`, `static Notify(string, float)`;
  - `Start` that loads the NH configs, applies Harmony `PatchAll`, and subscribes to the star-system-loaded event;
  - for `"SolarSystem"`: `Guard("Labyrinth", () => Labyrinth.Setup(this))` and `Guard("Herz", () => BrambleHeart.Setup(this))`.
- `ScaffoldTests.LogicCompiles` asserts `MazeGraph.Start == 0UL`.

- [ ] **Step 1:** Write the test, then run it. Expected: FAIL to compile (`MazeGraph` is missing). Task 2 makes it pass.
- [ ] **Step 2:** Commit the scaffold, together with Task 2.

### Task 2: MazeGraph (TDD)

**Files:** Create `Zeki.Dornenlabyrinth.Source/Logic/MazeGraph.cs`; Test `Zeki.Dornenlabyrinth.Tests/MazeGraphTests.cs`.

**Produces** (namespace `ZekiDornenlabyrinth`, no Unity types):
- `public enum RoomType { Vorhof, Dornengang, Dornenwald, Hitzekammer, Frostkammer, Nest, Samenkammer, Nebelkammer, Leere, Stroemung, Echokammer, Wrack, Spiegelkammer, Herzpfad, Herzkammer }`
- `public enum ExitColor { Normal, Rot, Gruen, Gelb, Lila }`
- `public readonly struct Exit { int Slot; bool Seed; ExitColor Color; ulong Target; int Vanilla; }`
  - `Slot` is the index into the room's pool (adult nodes 0..K-1, seeds 0..S-1).
  - `Vanilla` is the index into `MazeGraph.VanillaBodies` for Gelb, else -1.
- `public sealed class Room { public ulong Id; public RoomType Type; public int H; public int Depth; public List<Exit> Exits; }`
- `public static class MazeGraph`:
  - `const ulong Start = 0`
  - `static readonly string[] VanillaBodies = { "DB_HubDimension_Body", "DB_EscapePodDimension_Body", "DB_PioneerDimension_Body", "DB_AnglerNestDimension_Body", "DB_ClusterDimension_Body", "DB_SmallNest_Body", "DB_VesselDimension_Body" }`
  - `static (int nodes, int seeds) Pool(RoomType t)`: the spec 5 table (Vorhof 3/2, Dornengang 4/3, Dornenwald 4/3, Hitzekammer 1/6, Frostkammer 3/2, Nest 3/1, Samenkammer 1/8, Nebelkammer 3/2, Leere 1/0, Stroemung 3/2, Echokammer 3/2, Wrack 3/1, Spiegelkammer 4/0, Herzpfad 3/2, Herzkammer 1/0)
  - `static ulong Id(RoomType type, int h, int depth, ulong hash)`: packs type in bits 0–3, h in 4–11, depth (capped 255) in 12–19, and hash in the rest. Instance 0 is the Vorhof with h 9, depth 0.
  - `static Room Get(ulong id, bool bleeding = false)`

**Rules** (spec 4 and 5): randomness is SplitMix64 seeded from the id; child hash = `mix(id * 31 + slot + (seed ? 1000 : 0))`.
- Every room shows all its pool nodes and seeds as exits, except the Leere, which shows its single node.
- **Lila:** exactly one per room with `h ≤ 9` on the heart path. The Vorhof always has one. A room reached through lila has `h - 1`. Lila from `h == 1` targets a Herzkammer.
- **Gruen:** in about 1/4 of rooms one exit is green; it targets `Start`.
- **Gelb:** in about 1/7 of rooms one exit is yellow, with `Vanilla` = hash % 7.
- **Rot:** only at depth ≥ 2, in about 1/5 of rooms one exit; it targets a Nest.
- **Normal:** targets a type from the spec 5 distribution, with h in 6..12. Targets with `h ≤ 3` are a Herzpfad half the time.
- **Hitzekammer:** all seeds are Normal and target a Hitzekammer. The adult node is the way out (Normal, any other type).
- **Spiegelkammer:** all exits but the last target a Spiegelkammer with h = min(h + 1, 12). The last exit is Normal.
- **Herzkammer:** one exit, Gruen.
- **Vorhof:** no Rot.
- **bleeding:** every exit that is not Gruen becomes Rot and targets a Nest.

**Test names and assertions:**
- `SameIdSameRoom`: `Get(x)` equals `Get(x)` (type, h, every exit's colour and target) for 50 ids.
- `StartIsVorhofWithLila`: `Get(0)` has type Vorhof, h 9, exactly one Lila, no Rot.
- `LilaCountsDownToTheHeart`: following the Lila exit from `Start` 9 times reaches a Room whose type is Herzkammer.
- `RotLeadsToANest`: for 2000 random ids, every Rot exit's target room type is Nest, and no Rot appears at depth < 2.
- `GruenLeadsHome`: every Gruen target is `Start`.
- `GelbHasAVanillaIndex`: every Gelb exit has `Vanilla` in 0..6, and every other exit has -1.
- `HeatSeedsLoopIntoHeat`: in a Hitzekammer, every seed exit targets type Hitzekammer and the node exit does not.
- `PoolSizesMatchExits`: the exits' slots stay within `Pool(type)`.
- `HerzkammerOnlyGreen`: the Herzkammer has one exit, Gruen.
- `BleedingKeepsGreenTurnsRestRed`: `Get(id, true)` has no Normal, Gelb or Lila exits; its Gruen exits stay where `Get(id)` had them.

- [ ] **Step 1:** Write the tests. Run them. Expected: compile FAIL.
- [ ] **Step 2:** Implement. Run the tests. Expected: all pass.
- [ ] **Step 3:** Commit `Dornenlabyrinth: scaffold and maze graph`.

### Task 3: MazeWalk (TDD)

**Files:** Create `Logic/MazeWalk.cs`; Test `MazeWalkTests.cs`.

**Produces** `public sealed class MazeWalk`:
- `ulong Current` (starts at `MazeGraph.Start`)
- `int Heat`
- `int Count`
- `void Enter(ulong from, int slot, bool seed, ulong to)`: pushes `(from, slot, seed)`, sets `Current = to`, updates `Heat` with `HeatAfter`. The stack is capped at 64 and drops the oldest entry.
- `(ulong room, int slot, bool seed)? Back()`: pops; sets `Current` to the popped room; sets `Heat` to 0; returns null when empty and leaves `Current` at Start.
- `void Reset()`
- `static int HeatAfter(RoomType from, RoomType to, int heat)`: to Hitzekammer from Hitzekammer gives heat + 1; to Hitzekammer from elsewhere gives 1; else 0.

**Tests:**
- `BackReturnsWhereYouCameFrom`
- `BackOnEmptyIsNull`
- `StackIsCappedAt64`: after 70 Enter calls, 64 Back calls succeed and the 65th returns null.
- `HeatGrowsInsideTheHeatChamber`: 1, 2, 3.
- `HeatResetsOnLeaving`
- `BackResetsHeat`

- [ ] **Step 1:** Write the tests. Expected: FAIL.
- [ ] **Step 2:** Implement. Expected: PASS.
- [ ] **Step 3:** Commit `Dornenlabyrinth: maze walk (back stack, heat)`.

### Task 4: Blender models

**Files:** Create `tools/labyrinth_models.py`. It reuses helpers by `exec` of the helper part of `tools/verdornt_models.py`: everything above `# ---- the bodies`.

**Produces** OBJs in `Zeki.Dornenlabyrinth/assets/models`:
- `farbkranz`: a thorned ring, 1.0 m radius, glow material slot `Kranzlicht`. The DLL tints it per colour and scales it to the node.
- `wasserkristalle`: a cluster about 40 m, `DornEis`.
- `eisblock`: a translucent block about 30 × 14 × 14 m around a frozen fish, `NomaiGlas`.
- `wrack`: Hearthian ship hull plates, a cockpit ring and a landing leg, about 25 m, materials `Holz` and `Metall`.
- `notiz`: a paper sheet on a stake, `Papier`.
- `herz`: a pulsing purple seed core of radius 1.2 inside a thorn cage, `Herzlicht` glow.

Previews go to `$S/dlprev`.

- [ ] **Step 1:** Write the script, run Blender, run the mesh check. Expected: 0 flipped faces. Look at the previews.
- [ ] **Step 2:** Commit `Dornenlabyrinth: Blender models`.

### Task 5: NH configs (build script)

**Files:** Create `tools/labyrinth_build.py`, `tools/labyrinth_texts.py` (Gneis's notes as DialogueTree XML) and `tools/labyrinth_shiplog.py`. Generated: `Zeki.Dornenlabyrinth/{manifest.json, default-config.json, addon-manifest.json, planets/*.json, planets/dialogue/*.xml, planets/shiplogs/*.xml, assets/labyrinth.json, assets/models/placements.json}`.

**Produces:**
- **Treibsamen body:**
  - Orbit primary Sun, semiMajorAxis 18000;
  - node `ZEKIDL_Treibsamen` → `Labyrinth_Vorhof`;
  - signal "Treibsamen" on frequency "Dornenrufe";
  - ship log entry `ZEKIDL_TREIBSAMEN`.
- **15 dimensions `Labyrinth_<Typ>`:**
  - radius and fog per spec 5;
  - `vinePrefab`: `hub` for the Vorhof, Dornengang and Herzpfad; `cluster` for the Dornenwald; `smallNest` otherwise; `none` for the Leere;
  - exit `linksTo` = `ZEKIDL_Treibsamen`;
  - pool nodes and seeds at fixed spherical positions (0.55 R, seed per type), all with `linksTo` = `Labyrinth_Vorhof`;
  - reveal volume `ZEKIDL_<TYP>_FOUND`.
- **Per-room content:**
  - Hitzekammer: hazardVolume heat, radius R, damagePerSecond 4, rename `ZEKIDL_Hitze`.
  - Frostkammer: crystals, 2 eisblock props, a skeleton detail (`nh_props` `skeleton`), a directional volume with force 0 as drag.
  - Nest: 2 anglerfish details (`P["angler"]`).
  - Stroemung: directional volume, force 6.
  - Echokammer: 4 signals named "Echo" on "Dornenrufe".
  - Wrack: wreck plus notiz with dialogue `Gneis_Wrack`.
  - Vorhof: notiz `Gneis_Farben`.
  - Herzpfad: notiz `Gneis_Herzpfad`.
  - Herzkammer: herz as an NH item ("Bramble-Herz", itemType "BrambleHerz", pickupFact `ZEKIDL_HERZ_GENOMMEN`) plus light.
- **`assets/labyrinth.json`:** `{"raeume": {"<Typ>": {"body": "Labyrinth_<Typ>", "knoten": ["ZEKIDL_<Typ>_K0", …], "samen": [...]}}}`, in the same order as `MazeGraph.Pool`.
- **Ship log:**
  - curiosity `ZEKIDL_LABYRINTH` with entries `ZEKIDL_TREIBSAMEN`, `ZEKIDL_FARBEN` (rumors from the Vorhof note) and `ZEKIDL_HERZ`;
  - every entry linked by a SourceID;
  - entryPositions far below (y −3000);
  - ship log facts revealed by the DLL use string constants in the DLL.

- [ ] **Step 1:** Write the scripts and run them. Validate. Expected: 0 errors, 0 warnings.
- [ ] **Step 2:** Commit `Dornenlabyrinth: NH configs`.

### Task 6: Labyrinth runtime

**Files:** Create `Labyrinth.cs`, `NodeTint.cs`, `WarpPatch.cs`.

**Consumes:** `MazeGraph`, `MazeWalk`, `labyrinth.json`.

**Produces:**
- `Labyrinth.Setup(mod)`:
  - finds each room's body (`NewHorizons.GetPlanet`), its `OuterFogWarpVolume` and its pool nodes by name, deep search in the body. Each node has an `InnerFogWarpVolume`.
  - finds the vanilla bodies' `OuterFogWarpVolume`s;
  - logs counts;
  - configures the Vorhof as instance 0.
- `Labyrinth.Configure(Room room)`:
  - for each pool node: show the exit nodes (SetActive), hide the rest;
  - set `_linkedOuterWarpVolume` to the target type's outer volume, or the vanilla one for Gelb;
  - tint via `NodeTint.Apply(node, color)`: the point light colour, the light shafts' material colour and a `farbkranz` child, created once and scaled by the node's lossyScale.
- `WarpPatch`: Harmony prefix `FogWarpVolume.WarpDetector(FogWarpDetector detector, ref FogWarpVolume linkedWarpVolume)`.
  - **Player, through one of our inner nodes:**
    1. Look up the exit.
    2. `Configure(Get(target, Bleeding))`.
    3. Set the target room's outer `_linkedInnerWarpVolume` to the node just used.
    4. Set `linkedWarpVolume` to the target's outer volume.
    5. `walk.Enter`.
    6. Apply the heat: the HazardVolume `_damagePerSecond` = 4 × Heat, with a notification "HITZE STUFE n".
  - **Player, through one of our outer volumes:** call `walk.Back()` and configure the previous instance. Its outer volume links back to the node it was entered by, kept from the stack. At the Vorhof the outer volume keeps `ZEKIDL_Treibsamen`.
  - **Non-player detectors:** untouched.
- On scene load: `walk.Reset()`.

- [ ] **Step 1:** Implement and build. Expected: 0 warnings. Run the tests. Expected: all pass.
- [ ] **Step 2:** Commit `Dornenlabyrinth: runtime (warp, retarget, colours)`.

### Task 7: The Bramble Heart

**Files:** Create `BrambleHeart.cs`.

**Produces:**
- `BrambleHeart.Setup(mod)` watches the ship log fact `ZEKIDL_HERZ_GENOMMEN`.
- Once it is revealed in this loop:
  - `Labyrinth.Bleeding = true`, then reconfigure the current room;
  - notify "DAS LABYRINTH BLUTET";
  - reveal `ZEKIDL_HERZ_BLUTET`.
- When the player is outside every labyrinth dimension while bleeding:
  - set `Calm = true`;
  - notify "DAS HERZ SINGT. DIE ANGLERFISCHE SCHLAFEN.";
  - reveal `ZEKIDL_HERZ_SINGT`.
- Harmony prefix `AnglerfishController.ChangeState(AnglerState newState)`: returns false while `Calm` is true and newState is Investigating or Chasing.
- A static flag, reset on scene load.

- [ ] **Step 1:** Implement, build and test.
- [ ] **Step 2:** Commit `Dornenlabyrinth: the Bramble Heart`.

### Task 8: Release

- **README** (German): the story, the colours, the rooms, the heart, a walkthrough, a test list.
- **Zip:** `releases/Zeki.Dornenlabyrinth_v0.1.0.zip`.
- Run every command. Do a final review. Push. Update the PR.
