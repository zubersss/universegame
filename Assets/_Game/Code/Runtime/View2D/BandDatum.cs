using Meridian.Planets;
using Meridian.Terrain;

namespace Meridian.View2D
{
    /// <summary>
    /// U-128: the painted stage's datum per band. Until now the layers sat at the spawn's surface everywhere, so the coast (16 m
    /// under the camp) showed nothing behind the Maw. Here each band has its own datum — Earth's biome bands their mean surface
    /// (EarthBiomes.MeanSurface; the Ocean band its water line), Mars's landforms their profile (the canyon floor, the shield's mid
    /// slope, the cap's rise) — blended across the ±Blend-column borders exactly as the heights blend, and the spawn's own band keeps
    /// the measured spawn surface (the stamped camp), so the camp frames do not move. One delegate per instance; At allocates nothing.
    /// </summary>
    public sealed class BandDatum
    {
        public const int Blend = EarthBiomes.Blend;
        public readonly PlanetId planet;
        public readonly float planetDatum, spawnSurface;
        public readonly int spawnX;
        readonly Biome spawnBand;
        readonly MarsFeature spawnFeature;
        readonly System.Func<Biome, float> earth;
        readonly System.Func<MarsFeature, float> mars;

        public BandDatum(PlanetId planet, float planetDatum, int spawnX, float spawnSurface)
        {
            this.planet = planet; this.planetDatum = planetDatum; this.spawnX = spawnX; this.spawnSurface = spawnSurface;
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
                default: return spawnSurface;
            }
        }
    }
}
