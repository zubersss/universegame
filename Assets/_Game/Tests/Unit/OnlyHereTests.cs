using Meridian.Items;
using Meridian.Planet.POI;
using Meridian.Planets;
using Meridian.Survey;
using Meridian.Terrain;
using NUnit.Framework;
using UnityEditor;

namespace Meridian.Tests
{
    /// <summary>U-059 (EditMode): each inner planet's "only here" item is obtainable in a seeded world, and catalogued.</summary>
    public class OnlyHereTests
    {
        const int Seed = 1969;
        static PlanetConfig Load(string name) => AssetDatabase.LoadAssetAtPath<PlanetConfig>($"Assets/_Game/Settings/Planets/{name}.asset");

        [Test]
        public void EveryInnerPlanetHasItsFindRegisteredAndCatalogued()
        {
            foreach (var p in new[] { PlanetId.Mercury, PlanetId.Venus, PlanetId.Earth, PlanetId.Mars })
            {
                var key = OnlyHere.KeyFor(p);
                var def = ItemRegistry.Get(key);
                Assert.NotNull(def, key);
                Assert.NotNull(Catalogue.Find(p, Catalogue.MineralId(def.id)), $"{p}: catalogue entry for {key}");
            }
            Assert.NotNull(ItemRegistry.Get("wormplate"), "the Wormplate stub (M4+)");
        }

        [Test]
        public void MarsPerchlorateLiesInDepositsOnThePlainsAndTheCap()
        {
            var mars = Load("Mars");
            var gen = new SolidWorldGenerator(mars, Seed);
            int perchlorate = ItemRegistry.Get("perchlorate").id, plains = 0, cap = 0, canyon = 0;
            for (int x = 0; x < mars.worldWidth; x++)
            {
                int s = gen.SurfaceHeight(x);
                // The surface, and just under the cap's two tiles of CO₂ frost.
                if (OnlyHere.DropAt(PlanetId.Mars, gen.TileAt(x, s), x, s, 0).replace != perchlorate
                    && OnlyHere.DropAt(PlanetId.Mars, gen.TileAt(x, s - 2), x, s - 2, 2).replace != perchlorate) continue;
                var f = MarsLandforms.At(x);
                if (f == MarsFeature.Plains) plains++; else if (f == MarsFeature.PolarCap) cap++; else canyon++;
            }
            TestContext.Out.WriteLine($"[MERIDIAN] perchlorate surface columns: plains {plains}, polar cap {cap}");
            Assert.Greater(plains, 20, "plains deposits");
            Assert.Greater(cap, 5, "polar deposits");
            Assert.AreEqual(0, canyon, "none in the canyon or on Olympus");
            int sx = 0;
            while (!(OnlyHere.InPerchlorateDeposit(sx) && gen.TileAt(sx, gen.SurfaceHeight(sx)) == TileId.Regolith)) sx++;
            Assert.AreEqual(0, OnlyHere.DropAt(PlanetId.Mars, TileId.Regolith, sx, 0, OnlyHere.DepositDepth).replace, "deposits are shallow");
            Assert.AreEqual(0, OnlyHere.DropAt(PlanetId.Mars, TileId.Basalt, sx, 0, 0).replace, "only regolith (and polar ice) holds it");
        }

        [Test]
        public void EarthTurfYieldsLivingSeedInForestAndPlains()
        {
            var earth = Load("Earth");
            var gen = new SolidWorldGenerator(earth, Seed);
            int seed = ItemRegistry.Get("living_seed").id, found = 0, grass = 0;
            for (int x = 0; x < earth.worldWidth; x++)
            {
                int s = gen.SurfaceHeight(x);
                if (gen.TileAt(x, s) != TileId.Grass) continue;
                grass++;
                if (OnlyHere.DropAt(PlanetId.Earth, TileId.Grass, x, s, 0).bonus == seed)
                {
                    found++;
                    var b = EarthBiomes.At(x);
                    Assert.IsTrue(b == Biome.Forest || b == Biome.Plains, $"seed at {x} in {b}");
                }
            }
            TestContext.Out.WriteLine($"[MERIDIAN] living seed: {found} of {grass} turf columns");
            Assert.Greater(found, 30);
            Assert.Less(found, grass / 3, "a find, not every tile");
        }

        [Test]
        public void VenusVentGlassAndMercurySolariteFieldExist()
        {
            var venus = Load("Venus");
            var gen = new SolidWorldGenerator(venus, Seed);
            int glass = 0;
            var vent = VenusLandforms.Vents[0];
            for (int x = vent.x0; x < vent.x1; x++)
                for (int d = 0; d < 6; d++) if (gen.TileAt(x, gen.SurfaceHeight(x) - d) == TileId.VentGlass) glass++;
            Assert.Greater(glass, 10, "Vitriol Glass in the vent field");
            Assert.AreEqual(ItemRegistry.Get("vitriol_glass").id, ItemRegistry.DropOf(TileId.VentGlass));
            Assert.IsTrue(System.Linq.Enumerable.Any(PoiCatalog.For(PlanetId.Mercury), p => p.id == "solarite_field"), "Mercury's Solarite field");
            Assert.IsTrue(OnlyHere.SolariteHarvestable(30f), "+30 s after a flare");
            Assert.IsFalse(OnlyHere.SolariteHarvestable(120f), "+120 s: crusted over");
            Assert.IsFalse(OnlyHere.SolariteHarvestable(-1f));
        }
    }
}
