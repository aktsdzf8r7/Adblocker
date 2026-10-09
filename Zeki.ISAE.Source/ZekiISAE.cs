using HarmonyLib;
using OWML.Common;
using OWML.ModHelper;
using System.Collections;
using System.Reflection;
using UnityEngine;

namespace ZekiISAE;

/// <summary>
/// "Die Aussendungseinheit": while the Interstellare Sonden Aussendungseinheit (ISAE) is still running,
/// the end of the time loop does not end in a supernova. The ISAE drains the dying sun instead: it shrinks
/// until it is gone, and the game ends with a New Horizons game over (see addon-manifest.json).
/// The ISAE is switched off in game through NH interaction volumes that set persistent conditions.
/// </summary>
public class ZekiISAE : ModBehaviour
{
    // persistent conditions (set by the NH configs of this mod)
    public const string Deactivated = "ZEKISAE_DEAKTIVIERT";
    public const string Discovered = "ZEKISAE_ENTDECKT";
    // dialogue conditions (set here)
    public const string DrainActive = "ZEKISAE_ENTZUG";
    public const string UniverseEnds = "ZEKISAE_UNIVERSUM_ENDET";

    public static ZekiISAE Instance;
    public INewHorizons NewHorizons;

    public bool OnlyAfterDiscovery;
    public float DrainSeconds = 45f;

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
        new Harmony("Zeki.ISAE").PatchAll(Assembly.GetExecutingAssembly());
        LoadManager.OnCompleteSceneLoad += OnCompleteSceneLoad;
        ModHelper.Console.WriteLine("Die Aussendungseinheit ist geladen.", MessageType.Success);
    }

    public override void Configure(IModConfig config)
    {
        OnlyAfterDiscovery = config.GetSettingsValue<bool>("onlyAfterDiscovery");
        DrainSeconds = Mathf.Clamp(config.GetSettingsValue<float>("drainSeconds"), 10f, 180f);
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
public static class SunControllerPatches
{
    private static bool IsHearthianSun(SunController sun)
    {
        var astro = sun.GetComponentInParent<AstroObject>();
        return astro != null && astro.GetAstroObjectName() == AstroObject.Name.Sun;
    }

    /// <summary>The loop is over: let the ISAE take the dying sun instead of the supernova.</summary>
    [HarmonyPrefix]
    [HarmonyPatch(typeof(SunController), nameof(SunController.OnTriggerSupernova))]
    public static bool OnTriggerSupernova(SunController __instance)
    {
        if (ZekiISAE.Instance == null || !ZekiISAE.Instance.IsArmed() || !IsHearthianSun(__instance)) return true;
        if (__instance.GetComponent<SunDrain>() == null) __instance.gameObject.AddComponent<SunDrain>().Sun = __instance;
        return false;
    }

    /// <summary>While the sun is drained, the vanilla growth/collapse animation must not run.</summary>
    [HarmonyPrefix]
    [HarmonyPatch(typeof(SunController), nameof(SunController.Update))]
    public static bool Update(SunController __instance) => __instance.GetComponent<SunDrain>() == null;
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
    [HarmonyPatch(nameof(OrbitalProbeLaunchController.FixedUpdate))]
    public static bool FixedUpdate(OrbitalProbeLaunchController __instance) => !IsCopy(__instance);

    [HarmonyPrefix]
    [HarmonyPatch(nameof(OrbitalProbeLaunchController.OnDestroy))]
    public static bool OnDestroy(OrbitalProbeLaunchController __instance) => !IsCopy(__instance);

    [HarmonyPrefix]
    [HarmonyPatch(nameof(OrbitalProbeLaunchController.OnStartOfTimeLoop))]
    public static bool OnStartOfTimeLoop(OrbitalProbeLaunchController __instance) => !IsCopy(__instance);

    [HarmonyPrefix]
    [HarmonyPatch(nameof(OrbitalProbeLaunchController.LaunchProbe))]
    public static bool LaunchProbe(OrbitalProbeLaunchController __instance) => !IsCopy(__instance);
}

/// <summary>Shrinks the sun to nothing, puts out its light and then ends the game.</summary>
public class SunDrain : MonoBehaviour
{
    public SunController Sun;

    private float _start;
    private float _startScale;
    private float _startSunLight, _startAmbientLight, _startLocalAmbient;
    private bool _finished;

    public void Start()
    {
        _start = Time.time;
        _startScale = Sun._scale > 0f ? Sun._scale : 1f;
        var light = Sun._sunLight;
        if (light != null)
        {
            _startSunLight = light._sunBaseIntensity;
            _startAmbientLight = light._ambientBaseIntensity;
        }
        if (Sun._ambientLight != null) _startLocalAmbient = Sun._ambientLight.intensity;

        DialogueConditionManager.SharedInstance.SetConditionState(ZekiISAE.DrainActive, true);
        ZekiISAE.Notify("DIE AUSSENDUNGSEINHEIT ENTZIEHT DER SONNE IHRE ENERGIE", 8f);
    }

    public void Update()
    {
        if (_finished) return;
        var t = Mathf.Clamp01((Time.time - _start) / ZekiISAE.Instance.DrainSeconds);
        var remaining = 1f - t * t * (3f - 2f * t);

        Sun.UpdateScale(Mathf.Max(_startScale * remaining, 0.002f));
        var light = Sun._sunLight;
        if (light != null)
        {
            light._sunBaseIntensity = _startSunLight * remaining;
            light._ambientBaseIntensity = _startAmbientLight * remaining;
            light.sunIntensity = _startSunLight * remaining;
            light.ambientIntensity = _startAmbientLight * remaining;
        }
        if (Sun._ambientLight != null) Sun._ambientLight.intensity = _startLocalAmbient * remaining;

        if (t >= 1f)
        {
            _finished = true;
            Sun.SetRenderingEnabled(false);
            StartCoroutine(EndOfEverything());
        }
    }

    private IEnumerator EndOfEverything()
    {
        ZekiISAE.Notify("DIE SONNE IST ERLOSCHEN", 5f);
        yield return new WaitForSeconds(5f);
        // New Horizons shows the game over text of addon-manifest.json when the player dies while this is set
        DialogueConditionManager.SharedInstance.SetConditionState(ZekiISAE.UniverseEnds, true);
        var death = Locator.GetDeathManager();
        if (death != null && !death.IsPlayerDying() && !death.IsPlayerDead())
        {
            death.KillPlayer(DeathType.Energy);
        }
    }
}
