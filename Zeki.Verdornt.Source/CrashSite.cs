using System.Collections;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

namespace ZekiVerdornt;

/// <summary>
/// The crash site on Timber Hearth (spec section 4): the crater, the seed, the barrier and Tansy's text.
/// New Horizons builds them as one container (VD_Absturzstelle) at a provisional spot, and the seed node in the
/// planet's core (NH builds nodes before details). This places the whole site beside the vanilla impact crater:
///   1. sample the ground around the old seed with rays (a height map) and pick the flattest spot,
///   2. stand the site upright there, its +z facing the old seed,
///   3. measure a finer height map under the site and fit the crater, the barrier and the texts onto it,
///   4. set the seed half buried into the middle of the crater.
/// Terrain colliders can be missing right after loading, so it tries again until it finds ground.
/// </summary>
public class CrashSite : MonoBehaviour
{
    public const string SiteName = "VD_Absturzstelle";
    public const string FoundFact = "ZEKIVD_ABSTURZ_FOUND";
    private const string OldSeedPath = "Sector_TH/Sector_ImpactCrater/Interactables_ImpactCrater/ControlledByProxy_Structures/Terrain_DB_BrambleSphere_Seed_V2";
    private const string CraterSectorPath = "Sector_TH/Sector_ImpactCrater";
    /// <summary>Objects of the site that stand on the ground; their height in the config is kept above it.</summary>
    private static readonly string[] OnGround = { "VD_Absperrung", "VD_Absturz_Rinde", "VD_Absperrung_Notiz", "VD_Rauch" };
    /// <summary>The crater reaches 47 m out, its streaks 68 m: the height map covers that, the site keeps clear of the old seed.</summary>
    private const float SeedHeight = 6f, SiteRadius = 70f, Footprint = 30f, Clearance = 70f;
    private const int Attempts = 40, Cells = 28;

    private ZekiVerdornt _mod;
    private Transform _th, _site, _oldSeed, _seed, _templates;
    private OWRigidbody _body;

    public static void Begin(ZekiVerdornt mod)
    {
        var th = Locator.GetAstroObject(AstroObject.Name.TimberHearth);
        if (th == null)
        {
            mod.Log("Absturzstelle: Timber Hearth nicht gefunden.", true);
            return;
        }
        var go = new GameObject("VD_Absturzstelle_Platzierung");
        go.transform.SetParent(th.transform, false);
        var c = go.AddComponent<CrashSite>();
        c._mod = mod;
        c._th = th.transform;
        c._body = th.GetComponent<OWRigidbody>();
        c.StartCoroutine(c.Run());
    }

    private IEnumerator Run()
    {
        yield return null;
        if (!FindParts()) yield break;
        for (var attempt = 1; attempt <= Attempts; attempt++)
        {
            bool done;
            try
            {
                done = TryPlace(attempt, attempt == Attempts);
            }
            catch (System.Exception e)
            {
                Fail($"Fehler: {e}");
                done = true;
            }
            if (done) yield break;
            yield return new WaitForSeconds(1f);
        }
    }

    // ------------------------------------------------------------------------------------------ the parts
    private bool FindParts()
    {
        _oldSeed = _th.Find(OldSeedPath);
        foreach (var t in _th.GetComponentsInChildren<Transform>(true))
        {
            if (t.name == SiteName && _site == null) _site = t;
            else if (t.name == Crossing.SeedNode && _seed == null) _seed = t;
            else if (t.name == "VD_Rankenvorlagen") _templates = t;
        }
        // the vanilla seed by name, if its path ever changes (not our copy of it, which lives in VD_Rankenvorlagen)
        if (_oldSeed == null)
            _oldSeed = _th.GetComponentsInChildren<Transform>(true)
                .FirstOrDefault(t => t.name == "Terrain_DB_BrambleSphere_Seed_V2" && (_templates == null || !t.IsChildOf(_templates)));
        if (_oldSeed == null) _oldSeed = _th.Find(CraterSectorPath);
        _mod.Log($"Absturzstelle: Container {Ok(_site)}, Samenknoten {Ok(_seed)}, alter Samen {Ok(_oldSeed)}" +
                 (_oldSeed != null ? $" ({_oldSeed.name}, {Vector3.Distance(_oldSeed.position, _th.position):0} m vom Kern)." : "."));
        if (_site != null && _oldSeed != null) return true;
        Fail("Container oder alter Krater fehlen");
        return false;
    }

