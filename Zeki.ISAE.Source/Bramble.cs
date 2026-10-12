using System.Collections.Generic;
using UnityEngine;

namespace ZekiISAE;

/// <summary>A root path from tools/isae_models.py (points in the frame it is built in, thickness in the same units).</summary>
public class VinePath
{
    public List<Vector3Data> punkte = new();
    public float dicke = 1f;
}

public class SeedSpot
{
    public Vector3Data position = new();
    public float groesse = 10f;
}

/// <summary>placements.json "bramble": where the real Dark Bramble vines and seeds go.</summary>
public class BramblePlan
{
    /// <summary>Roots around the cannon, in the frame of the ISAE pivot.</summary>
    public List<VinePath> isae = new();
    /// <summary>Real bramble seeds sitting on the roots of the cannon.</summary>
    public List<SeedSpot> knoten = new();
    /// <summary>Unit-size roots out of a seed (Keimdorn thorns, the seed in the sun).</summary>
    public List<VinePath> stern = new();
    public float keimdornScale = 30f;
}

/// <summary>
/// Everything bramble that grows in this mod is the game's own: the five vines of Dark Bramble (copied by New
/// Horizons from the Dark Bramble state of the Quantum Moon) and the bramble seed from the crater on Timber Hearth.
/// The copies sit hidden in "ISAE_Rankenvorlagen"; this class measures them (long axis, centre, size) and lays
/// clones along the root paths exported from Blender, or sets a seed to a given size.
/// </summary>
public static class CanonBramble
{
    public const string TemplatePath = "Sector/ISAE_Rankenvorlagen";

    private class Template
    {
        public GameObject Go;
        public Vector3 Center, Axis;
        public float Length, Size;
    }

    private static readonly List<Template> Vines = new();
    private static Template _seed;

    public static bool HasVines => Vines.Count > 0;

    /// <summary>Reads the hidden copies below the ISAE body (NH details Ranke_1..5 and Samen).</summary>
    public static void Setup(ZekiISAE mod, Transform isae)
    {
        Vines.Clear();
        _seed = null;
        var container = isae == null ? null : isae.Find(TemplatePath);
        if (container == null)
        {
            mod.Log("Vorlagen der Dornenranken fehlen.", true);
            return;
        }
        foreach (Transform child in container)
        {
            var t = Measure(child.gameObject);
            if (t == null) continue;
            if (child.name.StartsWith("Ranke_")) Vines.Add(t);
            else if (child.name.StartsWith("Samen")) _seed = t;
        }
        container.gameObject.SetActive(false);
        mod.Log($"Dark-Bramble-Vorlagen: {Vines.Count} Ranken, Samen {(_seed != null ? "ok" : "fehlt")}." +
                (Vines.Count > 0 ? $" Ranke 1: {Vines[0].Length:0.0} m lang." : ""));
    }

    /// <summary>Bounds of all meshes of go in its own frame: centre, longest axis, its length and the largest size.</summary>
    private static Template Measure(GameObject go)
    {
        var root = go.transform;
        var min = Vector3.positiveInfinity;
        var max = Vector3.negativeInfinity;
        var any = false;
        foreach (var f in go.GetComponentsInChildren<MeshFilter>(true))
        {
            if (f.sharedMesh == null) continue;
            var b = f.sharedMesh.bounds;
            for (var i = 0; i < 8; i++)
            {
                var c = new Vector3((i & 1) == 0 ? b.min.x : b.max.x, (i & 2) == 0 ? b.min.y : b.max.y, (i & 4) == 0 ? b.min.z : b.max.z);
                var local = root.InverseTransformPoint(f.transform.TransformPoint(c));
                min = Vector3.Min(min, local);
                max = Vector3.Max(max, local);
            }
            any = true;
        }
        if (!any) return null;
        var size = max - min;
        var axis = size.x >= size.y && size.x >= size.z ? Vector3.right : size.y >= size.z ? Vector3.up : Vector3.forward;
        var length = Vector3.Dot(size, axis);
        return new Template { Go = go, Center = (min + max) / 2f, Axis = axis, Length = Mathf.Max(0.01f, length), Size = Mathf.Max(size.x, Mathf.Max(size.y, size.z)) };
    }

