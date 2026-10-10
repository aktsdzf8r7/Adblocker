using UnityEngine;

namespace ZekiISAE;

/// <summary>
/// Ende 3 "Verwurzelt": the ISAE is switched off, but the Samenkern lies in its Pulskern and roots hold it.
///
///   0 .. 5.5     The sun wants to die. The cannon turns to it one last time.
///   5.5          Instead of a shot: an energy explosion. The cannon falls apart into a wreck held by roots.
///   12 .. 12+W   The sun stays as it is. The player lives on for W seconds ("wreckSeconds", default 5 minutes)
///                while the core of the wreck gets unstable. Going into the seedling over the core burns.
///   T0 = 12+W    A timing error: the cannon fires its probe, a rooting baby seed on it, straight into the sun.
///   A (arrival)  The sun pulses, then slowly dissolves - no supernova.
///   A+32         Where the sun was, a baby seed grows roots. The air runs out.
///   death        Game over "Das Universum endet, aber du pflanzt invasive Pflanzen in Sternen".
/// </summary>
public class RootEnding : Ending
{
    public override EndingKind Kind => EndingKind.Verwurzelt;

    private const float ExplodeAt = 5.5f, FreeAt = 12f, Flight = 9f, PulseLength = 14f, DissolveLength = 18f;

    private float _wreckSeconds;
    private float _fireAt, _arrivedAt = -1f;
    private Transform _core, _seedMarker;
    private bool _looked, _exploded, _freed, _fired, _arrived, _dissolving, _gone, _air;
    private int _nextWarning;
    private static readonly int[] Warnings = { 240, 180, 120, 60, 30, 10 };
    private GameObject _probe, _bigSeed, _starRoots;
    private Light _seedLight;
    private PlayerResources _resources;
    private float _airStart;
    private Color _pulseColor;

    /// <summary>Skip key 3 during the wreck: the core gives up now.</summary>
    public void SkipWait()
    {
        if (_freed && !_fired) _fireAt = T;
    }

    protected override void Begin()
    {
        var mod = ZekiISAE.Instance;
        _wreckSeconds = mod != null && mod.SkipFast ? 25f : mod != null ? mod.WreckSeconds : 300f;
        _fireAt = FreeAt + _wreckSeconds;
        _nextWarning = 0;
        while (_nextWarning < Warnings.Length && Warnings[_nextWarning] >= _wreckSeconds) _nextWarning++;
        Lines(
            (0.5f, "Die Sonne will sterben. Die Aussendungseinheit richtet sich ein letztes Mal aus.", 5f),
            (ExplodeAt + 0.8f, "Doch sie ist abgeschaltet. Ihre Energie hat kein Ziel mehr.", 4.5f),
            (ExplodeAt + 5.6f, "Nur die Wurzeln halten das Wrack noch zusammen.", 4.5f));
        Cinema.Bars(true);
        ZekiISAE.Notify("DIE SONNE WILL STERBEN. DIE AUSSENDUNGSEINHEIT RICHTET SICH AUS.", 6f);
        PlayOneShot(AudioType.NomaiVesselPowerUp);
        var aim = SunAim.Instance;
        if (aim != null) aim.DegreesPerSecond = 14f;
        if (GameProps.Pivot != null) _core = Marker("ISAE_Kern_Kamera", GameProps.Pivot, GameProps.Point("kern"));
    }

    protected override void Tick(float t)
    {
        var sun = Locator.GetSunTransform();
        var aim = SunAim.Instance;
        // the wreck keeps pointing at the sun; that is where the probe will go
        if (aim != null && sun != null && !_fired) aim.Override = (sun.position - aim.transform.position).normalized;
        if (!_looked && t > 0.5f)
        {
            _looked = true;
            Look(_core, 2.5f);
        }
        if (!_exploded && t >= ExplodeAt) Explode();
        if (!_freed && t >= FreeAt)
        {
            _freed = true;
            FreeLook();
            Cinema.Bars(false);
            ZekiISAE.Notify($"DER ENERGIEKERN DES WRACKS IST INSTABIL. NOCH {Mathf.RoundToInt(_wreckSeconds)} SEKUNDEN.", 8f);
        }
        if (_freed && !_fired) WreckPhase(t);
        if (!_fired && t >= _fireAt) Fire(sun);
        if (_arrived) AfterArrival(t - _arrivedAt);
        else if (!_fired) SunBreathes(t);
    }

    // ------------------------------------------------------------------------------------------ the explosion
    private void Explode()
    {
        _exploded = true;
        if (GameProps.Pivot != null)
            EnergyBurst.Create(GameProps.Pivot, GameProps.Point("kern"), 480f, 3.5f, new Color(2.6f, 1.6f, 0.8f, 1f));
        Cinema.Flash(1f);
        PlayOneShot(AudioType.SingularityCollapse);
        PlayOneShot(AudioType.NomaiPowerOff);
        PlayOneShot(AudioType.GeneralDestruction);
        RumbleManager.PulseHeavyImpact();
        Wreck.Begin(false);
        if (SeedSystem.Instance != null) SeedSystem.Instance.Instability = 0.05f;
        ZekiISAE.Notify("ENERGIEEXPLOSION! NUR NOCH WURZELN HALTEN DIE AUSSENDUNGSEINHEIT ZUSAMMEN.", 7f);
    }

