using System.Collections.Generic;
using System.Numerics;

namespace ZekiVerdornt;

/// <summary>The centre line of a marble tube: arc length, points along it, projection, nearest slot.</summary>
public class TubePath
{
    private readonly List<Vector3> _points;
    private readonly List<float> _lengths = new() { 0f };

    public TubePath(IReadOnlyList<Vector3> points)
    {
        _points = new List<Vector3>(points);
        for (var i = 1; i < _points.Count; i++) _lengths.Add(_lengths[i - 1] + Vector3.Distance(_points[i - 1], _points[i]));
    }

    public float Length => _lengths[_lengths.Count - 1];

    /// <summary>The point at arc length s (clamped to the tube).</summary>
    public Vector3 At(float s)
    {
        if (_points.Count == 1 || s <= 0f) return _points[0];
        for (var i = 1; i < _points.Count; i++)
        {
            if (s > _lengths[i]) continue;
            var seg = _lengths[i] - _lengths[i - 1];
            return Vector3.Lerp(_points[i - 1], _points[i], seg > 0f ? (s - _lengths[i - 1]) / seg : 0f);
        }
        return _points[_points.Count - 1];
    }

    /// <summary>Arc length of the point on the tube nearest to p.</summary>
    public float Project(Vector3 p)
    {
        var best = 0f;
        var bestDist = float.MaxValue;
        for (var i = 1; i < _points.Count; i++)
        {
            var a = _points[i - 1];
            var ab = _points[i] - a;
            var len2 = ab.LengthSquared();
            var t = len2 > 0f ? System.Math.Max(0f, System.Math.Min(1f, Vector3.Dot(p - a, ab) / len2)) : 0f;
            var d = Vector3.DistanceSquared(p, a + ab * t);
            if (d < bestDist)
            {
                bestDist = d;
                best = _lengths[i - 1] + t * (_lengths[i] - _lengths[i - 1]);
            }
        }
        return best;
    }

    /// <summary>Index of the slot (arc lengths) nearest to s; ties go to the lower slot.</summary>
    public static int NearestSlot(float s, IReadOnlyList<float> slots)
    {
        var best = 0;
        for (var i = 1; i < slots.Count; i++)
            if (System.Math.Abs(slots[i] - s) < System.Math.Abs(slots[best] - s)) best = i;
        return best;
    }
}
