using System.Collections.Generic;
using System.IO;
using UnityEngine;
using UnityEngine.UI;

namespace ZekiISAE;

/// <summary>
/// The end of the universe, as a cutscene. Replaces the supernova while the ISAE is still running:
///
///   0 .. D       Energy streams flow from the sun into the lens of the main cannon (which points at the sun)
///                and into the emitters of the three focus cannons.
///                The sun shrinks, turns red, then violet-white. Subtitles tell what happens.
///   D-10 .. D    Collapse: the camera turns to the sun, the vanilla collapse particles and sound play.
///   D            The sun goes out with a flash.
///   D+0.5        The cannon turns away from the dead sun, towards the stars; the camera watches its muzzle.
///   D+7          It fires the interstellar probe along its barrel; the camera follows the probe.
///   D+12 .. D+19 Darkness. The eyes close.
///   D+19 .. D+31 Epilogue on black: where the probe goes. Then the New Horizons game over shows
///                "Das Universum endet, aber du endest vor ihm..." (addon-manifest.json).
///
/// D is the "drainSeconds" setting. With "cinematic" off the camera stays free, everything else still happens.
/// This is Ende 1 "Aussendung"; Ende 2 and 3 are in RiftEnding.cs and RootEnding.cs.
/// </summary>
public class Finale : Ending
{
    private const float CollapseLength = 10f;

    public override EndingKind Kind => EndingKind.Aussendung;

    private float _d;
    private readonly List<(LineRenderer line, Transform anchor, Vector3 local, float width)> _streams = new();
    private Transform _muzzle;
    private bool _collapseStarted, _sunGone, _turning, _fired, _darkness, _eyesClosed;
    private GameObject _probe;
    private float _probeSpeed;
    private Vector3 _probeDirection = Vector3.up;
    private LineRenderer _shotBeam;
    private float _shotTime;

    protected override void Begin()
    {
        _d = ZekiISAE.Instance.DrainSeconds;
        Lines(
            (0.5f, "Die Aussendungseinheit erwacht.", 4.5f),
            (_d * 0.13f, "281 042 Jahre hat sie auf diesen Augenblick gewartet.", 5f),
            (_d * 0.28f, "Sie trinkt das Licht der Sonne.", 4.5f),
            (_d * 0.43f, "Alpha. Beta. Gamma. Das Dreieck schließt sich.", 5f),
            (_d * 0.58f, "Keine Supernova. Kein Projekt. Keine Erinnerung, die zurückkehrt.", 5.5f),
            (_d * 0.74f, "Sedum wollte die Clans warnen. Linum wollte uns alle retten.", 5.5f),
            (_d - CollapseLength + 1f, "Die Sonne verlischt.", 4.5f),
            (_d + 1f, "Die Kanone wendet sich von der toten Sonne ab. Zu den Sternen.", 5.5f),
            (_d + 7.5f, "Ein einziger Schuss. Eine Botschaft an Clans, die längst vergangen sind.", 4.5f),
            (_d + 12.5f, "Niemand wird sie je empfangen.", 3.8f));
        Cards(
            (_d + 20f, "Die Sonde fliegt.", 3.2f),
            (_d + 23.5f, "Zehntausend Jahre. Hunderttausend.", 3.2f),
            (_d + 27f, "Sie erreicht einen Stern, an dem niemand mehr wartet.", 4f));

        BuildStreams();
        Cinema.Bars(true);
        DialogueConditionManager.SharedInstance.SetConditionState(ZekiISAE.DrainActive, true);
        ZekiISAE.Notify("DIE AUSSENDUNGSEINHEIT ENTZIEHT DER SONNE IHRE ENERGIE", 8f);
    }

    protected override void Tick(float t)
    {
        if (!_sunGone) UpdateSun(Mathf.Clamp01(t / _d));
        UpdateStreams(t);

        if (!_collapseStarted && t >= _d - CollapseLength) StartCollapse();
        if (!_sunGone && t >= _d) SunGoesOut();
        if (!_turning && t >= _d + 0.5f) TurnAway();
        if (!_fired && t >= _d + 7f) Fire();
        if (_fired) UpdateShot();
        if (!_darkness && t >= _d + 12f) _darkness = true;
        if (_darkness) DimAmbient();
        if (!_eyesClosed && t >= _d + 16f)
        {
            _eyesClosed = true;
            Killing = true;
            Cinema.Bars(false);
            Cinema.Black(1f, 3f);
            var effects = FindObjectOfType<PlayerCameraEffectController>();
            if (effects != null) effects.CloseEyes(3f);
        }
        if (t >= _d + 31.5f) EndWith(ZekiISAE.UniverseEnds, DeathType.Meditation);
    }

