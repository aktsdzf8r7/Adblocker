using Newtonsoft.Json;
using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEngine;

namespace ZekiDornenlabyrinth;

/// <summary>assets/labyrinth.json, written by tools/labyrinth_build.py: the node names of every room type.</summary>
public class LabyrinthData
{
    public string eingang;
    public Dictionary<string, RoomData> raeume = new();
}

public class RoomData
{
    public string body;
    public List<string> knoten = new();
    public List<string> samen = new();
}

/// <summary>
/// The infinite labyrinth at runtime (spec 3). Every room type is one New Horizons dimension with a pool of nodes;
/// before the player flies through one of them (WarpPatch), the target type's dimension is set up as the next room
/// instance: which nodes show, their colours and where they lead, and the way back through the wall. Whatever fails
/// here, the nodes keep the targets New Horizons gave them (the Vorhof), so the player never gets stuck.
/// </summary>
public static class Labyrinth
{
    public static readonly MazeWalk Walk = new();

    /// <summary>The heart was taken in this loop: every exit but the green ones is red (BrambleHeart.cs).</summary>
    public static bool Bleeding;

    public static bool Ready { get; private set; }

    private sealed class Rig
    {
        public RoomType Type;
        public GameObject Body;
        public OuterFogWarpVolume Outer;
        public InnerFogWarpVolume[] Nodes;
        public InnerFogWarpVolume[] Seeds;
        public HazardVolume Heat;
        /// <summary>The instance the dimension currently shows (null until set up).</summary>
        public ulong? Shown;

        public InnerFogWarpVolume Node(int slot, bool seed)
        {
            var pool = seed ? Seeds : Nodes;
            return slot >= 0 && slot < pool.Length ? pool[slot] : null;
        }
    }

    private static ZekiDornenlabyrinth _mod;
    private static readonly Dictionary<RoomType, Rig> Rigs = new();
    private static readonly Dictionary<InnerFogWarpVolume, (Rig rig, int slot, bool seed)> NodeIndex = new();
    private static readonly Dictionary<OuterFogWarpVolume, Rig> OuterIndex = new();
    private static readonly OuterFogWarpVolume[] Vanilla = new OuterFogWarpVolume[MazeGraph.VanillaBodies.Length];
    private static InnerFogWarpVolume _entrance;
    /// <summary>The target New Horizons gave every node (the Vorhof): where a node leads when its target is missing.</summary>
    private static readonly Dictionary<InnerFogWarpVolume, OuterFogWarpVolume> Original = new();
    /// <summary>Our baby seeds: New Horizons makes seeds scout-only, in the labyrinth the player flies through them.</summary>
    private static readonly HashSet<FogWarpVolume> PlayerSeeds = new();

    public static bool IsPlayerSeed(FogWarpVolume volume) => volume != null && PlayerSeeds.Contains(volume);

    // the ship and the player inside it can fly through the same volume together: decide once
    private static FogWarpVolume _lastVolume;
    private static float _lastTime = -10f;
    private static FogWarpVolume _lastLinked;

    public static void Reset()
    {
        Ready = false;
        Bleeding = false;
        Walk.Reset();
        Rigs.Clear();
        NodeIndex.Clear();
        Original.Clear();
        PlayerSeeds.Clear();
        OuterIndex.Clear();
        Array.Clear(Vanilla, 0, Vanilla.Length);
        _entrance = null;
        _lastVolume = _lastLinked = null;
        NodeTint.Reset();
    }

