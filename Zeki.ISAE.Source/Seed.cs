using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using UnityEngine.UI;

namespace ZekiISAE;

/// <summary>
/// The Samenkern and what it does (1.5, "Verwurzelt"):
///   * The Keimdorn, a small bramble seed, orbits Dark Bramble. Inside it lies the Samenkammer, a small bramble
///     dimension (NH configs). Its baby seed is linked here to the dimension of the Vessel.
///   * The Samenkern floats in the middle of the Samenkammer (an NH item). Taking it makes the chamber quake;
///     whoever stays too long is crushed. Once the player has left, the Keimdorn behind them goes out.
///   * The Pulskern on the floor of the ISAE's core chamber pulses (an NH item socket over it). The Samenkern
///     inserted there makes a baby seed appear that grows a year in every second and swallows the cannon with roots.
///     Inside the chamber the player ages a year per second as well.
/// </summary>
public class SeedSystem : MonoBehaviour
{
    public const string BabyNode = "ZEKISAE_Babysamen_Knoten";
    public const string KeimNode = "ZEKISAE_Keimdorn_Knoten";
    private const float QuakeDeadline = 75f;

    public static SeedSystem Instance;
    public static bool Rooted => Instance != null && Instance._rooted;

    /// <summary>0..1: the core of the switched-off wreck gets unstable (Ende 3).</summary>
    public float Instability;

    private ZekiISAE _mod;
    private Transform _glow, _seedling, _roots, _keimdorn, _keimNode, _thorns, _samenkammer, _seedModel, _frame;
    private Light _pulseLight, _keimLight;
    private float _pulseLightBase = 2f, _keimLightBase = 1.6f;
    private Vector3 _frameHome;
    private readonly List<GameObject> _beacons = new();

    private bool _taken, _wasInside, _extinguishing, _extinguished, _crushed, _rooted;
    private float _takenAt, _leftAt = -1f, _extinguishStart, _rootStart, _nextQuakeSound, _years;
    private float _nodeScale = 1f, _thornScale = 1f;
    private Text _hud;
    private CanvasGroup _hudGroup;

    public static void Setup(ZekiISAE mod)
    {
        if (GameProps.Pivot == null) return;
        var s = GameProps.Pivot.gameObject.AddComponent<SeedSystem>();
        s._mod = mod;
    }

    public void Awake() => Instance = this;

    public void Start()
    {
        var pivot = transform;
        _glow = pivot.Find("ISAE_Pulsglut");
        _seedling = pivot.Find("ISAE_Keimling");
        _roots = pivot.Find("ISAE_Wurzeln");
        var light = pivot.Find("Licht_Pulskern");
        _pulseLight = light != null ? light.GetComponent<Light>() : null;
        if (_pulseLight != null) _pulseLightBase = _pulseLight.intensity;

        var keim = _mod.NewHorizons.GetPlanet("Keimdorn");
        _keimdorn = keim != null ? keim.transform : null;
        if (_keimdorn != null)
        {
            _keimNode = Deep(_keimdorn, KeimNode);
            _thorns = Deep(_keimdorn, "Keimdorn_Dornen");
            var kl = Deep(_keimdorn, "Licht_Keimdorn");
            _keimLight = kl != null ? kl.GetComponent<Light>() : null;
            if (_keimLight != null) _keimLightBase = _keimLight.intensity;
            foreach (var t in _keimdorn.GetComponentsInChildren<Transform>(true))
                if (t.name.StartsWith("Keimdorn_Leuchtfeuer")) _beacons.Add(t.gameObject);
        }
        var kammer = _mod.NewHorizons.GetPlanet("Samenkammer");
        _samenkammer = kammer != null ? kammer.transform : null;
        if (_samenkammer != null)
        {
            _seedModel = Deep(_samenkammer, "Samenkern_Modell");
            _frame = Deep(_samenkammer, "Herzgeruest");
            if (_frame != null) _frameHome = _frame.localPosition;
            LinkBabyNode();
        }
        _mod.Log($"Samen: Keimdorn {(_keimdorn != null ? "ok" : "fehlt")}, Knoten {(_keimNode != null ? "ok" : "fehlt")}, " +
                 $"Samenkammer {(_samenkammer != null ? "ok" : "fehlt")}, Pulskern {(_glow != null ? "ok" : "fehlt")}, Wurzeln {(_roots != null ? "ok" : "fehlt")}.");
    }