    // ------------------------------------------------------------------------------------------ the sun
    private void UpdateSun(float k)
    {
        var s = Smooth(k);
        var remaining = 1f - s;
        SunScale(remaining);
        var red = new Color(1f, 0.32f, 0.16f);
        var violet = new Color(0.78f, 0.62f, 1f);
        var color = k < 0.7f ? Color.Lerp(StartColor, red, k / 0.7f) : Color.Lerp(red, violet, (k - 0.7f) / 0.3f);
        SunLight(Mathf.Pow(remaining, 0.7f), color);
        // the same surface materials the vanilla collapse uses
        SunSurface(k);
        DistantSun(remaining);
    }

    private void StartCollapse()
    {
        _collapseStarted = true;
        CollapseParticles();
        PlayOneShot(AudioType.Sun_Collapse);
        LockInput();
        Look(Locator.GetSunTransform());
    }

    private void SunGoesOut()
    {
        _sunGone = true;
        SunOut();
        PlayOneShot(AudioType.SingularityCollapse);
        Cinema.Flash(0.9f);
        ZekiISAE.Notify("DIE SONNE IST ERLOSCHEN", 5f);
    }

    // ------------------------------------------------------------------------------------------ energy streams
    private void BuildStreams()
    {
        if (GameProps.Pivot == null) return;
        AddStream(GameProps.Pivot, GameProps.LocalPoint("linse", Vector3.up * 770f), 80f);
        var emitter = GameProps.LocalPoint("fokus_emitter", Vector3.up * 113f);
        foreach (var focus in GameProps.FocusCannons) AddStream(focus, emitter, 32f);
        _muzzle = new GameObject("ISAE_Muendung_Kamera").transform;
        _muzzle.SetParent(GameProps.Pivot, false);
        _muzzle.localPosition = GameProps.LocalPoint("muendung", Vector3.up * 800f);
    }

    private void AddStream(Transform anchor, Vector3 local, float width)
    {
        var go = new GameObject("Energiestrom_" + anchor.name);
        var line = go.AddComponent<LineRenderer>();
        line.useWorldSpace = true;
        line.positionCount = 32;
        line.sharedMaterial = LineMaterial;
        line.widthMultiplier = width;
        line.widthCurve = new AnimationCurve(new Keyframe(0f, 1f), new Keyframe(0.7f, 0.35f), new Keyframe(1f, 0.12f));
        line.colorGradient = Gradient(new Color(1.6f, 0.7f, 0.3f, 0f), new Color(1.8f, 1.0f, 0.5f, 0.8f), new Color(2.4f, 0.9f, 0.4f, 1f));
        line.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
        line.receiveShadows = false;
        _streams.Add((line, anchor, local, width));
    }

    /// <summary>The sun is dead: the cannon turns its muzzle away from it, towards the stars.</summary>
    private void TurnAway()
    {
        _turning = true;
        var aim = SunAim.Instance;
        var sun = Locator.GetSunTransform();
        if (aim == null || sun == null) return;
        aim.Override = (aim.transform.position - sun.position).normalized;
        aim.DegreesPerSecond = 32f;
        PlayOneShot(AudioType.NomaiVesselPowerUp);
        Look(_muzzle, 2.5f);
    }

    private void UpdateStreams(float t)
    {
        var sun = Locator.GetSunTransform();
        var fade = _sunGone ? Mathf.Clamp01(1f - (t - _d) / 1.2f) : Mathf.Clamp01(t / 3f);
        StreamLines.Update(_streams, sun, _sunGone ? 0f : SunRadius, t, fade, Mathf.Clamp01(t / _d));
    }

