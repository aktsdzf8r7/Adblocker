using System;
using System.Collections.Generic;

namespace ZekiDornenlabyrinth;

public enum RoomType { Vorhof, Dornengang, Dornenwald, Hitzekammer, Frostkammer, Nest, Samenkammer, Nebelkammer, Leere, Stroemung, Echokammer, Wrack, Spiegelkammer, Herzpfad, Herzkammer }

public enum ExitColor { Normal, Rot, Gruen, Gelb, Lila }

/// <summary>One way out of a room: a node (or baby seed) of the room's pool, its colour and where it leads.</summary>
public readonly struct Exit
{
    public readonly int Slot;
    public readonly bool Seed;
    public readonly ExitColor Color;
    public readonly ulong Target;
    /// <summary>Index into MazeGraph.VanillaBodies for a yellow exit, else -1.</summary>
    public readonly int Vanilla;

    public Exit(int slot, bool seed, ExitColor color, ulong target, int vanilla = -1)
    {
        Slot = slot;
        Seed = seed;
        Color = color;
        Target = target;
        Vanilla = vanilla;
    }
}

/// <summary>A room instance of the infinite labyrinth.</summary>
public sealed class Room
{
    public ulong Id;
    public RoomType Type;
    /// <summary>Heart distance: purple exits lead to h - 1; at 0 lies the heart.</summary>
    public int H;
    /// <summary>Rooms since the entrance hall (capped at 255).</summary>
    public int Depth;
    public List<Exit> Exits = new();
}

/// <summary>
/// The infinite, fixed labyrinth (spec 2026-10-11 Dornenlabyrinth, sections 3-5). A room instance is a 64-bit id:
/// type (bits 0-3), heart distance (4-11), depth (12-19) and a hash (20-63). Everything else follows from the id
/// with SplitMix64, so the labyrinth is the same in every loop and for everyone.
/// </summary>
public static class MazeGraph
{
    public const ulong Start = 0;
    public const int StartH = 9;

    public static readonly string[] VanillaBodies =
    {
        "DB_HubDimension_Body", "DB_EscapePodDimension_Body", "DB_PioneerDimension_Body", "DB_AnglerNestDimension_Body",
        "DB_ClusterDimension_Body", "DB_SmallNest_Body", "DB_VesselDimension_Body",
    };

    /// <summary>Ordinary room types and their weights (spec 5).</summary>
    private static readonly (RoomType type, int weight)[] Ordinary =
    {
        (RoomType.Dornengang, 22), (RoomType.Dornenwald, 12), (RoomType.Samenkammer, 10), (RoomType.Nebelkammer, 10),
        (RoomType.Frostkammer, 9), (RoomType.Stroemung, 9), (RoomType.Echokammer, 8), (RoomType.Leere, 6),
        (RoomType.Hitzekammer, 6), (RoomType.Wrack, 4), (RoomType.Spiegelkammer, 4),
    };

    /// <summary>How many adult nodes and baby seeds the room type's dimension holds.</summary>
    public static (int nodes, int seeds) Pool(RoomType t) => t switch
    {
        RoomType.Vorhof => (3, 2),
        RoomType.Dornengang => (4, 3),
        RoomType.Dornenwald => (4, 3),
        RoomType.Hitzekammer => (1, 6),
        RoomType.Frostkammer => (3, 2),
        RoomType.Nest => (3, 1),
        RoomType.Samenkammer => (1, 8),
        RoomType.Nebelkammer => (3, 2),
        RoomType.Leere => (1, 0),
        RoomType.Stroemung => (3, 2),
        RoomType.Echokammer => (3, 2),
        RoomType.Wrack => (3, 1),
        RoomType.Spiegelkammer => (4, 0),
        RoomType.Herzpfad => (3, 2),
        RoomType.Herzkammer => (1, 0),
        _ => (1, 0),
    };

    public static ulong Id(RoomType type, int h, int depth, ulong hash) =>
        ((ulong)type & 0xF) | ((ulong)(h & 0xFF) << 4) | ((ulong)Math.Min(depth, 255) << 12) | (hash << 20);

