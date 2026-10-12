using System;
using System.Collections.Generic;
using UnityEngine;

namespace ZekiISAE;

/// <summary>The three endings of the mod. 0 = the vanilla supernova.</summary>
public enum EndingKind
{
    Vanilla = 0,
    /// <summary>Ende 1 "Aussendung": the armed ISAE drains the sun and fires its probe (Finale).</summary>
    Aussendung = 1,
    /// <summary>Ende 2 "Riss": the armed, rooted ISAE fires a broken seed into the sun and reality breaks (RiftEnding).</summary>
    Riss = 2,
    /// <summary>Ende 3 "Verwurzelt": the switched-off, rooted ISAE explodes into a wreck, later its probe plants a seed in the sun (RootEnding).</summary>
    Verwurzelt = 3,
}

/// <summary>
/// Shared machinery of the endings: the frozen or dying sun, subtitles and cards (Cinema), camera lock-on,
/// shaking, lines, and the final game over. An ending is added to the sun when the loop ends
/// (SunPatches.OnTriggerSupernova); while one exists the vanilla sun animation does not run.
/// </summary>
public abstract class Ending : MonoBehaviour
{
    public static Ending Current;
    public static bool Running => Current != null;

    public SunController Sun;
    public abstract EndingKind Kind { get; }

    protected Cinema Cinema;
    protected PlayerLockOnTargeting LockOn;
    protected Material LineMaterial;
    protected float StartTime;
    protected bool Ended;
    /// <summary>Set once the ending kills the player itself; before that a death means the loop just ends.</summary>
    protected bool Killing;

    protected float StartScale = 1f, CurrentScale = 1f, StartRadius, StartSunLight, StartAmbientLight, StartLocalAmbient;
    protected Color StartColor = Color.white;
    protected Material BaseSurface;
    protected readonly List<(DistantSunController sun, Vector3 scale, float light)> Distant = new();

    private (float at, string text, float duration)[] _lines = Array.Empty<(float, string, float)>();
    private (float at, string text, float duration)[] _cards = Array.Empty<(float, string, float)>();
    private int _nextLine, _nextCard;
    private bool _inputLocked;

    protected float T => Time.time - StartTime;
    protected static bool Cinematic => ZekiISAE.Instance == null || ZekiISAE.Instance.Cinematic;

    public void Start()
    {
        Current = this;
        StartTime = Time.time;
        CaptureSun();
        LineMaterial = new Material(Shader.Find("Sprites/Default") ?? Shader.Find("Standard"));
        // vertex colours of lines are clamped to 1; the material colour pushes them into the bloom range
        LineMaterial.color = new Color(2.4f, 2.4f, 2.4f, 1f);
        Cinema = Cinema.Create();
        var player = Locator.GetPlayerTransform();
        LockOn = player != null ? player.GetComponent<PlayerLockOnTargeting>() : null;
        if (LockOn == null) LockOn = FindObjectOfType<PlayerLockOnTargeting>();
        ZekiISAE.Instance?.Log($"Ende: {Kind}");
        Begin();
    }

    public void OnDestroy()
    {
        if (Current == this) Current = null;
        if (Cinema != null) Destroy(Cinema.gameObject);
    }

    protected abstract void Begin();
    protected abstract void Tick(float t);

    public void Update()
    {
        if (Ended) return;
        var dm = Locator.GetDeathManager();
        if (!Killing && dm != null && (dm.IsPlayerDying() || dm.IsPlayerDead()))
        {
            // the player died some other way; the loop ends normally from here
            Ended = true;
            Cinema.Bars(false);
            UnlockInput();
            return;
        }
        var t = T;
        while (_nextLine < _lines.Length && t >= _lines[_nextLine].at)
        {
            Cinema.Say(_lines[_nextLine].text, _lines[_nextLine].duration);
            _nextLine++;
        }
        while (_nextCard < _cards.Length && t >= _cards[_nextCard].at)
        {
            Cinema.Card(_cards[_nextCard].text, _cards[_nextCard].duration);
            _nextCard++;
        }
        Tick(t);
    }

