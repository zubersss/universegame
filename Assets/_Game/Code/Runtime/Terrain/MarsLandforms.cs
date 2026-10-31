using UnityEngine;

namespace Meridian.Terrain
{
    public enum MarsFeature { Plains, PolarCap, Canyon, Olympus }

    /// <summary>
    /// U-039 Mars landforms (Bible §7.2), scaled into the 3072 × 640 world (P-22): Valles Marineris
    /// (600 columns, 160 m deep, walls terraced in 5 m steps with ~4-column ledges: jumpable at Mars g,
    /// v₀²/2g = 6.6 m), Olympus Mons (660 columns, 220 m tall so the summit stays 30 m under the
    /// Escape Line at Datum + 250, with a caldera), the polar cap at the world seam (CO₂ frost over
    /// water ice), and three lava tubes (4 m tall tunnels 14–16 m down, each with a skylight; natural
    /// radiation shelters for M3). Positions are fixed so they never cover the Mars POIs (hauler x 900,
    /// Warden outpost x 2000); the rock between them comes from the world seed. Pure, thread-safe.
    /// </summary>
    public static class MarsLandforms
    {
        public const int Width = 3072;

        public const int CanyonStart = 1150, CanyonEnd = 1750, CanyonWall = 128;
        public const float CanyonDepth = 160f, LedgeStep = 5f;

        public const int OlympusCenter = 2420, OlympusHalfWidth = 330, CalderaHalfWidth = 36;
        public const float OlympusHeight = 220f, CalderaDepth = 35f;

        /// <summary>The cap spans the seam: 2860..3071 and 0..211.</summary>
        public const int CapHalfWidth = 212;
        public const float CapRise = 8f;

        /// <summary>Lava tubes: first column, last column, depth of the ceiling below the surface at the tube's middle.</summary>
        public static readonly (int x0, int x1, int depth)[] Tubes = { (300, 470, 14), (580, 760, 16), (1850, 1980, 15) };
        public const int TubeHeight = 4, SkylightWidth = 2, SkylightInset = 12;

        static int Wrap(int x) => ((x % Width) + Width) % Width;

        public static MarsFeature At(int x)
        {
            x = Wrap(x);
            if (x < CapHalfWidth || x >= Width - CapHalfWidth) return MarsFeature.PolarCap;
            if (x >= CanyonStart && x < CanyonEnd) return MarsFeature.Canyon;
            if (Mathf.Abs(x - OlympusCenter) < OlympusHalfWidth) return MarsFeature.Olympus;
            return MarsFeature.Plains;
        }

        /// <summary>Surface height of column x from the plain's height `plain` (Datum + seed noise).</summary>
        public static float Height(int x, float plain)
        {
            x = Wrap(x);
            switch (At(x))
            {
                case MarsFeature.Canyon:
                {
                    int d = Mathf.Min(x - CanyonStart, CanyonEnd - 1 - x); // columns in from the nearer rim
                    float target = CanyonDepth * Mathf.Clamp01(d / (float)CanyonWall);
                    float terraced = Mathf.Floor(target / LedgeStep) * LedgeStep; // flat ledges, 5 m risers
                    return plain - terraced;
                }
                case MarsFeature.Olympus:
                {
                    float r = Mathf.Abs(x - OlympusCenter) / (float)OlympusHalfWidth;   // 0 summit … 1 foot
                    float shield = OlympusHeight * Smooth(1f - r);                      // broad, gentle shield
                    float rc = Mathf.Abs(x - OlympusCenter) / (float)CalderaHalfWidth;
                    float caldera = rc < 1f ? CalderaDepth * Smooth(1f - rc) : 0f;
                    return plain + shield - caldera;
                }
                case MarsFeature.PolarCap:
                {
                    int d = Mathf.Min(x, Width - x); // columns from the seam
                    return plain + CapRise * Smooth(1f - d / (float)CapHalfWidth);
                }
            }
            return plain;
        }

        /// <summary>Whether (x, y) is inside a lava tube (air; Radiation 0 there in M3). `surfaceAtMiddle(x)` gives a column's surface.</summary>
        public static bool InTube(int x, int y, System.Func<int, int> surfaceAt)
        {
            x = Wrap(x);
            foreach (var t in Tubes)
            {
                if (x < t.x0 || x > t.x1) continue;
                int ceiling = TubeCeiling(t, surfaceAt);
                if (y <= ceiling && y > ceiling - TubeHeight) return true;
                // Skylight: a shaft from the surface down into the tube near its west end.
                if (x >= t.x0 + SkylightInset && x < t.x0 + SkylightInset + SkylightWidth && y > ceiling - TubeHeight && y <= surfaceAt(x)) return true;
            }
            return false;
        }

        /// <summary>Within `margin` tiles of a tube's walls: random caves keep out, so tubes stay whole shelters.</summary>
        public static bool NearTube(int x, int y, System.Func<int, int> surfaceAt, int margin)
        {
            x = Wrap(x);
            foreach (var t in Tubes)
            {
                if (x < t.x0 - margin || x > t.x1 + margin) continue;
                int ceiling = TubeCeiling(t, surfaceAt);
                if (y <= ceiling + margin && y > ceiling - TubeHeight - margin) return true;
            }
            return false;
        }

        public static int TubeCeiling((int x0, int x1, int depth) t, System.Func<int, int> surfaceAt) =>
            surfaceAt((t.x0 + t.x1) / 2) - t.depth;

        static float Smooth(float k) { k = Mathf.Clamp01(k); return k * k * (3f - 2f * k); }
    }
}
