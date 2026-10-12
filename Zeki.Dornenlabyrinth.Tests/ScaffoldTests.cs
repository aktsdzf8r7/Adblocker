using Xunit;

namespace ZekiDornenlabyrinth.Tests;

public class ScaffoldTests
{
    [Fact]
    public void LogicCompiles() => Assert.Equal(0UL, MazeGraph.Start);
}
