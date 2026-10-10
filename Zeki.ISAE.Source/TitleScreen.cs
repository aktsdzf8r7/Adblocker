using System.Linq;
using UnityEngine;

namespace ZekiISAE;

/// <summary>
/// Shows the Aussendungseinheit in the sky of the main menu: the Blender cannon with its spinning rings and
/// the three focus emitters, far behind the planet, pointed up across the sky. The title scene has none of
/// the game's Vessel materials, so the models use plain colours there.
/// </summary>
public static class TitleScreen
{
    private const float Distance = 3400f;

    public static void Build(ZekiISAE mod)
    {
        if (!mod.ShowOnTitle) return;
        if (!ModelPlacer.Load(mod)) return;
        var cam = Camera.main;
        if (cam == null) cam = Object.FindObjectsOfType<Camera>().FirstOrDefault(c => c.enabled);
        if (cam == null)
        {
            mod.Log("Titelbildschirm: keine Kamera gefunden.", true);
            return;
        }
        var t = cam.transform;
        var root = new GameObject("ZekiISAE_Titelkanone");
        root.transform.position = t.position + t.forward * Distance - t.right * Distance * 0.38f + t.up * Distance * 0.12f;
        // the barrel climbs diagonally across the sky, slightly away from the viewer
        var axis = (t.up * 0.85f + t.right * 0.5f + t.forward * 0.3f).normalized;
        root.transform.rotation = Quaternion.LookRotation(Vector3.ProjectOnPlane(-t.forward, axis), axis);
        var pivot = new GameObject("ISAE_Ausrichtung").transform;
        pivot.SetParent(root.transform, false);

        foreach (var p in ModelPlacer.Data.props)
        {
            if (p.model == "hauptkanone" || p.model == "laufringe")
            {
                var clone = Copy(p);
                clone.parentPath = null;
                clone.collider = false;
                ModelPlacer.Build(mod, clone, pivot, true);
            }
        }
        // the three focus emitters around the barrel
        foreach (var (letter, greek) in GameProps.Focus)
        {
            if (!ModelPlacer.Data.points.TryGetValue("fokus_" + letter, out var at)) continue;
            var focus = new GameObject("Fokus_" + greek).transform;
            focus.SetParent(pivot, false);
            focus.localPosition = at.ToVector();
            var frame = ModelPlacer.Data.props.FirstOrDefault(p => p.model == "fokusgeruest");
            if (frame != null)
            {
                var clone = Copy(frame);
                clone.collider = false;
                ModelPlacer.Build(mod, clone, focus, true);
            }
        }
        // a warm light from below, as if the sun stood under the horizon (a point light: only the cannon is near it)
        var light = new GameObject("Titelkanone_Licht").AddComponent<Light>();
        light.transform.SetParent(root.transform, false);
        light.transform.position = root.transform.position - t.up * 600f - t.forward * 900f + t.right * 300f;
        light.type = LightType.Point;
        light.range = 2600f;
        light.intensity = 1.6f;
        light.color = new Color(1f, 0.62f, 0.38f);
        mod.Log("Die Aussendungseinheit steht am Himmel des Titelbildschirms.");
    }

    private static PropPlacement Copy(PropPlacement p) => new()
    {
        model = p.model, name = p.name, body = p.body, parentPath = p.parentPath, position = p.position,
        rotation = p.rotation, scale = p.scale, collider = p.collider, spin = p.spin,
    };
}
