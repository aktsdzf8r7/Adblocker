using System.Collections.Generic;
using UnityEngine;

namespace ZekiISAE;

/// <summary>
/// Ende 2 "Riss": the ISAE is still armed, but the Samenkern lies in its Pulskern and roots hold it.
///
///   0 .. 16   The sun wants to die. The rooted cannon wakes up, turns to the sun and starts to drink it.
///   10 .. 16  It tries to fire: reality cracks around the weapon (cracks in space and on the screen).
///   16        It fires a broken baby seed instead of light, then decays: glows out, rings drift off.
///   ~26       The seed falls into the sun. Reality breaks.
///   +5 .. +16 Cards on black. Then the game over "Das Universum hätte noch lange gelebt, wenn du nicht wärst...".
/// </summary>
public class RiftEnding : Ending
{
    public override EndingKind Kind => EndingKind.Riss;

    private const float CrackStart = 10f, FireAt = 16f, Flight = 10f;

    private readonly List<(LineRenderer line, Transform anchor, Vector3 local, float width)> _streams = new();
    private Transform _muzzle;
    private RealityCracks _cracks;
    private GameObject _seed;
    private Light _seedLight;
    private bool _looked, _cracking, _fired, _arrived, _black, _sunGone;
    private float _arrivedAt = -1f, _nextFlash;

    protected override void Begin()
    {
        Lines(
            (0.5f, "Die Sonne will sterben. Die Aussendungseinheit erwacht – gefangen in Wurzeln.", 5f),
            (6f, "Der Pulskern rast. Ein Jahr in jeder Sekunde.", 4.5f),
            (11f, "Sie will schießen. Die Wirklichkeit um sie bekommt Risse.", 5f),
            (FireAt + 1f, "Statt Licht schießt sie einen kranken Samen.", 4.5f),
            (FireAt + 6f, "Hinter ihm zerfällt die Kanone.", 4f));
        Cinema.Bars(true);
        ZekiISAE.Notify("DIE VERWURZELTE AUSSENDUNGSEINHEIT ERWACHT", 6f);
        PlayOneShot(AudioType.NomaiVesselPowerUp);
        var aim = SunAim.Instance;
        if (aim != null) aim.DegreesPerSecond = 10f;
        if (GameProps.Pivot != null)
        {
            _muzzle = Marker("ISAE_Muendung_Kamera", GameProps.Pivot, GameProps.Point("muendung"));
            AddStream(GameProps.Pivot, GameProps.LocalPoint("linse", Vector3.up * 770f), 60f);
            var emitter = GameProps.LocalPoint("fokus_emitter", Vector3.up * 113f);
            foreach (var focus in GameProps.FocusCannons) AddStream(focus, emitter, 24f);
        }
        DialogueConditionManager.SharedInstance.SetConditionState(ZekiISAE.DrainActive, true);
    }

    private void AddStream(Transform anchor, Vector3 local, float width)
    {
        var line = new GameObject("Energiestrom_" + anchor.name).AddComponent<LineRenderer>();
        line.useWorldSpace = true;
        line.positionCount = 32;
        line.sharedMaterial = LineMaterial;
        line.widthCurve = new AnimationCurve(new Keyframe(0f, 1f), new Keyframe(0.7f, 0.35f), new Keyframe(1f, 0.12f));
        line.colorGradient = Gradient(new Color(1.6f, 0.7f, 0.3f, 0f), new Color(1.4f, 1.8f, 0.7f, 0.8f), new Color(0.9f, 2.4f, 1.0f, 1f));
        line.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
        _streams.Add((line, anchor, local, width));
    }

