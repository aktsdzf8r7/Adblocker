using System.Numerics;
using Xunit;

namespace ZekiVerdornt.Tests;

public class PlatformCarryTests
{
    [Fact]
    public void StandingOnTheDeckIsCarried() => Assert.True(PlatformCarry.IsOn(new Vector3(1.2f, 1.0f, -0.8f), 2.4f));

    [Fact]
    public void BesideTheDeckIsNotCarried() => Assert.False(PlatformCarry.IsOn(new Vector3(3.5f, 1.0f, 0f), 2.4f));

    [Fact]
    public void FarAboveTheDeckIsNotCarried() => Assert.False(PlatformCarry.IsOn(new Vector3(0f, 6f, 0f), 2.4f));

    [Fact]
    public void BelowTheDeckIsNotCarried() => Assert.False(PlatformCarry.IsOn(new Vector3(0f, -1.5f, 0f), 2.4f));
}
