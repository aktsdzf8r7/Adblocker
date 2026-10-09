using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

namespace ZekiISAE;

/// <summary>
/// The end of the universe, as a cutscene. Replaces the supernova while the ISAE is still running:
///
///   0 .. D       Energy streams flow from the sun into the main cannon and the three focus cannons.
///                The sun shrinks, turns red, then violet-white. Subtitles tell what happens.
///   D-10 .. D    Collapse: the camera turns to the sun, the vanilla collapse particles and sound play.
///   D            The sun goes out with a flash.
///   D+1.5        The main cannon fires the interstellar probe along its barrel; the camera follows it.
///   D+7 .. D+14  Darkness. The eyes close.
///   D+14 .. D+26 Epilogue on black: where the probe goes. Then the New Horizons game over shows
///                "Das Universum endet, aber du endest vor ihm..." (addon-manifest.json).
///
/// D is the "drainSeconds" setting. With "cinematic" off the camera stays free, everything else still happens.
/// </summary>
public class Finale : MonoBehaviour
{
    public static bool Running;
    public SunController Sun;

    private const float CollapseLength = 10f;
    private const float FocusStreamHeight = 4f; // the energy streams end a few metres above the launch platform

    private float _start, _d;
    private float _startScale, _currentScale, _startRadius, _startSunLight, _startAmbientLight, _startLocalAmbient;
    private Color _startColor;
    private Material _baseSurface;
    private readonly List<(DistantSunController sun, Vector3 scale, float light)> _distant = new();
    private readonly List<(LineRenderer line, Transform body, float height)> _streams = new();
    private Cinema _cinema;
    private PlayerLockOnTargeting _lockOn;
    private Material _lineMaterial;

    private bool _collapseStarted, _sunGone, _fired, _darkness, _eyesClosed, _ended;
    private GameObject _probe;
    private float _probeSpeed;
    private Vector3 _probeDirection = Vector3.up;
    private LineRenderer _shotBeam;
    private float _shotTime;
    private int _nextLine;

    private (float at, string text, float duration)[] _lines;
    private (float at, string text, float duration)[] _epilogue;
    private int _nextCard;

    public void Start()
    {
        Running = true;
        _start = Time.time;
        _d = ZekiISAE.Instance.DrainSeconds;
        _startScale = Sun._scale > 0f ? Sun._scale : 1f;
        _currentScale = _startScale;
        _startRadius = Sun.GetSurfaceRadius();
        var light = Sun._sunLight;
        if (light != null)
        {
            _startSunLight = light._sunBaseIntensity;
            _startAmbientLight = light._ambientBaseIntensity;
            _startColor = light._sunBaseColor;
        }
        if (Sun._ambientLight != null) _startLocalAmbient = Sun._ambientLight.intensity;
        if (Sun._surfaceMaterial != null) _baseSurface = new Material(Sun._surfaceMaterial);
        foreach (var d in FindObjectsOfType<DistantSunController>())
        {
            if (d._model != null) _distant.Add((d, d._model.localScale, d._light != null ? d._light.intensity : 0f));
        }

        _lines = new[]
        {
            (0.5f, "Die Aussendungseinheit erwacht.", 4.5f),
            (_d * 0.13f, "281 042 Jahre hat sie auf diesen Augenblick gewartet.", 5f),
            (_d * 0.28f, "Sie trinkt das Licht der Sonne.", 4.5f),
            (_d * 0.43f, "Alpha. Beta. Gamma. Das Dreieck schließt sich.", 5f),
            (_d * 0.58f, "Keine Supernova. Kein Projekt. Keine Erinnerung, die zurückkehrt.", 5.5f),
            (_d * 0.74f, "Sedum wollte die Clans warnen. Linum wollte uns alle retten.", 5.5f),
            (_d - CollapseLength + 1f, "Die Sonne verlischt.", 4.5f),
            (_d + 2f, "Ein einziger Schuss. Eine Botschaft an Clans, die längst vergangen sind.", 4.5f),
            (_d + 7f, "Niemand wird sie je empfangen.", 3.8f),
        };
        _epilogue = new[]
        {
            (_d + 14.5f, "Die Sonde fliegt.", 3.2f),
            (_d + 18f, "Zehntausend Jahre. Hunderttausend.", 3.2f),
            (_d + 21.5f, "Sie erreicht einen Stern, an dem niemand mehr wartet.", 4f),
        };

        _lineMaterial = new Material(Shader.Find("Sprites/Default") ?? Shader.Find("Standard"));
        // vertex colours of lines are clamped to 1; the material colour pushes them into the bloom range
        _lineMaterial.color = new Color(2.4f, 2.4f, 2.4f, 1f);
        BuildStreams();
        _cinema = Cinema.Create();
        _cinema.Bars(true);
        _lockOn = Locator.GetPlayerTransform() != null ? Locator.GetPlayerTransform().GetComponent<PlayerLockOnTargeting>() : null;
        if (_lockOn == null) _lockOn = FindObjectOfType<PlayerLockOnTargeting>();

        DialogueConditionManager.SharedInstance.SetConditionState(ZekiISAE.DrainActive, true);
        ZekiISAE.Notify("DIE AUSSENDUNGSEINHEIT ENTZIEHT DER SONNE IHRE ENERGIE", 8f);
    }

