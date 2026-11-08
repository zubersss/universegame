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
            amplitude = planet == PlanetId.Earth ? 28f : planet == PlanetId.Mercury ? 14f : 34f; // Mercury: low rolling plains, craters do the rest
            // The surface profile once per world (U-039 fix: it was recomputed for every tile, ~1.5 s Mars entry).
            surface = new int[width];
            if (planet == PlanetId.Mercury) band = new int[width]; // D-146: filled beside the surface, read-only after (the chunk thread reads too)
            for (int x = 0; x < width; x++) surface[x] = ComputeSurface(x);
            smoothGround = GroundField.Smooth(planet);
            if (smoothGround)
            {
                // U-156 (D-161 / D-162): rolling hills: the raw heights averaged and slope-clamped (≤ 31°), so the hidden grid under the drawn
                // curve never steps more than 1 m between neighbouring columns.
                var raw = new float[width];
                for (int x = 0; x < width; x++) raw[x] = EarthBiomes.Height(x, WorldNoise.Fbm1D(x, width, this.seed), datum);
                var smoothed = GroundField.SmoothSurface(raw, GroundField.SmoothRadius, GroundField.SurfaceSlope);
                for (int x = 0; x < width; x++) surface[x] = Clamp((int)System.Math.Round(smoothed[x]));
                if (planet == PlanetId.Earth) sea = SeaColumns(); // U-166 (D-171)
            }
        }

        /// <summary>U-166 (D-171): on a smooth Earth only the sea holds water: the columns reached from the ocean trench outward, both ways,
        /// while the ground stays under the water line (the shore stops it). An inland basin under the datum is dry ground on the smoothed
        /// curve (it held a lake drawn as faint tiles over the backdrop). Null elsewhere: every column under the datum fills, as before.</summary>
        readonly bool[] sea;

        bool[] SeaColumns()
        {
            var s = new bool[width];
            for (int dir = -1; dir <= 1; dir += 2)
                for (int i = 0, x = EarthBiomes.TrenchCenter; i < width; i++, x += dir)
                {
                    int wx = ((x % width) + width) % width;
                    if (surface[wx] >= datum) break;
                    s[wx] = true;
                }
            return s;
        }

        /// <summary>U-166: column x holds the sea (always true off a smooth Earth).</summary>
        public bool SeaAt(int x) => sea == null || sea[((x % width) + width) % width];

        readonly int[] surface;
        /// <summary>U-156: a smooth planet (D-161): rolling-hill surface, no noise caves (the underground is the drawn cross-section, opened only by digs).</summary>
        readonly bool smoothGround;
        public bool SmoothGround => smoothGround;
        /// <summary>D-146 (Mercury): the band surface per column — the noise and the cold-trap bowls without the seeded small craters.</summary>
        readonly int[] band;

        /// <summary>D-146: the topmost solid tile's y of the band surface at column x (the painted stage's datum source): Mercury without its
        /// seeded small craters; every other planet its SurfaceHeight.</summary>
        public int BandSurfaceHeight(int x) => band != null ? band[((x % width) + width) % width] : SurfaceHeight(x);

        System.Func<int, int> surfaceOf;
        System.Func<int, int> SurfaceOf => surfaceOf ??= c => SurfaceHeight(((c % width) + width) % width);

        public int SurfaceHeight(int x) => surface[((x % width) + width) % width];

        int ComputeSurface(int x)
        {
            float n = WorldNoise.Fbm1D(x, width, seed);
            if (band != null) band[x] = Clamp(datum + (int)MercuryLandforms.BandHeight(x, width, (n - 0.5f) * 2f * amplitude));
            // Earth: biome bands (U-037); the forest band keeps exactly this old offset and truncation.
            int h = planet == PlanetId.Earth
                ? datum + (int)(EarthBiomes.Height(x, n, datum) - datum)
                : planet == PlanetId.Mars
                    ? datum + (int)(MarsLandforms.Height(x, datum + (n - 0.5f) * 2f * amplitude) - datum) // U-039 landforms
                    : planet == PlanetId.Mercury
                        ? datum + (int)(MercuryLandforms.Height(x, width, (n - 0.5f) * 2f * amplitude, seed)) // U-048 craters + cold traps
                        : planet == PlanetId.Venus
                            ? datum + (int)VenusLandforms.Height(x, (n - 0.5f) * 2f * amplitude) // U-050 tesserae + vents
                            : datum + (int)((n - 0.5f) * 2f * amplitude);
            return Clamp(h);
        }

        int Clamp(int h) => h < 1 ? 1 : (h >= height - 1 ? height - 2 : h);

        public byte TileAt(int x, int y)
        {
            if (y >= height) return TileId.Air;
            if (y < 0) return planet == PlanetId.Earth ? TileId.Stone : planet == PlanetId.Mercury ? TileId.MercuryBasalt : planet == PlanetId.Venus ? TileId.VenusBasalt : TileId.Basalt;

            int surface = SurfaceHeight(x);
            if (y > surface)
                return planet == PlanetId.Earth && y <= datum && SeaAt(x) ? TileId.Water : TileId.Air; // U-166: no inland lakes on the smooth ground

            if (planet == PlanetId.Mars && MarsLandforms.InTube(x, y, SurfaceOf)) return TileId.Air; // lava tubes (U-039)
            int depth = surface - y;
            // Random caves; inside Mars landforms only rare small pockets (U-039 fix: no Swiss-cheese walls).
            float caveCut = planet == PlanetId.Mars && MarsLandforms.At(x) != MarsFeature.Plains ? 0.9f : 0.72f;
            if (!smoothGround && depth > 6 && y > 2 && WorldNoise.Value2D(x, y, 16, width, seed + 101) > caveCut
                && !(planet == PlanetId.Mars && MarsLandforms.NearTube(x, y, SurfaceOf, 2))
                && !(planet == PlanetId.Mercury && depth < MercuryLandforms.IceSkin + MercuryLandforms.IceThickness + 1 && MercuryLandforms.PermanentShadow(x, width))) return TileId.Air; // keep cold-trap ice whole

            if (planet == PlanetId.Earth) return EarthMaterial(x, y, surface, depth);
            if (planet == PlanetId.Mercury) return MercuryMaterial(x, y, depth);
            if (planet == PlanetId.Venus) return VenusLandforms.Material(x, depth, WorldNoise.Value2D(x, y, 6, width, seed + 401));
            return planet == PlanetId.Mars ? MarsMaterial(x, y, depth) : RockyMaterial(x, y, depth);
        }

        byte EarthMaterial(int x, int y, int surface, int depth)
        {
            var biome = EarthBiomes.At(x);
            bool shore = surface <= datum + 1;
            switch (biome)
            {
                case Biome.Desert: return depth < 8 ? TileId.Sand : TileId.Stone;
                case Biome.Ocean: return depth < 5 ? TileId.Sand : TileId.Stone;
                case Biome.Tundra:
                    if (depth == 0) return TileId.Snow;
                    return depth < 4 ? TileId.Soil : TileId.Stone;
            }
            // Forest, plains, taiga: grass over soil over stone; sandy shores; snow only on high peaks.
            if (shore && depth < 4) return TileId.Sand;
            if (depth == 0) return surface > datum + 40 ? TileId.Snow : TileId.Grass;
            if (depth < 5) return TileId.Soil;
            return TileId.Stone;
        }

        byte MarsMaterial(int x, int y, int depth)
        {
            switch (MarsLandforms.At(x))
            {
                case MarsFeature.PolarCap: // CO₂ frost over water ice
                    if (depth < 2) return TileId.Snow;
                    return depth < 10 ? TileId.Ice : TileId.Basalt;
                case MarsFeature.Canyon: // layered walls: basalt with hematite-rich bands every 5 m
                    if (depth < 2) return TileId.Regolith;
                    return ((y / 5) % 3) == 1 ? TileId.Hematite : TileId.Basalt;
                case MarsFeature.Olympus: // a thin regolith skin over lava
                    return depth < 2 ? TileId.Regolith : TileId.Basalt;
            }
            return RockyMaterial(x, y, depth);
        }

        /// <summary>Mercury (U-048, B-027): regolith over basalt with sulfide veins; cold-trap floors hold water ice under a thin skin.</summary>
        byte MercuryMaterial(int x, int y, int depth)
        {
            if (MercuryLandforms.PermanentShadow(x, width))
            {
                if (depth < MercuryLandforms.IceSkin) return TileId.MercuryRegolith;
                if (depth < MercuryLandforms.IceSkin + MercuryLandforms.IceThickness) return TileId.MercuryIce;
            }
            if (depth < 3) return TileId.MercuryRegolith;
            if (depth > 6 && WorldNoise.Value2D(x, y, 8, width, seed + 211) > 0.80f) return TileId.Sulfide;
            return TileId.MercuryBasalt;
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
