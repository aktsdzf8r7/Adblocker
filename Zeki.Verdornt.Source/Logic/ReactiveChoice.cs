using System.Collections.Generic;

namespace ZekiVerdornt;

/// <summary>Which text a reactive Nomai computer shows: the active state with the highest priority.</summary>
public static class ReactiveChoice
{
    /// <returns>The name of the active state with the highest priority, or the first state when none is active.</returns>
    public static string Pick(IReadOnlyList<(string name, int priority, bool active)> states)
    {
        if (states == null || states.Count == 0) return null;
        string best = null;
        var bestPriority = int.MinValue;
        foreach (var (name, priority, active) in states)
        {
            if (!active || priority <= bestPriority) continue;
            best = name;
            bestPriority = priority;
        }
        return best ?? states[0].name;
    }
}
