using System.Collections.Generic;
using Xunit;

namespace ZekiVerdornt.Tests;

public class ReactiveChoiceTests
{
    [Fact]
    public void PicksHighestActive() =>
        Assert.Equal("b", ReactiveChoice.Pick(new List<(string, int, bool)> { ("a", 0, true), ("b", 2, true), ("c", 1, true) }));

    [Fact]
    public void FallsBackToFirst() =>
        Assert.Equal("a", ReactiveChoice.Pick(new List<(string, int, bool)> { ("a", 0, false), ("b", 2, false) }));

    [Fact]
    public void IgnoresInactiveHigher() =>
        Assert.Equal("a", ReactiveChoice.Pick(new List<(string, int, bool)> { ("a", 0, true), ("b", 5, false) }));
}
