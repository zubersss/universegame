using UnityEngine;

namespace Meridian.Terrain
{
    public enum Biome { Forest, Plains, Desert, Ocean, Taiga, Tundra }

    /// <summary>
    /// U-037 Earth biomes v1 (Bible §7.1): longitude bands, fixed so the spawn (x 64) and the Survey
    /// Archive sit in temperate forest and the launch complex (x 2048) on the coast; the terrain inside
    /// each band comes from the world seed. Heights blend over ±48 columns at every border, so no step is
    /// taller than 3 tiles. The ocean slopes from the shore to a shelf and has a trench ~245 m below sea
    /// level (D-010: water to depth 250). Pure functions, safe on the chunk worker thread.
    /// </summary>
    public static class EarthBiomes
    {
        public const int Width = 4096;
        public const int Blend = 48;
        public const int TrenchCenter = 2490, TrenchHalfWidth = 230;
        public const float TrenchDepth = 245f, ShelfDepth = 60f;

        // Band starts in order around the world; each band ends where the next begins (wraps at 4096).
        static readonly int[] Starts = { 3900, 700, 1300, 2080, 2900, 3400 };
        static readonly Biome[] Kinds = { Biome.Forest, Biome.Plains, Biome.Desert, Biome.Ocean, Biome.Taiga, Biome.Tundra };

        static int Wrap(int x) => ((x % Width) + Width) % Width;

        /// <summary>Band index and distances (columns) to its start and to its end.</summary>
        static int Band(int x, out int fromStart, out int toEnd)
        {
            x = Wrap(x);
            for (int i = 0; i < Starts.Length; i++)
            {
                int s = Starts[i], e = Starts[(i + 1) % Starts.Length];
                int len = Wrap(e - s), d = Wrap(x - s);
                if (d < len) { fromStart = d; toEnd = len - d; return i; }
            }
            fromStart = toEnd = Width;
            return 0;
        }

        public static Biome At(int x) => Kinds[Band(x, out _, out _)];

        /// <summary>First column and length of a biome's band (for tests and captures).</summary>
        public static void Range(Biome b, out int start, out int length)
        {
            int i = System.Array.IndexOf(Kinds, b);
            start = Starts[i];
            length = Wrap(Starts[(i + 1) % Starts.Length] - start);
        }

        /// <summary>Surface height of column x, blended across band borders. `n` is the seed's fBm at x (0..1).</summary>
        public static float Height(int x, float n, int datum)
        {
            int i = Band(x, out int fromStart, out int toEnd);
            float h = Raw(Kinds[i], x, n, datum, fromStart, toEnd);
            if (fromStart < Blend)
            {
                int p = (i + Kinds.Length - 1) % Kinds.Length;
                float other = Raw(Kinds[p], x, n, datum, int.MaxValue / 2, 0);
                h = Mathf.Lerp(other, h, Smooth(0.5f + 0.5f * fromStart / Blend));
            }
            else if (toEnd < Blend)
            {
                int q = (i + 1) % Kinds.Length;
                float other = Raw(Kinds[q], x, n, datum, 0, int.MaxValue / 2);
                h = Mathf.Lerp(other, h, Smooth(0.5f + 0.5f * toEnd / Blend));
            }
            return h;
        }

        static float Raw(Biome b, int x, float n, int datum, int fromStart, int toEnd)
        {
            switch (b)
            {
                case Biome.Forest: return datum + (n - 0.5f) * 56f;      // the U-007 Earth surface, unchanged around spawn
                case Biome.Plains: return datum + 6f + (n - 0.5f) * 14f;
                case Biome.Desert: return datum + 8f + (n - 0.5f) * 16f + 4f * Mathf.Sin(x * (2f * Mathf.PI / 41f));
                case Biome.Taiga: return datum + 18f + (n - 0.5f) * 36f;
                case Biome.Tundra: return datum + 22f + (n - 0.5f) * 18f;
                case Biome.Ocean:
                {
                    // Shore down to the shelf over ~120 columns from either coast, then the trench.
                    float coast = Mathf.Min(fromStart, toEnd);
                    float shelf = -4f - (ShelfDepth - 4f) * Smooth(Mathf.Clamp01(coast / 120f));
                    float t = Mathf.Clamp01(1f - Mathf.Abs(Wrap(x) - TrenchCenter) / (float)TrenchHalfWidth);
                    float trench = (TrenchDepth - ShelfDepth) * Smooth(t);
                    return datum + shelf - trench + (n - 0.5f) * 8f;
                }
            }
            return datum;
        }

        static float Smooth(float k) => k * k * (3f - 2f * k);
    }
}
