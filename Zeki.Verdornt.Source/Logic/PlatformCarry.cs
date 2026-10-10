using System.Numerics;

namespace ZekiVerdornt;

/// <summary>Is someone standing on a moving platform? (Position in the platform's frame, deck at y = 0.)</summary>
public static class PlatformCarry
{
    public static bool IsOn(Vector3 local, float deckRadius, float maxHeight = 3f) =>
        local.Y > -0.5f && local.Y < maxHeight && local.X * local.X + local.Z * local.Z < (deckRadius + 0.2f) * (deckRadius + 0.2f);
}
