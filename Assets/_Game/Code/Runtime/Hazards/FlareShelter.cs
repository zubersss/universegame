using UnityEngine;

namespace Meridian.Hazards
{
    /// <summary>A flare shelter (B-033 prop, POIs): inside `radius` m the flare can't reach (D-048).</summary>
    public sealed class FlareShelter : MonoBehaviour
    {
        public float radius = 4f;
        static readonly System.Collections.Generic.List<FlareShelter> active = new System.Collections.Generic.List<FlareShelter>();
        void OnEnable() => active.Add(this);
        void OnDisable() => active.Remove(this);

        public static bool AnyCovers(Vector2 p)
        {
            for (int i = 0; i < active.Count; i++)
                if (((Vector2)active[i].transform.position - p).sqrMagnitude <= active[i].radius * active[i].radius) return true;
            return false;
        }
    }
}
