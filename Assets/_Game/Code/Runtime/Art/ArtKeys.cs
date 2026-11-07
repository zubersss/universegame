using System;
using System.Collections.Generic;

namespace Meridian.Art
{
    public enum ArtMap { Color, Normal, Emission, Mask }

    /// <summary>
    /// Asset keys (contract §1). Code loads art only through these constants, as Addressable
    /// addresses. A key is the file path relative to Art/ (or Placeholders/) without
    /// "_&lt;map&gt;.png", always category/name/variant: `ships/pilgrim/top` →
    /// `Art/ships/pilgrim/top_color.png`. Single-variant assets use `base`, as icons do:
    /// `fx/thruster/base`, `characters/surveyor/base` (sheet manifest `base.json`).
    /// </summary>
    public static class ArtKeys
    {
        public static class Characters
        {
            public const string Surveyor = "characters/surveyor/base";
            /// <summary>U-049: the surveyor sheet per Envirosuit tier (0 = base, 1–3 = B-041 mk1–mk3).</summary>
            public static string SurveyorSheet(int tier) => tier <= 0 ? Surveyor : "characters/surveyor/mk" + System.Math.Clamp(tier, 1, 3);
        }

        public static class Ships
        {
            public const string PilgrimTop = "ships/pilgrim/top";
            public const string PilgrimSide = "ships/pilgrim/side";
            /// <summary>Skids deployed (below 10 m, Bible §4.3; D-025). `PilgrimSide` is gear retracted.</summary>
            public const string PilgrimSideLegs = "ships/pilgrim/side_legs";
            /// <summary>U-076: the Pilgrim's 3D model (B-079), centre-of-mass origin.</summary>
            public const string PilgrimModel = "ships/pilgrim/base";
            /// <summary>U-103 (B-122, D-111): the drawn Pilgrim rig (parts sheet + json with the side and top plants) and its exhaust puff loop.</summary>
            public const string PilgrimRig = "ships/pilgrim/rig";
            public const string PilgrimPuff = "ships/pilgrim/puff";
        }

        public static class Terrain
        {
            public const string EarthSoil = "terrain/earth/soil";
            public const string EarthGrass = "terrain/earth/grass";
            public const string EarthStone = "terrain/earth/stone";
            public const string EarthSand = "terrain/earth/sand";
            public const string EarthSnow = "terrain/earth/snow";
            public const string EarthWater = "terrain/earth/water";
            public const string MarsRegolith = "terrain/mars/regolith";
            public const string MarsBasalt = "terrain/mars/basalt";
            public const string MarsHematite = "terrain/mars/hematite";
            public const string MarsIce = "terrain/mars/ice";
            public const string MercuryRegolith = "terrain/mercury/regolith";
            public const string MercuryBasalt = "terrain/mercury/basalt";
            public const string MercurySulfide = "terrain/mercury/sulfide";
            public const string MercuryIce = "terrain/mercury/ice";
            public const string VenusBasalt = "terrain/venus/basalt";
            public const string VenusSulfur = "terrain/venus/sulfur";
            public const string VenusTessera = "terrain/venus/tessera";
            public const string VenusVentGlass = "terrain/venus/vent_glass";
            // U-061 cloud-column floes (B-048): one sheet each, every giant (Jupiter first).
            public const string JupiterFloeIce = "terrain/jupiter/floe_ice";
            public const string JupiterFloeCore = "terrain/jupiter/floe_core";
            /// <summary>
            /// U-091 (D-110): sheets more than one planet's terrain uses: Mars's CO2 frost is Earth's snow, the giants' floes are
            /// Jupiter's. They live in the `common` group, unpacked, so no planet's bundle stays open for another planet's visit.
            /// </summary>
            public static readonly string[] Shared = { EarthSnow, JupiterFloeIce, JupiterFloeCore };
        }

        /// <summary>U-091: true for a terrain sheet in Terrain.Shared (no allocation).</summary>
        public static bool IsSharedTerrain(string key) => key != null && System.Array.IndexOf(Terrain.Shared, key) >= 0;

