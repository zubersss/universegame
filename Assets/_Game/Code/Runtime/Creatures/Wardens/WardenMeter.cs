using System.Collections.Generic;

namespace Meridian.Creatures.Wardens
{
    /// <summary>
    /// U-053 extraction meter (Bible §9: "a per-area extraction meter"). U-190 (Bible 5.3 §8.1): it meters only near a Warden site:
    /// a tile dug out within GuardRadius (48 m) of a guarded site (a vault, an outpost, the Survey Archive) adds 1 to its area
    /// (AreaWidth columns); anywhere else digging never fills it (the camp is no site: a dig run is never hounded). The meter drains at
    /// DecayPerSecond; past GuardedThreshold the area trips once and stays tripped until it drains below half.
    /// Pure: the director feeds it, tests drive it directly.
    /// </summary>
    public sealed class WardenMeter
    {
        public const int AreaWidth = 32;
        public const float GuardedThreshold = 15f, GuardRadius = 48f, DecayPerSecond = 0.2f;

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

        /// <summary>The tiles an area takes to trip at column x (infinite away from every site: it never trips there).</summary>
        public float ThresholdAt(int x) => IsGuarded(x) ? GuardedThreshold : float.PositiveInfinity;

        /// <summary>The area's meter at `time` (after decay).</summary>
        public float Level(int x, float time)
        {
            int a = AreaOf(x);
            if (!level.TryGetValue(a, out float v)) return 0f;
            float since = time - stamp[a];
            return System.Math.Max(0f, v - since * DecayPerSecond);
        }

        /// <summary>One tile dug at column x. True exactly when this dig trips the area. Away from every site: nothing (U-190).</summary>
        public bool Dig(int x, float time)
        {
            if (!IsGuarded(x)) return false;
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
