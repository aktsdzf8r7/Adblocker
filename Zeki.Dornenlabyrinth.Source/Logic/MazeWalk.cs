using System.Collections.Generic;

namespace ZekiDornenlabyrinth;

/// <summary>
/// The player's way through the labyrinth: the current instance, the way back (which node of which instance each
/// room was entered by, at most 64, the oldest is forgotten) and the heat level of the heat chamber.
/// </summary>
public sealed class MazeWalk
{
    public const int MaxDepth = 64;

    private readonly List<(ulong room, int slot, bool seed)> _back = new();

    public ulong Current { get; private set; } = MazeGraph.Start;

    /// <summary>How often in a row the player has flown into a heat chamber; 0 outside of one.</summary>
    public int Heat { get; private set; }

    public int Count => _back.Count;

    public void Enter(ulong from, int slot, bool seed, ulong to)
    {
        _back.Add((from, slot, seed));
        if (_back.Count > MaxDepth) _back.RemoveAt(0);
        Heat = HeatAfter(TypeOf(from), TypeOf(to), Heat);
        Current = to;
    }

    /// <summary>Out through the wall: the instance and node the current room was entered by, or null at the end.</summary>
    public (ulong room, int slot, bool seed)? Back()
    {
        Heat = 0;
        if (_back.Count == 0)
        {
            Current = MazeGraph.Start;
            return null;
        }
        var last = _back[_back.Count - 1];
        _back.RemoveAt(_back.Count - 1);
        Current = last.room;
        return last;
    }

    /// <summary>The way back from the current room, without taking it; null at the end.</summary>
    public (ulong room, int slot, bool seed)? Peek() => _back.Count == 0 ? null : _back[_back.Count - 1];

    public void Reset() => Restart(MazeGraph.Start);

    /// <summary>Stand in the given instance with no way back (when the walk lost track of the player).</summary>
    public void Restart(ulong at)
    {
        _back.Clear();
        Heat = 0;
        Current = at;
    }

    public static int HeatAfter(RoomType from, RoomType to, int heat) =>
        to != RoomType.Hitzekammer ? 0 : from == RoomType.Hitzekammer ? heat + 1 : 1;

    private static RoomType TypeOf(ulong id) => MazeGraph.Get(id).Type;
}
