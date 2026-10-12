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

public class CrossingAbortTests
{
    [Fact]
    public void DyingDuringTheVeilCancelsTheChange()
    {
        var state = new CrossingState();
        Assert.True(state.TryBegin());
        Assert.False(state.MayChangeSystem(playerDying: true));
        Assert.False(state.TryBegin()); // stays busy: the death reloads the scene anyway
    }

    [Fact]
    public void AliveAfterTheVeilChanges()
    {
        var state = new CrossingState();
        state.TryBegin();
        Assert.True(state.MayChangeSystem(playerDying: false));
    }

    [Fact]
    public void NoChangeWithoutABegin() => Assert.False(new CrossingState().MayChangeSystem(playerDying: false));
}
