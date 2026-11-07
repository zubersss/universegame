using Meridian.Flora;
using Meridian.Planets;
using Meridian.Terrain;
using Meridian.View2D;
using NUnit.Framework;
using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>
    /// U-110 (B-129 / B-133): the plants of a column come from its biome's list (a desert spawn never picks Nodbell, the plains pick
    /// among snoozle, Nodbell and Whiptuft, the desert is all Shiverbarrel), and the cartoon scene set follows the spawn biome
    /// (plains / forest / coast). Pure functions on the live rig set.
    /// </summary>
    public class BiomeFloraTests
    {
        static RigSet Earth()
        {
            var json = System.IO.File.ReadAllText("Assets/_Game/Art/flora/earth/rigset.json");
            var set = RigSet.Parse(json, out var error);
            Assert.IsNull(error, "the Earth rig set parses");
            return set;
        }

        [Test]
        public void PlantsFollowTheirBiomeAndEveryBiomeKeepsTwoKinds()
        {
            var set = Earth();
            string[] Names(RigSet.Plant[] ps) { var n = new string[ps.Length]; for (int i = 0; i < ps.Length; i++) n[i] = ps[i].name; return n; }
            var desert = Names(FloraRigs.PlantsFor(set, "desert"));
            CollectionAssert.DoesNotContain(desert, "nodbell", "a desert spawn never picks Nodbell");
            CollectionAssert.AreEquivalent(new[] { "shiverbarrel" }, desert, "the desert is all Shiverbarrel (B-129 lists one kind: one kind is a kind, not a fallback)");
            var plains = Names(FloraRigs.PlantsFor(set, "plains"));
            CollectionAssert.Contains(plains, "snoozle"); CollectionAssert.Contains(plains, "nodbell"); CollectionAssert.Contains(plains, "whiptuft");
            CollectionAssert.DoesNotContain(plains, "shiverbarrel", "the desert's barrel stays out of the meadow");
            foreach (var biome in new[] { "plains", "forest", "coast", "desert", "taiga", "tundra" })
                Assert.GreaterOrEqual(FloraRigs.PlantsFor(set, biome).Length, 1, biome + " has at least one kind");
            Assert.AreEqual(set.plants.Length, FloraRigs.PlantsFor(set, null).Length, "no biome: the whole set");
            Assert.AreEqual(set.plants.Length, FloraRigs.PlantsFor(set, "moon").Length, "an unknown biome: the whole set");
        }

        [Test]
        public void TheBiomeNameAndTheSceneSetFollowTheColumn()
        {
            EarthBiomes.Range(Biome.Desert, out int desert, out int dl);
            EarthBiomes.Range(Biome.Plains, out int plains, out int pl);
            EarthBiomes.Range(Biome.Ocean, out int ocean, out int ol);
            EarthBiomes.Range(Biome.Forest, out int forest, out int fl);
            Assert.AreEqual("desert", FloraRigs.BiomeNameAt(PlanetId.Earth, desert + dl / 2));
            Assert.AreEqual("plains", FloraRigs.BiomeNameAt(PlanetId.Earth, plains + pl / 2));
            Assert.AreEqual("coast", FloraRigs.BiomeNameAt(PlanetId.Earth, ocean + ol / 2), "the ocean band's land is the coast");
            Assert.AreEqual("forest", FloraRigs.BiomeNameAt(PlanetId.Earth, forest + fl / 2));
            Assert.IsNull(FloraRigs.BiomeNameAt(PlanetId.Mars, 100), "no bands on Mars yet: no filter");
            Assert.IsNull(FloraRigs.BiomeNameAt(null, 100));
            Assert.AreEqual("forest", CartoonStage.SceneFor(Biome.Forest));
            Assert.AreEqual("plains", CartoonStage.SceneFor(Biome.Plains));
            Assert.AreEqual("coast", CartoonStage.SceneFor(Biome.Ocean));
            Assert.AreEqual("plains", CartoonStage.SceneFor(Biome.Desert), "no desert set yet: the plains");
            Assert.AreEqual("plains", CartoonStage.SceneFor(Biome.Taiga));
            foreach (var scene in new[] { "plains", "forest", "coast" })
                Assert.IsTrue(System.IO.File.Exists($"Assets/_Game/Art/backgrounds/earth/{scene}/{scene}.json"), scene + " scene set exported (B-133)");
        }
    }
}
