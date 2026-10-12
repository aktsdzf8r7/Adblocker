using System;
using System.Linq;
using Xunit;

namespace ZekiDornenlabyrinth.Tests;

public class RouterTests
{
    private static readonly Func<int, bool> AllVanilla = _ => true;
    private static readonly Func<int, bool> NoVanilla = _ => false;

    /// <summary>The first room (walking the lila way from the Vorhof, then anything) that has an exit of the colour.</summary>
    private static (Room room, Exit exit) Find(ExitColor color, int maxDepth = 400)
    {
        var rnd = new Random(3);
        var id = MazeGraph.Start;
        for (var i = 0; i < maxDepth; i++)
        {
            var room = MazeGraph.Get(id);
            var hit = room.Exits.Where(e => e.Color == color).ToList();
            if (hit.Count > 0 && room.Type != RoomType.Herzkammer) return (room, hit[0]);
            var next = room.Exits.Where(e => e.Color != ExitColor.Gelb && e.Target != MazeGraph.Start).ToList();
            id = next.Count == 0 ? MazeGraph.Start : next[rnd.Next(next.Count)].Target;
        }
        throw new Exception("no exit of colour " + color);
    }

    [Fact]
    public void ThroughANodeEntersTheTargetAndRemembersTheWay()
    {
        var walk = new MazeWalk();
        var lila = MazeGraph.Get(MazeGraph.Start).Exits.Single(e => e.Color == ExitColor.Lila);
        var d = Router.ThroughNode(walk, RoomType.Vorhof, lila.Slot, lila.Seed, MazeGraph.Start, false, AllVanilla);
        Assert.Equal(WarpKind.Room, d.Kind);
        Assert.Equal(lila.Target, d.Target.Id);
        Assert.Equal(MazeGraph.StartH - 1, d.Target.H);
        Assert.Equal(lila.Target, walk.Current);
        Assert.Equal(1, walk.Count);
    }

    [Fact]
    public void GreenGoesHomeAndForgetsTheWay()
    {
        var (room, green) = Find(ExitColor.Gruen);
        var walk = new MazeWalk();
        walk.Enter(MazeGraph.Start, 0, false, room.Id);
        var d = Router.ThroughNode(walk, room.Type, green.Slot, green.Seed, room.Id, false, AllVanilla);
        Assert.Equal(WarpKind.Home, d.Kind);
        Assert.Equal(RoomType.Vorhof, d.Target.Type);
        Assert.Equal(MazeGraph.Start, walk.Current);
        Assert.Equal(0, walk.Count);
    }

    [Fact]
    public void YellowLeavesTheMaze()
    {
        var (room, yellow) = Find(ExitColor.Gelb);
        var walk = new MazeWalk();
        walk.Restart(room.Id);
        var d = Router.ThroughNode(walk, room.Type, yellow.Slot, yellow.Seed, room.Id, false, AllVanilla);
        Assert.Equal(WarpKind.Vanilla, d.Kind);
        Assert.InRange(d.Vanilla, 0, MazeGraph.VanillaBodies.Length - 1);
        Assert.Equal(MazeGraph.Start, walk.Current);
    }

    [Fact]
    public void YellowWithoutItsDimensionBecomesNormal()
    {
        var (room, yellow) = Find(ExitColor.Gelb);
        Assert.Equal(ExitColor.Normal, Router.Effective(room, yellow, NoVanilla).Color);
        var walk = new MazeWalk();
        walk.Restart(room.Id);
        var d = Router.ThroughNode(walk, room.Type, yellow.Slot, yellow.Seed, room.Id, false, NoVanilla);
        Assert.Equal(WarpKind.Room, d.Kind);
        Assert.Equal(1, walk.Count);
    }

    [Fact]
    public void ADimensionShowingAnotherInstanceRestartsTheWalk()
    {
        // a room deeper inside, while the walk still stands at the Vorhof
        var room = MazeGraph.Get(MazeGraph.Get(MazeGraph.Start).Exits.Single(e => e.Color == ExitColor.Lila).Target);
        var exit = room.Exits.First(e => e.Color == ExitColor.Normal);
        var walk = new MazeWalk();
        var d = Router.ThroughNode(walk, room.Type, exit.Slot, exit.Seed, room.Id, false, AllVanilla);
        Assert.True(d.Restarted);
        Assert.Equal(WarpKind.Room, d.Kind);
        Assert.Equal(1, walk.Count);
        Assert.Equal((room.Id, exit.Slot, exit.Seed), walk.Peek());
    }

    [Fact]
    public void ANeverShownRoomIsLeftToNewHorizons()
    {
        var walk = new MazeWalk();
        var d = Router.ThroughNode(walk, RoomType.Dornengang, 0, false, null, false, AllVanilla);
        Assert.Equal(WarpKind.None, d.Kind);
        Assert.Equal(MazeGraph.Start, walk.Current);
        Assert.Equal(0, walk.Count);
    }

    [Fact]
    public void AHiddenNodeIsLeftToNewHorizons()
    {
        var walk = new MazeWalk();
        var d = Router.ThroughNode(walk, RoomType.Vorhof, 99, false, MazeGraph.Start, false, AllVanilla);
        Assert.Equal(WarpKind.None, d.Kind);
        Assert.Equal(0, walk.Count);
    }

    [Fact]
    public void BleedingLeadsIntoNestsExceptGreen()
    {
        var walk = new MazeWalk();
        var start = MazeGraph.Get(MazeGraph.Start, true);
        foreach (var e in start.Exits)
        {
            walk.Reset();
            var d = Router.ThroughNode(walk, RoomType.Vorhof, e.Slot, e.Seed, MazeGraph.Start, true, AllVanilla);
            Assert.Equal(RoomType.Nest, d.Target.Type);
        }
    }

    [Fact]
    public void BackGoesToTheNodeYouCameThrough()
    {
        var walk = new MazeWalk();
        var lila = MazeGraph.Get(MazeGraph.Start).Exits.Single(e => e.Color == ExitColor.Lila);
        var into = Router.ThroughNode(walk, RoomType.Vorhof, lila.Slot, lila.Seed, MazeGraph.Start, false, AllVanilla).Target;
        var next = into.Exits.First(e => e.Color == ExitColor.Normal);
        Router.ThroughNode(walk, into.Type, next.Slot, next.Seed, into.Id, false, AllVanilla);

        var back = Router.Back(walk, false);
        Assert.NotNull(back);
        Assert.Equal(into.Id, back.Value.room.Id);
        Assert.Equal(next.Slot, back.Value.slot);
        Assert.Equal(next.Seed, back.Value.seed);
        Assert.Equal(into.Id, walk.Current);

        var home = Router.Back(walk, false);
        Assert.Equal(RoomType.Vorhof, home.Value.room.Type);
        Assert.Equal(lila.Slot, home.Value.slot);
    }

    [Fact]
    public void BackFromTheVorhofLeadsOutside()
    {
        var walk = new MazeWalk();
        Assert.Null(Router.Back(walk, false));
        Assert.Equal(MazeGraph.Start, walk.Current);
    }
}
