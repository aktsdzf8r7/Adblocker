using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using UnityEngine;
using UnityEngine.Rendering;

namespace ZekiVerdornt;

/// <summary>assets/models/placements.json, written by tools/isae_build.py.</summary>
public class Placements
{
    public List<PropPlacement> props = new();
    public List<LightPlacement> lights = new();
    /// <summary>Real Dark Bramble vines and seeds per body or dimension (Bramble.cs).</summary>
    public Dictionary<string, VinePlan> bramble = new();
    /// <summary>Reactive Nomai computers (ReactiveComputers.cs).</summary>
    public List<ReactiveComputer> computers = new();
    /// <summary>Marble tubes (MarbleTube.cs).</summary>
    public List<TubeConfig> tubes = new();
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
    /// <summary>Built but switched off; the DLL shows it later (the roots of "Verwurzelt").</summary>
    public bool hidden;
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

/// <summary>
/// Builds the Blender models once New Horizons has built a system. Dornenkranz has no stock planets
/// (destroyStockPlanets), so the opaque materials come from hidden New Horizons copies of game props:
/// the bark from a real Dark Bramble vine, the Nomai hull and copper from a real Nomai structure
/// ("VD_Materialvorlagen" on Erstling). Ice, glow and glass are made here.
/// </summary>
public static class ModelPlacer
{
    public const string MaterialTemplates = "Sector/VD_Materialvorlagen";
    private static readonly Dictionary<string, Material> Materials = new();
    public static Placements Data = new();

    public static bool Load(ZekiVerdornt mod)
    {
        var file = Path.Combine(mod.ModHelper.Manifest.ModFolderPath, "assets/models/placements.json");
        if (!File.Exists(file)) return false;
        Data = JsonConvert.DeserializeObject<Placements>(File.ReadAllText(file));
        return true;
    }

    /// <summary>Places every model and light of the given star system's bodies.</summary>
    public static void PlaceAll(ZekiVerdornt mod)
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
                if (Place(mod, p) != null) count++;
            }
            catch (Exception e)
            {
                mod.Log($"Modell {p.name ?? p.model} konnte nicht platziert werden: {e}", true);
            }
        }
        foreach (var l in Data.lights) AddLight(mod, l);
        mod.Log($"{count} Modelle platziert.");
        PlaceVines(mod);
    }

    /// <summary>The parent of a placement, or null when its body is not in the current system.</summary>
    public static Transform Parent(ZekiVerdornt mod, string body, string parentPath)
    {
        var go = mod.NewHorizons.GetPlanet(body);
        // vanilla bodies are named like the AstroObject names in the configs (TIMBER_HEARTH)
        if (go == null && Enum.TryParse<AstroObject.Name>(body.Replace("_", ""), true, out var name) && name != AstroObject.Name.None)
        {
            var astro = Locator.GetAstroObject(name);
            if (astro != null) go = astro.gameObject;
        }
        if (go == null) return null;
        return string.IsNullOrEmpty(parentPath) ? go.transform.Find("Sector") ?? go.transform : go.transform.Find(parentPath);
    }

    private static GameObject Place(ZekiVerdornt mod, PropPlacement p)
    {
        var parent = Parent(mod, p.body, p.parentPath);
        if (parent == null) return null;
        var go = Build(mod, p, parent);
        if (go != null && p.hidden) go.SetActive(false);
        return go;
    }

    public static GameObject Build(ZekiVerdornt mod, PropPlacement p, Transform parent)
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
        go.transform.SetParent(parent, false);
        go.transform.localPosition = p.position.ToVector();
        go.transform.localRotation = Quaternion.Euler(p.rotation.ToVector());
        go.transform.localScale = Vector3.one * p.scale;
        go.AddComponent<MeshFilter>().sharedMesh = model.Mesh;
        var renderer = go.AddComponent<MeshRenderer>();
        renderer.sharedMaterials = model.MaterialSlots.Select(s => Resolve(mod, s)).ToArray();
        renderer.shadowCastingMode = ShadowCastingMode.On;
        if (p.collider) go.AddComponent<MeshCollider>().sharedMesh = model.Mesh;
        if (p.spin != 0f) go.AddComponent<Spinner>().DegreesPerSecond = p.spin;
        go.SetActive(true);
        return go;
    }

    /// <summary>The real Dark Bramble vines and seeds of every body of this system that has a plan.</summary>
    private static void PlaceVines(ZekiVerdornt mod)
    {
        // the templates of this system: on Erstling in Dornenkranz, on Timber Hearth at home
        var host = mod.NewHorizons.GetPlanet("Erstling")?.transform;
        if (host == null) host = Locator.GetAstroObject(AstroObject.Name.TimberHearth)?.transform;
        if (host == null || Data.bramble == null) return;
        CanonBramble.Setup(mod, host);
        foreach (var kv in Data.bramble)
        {
            var parent = Parent(mod, kv.Key, null);
            if (parent == null) continue;
            var vines = CanonBramble.BuildVines(parent, "VD_Ranken", kv.Value.pfade, 1f, true, kv.Key.GetHashCode());
            for (var i = 0; i < kv.Value.samen.Count; i++)
                CanonBramble.MakeSeed(vines.transform, "VD_Samen_" + i, kv.Value.samen[i].position.ToVector(), kv.Value.samen[i].groesse, true);
        }
    }

    private static void AddLight(ZekiVerdornt mod, LightPlacement l)
    {
        var parent = Parent(mod, l.body, l.parentPath);
        if (parent == null) return;
        var go = new GameObject(l.name ?? "VD_Licht");
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
    private static Material Resolve(ZekiVerdornt mod, string slot)
    {
        if (Materials.TryGetValue(slot, out var known) && known != null) return known;
        var m = slot switch
        {
            "DornRinde" => FromTemplates(mod, "Ranke", 0),
            "NomaiHuelle" => FromTemplates(mod, "Nomai", 0),
            "NomaiKupfer" => FromTemplates(mod, "Nomai", 1),
            _ => null,
        } ?? Procedural.Make(slot);
        mod.Log($"Material {slot} -> {m.name}");
        Materials[slot] = m;
        return m;
    }

    /// <summary>The n-th most used opaque material of the hidden template copies whose name starts with prefix.</summary>
    private static Material FromTemplates(ZekiVerdornt mod, string prefix, int rank)
    {
        var erstling = mod.NewHorizons.GetPlanet("Erstling");
        var root = erstling == null ? null : erstling.transform.Find(MaterialTemplates);
        if (root == null) return null;
        var usage = new Dictionary<Material, float>();
        foreach (Transform t in root)
        {
            if (!t.name.StartsWith(prefix)) continue;
            foreach (var r in t.GetComponentsInChildren<MeshRenderer>(true))
            {
                var size = r.bounds.size;
                var weight = Mathf.Max(1f, size.x * size.y + size.y * size.z + size.x * size.z);
                foreach (var m in r.sharedMaterials)
                {
                    if (m == null || m.shader == null || m.renderQueue >= 2450) continue;
                    var s = m.shader.name.ToLowerInvariant();
                    if (s.Contains("particle") || s.Contains("transparent") || s.Contains("additive") || s.Contains("fog")) continue;
                    usage[m] = usage.TryGetValue(m, out var w) ? w + weight : weight;
                }
            }
        }
        var ordered = usage.OrderByDescending(kv => kv.Value).Select(kv => kv.Key).ToList();
        return ordered.Count == 0 ? null : ordered[Mathf.Min(rank, ordered.Count - 1)];
    }
}

