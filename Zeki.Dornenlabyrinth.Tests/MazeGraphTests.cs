using System;
using System.Linq;
using Xunit;

namespace ZekiDornenlabyrinth.Tests;

public class MazeGraphTests
{
    /// <summary>Rooms from walking the maze at random (seeded), so every test sees real instances.</summary>
    private static Room[] Sample(int count, int seed = 7)
    {
        var rnd = new Random(seed);
        var rooms = new Room[count];
        var id = MazeGraph.Start;
        for (var i = 0; i < count; i++)
        {
            var room = MazeGraph.Get(id);
            rooms[i] = room;
            var walkable = room.Exits.Where(e => e.Color != ExitColor.Gelb).ToList();
            id = walkable.Count == 0 || rnd.Next(12) == 0 ? MazeGraph.Start : walkable[rnd.Next(walkable.Count)].Target;
        }
        return rooms;
    }

    [Fact]
    public void SameIdSameRoom()
    {
        foreach (var r in Sample(50))
        {
            var again = MazeGraph.Get(r.Id);
            Assert.Equal(r.Type, again.Type);
            Assert.Equal(r.H, again.H);
            Assert.Equal(r.Exits.Select(e => (e.Slot, e.Seed, e.Color, e.Target)), again.Exits.Select(e => (e.Slot, e.Seed, e.Color, e.Target)));
        }
    }

    [Fact]
    public void StartIsVorhofWithLila()
    {
        var start = MazeGraph.Get(MazeGraph.Start);
        Assert.Equal(RoomType.Vorhof, start.Type);
        Assert.Equal(9, start.H);
        Assert.Single(start.Exits, e => e.Color == ExitColor.Lila);
        Assert.DoesNotContain(start.Exits, e => e.Color == ExitColor.Rot);
    }

    [Fact]
    public void LilaCountsDownToTheHeart()
    {
        var room = MazeGraph.Get(MazeGraph.Start);
        for (var i = 0; i < 9; i++)
            room = MazeGraph.Get(room.Exits.Single(e => e.Color == ExitColor.Lila).Target);
        Assert.Equal(RoomType.Herzkammer, room.Type);
    }

    [Fact]
    public void RotLeadsToANest()
    {
        foreach (var r in Sample(2000))
            foreach (var e in r.Exits.Where(e => e.Color == ExitColor.Rot))
            {
                Assert.True(r.Depth >= 2);
                Assert.Equal(RoomType.Nest, MazeGraph.Get(e.Target).Type);
            }
    }

    [Fact]
    public void GruenLeadsHome()
    {
        foreach (var r in Sample(2000))
            foreach (var e in r.Exits.Where(e => e.Color == ExitColor.Gruen))
                Assert.Equal(MazeGraph.Start, e.Target);
    }

    [Fact]
    public void GelbHasAVanillaIndex()
    {
        foreach (var r in Sample(2000))
            foreach (var e in r.Exits)
                if (e.Color == ExitColor.Gelb) Assert.InRange(e.Vanilla, 0, MazeGraph.VanillaBodies.Length - 1);
                else Assert.Equal(-1, e.Vanilla);
    }

    [Fact]
    public void HeatSeedsLoopIntoHeat()
    {
        var heat = Sample(4000).Where(r => r.Type == RoomType.Hitzekammer).ToList();
        Assert.NotEmpty(heat);
        foreach (var r in heat)
            foreach (var e in r.Exits)
                if (e.Seed) Assert.Equal(RoomType.Hitzekammer, MazeGraph.Get(e.Target).Type);
                else Assert.NotEqual(RoomType.Hitzekammer, MazeGraph.Get(e.Target).Type);
    }

    [Fact]
    public void PoolSizesMatchExits()
    {
        foreach (var r in Sample(2000))
        {
            var (nodes, seeds) = MazeGraph.Pool(r.Type);
            foreach (var e in r.Exits) Assert.InRange(e.Slot, 0, (e.Seed ? seeds : nodes) - 1);
        }
    }

    [Fact]
    public void HerzkammerOnlyGreen()
    {
        var heart = MazeGraph.Get(MazeGraph.Id(RoomType.Herzkammer, 0, 10, 12345));
        Assert.Single(heart.Exits);
        Assert.Equal(ExitColor.Gruen, heart.Exits[0].Color);
    }

    [Fact]
    public void BleedingKeepsGreenTurnsRestRed()
    {
        foreach (var r in Sample(500))
        {
            var bleeding = MazeGraph.Get(r.Id, true);
            Assert.DoesNotContain(bleeding.Exits, e => e.Color is ExitColor.Normal or ExitColor.Gelb or ExitColor.Lila);
            Assert.Equal(r.Exits.Where(e => e.Color == ExitColor.Gruen).Select(e => e.Slot),
                         bleeding.Exits.Where(e => e.Color == ExitColor.Gruen).Select(e => e.Slot));
            foreach (var e in bleeding.Exits.Where(e => e.Color == ExitColor.Rot))
                Assert.Equal(RoomType.Nest, MazeGraph.Get(e.Target).Type);
        }
    }
}
