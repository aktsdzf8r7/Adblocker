using HarmonyLib;
using System;

namespace ZekiDornenlabyrinth;

/// <summary>Before a fog warp volume warps the player, the labyrinth sets up where it leads (Labyrinth.OnWarp).</summary>
[HarmonyPatch(typeof(FogWarpVolume), nameof(FogWarpVolume.WarpDetector))]
public static class WarpPatch
{
    [HarmonyPrefix]
    public static void Prefix(FogWarpVolume __instance, FogWarpDetector detector, ref FogWarpVolume linkedWarpVolume)
    {
        try
        {
            Labyrinth.OnWarp(__instance, detector, ref linkedWarpVolume);
        }
        catch (Exception e)
        {
            ZekiDornenlabyrinth.Instance?.Log("Labyrinth (Durchflug): " + e, true);
        }
    }
}

/// <summary>
/// New Horizons makes every seed scout-only (SphericalFogWarpVolume.IsProbeOnly). The baby seeds of the labyrinth are
/// real exits, so the player may fly through them too.
/// </summary>
[HarmonyPatch(typeof(SphericalFogWarpVolume), nameof(SphericalFogWarpVolume.IsProbeOnly))]
public static class SeedPatch
{
    [HarmonyPostfix]
    [HarmonyPriority(Priority.Last)]
    public static void Postfix(SphericalFogWarpVolume __instance, ref bool __result)
    {
        if (__result && Labyrinth.IsPlayerSeed(__instance)) __result = false;
    }
}
