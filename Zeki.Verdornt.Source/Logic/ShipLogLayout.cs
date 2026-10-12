using System.Collections.Generic;
using System.Linq;

namespace ZekiVerdornt;

/// <summary>
/// Keeps a mod's ship log cards off everyone else's in rumor mode: if the mod's cards (id prefix) come within margin of
/// the other cards, the whole group moves below them, centred, keeping its own layout. Run by every mod that uses it,
/// in any order, the groups stack below each other.
/// </summary>
public static class ShipLogLayout
{
    /// <summary>The offset for every card whose id starts with prefix; (0, 0) when they do not overlap the others.</summary>
    public static (float dx, float dy) MoveBelow(IList<(string id, float x, float y)> cards, string prefix, float margin)
    {
        var own = cards.Where(c => c.id.StartsWith(prefix)).ToList();
        var others = cards.Where(c => !c.id.StartsWith(prefix)).ToList();
        if (own.Count == 0 || others.Count == 0) return (0f, 0f);
        float oMinX = others.Min(c => c.x), oMaxX = others.Max(c => c.x), oMinY = others.Min(c => c.y), oMaxY = others.Max(c => c.y);
        float mMinX = own.Min(c => c.x), mMaxX = own.Max(c => c.x), mMinY = own.Min(c => c.y), mMaxY = own.Max(c => c.y);
        var overlaps = mMinX - margin <= oMaxX && mMaxX + margin >= oMinX && mMinY - margin <= oMaxY && mMaxY + margin >= oMinY;
        if (!overlaps) return (0f, 0f);
        return ((oMinX + oMaxX) / 2f - (mMinX + mMaxX) / 2f, oMinY - margin - mMaxY);
    }
}
