using System.Collections.Generic;
using UnityEngine;

namespace ZekiISAE;

/// <summary>
/// Puts the ISAE together once New Horizons has built it. Everything hangs below one pivot,
/// "Sector/ISAE_Ausrichtung", which this class turns towards the sun:
///   * the Blender cannon (Models.cs) and its core chamber,
///   * three copies of the real Orbital Probe Cannon's module, mounted on the ends of the arms in the same
///     pose they have on the real cannon (measured in game),
///   * the circle of the three focus cannons, which slowly turns around the barrel; each focus cannon is the
///     game's gravity cannon of Ember Twin, shifted so that its launch platform lies where the configs put the
///     deck, inside a Blender emitter frame,
///   * red energy tethers from the focus emitters to the lens of the main cannon; a tether goes out when its
///     phase coupler is cut,
///   * the copy of the Nomai probe in its cradle between the claws, turned along the barrel for the endings,
///   * the projection pools of the module copies: the NH pools of this mod take their place (FixPools),
///   * the Samenkern, the Pulskern and the roots (SeedSystem, Seed.cs).
/// </summary>
public static class GameProps
{
    public const string PivotPath = "Sector/ISAE_Ausrichtung";
    public static readonly (string letter, string greek)[] Focus = { ("A", "Alpha"), ("B", "Beta"), ("C", "Gamma") };
    public static readonly (string key, string name)[] Modules = { ("kontrolle", "Kontrolle"), ("start", "Start"), ("navigation", "Navigation") };
    private const string PlatformCollider = "Structure_NOM_GravityCannon/Structure_NOM_GravityCannon_LaunchuingPlatform_Collider";
    private const string PlatformModel = "Structure_NOM_GravityCannon/Structure_NOM_GravityCannon_LaunchingPlatform";

    public static Transform Isae, Pivot, FocusCircle;
    public static readonly List<Transform> FocusCannons = new();
    public static GameObject Probe;
    /// <summary>The longest axis of the probe model in its own frame (it flies along it).</summary>
    public static Vector3 ProbeAxis = Vector3.up;

    public static void Setup(ZekiISAE mod)
    {
        FocusCannons.Clear();
        Probe = null;
        Physics.SyncTransforms();
        var isae = mod.NewHorizons.GetPlanet(ZekiISAE.IsaeName);
        Isae = isae == null ? null : isae.transform;
        Pivot = Isae == null ? null : Isae.Find(PivotPath);
        if (Pivot == null)
        {
            mod.Log("Drehpunkt der Aussendungseinheit nicht gefunden.", true);
            return;
        }
        FocusCircle = Pivot.Find("ISAE_Fokuskreis");
        foreach (var (_, greek) in Focus)
        {
            var focus = FocusCircle == null ? null : FocusCircle.Find("Fokus_" + greek);
            if (focus == null) continue;
            FocusCannons.Add(focus);
            AlignPlatform(mod, focus, greek);
        }
        MountModules(mod);
        PrepareProbe(mod);
        FixPools(mod);
        Pivot.gameObject.AddComponent<SunAim>();
        if (FocusCircle != null) FocusCircle.gameObject.AddComponent<FocusOrbit>();
        Pivot.gameObject.AddComponent<Tethers>();
        CanonBramble.Setup(mod, Isae);
        SeedSystem.Setup(mod);
    }

    /// <summary>A named point from placements.json (frame of the pivot) in world space.</summary>
    public static Vector3 Point(string name)
    {
        if (Pivot == null) return Vector3.zero;
        return ModelPlacer.Data.points != null && ModelPlacer.Data.points.TryGetValue(name, out var p) ? Pivot.TransformPoint(p.ToVector()) : Pivot.position;
    }

    public static Vector3 LocalPoint(string name, Vector3 fallback) =>
        ModelPlacer.Data.points != null && ModelPlacer.Data.points.TryGetValue(name, out var p) ? p.ToVector() : fallback;

    public static Vector3 AxisWorld() => Pivot != null ? Pivot.up : Vector3.up;

    /// <summary>The probe lies in its cradle at the muzzle: centred on the cradle, its long axis along the barrel.</summary>
    private static void PrepareProbe(ZekiISAE mod)
    {
        var probe = Pivot.Find("Interstellare_Sonde");
        if (probe == null)
        {
            mod.Log("Interstellare Sonde nicht gefunden.", true);
            return;
        }
        Probe = probe.gameObject;
        var filter = Probe.GetComponentInChildren<MeshFilter>(true);
        if (filter != null && filter.sharedMesh != null)
        {
            var size = filter.sharedMesh.bounds.size;
            var local = size.x >= size.y && size.x >= size.z ? Vector3.right : size.y >= size.z ? Vector3.up : Vector3.forward;
            ProbeAxis = Probe.transform.InverseTransformDirection(filter.transform.TransformDirection(local)).normalized;
        }
        var cradle = Point("sonde");
        probe.rotation = Quaternion.FromToRotation(probe.TransformDirection(ProbeAxis), Pivot.up) * probe.rotation;
        if (filter != null && filter.sharedMesh != null)
            probe.position += cradle - filter.transform.TransformPoint(filter.sharedMesh.bounds.center);
    }

