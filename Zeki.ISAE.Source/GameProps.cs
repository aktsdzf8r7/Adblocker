using UnityEngine;

namespace ZekiISAE;

/// <summary>
/// Finishes the placement of props that needs measurements in the running game:
///   * each focus cannon (Ember Twin's gravity cannon, copied by New Horizons) is shifted so that its launch
///     platform lies at the body origin, where the configs put the coupler, the computer, the lamps and the
///     deck gravity,
///   * the copy of the Nomai probe that waits in the cradle of the launch module is remembered for the finale.
/// The centrepiece itself (Blender, Models.cs) is built along +y and needs no measuring.
/// </summary>
public static class GameProps
{
    public static readonly string[] FocusNames = { "Fokuskanone Alpha", "Fokuskanone Beta", "Fokuskanone Gamma" };
    private const string PlatformCollider = "Structure_NOM_GravityCannon/Structure_NOM_GravityCannon_LaunchuingPlatform_Collider";
    private const string PlatformModel = "Structure_NOM_GravityCannon/Structure_NOM_GravityCannon_LaunchingPlatform";

    public static Transform Isae;
    public static GameObject Probe;
    /// <summary>The longest axis of the probe model in its own frame (it flies along it).</summary>
    public static Vector3 ProbeAxis = Vector3.up;

    public static void Setup(ZekiISAE mod)
    {
        Physics.SyncTransforms();
        var isae = mod.NewHorizons.GetPlanet(ZekiISAE.IsaeName);
        Isae = isae == null ? null : isae.transform;
        if (Isae != null) PrepareProbe(Isae);
        foreach (var name in FocusNames)
        {
            var body = mod.NewHorizons.GetPlanet(name);
            if (body != null) AlignPlatform(mod, body.transform, name);
        }
    }

    public static Vector3 Point(string name, Vector3 fallback)
    {
        if (Isae == null) return fallback;
        return ModelPlacer.Data.points != null && ModelPlacer.Data.points.TryGetValue(name, out var p)
            ? Isae.TransformPoint(p.ToVector())
            : Isae.position;
    }

    public static Vector3 MuzzleWorld() => Point("muendung", Vector3.zero);
    public static Vector3 CoreWorld() => Point("kern", Vector3.zero);
    public static Vector3 AxisWorld() => Isae != null ? Isae.up : Vector3.up;

    private static void PrepareProbe(Transform isae)
    {
        var probe = isae.Find("Sector/Interstellare_Sonde");
        if (probe == null) return;
        Probe = probe.gameObject;
        var filter = Probe.GetComponentInChildren<MeshFilter>(true);
        if (filter != null && filter.sharedMesh != null)
        {
            var size = filter.sharedMesh.bounds.size;
            var local = size.x >= size.y && size.x >= size.z ? Vector3.right : size.y >= size.z ? Vector3.up : Vector3.forward;
            // from the mesh's frame to the probe root's frame
            ProbeAxis = Probe.transform.InverseTransformDirection(filter.transform.TransformDirection(local)).normalized;
        }
    }

/// <summary>Shift the gravity cannon so that the top of its launch platform is at the body origin.</summary>
    private static void AlignPlatform(ZekiISAE mod, Transform body, string name)
    {
        var structure = body.Find($"Sector/{name.Replace(' ', '_')}_Struktur");
        if (structure == null)
        {
            mod.Log($"Schwerkraftkanone von {name} nicht gefunden.", true);
            return;
        }
        // the platform's collider, or else its visible mesh
        var bounds = new System.Collections.Generic.List<Bounds>();
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
            mod.Log($"Startplattform von {name} nicht gefunden - Kanone bleibt, wo sie ist.", true);
            return;
        }
        var min = Vector3.positiveInfinity;
        var max = Vector3.negativeInfinity;
        foreach (var b in bounds)
        {
            for (var i = 0; i < 8; i++)
            {
                var corner = new Vector3((i & 1) == 0 ? b.min.x : b.max.x, (i & 2) == 0 ? b.min.y : b.max.y, (i & 4) == 0 ? b.min.z : b.max.z);
                var local = body.InverseTransformPoint(corner);
                min = Vector3.Min(min, local);
                max = Vector3.Max(max, local);
            }
        }
        var top = new Vector3((min.x + max.x) / 2f, max.y, (min.z + max.z) / 2f);
        structure.localPosition -= top;
        mod.Log($"{name}: Plattform {max.x - min.x:0.0} x {max.z - min.z:0.0} m, um {top} verschoben.");
    }
}

/// <summary>Turns an object around its own up axis; faster while the sun is being drained.</summary>
public class Spinner : MonoBehaviour
{
    public float DegreesPerSecond;

    public void Update()
    {
        var boost = Finale.Running ? 8f : ZekiISAE.Instance != null && ZekiISAE.Instance.Awakening ? 3f : 1f;
        transform.Rotate(Vector3.up, DegreesPerSecond * boost * Time.deltaTime, Space.Self);
    }
}

