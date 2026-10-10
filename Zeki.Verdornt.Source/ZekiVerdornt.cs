using HarmonyLib;
using OWML.Common;
using OWML.ModHelper;
using System;
using System.Reflection;
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

    public void Start()
    {
        NewHorizons = ModHelper.Interaction.TryGetModApi<INewHorizons>("xen.NewHorizons");
        NewHorizons.LoadConfigs(this);
        NewHorizons.GetStarSystemLoadedEvent().AddListener(OnSystemLoaded);
        new Harmony("Zeki.Verdornt").PatchAll(Assembly.GetExecutingAssembly());
        SystemLoaded += system =>
        {
            if (system != SystemName && system != "SolarSystem") return;
            // the crossing is the only way in and out: it comes first, and nothing else may take it down
            Guard("Übergang", () => Crossing.Setup(this, system));
            Guard("Modelle", () => ModelPlacer.PlaceAll(this));
            Guard("Computer", () => ReactiveComputers.Setup(this));
            Guard("Murmelröhren", () => MarbleTube.Setup(this));
        };
        Log("Verdornt ist geladen.");
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
