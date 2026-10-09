using HarmonyLib;
using OWML.Common;
using OWML.ModHelper;
using System;
using System.Reflection;
using UnityEngine;

namespace ZekiISAE;

/// <summary>
/// "Die Aussendungseinheit": while the Interstellare Sonden Aussendungseinheit (ISAE) is still running,
/// the end of the time loop does not end in a supernova. The ISAE drains the dying sun instead (see Finale):
/// it shrinks until it is gone, the cannon fires, and the game ends with a New Horizons game over.
/// The ISAE is switched off in game through NH interaction volumes that set persistent conditions.
/// This class also loads the Blender props (Models.cs) once New Horizons has built the system.
/// </summary>
public class ZekiISAE : ModBehaviour
{
    public const string IsaeName = "Interstellare Sonden Aussendungseinheit";

    // persistent conditions (set by the NH configs of this mod)
    public const string Deactivated = "ZEKISAE_DEAKTIVIERT";
    public const string Discovered = "ZEKISAE_ENTDECKT";
    // dialogue conditions (set here)
    public const string DrainActive = "ZEKISAE_ENTZUG";
    public const string UniverseEnds = "ZEKISAE_UNIVERSUM_ENDET";

    public static ZekiISAE Instance;
    public INewHorizons NewHorizons;

    public bool OnlyAfterDiscovery;
    public float DrainSeconds = 60f;
    public bool Cinematic = true;
    public bool UseGameMaterials = true;
    public bool AutoAim = true;

    private bool _warnedAtStart;
    private bool _warnedBeforeEnd;
    private bool _wasDeactivated;
    private float _sceneLoadedAt = -1f;

    public void Awake()
    {
        Instance = this;
    }

    public void Start()
    {
        NewHorizons = ModHelper.Interaction.TryGetModApi<INewHorizons>("xen.NewHorizons");
        NewHorizons.LoadConfigs(this);
        NewHorizons.GetStarSystemLoadedEvent().AddListener(OnStarSystemLoaded);
        new Harmony("Zeki.ISAE").PatchAll(Assembly.GetExecutingAssembly());
        LoadManager.OnCompleteSceneLoad += OnCompleteSceneLoad;
        Log("Die Aussendungseinheit ist geladen.");
    }

    public override void Configure(IModConfig config)
    {
        OnlyAfterDiscovery = config.GetSettingsValue<bool>("onlyAfterDiscovery");
        DrainSeconds = Mathf.Clamp(config.GetSettingsValue<float>("drainSeconds"), 20f, 180f);
        Cinematic = config.GetSettingsValue<bool>("cinematic");
        UseGameMaterials = config.GetSettingsValue<bool>("useGameMaterials");
        AutoAim = config.GetSettingsValue<bool>("autoAim");
    }

    public void Log(string message, bool warning = false)
    {
        ModHelper.Console.WriteLine(message, warning ? MessageType.Warning : MessageType.Info);
    }

    private void OnStarSystemLoaded(string system)
    {
        if (system != "SolarSystem") return;
        try
        {
            CannonAim.Apply(this);
            ModelPlacer.PlaceAll(this);
        }
        catch (Exception e)
        {
            Log("Fehler beim Aufbau der Aussendungseinheit: " + e, true);
        }
    }

    private void OnCompleteSceneLoad(OWScene previousScene, OWScene newScene)
    {
        _warnedAtStart = false;
        _warnedBeforeEnd = false;
        _wasDeactivated = PlayerData.GetPersistentCondition(Deactivated);
        _sceneLoadedAt = newScene == OWScene.SolarSystem ? Time.time : -1f;
    }

    /// <summary>Is the ISAE armed in the current loop?</summary>
    public bool IsArmed()
    {
        if (LoadManager.GetCurrentScene() != OWScene.SolarSystem) return false;
        if (NewHorizons != null && NewHorizons.GetCurrentStarSystem() != "SolarSystem") return false;
        if (PlayerData.GetPersistentCondition(Deactivated)) return false;
        if (OnlyAfterDiscovery && !PlayerData.GetPersistentCondition(Discovered)) return false;
        return true;
    }

