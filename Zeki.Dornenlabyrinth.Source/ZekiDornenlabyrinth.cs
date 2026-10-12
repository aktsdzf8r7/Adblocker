using HarmonyLib;
using OWML.Common;
using OWML.ModHelper;
using System;
using UnityEngine;

namespace ZekiDornenlabyrinth;

/// <summary>
/// "Das Dornenlabyrinth": a drifting bramble seed in the solar system leads into an infinite, fixed labyrinth of
/// bramble dimensions with coloured nodes and the Bramble Heart at its centre. New Horizons builds one dimension per
/// room type; this DLL turns them into the infinite maze by retargeting the nodes before every warp.
/// Design: docs/superpowers/specs/2026-10-11-dornenlabyrinth-design.md
/// </summary>
public class ZekiDornenlabyrinth : ModBehaviour
{
    public static ZekiDornenlabyrinth Instance;
    public INewHorizons NewHorizons;

    public void Awake() => Instance = this;

    /// <summary>Whether this scene's star system was built (by the NH event or, failing that, by the watchdog).</summary>
    private bool _built;

    public void Start()
    {
        Log("Dornenlabyrinth startet.");
        NewHorizons = ModHelper.Interaction.TryGetModApi<INewHorizons>("xen.NewHorizons");
        if (NewHorizons == null)
        {
            Log("New Horizons nicht gefunden - das Dornenlabyrinth bleibt aus.", true);
            return;
        }
        NewHorizons.GetStarSystemLoadedEvent().AddListener(OnSystemLoaded);
        NewHorizons.LoadConfigs(this);
        Guard("Harmony", () => new Harmony("Zeki.Dornenlabyrinth").PatchAll(typeof(ZekiDornenlabyrinth).Assembly));
        LoadManager.OnStartSceneLoad += (_, _) =>
        {
            _built = false;
            Guard("Zurücksetzen", Labyrinth.Reset);
            Guard("Zurücksetzen (Herz)", BrambleHeart.Reset);
        };
        GlobalMessenger.AddListener("WakeUp", OnWakeUp);
        Log("Dornenlabyrinth ist geladen.");
    }

    private void OnSystemLoaded(string system)
    {
        Log($"Sternsystem {system} geladen.");
        _built = true;
        if (system != "SolarSystem") return;
        Guard("Modelle", () => ModelPlacer.PlaceAll(this));
        // the maze needs the models (colour rings) but must come up even if they failed
        Guard("Labyrinth", () => Labyrinth.Setup(this));
        Guard("Herz", () => BrambleHeart.Setup(this));
    }

    /// <summary>
    /// New Horizons calls its listeners one after another; one that throws stops the rest. If the "system loaded"
    /// event never reached us by the time the player wakes up, build anyway.
    /// </summary>
    private void OnWakeUp() => StartCoroutine(Watchdog());

    private System.Collections.IEnumerator Watchdog()
    {
        yield return new WaitForSeconds(1f);
        if (_built) yield break;
        var system = NewHorizons.GetCurrentStarSystem();
        Log($"Das Ladeereignis von New Horizons kam nicht an - baue {system} selbst auf.", true);
        OnSystemLoaded(system);
    }

    public void Guard(string what, Action step)
    {
        try
        {
            step();
        }
        catch (Exception e)
        {
            Log($"Fehler ({what}): {e}", true);
        }
    }

    public void Log(string message, bool warning = false) =>
        ModHelper.Console.WriteLine(message, warning ? MessageType.Warning : MessageType.Info);

    public static void Notify(string message, float duration = 6f) =>
        NotificationManager.SharedInstance?.PostNotification(new NotificationData(NotificationTarget.All, message, duration, true), false);
}
