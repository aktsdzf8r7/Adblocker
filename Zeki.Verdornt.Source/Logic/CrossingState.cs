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

    /// <summary>
    /// After the veil has closed: change the system only if a crossing is running and the player is alive. A death
    /// during the veil reloads the scene by itself (and NH would keep the loop time), so the crossing stays busy.
    /// </summary>
    public bool MayChangeSystem(bool playerDying) => Busy && !playerDying;
}
