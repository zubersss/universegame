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

        /// <summary>U-139: the FINAL surface at a column (TerrainStreamer.OriginalTop + 1: the landforms, the traps, every POI stamp and its
        /// shoulders; player digs not) — the datum takes it across each POI's stamp and blends back over its shoulders. Null: the D-146 rules.</summary>
        readonly System.Func<int, float> finalSurface;
        /// <summary>U-139: the planet's stamped POIs as (first column, width) pairs: where the final surface overrides the band surface.</summary>
        readonly int[] stamps;
        /// <summary>U-139: the measured spawn surface holds this many columns either side of the spawn (the pad frames never move), then blends
        /// over Blend columns into the rule.</summary>
        public const int PadHold = 24;
        int cachedX = int.MinValue; float cachedValue;

        public BandDatum(PlanetId planet, float planetDatum, int spawnX, float spawnSurface, int worldWidth = 0, System.Func<int, float> bandSurface = null,
            System.Func<int, float> finalSurface = null, int[] stamps = null)
        {
            this.planet = planet; this.planetDatum = planetDatum; this.spawnX = spawnX; this.spawnSurface = spawnSurface; this.worldWidth = worldWidth;
            this.bandSurface = bandSurface;
            this.finalSurface = finalSurface;
            this.stamps = stamps;
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
                case PlanetId.Mars: return Stamped(x, MarsLandforms.Blended(x, Blend, mars)); // U-139 (LEAD 16:1x): the hauler, the outpost, the beacon on their stamped ground
                case PlanetId.Mercury: return finalSurface != null && bandSurface != null && worldWidth > 0 ? Followed(x) : MercuryAt(x);
                case PlanetId.Venus: return finalSurface != null && bandSurface != null && worldWidth > 0 ? Followed(x) : spawnSurface; // U-139: the tesserae rise 55 m
                default: return spawnSurface;
            }
        }

        /// <summary>
        /// U-139 (the 0.4.5 smoke finding: the set 3 m over the solarite field's terrace, 6 m under the flare shelter's plateau): the datum follows
        /// the surface the surveyor walks. Off the POIs it is the generator's band surface (no small craters, D-146) with its noise averaged over
        /// ±Blend columns and Mercury's cold-trap bowl added back unsmoothed (an average would lift the set ~5.6 m off a trap's floor); across a
        /// POI's stamp it is the final stamped surface, blended back over the stamp's shoulders (PoiStamp.MaxShoulder); within PadHold of the
        /// spawn it is the measured spawn surface, so the pad frames never move. One cached column; no allocation.
        /// </summary>
        float Followed(int x)
        {
            if (x == cachedX) return cachedValue;
            float d = SmoothedPlain(x) + Bowl(x);
            // Inside a cold trap D-146's exact rule wins from the rim in: the floor's own column, not the averaged noise over the bowl.
            if (planet == PlanetId.Mercury && MercuryLandforms.InColdTrap(x, worldWidth, out int trap))
            {
                int off = Mathf.Abs(MercuryLandforms.ColdTrapOffset(x, trap, worldWidth));
                d = Mathf.Lerp(d, bandSurface(x), Mathf.Clamp01((MercuryLandforms.ColdTrapHalfWidth - off) / (float)Blend));
            }
            float w = StampWeight(x);
            if (w > 0f) d = Mathf.Lerp(d, finalSurface(x), w);
            float hold = Mathf.Clamp01((Wrapped(x - spawnX) - PadHold) / (float)Blend);
            d = Mathf.Lerp(spawnSurface, d, hold);
            cachedX = x; cachedValue = d;
            return d;
        }

        /// <summary>U-139: a band datum pulled onto a ground POI's stamped surface across its stamp, back over its shoulders (Mars; Earth untouched).</summary>
        float Stamped(int x, float d)
        {
            if (finalSurface == null) return d;
            float w = StampWeight(x);
            return w > 0f ? Mathf.Lerp(d, finalSurface(x), w) : d;
        }

        float Bowl(int x) => planet == PlanetId.Mercury ? MercuryLandforms.ColdTrapProfile(x, worldWidth) : 0f;

        /// <summary>U-139: the band surface without the bowls, averaged over ±Blend columns (the plain's noise as one gentle line).</summary>
        float SmoothedPlain(int x)
        {
            float sum = 0f;
            for (int c = x - Blend; c <= x + Blend; c++) sum += bandSurface(c) - Bowl(c);
            return sum / (2 * Blend + 1);
        }

        /// <summary>U-139: 1 across a POI's stamp, falling to 0 over its shoulders (MaxShoulder columns), 0 elsewhere; the nearest stamp wins.</summary>
        float StampWeight(int x)
        {
            if (stamps == null) return 0f;
            float best = 0f;
            for (int i = 0; i + 1 < stamps.Length; i += 2)
            {
                int start = stamps[i], width = stamps[i + 1];
                int d = WrappedSigned(x - start);
                int k = d >= 0 && d < width ? 0 : d >= width ? d - width + 1 : -d;
                float w = k == 0 ? 1f : 1f - k / (float)Meridian.Planet.POI.PoiStamp.MaxShoulder;
                if (w > best) best = w;
            }
            return best;
        }

        int WrappedSigned(int d) { if (worldWidth <= 0) return d; d %= worldWidth; if (d > worldWidth / 2) d -= worldWidth; if (d < -worldWidth / 2) d += worldWidth; return d; }
        int Wrapped(int d) => Mathf.Abs(WrappedSigned(d));

        /// <summary>U-139: the stamp extents of a planet's ground POIs (floating stations excluded) as (first column, width) pairs.</summary>
        public static int[] StampsOf(PlanetId planet)
        {
            var list = new System.Collections.Generic.List<int>();
            foreach (var poi in Meridian.Planet.POI.PoiCatalog.For(planet))
                if (!poi.Floating && poi.stamp != null) { list.Add(poi.x); list.Add(poi.Width); }
            return list.ToArray();
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
