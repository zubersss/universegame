using UnityEngine;

namespace Meridian.Terrain
{
    /// <summary>
    /// Mercury's fixed landforms (U-048, Bible §7.3): the two polar cold-trap craters (permanent shadow,
    /// water ice under a thin regolith skin) half a world apart, and seeded smaller craters that give the
    /// surface its pocked look. Positions are fixed per world width; heights are offsets from the fBm surface.
    /// </summary>
    public static class MercuryLandforms
    {
        /// <summary>Cold-trap crater centres as a fraction of the world width (the two "poles").</summary>
        public static readonly float[] ColdTrapAt = { 0.125f, 0.625f };
        public const int ColdTrapHalfWidth = 70;
        public const float ColdTrapDepth = 36f, RimHeight = 6f;
        /// <summary>Ice lies this many metres under the crater floor's regolith skin, this thick.</summary>
        public const int IceSkin = 1, IceThickness = 9;
        /// <summary>D-146: the pad's column (PlanetSideRoot.spawnX's default) and the clear half-width around it: no seeded small crater
        /// reaches within ±PadClear of the pad (its rim fall-off included), so the camp sits on the plain, not in a 9 m bowl.</summary>
        public const int PadX = 64, PadClear = 40;
        /// <summary>A small crater's footprint: its rim falls off out to this many half-widths (Crater's 1.35).</summary>
        const float RimReach = 1.35f;

        public static int ColdTrapCentre(int i, int width) => Mathf.RoundToInt(ColdTrapAt[i] * width);

        /// <summary>Whether column x is inside a cold-trap crater (rim to rim), and which one.</summary>
        public static bool InColdTrap(int x, int width, out int index)
        {
            for (int i = 0; i < ColdTrapAt.Length; i++)
            {
                int d = Wrapped(x - ColdTrapCentre(i, width), width);
                if (Mathf.Abs(d) <= ColdTrapHalfWidth) { index = i; return true; }
            }
            index = -1;
            return false;
        }

        public static bool InColdTrap(int x, int width) => InColdTrap(x, width, out _);

        /// <summary>U-123: column x's signed offset from cold trap i's centre (wrapped). Pure.</summary>
        public static int ColdTrapOffset(int x, int i, int width) => Wrapped(x - ColdTrapCentre(i, width), width);

        /// <summary>U-123: the cold-trap bowls' height alone (no fbm, no small craters) at column x: the painted stage's datum follows it into the craters. Pure.</summary>
        public static float ColdTrapProfile(int x, int width)
        {
            float h = 0f;
            for (int i = 0; i < ColdTrapAt.Length; i++) h += Crater(Wrapped(x - ColdTrapCentre(i, width), width), ColdTrapHalfWidth, ColdTrapDepth, RimHeight);
            return h;
        }

        /// <summary>The crater floor is in permanent shadow: no sun reaches it on any side of the terminator.</summary>
        public static bool PermanentShadow(int x, int width)
        {
            if (!InColdTrap(x, width, out int i)) return false;
            return Mathf.Abs(Wrapped(x - ColdTrapCentre(i, width), width)) <= ColdTrapHalfWidth - 12; // inside the rim walls
        }

        /// <summary>D-146: the band surface — the plain's noise and the cold-trap bowls, without the seeded small craters. The painted stage's
        /// datum follows it (a small crater is a dip in the ground, not a band). Pure.</summary>
        public static float BandHeight(int x, int width, float fbm) => fbm + ColdTrapProfile(x, width);

        /// <summary>Surface height with the craters cut in (`fbm` is the plain surface at x).</summary>
        public static float Height(int x, int width, float fbm, int seed)
        {
            float h = BandHeight(x, width, fbm);
            // Smaller impact craters: one every ~160 m, seeded, 12–30 m across; none reaches the pad (D-146).
            const int Cell = 160;
            int cell = Mathf.FloorToInt(x / (float)Cell);
            for (int c = cell - 1; c <= cell + 1; c++)
            {
                var r = new System.Random(seed ^ (c * 73856093));
                int centre = c * Cell + r.Next(20, Cell - 20);
                int half = r.Next(6, 16);
                if (ReachesPad(centre, half, width)) continue; // D-146: the camp stays on the plain
                float depth = half * 0.6f;
                h += Crater(x - centre, half, depth, depth * 0.25f);
            }
            return h;
        }

        /// <summary>D-146: whether a small crater centred at `centre` (half-width `half`, rim fall-off included) reaches within ±PadClear of the pad. Pure.</summary>
        public static bool ReachesPad(int centre, int half, int width) => Mathf.Abs(Wrapped(centre - PadX, width)) - half * RimReach < PadClear;

        /// <summary>A bowl of half-width `half` and depth `depth` with a raised rim, at offset d from its centre.</summary>
        static float Crater(int d, int half, float depth, float rim)
        {
            float a = Mathf.Abs(d) / (float)half;
            if (a >= 1.35f) return 0f;
            if (a >= 1f) return rim * (1f - (a - 1f) / 0.35f);  // rim falling off outside
            return -depth * (1f - a * a) + rim * a * a * a;      // bowl rising to the rim
        }

        static int Wrapped(int d, int width)
        {
            d %= width;
            if (d > width / 2) d -= width;
            if (d < -width / 2) d += width;
            return d;
        }
    }
}