    public static void Setup(ZekiDornenlabyrinth mod)
    {
        _mod = mod;
        Reset();
        var file = Path.Combine(mod.ModHelper.Manifest.ModFolderPath, "assets/labyrinth.json");
        if (!File.Exists(file))
        {
            mod.Log("labyrinth.json fehlt - das Labyrinth bleibt beim Vorhof.", true);
            return;
        }
        var data = JsonConvert.DeserializeObject<LabyrinthData>(File.ReadAllText(file));
        foreach (RoomType type in Enum.GetValues(typeof(RoomType)))
        {
            if (!data.raeume.TryGetValue(type.ToString(), out var rd))
            {
                mod.Log($"labyrinth.json: Raum {type} fehlt.", true);
                continue;
            }
            mod.Guard("Raum " + type, () => Find(mod, type, rd));
        }
        _entrance = mod.NewHorizons.GetPlanet("Treibsamen")?.GetComponentsInChildren<InnerFogWarpVolume>(true).FirstOrDefault(n => n.name == data.eingang);
        if (_entrance == null) mod.Log($"Der Eingang {data.eingang} am Treibsamen fehlt.", true);
        for (var i = 0; i < Vanilla.Length; i++)
        {
            Vanilla[i] = GameObject.Find(MazeGraph.VanillaBodies[i])?.GetComponentInChildren<OuterFogWarpVolume>(true);
            if (Vanilla[i] == null) mod.Log($"Dark-Bramble-Dimension {MazeGraph.VanillaBodies[i]} nicht gefunden - gelbe Knoten dorthin werden normal.", true);
        }
        mod.Log($"Labyrinth: {Rigs.Count} von 15 Räumen, {NodeIndex.Count} Knoten, {Vanilla.Count(v => v != null)} von {Vanilla.Length} Dark-Bramble-Dimensionen.");
        Ready = Rigs.ContainsKey(RoomType.Vorhof);
        // New Horizons colours its nodes one frame after building them; ours come after that
        mod.StartCoroutine(AfterNewHorizons(mod));
    }

    private static void Find(ZekiDornenlabyrinth mod, RoomType type, RoomData rd)
    {
        var body = mod.NewHorizons.GetPlanet(rd.body);
        if (body == null)
        {
            mod.Log($"Dimension {rd.body} nicht gefunden.", true);
            return;
        }
        var outer = body.GetComponentInChildren<OuterFogWarpVolume>(true);
        var inner = new Dictionary<string, InnerFogWarpVolume>();
        foreach (var n in body.GetComponentsInChildren<InnerFogWarpVolume>(true)) inner[n.name] = n;
        InnerFogWarpVolume Lookup(string name)
        {
            if (inner.TryGetValue(name, out var n)) return n;
            mod.Log($"Knoten {name} in {rd.body} nicht gefunden - er behält sein Ziel (den Vorhof).", true);
            return null;
        }
        var rig = new Rig
        {
            Type = type,
            Body = body,
            Outer = outer,
            Nodes = rd.knoten.Select(Lookup).ToArray(),
            Seeds = rd.samen.Select(Lookup).ToArray(),
            Heat = type == RoomType.Hitzekammer ? body.GetComponentsInChildren<HazardVolume>(true).OrderBy(h => h.name == "ZEKIDL_Hitze" ? 0 : 1).FirstOrDefault() : null,
        };
        var (nodes, seeds) = MazeGraph.Pool(type);
        if (rig.Nodes.Length != nodes || rig.Seeds.Length != seeds)
            mod.Log($"{rd.body}: {rig.Nodes.Length}/{rig.Seeds.Length} Knoten/Samen, erwartet {nodes}/{seeds}.", true);
        if (outer == null) mod.Log($"{rd.body} hat keine äußere Nebelwand.", true);
        Rigs[type] = rig;
        if (outer != null) OuterIndex[outer] = rig;
        for (var i = 0; i < rig.Nodes.Length; i++)
            if (rig.Nodes[i] != null) NodeIndex[rig.Nodes[i]] = (rig, i, false);
        for (var i = 0; i < rig.Seeds.Length; i++)
            if (rig.Seeds[i] != null)
            {
                NodeIndex[rig.Seeds[i]] = (rig, i, true);
                OpenSeed(rig.Seeds[i]);
            }
        foreach (var n in NodeIndex.Keys.Where(n => !Original.ContainsKey(n))) Original[n] = n._linkedOuterWarpVolume;
    }

    /// <summary>
    /// A seed the player can fly into: not scout-only (WarpPatch), and its solid shell does not stop the player
    /// before the warp radius (the trigger volumes stay).
    /// </summary>
    private static void OpenSeed(InnerFogWarpVolume seed)
    {
        PlayerSeeds.Add(seed);
        foreach (var c in seed.GetComponentsInChildren<Collider>(true))
            if (!c.isTrigger) c.enabled = false;
    }

