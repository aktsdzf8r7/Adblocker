using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using UnityEngine;
using UnityEngine.Rendering;

namespace ZekiISAE;

/// <summary>assets/models/placements.json, written by tools/isae_build.py.</summary>
public class Placements
{
    /// <summary>Optional exact game material names for the Blender material slots.</summary>
    public Dictionary<string, string> materials = new();
    public List<PropPlacement> props = new();
    public List<LightPlacement> lights = new();
    /// <summary>Named points in the frame of the ISAE pivot (muzzle, lens, core, mounts, focus emitter).</summary>
    public Dictionary<string, Vector3Data> points = new();
}

public class PropPlacement
{
    public string model;
    public string name;
    /// <summary>New Horizons name of the body the prop belongs to.</summary>
    public string body;
    /// <summary>Path below the body; defaults to its "Sector".</summary>
    public string parentPath;
    public Vector3Data position = new();
    public Vector3Data rotation = new();
    public float scale = 1f;
    public bool collider;
    /// <summary>Degrees per second around the prop's own up axis.</summary>
    public float spin;
}

public class LightPlacement
{
    public string name;
    public string body;
    public string parentPath;
    public Vector3Data position = new();
    public Vector3Data color = new() { x = 1f, y = 1f, z = 1f };
    public float range = 10f;
    public float intensity = 1f;
}

public class Vector3Data
{
    public float x, y, z;
    public Vector3 ToVector() => new(x, y, z);
}

/// <summary>Minimal Wavefront OBJ reader for the meshes exported by tools/isae_models.py.</summary>
public static class ObjLoader
{
    public class Model
    {
        public Mesh Mesh;
        public string[] MaterialSlots;
    }

    private static readonly Dictionary<string, Model> Cache = new();

    public static Model Load(string path)
    {
        if (Cache.TryGetValue(path, out var cached) && cached.Mesh != null) return cached;

        var positions = new List<Vector3>();
        var uvs = new List<Vector2>();
        var normals = new List<Vector3>();
        var outPos = new List<Vector3>();
        var outUv = new List<Vector2>();
        var outNormal = new List<Vector3>();
        var lookup = new Dictionary<string, int>();
        var slots = new List<string>();
        var triangles = new List<List<int>>();
        List<int> current = null;

        float F(string s) => float.Parse(s, CultureInfo.InvariantCulture);
        int Vertex(string token)
        {
            if (lookup.TryGetValue(token, out var index)) return index;
            var parts = token.Split('/');
            int Resolve(string s, int count) { var i = int.Parse(s, CultureInfo.InvariantCulture); return i < 0 ? count + i : i - 1; }
            outPos.Add(positions[Resolve(parts[0], positions.Count)]);
            outUv.Add(parts.Length > 1 && parts[1].Length > 0 ? uvs[Resolve(parts[1], uvs.Count)] : Vector2.zero);
            outNormal.Add(parts.Length > 2 && parts[2].Length > 0 ? normals[Resolve(parts[2], normals.Count)] : Vector3.zero);
            lookup[token] = outPos.Count - 1;
            return outPos.Count - 1;
        }

        foreach (var raw in File.ReadAllLines(path))
        {
            var line = raw.Trim();
            if (line.Length == 0 || line[0] == '#') continue;
            var t = line.Split(new[] { ' ', '\t' }, StringSplitOptions.RemoveEmptyEntries);
            switch (t[0])
            {
                // Blender (right-handed) -> Unity (left-handed): mirror x and flip the winding below
                case "v": positions.Add(new Vector3(-F(t[1]), F(t[2]), F(t[3]))); break;
                case "vn": normals.Add(new Vector3(-F(t[1]), F(t[2]), F(t[3]))); break;
                case "vt": uvs.Add(new Vector2(F(t[1]), F(t[2]))); break;
                case "usemtl":
                    var slot = slots.IndexOf(t[1]);
                    if (slot < 0) { slots.Add(t[1]); triangles.Add(new List<int>()); slot = slots.Count - 1; }
                    current = triangles[slot];
                    break;
                case "f":
                    if (current == null) { slots.Add("VesselHuelle"); triangles.Add(new List<int>()); current = triangles[0]; }
                    var first = Vertex(t[1]);
                    for (var i = 2; i + 1 < t.Length; i++)
                    {
                        current.Add(first);
                        current.Add(Vertex(t[i + 1]));
                        current.Add(Vertex(t[i]));
                    }
                    break;
            }
        }

        var mesh = new Mesh { name = Path.GetFileNameWithoutExtension(path) };
        if (outPos.Count > 65000) mesh.indexFormat = IndexFormat.UInt32;
        mesh.SetVertices(outPos);
        mesh.SetUVs(0, outUv);
        mesh.SetNormals(outNormal);
        mesh.subMeshCount = triangles.Count;
        for (var i = 0; i < triangles.Count; i++) mesh.SetTriangles(triangles[i], i);
        if (normals.Count == 0) mesh.RecalculateNormals();
        mesh.RecalculateBounds();
        mesh.RecalculateTangents();

        var model = new Model { Mesh = mesh, MaterialSlots = slots.ToArray() };
        Cache[path] = model;
        return model;
    }
}