    /// <summary>Subtitles at the given seconds after the start of the ending.</summary>
    protected void Lines(params (float at, string text, float duration)[] lines)
    {
        _lines = lines;
        _nextLine = 0;
        while (_nextLine < _lines.Length && _lines[_nextLine].at < T) _nextLine++;
    }

    /// <summary>Big centred lines on black at the given seconds after the start of the ending.</summary>
    protected void Cards(params (float at, string text, float duration)[] cards)
    {
        _cards = cards;
        _nextCard = 0;
        while (_nextCard < _cards.Length && _cards[_nextCard].at < T) _nextCard++;
    }

    // ------------------------------------------------------------------------------------------ the sun
    private void CaptureSun()
    {
        StartScale = Sun._scale > 0f ? Sun._scale : 1f;
        CurrentScale = StartScale;
        StartRadius = Sun.GetSurfaceRadius();
        var light = Sun._sunLight;
        if (light != null)
        {
            StartSunLight = light._sunBaseIntensity;
            StartAmbientLight = light._ambientBaseIntensity;
            StartColor = light._sunBaseColor;
        }
        if (Sun._ambientLight != null) StartLocalAmbient = Sun._ambientLight.intensity;
        if (Sun._surfaceMaterial != null) BaseSurface = new Material(Sun._surfaceMaterial);
        foreach (var d in FindObjectsOfType<DistantSunController>())
            if (d._model != null) Distant.Add((d, d._model.localScale, d._light != null ? d._light.intensity : 0f));
    }

    protected void SunScale(float factor)
    {
        CurrentScale = Mathf.Max(StartScale * factor, 0.002f);
        Sun.UpdateScale(CurrentScale);
    }

    protected float SunRadius => StartRadius * CurrentScale / StartScale;

    protected void SunLight(float factor, Color color)
    {
        var light = Sun._sunLight;
        if (light != null)
        {
            light._sunBaseIntensity = StartSunLight * factor;
            light._ambientBaseIntensity = StartAmbientLight * factor;
            light.sunIntensity = StartSunLight * factor;
            light.ambientIntensity = StartAmbientLight * factor;
            light._sunBaseColor = color;
            light.sunColor = color;
        }
        if (Sun._ambientLight != null) Sun._ambientLight.intensity = StartLocalAmbient * factor;
    }

    /// <summary>0 = the living surface, 0.8 = the vanilla collapse start, 1 = the collapse end.</summary>
    protected void SunSurface(float k)
    {
        var surface = Sun._surfaceMaterial;
        if (surface == null || BaseSurface == null) return;
        if (k < 0.8f) LerpMaterial(surface, BaseSurface, Sun._collapseStartSurfaceMaterial, k / 0.8f);
        else LerpMaterial(surface, Sun._collapseStartSurfaceMaterial, Sun._collapseEndSurfaceMaterial, (k - 0.8f) / 0.2f);
    }

    private static void LerpMaterial(Material target, Material a, Material b, float k)
    {
        if (a == null || b == null || a.shader != target.shader || b.shader != target.shader) return;
        target.Lerp(a, b, Mathf.Clamp01(k));
    }

    protected void DistantSun(float factor)
    {
        foreach (var (d, scale, intensity) in Distant)
        {
            if (d == null) continue;
            d._model.localScale = scale * Mathf.Max(factor, 0.002f);
            if (d._light != null) d._light.intensity = intensity * factor;
        }
    }

    protected void CollapseParticles()
    {
        if (Sun._collapseParticles == null) return;
        foreach (var ps in Sun._collapseParticles)
            if (ps != null) ps.Play();
    }

    /// <summary>The sun is gone: no surface, no light, no far-away picture.</summary>
    protected void SunOut()
    {
        SunScale(0f);
        Sun.SetRenderingEnabled(false);
        if (Sun._sunLight != null)
        {
            Sun._sunLight._sunBaseIntensity = 0f;
            Sun._sunLight.sunIntensity = 0f;
        }
        foreach (var (d, _, _) in Distant)
        {
            if (d == null) continue;
            d._model.gameObject.SetActive(false);
            if (d._light != null) d._light.intensity = 0f;
        }
    }