    protected override void Tick(float t)
    {
        var sun = Locator.GetSunTransform();
        var aim = SunAim.Instance;
        if (aim != null && sun != null && !_fired) aim.Override = (sun.position - aim.transform.position).normalized;
        if (!_looked && t > 0.5f)
        {
            _looked = true;
            LockInput();
            Look(_muzzle, 2.5f);
        }

        // the sun is drunk a little before the shot goes wrong
        if (!_sunGone)
        {
            var drain = Smooth(Mathf.Clamp01(t / (FireAt + Flight)));
            var flicker = _arrived ? Random.Range(0.1f, 1.4f) : 1f;
            SunScale(Mathf.Lerp(1f, 0.82f, drain));
            SunLight(Mathf.Lerp(1f, 0.6f, drain) * flicker, _arrived ? Color.Lerp(new Color(0.4f, 1f, 0.5f), Color.black, Random.value * 0.6f)
                                                                   : Color.Lerp(StartColor, new Color(1f, 0.5f, 0.3f), drain));
            SunSurface(drain * 0.6f);
            DistantSun(Mathf.Lerp(1f, 0.82f, drain));
        }
        var streamFade = _fired ? Mathf.Clamp01(1f - (t - FireAt) / 1.5f) : Mathf.Clamp01(t / 3f);
        StreamLines.Update(_streams, sun, SunRadius, t, streamFade, Mathf.Clamp01(t / FireAt));
        if (SeedSystem.Instance != null) SeedSystem.Instance.Instability = Mathf.Clamp01(t / FireAt);

        if (!_cracking && t >= CrackStart) StartCracks();
        if (_cracking)
        {
            var k = Mathf.Clamp01((t - CrackStart) / (FireAt + Flight - CrackStart));
            if (_cracks != null) _cracks.Progress = _arrived ? 1f : k;
            if (!_arrived) Cinema.Cracks(0.12f + 0.45f * k);
            Shaker.Request(_arrived ? 1f : 0.3f + 0.6f * k);
            if (Time.time >= _nextFlash)
            {
                _nextFlash = Time.time + Random.Range(0.6f, 2.2f) * (_arrived ? 0.4f : 1f);
                Cinema.Flash(Random.Range(0.15f, 0.45f), new Color(0.75f, 1f, 0.8f));
            }
        }
        if (!_fired && t >= FireAt) Fire(sun);
        if (_seed != null && !_arrived)
        {
            // the seed is broken: it twitches, flickers and spins
            _seed.transform.localScale = Vector3.one * Random.Range(0.85f, 1.2f) / Mathf.Max(0.0001f, sun != null ? sun.lossyScale.x : 1f);
            _seed.transform.Rotate(new Vector3(70f, 130f, 40f) * Time.deltaTime, Space.Self);
            if (_seedLight != null) _seedLight.color = Random.value > 0.85f ? new Color(1f, 0.3f, 0.3f) : new Color(0.5f, 1f, 0.55f);
        }
        if (_arrived)
        {
            var since = t - _arrivedAt;
            if (!_black && since > 3.5f)
            {
                _black = true;
                Cinema.Black(1f, 1.2f);
                SunOut();
                _sunGone = true;
            }
            if (since > 17f) EndWith(ZekiISAE.EndRift, DeathType.Meditation);
        }
    }

    private void StartCracks()
    {
        _cracking = true;
        if (GameProps.Pivot != null) _cracks = RealityCracks.Create(GameProps.Pivot, LineMaterial, 900f, 48, 23);
        PlayOneShot(AudioType.TimelineEndEffect_Cracks);
        RumbleManager.PlayEndOfRealityRumble();
        ZekiISAE.Notify("DIE WIRKLICHKEIT UM DIE AUSSENDUNGSEINHEIT REISST", 6f);
    }

    private void Fire(Transform sun)
    {
        _fired = true;
        DialogueConditionManager.SharedInstance.SetConditionState(ZekiISAE.DrainActive, false);
        PlayOneShot(AudioType.NomaiGravityCannonActivate);
        PlayOneShot(AudioType.DB_VineImpact);
        Cinema.Flash(0.8f, new Color(0.8f, 1f, 0.8f));
        Wreck.Begin(true);
        if (sun == null || GameProps.Pivot == null || ZekiISAE.Instance == null) return;
        // the game's own bramble seed, 45 m across, sick and twitching
        _seed = CanonBramble.MakeSeed(GameProps.Pivot, "Fehlerhafter_Babysamen", GameProps.LocalPoint("muendung", Vector3.up * 795f), 45f, false);
        _seedLight = _seed.AddComponent<Light>();
        _seedLight.type = LightType.Point;
        _seedLight.range = 600f;
        _seedLight.intensity = 3f;
        Trail(_seed, 40f, new Color(1.2f, 2.6f, 1.3f, 1f), new Color(2.4f, 0.6f, 0.5f, 0f));
        SunShot.Launch(_seed, sun, _seed.transform.position, Flight, SunRadius, Arrive);
        Look(_seed.transform, 3f);
    }

    /// <summary>The broken seed falls into the sun: reality breaks.</summary>
    private void Arrive()
    {
        _arrived = true;
        _arrivedAt = T;
        Killing = true;
        Cinema.Bars(false);
        Cinema.Cracks(1f);
        Cinema.Flash(1f, new Color(0.85f, 1f, 0.9f));
        PlayOneShot(AudioType.SingularityCollapse);
        PlayOneShot(AudioType.TimelineEndEffect_Cracks);
        RumbleManager.PlayEndOfRealityRumble();
        if (_seed != null) _seed.SetActive(false);
        try
        {
            var effects = FindObjectOfType<PlayerCameraEffectController>();
            if (effects != null) effects.PlayRealityShatterEffect();
        }
        catch (System.Exception e)
        {
            ZekiISAE.Instance?.Log("Realitätsbruch-Effekt: " + e.Message, true);
        }
        Cards(
            (_arrivedAt + 5f, "Ein Riss. Dann tausend.", 3.2f),
            (_arrivedAt + 8.6f, "Ein Samen, der in jeder Sekunde ein Jahr wächst, wurzelt in einem sterbenden Stern.", 3.8f),
            (_arrivedAt + 12.8f, "Und die Wirklichkeit gibt nach.", 3.5f));
    }
}
