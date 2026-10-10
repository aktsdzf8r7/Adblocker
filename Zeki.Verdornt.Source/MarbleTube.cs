using System.Collections.Generic;
using UnityEngine;
using Num = System.Numerics;

namespace ZekiVerdornt;

/// <summary>placements.json "tubes": a marble tube of the Nomai (spec 7.1).</summary>
public class TubeConfig
{
    public string name;
    public string body;
    /// <summary>The transform the path is given in (empty: the body's Sector). Moving parents carry the tube along.</summary>
    public string parentPath;
    public List<Vector3Data> pfad = new();
    /// <summary>Slot name -> arc length along the path.</summary>
    public Dictionary<string, float> mulden = new();
    public string ruhe;
    public List<TubeAction> aktionen = new();
}

/// <summary>An object that moves with the marble: base position plus the offset of the slot the marble lies in.</summary>
public class TubeAction
{
    public string objekt;
    public Dictionary<string, Vector3Data> versatz = new();
    public float sekunden = 3f;
    /// <summary>A platform (lift): whoever stands on it within this radius rides along. 0 = not a platform.</summary>
    public float traegt;
}

/// <summary>
/// A Nomai marble tube. Look at the marble and hold the interact button: it follows your view along the tube.
/// Let go and it rolls into the nearest slot. The slot is stored as a persistent condition ZEKIVD_&lt;TUBE&gt;_&lt;SLOT&gt;
/// (New Horizons props and the reactive computers react to it), and objects of the tube move to that slot's offset.
/// </summary>
public class MarbleTube : MonoBehaviour
{
    private const float MarbleRadius = 0.45f, Reach = 3.5f, DragSpeed = 4f, RollSpeed = 2.5f;

    private TubeConfig _config;
    private TubePath _path;
    private readonly List<(string name, float s)> _slots = new();
    private readonly List<(Transform t, Vector3 home, TubeAction action)> _movers = new();
    private Transform _marble;
    private float _s, _target;
    private bool _held;
    private float _grabDistance;
    private string _slot;
    private ScreenPrompt _prompt;
    private bool _promptShown;

    public static void Setup(ZekiVerdornt mod)
    {
        foreach (var c in ModelPlacer.Data.tubes ?? new List<TubeConfig>())
        {
            var parent = ModelPlacer.Parent(mod, c.body, c.parentPath);
            if (parent == null) continue;
            var go = new GameObject("VD_Murmelroehre_" + c.name);
            go.transform.SetParent(parent, false);
            var tube = go.AddComponent<MarbleTube>();
            tube.Init(mod, c);
        }
    }

    public static string Condition(string tube, string slot) => $"ZEKIVD_{tube.ToUpperInvariant()}_{slot.ToUpperInvariant()}";

    private void Init(ZekiVerdornt mod, TubeConfig c)
    {
        _config = c;
        var pts = new List<Num.Vector3>();
        foreach (var p in c.pfad) pts.Add(new Num.Vector3(p.x, p.y, p.z));
        _path = new TubePath(pts);
        foreach (var kv in c.mulden) _slots.Add((kv.Key, kv.Value));
        _slots.Sort((a, b) => a.s.CompareTo(b.s));

        // where the marble lay when it was last let go (persistent), else the rest slot
        _slot = c.ruhe;
        foreach (var (name, _) in _slots)
            if (PlayerData.GetPersistentCondition(Condition(c.name, name))) _slot = name;
        _s = _target = SlotLength(_slot);

        var root = transform.root;
        foreach (var a in c.aktionen)
        {
            Transform found = null;
            foreach (var t in root.GetComponentsInChildren<Transform>(true))
                if (t.name == a.objekt) { found = t; break; }
            if (found == null) mod.Log($"Murmelröhre {c.name}: Objekt {a.objekt} nicht gefunden.", true);
            else
            {
                _movers.Add((found, found.localPosition, a));
                // a moving collider should be a kinematic rigidbody, not a static one
                if (a.traegt > 0f && found.GetComponent<Rigidbody>() == null) found.gameObject.AddComponent<Rigidbody>().isKinematic = true;
            }
        }
        BuildMarble();
        foreach (var (t, home, a) in _movers) t.localPosition = home + Offset(a, _slot);
        _prompt = new ScreenPrompt(InputLibrary.interact, "Murmel rollen (halten)");
        mod.Log($"Murmelröhre {c.name}: {_slots.Count} Mulden, Murmel in \"{_slot}\".");
    }

    private float SlotLength(string name)
    {
        foreach (var (n, s) in _slots)
            if (n == name) return s;
        return _slots.Count > 0 ? _slots[0].s : 0f;
    }

    private static Vector3 Offset(TubeAction a, string slot) =>
        a.versatz != null && slot != null && a.versatz.TryGetValue(slot, out var v) ? v.ToVector() : Vector3.zero;