    private static IEnumerator AfterNewHorizons(ZekiDornenlabyrinth mod)
    {
        for (var i = 0; i < 3; i++) yield return null;
        mod.Guard("Vorhof", () => Show(MazeGraph.Get(MazeGraph.Start, Bleeding)));
        mod.Guard("Eisfisch", () => Rooms.Freeze(mod));
    }

    /// <summary>Whether the player is inside one of the labyrinth's dimensions.</summary>
    public static bool PlayerInside()
    {
        var outer = PlayerState.GetOuterFogWarpVolume() as OuterFogWarpVolume;
        return outer != null && OuterIndex.ContainsKey(outer);
    }

    /// <summary>Sets up the room the player is in again (after the heart was taken).</summary>
    public static void Refresh()
    {
        if (!Ready || !PlayerInside()) return;
        Show(MazeGraph.Get(Walk.Current, Bleeding));
    }

    private static bool VanillaExists(int i) => i >= 0 && i < Vanilla.Length && Vanilla[i] != null;

    /// <summary>Sets up the dimension of the room's type as this instance: nodes, colours, targets.</summary>
    private static void Show(Room room)
    {
        if (!Rigs.TryGetValue(room.Type, out var rig)) return;
        var colours = new List<string>();
        void Set(InnerFogWarpVolume node, int slot, bool seed)
        {
            if (node == null) return;
            var index = room.Exits.FindIndex(e => e.Slot == slot && e.Seed == seed);
            if (index < 0)
            {
                node.gameObject.SetActive(false);
                return;
            }
            var exit = Router.Effective(room, room.Exits[index], VanillaExists);
            node.gameObject.SetActive(true);
            var target = exit.Color switch
            {
                ExitColor.Gelb => Vanilla[exit.Vanilla],
                ExitColor.Gruen => Rigs.TryGetValue(RoomType.Vorhof, out var home) ? home.Outer : null,
                _ => Rigs.TryGetValue(MazeGraph.Get(exit.Target).Type, out var next) ? next.Outer : null,
            };
            node._linkedOuterWarpVolume = target != null ? target : Original.TryGetValue(node, out var nh) ? nh : node._linkedOuterWarpVolume;
            NodeTint.Apply(_mod, node, exit.Color);
            if (exit.Color != ExitColor.Normal) colours.Add($"{(seed ? "S" : "K")}{slot}={exit.Color}");
        }
        for (var i = 0; i < rig.Nodes.Length; i++) Set(rig.Nodes[i], i, false);
        for (var i = 0; i < rig.Seeds.Length; i++) Set(rig.Seeds[i], i, true);
        rig.Shown = room.Id;
        _mod.Log($"Raum {room.Type} #{room.Id:X} (Herzabstand {room.H}, Tiefe {room.Depth}): {(colours.Count == 0 ? "nur normale Knoten" : string.Join(", ", colours))}");
    }

    /// <summary>Called by WarpPatch before a fog warp volume warps something.</summary>
    public static void OnWarp(FogWarpVolume volume, FogWarpDetector detector, ref FogWarpVolume linked)
    {
        if (!Ready || detector == null) return;
        var player = detector.CompareName(FogWarpDetector.Name.Player) || (detector.CompareName(FogWarpDetector.Name.Ship) && PlayerState.IsInsideShip());
        // only the player's way moves the labyrinth; the scout and an empty ship use the links as they are
        if (!player || PlayerState.UsingNomaiRemoteCamera()) return;
        if (volume == _lastVolume && Time.time - _lastTime < 0.5f)
        {
            if (_lastLinked != null) linked = _lastLinked;
            return;
        }
        FogWarpVolume decided = null;
        if (volume is InnerFogWarpVolume inner)
        {
            if (inner == _entrance) decided = Enter();
            else if (NodeIndex.TryGetValue(inner, out var at)) decided = ThroughNode(inner, at.rig, at.slot, at.seed);
        }
        else if (volume is OuterFogWarpVolume outer && OuterIndex.TryGetValue(outer, out var rig))
        {
            decided = OutThroughWall(rig);
        }
        _lastVolume = volume;
        _lastTime = Time.time;
        _lastLinked = decided;
        if (decided != null) linked = decided;
    }