    /// <summary>
    /// Lays real vines along the paths below parent. A vine segment is about twelve times as long as the root is
    /// thick; neighbouring segments overlap, each one turned and picked at random so the roots do not repeat.
    /// </summary>
    public static GameObject BuildVines(Transform parent, string name, List<VinePath> paths, float pathScale, bool colliders, int seed)
    {
        var container = new GameObject(name);
        container.transform.SetParent(parent, false);
        if (Vines.Count == 0 || paths == null) return container;
        var rnd = new System.Random(seed);
        var count = 0;
        foreach (var path in paths)
        {
            if (path.punkte == null || path.punkte.Count < 2) continue;
            var pts = new List<Vector3>();
            foreach (var p in path.punkte) pts.Add(p.ToVector() * pathScale);
            var total = 0f;
            for (var i = 1; i < pts.Count; i++) total += Vector3.Distance(pts[i - 1], pts[i]);
            var segment = Mathf.Clamp(path.dicke * pathScale * 12f, 0.5f * pathScale, total);
            var step = segment * 0.78f;
            for (var s = 0f; s < total - segment * 0.35f || s == 0f; s += step)
            {
                var a = PointAt(pts, s);
                var b = PointAt(pts, Mathf.Min(s + segment, total));
                var dir = b - a;
                var length = dir.magnitude;
                if (length < 0.01f) break;
                var t = Vines[rnd.Next(Vines.Count)];
                var piece = new GameObject("Ranke");
                piece.transform.SetParent(container.transform, false);
                piece.transform.localPosition = (a + b) / 2f;
                var side = Mathf.Abs(Vector3.Dot(dir / length, Vector3.up)) > 0.95f ? Vector3.right : Vector3.up;
                piece.transform.localRotation = Quaternion.LookRotation(dir / length, side) * Quaternion.AngleAxis((float)rnd.NextDouble() * 360f, Vector3.forward);
                Place(t, piece.transform, length * 1.15f / t.Length, Quaternion.FromToRotation(t.Axis, Vector3.forward), colliders);
                count++;
                if (s + segment >= total) break;
            }
        }
        ZekiISAE.Instance?.Log($"{name}: {count} echte Dark-Bramble-Ranken gelegt.");
        return container;
    }

    /// <summary>A real bramble seed of the given diameter, centred on a new object at localPosition below parent.</summary>
    public static GameObject MakeSeed(Transform parent, string name, Vector3 localPosition, float diameter, bool colliders)
    {
        var wrapper = new GameObject(name);
        wrapper.transform.SetParent(parent, false);
        wrapper.transform.localPosition = localPosition;
        if (_seed != null) Place(_seed, wrapper.transform, diameter / _seed.Size, Random.rotation, colliders);
        else
        {
            // fallback: a dark sphere
            var ball = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            Object.Destroy(ball.GetComponent<Collider>());
            ball.transform.SetParent(wrapper.transform, false);
            ball.transform.localScale = Vector3.one * diameter;
            ball.GetComponent<MeshRenderer>().material.color = new Color(0.12f, 0.1f, 0.08f);
        }
        return wrapper;
    }

    private static void Place(Template t, Transform holder, float scale, Quaternion rotation, bool colliders)
    {
        var clone = Object.Instantiate(t.Go, holder, false);
        clone.name = t.Go.name;
        clone.transform.localRotation = rotation;
        clone.transform.localScale = Vector3.one * scale;
        clone.transform.localPosition = -(rotation * (t.Center * scale));
        if (!colliders)
            foreach (var c in clone.GetComponentsInChildren<Collider>(true))
                Object.Destroy(c);
        clone.SetActive(true);
    }

    private static Vector3 PointAt(List<Vector3> pts, float distance)
    {
        for (var i = 1; i < pts.Count; i++)
        {
            var d = Vector3.Distance(pts[i - 1], pts[i]);
            if (distance <= d) return Vector3.Lerp(pts[i - 1], pts[i], d > 0f ? distance / d : 0f);
            distance -= d;
        }
        return pts[pts.Count - 1];
    }
}
