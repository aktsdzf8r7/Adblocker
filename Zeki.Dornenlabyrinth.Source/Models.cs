using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using UnityEngine;
using UnityEngine.Rendering;

namespace ZekiDornenlabyrinth;

/// <summary>assets/models/placements.json, written by tools/labyrinth_build.py.</summary>
public class Placements
{
    public List<PropPlacement> props = new();
    public List<LightPlacement> lights = new();
}

public class PropPlacement
{
    public string model;
    public string name;
    /// <summary>New Horizons name of the body (dimension) the prop belongs to.</summary>
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

/// <summary>Minimal Wavefront OBJ reader for the meshes exported by tools/labyrinth_models.py.</summary>
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
                    if (current == null) { slots.Add("DornRinde"); triangles.Add(new List<int>()); current = triangles[0]; }
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

/// <summary>Builds the Blender models and lights of placements.json once New Horizons has built the system.</summary>
public static class ModelPlacer
{
    private static readonly Dictionary<string, Material> Materials = new();

    public static void PlaceAll(ZekiDornenlabyrinth mod)
    {
        Materials.Clear();
        var file = Path.Combine(mod.ModHelper.Manifest.ModFolderPath, "assets/models/placements.json");
        if (!File.Exists(file))
        {
            mod.Log("placements.json fehlt - keine Modelle geladen.", true);
            return;
        }
        var data = JsonConvert.DeserializeObject<Placements>(File.ReadAllText(file));
        var count = 0;
        foreach (var p in data.props)
        {
            try
            {
                var parent = Parent(mod, p.body, p.parentPath);
                if (parent == null)
                {
                    mod.Log($"Modell {p.name ?? p.model}: {p.body}/{p.parentPath} nicht gefunden.", true);
                    continue;
                }
                if (Build(mod, p.model, p.name, parent, p.position.ToVector(), Quaternion.Euler(p.rotation.ToVector()), p.scale, p.collider, p.spin) != null)
                    count++;
            }
            catch (Exception e)
            {
                mod.Log($"Modell {p.name ?? p.model} konnte nicht platziert werden: {e}", true);
            }
        }
        foreach (var l in data.lights)
        {
            var parent = Parent(mod, l.body, null);
            if (parent == null) continue;
            var go = new GameObject(l.name ?? "ZEKIDL_Licht");
            go.transform.SetParent(parent, false);
            go.transform.localPosition = l.position.ToVector();
            var light = go.AddComponent<Light>();
            light.type = LightType.Point;
            light.range = l.range;
            light.intensity = l.intensity;
            light.color = new Color(l.color.x, l.color.y, l.color.z);
            light.shadows = LightShadows.None;
        }
        mod.Log($"{count} von {data.props.Count} Modellen platziert.");
    }

    public static Transform Parent(ZekiDornenlabyrinth mod, string body, string parentPath)
    {
        var go = mod.NewHorizons.GetPlanet(body);
        if (go == null) return null;
        return string.IsNullOrEmpty(parentPath) ? go.transform.Find("Sector") ?? go.transform : go.transform.Find(parentPath);
    }

    public static GameObject Build(ZekiDornenlabyrinth mod, string modelName, string name, Transform parent, Vector3 position, Quaternion rotation,
        float scale = 1f, bool collider = false, float spin = 0f)
    {
        var path = Path.Combine(mod.ModHelper.Manifest.ModFolderPath, "assets/models/" + modelName + ".obj");
        if (!File.Exists(path))
        {
            mod.Log($"Modell {path} fehlt.", true);
            return null;
        }
        var model = ObjLoader.Load(path);
        var go = new GameObject(name ?? modelName);
        go.SetActive(false);
        go.transform.SetParent(parent, false);
        go.transform.localPosition = position;
        go.transform.localRotation = rotation;
        go.transform.localScale = Vector3.one * scale;
        go.AddComponent<MeshFilter>().sharedMesh = model.Mesh;
        var renderer = go.AddComponent<MeshRenderer>();
        renderer.sharedMaterials = model.MaterialSlots.Select(s => Resolve(mod, s)).ToArray();
        renderer.shadowCastingMode = ShadowCastingMode.On;
        if (collider) go.AddComponent<MeshCollider>().sharedMesh = model.Mesh;
        if (spin != 0f) go.AddComponent<Spinner>().DegreesPerSecond = spin;
        go.SetActive(true);
        return go;
    }

    private static Material Resolve(ZekiDornenlabyrinth mod, string slot)
    {
        if (Materials.TryGetValue(slot, out var known) && known != null) return known;
        var m = (slot == "DornRinde" ? BarkOfDarkBramble() : null) ?? Procedural.Make(slot);
        mod.Log($"Material {slot} -> {m.name}");
        Materials[slot] = m;
        return m;
    }

    /// <summary>The most used opaque material of Dark Bramble's outer body: its bark.</summary>
    private static Material BarkOfDarkBramble()
    {
        var db = Locator.GetAstroObject(AstroObject.Name.DarkBramble);
        if (db == null) return null;
        var usage = new Dictionary<Material, float>();
        foreach (var r in db.GetComponentsInChildren<MeshRenderer>(true))
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
        return usage.Count == 0 ? null : usage.OrderByDescending(kv => kv.Value).First().Key;
    }
}

/// <summary>Materials made at runtime: glow, ice glass and fallbacks with a little noise so nothing looks flat.</summary>
public static class Procedural
{
    public static bool IsGlow(string slot) => slot is "Kranzlicht" or "Herzlicht" or "Laternenlicht";

    public static Material Make(string slot)
    {
        var color = slot switch
        {
            "Kranzlicht" => new Color(1.6f, 1.9f, 1.5f),
            "Herzlicht" => new Color(2.2f, 0.9f, 3.2f),
            "Laternenlicht" => new Color(3.0f, 2.2f, 1.1f),
            "Eisglas" => new Color(0.7f, 0.88f, 1f, 0.3f),
            "DornEis" => new Color(0.62f, 0.76f, 0.86f),
            "Knochen" => new Color(0.82f, 0.78f, 0.68f),
            "Holz" => new Color(0.45f, 0.3f, 0.18f),
            "Metall" => new Color(0.5f, 0.52f, 0.55f),
            "Papier" => new Color(0.92f, 0.88f, 0.76f),
            _ => new Color(0.16f, 0.12f, 0.085f),
        };
        if (IsGlow(slot) || slot == "Eisglas") return Glow(slot, color);
        var m = new Material(Shader.Find("Standard")) { name = "ZEKIDL_" + slot, color = Color.white };
        m.mainTexture = Noise(color, slot.GetHashCode());
        m.SetFloat("_Glossiness", slot is "DornEis" or "Metall" ? 0.7f : 0.15f);
        return m;
    }

    /// <summary>Unlit, so it shines in the fog of a dimension (the colour rings get one per colour).</summary>
    public static Material Glow(string name, Color color) =>
        new(Shader.Find("Sprites/Default") ?? Shader.Find("Standard")) { name = "ZEKIDL_" + name, color = color };

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

/// <summary>Lets an object beat like a heart.</summary>
public class Pulser : MonoBehaviour
{
    public float Amount = 0.08f;
    public float BeatsPerSecond = 0.8f;
    private Vector3 _base;

    public void Awake() => _base = transform.localScale;

    public void Update()
    {
        var t = Time.time * BeatsPerSecond;
        // two quick beats, then a pause
        var beat = Mathf.Max(0f, Mathf.Sin(t * Mathf.PI * 2f)) * (Mathf.Repeat(t, 2f) < 1f ? 1f : 0.55f);
        transform.localScale = _base * (1f + Amount * beat);
    }
}
