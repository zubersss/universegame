using Meridian.Planet.Backdrop;
using Meridian.Planets;
using Meridian.Terrain;
using NUnit.Framework;

namespace Meridian.Tests
{
    /// <summary>U-076 (EditMode): the depth bands' pure tables: the ridge per biome, the flora per column (seeded, deterministic, in range).</summary>
    public class DepthBandsTests
    {
        [Test]
        public void RidgeAndSkylineFollowTheBiome()
        {
            Assert.AreEqual("backgrounds/earth_forest/ridge_mid", DepthBands.RidgeFor(PlanetId.Earth, 64), "spawn: forest");
            Assert.AreEqual("backgrounds/earth_coast/ridge_mid", DepthBands.RidgeFor(PlanetId.Earth, 2500), "ocean band: the coast ridge");
            Assert.AreEqual("backgrounds/earth_desert/ridge_mid", DepthBands.RidgeFor(PlanetId.Earth, 1500));
            Assert.AreEqual("backgrounds/mars_plains/ridge_mid", DepthBands.RidgeFor(PlanetId.Mars, 100));
            Assert.IsNull(DepthBands.RidgeFor(PlanetId.Venus, 0), "no bands yet off Earth and Mars");
            Assert.AreEqual("backgrounds/earth/skyline_far", DepthBands.SkylineFor(PlanetId.Earth));
            Assert.AreEqual("backgrounds/mars/skyline_far", DepthBands.SkylineFor(PlanetId.Mars));
            Assert.IsNull(DepthBands.SkylineFor(PlanetId.Mercury));
        }

        [Test]
        public void FloraIsSeededPerColumnAndStaysInItsBand()
        {
            int planted = 0, trees = 0;
            for (int x = 0; x < 4096; x++)
            {
                bool a = DepthBands.FloraAt(PlanetId.Earth, x, out var p1, out float z1, out float yaw1, out float s1);
                bool b = DepthBands.FloraAt(PlanetId.Earth, x, out var p2, out float z2, out float yaw2, out float s2);
                Assert.AreEqual(a, b, $"column {x} deterministic");
                if (!a) continue;
                planted++;
                Assert.AreEqual(p1.key, p2.key);
                Assert.AreEqual(z1, z2);
                Assert.That(z1, Is.InRange(p1.tree ? DepthBands.TreeNearZ : DepthBands.FloraNearZ, p1.tree ? DepthBands.TreeFarZ : DepthBands.FloraFarZ), $"{p1.key} at x {x}: in its depth band (D-071)");
                Assert.That(yaw1, Is.InRange(0f, 360f));
                Assert.That(s1, Is.InRange(0.85f, 1.15f));
                if (p1.tree) trees++;
                StringAssert.StartsWith("props/earth_flora/", p1.key);
            }
            Assert.Greater(planted, 4096 * 0.15f, "Earth is planted (≥ 15 % of columns)");
            Assert.Greater(trees, 100, "with trees");
            Assert.IsFalse(DepthBands.FloraAt(PlanetId.Venus, 10, out _, out _, out _, out _), "no flora table: nothing planted");
        }

        [Test]
        public void TheDesertHasNoOaksAndTheTaigaHasSpruce()
        {
            foreach (var p in DepthBands.FloraFor(PlanetId.Earth, 1500)) StringAssert.DoesNotContain("tree_oak", p.key, "desert");
            bool spruce = false;
            foreach (var p in DepthBands.FloraFor(PlanetId.Earth, 3000)) spruce |= p.key.EndsWith("tree_spruce");
            Assert.IsTrue(spruce, "taiga has spruce");
            Assert.AreEqual(Biome.Taiga, EarthBiomes.At(3000));
        }
    }
}
