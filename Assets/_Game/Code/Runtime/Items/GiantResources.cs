using Meridian.Planets;

namespace Meridian.Items
{
    /// <summary>Where a giant-world or ring resource comes from (U-069; the generators that fill it land with U-061/U-066).</summary>
    public enum ResourceSource { DeckFloe, DeepVein, RedSpotFloe, RingMining, DiamondRain, HeliumTrap }

    /// <summary>One M4 raw resource: its item key, the planets that hold it, and how it is gathered.</summary>
    public readonly struct GiantResource
    {
        public readonly string key;
        public readonly PlanetId[] planets;
        public readonly ResourceSource source;
        public GiantResource(string key, ResourceSource source, params PlanetId[] planets) { this.key = key; this.source = source; this.planets = planets; }
    }

    /// <summary>
    /// U-069 M4 materials (Bible §7.6–7.9) as data: each raw resource of the giants and the rings, where it is,
    /// and its source. Pure. The survey catalogue lists them per planet; the cloud column (U-061) and ring
    /// mining (U-066) read the same table for what a floe, a vein or a ring body yields.
    /// </summary>
    public static class GiantResources
    {
        public static readonly GiantResource[] All =
        {
            new GiantResource("ammonia_ice", ResourceSource.DeckFloe, PlanetId.Jupiter, PlanetId.Saturn, PlanetId.Uranus, PlanetId.Neptune),
            new GiantResource("phosphorus_pigment", ResourceSource.RedSpotFloe, PlanetId.Jupiter),
            new GiantResource("metallic_hydrogen", ResourceSource.DeepVein, PlanetId.Jupiter),
            new GiantResource("helium3_condensate", ResourceSource.HeliumTrap, PlanetId.Saturn),
            new GiantResource("ring_ice", ResourceSource.RingMining, PlanetId.Saturn),
            new GiantResource("ring_rock", ResourceSource.RingMining, PlanetId.Saturn),
            new GiantResource("methane_ice", ResourceSource.DeckFloe, PlanetId.Uranus, PlanetId.Neptune),
            new GiantResource("deep_diamond", ResourceSource.DiamondRain, PlanetId.Uranus),
            new GiantResource("superionic_ice", ResourceSource.DeepVein, PlanetId.Neptune),
        };

        /// <summary>The entry for an item key, or false.</summary>
        public static bool TryGet(string key, out GiantResource r)
        {
            foreach (var g in All)
                if (g.key == key) { r = g; return true; }
            r = default;
            return false;
        }

        public static bool On(in GiantResource r, PlanetId p)
        {
            foreach (var q in r.planets) if (q == p) return true;
            return false;
        }
    }
}