    public static Room Get(ulong id, bool bleeding = false)
    {
        var room = id == Start
            ? new Room { Id = id, Type = RoomType.Vorhof, H = StartH, Depth = 0 }
            : new Room { Id = id, Type = (RoomType)(id & 0xF), H = (int)((id >> 4) & 0xFF), Depth = (int)((id >> 12) & 0xFF) };
        var rng = new Rng(id);
        var (nodes, seeds) = Pool(room.Type);
        var slots = new List<(int slot, bool seed)>();
        for (var i = 0; i < nodes; i++) slots.Add((i, false));
        for (var i = 0; i < seeds; i++) slots.Add((i, true));

        var color = new Dictionary<(int, bool), ExitColor>();
        if (room.Type == RoomType.Herzkammer) color[slots[0]] = ExitColor.Gruen;
        else if (room.Type is not (RoomType.Hitzekammer or RoomType.Spiegelkammer))
        {
            // the special exits, each on its own slot; heat seeds and mirror exits have their own rules below
            var free = new List<(int, bool)>(slots);
            void Pick(ExitColor c)
            {
                if (free.Count == 0) return;
                var k = rng.Below(free.Count);
                color[free[k]] = c;
                free.RemoveAt(k);
            }
            if (room.H >= 1 && room.H <= StartH) Pick(ExitColor.Lila);
            if (room.Type != RoomType.Vorhof && rng.Below(4) == 0) Pick(ExitColor.Gruen);
            if (rng.Below(7) == 0) Pick(ExitColor.Gelb);
            if (room.Type != RoomType.Vorhof && room.Depth >= 2 && rng.Below(5) == 0) Pick(ExitColor.Rot);
        }
        else if (room.Type == RoomType.Hitzekammer && rng.Below(4) == 0) color[(0, false)] = ExitColor.Gruen;

        for (var i = 0; i < slots.Count; i++)
        {
            var (slot, seed) = slots[i];
            var child = Mix(id * 31UL + (ulong)slot + (seed ? 1000UL : 0UL)) >> 20;
            var c = color.TryGetValue((slot, seed), out var cc) ? cc : ExitColor.Normal;
            var crng = new Rng(child);
            var depth = room.Depth + 1;
            Exit exit;
            switch (c)
            {
                case ExitColor.Gruen:
                    exit = new Exit(slot, seed, c, Start);
                    break;
                case ExitColor.Gelb:
                    exit = new Exit(slot, seed, c, Start, (int)(child % (ulong)VanillaBodies.Length));
                    break;
                case ExitColor.Rot:
                    exit = new Exit(slot, seed, c, Id(RoomType.Nest, 6 + crng.Below(7), depth, child));
                    break;
                case ExitColor.Lila:
                    var h = room.H - 1;
                    var type = h == 0 ? RoomType.Herzkammer : h <= 3 && crng.Below(2) == 0 ? RoomType.Herzpfad : OrdinaryType(crng, onHeartPath: true);
                    exit = new Exit(slot, seed, c, Id(type, h, depth, child));
                    break;
                default:
                    if (room.Type == RoomType.Hitzekammer && seed)
                        exit = new Exit(slot, seed, c, Id(RoomType.Hitzekammer, room.H, depth, child));
                    else if (room.Type == RoomType.Spiegelkammer && i < slots.Count - 1)
                        exit = new Exit(slot, seed, c, Id(RoomType.Spiegelkammer, Math.Min(room.H + 1, 12), depth, child));
                    else
                    {
                        var t = OrdinaryType(crng, onHeartPath: false);
                        while (room.Type == RoomType.Hitzekammer && t == RoomType.Hitzekammer) t = OrdinaryType(crng, false);
                        exit = new Exit(slot, seed, c, Id(t, 6 + crng.Below(7), depth, child));
                    }
                    break;
            }
            if (bleeding && exit.Color != ExitColor.Gruen)
                exit = new Exit(slot, seed, ExitColor.Rot, Id(RoomType.Nest, 6 + crng.Below(7), depth, child));
            room.Exits.Add(exit);
        }
        return room;
    }

    /// <summary>A weighted ordinary type; on the heart path no heat or mirror chamber (they have no purple exit).</summary>
    private static RoomType OrdinaryType(Rng rng, bool onHeartPath)
    {
        while (true)
        {
            var roll = rng.Below(100);
            foreach (var (type, weight) in Ordinary)
            {
                if (roll < weight)
                {
                    if (onHeartPath && type is RoomType.Hitzekammer or RoomType.Spiegelkammer) break;
                    return type;
                }
                roll -= weight;
            }
        }
    }

    private static ulong Mix(ulong z)
    {
        z += 0x9E3779B97F4A7C15UL;
        z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9UL;
        z = (z ^ (z >> 27)) * 0x94D049BB133111EBUL;
        return z ^ (z >> 31);
    }

    /// <summary>SplitMix64.</summary>
    private sealed class Rng
    {
        private ulong _state;

        public Rng(ulong seed) => _state = seed;

        public ulong Next() => Mix(_state += 0x9E3779B97F4A7C15UL);

        public int Below(int n) => (int)(Next() % (ulong)n);
    }
}
