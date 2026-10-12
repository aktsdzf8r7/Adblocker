using UnityEngine;
using UnityEngine.UI;

namespace ZekiVerdornt;

/// <summary>
/// The way between Timber Hearth and Dornenkranz (spec section 4):
///   * the thorn vortex in the middle of the Samenschlund changes the star system to "Verdornt",
///   * after such a crossing the player comes to on Erstling in a green haze,
///   * the return seed in the camp (NH interaction volume sets ZEKIVD_HEIMREISE) changes back to the SolarSystem.
/// </summary>
public class Crossing : MonoBehaviour
{
    public const string HomeCondition = "ZEKIVD_HEIMREISE";
    public const string FirstJourney = "ZEKIVD_ERSTE_REISE";
    public const string ArrivalFact = "ZEKIVD_ANKUNFT";
    public const string SeedNode = "ZEKIVD_Absturzsamen";
    private const float VortexRadius = 12f;

    /// <summary>Survives the scene change: the next "Verdornt" load is an arrival through the seed.</summary>
    private static bool _arriving;

    private readonly CrossingState _state = new();
    private ZekiVerdornt _mod;
    private string _system;
    private Transform _vortex;
    private Veil _veil;

    public static void Setup(ZekiVerdornt mod, string system)
    {
        var go = new GameObject("VD_Uebergang");
        var c = go.AddComponent<Crossing>();
        c._mod = mod;
        c._system = system;
        c._veil = Veil.Create();
        if (system == "SolarSystem")
        {
            var schlund = mod.NewHorizons.GetPlanet("Samenschlund");
            c._vortex = schlund != null ? schlund.transform : null;
        }
        else if (system == ZekiVerdornt.SystemName && _arriving)
        {
            _arriving = false;
            c.Arrive();
        }
    }

    // ------------------------------------------------------------------------------------------ crossings
    public void Update()
    {
        var dm = Locator.GetDeathManager();
        var dying = dm != null && (dm.IsPlayerDying() || dm.IsPlayerDead());
        var player = Locator.GetPlayerTransform();
        if (player == null || dying) return;
        if (_vortex != null && Vector3.Distance(player.position, _vortex.position) < VortexRadius && _state.TryBegin())
            StartCoroutine(Cross(ZekiVerdornt.SystemName, true));
        if (_system == ZekiVerdornt.SystemName && Condition(HomeCondition))
        {
            DialogueConditionManager.SharedInstance.SetConditionState(HomeCondition, false);
            if (_state.TryBegin()) StartCoroutine(Cross("SolarSystem", false));
        }
    }

    private static bool Condition(string name) => DialogueConditionManager.SharedInstance != null &&
                                                 DialogueConditionManager.SharedInstance.GetConditionState(name);

    private System.Collections.IEnumerator Cross(string target, bool arrive)
    {
        _mod.Log($"Übergang nach {target}.");
        PlayOneShot(AudioType.DB_VineImpact);
        _veil.FadeTo(1f, 1.1f);
        yield return new WaitForSeconds(1.2f);
        var dm = Locator.GetDeathManager();
        if (!_state.MayChangeSystem(dm != null && (dm.IsPlayerDying() || dm.IsPlayerDead())))
        {
            _mod.Log("Übergang abgebrochen: der Spieler stirbt.");
            _veil.FadeTo(0f, 0.5f);
            yield break;
        }
        _arriving = arrive;
        if (!_mod.NewHorizons.ChangeCurrentStarSystem(target))
        {
            _mod.Log($"Systemwechsel nach {target} abgelehnt.", true);
            _arriving = false;
            _veil.FadeTo(0f, 1f);
            _state.Reset();
        }
    }

    /// <summary>Waking up on Erstling: the green haze of the seed lifts.</summary>
    private void Arrive()
    {
        _veil.Set(1f);
        _veil.FadeTo(0f, 3.5f);
        PlayOneShot(AudioType.VesselSingularityCreate);
        PlayerData.SetPersistentCondition(FirstJourney, true);
        var log = Locator.GetShipLogManager();
        if (log != null) log.RevealFact(ArrivalFact, true, true);
        ZekiVerdornt.Notify("UNBEKANNTES SYSTEM. DIE DORNEN SIND ÜBERALL.", 7f);
    }

    public static void PlayOneShot(AudioType type)
    {
        var audio = Locator.GetPlayerAudioController();
        if (audio != null) audio.PlayOneShotInternal(type);
    }
}

/// <summary>A full-screen green haze for the crossings.</summary>
public class Veil : MonoBehaviour
{
    private Image _image;
    private float _target, _speed = 1f;

    public static Veil Create()
    {
        var go = new GameObject("VD_Schleier");
        var canvas = go.AddComponent<Canvas>();
        canvas.renderMode = RenderMode.ScreenSpaceOverlay;
        canvas.sortingOrder = 31500;
        var imageGo = new GameObject("Bild", typeof(RectTransform));
        imageGo.transform.SetParent(go.transform, false);
        var rt = (RectTransform)imageGo.transform;
        rt.anchorMin = Vector2.zero;
        rt.anchorMax = Vector2.one;
        rt.offsetMin = rt.offsetMax = Vector2.zero;
        var v = go.AddComponent<Veil>();
        v._image = imageGo.AddComponent<Image>();
        v._image.color = new Color(0.32f, 0.55f, 0.36f, 0f);
        v._image.raycastTarget = false;
        return v;
    }

    public void Set(float alpha)
    {
        var c = _image.color;
        _image.color = new Color(c.r, c.g, c.b, alpha);
        _target = alpha;
    }

    public void FadeTo(float alpha, float seconds)
    {
        _target = alpha;
        _speed = 1f / Mathf.Max(0.01f, seconds);
    }

    public void Update()
    {
        var c = _image.color;
        _image.color = new Color(c.r, c.g, c.b, Mathf.MoveTowards(c.a, _target, Time.deltaTime * _speed));
    }
}
