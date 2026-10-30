namespace Meridian.Terrain
{
    /// <summary>
    /// Deterministic, allocation-free value noise. Lattices are periodic in x so the world wraps
    /// (Bible §5.1) when the period divides the planet width.
    /// </summary>
    public static class WorldNoise
    {
        public static float Hash(int x, int y, int seed)
        {
            unchecked
            {
                uint h = (uint)seed * 0x9E3779B1u;
                h ^= (uint)x * 0x85EBCA6Bu;
                h = (h << 13) | (h >> 19);
                h ^= (uint)y * 0xC2B2AE35u;
                h *= 0x27D4EB2Fu;
                h ^= h >> 15;
                h *= 0x165667B1u;
                h ^= h >> 13;
                return (h & 0xFFFFFF) / 16777216f;
            }
        }

        static int Wrap(int i, int period) => ((i % period) + period) % period;

        static float Smooth(float t) => t * t * (3f - 2f * t);

        /// <summary>1D value noise in [0,1), cell size `cell`, repeating every `period` tiles.</summary>
        public static float Value1D(int x, int cell, int period, int seed)
        {
            int cells = period / cell;
            int i = FloorDiv(x, cell);
            float t = Smooth((x - i * cell) / (float)cell);
            float a = Hash(Wrap(i, cells), 0, seed), b = Hash(Wrap(i + 1, cells), 0, seed);
            return a + (b - a) * t;
        }

        /// <summary>2D value noise in [0,1), periodic in x.</summary>
        public static float Value2D(int x, int y, int cell, int period, int seed)
        {
            int cells = period / cell;
            int ix = FloorDiv(x, cell), iy = FloorDiv(y, cell);
            float tx = Smooth((x - ix * cell) / (float)cell), ty = Smooth((y - iy * cell) / (float)cell);
            int x0 = Wrap(ix, cells), x1 = Wrap(ix + 1, cells);
            float a = Hash(x0, iy, seed), b = Hash(x1, iy, seed);
            float c = Hash(x0, iy + 1, seed), d = Hash(x1, iy + 1, seed);
            float top = a + (b - a) * tx, bottom = c + (d - c) * tx;
            return top + (bottom - top) * ty;
        }

        /// <summary>Four octaves (cells 128, 64, 32, 16), normalized to [0,1).</summary>
        public static float Fbm1D(int x, int period, int seed)
        {
            float sum = 0f, amp = 1f, norm = 0f;
            for (int cell = 128; cell >= 16; cell /= 2)
            {
                sum += Value1D(x, cell, period, seed + cell) * amp;
                norm += amp;
                amp *= 0.5f;
            }
            return sum / norm;
        }

        public static int FloorDiv(int a, int b) => a >= 0 ? a / b : (a - b + 1) / b;
    }
}