    private void WreckPhase(float t)
    {
        var k = Mathf.Clamp01((t - FreeAt) / Mathf.Max(1f, _wreckSeconds));
        if (SeedSystem.Instance != null) SeedSystem.Instance.Instability = Mathf.Max(0.05f, k);
        var left = _fireAt - t;
        while (_nextWarning < Warnings.Length && left <= Warnings[_nextWarning])
        {
            ZekiISAE.Notify($"ENERGIEKERN INSTABIL: NOCH {Warnings[_nextWarning]} SEKUNDEN", 5f);
            _nextWarning++;
        }
        if (GameProps.Pivot != null && !GameProps.PlayerFar(GameProps.Pivot, 2500f))
            Shaker.Request(0.06f + 0.4f * k * k + (Random.value > 0.995f ? 0.6f : 0f));
    }

    /// <summary>The sun wants to die but nothing takes it: it flickers dark red, but it does not explode.</summary>
    private void SunBreathes(float t)
    {
        var w = 0.5f + 0.5f * Mathf.Sin(t * 0.9f);
        SunLight(0.85f + 0.15f * w, Color.Lerp(StartColor, new Color(1f, 0.45f, 0.25f), 0.35f + 0.25f * w));
    }

    // ------------------------------------------------------------------------------------------ the probe
    private void Fire(Transform sun)
    {
        _fired = true;
        Cinema.Bars(true);
        LockInput();
        Cinema.Flash(0.9f, new Color(1f, 0.85f, 0.7f));
        PlayOneShot(AudioType.NomaiGravityCannonActivate);
        PlayOneShot(AudioType.DB_VineImpact);
        RumbleManager.PulseHeavyImpact();
        Shaker.Request(1f);
        if (SeedSystem.Instance != null) SeedSystem.Instance.Instability = 1f;
        ZekiISAE.Notify("TIMING-FEHLER IM ENERGIEKERN: DIE KANONE FEUERT IHRE SONDE", 7f);
        Lines(
            (T + 0.5f, "Ein Fehler im Takt des Kerns. Die Kanone feuert doch.", 4.5f),
            (T + 5.2f, "Die Sonde fliegt in die Sonne – und an ihr schlägt ein Samen Wurzeln.", 5f));
        if (sun == null || GameProps.Pivot == null) return;

        var muzzle = GameProps.Point("muendung");
        _probe = GameProps.Probe != null ? GameProps.Probe : new GameObject("Interstellare_Sonde");
        _probe.SetActive(true);
        _probe.transform.SetParent(GameProps.Pivot, true);
        _probe.transform.position = muzzle;
        _probe.transform.rotation = Quaternion.FromToRotation(GameProps.ProbeAxis, GameProps.AxisWorld());
        _probe.transform.localScale = Vector3.one * 6f;
        // a baby seed that already roots, grown onto the probe
        // the game's own bramble seed, already rooting with real Dark Bramble vines (sizes in the probe's frame)
        var seed = CanonBramble.MakeSeed(_probe.transform, "Babysamen_an_der_Sonde", GameProps.ProbeAxis * -0.6f, 1.1f, false);
        var plan = ModelPlacer.Data.bramble;
        if (plan != null) CanonBramble.BuildVines(seed.transform, "Wurzeln_an_der_Sonde", plan.stern, 0.45f, false, 3);
        var light = _probe.AddComponent<Light>();
        light.type = LightType.Point;
        light.color = new Color(0.55f, 1f, 0.6f);
        light.range = 400f;
        light.intensity = 2.5f;
        Trail(_probe, 22f, new Color(1.3f, 2.6f, 1.4f, 1f), new Color(0.5f, 1.4f, 0.6f, 0f));
        SunShot.Launch(_probe, sun, muzzle, Flight, SunRadius, () =>
        {
            _arrived = true;
            _arrivedAt = T;
            if (_probe != null) _probe.SetActive(false);
            Cinema.Flash(0.6f, new Color(0.7f, 1f, 0.75f));
            PlayOneShot(AudioType.SingularityCreate);
            Look(Locator.GetSunTransform(), 2f);
            _pulseColor = Sun._sunLight != null ? Sun._sunLight._sunBaseColor : StartColor;
        });
        Look(_probe.transform, 3f);
    }

