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

        static readonly List<CraftingStation> active = new List<CraftingStation>();

        void OnEnable() => active.Add(this);
        void OnDisable() => active.Remove(this);

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