    // ------------------------------------------------------------------------------------------ projection pools
    /// <summary>
    /// The module copies come with the pool of the real module, which has nothing to show. This mod's NH pools
    /// (ISAE_Becken_*) take their place, their stones lie next to them; the copied pool is switched off.
    /// </summary>
    private static void FixPools(ZekiISAE mod)
    {
        var vanilla = Locator.GetAstroObject(AstroObject.Name.ProbeCannon);
        var real = vanilla == null ? null : vanilla.transform.Find("Sector_OrbitalProbeCannon/Sector_Module_Intact");
        foreach (var (_, name) in Modules)
        {
            var copy = Pivot.Find("ISAE_Modul_" + name);
            if (copy == null) continue;
            var ours = FindDeep(copy, "ISAE_Becken_" + name);
            Transform target = null;
            foreach (var platform in copy.GetComponentsInChildren<NomaiRemoteCameraPlatform>(true))
            {
                if (ours != null && platform.transform.IsChildOf(ours)) continue;
                if (target == null) target = platform.transform;
                platform.gameObject.SetActive(false);
            }
            Vector3 position;
            Quaternion rotation;
            if (target != null)
            {
                position = target.position;
                rotation = target.rotation;
            }
            else
            {
                // no pool left in the copy: take its place on the real module
                var vanillaPool = real == null ? null : real.GetComponentInChildren<NomaiRemoteCameraPlatform>(true);
                if (vanillaPool == null)
                {
                    mod.Log($"Modul {name}: kein Projektionsbecken gefunden, das eigene bleibt am Ersatzplatz.");
                    continue;
                }
                position = copy.TransformPoint(real.InverseTransformPoint(vanillaPool.transform.position));
                rotation = copy.rotation * (Quaternion.Inverse(real.rotation) * vanillaPool.transform.rotation);
            }
            if (ours != null)
            {
                ours.SetPositionAndRotation(position, rotation);
                // the projection stone of this module lies on the floor beside the pool
                foreach (var stone in copy.GetComponentsInChildren<Transform>(true))
                    if (stone.name.StartsWith("ISAE_Stein_" + name + "_"))
                        stone.position = position + rotation * new Vector3(3.4f, 0.5f, 0f);
            }
            mod.Log($"Modul {name}: Projektionsbecken {(target != null ? "der Kopie ersetzt" : "vom echten Modul übernommen")}.");
        }
    }

    private static Transform FindDeep(Transform root, string name)
    {
        foreach (var t in root.GetComponentsInChildren<Transform>(true))
            if (t.name == name) return t;
        return null;
    }

    // ------------------------------------------------------------------------------------------ bounds
    private static bool Bounds(Transform root, Transform frame, out Vector3 min, out Vector3 max)
    {
        min = Vector3.positiveInfinity;
        max = Vector3.negativeInfinity;
        var any = false;
        foreach (var r in root.GetComponentsInChildren<MeshRenderer>(true))
        {
            var b = r.bounds;
            if (b.size.sqrMagnitude < 0.01f)
            {
                var f = r.GetComponent<MeshFilter>();
                if (f == null || f.sharedMesh == null) continue;
                var mb = f.sharedMesh.bounds;
                b = new Bounds(r.transform.TransformPoint(mb.center), Vector3.Scale(mb.size, r.transform.lossyScale));
            }
            for (var i = 0; i < 8; i++)
            {
                var corner = new Vector3((i & 1) == 0 ? b.min.x : b.max.x, (i & 2) == 0 ? b.min.y : b.max.y, (i & 4) == 0 ? b.min.z : b.max.z);
                var local = frame.InverseTransformPoint(corner);
                min = Vector3.Min(min, local);
                max = Vector3.Max(max, local);
            }
            any = true;
        }
        return any;
    }