    private static Transform Deep(Transform root, string name) =>
        root.GetComponentsInChildren<Transform>(true).FirstOrDefault(t => t.name == name);

    private static bool Condition(string name) => DialogueConditionManager.SharedInstance != null &&
                                                 DialogueConditionManager.SharedInstance.GetConditionState(name);

    /// <summary>NH can only link nodes to its own dimensions; the baby seed leads into the vanilla Vessel dimension.</summary>
    private void LinkBabyNode()
    {
        var node = Deep(_samenkammer, BabyNode);
        var inner = node != null ? node.GetComponentInChildren<InnerFogWarpVolume>(true) : null;
        var outer = Resources.FindObjectsOfTypeAll<OuterFogWarpVolume>()
            .FirstOrDefault(o => o.gameObject.scene.IsValid() && o.transform.root.name == "DB_VesselDimension_Body");
        if (inner == null || outer == null)
        {
            _mod.Log($"Babysamen nicht mit dem Vessel verbunden (Knoten {(inner != null ? "ok" : "fehlt")}, Vessel-Dimension {(outer != null ? "ok" : "fehlt")}).", true);
            return;
        }
        var own = inner._linkedOuterWarpVolume;
        if (own != null && own != outer && own._senderWarps != null) own._senderWarps.Remove(inner);
        inner._linkedOuterWarpVolume = outer;
        inner._linkedOuterWarpName = outer.GetName();
        if (outer._senderWarps == null || !outer._senderWarps.Contains(inner)) outer.RegisterSenderWarp(inner);
        _mod.Log("Babysamen führt jetzt in die Dimension des Vessels.");
    }

    public void Update()
    {
        Pulse();
        if (!_taken && Condition(ZekiISAE.SeedTaken))
        {
            _taken = true;
            _takenAt = Time.time;
            ZekiISAE.Notify("DER SAMENKERN LÖST SICH. DIE SAMENKAMMER BEBT – VERLASSE SIE!", 7f);
            Ending.PlayOneShot(AudioType.DB_VineImpact);
        }
        if (_taken && !_extinguishing) Quake();
        if (_extinguishing && !_extinguished) Extinguish();
        if (!_rooted && Condition(ZekiISAE.SeedInserted)) StartRooting(false);
        if (_rooted) Grow();
        Years();
    }

    // ------------------------------------------------------------------------------------------ pulse
    private void Pulse()
    {
        var t = Time.time;
        if (_glow != null)
        {
            float s, light;
            if (Instability > 0f)
            {
                // the wreck's core: irregular, ever stronger flicker
                var n = Mathf.PerlinNoise(t * (4f + 14f * Instability), 0.5f);
                s = 1f + (0.2f + 0.9f * Instability) * (n - 0.3f);
                light = 0.6f + 2.4f * n * (0.5f + Instability);
            }
            else if (_rooted)
            {
                var w = Mathf.Abs(Mathf.Sin(t * Mathf.PI * 3.5f));
                s = 1.05f + 0.35f * w;
                light = 1f + 1.5f * w;
            }
            else
            {
                var w = 0.5f + 0.5f * Mathf.Sin(t * Mathf.PI * 1.4f);
                s = 1f + 0.14f * w;
                light = 0.8f + 0.5f * w;
            }
            _glow.localScale = Vector3.one * s;
            if (_pulseLight != null) _pulseLight.intensity = _pulseLightBase * light;
        }
        if (_seedModel != null)
        {
            // the Samenkern beats once every eleven seconds - and fast once it is taken
            var period = _taken ? 1.1f : 11f;
            var since = t % period;
            _seedModel.localScale = Vector3.one * (1f + 0.35f * Mathf.Exp(-since * 4f));
        }
    }

    // ------------------------------------------------------------------------------------------ the quaking seed chamber
    private bool PlayerInSeedChamber()
    {
        var player = Locator.GetPlayerTransform();
        if (player == null || _samenkammer == null || !PlayerState.InBrambleDimension()) return false;
        return Vector3.Distance(player.position, _samenkammer.position) < 450f;
    }