    // ------------------------------------------------------------------------------------------ the shot
    private void Fire()
    {
        _fired = true;
        _shotTime = Time.time;
        DialogueConditionManager.SharedInstance.SetConditionState(ZekiISAE.DrainActive, false);
        PlayOneShot(AudioType.NomaiGravityCannonActivate);
        PlayOneShot(AudioType.NomaiVesselPowerUp);

        if (GameProps.Pivot == null) return;
        var muzzle = GameProps.Point("muendung");
        var axis = GameProps.AxisWorld();

        var beamGo = new GameObject("ISAE_Schuss");
        _shotBeam = beamGo.AddComponent<LineRenderer>();
        _shotBeam.useWorldSpace = true;
        _shotBeam.positionCount = 2;
        _shotBeam.SetPosition(0, muzzle);
        _shotBeam.SetPosition(1, muzzle + axis * 90000f);
        _shotBeam.sharedMaterial = LineMaterial;
        _shotBeam.widthMultiplier = 40f;
        _shotBeam.colorGradient = Gradient(new Color(2.5f, 2.5f, 3f, 1f), new Color(1.4f, 2f, 3f, 0.9f), new Color(1f, 1.6f, 3f, 0f));
        _shotBeam.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;

        // the copy of the real Nomai probe that waited in its cradle at the muzzle; it leaves along the barrel
        _probe = GameProps.Probe != null ? GameProps.Probe : new GameObject("Interstellare_Sonde");
        _probe.transform.SetParent(null, true);
        _probe.SetActive(true);
        _probe.transform.position = muzzle;
        _probe.transform.rotation = Quaternion.FromToRotation(GameProps.ProbeAxis, axis);
        _probe.transform.localScale = Vector3.one * 6f;
        _probeDirection = axis;
        Trail(_probe, 18f, new Color(2f, 2.4f, 3f, 1f), new Color(0.4f, 0.8f, 2f, 0f));
        _probeSpeed = 250f;

        Cinema.Flash(0.5f);
        Look(_probe.transform, 3f);
    }

    private void UpdateShot()
    {
        var since = Time.time - _shotTime;
        if (_shotBeam != null)
        {
            _shotBeam.widthMultiplier = 40f * Mathf.Clamp01(1f - since / 2.5f);
            if (since > 2.5f) Destroy(_shotBeam.gameObject);
        }
        if (_probe != null)
        {
            _probeSpeed = Mathf.Min(_probeSpeed * (1f + 1.4f * Time.deltaTime), 30000f);
            _probe.transform.position += _probeDirection * _probeSpeed * Time.deltaTime;
        }
    }
}

/// <summary>Wobbling energy lines from the sun's surface to points on the ISAE.</summary>
public static class StreamLines
{
    public static void Update(List<(LineRenderer line, Transform anchor, Vector3 local, float width)> streams, Transform sun, float radius,
                              float t, float fade, float charge)
    {
        foreach (var (line, anchor, local, width) in streams)
        {
            if (line == null) continue;
            if (sun == null || anchor == null || fade <= 0f)
            {
                line.enabled = false;
                continue;
            }
            line.enabled = true;
            var target = anchor.TransformPoint(local);
            var dir = (target - sun.position).normalized;
            var from = sun.position + dir * radius;
            var side = Vector3.Cross(dir, Vector3.up);
            if (side.sqrMagnitude < 0.01f) side = Vector3.Cross(dir, Vector3.right);
            side.Normalize();
            var lift = Vector3.Cross(dir, side);
            var length = Vector3.Distance(from, target);
            for (var i = 0; i < line.positionCount; i++)
            {
                var u = i / (float)(line.positionCount - 1);
                var wobble = Mathf.Sin(u * 18f - t * 6f) * Mathf.Sin(u * Mathf.PI) * length * 0.004f;
                var twist = Mathf.Cos(u * 13f - t * 4.3f) * Mathf.Sin(u * Mathf.PI) * length * 0.003f;
                line.SetPosition(i, Vector3.Lerp(from, target, u) + side * wobble + lift * twist);
            }
            line.widthMultiplier = Mathf.Lerp(0.4f, 1.3f, charge) * (1f + 0.25f * Mathf.Sin(t * 9f)) * fade * width;
        }
    }
}

/// <summary>Letterbox bars, subtitles and a white flash on top of the game.</summary>
public class Cinema : MonoBehaviour
{
    private RectTransform _top, _bottom;
    private Text _text;
    private CanvasGroup _textGroup;
    private Image _flash, _black;
    private Text _card;
    private CanvasGroup _cardGroup;
    private float _cardStart = -100f, _cardDuration;
    private float _blackTarget, _blackSpeed = 1f;
    private float _barsTarget, _bars;
    private float _textStart = -100f, _textDuration;
    private float _flashAlpha;
    private readonly List<RawImage> _cracks = new();
    private float _crackAlpha, _crackTarget;
    private Color _flashColor = new(1f, 0.97f, 0.92f);

