using UnityEngine;

namespace Meridian.Planet.Weather
{
    /// <summary>
    /// U-133 (Bible §7.9, D-148): Neptune's wind as the stage reads it. A lateral wind of 8–20 m/s that swells slowly, gusts to 35 m/s in short
    /// windows, blowing +x (the drawing's direction; the −x zones and their mirrored layers are a later slice). The flora's root bones lean by it
    /// through one controller (FloraRigs.leanDegrees): 0° at calm to MaxLean at GustPeak, mirrored for −x wind, a stepped shiver at ShiverHz in a gust.
    /// Pure; t is real seconds. The player's drift and the build gate (wind anchors) are their own cards.
    /// </summary>
    public static class NeptuneWind
    {
        public const float CalmMin = 8f, CalmMax = 20f, GustPeak = 35f;
        public const float SwellSeconds = 97f, GustEvery = 23f, GustSeconds = 4f;
        public const float MaxLean = 25f, ShiverHz = 12f, ShiverDegrees = 1.5f;

        /// <summary>The wind's direction at column x: +1 everywhere for now (the drawing's +x).</summary>
        public static int Direction(int x) => 1;

        /// <summary>Whether a gust is blowing at t (a GustSeconds window every GustEvery seconds).</summary>
        public static bool Gusting(double t) => Mod(t, GustEvery) < GustSeconds;

        /// <summary>The wind's speed (m/s, unsigned) at t: the slow swell between CalmMin and CalmMax, lifted toward GustPeak in a gust.</summary>
        public static float Speed(double t)
        {
            float swell = Mathf.Lerp(CalmMin, CalmMax, 0.5f + 0.5f * Mathf.Sin((float)(Mod(t, SwellSeconds) / SwellSeconds * 2.0 * System.Math.PI)));
            if (!Gusting(t)) return swell;
            float k = Mathf.Sin((float)(Mod(t, GustEvery) / GustSeconds * System.Math.PI)); // 0 → 1 → 0 across the window
            return Mathf.Lerp(swell, GustPeak, k);
        }

        /// <summary>The signed wind (m/s, +x positive) at column x and time t.</summary>
        public static float At(int x, double t) => Direction(x) * Speed(t);

        /// <summary>The root bone's lean (z degrees; negative tips the top toward +x) for a signed wind: 0 at calm, −MaxLean at +GustPeak, mirrored for
        /// −x; in a gust a stepped shiver of ±ShiverDegrees flips every 1 / ShiverHz s on top. Pure.</summary>
        public static float Lean(float wind, bool gusting, double t)
        {
            float lean = -MaxLean * Mathf.Clamp(wind / GustPeak, -1f, 1f);
            if (!gusting) return lean;
            long step = (long)System.Math.Floor(t * ShiverHz);
            return lean + ((step & 1) == 0 ? ShiverDegrees : -ShiverDegrees);
        }

        static double Mod(double t, double m) { double r = t % m; return r < 0 ? r + m : r; }
    }

    /// <summary>
    /// U-133 (Bible §7.9): Neptune's Dark Storm zones, 400 m wide. One storm drifts along the column (StormDrift m/s of game time at the
    /// TimeSystem's rate); the Great Dark Spot, where the Meridian lies, stays put. The stage shows B-161's storm set inside a storm and the spot set
    /// inside the Spot (both share their layers 1–2). Pure. The inward pull is a hazard card's.
    /// </summary>
    public static class NeptuneStorms
    {
        public const int HalfWidth = 200;
        public const int StormStart = 1024, DarkSpotCentre = 3072;
        public const float StormDrift = 0.5f;

        static int Offset(int x, int centre, int width)
        {
            if (width <= 0) return x - centre;
            int d = ((x - centre) % width + width) % width;
            return d > width / 2 ? d - width : d;
        }

        /// <summary>The drifting storm's centre column at game time t (game seconds).</summary>
        public static int StormCentre(double t, int width)
        {
            double realSeconds = t / Meridian.Core.TimeSystem.GameSecondsPerRealSecond;
            long c = StormStart + (long)System.Math.Floor(StormDrift * realSeconds);
            return width > 0 ? (int)(((c % width) + width) % width) : (int)c;
        }

        /// <summary>Whether column x lies within the drifting storm (widened by hold columns, for a set already showing it).</summary>
        public static bool InStorm(int x, double t, int width, int hold = 0) => Mathf.Abs(Offset(x, StormCentre(t, width), width)) <= HalfWidth + hold;

        /// <summary>Whether column x lies within the Great Dark Spot (widened by hold columns).</summary>
        public static bool InDarkSpot(int x, int width, int hold = 0) => Mathf.Abs(Offset(x, DarkSpotCentre, width)) <= HalfWidth + hold;
    }
}
