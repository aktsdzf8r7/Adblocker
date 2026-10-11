using Xunit;

namespace ZekiDornenlabyrinth.Tests;

public class MazeWalkTests
{
    private static readonly ulong A = MazeGraph.Id(RoomType.Dornengang, 8, 1, 11);
    private static readonly ulong B = MazeGraph.Id(RoomType.Frostkammer, 7, 2, 12);
    private static readonly ulong Heat1 = MazeGraph.Id(RoomType.Hitzekammer, 7, 2, 13);
    private static readonly ulong Heat2 = MazeGraph.Id(RoomType.Hitzekammer, 7, 3, 14);
    private static readonly ulong Heat3 = MazeGraph.Id(RoomType.Hitzekammer, 7, 4, 15);

    [Fact]
    public void BackReturnsWhereYouCameFrom()
    {
        var walk = new MazeWalk();
        walk.Enter(MazeGraph.Start, 1, false, A);
        walk.Enter(A, 2, true, B);
        Assert.Equal(B, walk.Current);
        Assert.Equal(2, walk.Count);

        var back = walk.Back();
        Assert.Equal((A, 2, true), back);
        Assert.Equal(A, walk.Current);
        Assert.Equal((MazeGraph.Start, 1, false), walk.Back());
        Assert.Equal(MazeGraph.Start, walk.Current);
        Assert.Equal(0, walk.Count);
    }

    [Fact]
    public void BackOnEmptyIsNull()
    {
        var walk = new MazeWalk();
        Assert.Null(walk.Back());
        Assert.Equal(MazeGraph.Start, walk.Current);
    }

    [Fact]
    public void StackIsCappedAt64()
    {
        var walk = new MazeWalk();
        var from = MazeGraph.Start;
        for (var i = 0; i < 70; i++)
        {
            var to = MazeGraph.Id(RoomType.Dornengang, 8, i + 1, (ulong)i + 100);
            walk.Enter(from, 0, false, to);
            from = to;
        }
        Assert.Equal(64, walk.Count);
        for (var i = 0; i < 64; i++) Assert.NotNull(walk.Back());
        Assert.Null(walk.Back());
    }

    [Fact]
    public void HeatGrowsInsideTheHeatChamber()
    {
        var walk = new MazeWalk();
        walk.Enter(MazeGraph.Start, 0, false, Heat1);
        Assert.Equal(1, walk.Heat);
        walk.Enter(Heat1, 0, true, Heat2);
        Assert.Equal(2, walk.Heat);
        walk.Enter(Heat2, 3, true, Heat3);
        Assert.Equal(3, walk.Heat);
    }

    [Fact]
    public void HeatResetsOnLeaving()
    {
        var walk = new MazeWalk();
        walk.Enter(MazeGraph.Start, 0, false, Heat1);
        walk.Enter(Heat1, 0, true, Heat2);
        walk.Enter(Heat2, 0, false, A);
        Assert.Equal(0, walk.Heat);
        Assert.Equal(0, MazeWalk.HeatAfter(RoomType.Hitzekammer, RoomType.Dornengang, 5));
        Assert.Equal(1, MazeWalk.HeatAfter(RoomType.Dornengang, RoomType.Hitzekammer, 5));
    }

    [Fact]
    public void BackResetsHeat()
    {
        var walk = new MazeWalk();
        walk.Enter(MazeGraph.Start, 0, false, Heat1);
        walk.Enter(Heat1, 0, true, Heat2);
        walk.Back();
        Assert.Equal(0, walk.Heat);
    }

    [Fact]
    public void ResetGoesBackToTheStart()
    {
        var walk = new MazeWalk();
        walk.Enter(MazeGraph.Start, 0, false, Heat1);
        walk.Reset();
        Assert.Equal(MazeGraph.Start, walk.Current);
        Assert.Equal(0, walk.Heat);
        Assert.Equal(0, walk.Count);
    }

    [Fact]
    public void PeekShowsTheNextWayBackWithoutTakingIt()
    {
        var walk = new MazeWalk();
        Assert.Null(walk.Peek());
        walk.Enter(MazeGraph.Start, 1, false, A);
        walk.Enter(A, 2, true, B);
        Assert.Equal((A, 2, true), walk.Peek());
        Assert.Equal(2, walk.Count);
        walk.Back();
        Assert.Equal((MazeGraph.Start, 1, false), walk.Peek());
    }

    [Fact]
    public void RestartForgetsTheWayAndStandsSomewhereElse()
    {
        var walk = new MazeWalk();
        walk.Enter(MazeGraph.Start, 0, false, Heat1);
        walk.Restart(B);
        Assert.Equal(B, walk.Current);
        Assert.Equal(0, walk.Count);
        Assert.Equal(0, walk.Heat);
    }
}
