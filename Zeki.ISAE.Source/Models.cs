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
    /// <summary>Optional exact game material names for the Blender material slots (NomaiMetall, NomaiDunkel, NomaiLeuchten).</summary>
    public Dictionary<string, string> materials = new();
    public List<PropPlacement> props = new();
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
    /// <summary>If set, the prop sits on the barrel of the main cannon at this fraction of the hub-to-muzzle distance.</summary>
    public float? alongBarrel;
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
                    if (current == null) { slots.Add("NomaiMetall"); triangles.Add(new List<int>()); current = triangles[0]; }
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

/// <summary>Turns a prop around its own up axis; faster while the sun is being drained.</summary>
public class Spinner : MonoBehaviour
{
    public float DegreesPerSecond;

    public void Update()
    {
        var boost = Finale.Running ? 8f : 1f;
        transform.Rotate(Vector3.up, DegreesPerSecond * boost * Time.deltaTime, Space.Self);
    }
}

/// <summary>Builds the Blender props in the scene once New Horizons has created all bodies.</summary>
public static class ModelPlacer
{
    private static readonly Dictionary<string, Material> Materials = new();
    private static Placements _placements = new();

    public static void PlaceAll(ZekiISAE mod)
    {
        Materials.Clear();
        var file = Path.Combine(mod.ModHelper.Manifest.ModFolderPath, "assets/models/placements.json");
        if (!File.Exists(file))
        {
            mod.Log("placements.json fehlt - keine Blender-Modelle geladen.", true);
            return;
        }
        _placements = JsonConvert.DeserializeObject<Placements>(File.ReadAllText(file));
        var count = 0;
        foreach (var p in _placements.props)
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
        mod.Log($"{count} Blender-Modelle platziert.");
    }

    /// <summary>A loose (inactive) GameObject with the model's mesh and materials.</summary>
    public static GameObject Build(ZekiISAE mod, string modelName, string name)
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
        go.layer = 0;
        go.AddComponent<MeshFilter>().sharedMesh = model.Mesh;
        var renderer = go.AddComponent<MeshRenderer>();
        renderer.sharedMaterials = model.MaterialSlots.Select(s => Resolve(mod, s, _placements)).ToArray();
        renderer.shadowCastingMode = ShadowCastingMode.On;
        go.SetActive(true);
        return go;
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

        var position = p.position.ToVector();
        var rotation = Quaternion.Euler(p.rotation.ToVector());
        if (p.alongBarrel.HasValue)
        {
            if (!CannonAim.Ready)
            {
                mod.Log($"Laufrichtung der Kanone unbekannt - {p.name} wird nicht gesetzt.", true);
                return false;
            }
            position = CannonAim.MuzzleLocal * p.alongBarrel.Value;
            rotation = Quaternion.FromToRotation(Vector3.up, CannonAim.MuzzleLocal.normalized);
        }

        var go = Build(mod, p.model, p.name);
        if (go == null) return false;
        go.SetActive(false);
        go.transform.SetParent(parent, false);
        go.transform.localPosition = position;
        go.transform.localRotation = rotation;
        go.transform.localScale = Vector3.one * p.scale;
        if (p.collider) go.AddComponent<MeshCollider>().sharedMesh = go.GetComponent<MeshFilter>().sharedMesh;
        if (p.spin != 0f) go.AddComponent<Spinner>().DegreesPerSecond = p.spin;
        go.SetActive(true);
        return true;
    }

    // ------------------------------------------------------------------------------------- materials
    private static Material Resolve(ZekiISAE mod, string slot, Placements all)
    {
        if (Materials.TryGetValue(slot, out var known)) return known;
        Material m = null;
        if (all.materials != null && all.materials.TryGetValue(slot, out var wanted) && !string.IsNullOrEmpty(wanted))
        {
            m = Resources.FindObjectsOfTypeAll<Material>().FirstOrDefault(x => x.name == wanted);
            if (m == null) mod.Log($"Material '{wanted}' für {slot} nicht gefunden, nehme Ersatz.", true);
        }
        if (m == null && mod.UseGameMaterials && slot != "NomaiLeuchten") m = FromCannon(slot == "NomaiDunkel" ? 1 : 0);
        if (m == null) m = Simple(slot);
        mod.Log($"Material {slot} -> {m.name} ({m.shader.name})");
        Materials[slot] = m;
        return m;
    }

    /// <summary>The most used opaque materials of the copied probe cannon: real Nomai metal from the game.</summary>
    private static Material FromCannon(int rank)
    {
        var cannon = CannonAim.Copy;
        if (cannon == null) return null;
        var usage = new Dictionary<Material, float>();
        foreach (var r in cannon.GetComponentsInChildren<MeshRenderer>(true))
        {
            var size = r.bounds.size;
            var weight = Mathf.Max(1f, size.x * size.y + size.y * size.z + size.x * size.z);
            foreach (var m in r.sharedMaterials)
            {
                if (m == null || m.shader == null) continue;
                var s = m.shader.name.ToLowerInvariant();
                if (m.renderQueue >= 2450 || s.Contains("particle") || s.Contains("transparent") || s.Contains("additive") || s.Contains("glass")) continue;
                usage[m] = usage.TryGetValue(m, out var w) ? w + weight : weight;
            }
        }
        return usage.OrderByDescending(kv => kv.Value).Select(kv => kv.Key).Skip(rank).FirstOrDefault();
    }

    private static Material Simple(string slot)
    {
        var glow = slot == "NomaiLeuchten";
        var shader = glow ? Shader.Find("Sprites/Default") : Shader.Find("Standard");
        if (shader == null) shader = Shader.Find("Sprites/Default") ?? Shader.Find("Standard");
        var m = new Material(shader) { name = "ZekiISAE_" + slot };
        m.color = slot switch
        {
            "NomaiLeuchten" => new Color(1.4f, 2.2f, 2.8f),
            "NomaiDunkel" => new Color(0.16f, 0.15f, 0.18f),
            _ => new Color(0.78f, 0.74f, 0.66f),
        };
        return m;
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
