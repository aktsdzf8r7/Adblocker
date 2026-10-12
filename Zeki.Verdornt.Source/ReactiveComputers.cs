using System.Collections.Generic;
using UnityEngine;

namespace ZekiVerdornt;

/// <summary>placements.json "computers": one reactive Nomai computer with several texts.</summary>
public class ReactiveComputer
{
    public string body;
    public string name;
    public List<ReactiveState> states = new();
}

public class ReactiveState
{
    /// <summary>Name of the New Horizons computer (its "rename") that shows this state's text.</summary>
    public string @object;
    public int priority;
    /// <summary>All must hold: "fact:ID", "persistent:NAME" or "dialogue:NAME". Empty = always.</summary>
    public List<string> conditions = new();
}

/// <summary>
/// Nomai computers that react to what the player did (spec 7.3). Every state is its own NH computer at the same
/// spot; a few times a second this shows exactly one of them: the active state with the highest priority
/// (ReactiveChoice). A new state blinks in like a Nomai text that is being written.
/// </summary>
public class ReactiveComputers : MonoBehaviour
{
    private readonly List<(ReactiveComputer config, List<(ReactiveState state, GameObject go)> states)> _computers = new();
    private float _next;

    public static void Setup(ZekiVerdornt mod)
    {
        var go = new GameObject("VD_Reaktive_Computer");
        var rc = go.AddComponent<ReactiveComputers>();
        foreach (var c in ModelPlacer.Data.computers ?? new List<ReactiveComputer>())
        {
            var body = ModelPlacer.Parent(mod, c.body, null);
            if (body == null) continue;
            var root = body.root;
            var states = new List<(ReactiveState, GameObject)>();
            foreach (var s in c.states)
            {
                GameObject found = null;
                foreach (var t in root.GetComponentsInChildren<Transform>(true))
                    if (t.name == s.@object) { found = t.gameObject; break; }
                if (found == null) mod.Log($"Computer {c.name}: Zustand {s.@object} nicht gefunden.", true);
                else states.Add((s, found));
            }
            if (states.Count > 0) rc._computers.Add((c, states));
        }
        mod.Log($"{rc._computers.Count} reaktive Computer.");
    }

    public void Update()
    {
        if (Time.time < _next) return;
        _next = Time.time + 0.4f;
        foreach (var (_, states) in _computers)
        {
            var choice = new List<(string, int, bool)>();
            foreach (var (s, _) in states) choice.Add((s.@object, s.priority, Holds(s.conditions)));
            var pick = ReactiveChoice.Pick(choice);
            foreach (var (s, go) in states)
            {
                var show = s.@object == pick;
                if (go.activeSelf != show) go.SetActive(show);
            }
        }
    }

    private static bool Holds(List<string> conditions)
    {
        if (conditions == null) return true;
        foreach (var c in conditions)
        {
            var i = c.IndexOf(':');
            var kind = i < 0 ? "dialogue" : c.Substring(0, i);
            var id = i < 0 ? c : c.Substring(i + 1);
            var ok = kind switch
            {
                "fact" => Locator.GetShipLogManager() != null && Locator.GetShipLogManager().IsFactRevealed(id),
                "persistent" => PlayerData.GetPersistentCondition(id),
                _ => DialogueConditionManager.SharedInstance != null && DialogueConditionManager.SharedInstance.GetConditionState(id),
            };
            if (!ok) return false;
        }
        return true;
    }
}