/// <summary>Builds the Blender models in the scene once New Horizons has created all bodies.</summary>
public static class ModelPlacer
{
    private static readonly Dictionary<string, Material> Materials = new();
    public static Placements Data = new();

    public static void PlaceAll(ZekiISAE mod)
    {
        Materials.Clear();
        if (!Load(mod))
        {
            mod.Log("placements.json fehlt - keine Modelle geladen.", true);
            return;
        }
        var count = 0;
        foreach (var p in Data.props)
        {
            try
            {
                if (Place(mod, p)) count++;
            }
            catch (Exception e)
            {
                mod.Log($"Modell {p.name ?? p.model} konnte nicht platziert werden: {e}", true);
            }
        }
        foreach (var l in Data.lights) AddLight(mod, l);
        mod.Log($"{count} Modelle und {Data.lights.Count} Lichter platziert.");
    }

    private static bool Place(ZekiISAE mod, PropPlacement p)
    {
        var body = mod.NewHorizons.GetPlanet(p.body);
        if (body == null)
        {
            mod.Log($"Körper '{p.body}' für Modell {p.model} nicht gefunden.", true);
            return false;
        }
        var parent = string.IsNullOrEmpty(p.parentPath) ? body.transform.Find("Sector") ?? body.transform : body.transform.Find(p.parentPath);
        if (parent == null)
        {
            mod.Log($"Pfad '{p.parentPath}' auf '{p.body}' nicht gefunden (Modell {p.model}).", true);
            return false;
        }
        var go = Build(mod, p, parent, false);
        return go != null;
    }

    /// <summary>Creates the model of a placement below parent. simple = plain colours (title screen).</summary>
    public static GameObject Build(ZekiISAE mod, PropPlacement p, Transform parent, bool simple)
    {
        var path = Path.Combine(mod.ModHelper.Manifest.ModFolderPath, "assets/models/" + p.model + ".obj");
        if (!File.Exists(path))
        {
            mod.Log($"Modell {path} fehlt.", true);
            return null;
        }
        var model = ObjLoader.Load(path);
        var go = new GameObject(p.name ?? p.model);
        go.SetActive(false);
        go.layer = 0;
        go.transform.SetParent(parent, false);
        go.transform.localPosition = p.position.ToVector();
        go.transform.localRotation = Quaternion.Euler(p.rotation.ToVector());
        go.transform.localScale = Vector3.one * p.scale;
        go.AddComponent<MeshFilter>().sharedMesh = model.Mesh;
        var renderer = go.AddComponent<MeshRenderer>();
        renderer.sharedMaterials = model.MaterialSlots.Select(s => simple ? SimpleCached(s) : Resolve(mod, s)).ToArray();
        renderer.shadowCastingMode = ShadowCastingMode.On;
        if (p.collider && !simple) go.AddComponent<MeshCollider>().sharedMesh = model.Mesh;
        if (p.spin != 0f) go.AddComponent<Spinner>().DegreesPerSecond = p.spin;
        go.SetActive(true);
        return go;
    }

    /// <summary>Reads placements.json (also used on the title screen).</summary>
    public static bool Load(ZekiISAE mod)
    {
        var file = Path.Combine(mod.ModHelper.Manifest.ModFolderPath, "assets/models/placements.json");
        if (!File.Exists(file)) return false;
        Data = JsonConvert.DeserializeObject<Placements>(File.ReadAllText(file));
        return true;
    }

    private static void AddLight(ZekiISAE mod, LightPlacement l)
    {
        var body = mod.NewHorizons.GetPlanet(l.body);
        if (body == null) return;
        var parent = string.IsNullOrEmpty(l.parentPath) ? body.transform.Find("Sector") ?? body.transform : body.transform.Find(l.parentPath);
        if (parent == null) return;
        var go = new GameObject(l.name ?? "ISAE_Licht");
        go.transform.SetParent(parent, false);
        go.transform.localPosition = l.position.ToVector();
        var light = go.AddComponent<Light>();
        light.type = LightType.Point;
        light.range = l.range;
        light.intensity = l.intensity;
        light.color = new Color(l.color.x, l.color.y, l.color.z);
        light.shadows = LightShadows.None;
    }