    public void OnDestroy()
    {
        Running = false;
        if (_cinema != null) Destroy(_cinema.gameObject);
    }

    public void Update()
    {
        if (_ended) return;
        var t = Time.time - _start;
        var dm = Locator.GetDeathManager();
        if (dm != null && (dm.IsPlayerDying() || dm.IsPlayerDead()) && !_eyesClosed)
        {
            // the player died some other way; the loop ends normally from here
            _ended = true;
            _cinema.Bars(false);
            return;
        }

        while (_nextLine < _lines.Length && t >= _lines[_nextLine].at)
        {
            _cinema.Say(_lines[_nextLine].text, _lines[_nextLine].duration);
            _nextLine++;
        }

        if (!_sunGone) UpdateSun(Mathf.Clamp01(t / _d));
        UpdateStreams(t);

        if (!_collapseStarted && t >= _d - CollapseLength) StartCollapse();
        if (!_sunGone && t >= _d) SunGoesOut();
        if (!_fired && t >= _d + 1.5f) Fire();
        if (_fired) UpdateShot();
        if (!_darkness && t >= _d + 7f) _darkness = true;
        if (_darkness) DimEverything();
        if (!_eyesClosed && t >= _d + 11f)
        {
            _eyesClosed = true;
            _cinema.Bars(false);
            _cinema.Black(1f, 3f);
            var effects = FindObjectOfType<PlayerCameraEffectController>();
            if (effects != null) effects.CloseEyes(3f);
        }
        while (_nextCard < _epilogue.Length && t >= _epilogue[_nextCard].at)
        {
            _cinema.Card(_epilogue[_nextCard].text, _epilogue[_nextCard].duration);
            _nextCard++;
        }
        if (t >= _d + 26f) EndOfEverything();
    }

    // ------------------------------------------------------------------------------------------ the sun
    private void UpdateSun(float k)
    {
        var s = k * k * (3f - 2f * k);
        var remaining = 1f - s;
        _currentScale = Mathf.Max(_startScale * remaining, 0.002f);
        Sun.UpdateScale(_currentScale);

        var red = new Color(1f, 0.32f, 0.16f);
        var violet = new Color(0.78f, 0.62f, 1f);
        var color = k < 0.7f ? Color.Lerp(_startColor, red, k / 0.7f) : Color.Lerp(red, violet, (k - 0.7f) / 0.3f);
        var light = Sun._sunLight;
        if (light != null)
        {
            var intensity = Mathf.Pow(remaining, 0.7f);
            light._sunBaseIntensity = _startSunLight * intensity;
            light._ambientBaseIntensity = _startAmbientLight * intensity;
            light.sunIntensity = _startSunLight * intensity;
            light.ambientIntensity = _startAmbientLight * intensity;
            light._sunBaseColor = color;
            light.sunColor = color;
        }
        if (Sun._ambientLight != null) Sun._ambientLight.intensity = _startLocalAmbient * remaining;

        // the same surface materials the vanilla collapse uses
        var surface = Sun._surfaceMaterial;
        if (surface != null && _baseSurface != null)
        {
            if (k < 0.8f) LerpMaterial(surface, _baseSurface, Sun._collapseStartSurfaceMaterial, k / 0.8f);
            else LerpMaterial(surface, Sun._collapseStartSurfaceMaterial, Sun._collapseEndSurfaceMaterial, (k - 0.8f) / 0.2f);
        }

        foreach (var (d, scale, intensity) in _distant)
        {
            if (d == null) continue;
            d._model.localScale = scale * Mathf.Max(remaining, 0.002f);
            if (d._light != null) d._light.intensity = intensity * remaining;
        }
    }

