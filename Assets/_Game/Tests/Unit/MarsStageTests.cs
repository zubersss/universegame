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
            Assert.IsTrue(CartoonStage.Converted(PlanetId.Mercury), "U-123: Mercury too");
            Assert.IsTrue(CartoonStage.Converted(PlanetId.Venus), "U-125: Venus joins");
            Assert.IsFalse(CartoonStage.Converted(PlanetId.Saturn), "Saturn waits for its own card (U-129)");
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
            Assert.AreEqual(3, keys.Length, "B-140: regolith + basalt strips, and the frost strip's key (D-143; the sheet falls back to regolith until it lands)");
            Assert.AreEqual("terrain/mars/ground_strip", keys[GroundStrip.Regolith]);
            Assert.AreEqual("terrain/mars/ground_strip_basalt", keys[GroundStrip.Basalt]);
            Assert.AreEqual("terrain/mars/ground_strip_frost", keys[GroundStrip.Frost]);
            Assert.AreEqual(GroundStrip.Basalt, GroundStrip.MaterialFor(PlanetId.Mars, TileId.Basalt));
            Assert.AreEqual(GroundStrip.Regolith, GroundStrip.MaterialFor(PlanetId.Mars, TileId.Regolith));
            Assert.AreEqual(GroundStrip.Regolith, GroundStrip.MaterialFor(PlanetId.Mars, TileId.Hematite), "no hematite strip yet: regolith");
            Assert.AreEqual(GroundStrip.Frost, GroundStrip.MaterialFor(PlanetId.Mars, TileId.Ice), "D-143: ice takes the frost strip");
            Assert.AreEqual(GroundStrip.Frost, GroundStrip.MaterialFor(PlanetId.Mars, TileId.Snow), "D-143: the cap's CO₂ frost too");
            Assert.AreEqual(TileId.Regolith, Meridian.Planet.POI.PoiStamp.CellTile('#', PlanetId.Mars), "D-143 (2): the Mars pad stamps regolith");
            Assert.AreEqual(TileId.Stone, Meridian.Planet.POI.PoiStamp.CellTile('#', PlanetId.Earth));
            Assert.AreEqual(GroundStrip.Sand, GroundStrip.MaterialFor(PlanetId.Earth, TileId.Sand), "Earth keeps its four");
            Assert.AreSame(GroundStrip.Keys, GroundStrip.KeysFor(PlanetId.Earth));
            foreach (var k in keys)
            {
                string json = "Assets/_Game/Art/" + k + ".json";
                if (k.EndsWith("_frost") && !File.Exists(json)) { TestContext.Out.WriteLine("[MERIDIAN] " + k + ": not exported yet (D-143: BLENDER's B-140 kind); the regolith strip stands in"); continue; }
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

        /// <summary>U-118 (B-142, D-126): the tube lurker is a den species over the lava tubes with props/mars/tube_mound as its den; the polar crawler lives on the ice caps; the Earth table is untouched.</summary>
        [Test]
        public void TheLurkerDensOverTheTubesAndTheCrawlerKeepsToTheIce()
        {
            var lurker = Meridian.Creatures.SpeciesSpec.Get(Meridian.Creatures.Species.TubeLurker);
            Assert.AreEqual(PlanetId.Mars, lurker.planet); Assert.AreEqual("creatures/mars/tube_lurker", lurker.artKey);
            Assert.IsTrue(lurker.HasDen); Assert.AreEqual("props/mars/tube_mound", lurker.den, "D-126: the mound is a separate static prop");
            Assert.AreEqual(Meridian.Creatures.Temper.Flees, lurker.temper, "a shy peeker (D-087)");
            var crawler = Meridian.Creatures.SpeciesSpec.Get(Meridian.Creatures.Species.PolarCrawler);
            Assert.AreEqual("creatures/mars/polar_crawler", crawler.artKey); Assert.IsFalse(crawler.HasDen);
            Assert.Less(crawler.wanderSpeed, 1f, "slow");
            Assert.AreEqual((int)Meridian.Creatures.Species.PolarCrawler, Meridian.Creatures.SpeciesSpec.Count - 1, "appended last");
            var tube = MarsLandforms.Tubes[0];
            Assert.IsTrue(MarsLandforms.OverTube(tube.x0 + 20)); Assert.IsFalse(MarsLandforms.OverTube(tube.x0 - 20));
            var site = new Meridian.Creatures.SpawnSite { x = tube.x0 + 20, surfaceTile = TileId.Regolith, surfaceY = 320, datumY = 320, planet = PlanetId.Mars };
            Assert.IsTrue(lurker.Allows(site), "over a tube on regolith");
            site.x = tube.x0 - 20; Assert.IsFalse(lurker.Allows(site), "off the tubes: no den");
            site.x = tube.x0 + 20; site.surfaceTile = TileId.Ice; Assert.IsFalse(lurker.Allows(site));
            Assert.IsTrue(crawler.Allows(site), "ice: the crawler");
            site.surfaceTile = TileId.Regolith; Assert.IsFalse(crawler.Allows(site));
            Assert.AreEqual("idle_open", Meridian.Creatures.Creature.IdleOpenClip);
            Assert.Greater(Meridian.Creatures.CreatureDirector.DenOrder, 5, "the mound draws in front of the creatures");
        }
    }
}
