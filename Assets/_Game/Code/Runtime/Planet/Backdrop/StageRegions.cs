using Meridian.Planets;
using Meridian.Terrain;
using UnityEngine;

namespace Meridian.Planet.Backdrop
{
    /// <summary>
    /// U-090 (Bible §10.10, contract §10): the stage region at a world column and its bounds. Earth's regions are its
    /// biome bands, Mars's its landforms; every other planet is one region for now (its first backdrop set's name),
    /// so all 8 planets run on placeholders before BLENDER's sets land. Pure; safe to call every frame.
    /// </summary>
    public static class StageRegions
    {
        public static string At(PlanetId planet, int x)
        {
            switch (planet)
            {
                case PlanetId.Earth:
                    switch (EarthBiomes.At(x))
                    {
                        case Biome.Plains: return "earth_plains";
                        case Biome.Desert: return "earth_desert";
                        case Biome.Ocean: return "earth_coast";
                        case Biome.Taiga: return "earth_taiga";
                        case Biome.Tundra: return "earth_tundra";
                        default: return "earth_forest";
                    }
                case PlanetId.Mars:
                    switch (MarsLandforms.At(x))
                    {
                        case MarsFeature.PolarCap: return "mars_polar";
                        case MarsFeature.Canyon: return "mars_canyon";
                        case MarsFeature.Olympus: return "mars_tharsis";
                        default: return "mars_plains";
                    }
                case PlanetId.Mercury: return "mercury_day";
                case PlanetId.Venus: return "venus_surface";
                default: return planet.ToString().ToLowerInvariant() + "_deck1";
            }
        }

        /// <summary>The planet part of a region name ("earth_forest" → "earth").</summary>
        public static string PlanetOf(string region)
        {
            int u = region.IndexOf('_');
            return u < 0 ? region : region.Substring(0, u);
        }

        /// <summary>
        /// First column and length of the region containing wrapped column `x`. Earth: the biome band. Mars: scanned
        /// from x in both directions (landforms are contiguous spans). Others: the whole world.
        /// </summary>
        public static void Bounds(PlanetId planet, int width, int x, out int start, out int length)
        {
            x = ((x % width) + width) % width;
            if (planet == PlanetId.Earth)
            {
                EarthBiomes.Range(EarthBiomes.At(x), out start, out length);
                return;
            }
            if (planet == PlanetId.Mars)
            {
                var here = MarsLandforms.At(x);
                int lo = x, hi = x;
                while (lo > x - width && MarsLandforms.At(((lo - 1) % width + width) % width) == here) lo--;
                while (hi < x + width && MarsLandforms.At((hi + 1) % width) == here) hi++;
                start = ((lo % width) + width) % width;
                length = Mathf.Min(width, hi - lo + 1);
                return;
            }
            start = 0; length = width;
        }

        /// <summary>Distance (columns) from wrapped `x` to the nearest border of its region, 0 inside a one-region world... never below 0.</summary>
        public static int DistanceToBorder(PlanetId planet, int width, int x)
        {
            Bounds(planet, width, x, out int start, out int length);
            if (length >= width) return width;
            int d = (((x - start) % width) + width) % width; // columns past the start
            return Mathf.Min(d, length - d);
        }

        /// <summary>The region on the far side of the nearest border: the one the player is walking toward.</summary>
        public static string Neighbour(PlanetId planet, int width, int x)
        {
            Bounds(planet, width, x, out int start, out int length);
            if (length >= width) return null;
            int d = (((x - start) % width) + width) % width;
            int probe = d < length - d ? start - 1 : start + length;
            return At(planet, ((probe % width) + width) % width);
        }
    }
}
