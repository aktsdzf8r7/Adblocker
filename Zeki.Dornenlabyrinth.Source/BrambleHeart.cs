using HarmonyLib;
using System;
using UnityEngine;

namespace ZekiDornenlabyrinth;

/// <summary>
/// The Bramble Heart (spec 6). Taking it makes the labyrinth bleed: every exit but the green ones turns red. Once the
/// player is out of the labyrinth with it, the heart sings and no anglerfish of the system hunts anyone until the
/// loop ends. In the next loop the heart is back in its chamber.
/// </summary>
public static class BrambleHeart
{
    public const string HeartName = "ZEKIDL_Herz";
    public const string BleedFact = "ZEKIDL_HERZ_BLUTET";
    public const string SingFact = "ZEKIDL_HERZ_SINGT";

    /// <summary>Taken in this loop.</summary>
    public static bool Taken { get; private set; }

    /// <summary>The heart sings: anglerfish do not investigate or chase.</summary>
    public static bool Calm { get; private set; }

    private static ZekiDornenlabyrinth _mod;
    private static Transform _heart;
    private static float _outsideSince = -1f;

    public static void Reset()
    {
        Taken = Calm = false;
        _heart = null;
        _outsideSince = -1f;
    }

    public static void Setup(ZekiDornenlabyrinth mod)
    {
        _mod = mod;
        Reset();
        var chamber = mod.NewHorizons.GetPlanet("Labyrinth_Herzkammer");
        _heart = chamber == null ? null : Rooms.FindDeep(chamber.transform, HeartName);
        var model = chamber == null ? null : Rooms.FindDeep(chamber.transform, "ZEKIDL_Herz_Modell");
        if (model != null) model.gameObject.AddComponent<Pulser>();
        mod.Log(_heart == null ? "Das Bramble-Herz fehlt in der Herzkammer." : "Das Bramble-Herz schlägt.", _heart == null);
        new GameObject("ZEKIDL_Herzwaechter").AddComponent<HeartWatcher>();
    }

    private static bool Holding()
    {
        var item = Locator.GetToolModeSwapper()?.GetItemCarryTool()?.GetHeldItem();
        return item != null && item.name == HeartName;
    }

    /// <summary>Whether the heart (held, or dropped somewhere) is outside every labyrinth dimension.</summary>
    private static bool HeartOutside()
    {
        if (_heart == null) return Holding();
        for (var t = _heart; t != null; t = t.parent)
            if (t.name.StartsWith("Labyrinth_")) return false;
        return true;
    }

    internal static void Check()
    {
        if (!Taken && Holding())
        {
            Taken = true;
            Labyrinth.Bleeding = true;
            Labyrinth.Refresh();
            ZekiDornenlabyrinth.Notify("DAS LABYRINTH BLUTET", 6f);
            Reveal(BleedFact);
            Sound();
            _mod.Log("Das Herz ist genommen: Das Labyrinth blutet.");
        }
        if (!Taken || Calm) return;
        // out of the labyrinth with the heart for a moment (not just the frame of a warp)
        if (Labyrinth.PlayerInside() || !HeartOutside())
        {
            _outsideSince = -1f;
            return;
        }
        if (_outsideSince < 0f) _outsideSince = Time.time;
        if (Time.time - _outsideSince < 1f) return;
        Calm = true;
        foreach (var angler in UnityEngine.Object.FindObjectsOfType<AnglerfishController>())
            if (angler.GetAnglerState() is AnglerfishController.AnglerState.Investigating or AnglerfishController.AnglerState.Chasing)
                angler.ChangeState(AnglerfishController.AnglerState.Lurking);
        ZekiDornenlabyrinth.Notify("DAS HERZ SINGT. DIE ANGLERFISCHE SCHLAFEN.", 8f);
        Reveal(SingFact);
        Sound();
        _mod.Log("Das Herz singt: Die Anglerfische jagen nicht mehr.");
    }

    private static void Reveal(string fact) => Locator.GetShipLogManager()?.RevealFact(fact, true, true);

    private static void Sound() => Locator.GetPlayerAudioController()?._oneShotSource?.PlayOneShot(AudioType.DB_VesselDiscovery, 1f);
}

public class HeartWatcher : MonoBehaviour
{
    private bool _failed;

    public void Update()
    {
        if (_failed) return;
        try
        {
            BrambleHeart.Check();
        }
        catch (Exception e)
        {
            _failed = true;
            ZekiDornenlabyrinth.Instance?.Log("Bramble-Herz: " + e, true);
        }
    }
}

/// <summary>While the heart sings, anglerfish neither investigate nor chase.</summary>
[HarmonyPatch(typeof(AnglerfishController), nameof(AnglerfishController.ChangeState))]
public static class AnglerCalmPatch
{
    [HarmonyPrefix]
    public static bool Prefix(AnglerfishController.AnglerState newState) =>
        !(BrambleHeart.Calm && newState is AnglerfishController.AnglerState.Investigating or AnglerfishController.AnglerState.Chasing);
}