    // ------------------------------------------------------------------------------------- materials
    /// <summary>The material for a Blender slot: an exact name from placements.json, else the game's own.</summary>
    private static Material Resolve(ZekiISAE mod, string slot)
    {
        if (Materials.TryGetValue(slot, out var known)) return known;
        Material m = null;
        if (Data.materials != null && Data.materials.TryGetValue(slot, out var wanted) && !string.IsNullOrEmpty(wanted))
        {
            m = Resources.FindObjectsOfTypeAll<Material>().FirstOrDefault(x => x.name == wanted);
            if (m == null) mod.Log($"Material '{wanted}' für {slot} nicht gefunden, nehme Ersatz.", true);
        }
        var rank = slot switch { "VesselKupfer" => 1, "VesselDunkel" => 2, _ => 0 };
        if (m == null && !IsGlow(slot))
        {
            if (mod.MaterialSource == "Vessel") m = FromRenderers(VesselRoot(), rank) ?? FromRenderers(CannonRoot(), rank);
            else if (mod.MaterialSource == "Sondenkanone") m = FromRenderers(CannonRoot(), rank);
        }
        if (m == null) m = Simple(slot);
        mod.Log($"Material {slot} -> {m.name} ({m.shader.name})");
        Materials[slot] = m;
        return m;
    }

    private static Transform VesselRoot()
    {
        Transform fallback = null;
        foreach (var t in Resources.FindObjectsOfTypeAll<Transform>())
        {
            if (t.name != "Structure_NOM_Vessel" || !t.gameObject.scene.IsValid()) continue;
            if (t.root.name == "DB_VesselDimension_Body") return t;
            fallback = t;
        }
        return fallback;
    }

    private static Transform CannonRoot()
    {
        var opc = Locator.GetAstroObject(AstroObject.Name.ProbeCannon);
        return opc == null ? null : opc.transform.Find("Sector_OrbitalProbeCannon");
    }

    /// <summary>The n-th most used opaque material under root, weighted by surface.</summary>
    private static Material FromRenderers(Transform root, int rank)
    {
        if (root == null) return null;
        var usage = new Dictionary<Material, float>();
        foreach (var r in root.GetComponentsInChildren<MeshRenderer>(true))
        {
            var size = r.bounds.size;
            var weight = Mathf.Max(1f, size.x * size.y + size.y * size.z + size.x * size.z);
            foreach (var m in r.sharedMaterials)
            {
                if (m == null || m.shader == null) continue;
                var s = m.shader.name.ToLowerInvariant();
                if (m.renderQueue >= 2450 || s.Contains("particle") || s.Contains("transparent") || s.Contains("additive") || s.Contains("glass") || s.Contains("fog")) continue;
                usage[m] = usage.TryGetValue(m, out var w) ? w + weight : weight;
            }
        }
        var ordered = usage.OrderByDescending(kv => kv.Value).Select(kv => kv.Key).ToList();
        return ordered.Count == 0 ? null : ordered[Mathf.Min(rank, ordered.Count - 1)];
    }

    private static bool IsGlow(string slot) => slot == "VesselLeuchten" || slot == "VesselGlut";

    private static readonly Dictionary<string, Material> SimpleMaterials = new();

    private static Material SimpleCached(string slot)
    {
        if (!SimpleMaterials.TryGetValue(slot, out var m) || m == null) SimpleMaterials[slot] = m = Simple(slot);
        return m;
    }

    private static Material Simple(string slot)
    {
        var glow = IsGlow(slot);
        var shader = glow ? Shader.Find("Sprites/Default") : Shader.Find("Standard");
        if (shader == null) shader = Shader.Find("Sprites/Default") ?? Shader.Find("Standard");
        var m = new Material(shader) { name = "ZekiISAE_" + slot };
        m.color = slot switch
        {
            "VesselLeuchten" => new Color(1.3f, 2.1f, 2.8f),
            "VesselGlut" => new Color(3.2f, 1.1f, 0.35f),
            "VesselDunkel" => new Color(0.11f, 0.1f, 0.11f),
            "VesselKupfer" => new Color(0.72f, 0.43f, 0.22f),
            _ => new Color(0.46f, 0.36f, 0.28f),
        };
        return m;
    }
}

/// <summary>Turns an object around its own up axis; faster while the ISAE charges and while it drains the sun.</summary>
public class Spinner : MonoBehaviour
{
    public float DegreesPerSecond;

    public void Update()
    {
        var boost = Finale.Running ? 8f : ZekiISAE.Instance != null && ZekiISAE.Instance.Awakening ? 3f : 1f;
        transform.Rotate(Vector3.up, DegreesPerSecond * boost * Time.deltaTime, Space.Self);
    }
}