    // ------------------------------------------------------------------------------------------ modules
    /// <summary>
    /// Pose each module copy like the real module sits on the real cannon: barrel along +y, the module out
    /// along its arm, then slide it outwards until it sits on the collar at the end of the arm.
    /// </summary>
    private static void MountModules(ZekiISAE mod)
    {
        var vanilla = Locator.GetAstroObject(AstroObject.Name.ProbeCannon);
        var sector = vanilla == null ? null : vanilla.transform.Find("Sector_OrbitalProbeCannon");
        var real = sector == null ? null : sector.Find("Sector_Module_Intact");
        var barrel = sector == null ? (Vector3?)null : MeasureBarrel(vanilla, sector);
        foreach (var (key, name) in Modules)
        {
            var copy = Pivot.Find("ISAE_Modul_" + name);
            if (copy == null) continue;
            var mount = LocalPoint("modul_" + key, Vector3.zero);
            var arm = new Vector3(mount.x, 0f, mount.z).normalized;
            var rotation = Quaternion.LookRotation(arm, Vector3.up);
            if (barrel != null && real != null && Bounds(real, sector, out var rmin, out var rmax))
            {
                var b = barrel.Value.normalized;
                var radial = Vector3.ProjectOnPlane((rmin + rmax) / 2f, b);
                if (radial.sqrMagnitude < 1f) radial = Vector3.ProjectOnPlane(real.localPosition, b);
                if (radial.sqrMagnitude > 0.01f)
                {
                    var from = Quaternion.LookRotation(radial.normalized, b);
                    var map = Quaternion.LookRotation(arm, Vector3.up) * Quaternion.Inverse(from);
                    rotation = map * (Quaternion.Inverse(sector.rotation) * real.rotation);
                }
            }
            copy.localRotation = rotation;
            copy.localPosition = Vector3.zero;
            if (Bounds(copy, Pivot, out var min, out var max))
            {
                var centre = (min + max) / 2f;
                var half = 0f;
                for (var i = 0; i < 8; i++)
                {
                    var corner = new Vector3((i & 1) == 0 ? min.x : max.x, (i & 2) == 0 ? min.y : max.y, (i & 4) == 0 ? min.z : max.z);
                    half = Mathf.Max(half, Vector3.Dot(corner - centre, arm));
                }
                copy.localPosition = mount + arm * (half * 0.85f) - centre;
            }
            mod.Log($"Modul {name} montiert bei {copy.localPosition} (Lauf der echten Kanone: {(barrel.HasValue ? barrel.Value.normalized.ToString() : "unbekannt")}).");
        }
    }

    /// <summary>The barrel of the real cannon in its sector's frame: its launch effects sit at the muzzle.</summary>
    private static Vector3? MeasureBarrel(AstroObject vanilla, Transform sector)
    {
        var launcher = vanilla.GetComponentInChildren<OrbitalProbeLaunchController>(true);
        if (launcher == null) return null;
        if (launcher._launchParticles != null)
            foreach (var ps in launcher._launchParticles)
            {
                if (ps == null) continue;
                var local = sector.InverseTransformPoint(ps.transform.position);
                if (local.magnitude > 10f) return local;
            }
        if (launcher._probeBody != null)
        {
            var local = sector.InverseTransformPoint(launcher._probeBody.transform.position);
            if (local.magnitude > 10f) return local;
        }
        return null;
    }

    // ------------------------------------------------------------------------------------------ focus cannons
    /// <summary>Shift the gravity cannon so that the top of its launch platform is at the focus cannon's origin.</summary>
    private static void AlignPlatform(ZekiISAE mod, Transform focus, string greek)
    {
        var structure = focus.Find($"Fokuskanone_{greek}_Struktur");
        if (structure == null) return;
        var bounds = new List<Bounds>();
        var colliderRoot = structure.Find(PlatformCollider);
        if (colliderRoot != null)
            foreach (var c in colliderRoot.GetComponentsInChildren<Collider>(true))
                if (c.enabled && c.gameObject.activeInHierarchy && c.bounds.size.sqrMagnitude > 0.01f) bounds.Add(c.bounds);
        var modelRoot = structure.Find(PlatformModel);
        if (bounds.Count == 0 && modelRoot != null)
            foreach (var r in modelRoot.GetComponentsInChildren<Renderer>(true))
                if (r.bounds.size.sqrMagnitude > 0.01f) bounds.Add(r.bounds);
        if (bounds.Count == 0)
        {
            mod.Log($"Startplattform von Fokuskanone {greek} nicht gefunden - Kanone bleibt, wo sie ist.", true);
            return;
        }
        var min = Vector3.positiveInfinity;
        var max = Vector3.negativeInfinity;
        foreach (var b in bounds)
            for (var i = 0; i < 8; i++)
            {
                var corner = new Vector3((i & 1) == 0 ? b.min.x : b.max.x, (i & 2) == 0 ? b.min.y : b.max.y, (i & 4) == 0 ? b.min.z : b.max.z);
                var local = focus.InverseTransformPoint(corner);
                min = Vector3.Min(min, local);
                max = Vector3.Max(max, local);
            }
        var top = new Vector3((min.x + max.x) / 2f, max.y, (min.z + max.z) / 2f);
        structure.localPosition -= top;
        mod.Log($"Fokuskanone {greek}: Plattform {max.x - min.x:0.0} x {max.z - min.z:0.0} m, um {top} verschoben.");
    }