    /// <summary>The ambient light fades after the sun is gone.</summary>
    protected void DimAmbient(float speed = 0.3f)
    {
        var light = Sun._sunLight;
        if (light == null) return;
        light._ambientBaseIntensity = Mathf.MoveTowards(light._ambientBaseIntensity, 0f, Time.deltaTime * speed);
        light.ambientIntensity = light._ambientBaseIntensity;
    }

    // ------------------------------------------------------------------------------------------ camera
    protected void Look(Transform target, float easing = 2f)
    {
        if (!Cinematic || LockOn == null || target == null) return;
        LockOn.BreakLock();
        LockOn.LockOn(target, easing, false, 1f);
    }

    protected void FreeLook()
    {
        if (LockOn != null) LockOn.BreakLock();
    }

    protected void LockInput()
    {
        if (!Cinematic || _inputLocked) return;
        _inputLocked = true;
        OWInput.ChangeInputMode(InputMode.None);
    }

    protected void UnlockInput()
    {
        if (!_inputLocked) return;
        _inputLocked = false;
        OWInput.RestorePreviousInputs();
    }

    /// <summary>An empty transform that follows parent (for lock-on targets and effects).</summary>
    protected static Transform Marker(string name, Transform parent, Vector3 world)
    {
        var t = new GameObject(name).transform;
        t.SetParent(parent, false);
        t.position = world;
        return t;
    }

    // ------------------------------------------------------------------------------------------ the end
    /// <summary>New Horizons shows the game over of addon-manifest.json whose condition is set when the player dies.</summary>
    protected void EndWith(string condition, DeathType death)
    {
        Ended = true;
        Killing = true;
        FreeLook();
        Cinema.Bars(false);
        DialogueConditionManager.SharedInstance.SetConditionState(condition, true);
        var dm = Locator.GetDeathManager();
        if (dm != null && !dm.IsPlayerDying() && !dm.IsPlayerDead()) dm.KillPlayer(death);
    }

    // ------------------------------------------------------------------------------------------ helpers
    public static void PlayOneShot(AudioType type)
    {
        var audio = Locator.GetPlayerAudioController();
        if (audio != null) audio.PlayOneShotInternal(type);
    }

    public static Gradient Gradient(Color a, Color b, Color c)
    {
        var g = new Gradient();
        g.SetKeys(
            new[] { new GradientColorKey(a, 0f), new GradientColorKey(b, 0.5f), new GradientColorKey(c, 1f) },
            new[] { new GradientAlphaKey(a.a, 0f), new GradientAlphaKey(b.a, 0.5f), new GradientAlphaKey(c.a, 1f) });
        return g;
    }

    protected TrailRenderer Trail(GameObject go, float width, Color head, Color tail)
    {
        var trail = go.AddComponent<TrailRenderer>();
        trail.sharedMaterial = LineMaterial;
        trail.time = 3.5f;
        trail.minVertexDistance = 20f;
        trail.widthMultiplier = width;
        trail.widthCurve = new AnimationCurve(new Keyframe(0f, 1f), new Keyframe(1f, 0f));
        trail.colorGradient = Gradient(head, Color.Lerp(head, tail, 0.5f), new Color(tail.r, tail.g, tail.b, 0f));
        trail.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
        return trail;
    }

    protected static float Smooth(float k)
    {
        k = Mathf.Clamp01(k);
        return k * k * (3f - 2f * k);
    }
}

/// <summary>
/// Something flying from the cannon into the sun. Lives in the frame of the sun (the game moves the world around
/// the player, a free object would be left behind) and arrives after the given seconds.
/// </summary>
public class SunShot : MonoBehaviour
{
    public Vector3 From;           // in the sun's frame
    public float Duration = 9f;
    public float Arrival;          // radius at which it counts as arrived (the sun's surface)
    public Action Arrived;
    private float _start;
    private bool _done;

