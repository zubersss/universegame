using Meridian.Planets;
using Meridian.Terrain.CloudColumn;
using UnityEngine;

namespace Meridian.Hazards
{
    /// <summary>
    /// U-068 giant-world hazard bands (Bible §7.5–7.9) as data: for Jupiter, Saturn, Uranus and Neptune, each
    /// hazard's raw level (0–3) by cloud band (CloudLayout.BandAt). Pure, no allocation; HazardTable reads it for
    /// the giants and U-061's cloud column consumes it. Numbers the Bible leaves open are listed in UNITY_STATUS
    /// (P-23) for LEAD's D- entry.
    /// </summary>
    public static class GiantBands
    {
        /// <summary>Row order of the table: the bands that can hold the surveyor (Space and Sky share the Sky row).</summary>
        const int Sky = 0, Deck1 = 1, Deck2 = 2, Deck3 = 3, Deep = 4, Crush = 5, Rows = 6;

        // Per giant, per band row: Thermal, Cryo, Radiation, Toxic, Pressure (HazardKind order).
        // Pressure in the Deep is filled at lookup time (2 at y 300 rising to 3 at the Crush Line, §7.5).
        static readonly byte[] Jupiter =
        {
            // T  C  R  X  P
               0, 2, 3, 0, 1, // Sky: above the Datum, in the belts (§7.6 Radiation 3 above Deck 2)
               0, 2, 3, 0, 1, // Deck 1: ammonia ice, Cryo 2, still in the belts
               0, 0, 1, 0, 1, // Deck 2: shielded by the atmosphere to 1
               0, 0, 1, 0, 2, // Deck 3: warm water clouds
               2, 0, 1, 0, 2, // Deep: Thermal 2 (§7.6)
               3, 0, 1, 0, 3, // Crush: lethal anyway
        };

        static readonly byte[] Saturn =
        {
               0, 2, 0, 0, 1, // Sky
               0, 2, 0, 0, 1, // Deck 1: Cryo 2 (§7.7)
               0, 0, 0, 0, 1, // Deck 2
               0, 0, 0, 0, 2, // Deck 3
               2, 0, 0, 0, 2, // Deep: Thermal rising (§7.5)
               3, 0, 0, 0, 3, // Crush
        };

        static readonly byte[] Uranus =
        {
               0, 3, 0, 0, 1, // Sky: coldest atmosphere, Cryo 3 (§7.8)
               0, 3, 0, 0, 1, // Deck 1
               0, 3, 0, 0, 1, // Deck 2
               0, 2, 0, 0, 2, // Deck 3: water clouds are warmer; diamond rain starts below
               2, 0, 0, 0, 2, // Deep
               3, 0, 0, 0, 3, // Crush
        };

        static readonly byte[] Neptune =
        {
               0, 3, 0, 0, 1, // Sky: Cryo 3 (§7.9)
               0, 3, 0, 0, 1, // Deck 1
               0, 3, 0, 0, 1, // Deck 2
               0, 2, 0, 0, 2, // Deck 3
               2, 0, 0, 0, 2, // Deep: Thermal in the Deep (§7.9)
               3, 0, 0, 0, 3, // Crush
        };

        public static bool IsGiant(PlanetId p) =>
            p == PlanetId.Jupiter || p == PlanetId.Saturn || p == PlanetId.Uranus || p == PlanetId.Neptune;

        /// <summary>Fills `levels` (HazardRules.Kinds long) with the giant's raw levels at height y; zeros for other planets.</summary>
        public static void For(PlanetId planet, float y, int[] levels)
        {
            for (int i = 0; i < levels.Length; i++) levels[i] = 0;
            var table = TableOf(planet);
            if (table == null) return;
            int row = RowOf(CloudLayout.BandAt(y));
            int o = row * HazardRules.Kinds;
            for (int k = 0; k < HazardRules.Kinds && k < levels.Length; k++) levels[k] = table[o + k];
            if (row == Deep) levels[(int)HazardKind.Pressure] = DeepPressure(y);
        }

        /// <summary>One hazard's raw level for a giant at height y (0 for other planets).</summary>
        public static int Level(PlanetId planet, float y, HazardKind kind)
        {
            var table = TableOf(planet);
            if (table == null) return 0;
            int row = RowOf(CloudLayout.BandAt(y));
            if (row == Deep && kind == HazardKind.Pressure) return DeepPressure(y);
            return table[row * HazardRules.Kinds + (int)kind];
        }

        /// <summary>Deep pressure: 2 at the Deep's top (y 300), 3 from two-thirds of the way down to the Crush Line.</summary>
        static int DeepPressure(float y)
        {
            float down = Mathf.InverseLerp(CloudLayout.Deck3Bottom, CloudLayout.CrushLine, y);
            return down >= 2f / 3f ? 3 : 2;
        }

        static int RowOf(CloudBand b) => b switch
        {
            CloudBand.Deck1 => Deck1,
            CloudBand.Deck2 => Deck2,
            CloudBand.Deck3 => Deck3,
            CloudBand.Deep => Deep,
            CloudBand.Crush => Crush,
            _ => Sky,
        };

        static byte[] TableOf(PlanetId p) => p switch
        {
            PlanetId.Jupiter => Jupiter,
            PlanetId.Saturn => Saturn,
            PlanetId.Uranus => Uranus,
            PlanetId.Neptune => Neptune,
            _ => null,
        };

        /// <summary>Tests: rows in a giant's table (one per band; 0 for other planets).</summary>
        public static int RowCount(PlanetId p) => TableOf(p) is { } t ? t.Length / HazardRules.Kinds : 0;
        public const int BandRows = Rows;
    }
}