    /// <summary>A glowing Nomai orb with its own light.</summary>
    private void BuildMarble()
    {
        var go = GameObject.CreatePrimitive(PrimitiveType.Sphere);
        go.name = "Murmel";
        Destroy(go.GetComponent<Collider>());
        go.transform.SetParent(transform, false);
        go.transform.localScale = Vector3.one * MarbleRadius * 2f;
        go.GetComponent<MeshRenderer>().sharedMaterial = new Material(Shader.Find("Sprites/Default") ?? Shader.Find("Standard"))
        {
            name = "VD_Murmel", color = new Color(1.6f, 1.9f, 2.4f)
        };
        var light = go.AddComponent<Light>();
        light.type = LightType.Point;
        light.color = new Color(0.7f, 0.85f, 1f);
        light.range = 4f;
        light.intensity = 1.2f;
        _marble = go.transform;
        _marble.localPosition = ToUnity(_path.At(_s));
    }

    private static Vector3 ToUnity(Num.Vector3 v) => new(v.X, v.Y, v.Z);
    private static Num.Vector3 ToNum(Vector3 v) => new(v.x, v.y, v.z);

    public void Update()
    {
        var cam = Locator.GetPlayerCamera();
        if (cam == null || _marble == null) return;
        var origin = cam.transform.position;
        var forward = cam.transform.forward;
        var toMarble = _marble.position - origin;
        var along = Vector3.Dot(toMarble, forward);
        var hovering = along > 0f && along < Reach && (toMarble - forward * along).magnitude < MarbleRadius + 0.35f;
        var input = OWInput.IsInputMode(InputMode.Character);

        if (!_held && hovering && input && OWInput.IsNewlyPressed(InputLibrary.interact, InputMode.Character))
        {
            _held = true;
            _grabDistance = along;
        }
        if (_held && (!input || !OWInput.IsPressed(InputLibrary.interact, InputMode.Character, 0f)))
        {
            _held = false;
            var slots = new List<float>();
            foreach (var (_, s) in _slots) slots.Add(s);
            _target = _slots.Count > 0 ? _slots[TubePath.NearestSlot(_s, slots)].s : _s;
        }
        if (_held)
        {
            var aim = origin + forward * _grabDistance;
            _target = _path.Project(ToNum(transform.InverseTransformPoint(aim)));
        }

        _s = Mathf.MoveTowards(_s, _target, (_held ? DragSpeed : RollSpeed) * Time.deltaTime);
        _marble.localPosition = ToUnity(_path.At(_s));
        if (!_held && Mathf.Abs(_s - _target) < 0.001f) Settle();
        MoveObjects();
        ShowPrompt(hovering && !_held && input);
    }

    /// <summary>The marble came to rest: remember the slot, set its condition, clear the others.</summary>
    private void Settle()
    {
        string slot = null;
        foreach (var (n, s) in _slots)
            if (Mathf.Abs(s - _s) < 0.01f) slot = n;
        if (slot == null || slot == _slot) return;
        _slot = slot;
        foreach (var (n, _) in _slots) PlayerData.SetPersistentCondition(Condition(_config.name, n), n == slot);
        var audio = Locator.GetPlayerAudioController();
        if (audio != null) audio.PlayOneShotInternal(AudioType.NomaiPowerOn);
    }

    private void MoveObjects()
    {
        foreach (var (t, home, a) in _movers)
        {
            if (t == null) continue;
            var target = home + Offset(a, _slot);
            var speed = Mathf.Max(0.1f, (Offset(a, _slot).magnitude + 0.5f) / Mathf.Max(0.1f, a.sekunden));
            var before = t.position;
            t.localPosition = Vector3.MoveTowards(t.localPosition, target, speed * Time.deltaTime);
            if (a.traegt > 0f) Carry(t, t.position - before, a.traegt);
        }
    }

    /// <summary>The player standing on a moving platform moves with it (no floor sliding up through their feet).</summary>
    private static void Carry(Transform platform, Vector3 delta, float radius)
    {
        if (delta.sqrMagnitude < 1e-8f) return;
        var player = Locator.GetPlayerBody();
        if (player == null) return;
        var local = platform.InverseTransformPoint(player.transform.position - delta);
        if (!PlatformCarry.IsOn(new Num.Vector3(local.x, local.y, local.z), radius)) return;
        player.SetPosition(player.transform.position + delta);
    }

    private void ShowPrompt(bool show)
    {
        var pm = Locator.GetPromptManager();
        if (pm == null || show == _promptShown) return;
        _promptShown = show;
        if (show) pm.AddScreenPrompt(_prompt, PromptPosition.Center, true);
        else pm.RemoveScreenPrompt(_prompt, PromptPosition.Center);
    }

    public void OnDestroy()
    {
        if (_promptShown) Locator.GetPromptManager()?.RemoveScreenPrompt(_prompt, PromptPosition.Center);
    }
}