    public static SunShot Launch(GameObject go, Transform sun, Vector3 fromWorld, float duration, float surface, Action arrived)
    {
        go.transform.SetParent(sun, true);
        var shot = go.AddComponent<SunShot>();
        shot.From = sun.InverseTransformPoint(fromWorld);
        shot.Duration = duration;
        shot.Arrival = surface / Mathf.Max(0.0001f, sun.lossyScale.x);
        shot.Arrived = arrived;
        go.transform.localPosition = shot.From;
        return shot;
    }

    public void Start() => _start = Time.time;

    public void Update()
    {
        if (_done) return;
        var k = Mathf.Clamp01((Time.time - _start) / Duration);
        // slow out of the muzzle, then faster and faster into the sun
        var e = k * k * (0.35f + 0.65f * k);
        transform.localPosition = Vector3.Lerp(From, Vector3.zero, e);
        if (k >= 1f || transform.localPosition.magnitude <= Arrival)
        {
            _done = true;
            Arrived?.Invoke();
        }
    }
}

/// <summary>Shakes the player camera a little (position and rotation) while something requests it this frame.</summary>
public class Shaker : MonoBehaviour
{
    private static Shaker _instance;
    private static float _requested;
    private float _amplitude;
    private Vector3 _lastOffset, _lastSet;
    private Quaternion _lastRotOffset = Quaternion.identity, _lastRotSet = Quaternion.identity;
    private Transform _camera;

    /// <summary>Shake with this strength (about 0..1) during the current frame.</summary>
    public static void Request(float strength)
    {
        if (_instance == null) _instance = new GameObject("ZekiISAE_Beben").AddComponent<Shaker>();
        _requested = Mathf.Max(_requested, strength);
    }

    public void LateUpdate()
    {
        var cam = Locator.GetPlayerCamera();
        var t = cam != null ? cam.transform : null;
        if (t != _camera)
        {
            _camera = t;
            _lastOffset = Vector3.zero;
            _lastRotOffset = Quaternion.identity;
        }
        _amplitude = Mathf.MoveTowards(_amplitude, _requested, Time.deltaTime * 3f);
        _requested = 0f;
        if (_camera == null) return;
        // take back last frame's offset, unless the camera controller has set the camera again since
        var basePos = _camera.localPosition == _lastSet ? _lastSet - _lastOffset : _camera.localPosition;
        var baseRot = _camera.localRotation == _lastRotSet ? _lastRotSet * Quaternion.Inverse(_lastRotOffset) : _camera.localRotation;
        if (_amplitude <= 0.001f)
        {
            _camera.localPosition = basePos;
            _camera.localRotation = baseRot;
            _lastOffset = Vector3.zero;
            _lastRotOffset = Quaternion.identity;
            _lastSet = basePos;
            _lastRotSet = baseRot;
            return;
        }
        var time = Time.time * 23f;
        _lastOffset = new Vector3(Mathf.PerlinNoise(time, 0.3f) - 0.5f, Mathf.PerlinNoise(0.7f, time) - 0.5f, 0f) * (0.12f * _amplitude);
        _lastRotOffset = Quaternion.Euler((Mathf.PerlinNoise(time, 4.1f) - 0.5f) * 2.4f * _amplitude, (Mathf.PerlinNoise(9.2f, time) - 0.5f) * 2.4f * _amplitude, 0f);
        _camera.localPosition = basePos + _lastOffset;
        _camera.localRotation = baseRot * _lastRotOffset;
        _lastSet = _camera.localPosition;
        _lastRotSet = _camera.localRotation;
    }
}

/// <summary>Jagged white-green cracks in space around a point, growing with Progress (Ende 2).</summary>
public class RealityCracks : MonoBehaviour
{
    public float Progress;
    private readonly List<(LineRenderer line, Vector3[] points, float appear)> _cracks = new();