    private void Quake()
    {
        var inside = PlayerInSeedChamber();
        if (inside)
        {
            _wasInside = true;
            _leftAt = -1f;
            var since = Time.time - _takenAt;
            var strength = 0.25f + 0.75f * Mathf.Clamp01(since / 60f);
            Shaker.Request(strength);
            if (_frame != null) _frame.localPosition = _frameHome + Random.insideUnitSphere * (0.4f * strength);
            if (Time.time >= _nextQuakeSound)
            {
                _nextQuakeSound = Time.time + Random.Range(2f, 4.5f) * (1.2f - strength);
                Ending.PlayOneShot(AudioType.DB_VineImpact);
                RumbleManager.PulseHeavyImpact();
            }
            if (since > QuakeDeadline - 20f && since - Time.deltaTime <= QuakeDeadline - 20f)
                ZekiISAE.Notify("DIE SAMENKAMMER FÄLLT IN SICH ZUSAMMEN!", 6f);
            if (since > QuakeDeadline && !_crushed)
            {
                _crushed = true;
                var dm = Locator.GetDeathManager();
                if (dm != null && !dm.IsPlayerDying() && !dm.IsPlayerDead()) dm.KillPlayer(DeathType.Crushed);
            }
            return;
        }
        if (!_wasInside) return;
        // the player got out: shortly after, the Keimdorn behind them goes out
        if (_leftAt < 0f) _leftAt = Time.time;
        if (Time.time - _leftAt > 1.5f)
        {
            _extinguishing = true;
            _extinguishStart = Time.time;
            if (_frame != null) _frame.localPosition = _frameHome;
            var player = Locator.GetPlayerTransform();
            if (_keimdorn != null && player != null && Vector3.Distance(player.position, _keimdorn.position) < 4000f)
                Ending.PlayOneShot(AudioType.VesselSingularityCollapse);
            ZekiISAE.Notify("HINTER DIR ERLISCHT DER KEIMDORN", 6f);
        }
    }

    private void Extinguish()
    {
        var k = Mathf.Clamp01((Time.time - _extinguishStart) / 14f);
        var flicker = k < 0.7f ? 0.75f + 0.25f * Mathf.PerlinNoise(Time.time * 12f, 1f) : 1f;
        if (_keimNode != null)
        {
            _nodeScale = Mathf.Max(0.01f, (1f - Mathf.Pow(k, 1.6f)) * flicker);
            _keimNode.localScale = Vector3.one * _nodeScale;
            foreach (var l in _keimNode.GetComponentsInChildren<Light>()) l.intensity *= 0.97f;
        }
        if (_thorns != null)
        {
            _thornScale = Mathf.Lerp(1f, 0.25f, k);
            _thorns.localScale = Vector3.one * (30f * _thornScale);
            _thorns.Rotate(Vector3.up, 8f * Time.deltaTime, Space.Self);
        }
        if (_keimLight != null) _keimLight.intensity = _keimLightBase * (1f - k) * flicker;
        for (var i = 0; i < _beacons.Count; i++)
            if (_beacons[i] != null && k > (i + 1f) / (_beacons.Count + 1f)) _beacons[i].SetActive(false);
        if (k >= 1f)
        {
            _extinguished = true;
            if (_keimNode != null) _keimNode.gameObject.SetActive(false);
            if (_thorns != null) _thorns.gameObject.SetActive(false);
            if (_keimLight != null) _keimLight.enabled = false;
        }
    }

    // ------------------------------------------------------------------------------------------ the roots
    /// <summary>The Samenkern lies in the Pulskern: a baby seed appears and its roots swallow the cannon.</summary>
    public void StartRooting(bool instant)
    {
        if (_rooted) return;
        _rooted = true;
        _rootStart = instant ? Time.time - 1000f : Time.time;
        if (!Condition(ZekiISAE.SeedInserted)) DialogueConditionManager.SharedInstance.SetConditionState(ZekiISAE.SeedInserted, true);
        if (_seedling != null)
        {
            _seedling.localScale = Vector3.one * 0.01f;
            _seedling.gameObject.SetActive(true);
        }
        if (_roots != null)
        {
            _roots.localScale = Vector3.one * 0.001f;
            _roots.gameObject.SetActive(true);
        }
        Grow();
        if (instant) return;
        Ending.PlayOneShot(AudioType.DB_VineImpact);
        Ending.PlayOneShot(AudioType.NomaiPowerOn);
        RumbleManager.PulseHeavyImpact();
        ZekiISAE.Notify("ZEITVERZERRUNG IM PULSKERN: EIN JAHR IN JEDER SEKUNDE", 6f);
        ZekiISAE.Instance.StartCoroutine(Later(5f, () => ZekiISAE.Notify("EIN BABYSAMEN KEIMT. SEINE WURZELN VERSCHLINGEN DIE AUSSENDUNGSEINHEIT.", 7f)));
    }

