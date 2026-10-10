using System.Collections.Generic;
using Xunit;

namespace ZekiVerdornt.Tests;

public class GroundFitTests
{
    [Fact]
    public void MedianOfOddCount() => Assert.Equal(3f, GroundFit.Median(new List<float> { 9, 1, 3 }));

    [Fact]
    public void MedianOfEvenCountIsMean() => Assert.Equal(2.5f, GroundFit.Median(new List<float> { 4, 1, 2, 3 }));

    [Fact]
    public void FlattestCandidateWins()
    {
        var candidates = new List<IList<float?>>
        {
            new List<float?> { 0, 8, -3, 2 },
            new List<float?> { 1, 1.5f, 0.5f, 1 },
            new List<float?> { 4, 0, 2, 9 },
        };
        Assert.Equal(1, GroundFit.PickFlattest(candidates, 3));
    }

    [Fact]
    public void CandidatesWithTooFewHitsAreSkipped()
    {
        var candidates = new List<IList<float?>>
        {
            new List<float?> { 1, null, null, 1 },
            new List<float?> { 0, 6, 2, 3 },
        };
        Assert.Equal(1, GroundFit.PickFlattest(candidates, 3));
    }

    [Fact]
    public void NoCandidateWithoutGround() =>
        Assert.Equal(-1, GroundFit.PickFlattest(new List<IList<float?>> { new List<float?> { null, null } }, 1));

    [Fact]
    public void GridReproducesASlope()
    {
        var grid = new HeightGrid(10f, 4);
        for (var i = 0; i < grid.Count; i++)
        {
            var (x, z) = grid.Point(i);
            grid.Set(i, 0.5f * x - 0.25f * z + 2f);
        }
        Assert.Equal(0.5f * 3.3f - 0.25f * -7.1f + 2f, grid.At(3.3f, -7.1f), 3);
    }

    [Fact]
    public void GridClampsOutside()
    {
        var grid = new HeightGrid(10f, 2);
        for (var i = 0; i < grid.Count; i++) grid.Set(i, grid.Point(i).x);
        Assert.Equal(10f, grid.At(50f, 0f), 3);
    }

    [Fact]
    public void MissingSamplesTakeTheMedian()
    {
        var grid = new HeightGrid(1f, 1);
        grid.Set(0, 1f);
        grid.Set(1, 3f);
        grid.Set(2, null);
        grid.Set(3, 2f);
        Assert.Equal(3, grid.FillMissing());
        Assert.Equal(2f, grid.At(-1f, 1f), 3);
    }

    [Fact]
    public void EmptyGridIsFlat()
    {
        var grid = new HeightGrid(5f, 2);
        Assert.Equal(0, grid.FillMissing());
        Assert.Equal(0f, grid.At(1f, 1f));
    }
}
