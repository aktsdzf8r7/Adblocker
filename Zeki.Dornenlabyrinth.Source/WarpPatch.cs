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