    private static string Ok(Object o) => o != null ? "ok" : "FEHLT";

    // ------------------------------------------------------------------------------------------ placing
    private bool TryPlace(int attempt, bool last)
    {
        var centre = _th.position;
        var anchor = _oldSeed.position;
        var up0 = (anchor - centre).normalized;
        var r0 = (anchor - centre).magnitude;
        var e1 = Vector3.Cross(up0, Mathf.Abs(Vector3.Dot(up0, _th.up)) < 0.9f ? _th.up : _th.right).normalized;
        var e2 = Vector3.Cross(up0, e1);
        var seedRadius = Mathf.Clamp(Radius(_oldSeed), 10f, 60f);

        // 1. candidate spots on rings around the old seed: 7 rays each (middle + 6 around), heights = distance to the core
        var dirs = new List<Vector3>();
        var heights = new List<IList<float?>>();
        foreach (var dist in new[] { seedRadius + Clearance, seedRadius + Clearance + 25f, seedRadius + Clearance + 50f })
            for (var k = 0; k < 12; k++)
            {
                var a = k * Mathf.PI / 6f;
                var dir = (up0 * r0 + (e1 * Mathf.Cos(a) + e2 * Mathf.Sin(a)) * dist).normalized;
                dirs.Add(dir);
                heights.Add(Ring(centre, dir, r0, Footprint));
            }
        var best = GroundFit.PickFlattest(heights, 6);
        if (best < 0)
        {
            if (!last)
            {
                if (attempt == 1 || attempt % 10 == 0) _mod.Log($"Absturzstelle: noch kein Boden unter dem Krater (Versuch {attempt}), warte.");
                return false;
            }
            Fail("kein Boden um den alten Krater gefunden");
            return true;
        }

        // 2. the site: on the ground, upright, facing the old seed
        var chosen = dirs[best];
        var ground = centre + chosen * (heights[best][0] ?? GroundFit.Median(heights[best].Where(h => h.HasValue).Select(h => h.Value).ToList()));
        var up = (ground - centre).normalized;
        var forward = Vector3.ProjectOnPlane(anchor - ground, up).normalized;
        _site.SetPositionAndRotation(ground, Quaternion.LookRotation(forward, up));

        // 3. the height map under the site, and everything fitted onto it
        var grid = new HeightGrid(SiteRadius, Cells);
        for (var i = 0; i < grid.Count; i++)
        {
            var (x, z) = grid.Point(i);
            var p = _site.TransformPoint(new Vector3(x, 0f, z));
            grid.Set(i, Ground(p + up * 80f, -up, 200f, out var hit) ? Vector3.Dot(hit - ground, up) : null);
        }
        var known = grid.FillMissing();
        var crater = Conform(grid);
        foreach (var name in OnGround) Snap(name, grid);

        // 4. the seed, half buried in the middle of the crater
        if (_seed != null)
        {
            _seed.SetParent(_site, false);
            _seed.localPosition = new Vector3(0f, grid.At(0f, 0f) + SeedHeight, 0f);
            _seed.localRotation = Quaternion.identity;
        }

        var spread = heights[best].Where(h => h.HasValue).Select(h => h.Value).ToList();
        _mod.Log($"Absturzstelle gesetzt (Versuch {attempt}): {Vector3.Distance(ground, anchor):0} m vom alten Samen, " +
                 $"Gelände-Unterschied {spread.Max() - spread.Min():0.0} m, Höhenkarte {known}/{grid.Count} Punkte, " +
                 $"Krater {(crater ? "angepasst" : "FEHLT")}, Samen {(_seed != null ? "eingesetzt" : "FEHLT")}.", !crater || _seed == null);
        if (!crater || _seed == null) ZekiVerdornt.Notify("VERDORNT: ABSTURZSTELLE UNVOLLSTÄNDIG – SIEHE OWML-LOG", 8f);
        else if (!(Locator.GetShipLogManager()?.IsFactRevealed(FoundFact) ?? false))
            ZekiVerdornt.Notify("SIGNALSKOP: UNBEKANNTES SIGNAL NAHE DEM ALTEN EINSCHLAGKRATER", 7f);
        return true;
    }