    private static System.Collections.IEnumerator Later(float seconds, System.Action action)
    {
        yield return new WaitForSeconds(seconds);
        action();
    }

    private void Grow()
    {
        var t = Time.time - _rootStart;
        if (_seedling != null)
        {
            // pops out of the core and keeps swelling: a year in every second
            var k = Mathf.Clamp01(t / 5f);
            var back = 1f + 2.2f * Mathf.Pow(k - 1f, 3f) + 1.2f * Mathf.Pow(k - 1f, 2f);
            _seedling.localScale = Vector3.one * (1.7f * Mathf.Max(0.01f, back) * (1f + 0.04f * Mathf.Sin(Time.time * 7f)));
        }
        if (_roots != null)
        {
            var k = Mathf.Clamp01((t - 2f) / 35f);
            _roots.localScale = Vector3.one * Mathf.Max(0.001f, k * k * (3f - 2f * k));
            if (k > 0f && k < 1f && !GameProps.PlayerFar(transform, 1500f)) Shaker.Request(0.25f);
            if (k > 0f && k < 1f && Time.time >= _nextQuakeSound && !GameProps.PlayerFar(transform, 3000f))
            {
                _nextQuakeSound = Time.time + Random.Range(1.5f, 3.5f);
                Ending.PlayOneShot(AudioType.DB_VineImpact);
            }
        }
    }

    // ------------------------------------------------------------------------------------------ a year per second
    private void Years()
    {
        var player = Locator.GetPlayerTransform();
        var inside = _rooted && player != null && Vector3.Distance(player.position, GameProps.Point("kern")) < 36f;
        if (inside) _years += Time.deltaTime;
        if (_hud == null && inside) BuildHud();
        if (_hud == null) return;
        _hudGroup.alpha = Mathf.MoveTowards(_hudGroup.alpha, inside ? 1f : 0f, Time.deltaTime * 2f);
        if (inside) _hud.text = $"ZEITVERZERRUNG: EIN JAHR PRO SEKUNDE\nDU BIST {Mathf.FloorToInt(_years)} JAHRE GEALTERT";
    }

    private void BuildHud()
    {
        var go = new GameObject("ZekiISAE_Jahre");
        var canvas = go.AddComponent<Canvas>();
        canvas.renderMode = RenderMode.ScreenSpaceOverlay;
        canvas.sortingOrder = 31000;
        var scaler = go.AddComponent<CanvasScaler>();
        scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
        scaler.referenceResolution = new Vector2(1920, 1080);
        var textGo = new GameObject("Text", typeof(RectTransform));
        textGo.transform.SetParent(go.transform, false);
        var rt = (RectTransform)textGo.transform;
        rt.anchorMin = new Vector2(0.25f, 1f);
        rt.anchorMax = new Vector2(0.75f, 1f);
        rt.pivot = new Vector2(0.5f, 1f);
        rt.anchoredPosition = new Vector2(0, -90);
        rt.sizeDelta = new Vector2(0, 110);
        _hudGroup = textGo.AddComponent<CanvasGroup>();
        _hudGroup.alpha = 0f;
        _hud = textGo.AddComponent<Text>();
        var gameOver = FindObjectOfType<GameOverController>();
        _hud.font = gameOver != null && gameOver._deathText != null && gameOver._deathText.font != null
            ? gameOver._deathText.font : Resources.GetBuiltinResource<Font>("Arial.ttf");
        _hud.fontSize = 34;
        _hud.alignment = TextAnchor.UpperCenter;
        _hud.color = new Color(0.65f, 1f, 0.7f);
        var shadow = textGo.AddComponent<Shadow>();
        shadow.effectColor = new Color(0, 0, 0, 0.9f);
        shadow.effectDistance = new Vector2(2, -2);
    }
}

