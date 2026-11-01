using System.Collections.Generic;

namespace Meridian.Creatures.Wardens
{
    /// <summary>
    /// U-053 extraction meter (Bible §9: "a per-area extraction meter"). Every tile dug out adds 1 to its
    /// area (AreaWidth columns); the meter drains at DecayPerSecond. Past the threshold the area trips once
    /// and stays tripped until it drains below half. Near a Warden site (vault, outpost) the threshold is lower.
    /// Pure: the director feeds it, tests drive it directly.
    /// </summary>
    public sealed class WardenMeter
    {
        public const int AreaWidth = 32;
        public const float Threshold = 40f, GuardedThreshold = 15f, GuardRadius = 48f, DecayPerSecond = 0.2f;

        readonly Dictionary<int, float> level = new Dictionary<int, float>();
        readonly Dictionary<int, float> stamp = new Dictionary<int, float>();
        readonly HashSet<int> tripped = new HashSet<int>();
        readonly List<float> guardedX = new List<float>();

        public static int AreaOf(int x) => x >= 0 ? x / AreaWidth : (x + 1) / AreaWidth - 1;

        public void Clear() { level.Clear(); stamp.Clear(); tripped.Clear(); guardedX.Clear(); }

        /// <summary>A Warden site at column x: areas within GuardRadius use the lower threshold.</summary>
        public void Guard(float x) => guardedX.Add(x);

        public bool IsGuarded(int x)
        {
            foreach (var g in guardedX) if (System.Math.Abs(g - x) <= GuardRadius) return true;
            return false;
        }

        public float ThresholdAt(int x) => IsGuarded(x) ? GuardedThreshold : Threshold;

        /// <summary>The area's meter at `time` (after decay).</summary>
        public float Level(int x, float time)
        {
            int a = AreaOf(x);
            if (!level.TryGetValue(a, out float v)) return 0f;
            float since = time - stamp[a];
            return System.Math.Max(0f, v - since * DecayPerSecond);
        }

        /// <summary>One tile dug at column x. True exactly when this dig trips the area.</summary>
        public bool Dig(int x, float time)
        {
            int a = AreaOf(x);
            float v = Level(x, time) + 1f;
            level[a] = v;
            stamp[a] = time;
            float limit = ThresholdAt(x);
            if (tripped.Contains(a))
            {
                if (v < limit * 0.5f) tripped.Remove(a);
                return false;
            }
            if (v < limit) return false;
            tripped.Add(a);
            return true;
        }
    }
}