    public static RealityCracks Create(Transform parent, Material material, float radius, int count, int seed)
    {
        var go = new GameObject("Realitaetsrisse");
        go.transform.SetParent(parent, false);
        var c = go.AddComponent<RealityCracks>();
        var rnd = new System.Random(seed);
        float R() => (float)rnd.NextDouble();
        for (var i = 0; i < count; i++)
        {
            var dir = new Vector3(R() - 0.5f, R() - 0.5f, R() - 0.5f).normalized;
            var start = dir * radius * (0.25f + 0.75f * R());
            var heading = Vector3.Cross(dir, new Vector3(R() - 0.5f, R() - 0.5f, R() - 0.5f)).normalized;
            var n = 10 + rnd.Next(10);
            var pts = new Vector3[n];
            var p = start;
            for (var k = 0; k < n; k++)
            {
                pts[k] = p;
                heading = (heading + new Vector3(R() - 0.5f, R() - 0.5f, R() - 0.5f) * 0.9f).normalized;
                p += heading * radius * (0.03f + 0.05f * R());
            }
            var lineGo = new GameObject("Riss_" + i);
            lineGo.transform.SetParent(go.transform, false);
            var line = lineGo.AddComponent<LineRenderer>();
            line.useWorldSpace = false;
            line.sharedMaterial = material;
            line.positionCount = 0;
            line.widthMultiplier = radius * (0.006f + 0.01f * R());
            line.colorGradient = Ending.Gradient(new Color(2.6f, 2.8f, 2.6f, 1f), new Color(1.4f, 2.8f, 1.6f, 0.9f), new Color(0.6f, 1.6f, 0.9f, 0.4f));
            line.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            c._cracks.Add((line, pts, i / (float)count * 0.85f));
        }
        return c;
    }

    public void Update()
    {
        foreach (var (line, pts, appear) in _cracks)
        {
            var k = Mathf.Clamp01((Progress - appear) / 0.15f);
            var n = Mathf.Clamp(Mathf.CeilToInt(k * pts.Length), 0, pts.Length);
            if (line.positionCount != n)
            {
                line.positionCount = n;
                for (var i = 0; i < n; i++) line.SetPosition(i, pts[i]);
            }
            line.enabled = n > 1 && UnityEngine.Random.value > 0.04f;
        }
    }
}

/// <summary>An expanding, fading glowing sphere with a light: the energy explosion of the ISAE core (Ende 3).</summary>
public class EnergyBurst : MonoBehaviour
{
    public float Radius = 400f, Duration = 3f;
    private float _start;
    private Material _material;
    private Light _light;

    public static EnergyBurst Create(Transform parent, Vector3 world, float radius, float duration, Color color)
    {
        var go = GameObject.CreatePrimitive(PrimitiveType.Sphere);
        go.name = "Energieexplosion";
        Destroy(go.GetComponent<Collider>());
        go.transform.SetParent(parent, false);
        go.transform.position = world;
        var b = go.AddComponent<EnergyBurst>();
        b.Radius = radius;
        b.Duration = duration;
        b._material = new Material(Shader.Find("Sprites/Default") ?? Shader.Find("Standard")) { color = color };
        go.GetComponent<MeshRenderer>().sharedMaterial = b._material;
        b._light = go.AddComponent<Light>();
        b._light.type = LightType.Point;
        b._light.color = color;
        b._light.range = radius * 6f;
        b._light.intensity = 6f;
        return b;
    }

    public void Start() => _start = Time.time;

    public void Update()
    {
        var k = Mathf.Clamp01((Time.time - _start) / Duration);
        var s = Radius * 2f * Mathf.Sqrt(k) / Mathf.Max(0.0001f, transform.parent != null ? transform.parent.lossyScale.x : 1f);
        transform.localScale = Vector3.one * Mathf.Max(0.01f, s);
        var c = _material.color;
        _material.color = new Color(c.r, c.g, c.b, (1f - k) * (1f - k));
        _light.intensity = 6f * (1f - k);
        if (k >= 1f) Destroy(gameObject);
    }
}
