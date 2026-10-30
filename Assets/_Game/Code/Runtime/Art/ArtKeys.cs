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
        }

        public static class Ships
        {
            public const string PilgrimTop = "ships/pilgrim/top";
            public const string PilgrimSide = "ships/pilgrim/side";
            /// <summary>Skids deployed (below 10 m, Bible §4.3; D-025). `PilgrimSide` is gear retracted.</summary>
            public const string PilgrimSideLegs = "ships/pilgrim/side_legs";
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
