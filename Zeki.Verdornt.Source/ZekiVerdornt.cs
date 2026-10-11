using HarmonyLib;
using OWML.Common;
using OWML.ModHelper;
using System;
using UnityEngine;

namespace ZekiVerdornt;

/// <summary>
/// "Verdornt": a bramble seed crashed on Timber Hearth leads into Dornenkranz, the overgrown home system of
/// Dark Bramble. New Horizons builds the world from the configs; this DLL adds what NH cannot do: the crossing
/// between the systems, marble tubes, reactive Nomai computers and the real Dark Bramble vines.
/// Design: docs/superpowers/specs/2026-10-10-verdornt-design.md
/// </summary>
public class ZekiVerdornt : ModBehaviour
{
    public const string SystemName = "Verdornt";

    public static ZekiVerdornt Instance;
    public INewHorizons NewHorizons;
    public bool Cinematic = true;

    /// <summary>Raised after New Horizons has built a star system (name of the system).</summary>
    public event Action<string> SystemLoaded;

    public void Awake() => Instance = this;

    /// <summary>Whether this scene's star system was built (by the NH event or, failing that, by the watchdog).</summary>
    private bool _built;

    public void Start()
    {
        Log("Verdornt startet.");
        // our own handler first: whatever happens below, the world still gets built
        SystemLoaded += Build;
        NewHorizons = ModHelper.Interaction.TryGetModApi<INewHorizons>("xen.NewHorizons");
        if (NewHorizons == null)
        {
            Log("New Horizons nicht gefunden - Verdornt bleibt aus.", true);
            return;
        }
        NewHorizons.GetStarSystemLoadedEvent().AddListener(OnSystemLoaded);
        NewHorizons.LoadConfigs(this);
        // only for the ship log layout (ShipLogPlacement.cs); the world does not depend on it
        Guard("Harmony", () => new Harmony("Zeki.Verdornt").PatchAll(typeof(ZekiVerdornt).Assembly));
        LoadManager.OnStartSceneLoad += (_, _) => _built = false;
        GlobalMessenger.AddListener("WakeUp", OnWakeUp);
        Log("Verdornt ist geladen.");
    }

    private void Build(string system)
    {
        Log($"Sternsystem {system} geladen.");
        _built = true;
        if (system != SystemName && system != "SolarSystem") return;
        // the crossing is the only way in and out: it comes first, and nothing else may take it down
        Guard("Übergang", () => Crossing.Setup(this, system));
        Guard("Modelle", () => ModelPlacer.PlaceAll(this));
        if (system == "SolarSystem") Guard("Absturzstelle", () => CrashSite.Begin(this));
        Guard("Computer", () => ReactiveComputers.Setup(this));
        Guard("Murmelröhren", () => MarbleTube.Setup(this));
        if (system == SystemName) Guard("Dornensprache", () => BrambleScript.Setup(this));
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

    public override void Configure(IModConfig config)
    {
        Cinematic = config.GetSettingsValue<bool>("cinematic");
    }

    private void OnSystemLoaded(string system)
    {
        try
        {
            SystemLoaded?.Invoke(system);
        }
        catch (Exception e)
        {
            Log($"Fehler beim Aufbau von {system}: {e}", true);
        }
    }

    private void Guard(string what, Action step)
    {
        try
        {
            step();
        }
        catch (Exception e)
        {
            Log($"Fehler beim Aufbau ({what}): {e}", true);
        }
    }

    public void Log(string message, bool warning = false) =>
        ModHelper.Console.WriteLine(message, warning ? MessageType.Warning : MessageType.Info);

    public static void Notify(string message, float duration = 6f) =>
        NotificationManager.SharedInstance?.PostNotification(new NotificationData(NotificationTarget.All, message, duration, true), false);
}
