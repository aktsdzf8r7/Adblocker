using Xunit;

namespace ZekiVerdornt.Tests;

public class CrossingStateTests
{
    [Fact]
    public void SecondBeginWhileBusyIsRejected()
    {
        var state = new CrossingState();
        Assert.True(state.TryBegin());
        Assert.True(state.Busy);
        Assert.False(state.TryBegin());
        state.Reset();
        Assert.False(state.Busy);
        Assert.True(state.TryBegin());
    }
}