    private static void LerpMaterial(Material target, Material a, Material b, float k)
    {
        if (a == null || b == null || a.shader != target.shader || b.shader != target.shader) return;
        target.Lerp(a, b, Mathf.Clamp01(k));
    }

    private void StartCollapse()
    {
        _collapseStarted = true;
        if (Sun._collapseParticles != null)
            foreach (var ps in Sun._collapseParticles)
                if (ps != null) ps.Play();
        PlayOneShot(AudioType.Sun_Collapse);
        if (ZekiISAE.Instance.Cinematic)
        {
            OWInput.ChangeInputMode(InputMode.None);
            if (_lockOn != null && Locator.GetSunTransform() != null) _lockOn.LockOn(Locator.GetSunTransform(), 2f, false, 1f);
        }
    }

    private void SunGoesOut()
    {
        _sunGone = true;
        Sun.UpdateScale(0.002f);
        Sun.SetRenderingEnabled(false);
        if (Sun._sunLight != null)
        {
            Sun._sunLight._sunBaseIntensity = 0f;
            Sun._sunLight.sunIntensity = 0f;
        }
        foreach (var (d, _, _) in _distant)
        {
            if (d == null) continue;
            d._model.gameObject.SetActive(false);
            if (d._light != null) d._light.intensity = 0f;
        }
        PlayOneShot(AudioType.SingularityCollapse);
        _cinema.Flash(0.9f);
        ZekiISAE.Notify("DIE SONNE IST ERLOSCHEN", 5f);
    }

    // ------------------------------------------------------------------------------------------ energy streams
    private void BuildStreams()
    {
        var nh = ZekiISAE.Instance.NewHorizons;
        var isae = nh.GetPlanet(ZekiISAE.IsaeName);
        if (isae != null) AddStream(isae.transform, 0f, 70f); // into the glowing core of the hub
        foreach (var name in GameProps.FocusNames)
        {
            var body = nh.GetPlanet(name);
            if (body != null) AddStream(body.transform, FocusStreamHeight, 30f);
        }
    }

    private void AddStream(Transform body, float height, float width)
    {
        var go = new GameObject("Energiestrom_" + body.name);
        var line = go.AddComponent<LineRenderer>();
        line.useWorldSpace = true;
        line.positionCount = 32;
        line.sharedMaterial = _lineMaterial;
        line.widthMultiplier = width;
        line.widthCurve = new AnimationCurve(new Keyframe(0f, 1f), new Keyframe(0.7f, 0.35f), new Keyframe(1f, 0.12f));
        line.colorGradient = Gradient(new Color(1.6f, 0.7f, 0.3f, 0f), new Color(1.8f, 1.2f, 0.7f, 0.8f), new Color(1.2f, 1.8f, 2.4f, 1f));
        line.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
        line.receiveShadows = false;
        _streams.Add((line, body, height));
    }

    private void UpdateStreams(float t)
    {
        var sun = Locator.GetSunTransform();
        var fade = _sunGone ? Mathf.Clamp01(1f - (Time.time - _start - _d) / 1.2f) : Mathf.Clamp01(t / 3f);
        foreach (var (line, body, height) in _streams)
        {
            if (line == null) continue;
            if (sun == null || body == null || fade <= 0f)
            {
                line.enabled = false;
                continue;
            }
            line.enabled = true;
            var target = body.TransformPoint(Vector3.up * height);
            var dir = (target - sun.position).normalized;
            var radius = _sunGone ? 0f : _startRadius * _currentScale / _startScale;
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
            var charge = Mathf.Clamp01(t / _d);
            line.widthMultiplier = Mathf.Lerp(0.4f, 1.3f, charge) * (1f + 0.25f * Mathf.Sin(t * 9f)) * fade * (body.name.Contains("Fokus") ? 30f : 70f);
        }
    }

