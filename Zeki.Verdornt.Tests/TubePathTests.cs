using System.Collections.Generic;
using System.Numerics;
using Xunit;

namespace ZekiVerdornt.Tests;

public class TubePathTests
{
    private static TubePath Straight() => new(new List<Vector3> { new(0, 0, 0), new(10, 0, 0) });

    [Fact]
    public void ProjectOntoStraightPath() => Assert.Equal(4f, Straight().Project(new Vector3(4, 3, 0)), 3);

    [Fact]
    public void ProjectClampsBeyondEnd() => Assert.Equal(10f, Straight().Project(new Vector3(15, 0, 0)), 3);

    [Fact]
    public void NearestSlotRoundsToClosest() => Assert.Equal(1, TubePath.NearestSlot(7.5f, new List<float> { 0, 6, 10 }));

    [Fact]
    public void NearestSlotBetweenTiesPrefersLower() => Assert.Equal(0, TubePath.NearestSlot(3f, new List<float> { 0, 6 }));

    [Fact]
    public void AtWalksAlongBends()
    {
        var path = new TubePath(new List<Vector3> { new(0, 0, 0), new(4, 0, 0), new(4, 3, 0) });
        Assert.Equal(7f, path.Length, 3);
        Assert.Equal(new Vector3(4, 1, 0), path.At(5f));
    }
}
