using System;
using System.Collections.Generic;
using System.Linq;

namespace ZekiVerdornt;

/// <summary>Choosing a spot on uneven ground from sampled heights (no Unity types, unit-tested).</summary>
public static class GroundFit
{
    public static float Median(IList<float> values)
    {
        if (values.Count == 0) return 0f;
        var sorted = values.OrderBy(v => v).ToList();
        var mid = sorted.Count / 2;
        return sorted.Count % 2 == 1 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2f;
    }

    /// <summary>
    /// The candidate whose sampled heights vary least (max - min). Candidates with fewer than minHits samples that
    /// found ground are skipped. -1 when none qualifies.
    /// </summary>
    public static int PickFlattest(IList<IList<float?>> candidates, int minHits)
    {
        var best = -1;
        var bestSpread = float.MaxValue;
        for (var i = 0; i < candidates.Count; i++)
        {
            var hits = candidates[i].Where(h => h.HasValue).Select(h => h.Value).ToList();
            if (hits.Count < Math.Max(1, minHits)) continue;
            var spread = hits.Max() - hits.Min();
            if (spread < bestSpread)
            {
                bestSpread = spread;
                best = i;
            }
        }
        return best;
    }
}

/// <summary>
/// A square height map from -halfSize to +halfSize in x and z with (cells + 1)² samples.
/// Sample i lies in row i / N (z) and column i % N (x). Heights between samples are interpolated bilinearly.
/// </summary>
public sealed class HeightGrid
{
    private readonly float _half, _step;
    private readonly int _n;
    private readonly float?[] _h;

    public HeightGrid(float halfSize, int cells)
    {
        _half = halfSize;
        _n = Math.Max(1, cells) + 1;
        _step = 2f * halfSize / (_n - 1);
        _h = new float?[_n * _n];
    }

    public int Count => _h.Length;

    public (float x, float z) Point(int i) => (-_half + i % _n * _step, -_half + i / _n * _step);

    public void Set(int i, float? height) => _h[i] = height;

    /// <summary>Samples without ground get the median of the others. Returns how many samples had ground.</summary>
    public int FillMissing()
    {
        var known = _h.Where(h => h.HasValue).Select(h => h.Value).ToList();
        var median = GroundFit.Median(known);
        for (var i = 0; i < _h.Length; i++) _h[i] ??= median;
        return known.Count;
    }

    public float At(float x, float z)
    {
        var fx = Clamp((x + _half) / _step, 0f, _n - 1);
        var fz = Clamp((z + _half) / _step, 0f, _n - 1);
        var x0 = Math.Min((int)fx, _n - 2);
        var z0 = Math.Min((int)fz, _n - 2);
        if (_n == 1) return H(0, 0);
        var tx = fx - x0;
        var tz = fz - z0;
        var a = H(x0, z0) + (H(x0 + 1, z0) - H(x0, z0)) * tx;
        var b = H(x0, z0 + 1) + (H(x0 + 1, z0 + 1) - H(x0, z0 + 1)) * tx;
        return a + (b - a) * tz;
    }

    private float H(int col, int row) => _h[row * _n + col] ?? 0f;

    private static float Clamp(float v, float lo, float hi) => v < lo ? lo : v > hi ? hi : v;
}
