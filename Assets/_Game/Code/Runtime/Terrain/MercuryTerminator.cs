using UnityEngine;

namespace Meridian.Terrain
{
    public enum MercuryZone { Day, Twilight, Night }

    /// <summary>
    /// Mercury's moving day/night boundary (Bible §7.3): two terminators half a world apart that creep
    /// 1 m every 6 real seconds; a ~400 m twilight band is centred on each. Columns between the dawn
    /// terminator and the dusk terminator (ahead of the creep) are on the day side. Pure math for the
    /// hazards (U-049) and the world (U-048).
    /// </summary>
    public static class MercuryTerminator
    {
        public const float CreepSecondsPerMetre = 6f;
        public const float TwilightWidth = 400f;
        /// <summary>Dawn terminator at real second 0.</summary>
        public const float DawnAtStart = 0f;

        /// <summary>World x of the dawn terminator after `realSeconds` (wrapped to 0..width).</summary>
        public static float Dawn(double realSeconds, int width) =>
            Mathf.Repeat(DawnAtStart + (float)(realSeconds / CreepSecondsPerMetre), width);

        /// <summary>Signed distance (m) from the nearest terminator, and whether x lies on the day half.</summary>
        public static MercuryZone ZoneAt(float x, double realSeconds, int width)
        {
            float dawn = Dawn(realSeconds, width);
            float rel = Mathf.Repeat(x - dawn, width);     // 0 at dawn, width/2 at dusk
            float half = width * 0.5f;
            float toNearest = Mathf.Min(Mathf.Min(rel, width - rel), Mathf.Abs(rel - half));
            if (toNearest <= TwilightWidth * 0.5f) return MercuryZone.Twilight;
            // The sun has risen on the stretch behind the dawn line (the creep runs +x, so the day side trails it).
            return rel > half ? MercuryZone.Day : MercuryZone.Night;
        }
    }
}