/// <summary>
/// The ISAE falls apart. Ende 2: it decays after its broken shot, parts drift off. Ende 3: an energy explosion
/// leaves a wreck that only the roots hold together. Glows and tethers go out, rings stop, focus cannons drift.
/// </summary>
public class Wreck : MonoBehaviour
{
    private static readonly string[] GlowNames = { "ISAE_Linsenglut", "ISAE_Muendungsglut", "ISAE_Entzugsstrahl", "Sondenglut", "Emitterglut_", "Kopplerlicht_", "Fokusstrahl_" };

    private float _start;
    private readonly List<(Material material, Color color)> _glows = new();
    private readonly List<(Light light, float intensity)> _lights = new();
    private readonly List<(Transform part, Vector3 velocity, Vector3 spin, float until)> _drift = new();

    public static Wreck Begin(bool scatter)
    {
        var pivot = GameProps.Pivot;
        if (pivot == null) return null;
        var w = pivot.gameObject.GetComponent<Wreck>() ?? pivot.gameObject.AddComponent<Wreck>();
        w._start = Time.time;
        foreach (var spinner in pivot.GetComponentsInChildren<Spinner>(true)) spinner.enabled = false;
        var orbit = pivot.GetComponentInChildren<FocusOrbit>(true);
        if (orbit != null) orbit.enabled = false;
        var tethers = pivot.GetComponent<Tethers>();
        if (tethers != null) tethers.enabled = false;
        foreach (var t in pivot.GetComponentsInChildren<Transform>(true))
        {
            if (t.name.StartsWith("Energieleitung_")) t.gameObject.SetActive(false);
            foreach (var g in GlowNames)
                if (t.name.StartsWith(g)) t.gameObject.SetActive(false);
        }
        var seen = new HashSet<Material>();
        foreach (var r in pivot.GetComponentsInChildren<MeshRenderer>(true))
            foreach (var m in r.sharedMaterials)
                if (m != null && (m.name.Contains("VesselGlut") || m.name.Contains("VesselLeuchten")) && seen.Add(m))
                    w._glows.Add((m, m.color));
        foreach (var l in pivot.GetComponentsInChildren<Light>(true))
            if (l.name.StartsWith("Licht_") && l.name != "Licht_Pulskern") w._lights.Add((l, l.intensity));

        var rnd = new System.Random(scatter ? 11 : 5);
        float R() => (float)rnd.NextDouble() - 0.5f;
        var rings = pivot.Find("ISAE_Laufringe");
        if (rings != null)
            w._drift.Add(scatter
                ? (rings, new Vector3(R(), 1f, R()) * 4f, new Vector3(R(), R(), R()) * 6f, 60f)
                : (rings, Vector3.zero, new Vector3(3f, 0f, 2f), 2.5f));
        foreach (var focus in GameProps.FocusCannons)
        {
            if (focus == null) continue;
            var outward = Vector3.ProjectOnPlane(focus.localPosition, Vector3.up).normalized;
            w._drift.Add((focus, outward * (scatter ? 3f : 1.5f), new Vector3(R(), R(), R()) * (scatter ? 3f : 1.2f), scatter ? 60f : 25f));
        }
        return w;
    }

    public void Update()
    {
        var since = Time.time - _start;
        var k = Mathf.Clamp01(since / 4f);
        foreach (var (m, c) in _glows)
            if (m != null) m.color = Color.Lerp(c, new Color(c.r * 0.05f, c.g * 0.05f, c.b * 0.05f, c.a), k);
        foreach (var (l, i) in _lights)
            if (l != null) l.intensity = i * (1f - k);
        foreach (var (part, velocity, spin, until) in _drift)
        {
            if (part == null || since > until) continue;
            // nothing moves under the feet of the player
            if (!GameProps.PlayerFar(part, 250f)) continue;
            part.localPosition += velocity * Time.deltaTime;
            part.Rotate(spin * Time.deltaTime, Space.Self);
        }
    }
}
