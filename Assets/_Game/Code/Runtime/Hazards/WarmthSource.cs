using System.Collections.Generic;
using UnityEngine;

namespace Meridian.Hazards
{
    /// <summary>
    /// U-029: a place that keeps the cold off within `radius` m: the landed ship now, lit shelters when
    /// building lands (M3). Registered while enabled; HazardSystem asks whether the player is inside one.
    /// </summary>
    public sealed class WarmthSource : MonoBehaviour
    {
        public float radius = 6f;

        static readonly List<WarmthSource> active = new List<WarmthSource>();

        void OnEnable() => active.Add(this);
        void OnDisable() => active.Remove(this);

        public static bool AnyCovers(Vector2 p)
        {
            for (int i = 0; i < active.Count; i++)
            {
                var s = active[i];
                if (((Vector2)s.transform.position - p).sqrMagnitude <= s.radius * s.radius) return true;
            }
            return false;
        }
    }
}