        /// <summary>
        /// Addressables group of a key (Bible §10.3): the one table, used by ArtRules.GroupFor at import and by Residency at
        /// run time (U-091: the two used to drift; flora had no runtime case). No Split: IndexOf and Substring only.
        /// </summary>
        public static string GroupOf(string key)
        {
            if (string.IsNullOrEmpty(key)) return "common";
            if (IsSharedTerrain(key)) return "common";
            int a = key.IndexOf('/');
            string category = a < 0 ? key : key.Substring(0, a);
            int b = a < 0 ? -1 : key.IndexOf('/', a + 1);
            string second = a < 0 ? "" : b < 0 ? key.Substring(a + 1) : key.Substring(a + 1, b - a - 1);
            switch (category)
            {
                case "terrain":
                case "creatures":
                case "flora": return "planet_" + second;
                case "props": return second == "common" ? "common" : "planet_" + second;
                case "backgrounds": return second == "space" ? "space" : "planet_" + second;
                case "planets": return "space";
                case "icons": return "icons";
                case "ui": return "ui";
                default: return "common"; // ships, characters, fx
            }
        }

        public static class Backgrounds
        {
            public static string Layer(string planet, int index) => $"backgrounds/{planet}/layer{index}";
        }

        public static class Planets
        {
            public static string Surface(string planet) => $"planets/{planet}/surface";
            public const string EarthClouds = "planets/earth/clouds";
        }

        public static class Fx
        {
            public const string Thruster = "fx/thruster/base";
            public const string Dust = "fx/dust/base";
            public const string DigSparks = "fx/dig_sparks/base";
            public const string EscapeBand = "fx/escape_band/base";
            public const string HeatShimmer = "fx/heat_shimmer/base";
            // U-046 rig modules (B-037)
            public const string BeamRay = "fx/beam_ray/base";
            public const string LanceBolt = "fx/lance_bolt/base";
            public const string SurveyScan = "fx/survey_scan/base";
            public const string BuilderGhost = "fx/builder_ghost/base";
            // U-053 (B-043)
            public const string WardenBolt = "fx/warden_bolt/base";
        }

        public static class Props
        {
            public const string Calibration = "props/common/calibration";
        }

        public static readonly string[] PlanetNames =
            { "sun", "mercury", "venus", "earth", "mars", "jupiter", "saturn", "uranus", "neptune" };

        /// <summary>The M1 placeholder set (U-005). Every key here has a file in Placeholders/.</summary>
        public static IReadOnlyList<string> M1
        {
            get
            {
                var list = new List<string>
                {
                    Characters.Surveyor, Ships.PilgrimTop, Ships.PilgrimSide,
                    Terrain.EarthSoil, Terrain.EarthGrass, Terrain.EarthStone, Terrain.EarthSand,
                    Terrain.EarthSnow, Terrain.EarthWater,
                    Terrain.MarsRegolith, Terrain.MarsBasalt, Terrain.MarsHematite, Terrain.MarsIce,
                    Planets.EarthClouds,
                    Fx.Thruster, Fx.Dust, Fx.DigSparks, Fx.EscapeBand, Fx.HeatShimmer,
                    Props.Calibration,
                };
                foreach (var p in new[] { "earth", "mars", "space" })
                    for (int i = 0; i < 3; i++) list.Add(Backgrounds.Layer(p, i));
                foreach (var p in PlanetNames) list.Add(Planets.Surface(p));
                return list;
            }
        }

        public static string MapSuffix(ArtMap map) => map switch
        {
            ArtMap.Color => "color",
            ArtMap.Normal => "normal",
            ArtMap.Emission => "emission",
            ArtMap.Mask => "mask",
            _ => throw new ArgumentOutOfRangeException(nameof(map)),
        };

        /// <summary>First key segment, e.g. "ships".</summary>
        public static string Category(string key)
        {
            int slash = key.IndexOf('/');
            return slash < 0 ? key : key.Substring(0, slash);
        }
    }
}
