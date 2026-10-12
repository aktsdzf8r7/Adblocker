using UnityEngine;

namespace ZekiDornenlabyrinth;

/// <summary>What some rooms need beyond New Horizons (spec 5).</summary>
public static class Rooms
{
    /// <summary>The anglerfish of the Frostkammer is a copy of a real one: no AI, no animation, inside a block of ice.</summary>
    public static void Freeze(ZekiDornenlabyrinth mod)
    {
        var body = mod.NewHorizons.GetPlanet("Labyrinth_Frostkammer");
        var fish = body == null ? null : FindDeep(body.transform, "ZEKIDL_Eisfisch");
        if (fish == null)
        {
            mod.Log("Frostkammer: kein Eisfisch gefunden.", true);
            return;
        }
        foreach (var c in fish.GetComponentsInChildren<AnglerfishController>(true)) c.enabled = false;
        foreach (var c in fish.GetComponentsInChildren<AnglerfishAnimController>(true)) c.enabled = false;
        foreach (var c in fish.GetComponentsInChildren<AnglerfishAudioController>(true)) c.enabled = false;
        foreach (var c in fish.GetComponentsInChildren<AnglerfishFluidVolume>(true)) c.gameObject.SetActive(false);
        foreach (var a in fish.GetComponentsInChildren<Animator>(true)) a.speed = 0f;
        foreach (var a in fish.GetComponentsInChildren<AudioSource>(true)) a.Stop();
        foreach (var b in fish.GetComponentsInChildren<Rigidbody>(true)) b.isKinematic = true;

        // the ice: a box around the fish's renderers, or a block of about its size if they are not there yet
        var bounds = new Bounds(fish.position, Vector3.zero);
        foreach (var r in fish.GetComponentsInChildren<Renderer>(true))
            if (r.bounds.size.sqrMagnitude > 0f) bounds.Encapsulate(r.bounds);
        var size = bounds.size.sqrMagnitude > 1f ? bounds.size * 1.15f : new Vector3(60f, 35f, 35f);
        var ice = GameObject.CreatePrimitive(PrimitiveType.Cube);
        Object.Destroy(ice.GetComponent<Collider>());
        ice.name = "ZEKIDL_Eisblock_Fisch";
        ice.transform.SetParent(fish.parent, true);
        ice.transform.position = bounds.size.sqrMagnitude > 1f ? bounds.center : fish.position;
        ice.transform.rotation = Quaternion.identity;
        ice.transform.localScale = size;
        ice.GetComponent<MeshRenderer>().sharedMaterial = Procedural.Make("Eisglas");
        mod.Log($"Frostkammer: Anglerfisch eingefroren, Eis {size.x:0}×{size.y:0}×{size.z:0} m.");
    }

    public static Transform FindDeep(Transform root, string name)
    {
        if (root.name == name) return root;
        foreach (Transform child in root)
        {
            var hit = FindDeep(child, name);
            if (hit != null) return hit;
        }
        return null;
    }
}