    /// <summary>Distances of the ground to the core: in direction dir, and at 6 points around it (null = no ground).</summary>
    private List<float?> Ring(Vector3 centre, Vector3 dir, float r0, float radius)
    {
        var t1 = Vector3.Cross(dir, Mathf.Abs(Vector3.Dot(dir, _th.up)) < 0.9f ? _th.up : _th.right).normalized;
        var t2 = Vector3.Cross(dir, t1);
        var list = new List<float?>();
        for (var k = -1; k < 6; k++)
        {
            var offset = k < 0 ? Vector3.zero : (t1 * Mathf.Cos(k * Mathf.PI / 3f) + t2 * Mathf.Sin(k * Mathf.PI / 3f)) * radius;
            var d = (dir * r0 + offset).normalized;
            list.Add(Ground(centre + d * (r0 + 200f), -d, 400f, out var hit) ? (hit - centre).magnitude : null);
        }
        return list;
    }

    /// <summary>The nearest solid ground of Timber Hearth along a ray (no triggers, nothing of ours, not the old seed).</summary>
    private bool Ground(Vector3 from, Vector3 dir, float length, out Vector3 point)
    {
        point = default;
        var best = float.MaxValue;
        foreach (var hit in Physics.RaycastAll(from, dir, length, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Ignore))
        {
            var t = hit.collider.transform;
            if (t.IsChildOf(_site) || t.IsChildOf(_oldSeed) || (_templates != null && t.IsChildOf(_templates)) || (_seed != null && t.IsChildOf(_seed))) continue;
            var rb = hit.collider.attachedRigidbody;
            if (_body != null && (rb == null || rb.GetComponent<OWRigidbody>() != _body)) continue;
            if (hit.distance < best)
            {
                best = hit.distance;
                point = hit.point;
            }
        }
        return best < float.MaxValue;
    }

    private static float Radius(Transform t)
    {
        var bounds = new Bounds(t.position, Vector3.zero);
        foreach (var r in t.GetComponentsInChildren<Renderer>(true)) bounds.Encapsulate(r.bounds);
        foreach (var c in t.GetComponentsInChildren<Collider>(true)) bounds.Encapsulate(c.bounds);
        var extent = Mathf.Max(bounds.extents.x, bounds.extents.y, bounds.extents.z);
        return extent > 1f ? extent : 25f;
    }

    // ------------------------------------------------------------------------------------------ fitting
    /// <summary>Lifts every vertex of the crater by the ground height under it, so the rim lies on the terrain.</summary>
    private bool Conform(HeightGrid grid)
    {
        var crater = _site.GetComponentsInChildren<MeshFilter>(true).FirstOrDefault(f => f.name == "VD_Krater");
        if (crater == null || crater.sharedMesh == null) return false;
        var t = crater.transform;
        var mesh = crater.sharedMesh;
        var vertices = mesh.vertices;
        for (var i = 0; i < vertices.Length; i++)
        {
            var s = _site.InverseTransformPoint(t.TransformPoint(vertices[i]));
            s.y += grid.At(s.x, s.z);
            vertices[i] = t.InverseTransformPoint(_site.TransformPoint(s));
        }
        mesh.vertices = vertices;
        mesh.RecalculateNormals();
        mesh.RecalculateBounds();
        var collider = crater.GetComponent<MeshCollider>();
        if (collider != null)
        {
            collider.sharedMesh = null;
            collider.sharedMesh = mesh;
        }
        return true;
    }

    private void Snap(string name, HeightGrid grid)
    {
        var t = _site.GetComponentsInChildren<Transform>(true).FirstOrDefault(x => x.name == name);
        if (t == null)
        {
            _mod.Log($"Absturzstelle: {name} nicht gefunden.", true);
            return;
        }
        // the config height counts from the ground
        var s = _site.InverseTransformPoint(t.position);
        s.y += grid.At(s.x, s.z);
        t.position = _site.TransformPoint(s);
    }

    private void Fail(string why)
    {
        _mod.Log($"Absturzstelle NICHT gesetzt: {why}.", true);
        ZekiVerdornt.Notify("VERDORNT: ABSTURZSTELLE NICHT GESETZT – SIEHE OWML-LOG", 8f);
    }
}
