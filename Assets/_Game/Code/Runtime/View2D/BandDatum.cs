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
        /// <summary>D-146: the generator's band surface at a column as a stage datum (SolidWorldGenerator.BandSurfaceHeight + 1: where feet
        /// stand); null in pure tests — then Mercury falls back to the spawn surface and the nominal bowl.</summary>
        readonly System.Func<int, float> bandSurface;
        /// <summary>D-146 (Mercury): the plain's datum — the band surface at the spawn column without any cold-trap bowl.</summary>
        public readonly float mercuryPlain;

        public BandDatum(PlanetId planet, float planetDatum, int spawnX, float spawnSurface, int worldWidth = 0, System.Func<int, float> bandSurface = null)
        {
            this.planet = planet; this.planetDatum = planetDatum; this.spawnX = spawnX; this.spawnSurface = spawnSurface; this.worldWidth = worldWidth;
            this.bandSurface = bandSurface;
            spawnBand = EarthBiomes.At(spawnX);
            spawnFeature = MarsLandforms.At(spawnX);
            earth = EarthValue;
            mars = MarsValue;
            mercuryPlain = bandSurface != null && worldWidth > 0 ? bandSurface(spawnX) - MercuryLandforms.ColdTrapProfile(spawnX, worldWidth) : spawnSurface;
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

        /// <summary>U-123 / D-146: Mercury's plain is one band at the plain's surface by the spawn (the generator's band surface there, no small
        /// crater, no bowl: an entry that lands in a small crater keeps the plain's datum); inside a cold trap the datum is the generator's band
        /// surface at that column (the plain's noise and the bowl), blended in from the rim over Blend columns, so the set meets the trap's floor.</summary>
        float MercuryAt(int x)
        {
            if (worldWidth <= 0 || !MercuryLandforms.InColdTrap(x, worldWidth, out int i)) return mercuryPlain;
            int d = Mathf.Abs(MercuryLandforms.ColdTrapOffset(x, i, worldWidth));
            float t = Mathf.Clamp01((MercuryLandforms.ColdTrapHalfWidth - d) / (float)Blend);
            float bowl = bandSurface != null ? bandSurface(x) : planetDatum + MercuryLandforms.ColdTrapProfile(x, worldWidth);
            return Mathf.Lerp(mercuryPlain, bowl, t);
        }
    }
}