    /// <summary>Is the player far enough away that the structure may move without pulling the floor away?</summary>
    public static bool PlayerFar(Transform t, float distance = 1600f)
    {
        var player = Locator.GetPlayerTransform();
        return player == null || Vector3.Distance(player.position, t.position) > distance;
    }
}

/// <summary>
/// Keeps the cannon (the pivot's +y) pointed at the sun. It only turns while the player is far away, so
/// nobody standing on it has the floor pulled away; the finale overrides the direction.
/// </summary>
public class SunAim : MonoBehaviour
{
    public static SunAim Instance;
    /// <summary>World direction that replaces the sun (finale), or null.</summary>
    public Vector3? Override;
    public float DegreesPerSecond = 1.5f;

    public void Awake() => Instance = this;

    public void Start()
    {
        var target = SunDirection();
        if (target != Vector3.zero) transform.rotation = Quaternion.FromToRotation(transform.up, target) * transform.rotation;
    }

    private Vector3 SunDirection()
    {
        var sun = Locator.GetSunTransform();
        return sun == null ? Vector3.zero : (sun.position - transform.position).normalized;
    }

    public void Update()
    {
        var target = Override ?? SunDirection();
        if (target == Vector3.zero) return;
        if (Override == null && !GameProps.PlayerFar(transform)) return;
        var desired = Quaternion.FromToRotation(transform.up, target) * transform.rotation;
        transform.rotation = Quaternion.RotateTowards(transform.rotation, desired, DegreesPerSecond * Time.deltaTime);
    }
}

/// <summary>The focus cannons circle the barrel - slowly, and only while nobody stands on them.</summary>
public class FocusOrbit : MonoBehaviour
{
    private float _speed;

    public void Update()
    {
        var target = Ending.Current is Finale ? 6f : GameProps.PlayerFar(transform) ? 1.2f : 0f;
        _speed = Mathf.MoveTowards(_speed, target, Time.deltaTime * 0.6f);
        if (_speed != 0f) transform.Rotate(Vector3.up, _speed * Time.deltaTime, Space.Self);
    }
}

/// <summary>Pulsing red energy lines from the focus emitters to the lens of the main cannon.</summary>
public class Tethers : MonoBehaviour
{
    private readonly List<(LineRenderer line, Transform focus, string condition)> _lines = new();
    private Vector3 _emitter;

    public void Start()
    {
        _emitter = GameProps.LocalPoint("fokus_emitter", new Vector3(0f, 113f, 0f));
        var material = new Material(Shader.Find("Sprites/Default") ?? Shader.Find("Standard")) { color = new Color(2.6f, 1.1f, 0.6f, 1f) };
        for (var i = 0; i < GameProps.FocusCannons.Count; i++)
        {
            var go = new GameObject("Energieleitung_" + GameProps.Focus[i].greek);
            go.transform.SetParent(transform, false);
            var line = go.AddComponent<LineRenderer>();
            line.useWorldSpace = true;
            line.positionCount = 24;
            line.sharedMaterial = material;
            line.widthCurve = new AnimationCurve(new Keyframe(0f, 1f), new Keyframe(0.5f, 0.6f), new Keyframe(1f, 1.4f));
            line.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            var g = new Gradient();
            g.SetKeys(new[] { new GradientColorKey(new Color(1f, 0.35f, 0.15f), 0f), new GradientColorKey(new Color(1f, 0.6f, 0.3f), 1f) },
                      new[] { new GradientAlphaKey(0.55f, 0f), new GradientAlphaKey(0.85f, 1f) });
            line.colorGradient = g;
            _lines.Add((line, GameProps.FocusCannons[i], string.Format(ZekiISAE.CouplerCut, GameProps.Focus[i].letter)));
        }
    }

    public void Update()
    {
        var off = PlayerData.GetPersistentCondition(ZekiISAE.Deactivated);
        var lens = GameProps.Point("linse");
        var t = Time.time;
        foreach (var (line, focus, condition) in _lines)
        {
            line.enabled = !off && !PlayerData.GetPersistentCondition(condition) && focus != null;
            if (!line.enabled) continue;
            var from = focus.TransformPoint(_emitter);
            var dir = lens - from;
            var side = Vector3.Cross(dir, transform.up).normalized;
            for (var i = 0; i < line.positionCount; i++)
            {
                var u = i / (float)(line.positionCount - 1);
                var wave = Mathf.Sin(u * 14f - t * 5f) * Mathf.Sin(u * Mathf.PI) * 3.5f;
                line.SetPosition(i, from + dir * u + side * wave);
            }
            line.widthMultiplier = (Ending.Current is Finale ? 9f : 2.2f) * (1f + 0.3f * Mathf.Sin(t * 7f + focus.GetInstanceID()));
        }
    }
}
