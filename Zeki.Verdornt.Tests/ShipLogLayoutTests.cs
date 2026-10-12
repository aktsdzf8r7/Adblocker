using System.Collections.Generic;
using Xunit;

namespace ZekiVerdornt.Tests;

public class ShipLogLayoutTests
{
    private static List<(string id, float x, float y)> Cards(params (string, float, float)[] c) => new(c);

    [Fact]
    public void OverlappingCardsMoveBelowTheOthers()
    {
        var cards = Cards(("TH_VILLAGE", 0, 0), ("BH_CITY", 1000, 500), ("ZEKIVD_A", 500, 200), ("ZEKIVD_B", 900, 300));
        var (dx, dy) = ShipLogLayout.MoveBelow(cards, "ZEKIVD_", 400);
        Assert.Equal(-200f, dx, 3);   // centred under the others: 500 - 700
        Assert.Equal(-700f, dy, 3);   // own top (300) ends 400 below the others' bottom (0)
    }

    [Fact]
    public void CardsClearOfTheOthersStay()
    {
        var cards = Cards(("TH_VILLAGE", 0, 0), ("BH_CITY", 1000, 500), ("ZEKIVD_A", 500, -2000));
        Assert.Equal((0f, 0f), ShipLogLayout.MoveBelow(cards, "ZEKIVD_", 400));
    }

    [Fact]
    public void CardsWithinTheMarginCountAsOverlapping()
    {
        var cards = Cards(("TH_VILLAGE", 0, 0), ("ZEKIVD_A", 0, -300));
        Assert.NotEqual((0f, 0f), ShipLogLayout.MoveBelow(cards, "ZEKIVD_", 400));
    }

    [Fact]
    public void NothingToMoveWithoutOwnCards() =>
        Assert.Equal((0f, 0f), ShipLogLayout.MoveBelow(Cards(("TH_VILLAGE", 0, 0)), "ZEKIVD_", 400));

    [Fact]
    public void NothingToMoveWithoutOtherCards() =>
        Assert.Equal((0f, 0f), ShipLogLayout.MoveBelow(Cards(("ZEKIVD_A", 0, 0), ("ZEKIVD_B", 400, 0)), "ZEKIVD_", 400));

    [Fact]
    public void OtherModsCountAsOthers()
    {
        // the cards of another of these mods are not ours: we go below them too
        var cards = Cards(("TH_VILLAGE", 0, 0), ("ZEKISAE_X", 0, -900), ("ZEKIVD_A", 0, -900));
        var (_, dy) = ShipLogLayout.MoveBelow(cards, "ZEKIVD_", 400);
        Assert.Equal(-400f, dy, 3);   // own top -900 -> -1300: 400 below the lowest other card (-900)
    }
}
