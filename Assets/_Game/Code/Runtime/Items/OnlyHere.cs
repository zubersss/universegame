using Meridian.Planets;
using Meridian.Terrain;

namespace Meridian.Items
{
    /// <summary>
    /// U-059: each inner planet's "only here" resource (Bible §7, M3 exit) and where the Beam finds it. Pure.
    /// Mercury Solarite comes from the flare-fused crystals (SolariteCrystals) inside the window after a flare;
    /// Venus Vitriol Glass is its own tile (vent glass, U-050); Mars Perchlorate replaces regolith in salt
    /// deposits near the surface (plains regolith, polar-cap ice); Earth Living Seed turns up when turf is
    /// dug in forest and plains. Wormplate (Tharsis Worm, M4+) is registered with no source yet.
    /// </summary>
    public static class OnlyHere
    {
        /// <summary>Perchlorate deposits: patches DepositWidth columns wide, in the top DepositDepth tiles.</summary>
        public const int DepositWidth = 6, DepositDepth = 3;
        public const float DepositShare = 0.22f;
        /// <summary>One turf tile in this many yields a Living Seed (forest and plains).</summary>
        public const int SeedOneIn = 6;
        /// <summary>Solarite stays harvestable for this long after a flare ends (Bible §7.3).</summary>
        public const float SolariteWindow = 90f;

        /// <summary>The resource only this planet has (its item key).</summary>
        public static string KeyFor(PlanetId p) => p switch
        {
            PlanetId.Mercury => "solarite",
            PlanetId.Venus => "vitriol_glass",
            PlanetId.Mars => "perchlorate",
            PlanetId.Earth => "living_seed",
            _ => null,
        };

        public static bool SolariteHarvestable(float secondsSinceFlareEnded) =>
            secondsSinceFlareEnded >= 0f && secondsSinceFlareEnded <= SolariteWindow;

        public static bool InPerchlorateDeposit(int x)
        {
            var f = MarsLandforms.At(x);
            if (f != MarsFeature.Plains && f != MarsFeature.PolarCap) return false;
            int patch = FloorDiv(x, DepositWidth);
            return Hash01(patch, 71) < DepositShare;
        }

        /// <summary>
        /// What the Beam yields for `tile` dug at (x, y), `depth` tiles under the surface: the item replacing
        /// the tile's own drop (0: the usual drop), and a bonus item on top (0: none).
        /// </summary>
        public static (int replace, int bonus) DropAt(PlanetId planet, byte tile, int x, int y, int depth)
        {
            // Plains: in the top regolith. The polar cap: in the water ice just under its two tiles of CO₂ frost.
            bool host = (tile == TileId.Regolith && depth < DepositDepth)
                || (tile == TileId.Ice && depth < DepositDepth + 2 && MarsLandforms.At(x) == MarsFeature.PolarCap);
            if (planet == PlanetId.Mars && host && InPerchlorateDeposit(x))
                return (Id("perchlorate"), 0);
            if (planet == PlanetId.Earth && tile == TileId.Grass)
            {
                var b = EarthBiomes.At(x);
                if ((b == Biome.Forest || b == Biome.Plains) && Hash01(x * 92821 + y, 13) < 1f / SeedOneIn)
                    return (0, Id("living_seed"));
            }
            return (0, 0);
        }

        static int Id(string key) => ItemRegistry.Get(key)?.id ?? 0;

        static int FloorDiv(int a, int b) => a >= 0 ? a / b : (a + 1) / b - 1;

        static float Hash01(int k, int salt)
        {
            unchecked
            {
                uint h = (uint)k * 0x9E3779B1u ^ (uint)salt * 0x85EBCA77u;
                h ^= h >> 15; h *= 0x2C1B3C6Du; h ^= h >> 12; h *= 0x297A2D39u; h ^= h >> 15;
                return (h & 0xFFFFFF) / (float)0x1000000;
            }
        }
    }
}
