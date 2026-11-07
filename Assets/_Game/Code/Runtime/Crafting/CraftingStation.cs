using System.Collections.Generic;
using UnityEngine;

namespace Meridian.Crafting
{
    /// <summary>
    /// U-051: a place that offers a crafting station within `radius` m: the spawn camp's Smelter, and the
    /// Pilgrim (its Refinery and Fabricator travel with you). Registered while enabled.
    /// </summary>
    public sealed class CraftingStation : MonoBehaviour
    {
        public Station kind = Station.Smelter;
        public float radius = 3.5f;
        /// <summary>U-113: a craft at this station keeps it working this long (the smelter's `working` loop).</summary>
        public const float WorkSeconds = 3f;
        public float WorkedUntil { get; private set; } = -1f;
        public bool Working => Time.time < WorkedUntil;

        static readonly List<CraftingStation> active = new List<CraftingStation>();

        void OnEnable() => active.Add(this);
        void OnDisable() => active.Remove(this);

        /// <summary>U-113: a craft happened at `p`: the nearest station of its kind within reach works for WorkSeconds.</summary>
        public static void Worked(Station kind, Vector2 p)
        {
            CraftingStation best = null; float bestD = float.MaxValue;
            for (int i = 0; i < active.Count; i++)
            {
                var s = active[i];
                float d = ((Vector2)s.transform.position - p).sqrMagnitude;
                if (s.kind == kind && d <= s.radius * s.radius && d < bestD) { best = s; bestD = d; }
            }
            if (best != null) best.WorkedUntil = Time.time + WorkSeconds;
        }

        public static bool AnyNear(Station kind, Vector2 p)
        {
            for (int i = 0; i < active.Count; i++)
            {
                var s = active[i];
                if (s.kind == kind && ((Vector2)s.transform.position - p).sqrMagnitude <= s.radius * s.radius) return true;
            }
            return false;
        }
    }
}
