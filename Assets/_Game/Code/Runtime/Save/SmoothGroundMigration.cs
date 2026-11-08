using System.Collections.Generic;
using Meridian.Planet.POI;
using Meridian.Planets;
using Meridian.Terrain;

namespace Meridian.Save
{
    /// <summary>
    /// U-157 (D-162 (6), D-165 (3)): save v2 → v3. A 0.4.8 save's POI stamps were cut against the blocky ground; on a smooth planet they would
    /// land on the wrong surface. Migrate drops the smooth planets' poi_stamped flags (DropFlags); after the save's terrain diffs load,
    /// StripOldStamps removes every cell 0.4.8's stamping wrote that still holds that value (the old stamping recomputed with
    /// GroundField.ForceBlocks: the raw ground, the 48-column shoulders), so the planet re-stamps against the smoothed ground on its next
    /// visit. A cell the player dug or built since keeps its diff (D-162 (6): saves keep their terrain edits).
    /// </summary>
    public static class SmoothGroundMigration
    {
        /// <summary>The save version that first holds smooth-ground stamps.</summary>
        public const int Version = 3;

        /// <summary>Drops each smooth planet's POI stamp flags.</summary>
        public static int DropFlags(List<string> flags)
        {
            if (flags == null) return 0;
            int n = 0;
            foreach (PlanetId p in System.Enum.GetValues(typeof(PlanetId)))
            {
                if (!GroundField.Smooth(p)) continue;
                foreach (var poi in PoiCatalog.For(p)) if (flags.Remove(poi.StampedFlag)) n++;
            }
            return n;
        }

        /// <summary>Removes the 0.4.8 stamp diffs still standing in a smooth planet's edits; returns how many went.</summary>
        public static int StripOldStamps(TerrainEdits edits, PlanetConfig cfg, int seed)
        {
            if (edits == null || cfg == null || !GroundField.Smooth(cfg.id)) return 0;
            var old = new TerrainEdits();
            bool was = GroundField.ForceBlocks;
            GroundField.ForceBlocks = true;
            try
            {
                var raw = new SolidWorldGenerator(cfg, seed);
                foreach (var poi in PoiCatalog.For(cfg.id)) PoiStamp.Apply(poi, raw, old, cfg.datumY);
            }
            finally { GroundField.ForceBlocks = was; }
            int n = 0;
            foreach (var (x, y, id) in old.Cells())
                if (edits.TryGet(x, y, out byte now) && now == id) { edits.Remove(x, y); n++; }
            return n;
        }
    }
}
