using System;

namespace ZekiDornenlabyrinth;

public enum WarpKind
{
    /// <summary>Not ours to decide: the node keeps the target New Horizons gave it (the Vorhof).</summary>
    None,
    /// <summary>Into another room instance; the way back is remembered.</summary>
    Room,
    /// <summary>A green exit: back to the Vorhof, the way back is forgotten.</summary>
    Home,
    /// <summary>A yellow exit: out of the labyrinth into a dimension of Dark Bramble.</summary>
    Vanilla,
}

public readonly struct WarpDecision
{
    public readonly WarpKind Kind;
    /// <summary>The room to set up and fly into (Room and Home).</summary>
    public readonly Room Target;
    /// <summary>Index into MazeGraph.VanillaBodies (Vanilla).</summary>
    public readonly int Vanilla;
    /// <summary>The walk had lost track of the player and starts again at the room the dimension shows.</summary>
    public readonly bool Restarted;

    public WarpDecision(WarpKind kind, Room target = null, int vanilla = -1, bool restarted = false)
    {
        Kind = kind;
        Target = target;
        Vanilla = vanilla;
        Restarted = restarted;
    }
}

/// <summary>
/// What happens when the player flies through a node or out through the wall of a room (spec 3 and 4). Pure: the
/// runtime (Labyrinth.cs) only carries the decisions out.
/// </summary>
public static class Router
{
    /// <summary>
    /// The player flies through node (slot, seed) of the dimension of the given room type, which currently shows the
    /// instance shown (null if the DLL never set it up).
    /// </summary>
    public static WarpDecision ThroughNode(MazeWalk walk, RoomType type, int slot, bool seed, ulong? shown, bool bleeding, Func<int, bool> vanillaExists)
    {
        var from = shown ?? (type == RoomType.Vorhof ? MazeGraph.Start : (ulong?)null);
        if (from == null) return new WarpDecision(WarpKind.None);
        var room = MazeGraph.Get(from.Value, bleeding);
        var index = room.Exits.FindIndex(e => e.Slot == slot && e.Seed == seed);
        if (index < 0) return new WarpDecision(WarpKind.None);
        var restarted = walk.Current != from.Value;
        if (restarted) walk.Restart(from.Value);
        var exit = Effective(room, room.Exits[index], vanillaExists);
        switch (exit.Color)
        {
            case ExitColor.Gelb:
                walk.Reset();
                return new WarpDecision(WarpKind.Vanilla, vanilla: exit.Vanilla, restarted: restarted);
            case ExitColor.Gruen:
                walk.Reset();
                return new WarpDecision(WarpKind.Home, MazeGraph.Get(MazeGraph.Start, bleeding), restarted: restarted);
            default:
                walk.Enter(from.Value, slot, seed, exit.Target);
                return new WarpDecision(WarpKind.Room, MazeGraph.Get(exit.Target, bleeding), restarted: restarted);
        }
    }

    /// <summary>The exit as it works in this game: a yellow exit whose Dark Bramble dimension is missing is a normal one.</summary>
    public static Exit Effective(Room room, Exit exit, Func<int, bool> vanillaExists)
    {
        if (exit.Color != ExitColor.Gelb || vanillaExists(exit.Vanilla)) return exit;
        var hash = (room.Id >> 20) ^ (ulong)(exit.Slot * 7 + (exit.Seed ? 1000 : 1));
        return new Exit(exit.Slot, exit.Seed, ExitColor.Normal, MazeGraph.Id(RoomType.Dornengang, 9, room.Depth + 1, hash));
    }

    /// <summary>
    /// The player flies out through the wall: the room to go back into and the node to come out of, or null when the
    /// way back ends (at the Vorhof that is the way outside).
    /// </summary>
    public static (Room room, int slot, bool seed)? Back(MazeWalk walk, bool bleeding)
    {
        var back = walk.Back();
        if (back == null) return null;
        return (MazeGraph.Get(back.Value.room, bleeding), back.Value.slot, back.Value.seed);
    }
}