    // ------------------------------------------------------------------------------------------ the sun dissolves
    private void AfterArrival(float since)
    {
        var green = new Color(0.55f, 1f, 0.6f);
        if (since < PulseLength)
        {
            // it starts to pulse, faster and harder
            var k = since / PulseLength;
            var amp = Mathf.Lerp(0.03f, 0.2f, k);
            var freq = Mathf.Lerp(0.5f, 1.6f, k);
            var w = Mathf.Sin(since * Mathf.PI * 2f * freq);
            SunScale(1f + amp * w);
            SunLight(1f + 0.4f * amp * w * 5f, Color.Lerp(_pulseColor, green, k * 0.6f));
            Shaker.Request(0.2f + 0.3f * k);
            return;
        }
        if (!_dissolving)
        {
            _dissolving = true;
            CollapseParticles();
            PlayOneShot(AudioType.Sun_Collapse);
            Lines((T + 0.5f, "Keine Supernova. Die Sonne löst sich einfach auf.", 5f));
        }
        var d = Mathf.Clamp01((since - PulseLength) / DissolveLength);
        if (d < 1f)
        {
            var remaining = 1f - Smooth(d);
            SunScale(remaining * (1f + 0.04f * Mathf.Sin(since * 9f)));
            SunLight(Mathf.Pow(remaining, 0.8f), Color.Lerp(green, new Color(0.25f, 0.5f, 0.3f), d));
            SunSurface(d);
            DistantSun(remaining);
            return;
        }
        if (!_gone)
        {
            _gone = true;
            SunOut();
            Seed();
        }
        var g = since - PulseLength - DissolveLength;
        GrowSeed(g);
        DimAmbient(0.2f);
        if (!_air && g > 8f)
        {
            _air = true;
            _airStart = T;
            // from here on any death ends the game with this ending's text
            Killing = true;
            DialogueConditionManager.SharedInstance.SetConditionState(ZekiISAE.EndRoots, true);
            _resources = FindObjectOfType<PlayerResources>();
            Lines((T + 1f, "Die Wurzeln wachsen. Langsam. Geduldig.", 4.5f),
                  (T + 7f, "Die Luft wird dünn.", 4f));
        }
        if (_air) RunOutOfAir(T - _airStart);
    }

    /// <summary>A baby seed where the sun was. Its roots grow slowly into the dark.</summary>
    private void Seed()
    {
        var sun = Locator.GetSunTransform();
        if (sun == null) return;
        _seedMarker = Marker("Sonnensamen", sun, sun.position);
        // the game's own bramble seed and Dark Bramble vines, unit size here, grown by GrowSeed
        _bigSeed = CanonBramble.MakeSeed(_seedMarker, "Sonnensamen_Kern", Vector3.zero, 2.4f, false);
        _starRoots = CanonBramble.BuildVines(_seedMarker, "Sonnensamen_Wurzeln", ModelPlacer.Data.bramble?.stern, 1f, false, 9);
        _seedLight = _seedMarker.gameObject.AddComponent<Light>();
        _seedLight.type = LightType.Point;
        _seedLight.color = new Color(0.5f, 1f, 0.55f);
        _seedLight.range = 40000f;
        _seedLight.intensity = 0f;
        PlayOneShot(AudioType.VesselSingularityCreate);
        Cinema.Flash(0.5f, new Color(0.6f, 1f, 0.65f));
        Look(_seedMarker, 2f);
        Lines((T + 1.5f, "Wo die Sonne war, keimt ein Samen.", 5f));
    }

    private void GrowSeed(float g)
    {
        var parentScale = _seedMarker != null ? Mathf.Max(0.0001f, _seedMarker.lossyScale.x) : 1f;
        if (_bigSeed != null)
        {
            var k = Smooth(g / 8f);
            _bigSeed.transform.localScale = Vector3.one * (420f * k * (1f + 0.03f * Mathf.Sin(g * 1.3f)) / parentScale);
            _bigSeed.transform.Rotate(Vector3.up, 2f * Time.deltaTime, Space.Self);
        }
        if (_starRoots != null)
        {
            var k = Mathf.Clamp01((g - 2f) / 45f);
            _starRoots.transform.localScale = Vector3.one * (Mathf.Max(0.001f, 950f * k * (0.6f + 0.4f * k)) / parentScale);
            _starRoots.transform.Rotate(Vector3.up, 0.6f * Time.deltaTime, Space.Self);
        }
        if (_seedLight != null) _seedLight.intensity = Mathf.MoveTowards(_seedLight.intensity, 1.4f, Time.deltaTime * 0.3f);
    }

    private void RunOutOfAir(float since)
    {
        if (_resources != null)
        {
            var max = PlayerResources._maxOxygen > 0f ? PlayerResources._maxOxygen : 100f;
            // the suit's tank runs dry within half a minute, whatever refills it
            var cap = max * 0.06f * Mathf.Clamp01(1f - since / 25f);
            if (_resources._currentOxygen > cap) _resources._currentOxygen = cap;
        }
        if (since > 26f) Cinema.Black(1f, 6f);
        if (since > 40f) EndWith(ZekiISAE.EndRoots, DeathType.Asphyxiation);
    }
}