    public static Cinema Create()
    {
        var go = new GameObject("ZekiISAE_Kino");
        var canvas = go.AddComponent<Canvas>();
        canvas.renderMode = RenderMode.ScreenSpaceOverlay;
        canvas.sortingOrder = 32000;
        var scaler = go.AddComponent<CanvasScaler>();
        scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
        scaler.referenceResolution = new Vector2(1920, 1080);
        scaler.matchWidthOrHeight = 0.5f;
        var c = go.AddComponent<Cinema>();

        c._black = Panel(go.transform, "Schwarz", new Vector2(0, 0), new Vector2(1, 1), new Color(0f, 0f, 0f, 0f));
        c.BuildCracks(go.transform);
        c._flash = Panel(go.transform, "Blitz", new Vector2(0, 0), new Vector2(1, 1), new Color(1f, 0.97f, 0.92f, 0f));
        c._top = Panel(go.transform, "Balken_oben", new Vector2(0, 1), new Vector2(1, 1), Color.black).rectTransform;
        c._top.pivot = new Vector2(0.5f, 1f);
        c._bottom = Panel(go.transform, "Balken_unten", new Vector2(0, 0), new Vector2(1, 0), Color.black).rectTransform;
        c._bottom.pivot = new Vector2(0.5f, 0f);

        var textGo = new GameObject("Untertitel", typeof(RectTransform));
        textGo.transform.SetParent(go.transform, false);
        var rt = (RectTransform)textGo.transform;
        rt.anchorMin = new Vector2(0.1f, 0f);
        rt.anchorMax = new Vector2(0.9f, 0f);
        rt.pivot = new Vector2(0.5f, 0f);
        rt.anchoredPosition = new Vector2(0, 150);
        rt.sizeDelta = new Vector2(0, 140);
        c._textGroup = textGo.AddComponent<CanvasGroup>();
        c._textGroup.alpha = 0f;
        c._text = textGo.AddComponent<Text>();
        c._text.font = GameFont();
        c._text.fontSize = 46;
        c._text.alignment = TextAnchor.MiddleCenter;
        c._text.color = new Color(1f, 0.86f, 0.72f);
        c._text.horizontalOverflow = HorizontalWrapMode.Wrap;
        var shadow = textGo.AddComponent<Shadow>();
        shadow.effectColor = new Color(0, 0, 0, 0.9f);
        shadow.effectDistance = new Vector2(2, -2);

        var cardGo = new GameObject("Epilog", typeof(RectTransform));
        cardGo.transform.SetParent(go.transform, false);
        var crt = (RectTransform)cardGo.transform;
        crt.anchorMin = new Vector2(0.15f, 0.35f);
        crt.anchorMax = new Vector2(0.85f, 0.65f);
        crt.offsetMin = crt.offsetMax = Vector2.zero;
        c._cardGroup = cardGo.AddComponent<CanvasGroup>();
        c._cardGroup.alpha = 0f;
        c._card = cardGo.AddComponent<Text>();
        c._card.font = c._text.font;
        c._card.fontSize = 60;
        c._card.alignment = TextAnchor.MiddleCenter;
        c._card.color = new Color(1f, 0.78f, 0.6f);
        c._card.horizontalOverflow = HorizontalWrapMode.Wrap;
        return c;
    }

    private static Image Panel(Transform parent, string name, Vector2 min, Vector2 max, Color color)
    {
        var go = new GameObject(name, typeof(RectTransform));
        go.transform.SetParent(parent, false);
        var rt = (RectTransform)go.transform;
        rt.anchorMin = min;
        rt.anchorMax = max;
        rt.offsetMin = Vector2.zero;
        rt.offsetMax = Vector2.zero;
        var image = go.AddComponent<Image>();
        image.color = color;
        image.raycastTarget = false;
        return image;
    }

    private static Font GameFont()
    {
        var gameOver = FindObjectOfType<GameOverController>();
        if (gameOver != null && gameOver._deathText != null && gameOver._deathText.font != null) return gameOver._deathText.font;
        return Resources.GetBuiltinResource<Font>("Arial.ttf");
    }

