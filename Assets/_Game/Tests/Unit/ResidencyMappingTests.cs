using Meridian.Art;
using Meridian.Perf;
using Meridian.Planets;
using Meridian.Terrain;
using NUnit.Framework;

namespace Meridian.Tests
{
    /// <summary>
    /// U-091 (EditMode, D-089 / D-110): every terrain sheet a planet loads is attributed to that planet's group, except the
    /// shared sheets (Mars's CO2 frost is Earth's snow, the giants' floes are Jupiter's), which live in `common` so no
    /// planet's bundle stays open for another planet's visit. One group table serves import and run time.
    /// </summary>
    public class ResidencyMappingTests
    {
        [Test]
        public void EveryPlanetsTerrainSheetsBelongToItOrToCommon()
        {
            foreach (PlanetId p in System.Enum.GetValues(typeof(PlanetId)))
            {
                string own = Residency.PlanetGroup(p);
                int ownCount = 0, shared = 0;
                foreach (var id in TerrainStreamer.MaterialsFor(p))
                {
                    var key = TileId.ArtKey(id);
                    if (key == null) continue;
                    var group = Residency.GroupOf(key);
                    if (ArtKeys.IsSharedTerrain(key)) { Assert.AreEqual("common", group, $"{p}: shared sheet {key}"); shared++; }
                    else { Assert.AreEqual(own, group, $"{p}: {key} must count for {own}, not another planet"); ownCount++; }
                }
                TestContext.Out.WriteLine($"[MERIDIAN] {p}: {ownCount} own sheets, {shared} shared");
                Assert.Greater(ownCount + shared, 0, $"{p} has terrain materials");
            }
        }

        [Test]
        public void TheSharedSheetsAreTheThreeFromD110()
        {
            CollectionAssert.AreEquivalent(new[] { ArtKeys.Terrain.EarthSnow, ArtKeys.Terrain.JupiterFloeIce, ArtKeys.Terrain.JupiterFloeCore }, ArtKeys.Terrain.Shared);
            Assert.IsTrue(ArtKeys.IsSharedTerrain("terrain/earth/snow"));
            Assert.IsFalse(ArtKeys.IsSharedTerrain("terrain/earth/soil"));
            Assert.IsFalse(ArtKeys.IsSharedTerrain(null));
            // Mars really uses the Earth snow sheet (its CO2 frost): the reason the Earth bundle stayed open on Mars before U-091.
            bool marsUsesSnow = false;
            foreach (var id in TerrainStreamer.MaterialsFor(PlanetId.Mars)) if (TileId.ArtKey(id) == ArtKeys.Terrain.EarthSnow) marsUsesSnow = true;
            Assert.IsTrue(marsUsesSnow, "Mars loads terrain/earth/snow");
        }

        [Test]
        public void GroupTableCoversEveryCategory()
        {
            Assert.AreEqual("planet_earth", ArtKeys.GroupOf("terrain/earth/soil"));
            Assert.AreEqual("common", ArtKeys.GroupOf("terrain/earth/snow"));
            Assert.AreEqual("planet_mars", ArtKeys.GroupOf("creatures/mars/skitter"));
            Assert.AreEqual("planet_earth", ArtKeys.GroupOf("flora/earth/rigset"), "flora follows its planet (the runtime table had no flora case)");
            Assert.AreEqual("planet_mars_flora", ArtKeys.GroupOf("props/mars_flora/cactus"));
            Assert.AreEqual("common", ArtKeys.GroupOf("props/common/calibration"));
            Assert.AreEqual("planet_earth_forest", ArtKeys.GroupOf("backgrounds/earth_forest/ridge_mid"));
            Assert.AreEqual("space", ArtKeys.GroupOf("backgrounds/space/starfield"));
            Assert.AreEqual("space", ArtKeys.GroupOf("planets/earth/disc"));
            Assert.AreEqual("icons", ArtKeys.GroupOf("icons/iron/base"));
            Assert.AreEqual("ui", ArtKeys.GroupOf("ui/hud/gauges"));
            Assert.AreEqual("common", ArtKeys.GroupOf("ships/pilgrim/side"));
            Assert.AreEqual("common", ArtKeys.GroupOf("characters/surveyor/side"));
            Assert.AreEqual("common", ArtKeys.GroupOf("fx/dust/base"));
            Assert.AreEqual("common", ArtKeys.GroupOf(""));
            Assert.AreEqual("planet_earth", Residency.PlanetOf("planet_earth_forest"));
            Assert.AreEqual("planet_mars", Residency.PlanetOf("planet_mars"));
            Assert.IsNull(Residency.PlanetOf("planet_space"));
            Assert.IsNull(Residency.PlanetOf("planet_warden"));
            Assert.IsNull(Residency.PlanetOf("common"));
            Assert.IsNull(Residency.PlanetOf("planet_earthling"), "a longer name is not a suffixed group");
        }
    }
}
