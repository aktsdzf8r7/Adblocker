using System;
using System.Collections.Generic;
using UnityEngine;

namespace ZekiDornenlabyrinth;

/// <summary>
/// Colours a node of the labyrinth (spec 4): its point light, its light shafts and its fog light, and a glowing
/// colour ring around it. The ring is ours and shows the colour even where New Horizons' internals do not take it.
/// </summary>
public static class NodeTint
{
    public const string RingName = "ZEKIDL_Farbkranz";

    private static readonly Dictionary<ExitColor, Material> RingMaterials = new();

    public static Color Of(ExitColor c) => c switch
    {
        ExitColor.Rot => new Color(1f, 0.16f, 0.1f),
        ExitColor.Gruen => new Color(0.2f, 1f, 0.3f),
        ExitColor.Gelb => new Color(1f, 0.85f, 0.2f),
        ExitColor.Lila => new Color(0.72f, 0.3f, 1f),
        _ => new Color(0.74f, 0.84f, 0.66f),
    };

    public static void Reset() => RingMaterials.Clear();

    public static void Apply(ZekiDornenlabyrinth mod, InnerFogWarpVolume node, ExitColor color)
    {
        var c = Of(color);
        try
        {
            var light = (node.transform.Find("Effects/PointLight_DB_FogLight") ?? node.transform.Find("PointLight_DB_FogLight"))?.GetComponent<Light>();
            if (light != null) light.color = c;
            var shafts = node.transform.Find("Effects/DB_BrambleLightShafts");
            if (shafts != null)
                foreach (var r in shafts.GetComponentsInChildren<MeshRenderer>(true))
                    r.material.color = new Color(c.r, c.g, c.b, r.material.color.a);
            var fog = node.GetComponent<FogLight>();
            if (fog != null)
            {
                var tint = new Color(c.r, c.g, c.b, fog._tint.a);
                fog._tint = tint;
                if (fog._primaryLightData != null) fog._primaryLightData.color = tint;
            }
        }
        catch (Exception e)
        {
            mod.Log($"Knoten {node.name} einfärben: {e.Message}", true);
        }
        try
        {
            Ring(mod, node, color);
        }
        catch (Exception e)
        {
            mod.Log($"Farbkranz um {node.name}: {e.Message}", true);
        }
    }

    /// <summary>The colour ring: built once per node, scaled to its warp radius; normal nodes get a faint one.</summary>
    private static void Ring(ZekiDornenlabyrinth mod, InnerFogWarpVolume node, ExitColor color)
    {
        var ring = node.transform.Find(RingName);
        if (ring == null)
        {
            var radius = node._warpRadius > 0f ? node._warpRadius : 30f;
            var go = ModelPlacer.Build(mod, "farbkranz", RingName, node.transform, Vector3.zero, UnityEngine.Random.rotation, radius * 1.15f, spin: 6f);
            if (go == null) return;
            ring = go.transform;
        }
        var renderer = ring.GetComponent<MeshRenderer>();
        if (!RingMaterials.TryGetValue(color, out var m) || m == null)
        {
            var c = Of(color) * (color == ExitColor.Normal ? 0.6f : 2.2f);
            m = Procedural.Glow("Kranz_" + color, new Color(c.r, c.g, c.b, color == ExitColor.Normal ? 0.35f : 1f));
            RingMaterials[color] = m;
        }
        renderer.sharedMaterial = m;
    }
}