    /// <summary>Cracks in reality over the whole screen (assets/riss.png, three layers turned against each other).</summary>
    private void BuildCracks(Transform parent)
    {
        var mod = ZekiISAE.Instance;
        if (mod == null) return;
        var path = Path.Combine(mod.ModHelper.Manifest.ModFolderPath, "assets/riss.png");
        if (!File.Exists(path)) return;
        var tex = new Texture2D(2, 2, TextureFormat.RGBA32, false);
        if (!ImageConversion.LoadImage(tex, File.ReadAllBytes(path))) return;
        for (var i = 0; i < 3; i++)
        {
            var go = new GameObject("Risse_" + i, typeof(RectTransform));
            go.transform.SetParent(parent, false);
            var rt = (RectTransform)go.transform;
            rt.anchorMin = rt.anchorMax = new Vector2(0.5f, 0.5f);
            rt.sizeDelta = new Vector2(1500 + 500 * i, 1500 + 500 * i);
            rt.anchoredPosition = new Vector2((i - 1) * 380, (i % 2 == 0 ? 1 : -1) * 160);
            rt.localRotation = Quaternion.Euler(0, 0, 37 + 121 * i);
            var image = go.AddComponent<RawImage>();
            image.texture = tex;
            image.color = new Color(1f, 1f, 1f, 0f);
            image.raycastTarget = false;
            _cracks.Add(image);
        }
    }

    /// <summary>0 = no cracks, 1 = the screen is shattered.</summary>
    public void Cracks(float alpha) => _crackTarget = Mathf.Clamp01(alpha);

    /// <summary>A coloured flash (Flash uses warm white).</summary>
    public void Flash(float strength, Color color)
    {
        _flashColor = color;
        _flashAlpha = Mathf.Max(_flashAlpha, strength);
    }

    public void Bars(bool on) => _barsTarget = on ? 130f : 0f;

    public void Say(string text, float duration)
    {
        _text.text = text;
        _textStart = Time.time;
        _textDuration = duration;
    }

    public void Flash(float strength) => Flash(strength, new Color(1f, 0.97f, 0.92f));

    /// <summary>Fade a black screen in (or out) over the given seconds.</summary>
    public void Black(float alpha, float seconds)
    {
        _blackTarget = alpha;
        _blackSpeed = 1f / Mathf.Max(0.01f, seconds);
    }

    /// <summary>A big centred line for the epilogue.</summary>
    public void Card(string text, float duration)
    {
        _card.text = text;
        _cardStart = Time.time;
        _cardDuration = duration;
    }

    public void Update()
    {
        _bars = Mathf.MoveTowards(_bars, _barsTarget, Time.deltaTime * 90f);
        _top.sizeDelta = new Vector2(0, _bars);
        _bottom.sizeDelta = new Vector2(0, _bars);

        var t = Time.time - _textStart;
        _textGroup.alpha = t < 0f || t > _textDuration ? 0f : Mathf.Min(Mathf.Clamp01(t / 0.9f), Mathf.Clamp01((_textDuration - t) / 0.9f));

        var k = Time.time - _cardStart;
        _cardGroup.alpha = k < 0f || k > _cardDuration ? 0f : Mathf.Min(Mathf.Clamp01(k / 1.1f), Mathf.Clamp01((_cardDuration - k) / 1.1f));
        _black.color = new Color(0f, 0f, 0f, Mathf.MoveTowards(_black.color.a, _blackTarget, Time.deltaTime * _blackSpeed));

        _flashAlpha = Mathf.MoveTowards(_flashAlpha, 0f, Time.deltaTime * 0.8f);
        _flash.color = new Color(_flashColor.r, _flashColor.g, _flashColor.b, _flashAlpha);

        _crackAlpha = Mathf.MoveTowards(_crackAlpha, _crackTarget, Time.deltaTime * 0.5f);
        for (var i = 0; i < _cracks.Count; i++)
        {
            // each layer appears at its own strength and flickers a little
            var a = Mathf.Clamp01(_crackAlpha * 3f - i) * (0.85f + 0.15f * Mathf.PerlinNoise(Time.time * 9f, i));
            _cracks[i].color = new Color(1f, 1f, 1f, a);
        }
    }
}