    // ------------------------------------------------------------------------------------------ the shot
    private void Fire()
    {
        _fired = true;
        _shotTime = Time.time;
        DialogueConditionManager.SharedInstance.SetConditionState(ZekiISAE.DrainActive, false);
        PlayOneShot(AudioType.NomaiGravityCannonActivate);
        PlayOneShot(AudioType.NomaiVesselPowerUp);

        if (GameProps.Isae == null) return;
        var muzzle = GameProps.MuzzleWorld();
        var axis = GameProps.AxisWorld();

        var beamGo = new GameObject("ISAE_Schuss");
        _shotBeam = beamGo.AddComponent<LineRenderer>();
        _shotBeam.useWorldSpace = true;
        _shotBeam.positionCount = 2;
        _shotBeam.SetPosition(0, muzzle);
        _shotBeam.SetPosition(1, muzzle + axis * 90000f);
        _shotBeam.sharedMaterial = _lineMaterial;
        _shotBeam.widthMultiplier = 40f;
        _shotBeam.colorGradient = Gradient(new Color(2.5f, 2.5f, 3f, 1f), new Color(1.4f, 2f, 3f, 0.9f), new Color(1f, 1.6f, 3f, 0f));
        _shotBeam.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;

        // the copy of the real Nomai probe that waited in the launch module's cradle; it leaves through the barrel
        _probe = GameProps.Probe != null ? GameProps.Probe : new GameObject("Interstellare_Sonde");
        _probe.transform.SetParent(null, true);
        _probe.SetActive(true);
        _probe.transform.position = muzzle;
        _probe.transform.rotation = Quaternion.FromToRotation(GameProps.ProbeAxis, axis);
        _probe.transform.localScale = Vector3.one * 6f;
        _probeDirection = axis;
        var trail = _probe.AddComponent<TrailRenderer>();
        trail.sharedMaterial = _lineMaterial;
        trail.time = 4f;
        trail.minVertexDistance = 40f;
        trail.widthMultiplier = 18f;
        trail.widthCurve = new AnimationCurve(new Keyframe(0f, 1f), new Keyframe(1f, 0f));
        trail.colorGradient = Gradient(new Color(2f, 2.4f, 3f, 1f), new Color(0.8f, 1.4f, 2.4f, 0.6f), new Color(0.4f, 0.8f, 2f, 0f));
        _probeSpeed = 250f;

        _cinema.Flash(0.5f);
        if (ZekiISAE.Instance.Cinematic && _lockOn != null)
        {
            _lockOn.BreakLock();
            _lockOn.LockOn(_probe.transform, 3f, false, 1f);
        }
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

    // ------------------------------------------------------------------------------------------ the end
    private void DimEverything()
    {
        var light = Sun._sunLight;
        if (light == null) return;
        light._ambientBaseIntensity = Mathf.MoveTowards(light._ambientBaseIntensity, 0f, Time.deltaTime * 0.3f);
        light.ambientIntensity = light._ambientBaseIntensity;
    }

    private void EndOfEverything()
    {
        _ended = true;
        if (_lockOn != null) _lockOn.BreakLock();
        _cinema.Bars(false);
        // New Horizons shows the game over text of addon-manifest.json when the player dies while this is set
        DialogueConditionManager.SharedInstance.SetConditionState(ZekiISAE.UniverseEnds, true);
        var death = Locator.GetDeathManager();
        if (death != null && !death.IsPlayerDying() && !death.IsPlayerDead())
        {
            death.KillPlayer(DeathType.Meditation);
        }
    }

    // ------------------------------------------------------------------------------------------ helpers
    private static void PlayOneShot(AudioType type)
    {
        var audio = Locator.GetPlayerAudioController();
        if (audio != null) audio.PlayOneShotInternal(type);
    }

    private static Gradient Gradient(Color a, Color b, Color c)
    {
        var g = new Gradient();
        g.SetKeys(
            new[] { new GradientColorKey(a, 0f), new GradientColorKey(b, 0.5f), new GradientColorKey(c, 1f) },
            new[] { new GradientAlphaKey(a.a, 0f), new GradientAlphaKey(b.a, 0.5f), new GradientAlphaKey(c.a, 1f) });
        return g;
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

    public void Bars(bool on) => _barsTarget = on ? 130f : 0f;

    public void Say(string text, float duration)
    {
        _text.text = text;
        _textStart = Time.time;
        _textDuration = duration;
    }

    public void Flash(float strength) => _flashAlpha = Mathf.Max(_flashAlpha, strength);

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
        _flash.color = new Color(1f, 0.97f, 0.92f, _flashAlpha);
    }
}
