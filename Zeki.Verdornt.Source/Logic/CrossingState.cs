namespace ZekiVerdornt;

/// <summary>Guards the change of star system: only one crossing at a time (vortex or return seed).</summary>
public class CrossingState
{
    public bool Busy { get; private set; }

    /// <summary>True if a crossing may start now; it then stays busy until Reset.</summary>
    public bool TryBegin()
    {
        if (Busy) return false;
        Busy = true;
        return true;
    }

    public void Reset() => Busy = false;
}