/// <summary>Materials made at runtime: glow, glass, ice and fallbacks with a little noise so nothing looks flat.</summary>
public static class Procedural
{
    public static bool IsGlow(string slot) => slot is "Keimlicht" or "Sternlicht" or "NomaiLeuchten" or "DornGlut";

    public static Material Make(string slot)
    {
        var color = slot switch
        {
            "Keimlicht" => new Color(0.9f, 2.8f, 1.2f),
            "Sternlicht" => new Color(3.2f, 2.5f, 1.2f),
            "NomaiLeuchten" => new Color(1.3f, 2.1f, 2.8f),
            "DornGlut" => new Color(3.4f, 0.9f, 0.25f),
            "NomaiGlas" => new Color(0.75f, 0.9f, 1f, 0.22f),
            "DornEis" => new Color(0.62f, 0.76f, 0.86f),
            "DornKristall" => new Color(0.55f, 0.38f, 0.9f),
            "NomaiKupfer" => new Color(0.72f, 0.43f, 0.22f),
            "NomaiHuelle" => new Color(0.46f, 0.36f, 0.28f),
            "HolzHearth" => new Color(0.45f, 0.3f, 0.18f),
            _ => new Color(0.16f, 0.12f, 0.085f),
        };
        if (IsGlow(slot) || slot == "NomaiGlas")
            return new Material(Shader.Find("Sprites/Default") ?? Shader.Find("Standard")) { name = "VD_" + slot, color = color };
        var m = new Material(Shader.Find("Standard")) { name = "VD_" + slot, color = Color.white };
        m.mainTexture = Noise(color, slot.GetHashCode());
        m.SetFloat("_Glossiness", slot is "DornEis" or "DornKristall" ? 0.75f : 0.15f);
        return m;
    }

    /// <summary>A tiling texture: the base colour, darkened and lightened by two octaves of Perlin noise.</summary>
    private static Texture2D Noise(Color baseColor, int seed)
    {
        const int size = 128;
        var tex = new Texture2D(size, size, TextureFormat.RGBA32, true) { wrapMode = TextureWrapMode.Repeat };
        var ox = (seed & 0xff) * 0.37f;
        var pixels = new Color[size * size];
        for (var y = 0; y < size; y++)
            for (var x = 0; x < size; x++)
            {
                // tileable: sample the noise on a torus
                float u = x / (float)size * Mathf.PI * 2f, v = y / (float)size * Mathf.PI * 2f;
                var n = 0.65f * Mathf.PerlinNoise(ox + 3f * Mathf.Cos(u), 3f * Mathf.Sin(v) + 1.7f * Mathf.Cos(v))
                        + 0.35f * Mathf.PerlinNoise(ox + 9f * Mathf.Sin(u), 9f * Mathf.Cos(v));
                var k = Mathf.Lerp(0.72f, 1.25f, n);
                pixels[y * size + x] = new Color(baseColor.r * k, baseColor.g * k, baseColor.b * k, 1f);
            }
        tex.SetPixels(pixels);
        tex.Apply(true);
        return tex;
    }
}

/// <summary>Turns an object around its own up axis.</summary>
public class Spinner : MonoBehaviour
{
    public float DegreesPerSecond;

    public void Update() => transform.Rotate(Vector3.up, DegreesPerSecond * Time.deltaTime, Space.Self);
}
