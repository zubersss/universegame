using Meridian.Planets;

namespace Meridian.Terrain.CloudColumn
{
    /// <summary>
    /// U-061: the giants' world (Bible §7.5, D-004) behind the same IWorldGenerator as the solid worlds, so the
    /// terrain streamer, edits, saves and digging work unchanged. Tiles come from CloudLayout (pure, O(1) per tile,
    /// thread-safe). "Surface" for spawning is the top of the highest floe in the column below the Datum (or the
    /// Datum itself when the column holds none: the ship hovers there).
    /// </summary>
    public sealed class CloudWorldGenerator : IWorldGenerator
    {
        readonly int seed;

        public CloudWorldGenerator(PlanetConfig config, int seed)
        {
            this.seed = seed;
            Width = config != null && config.worldWidth > 0 ? config.worldWidth : CloudLayout.Width;
            Height = config != null && config.worldHeight > 0 ? config.worldHeight : CloudLayout.Height;
        }

        public int Width { get; }
        public int Height { get; }

        public byte TileAt(int x, int y) => CloudLayout.TileAt(x, y, seed);

        /// <summary>U-153: this world's seed (the floes' slots: GroundStrip lays each floe's strip from them).</summary>
        public int Seed => seed;

        /// <summary>U-153: the standing height of the floe nearest under (x, y), over minY (CloudLayout.FloeTopUnder with this world's seed).</summary>
        public bool FloeTopUnder(float x, float y, float minY, out float top) => CloudLayout.FloeTopUnder(x, y, minY, seed, out top);

        public int SurfaceHeight(int x)
        {
            int wx = ((x % CloudLayout.Width) + CloudLayout.Width) % CloudLayout.Width;
            int sx = wx / CloudLayout.SlotW;
            // Slots from the Datum down: the first floe covering this column is the highest one.
            for (int sy = (CloudLayout.Datum - 1) / CloudLayout.SlotH; sy >= 0; sy--)
            {
                if (!CloudLayout.FloeInSlot(sx, sy, seed, out var f)) continue;
                if (wx < f.x || wx >= f.x + f.width) continue;
                return f.y + f.height - 1;
            }
            return CloudLayout.Datum;
        }
    }
}
