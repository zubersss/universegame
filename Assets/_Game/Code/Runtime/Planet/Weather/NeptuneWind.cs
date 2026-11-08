using UnityEngine;

namespace Meridian.Planet.Weather
{
    /// <summary>
    /// U-133 (Bible §7.9, D-148): Neptune's wind. A lateral wind of 8–20 m/s that swells slowly and gusts to 35 m/s in short windows, blowing +x
    /// over the column's first half and −x over its second (U-144: the −x zone mirrors its deck layers, floes and lean). The flora's root bones lean
    /// by it through one controller (FloraRigs.leanDegrees): 0° at calm to MaxLean at GustPeak, mirrored for −x wind, a stepped shiver at ShiverHz
    /// in a gust. U-144: the surveyor drifts DriftScale × the wind, nothing in the lee of a solid within ShelterReach or while holding a wind anchor.
    /// Pure; t is real seconds.
    /// </summary>
    public static class NeptuneWind
    {
        public const float CalmMin = 8f, CalmMax = 20f, GustPeak = 35f;
        public const float SwellSeconds = 97f, GustEvery = 23f, GustSeconds = 4f;
        public const float MaxLean = 25f, ShiverHz = 12f, ShiverDegrees = 1.5f;

        public const float DriftScale = 0.12f;
        public const int ShelterReach = 3, ZoneHold = 20;

        /// <summary>U-144: the wind's direction at column x: +1 (the drawing's +x) over the column's first half, −1 over its second.</summary>
        public static int Direction(int x)
        {
            int w = Meridian.Terrain.CloudColumn.CloudLayout.Width;
            int wx = ((x % w) + w) % w;
            return wx < w / 2 ? 1 : -1;
        }

        /// <summary>The direction for a view at column x given the one shown now (0: none): it holds ZoneHold columns past a zone's border.</summary>
        public static int DirectionFor(int x, int current)
        {
            if (current != 0 && (Direction(x - ZoneHold) == current || Direction(x + ZoneHold) == current)) return current;
            return Direction(x);
        }

        /// <summary>U-144: the surveyor's drift (m/s, signed) in a signed wind: DriftScale × the wind, none when sheltered or anchored.</summary>
        public static float Drift(float wind, bool sheltered, bool anchored) => sheltered || anchored ? 0f : DriftScale * wind;

        /// <summary>U-144: in the lee: a solid block at body height (the feet's row or the one above) within ShelterReach columns upwind.</summary>
        public static bool Sheltered(System.Func<int, int, bool> solid, Vector2 feet, int windDir)
        {
            if (windDir == 0 || solid == null) return false;
            int px = Mathf.FloorToInt(feet.x), py = Mathf.FloorToInt(feet.y);
            for (int k = 1; k <= ShelterReach; k++)
            {
                int x = px - windDir * k;
                if (solid(x, py) || solid(x, py + 1)) return true;
            }
            return false;
        }

        /// <summary>D-157 (c): the drawn surveyor leans into the wind: SurveyorSwell of the flora's steady lean in the swell, SurveyorGust in a gust
        /// (no shiver), none while anchored; positive z tips the head toward −x, so a +x wind leans the surveyor back toward it. Pure.</summary>
        public const float SurveyorSwell = 0.4f, SurveyorGust = 0.6f;
        public static float SurveyorLean(float wind, bool gusting, bool anchored) => anchored ? 0f : -(gusting ? SurveyorGust : SurveyorSwell) * Lean(wind, false, 0);

        /// <summary>U-144: seconds until the next gust (0 while one blows): the HUD's warning.</summary>
        public static float SecondsToGust(double t) => Gusting(t) ? 0f : (float)(GustEvery - Mod(t, GustEvery));

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
