using System.Collections.Generic;
using Meridian.Planets;
using UnityEngine;

namespace Meridian.Planet.POI
{
    /// <summary>A prop placed with a POI: asset key, x from the stamp's left edge, y from the ground line (m), size of its placeholder.</summary>
    public readonly struct PoiProp
    {
        public readonly string key;
        public readonly float dx, dy;
        public readonly Vector2 size;
        public PoiProp(string key, float dx, float dy, Vector2 size) { this.key = key; this.dx = dx; this.dy = dy; this.size = size; }
    }

    /// <summary>
    /// A handmade point of interest (U-030): a tile stamp merged into the generated terrain at a fixed
    /// column, plus props. Stamp rows run top to bottom; row `groundRow` lands on the ground line
    /// (the local surface, never below sea level). Cells: '.' air, '#' rock, 'g' surface material,
    /// ' ' leave the generated tile.
    /// </summary>
    public sealed class PoiDef
    {
        public string id, label;
        public PlanetId planet;
        /// <summary>Stamp left edge, as a tile column (fixed: the same in every world).</summary>
        public int x;
        public string[] stamp;
        public int groundRow;
        public PoiProp[] props;

        public int Width => stamp[0].Length;
        public float CenterX => x + Width * 0.5f;
        public string StampedFlag => "poi_stamped:" + id;
        string markerText;
        /// <summary>HUD marker text after the distance: "m  SURVEY ARCHIVE" (built once).</summary>
        public string MarkerText => markerText ??= "m  " + label;
    }

    /// <summary>U-030 POIs v1 (Bible §7.1, §7.2): two on Earth, two on Mars.</summary>
    public static class PoiCatalog
    {
        /// <summary>Survey Archive (story start, Bible §2): within 200 m of the Earth spawn (x 64).</summary>
        public static readonly PoiDef SurveyArchive = new PoiDef
        {
            id = "survey_archive", label = "SURVEY ARCHIVE", planet = PlanetId.Earth, x = 184, groundRow = 4,
            stamp = new[]
            {
                "....................",
                "....................",
                "....................",
                "....................",
                "gggggggg....gggggggg",
                "########....########",
                "########....########",
                "###................#",
                "###................#",
                "###................#",
                "####################",
            },
            props = new[]
            {
                new PoiProp("props/earth/archive_door", 10f, 0f, new Vector2(4f, 3f)),
                new PoiProp("props/earth/archive_terminal", 14f, -6f, new Vector2(1.5f, 2f)),
                new PoiProp("props/earth/beacon", 3f, 0f, new Vector2(0.8f, 3f)),
            },
        };

        /// <summary>Abandoned coastal launch complex (ship parts): a concrete pad by the sea, halfway round the world (x 2048 of 4096).</summary>
        public static readonly PoiDef LaunchComplex = new PoiDef
        {
            id = "coastal_launch_complex", label = "LAUNCH COMPLEX", planet = PlanetId.Earth, x = 2048, groundRow = 8,
            stamp = new[]
            {
                "................................",
                "................................",
                "................................",
                "................................",
                "................................",
                "................................",
                "................................",
                "................................",
                "################################",
                "################################",
                "################################",
            },
            props = new[]
            {
                new PoiProp("props/earth/launch_gantry", 10f, 1f, new Vector2(5f, 14f)),
                new PoiProp("props/earth/launch_tower_ruin", 24f, 1f, new Vector2(4f, 9f)),
            },
        };

        /// <summary>Crashed Halcyon hauler (Dray parts): a gouge in the regolith with the broken hull.</summary>
        public static readonly PoiDef HalcyonHauler = new PoiDef
        {
            id = "halcyon_hauler", label = "HALCYON HAULER", planet = PlanetId.Mars, x = 900, groundRow = 6,
            stamp = new[]
            {
                "..............................",
                "..............................",
                "..............................",
                "..............................",
                "..............................",
                "..............................",
                "ggg......................ggggg",
                "####gg..............gggg######",
                "######gggggggggggggg##########",
                "##############################",
            },
            props = new[]
            {
                new PoiProp("props/mars/hauler_hull_a", 9f, -1.5f, new Vector2(9f, 4f)),
                new PoiProp("props/mars/hauler_hull_b", 18f, -1f, new Vector2(7f, 3.5f)),
                new PoiProp("props/mars/hauler_cargo", 24f, 0f, new Vector2(2f, 1.6f)),
            },
        };

        /// <summary>Warden outpost: a levelled platform with pylons (Wardens arrive in M3).</summary>
        public static readonly PoiDef WardenOutpost = new PoiDef
        {
            id = "warden_outpost", label = "WARDEN OUTPOST", planet = PlanetId.Mars, x = 2000, groundRow = 8,
            stamp = new[]
            {
                "........................",
                "........................",
                "........................",
                "........................",
                "........................",
                "........................",
                "........................",
                "........................",
                "########################",
                "########################",
                "########################",
            },
            props = new[]
            {
                new PoiProp("props/mars/warden_pylon", 4f, 1f, new Vector2(1.2f, 6f)),
                new PoiProp("props/mars/warden_pylon", 20f, 1f, new Vector2(1.2f, 6f)),
                new PoiProp("props/mars/meridian_beacon", 12f, 1f, new Vector2(1f, 3f)),
            },
        };

        public static readonly PoiDef[] All = { SurveyArchive, LaunchComplex, HalcyonHauler, WardenOutpost };

        public static IEnumerable<PoiDef> For(PlanetId planet)
        {
            foreach (var p in All) if (p.planet == planet) yield return p;
        }
    }
}
