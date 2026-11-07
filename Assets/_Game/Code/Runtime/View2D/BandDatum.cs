using Meridian.Planets;
using Meridian.Terrain;
using UnityEngine;

namespace Meridian.View2D
{
    /// <summary>
    /// U-128: the painted stage's datum per band. Until now the layers sat at the spawn's surface everywhere, so the coast (16 m
    /// under the camp) showed nothing behind the Maw. Here each band has its own datum — Earth's biome bands their mean surface
    /// (EarthBiomes.MeanSurface; the Ocean band its water line), Mars's landforms their profile (the canyon floor, the shield's mid
    /// slope, the cap's rise) — blended across the ±Blend-column borders exactly as the heights blend, and the spawn's own band keeps
    /// the measured spawn surface (the stamped camp), so the camp frames do not move. U-123: Mercury's plain is one band at the pad's surface and each cold
    /// trap follows its bowl (MercuryLandforms.ColdTrapProfile) from the rim in. One delegate per instance; At allocates nothing.
    /// </summary>
    public sealed class BandDatum
    {
        public const int Blend = EarthBiomes.Blend;
        public readonly PlanetId planet;
        public readonly float planetDatum, spawnSurface;
        public readonly int spawnX;
        /// <summary>U-123: the world width (Mercury's cold traps wrap); 0 when unknown — then Mercury is flat at the spawn surface.</summary>
        public readonly int worldWidth;
        readonly Biome spawnBand;
        readonly MarsFeature spawnFeature;
        readonly System.Func<Biome, float> earth;
        readonly System.Func<MarsFeature, float> mars;

        public BandDatum(PlanetId planet, float planetDatum, int spawnX, float spawnSurface, int worldWidth = 0)
        {
            this.planet = planet; this.planetDatum = planetDatum; this.spawnX = spawnX; this.spawnSurface = spawnSurface; this.worldWidth = worldWidth;
            spawnBand = EarthBiomes.At(spawnX);
            spawnFeature = MarsLandforms.At(spawnX);
            earth = EarthValue;
            mars = MarsValue;
        }

        float EarthValue(Biome b) => b == spawnBand ? spawnSurface : EarthBiomes.MeanSurface(b, planetDatum);
        float MarsValue(MarsFeature f) => f == spawnFeature ? spawnSurface : MarsLandforms.MeanSurface(f, planetDatum);

        /// <summary>The stage datum at column x (unwrapped). No allocation.</summary>
        public float At(int x)
        {
            switch (planet)
            {
                case PlanetId.Earth: return EarthBiomes.Blended(x, earth);
                case PlanetId.Mars: return MarsLandforms.Blended(x, Blend, mars);
                case PlanetId.Mercury: return MercuryAt(x);
                default: return spawnSurface;
            }
        }

        /// <summary>U-123: Mercury's plain keeps the spawn's measured surface (the pad is on the plain); inside a cold trap the datum follows the bowl
        /// (planetDatum + the crater profile), blended in from the rim over Blend columns, so the stage drops into the crater with the ground.</summary>
        float MercuryAt(int x)
        {
            if (worldWidth <= 0 || !MercuryLandforms.InColdTrap(x, worldWidth, out int i)) return spawnSurface;
            int d = Mathf.Abs(MercuryLandforms.ColdTrapOffset(x, i, worldWidth));
            float t = Mathf.Clamp01((MercuryLandforms.ColdTrapHalfWidth - d) / (float)Blend);
            return Mathf.Lerp(spawnSurface, planetDatum + MercuryLandforms.ColdTrapProfile(x, worldWidth), t);
        }
    }
}
