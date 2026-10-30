using Meridian.Planets;

namespace Meridian.Terrain
{
    /// <summary>
    /// Solid-surface worlds (Earth, Mars, Mercury, Venus): an fBm surface around the Datum,
    /// material bands by depth, noise caves and ore pockets. Earth fills below sea level with water.
    /// </summary>
    public sealed class SolidWorldGenerator : IWorldGenerator
    {
        readonly int width, height, datum, seed;
        readonly PlanetId planet;
        readonly float amplitude;

        public int Width => width;
        public int Height => height;

        public SolidWorldGenerator(PlanetConfig config, int seed)
        {
            width = config.worldWidth;
            height = config.worldHeight;
            datum = config.datumY;
            planet = config.id;
            this.seed = seed ^ ((int)config.id * 7919);
            amplitude = planet == PlanetId.Earth ? 28f : 34f;
        }

        public int SurfaceHeight(int x)
        {
            float n = WorldNoise.Fbm1D(x, width, seed);
            int h = datum + (int)((n - 0.5f) * 2f * amplitude);
            return h < 1 ? 1 : (h >= height - 1 ? height - 2 : h);
        }

        public byte TileAt(int x, int y)
        {
            if (y >= height) return TileId.Air;
            if (y < 0) return planet == PlanetId.Earth ? TileId.Stone : TileId.Basalt;

            int surface = SurfaceHeight(x);
            if (y > surface)
                return planet == PlanetId.Earth && y <= datum ? TileId.Water : TileId.Air;

            int depth = surface - y;
            if (depth > 6 && y > 2 && WorldNoise.Value2D(x, y, 16, width, seed + 101) > 0.72f) return TileId.Air;

            return planet == PlanetId.Earth ? EarthMaterial(x, y, surface, depth) : RockyMaterial(x, y, depth);
        }

        byte EarthMaterial(int x, int y, int surface, int depth)
        {
            bool shore = surface <= datum + 1;
            if (shore && depth < 4) return TileId.Sand;
            if (depth == 0) return surface > datum + 20 ? TileId.Snow : TileId.Grass;
            if (depth < 5) return TileId.Soil;
            return TileId.Stone;
        }

        byte RockyMaterial(int x, int y, int depth)
        {
            if (depth < 3) return TileId.Regolith;
            if (depth > 8 && WorldNoise.Value2D(x, y, 8, width, seed + 211) > 0.80f) return TileId.Hematite;
            if (depth > 20 && WorldNoise.Value2D(x, y, 8, width, seed + 307) > 0.82f) return TileId.Ice;
            return TileId.Basalt;
        }
    }
}
