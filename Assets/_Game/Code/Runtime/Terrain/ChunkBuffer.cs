using System.Collections.Concurrent;

namespace Meridian.Terrain
{
    /// <summary>
    /// One chunk's generated data: tile ids plus blob sheet indices, filled on a worker thread.
    /// Buffers are pooled so steady-state streaming allocates nothing.
    /// </summary>
    public sealed class ChunkBuffer
    {
        const int C = TerrainConstants.ChunkSize, P = C + 2;

        /// <summary>Unwrapped chunk coordinate (cx may be negative or ≥ width/32; data comes from the wrapped column).</summary>
        public int cx, cy;
        public readonly byte[] ids = new byte[TerrainConstants.TilesPerChunk];
        public readonly byte[] blob = new byte[TerrainConstants.TilesPerChunk];
        readonly byte[] padded = new byte[P * P];

        static readonly ConcurrentBag<ChunkBuffer> Pool = new ConcurrentBag<ChunkBuffer>();

        public static ChunkBuffer Rent(int cx, int cy)
        {
            if (!Pool.TryTake(out var b)) b = new ChunkBuffer();
            b.cx = cx; b.cy = cy;
            return b;
        }

        public static void Return(ChunkBuffer b) => Pool.Add(b);

        public static long Key(int cx, int cy) => ((long)cx << 32) | (uint)cy;

        /// <summary>Generates ids for the chunk and a 1-tile border, then autotile indices. Thread-safe.</summary>
        public void Generate(IWorldGenerator gen)
        {
            int w = gen.Width;
            int x0 = cx * C - 1, y0 = cy * C - 1;
            for (int py = 0; py < P; py++)
            for (int px = 0; px < P; px++)
            {
                int wx = ((x0 + px) % w + w) % w;
                padded[py * P + px] = gen.TileAt(wx, y0 + py);
            }

            for (int y = 0; y < C; y++)
            for (int x = 0; x < C; x++)
            {
                int p = (y + 1) * P + (x + 1);
                byte id = padded[p];
                ids[y * C + x] = id;
                blob[y * C + x] = id == TileId.Air ? (byte)0 : BlobAutotile.Index(Mask(p, id));
            }
        }

        int Mask(int p, byte id)
        {
            bool liquid = TileId.IsLiquid(id);
            int m = 0;
            if (Connects(padded[p + P], liquid)) m |= BlobAutotile.N;
            if (Connects(padded[p + P + 1], liquid)) m |= BlobAutotile.NE;
            if (Connects(padded[p + 1], liquid)) m |= BlobAutotile.E;
            if (Connects(padded[p - P + 1], liquid)) m |= BlobAutotile.SE;
            if (Connects(padded[p - P], liquid)) m |= BlobAutotile.S;
            if (Connects(padded[p - P - 1], liquid)) m |= BlobAutotile.SW;
            if (Connects(padded[p - 1], liquid)) m |= BlobAutotile.W;
            if (Connects(padded[p + P - 1], liquid)) m |= BlobAutotile.NW;
            return m;
        }

        // Solids merge with any solid; liquids merge with liquid and solids.
        internal static bool Connects(byte n, bool liquid) => liquid ? n != TileId.Air : TileId.IsSolid(n);
    }
}