    /// <summary>In through the Treibsamen: the Vorhof, with the way out behind.</summary>
    private static FogWarpVolume Enter()
    {
        Walk.Reset();
        Show(MazeGraph.Get(MazeGraph.Start, Bleeding));
        var home = Rigs[RoomType.Vorhof];
        if (_entrance != null && home.Outer != null) home.Outer._linkedInnerWarpVolume = _entrance;
        Announce(RoomType.Vorhof, 0);
        return home.Outer;
    }

    private static FogWarpVolume ThroughNode(InnerFogWarpVolume node, Rig rig, int slot, bool seed)
    {
        var d = Router.ThroughNode(Walk, rig.Type, slot, seed, rig.Shown, Bleeding, VanillaExists);
        if (d.Restarted) _mod.Log($"Der Weg war aus dem Takt - neu angesetzt in {rig.Type} #{rig.Shown:X}.", true);
        switch (d.Kind)
        {
            case WarpKind.Vanilla:
                _mod.Log($"Gelber Knoten: hinaus nach {MazeGraph.VanillaBodies[d.Vanilla]}.");
                return Vanilla[d.Vanilla];
            case WarpKind.Home:
            {
                Show(d.Target);
                var home = Rigs[RoomType.Vorhof];
                if (_entrance != null && home.Outer != null) home.Outer._linkedInnerWarpVolume = _entrance;
                Announce(RoomType.Vorhof, 0);
                return home.Outer;
            }
            case WarpKind.Room:
            {
                if (!Rigs.TryGetValue(d.Target.Type, out var next) || next.Outer == null)
                {
                    _mod.Log($"Raum {d.Target.Type} fehlt - der Knoten behält sein Ziel.", true);
                    return null;
                }
                Show(d.Target);
                // out through the wall leads back out of this node
                next.Outer._linkedInnerWarpVolume = node;
                Announce(d.Target.Type, d.Target.Depth);
                ApplyHeat(next);
                return next.Outer;
            }
            default:
                _mod.Log($"Knoten {node.name}: kein Ausgang im Raum #{rig.Shown:X} - New Horizons entscheidet.", true);
                return null;
        }
    }

    private static FogWarpVolume OutThroughWall(Rig rig)
    {
        var back = Router.Back(Walk, Bleeding);
        if (back == null)
        {
            // the end of the way back: outside, as from the Vorhof
            Walk.Reset();
            _mod.Log($"Durch die Wand von {rig.Type}: hinaus.");
            return _entrance;
        }
        var (room, slot, seed) = back.Value;
        if (!Rigs.TryGetValue(room.Type, out var prev) || prev.Node(slot, seed) == null)
        {
            Walk.Reset();
            _mod.Log($"Der Rückweg nach {room.Type} fehlt - hinaus.", true);
            return _entrance;
        }
        Show(room);
        var peek = Walk.Peek();
        var way = peek == null ? _entrance : Rigs.TryGetValue(MazeGraph.Get(peek.Value.room).Type, out var before) ? before.Node(peek.Value.slot, peek.Value.seed) : null;
        if (prev.Outer != null && way != null) prev.Outer._linkedInnerWarpVolume = way;
        Announce(room.Type, room.Depth);
        ApplyHeat(prev);
        return prev.Node(slot, seed);
    }

    private static void ApplyHeat(Rig rig)
    {
        if (rig.Type != RoomType.Hitzekammer || rig.Heat == null) return;
        var level = Mathf.Max(1, Walk.Heat);
        rig.Heat._damagePerSecond = 4f * level;
        ZekiDornenlabyrinth.Notify($"HITZE STUFE {level}", 4f);
        _mod.Log($"Hitzekammer: Stufe {level}, {4 * level} Schaden pro Sekunde.");
    }

    private static void Announce(RoomType type, int depth) =>
        ZekiDornenlabyrinth.Notify(depth == 0 ? Name(type) : $"{Name(type)} · Tiefe {depth}", 3f);

    public static string Name(RoomType t) => t switch
    {
        RoomType.Nest => "ANGLERFISCH-NEST",
        RoomType.Stroemung => "STRÖMUNGSKAMMER",
        RoomType.Wrack => "WRACKKAMMER",
        _ => t.ToString().ToUpperInvariant(),
    };
}