    public void Update()
    {
        if (_sceneLoadedAt < 0f) return;
        if (!_wasDeactivated && PlayerData.GetPersistentCondition(Deactivated))
        {
            _wasDeactivated = true;
            Notify("DIE AUSSENDUNGSEINHEIT IST ABGESCHALTET. DIE SONNE GEHÖRT WIEDER SICH SELBST.", 8f);
        }
        if (!IsArmed() || !TimeLoop.IsTimeFlowing()) return;

        if (!_warnedAtStart && Time.time - _sceneLoadedAt > 12f)
        {
            _warnedAtStart = true;
            Notify("UNBEKANNTE NOMAI-ENERGIESIGNATUR IN DER NÄHE DER SONNE");
        }
        if (!_warnedBeforeEnd && TimeLoop.GetSecondsRemaining() < 300f && TimeLoop.GetSecondsRemaining() > 0f)
        {
            _warnedBeforeEnd = true;
            Notify("WARNUNG: DIE AUSSENDUNGSEINHEIT BEREITET DEN ENERGIEENTZUG VOR");
        }
    }

    public static void Notify(string message, float duration = 6f)
    {
        NotificationManager.SharedInstance?.PostNotification(new NotificationData(NotificationTarget.All, message, duration, true), false);
    }
}

[HarmonyPatch]
public static class SunPatches
{
    private static bool IsHearthianSun(Component sun)
    {
        var astro = sun.GetComponentInParent<AstroObject>();
        return astro != null && astro.GetAstroObjectName() == AstroObject.Name.Sun;
    }

    private static bool Armed => ZekiISAE.Instance != null && ZekiISAE.Instance.IsArmed();

    /// <summary>The loop is over: the ISAE takes the dying sun instead of the supernova.</summary>
    [HarmonyPrefix]
    [HarmonyPatch(typeof(SunController), nameof(SunController.OnTriggerSupernova))]
    public static bool OnTriggerSupernova(SunController __instance)
    {
        if (!Armed || !IsHearthianSun(__instance)) return true;
        if (__instance.GetComponent<Finale>() == null) __instance.gameObject.AddComponent<Finale>().Sun = __instance;
        return false;
    }

    /// <summary>While the sun is drained, the vanilla growth/collapse animation must not run.</summary>
    [HarmonyPrefix]
    [HarmonyPatch(typeof(SunController), nameof(SunController.Update))]
    public static bool Update(SunController __instance) => __instance.GetComponent<Finale>() == null;

    /// <summary>The far-away picture of the sun must not explode either; the Finale shrinks it.</summary>
    [HarmonyPrefix]
    [HarmonyPatch(typeof(DistantSunController), nameof(DistantSunController.OnTriggerSupernova))]
    public static bool DistantSupernova() => !Armed;
}

/// <summary>
/// The ISAE is a copy of the Orbital Probe Cannon's sector. If that copy contains the launch controller, it must
/// not touch the real Nomai probe: every controller that is not part of the vanilla cannon stays switched off.
/// </summary>
[HarmonyPatch(typeof(OrbitalProbeLaunchController))]
public static class ProbeCannonCopyPatches
{
    private static bool IsCopy(Component c)
    {
        var astro = c.GetComponentInParent<AstroObject>();
        return astro != null && astro.GetAstroObjectName() != AstroObject.Name.ProbeCannon;
    }

    [HarmonyPrefix]
    [HarmonyPatch(nameof(OrbitalProbeLaunchController.Awake))]
    public static bool Awake(OrbitalProbeLaunchController __instance)
    {
        if (!IsCopy(__instance)) return true;
        __instance.enabled = false;
        return false;
    }

    [HarmonyPrefix]
    [HarmonyPatch(nameof(OrbitalProbeLaunchController.OnDestroy))]
    public static bool OnDestroy(OrbitalProbeLaunchController __instance) => !IsCopy(__instance);

    [HarmonyPrefix]
    [HarmonyPatch(nameof(OrbitalProbeLaunchController.OnStartOfTimeLoop))]
    public static bool OnStartOfTimeLoop(OrbitalProbeLaunchController __instance) => !IsCopy(__instance);

    [HarmonyPrefix]
    [HarmonyPatch(nameof(OrbitalProbeLaunchController.FixedUpdate))]
    public static bool FixedUpdate(OrbitalProbeLaunchController __instance) => !IsCopy(__instance);

    [HarmonyPrefix]
    [HarmonyPatch(nameof(OrbitalProbeLaunchController.LaunchProbe))]
    public static bool LaunchProbe(OrbitalProbeLaunchController __instance) => !IsCopy(__instance);
}
