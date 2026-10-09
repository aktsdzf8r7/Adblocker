using UnityEngine;

namespace ZekiISAE;

/// <summary>
/// Every prop of the ISAE is copied from the game by New Horizons (planets/*.json). This class finishes the
/// placement that needs measurements in the running game:
///   * the copied probe cannon is turned so that its barrel points along +y, like the focus cannons,
///   * the Construction Yard rings slide onto the middle of that barrel and turn,
///   * each focus cannon (Ember Twin's gravity cannon) is shifted so that its launch platform lies at the
///     body origin, where the configs put the coupler, the computer, the lamps and the deck gravity,
///   * the copy of the Nomai probe is hidden until the finale fires it.
/// </summary>
public static class GameProps
{
    public static readonly string[] FocusNames = { "Fokuskanone Alpha", "Fokuskanone Beta", "Fokuskanone Gamma" };
    private const string PlatformCollider = "Structure_NOM_GravityCannon/Structure_NOM_GravityCannon_LaunchuingPlatform_Collider";
    private const string PlatformModel = "Structure_NOM_GravityCannon/Structure_NOM_GravityCannon_LaunchingPlatform";

    public static GameObject Probe;
    /// <summary>The longest axis of the probe model in its own frame (it flies along it).</summary>
    public static Vector3 ProbeAxis = Vector3.up;

    public static void Setup(ZekiISAE mod)
    {
        Physics.SyncTransforms();
        CannonAim.Apply(mod);
        var isae = mod.NewHorizons.GetPlanet(ZekiISAE.IsaeName);
        if (isae != null)
        {
            PlaceRings(mod, isae.transform);
            PrepareProbe(mod, isae.transform);
        }
        foreach (var name in FocusNames)
        {
            var body = mod.NewHorizons.GetPlanet(name);
            if (body != null) AlignPlatform(mod, body.transform, name);
        }
    }

    private static void PlaceRings(ZekiISAE mod, Transform isae)
    {
        var rings = isae.Find("Sector/ISAE_Bauringe");
        if (rings == null || !CannonAim.Ready) return;
        rings.localPosition = CannonAim.MuzzleLocal * 0.55f;
        rings.localRotation = Quaternion.identity;
        rings.gameObject.AddComponent<Spinner>().DegreesPerSecond = 4f;
        mod.Log($"Bauringe auf den Lauf gesetzt ({rings.localPosition.magnitude:0} m vor der Nabe).");
    }

    private static void PrepareProbe(ZekiISAE mod, Transform isae)
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
        Probe.SetActive(false);
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
        var boost = Finale.Running ? 8f : 1f;
        transform.Rotate(Vector3.up, DegreesPerSecond * boost * Time.deltaTime, Space.Self);
    }
}

/// <summary>
/// Turns the copied probe cannon so that its barrel points along the body's +y axis - the direction of the
/// three focus cannons. The barrel direction is measured on the real Orbital Probe Cannon: its launch
/// effects sit at the muzzle.
/// </summary>
public static class CannonAim
{
    public static bool Ready;
    public static Transform Copy;
    /// <summary>The muzzle in the frame of the ISAE body's sector.</summary>
    public static Vector3 MuzzleLocal;

    public static void Apply(ZekiISAE mod)
    {
        Ready = false;
        var isae = mod.NewHorizons.GetPlanet(ZekiISAE.IsaeName);
        Copy = isae == null ? null : isae.transform.Find("Sector/ISAE_Hauptkanone");
        if (Copy == null)
        {
            mod.Log("Kopie der Sondenkanone nicht gefunden.", true);
            return;
        }

        var vanilla = Locator.GetAstroObject(AstroObject.Name.ProbeCannon);
        var sector = vanilla == null ? null : vanilla.transform.Find("Sector_OrbitalProbeCannon");
        var launcher = vanilla == null ? null : vanilla.GetComponentInChildren<OrbitalProbeLaunchController>(true);
        if (sector == null || launcher == null)
        {
            mod.Log("Original-Sondenkanone nicht gefunden - Ausrichtung aus ISAE.json bleibt.", true);
            return;
        }
        Vector3? muzzle = null;
        if (launcher._launchParticles != null)
        {
            foreach (var ps in launcher._launchParticles)
            {
                if (ps == null) continue;
                var local = sector.InverseTransformPoint(ps.transform.position);
                if (local.magnitude > 10f) { muzzle = local; break; }
            }
        }
        if (muzzle == null && launcher._probeBody != null)
        {
            var local = sector.InverseTransformPoint(launcher._probeBody.transform.position);
            if (local.magnitude > 10f) muzzle = local;
        }
        if (muzzle == null)
        {
            mod.Log("Mündung der Sondenkanone nicht messbar - Ausrichtung aus ISAE.json bleibt.", true);
            return;
        }

        var barrel = muzzle.Value;
        if (mod.AutoAim)
        {
            Copy.localPosition = Vector3.zero;
            Copy.localRotation = Quaternion.FromToRotation(barrel.normalized, Vector3.up);
            MuzzleLocal = Vector3.up * barrel.magnitude;
        }
        else
        {
            MuzzleLocal = Copy.localRotation * barrel;
        }
        Ready = true;
        mod.Log($"Lauf der Sondenkanone (lokal): {barrel.normalized} Länge {barrel.magnitude:0.0} m - ausgerichtet: {mod.AutoAim}");
    }

    public static Vector3 MuzzleWorld()
    {
        if (!Ready || Copy == null) return Vector3.zero;
        return Copy.parent.TransformPoint(MuzzleLocal);
    }

    public static Vector3 AxisWorld()
    {
        if (!Ready || Copy == null) return Vector3.up;
        return Copy.parent.TransformDirection(MuzzleLocal.normalized);
    }
}
