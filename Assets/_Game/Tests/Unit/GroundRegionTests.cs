using Meridian.Planets;
using Meridian.Terrain;
using Meridian.View2D;
using NUnit.Framework;

namespace Meridian.Tests
{
    /// <summary>
    /// U-159 (B-178, B-181): each inner planet's ground sets by region. Earth by biome (unchanged), Mars by landform (Olympus's basalt with its
    /// own fill, the polar cap's frost, the canyon's talus), Mercury's cold traps' ice, Venus's tesserae and vent fields; every set named here
    /// and every own fill exists as exported art, and a column outside every region takes the planet's B-175 band.
    /// </summary>
    public class GroundRegionTests
    {
        const string Art = "Assets/_Game/Art/terrain/";

        [Test]
        public void EachInnerPlanetPicksItsGroundSetByRegion()
        {
            foreach (var id in new[] { PlanetId.Earth, PlanetId.Mars, PlanetId.Mercury, PlanetId.Venus })
            {
                var keys = SmoothGround.VariantKeys(id);
                Assert.AreEqual(SmoothGround.Variants, keys.Length, $"{id}: four slots");
                Assert.AreEqual("ground_band", keys[0], $"{id}: slot 0 is B-175's band");
                string planet = id.ToString().ToLowerInvariant();
                foreach (var k in keys)
                    if (k != null) Assert.IsTrue(System.IO.File.Exists($"{Art}{planet}/{k}.json"), $"{id}: {k} exported");
                var alt = SmoothGround.AltFillKey(id);
                if (alt != null) Assert.IsTrue(System.IO.File.Exists($"{Art}{planet}/{alt}.json"), $"{id}: {alt} exported");
                // B-242: a band fill of its own has a back wall of its own, by the fill's name
                var wall = SmoothGround.AltWallKey(id);
                Assert.AreEqual(alt == null, wall == null, $"{id}: a wall for the band's own fill, and only for one");
                if (wall != null)
                {
                    Assert.IsTrue(System.IO.File.Exists($"{Art}{planet}/{wall}.json"), $"{id}: {wall} exported");
                    Assert.IsTrue(Meridian.Art.ArtKeys.IsBackWall($"terrain/{planet}/{wall}"), $"{id}: {wall} imports by the walls' rule");
                }
            }
            Assert.AreEqual("back_wall_sand", SmoothGround.AltWallKey(PlanetId.Earth), "the desert's sand");
            Assert.AreEqual("back_wall_basalt", SmoothGround.AltWallKey(PlanetId.Mars), "Olympus's basalt");
            Assert.IsNull(SmoothGround.AltWallKey(PlanetId.Venus), "no fill of its own, no wall");
            // Earth (B-178): unchanged.
            EarthBiomes.Range(Biome.Desert, out int ds, out int dl);
            Assert.AreEqual(SmoothGround.Sand, SmoothGround.VariantFor(PlanetId.Earth, ds + dl / 2, 340, 320, 4096));
            EarthBiomes.Range(Biome.Taiga, out int ts, out int tl);
            Assert.AreEqual(SmoothGround.Snow, SmoothGround.VariantFor(PlanetId.Earth, ts + tl / 2, 340, 320, 4096));
            Assert.AreEqual(SmoothGround.Grass, SmoothGround.VariantFor(PlanetId.Earth, 64, 337, 320, 4096), "the camp's forest");
            // Mars (B-181, B-178's frost).
            Assert.AreEqual("ground_band_basalt", SmoothGround.VariantKeys(PlanetId.Mars)[SmoothGround.VariantFor(PlanetId.Mars, MarsLandforms.OlympusCenter, 0, 0, MarsLandforms.Width)], "Olympus");
            Assert.AreEqual("ground_band_frost", SmoothGround.VariantKeys(PlanetId.Mars)[SmoothGround.VariantFor(PlanetId.Mars, 10, 0, 0, MarsLandforms.Width)], "the polar cap");
            Assert.AreEqual("ground_band_talus", SmoothGround.VariantKeys(PlanetId.Mars)[SmoothGround.VariantFor(PlanetId.Mars, (MarsLandforms.CanyonStart + MarsLandforms.CanyonEnd) / 2, 0, 0, MarsLandforms.Width)], "the canyon floor");
            Assert.AreEqual(0, SmoothGround.VariantFor(PlanetId.Mars, 600, 0, 0, MarsLandforms.Width), "the plains");
            Assert.AreEqual("ground_fill_basalt", SmoothGround.AltFillKey(PlanetId.Mars), "Olympus's basalt has its own fill (slot 1)");
            // Mercury: the cold traps' ice, the plain elsewhere.
            int w = 4096, trap = MercuryLandforms.ColdTrapCentre(0, w);
            Assert.AreEqual("ground_band_ice", SmoothGround.VariantKeys(PlanetId.Mercury)[SmoothGround.VariantFor(PlanetId.Mercury, trap, 0, 0, w)], "a cold trap");
            Assert.AreEqual(0, SmoothGround.VariantFor(PlanetId.Mercury, MercuryLandforms.PadX, 0, 0, w), "the pad's plain");
            // Venus: the tesserae and the vent fields.
            Assert.AreEqual("ground_band_tessera", SmoothGround.VariantKeys(PlanetId.Venus)[SmoothGround.VariantFor(PlanetId.Venus, 800, 0, 0, w)], "a tessera");
            Assert.AreEqual("ground_band_vent", SmoothGround.VariantKeys(PlanetId.Venus)[SmoothGround.VariantFor(PlanetId.Venus, 1650, 0, 0, w)], "a vent field");
            Assert.AreEqual(0, SmoothGround.VariantFor(PlanetId.Venus, 200, 0, 0, w), "the plains");
        }
    }
}
