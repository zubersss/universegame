using System.IO;
using Meridian.Flora;
using Meridian.Planet.Backdrop;
using Meridian.Planets;
using Meridian.Terrain;
using Meridian.View2D;
using NUnit.Framework;
using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>
    /// U-118: Mars runs the cartoon path like Earth. The scene set follows the Mars region at the spawn (canyon → the B-141 canyon set; every
    /// other region asks for the plains set and falls back to the canyon set until B-141's plains lands), the ground strips are the B-140
    /// regolith / basalt pair by the column's top tile, the plant kinds come from the B-140 rig set's biome lists through the region names,
    /// and the dust storm shows as the storm set's veil whose alpha is the storm's intensity. Pure rules on the live art.
    /// </summary>
    public class MarsStageTests
    {
        static int FindX(string region)
        {
            for (int x = 0; x < 4096; x += 8) if (StageRegions.At(PlanetId.Mars, x) == region) return x;
            return -1;
        }

        [Test]
        public void MarsIsConvertedAndItsSceneSetFollowsTheRegion()
        {
            Assert.IsTrue(CartoonStage.Converted(PlanetId.Mars), "U-118: Mars on the cartoon stage");
            Assert.IsTrue(CartoonStage.Converted(PlanetId.Earth));
            Assert.IsFalse(CartoonStage.Converted(PlanetId.Mercury), "Mercury waits for its own card");
            int canyon = FindX("mars_canyon"), plains = FindX("mars_plains");
            Assert.GreaterOrEqual(canyon, 0, "a canyon region on Mars"); Assert.GreaterOrEqual(plains, 0, "a plains region on Mars");
            Assert.AreEqual("canyon", CartoonStage.SceneFor(PlanetId.Mars, canyon));
            Assert.AreEqual("plains", CartoonStage.SceneFor(PlanetId.Mars, plains));
            Assert.AreEqual("canyon", CartoonStage.MarsFallbackScene, "B-141 exported canyon + storm; plains falls back to the canyon set until it lands");
            Assert.AreEqual("forest", CartoonStage.SceneFor(PlanetId.Earth, 64), "Earth keeps its band rule (the camp is the forest band)");
            foreach (var scene in new[] { "canyon", "storm" })
            {
                string json = $"Assets/_Game/Art/backgrounds/mars/{scene}/{scene}.json";
                Assert.IsTrue(File.Exists(json), json + " (B-141)");
                var layout = SceneLayout.Parse(File.ReadAllText(json));
                Assert.AreEqual(3, layout.layers.Length, scene + ": three layers");
            }
            Assert.AreEqual(0f, CartoonStage.StormAlpha(0f), 1e-6f, "no storm: no veil");
            Assert.AreEqual(1f, CartoonStage.StormAlpha(1f), 1e-6f, "the full storm: the full veil");
            Assert.IsTrue(CartoonStage.StormAlpha(0.5f) > 0.3f && CartoonStage.StormAlpha(0.5f) < 0.7f);
        }

        [Test]
        public void TheMarsStripsAndPlantsFollowTheColumn()
        {
            var keys = GroundStrip.KeysFor(PlanetId.Mars);
            Assert.AreEqual(2, keys.Length, "B-140: regolith + basalt strips");
            Assert.AreEqual("terrain/mars/ground_strip", keys[GroundStrip.Regolith]);
            Assert.AreEqual("terrain/mars/ground_strip_basalt", keys[GroundStrip.Basalt]);
            Assert.AreEqual(GroundStrip.Basalt, GroundStrip.MaterialFor(PlanetId.Mars, TileId.Basalt));
            Assert.AreEqual(GroundStrip.Regolith, GroundStrip.MaterialFor(PlanetId.Mars, TileId.Regolith));
            Assert.AreEqual(GroundStrip.Regolith, GroundStrip.MaterialFor(PlanetId.Mars, TileId.Hematite), "no hematite strip yet: regolith");
            Assert.AreEqual(GroundStrip.Regolith, GroundStrip.MaterialFor(PlanetId.Mars, TileId.Ice), "no ice strip yet: regolith");
            Assert.AreEqual(GroundStrip.Sand, GroundStrip.MaterialFor(PlanetId.Earth, TileId.Sand), "Earth keeps its four");
            Assert.AreSame(GroundStrip.Keys, GroundStrip.KeysFor(PlanetId.Earth));
            foreach (var k in keys)
            {
                string json = "Assets/_Game/Art/" + k + ".json";
                Assert.IsTrue(File.Exists(json), json);
                var s = JsonUtility.FromJson<GroundStripTests.Sheet>(File.ReadAllText(json));
                Assert.AreEqual(64, s.frame_width); Assert.AreEqual(152, s.frame_height); Assert.AreEqual(128, s.ground_line_px); Assert.AreEqual(8, s.frames);
            }
            // The plants: the region names in the B-140 rig set's biome vocabulary (plains / canyon / polar / highlands), every region with at least one kind.
            var set = RigSet.Parse(File.ReadAllText("Assets/_Game/Art/flora/mars/rigset.json"), out var error);
            Assert.IsNull(error, "the Mars rig set parses");
            foreach (var region in new[] { "mars_plains", "mars_canyon", "mars_polar", "mars_tharsis" })
            {
                int x = FindX(region);
                if (x < 0) { TestContext.Out.WriteLine($"[MERIDIAN] no {region} on this Mars"); continue; }
                string biome = FloraRigs.BiomeNameAt(PlanetId.Mars, x);
                Assert.NotNull(biome, region);
                var kinds = FloraRigs.PlantsFor(set, biome);
                Assert.GreaterOrEqual(kinds.Length, 1, $"{region} → {biome}: at least one kind");
                TestContext.Out.WriteLine($"[MERIDIAN] {region} (x {x}) → {biome}: {kinds.Length} kinds");
            }
            Assert.AreEqual("canyon", FloraRigs.BiomeNameAt(PlanetId.Mars, FindX("mars_canyon")));
            Assert.AreEqual("highlands", FloraRigs.BiomeNameAt(PlanetId.Mars, FindX("mars_tharsis")), "Tharsis is the rig set's highlands");
        }
    }
}
