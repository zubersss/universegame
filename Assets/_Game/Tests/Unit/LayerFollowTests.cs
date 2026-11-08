using Meridian.View2D;
using NUnit.Framework;

namespace Meridian.Tests
{
    /// <summary>U-122 (D-135): the painted layers follow the camera from the anchor up and hold their datum pose below it, so they never cross in a pit, a pool or the trench.</summary>
    public class LayerFollowTests
    {
        [Test]
        public void TheLayersHoldTheirDatumPoseUnderTheAnchor()
        {
            Assert.AreEqual(343f, ParallaxLayers.FollowY(343f, 342.4f), 1e-6f, "above the anchor: the camera");
            Assert.AreEqual(742f, ParallaxLayers.FollowY(742f, 342.4f), 1e-6f, "the climb: the camera");
            Assert.AreEqual(342.4f, ParallaxLayers.FollowY(325f, 342.4f), 1e-6f, "a pool 17 m down: the anchor");
            Assert.AreEqual(342.4f, ParallaxLayers.FollowY(100f, 342.4f), 1e-6f, "the trench: the anchor");
            // Every layer then sits where it sits on the pad: the same y for a camera at the anchor and one far below it.
            foreach (var p in new[] { 0.1f, 0.35f, 0.6f })
                Assert.AreEqual(ParallaxMath.LayerY(342.4f, 342.4f, 337f, -1f, p), ParallaxMath.LayerY(ParallaxLayers.FollowY(300f, 342.4f), 342.4f, 337f, -1f, p), 1e-5f);
            Assert.AreEqual(2, SpriteCharacterView.FlashFrames, "U-089's two white frames on the drawn surveyor");
        }

        /// <summary>U-128: each band has its own datum (the camp band its stamped surface, the ocean its water line, the plains datum + 6), blended over the ±48-column border; Mars by landform; the set follows the camera's band through a smooth 1.5 s crossfade.</summary>
        [Test]
        public void TheDatumFollowsTheBandAndTheCampKeepsItsSurface()
        {
            var d = new BandDatum(Meridian.Planets.PlanetId.Earth, 320f, 64, 337f);
            Assert.AreEqual(337f, d.At(64), 1e-4f, "the camp band keeps the stamped camp surface");
            Assert.AreEqual(337f, d.At(300), 1e-4f, "the whole forest band");
            Meridian.Terrain.EarthBiomes.Range(Meridian.Terrain.Biome.Ocean, out int os, out int ol);
            Assert.AreEqual(321f, d.At(os + ol / 2), 1e-4f, "the ocean band: the water line (datum + 1)");
            Meridian.Terrain.EarthBiomes.Range(Meridian.Terrain.Biome.Plains, out int ps, out int pl);
            Assert.AreEqual(326f, d.At(ps + pl / 2), 1e-4f, "the plains: datum + 6");
            Assert.AreEqual(ps, 700, "the forest → plains border (U-037)");
            float prev = d.At(ps - 48);
            Assert.AreEqual(337f, prev, 1e-3f, "48 columns before the border: still the forest");
            for (int x = ps - 47; x <= ps + 48; x++) { float v = d.At(x); Assert.LessOrEqual(v, prev + 1e-4f, $"x {x}: falls toward the plains"); prev = v; }
            Assert.AreEqual(326f, d.At(ps + 48), 1e-3f, "48 columns in: the plains");
            Assert.AreEqual(d.At(ps - 1), d.At(ps), 0.5f, "no step at the border column");
            var m = new BandDatum(Meridian.Planets.PlanetId.Mars, 320f, 600, 325f);
            Assert.AreEqual(325f, m.At(600), 1e-4f, "the Mars spawn plateau");
            Assert.AreEqual(320f - Meridian.Terrain.MarsLandforms.CanyonDepth, m.At((Meridian.Terrain.MarsLandforms.CanyonStart + Meridian.Terrain.MarsLandforms.CanyonEnd) / 2), 1e-4f, "the canyon floor");
            Assert.AreEqual(320f + Meridian.Terrain.MarsLandforms.OlympusHeight * 0.5f, m.At(Meridian.Terrain.MarsLandforms.OlympusCenter), 1e-4f, "Olympus mid-slope");
            Assert.Less(m.At(Meridian.Terrain.MarsLandforms.CanyonStart + 10), 325f, "blending down into the canyon");
            Assert.Greater(m.At(Meridian.Terrain.MarsLandforms.CanyonStart + 10), 320f - Meridian.Terrain.MarsLandforms.CanyonDepth, "not yet the floor");
            Assert.AreEqual(0f, CartoonStage.CrossfadeAlpha(0f, 1.5f), 1e-6f);
            Assert.AreEqual(1f, CartoonStage.CrossfadeAlpha(1.5f, 1.5f), 1e-6f);
            Assert.AreEqual(0.5f, CartoonStage.CrossfadeAlpha(0.75f, 1.5f), 1e-6f);
            Assert.AreEqual("forest", CartoonStage.SceneFor(Meridian.Planets.PlanetId.Earth, ps - 50));
            Assert.AreEqual("plains", CartoonStage.SceneFor(Meridian.Planets.PlanetId.Earth, ps + 50));
            Assert.AreEqual("coast", CartoonStage.SceneFor(Meridian.Planets.PlanetId.Earth, os + 16), "the shore at 2096 asks for the coast set");
        }

        const int W = 4096;
        // A Mercury-like world: the plain at 320 with gentle noise (±5 m), the two cold-trap bowls; a POI stamp at 1000..1019.
        static float Plain(int x) => 320f + 5f * UnityEngine.Mathf.Sin(x * 0.3f);
        static float Band(int x) => Plain(x) + Meridian.Terrain.MercuryLandforms.ColdTrapProfile(x, W);

        /// <summary>U-139 (the 0.4.5 smoke: the set 6 m under the flare shelter's plateau): across a stamped plateau the datum is the stamped surface,
        /// blended back to the plain over the stamp's shoulders; the pad keeps its measured surface; the plain's noise is one gentle line.</summary>
        [Test]
        public void TheDatumFollowsAStampedPlateau()
        {
            System.Func<int, float> final = x => x >= 1000 && x < 1020 ? 326f : Band(x);
            var d = new BandDatum(Meridian.Planets.PlanetId.Mercury, 320f, 64, 318f, W, Band, final, new[] { 1000, 20 });
            Assert.AreEqual(326f, d.At(1010), 1e-3f, "on the plateau: its stamped surface");
            Assert.AreEqual(326f, d.At(1000), 1e-3f, "its first column");
            Assert.AreEqual(318f, d.At(64), 1e-3f, "the pad holds its measured surface (the u123 frames)");
            Assert.AreEqual(318f, d.At(64 + BandDatum.PadHold), 1e-3f, "for PadHold columns");
            Assert.AreEqual(320f, d.At(3000), 0.6f, "the plain (clear of both traps): its ±5 m noise averaged to one line");
            Assert.Less(UnityEngine.Mathf.Abs(d.At(1060) - d.At(1061)), 0.5f, "past the shoulders no step");
        }

        /// <summary>U-139 (the 0.4.5 smoke: the set 3 m over the solarite field's terrace, a grey bar and black under it): a stamp lower than the
        /// plain pulls the datum down to it.</summary>
        [Test]
        public void TheDatumFollowsAStampedTerrace()
        {
            System.Func<int, float> final = x => x >= 1800 && x < 1830 ? 317f : Band(x);
            var d = new BandDatum(Meridian.Planets.PlanetId.Mercury, 320f, 64, 318f, W, Band, final, new[] { 1800, 30 });
            Assert.AreEqual(317f, d.At(1815), 1e-3f, "on the terrace: within 1 m of the walking surface");
            Assert.AreEqual(317f, d.At(1829), 1e-3f);
        }

        /// <summary>U-139 keeps D-146's cold traps: the bowl is added back unsmoothed, so the night set still meets a trap's floor.</summary>
        [Test]
        public void TheColdTrapFloorStaysExact()
        {
            var d = new BandDatum(Meridian.Planets.PlanetId.Mercury, 320f, 64, 318f, W, Band, Band, new int[0]);
            int c = Meridian.Terrain.MercuryLandforms.ColdTrapCentre(0, W);
            Assert.AreEqual(Band(c), d.At(c), 1e-3f, "the trap's floor: D-146's own column from the rim in");
            Assert.Less(d.At(c), 300f, "and 36 m down");
        }

        /// <summary>U-139: Venus's surface set follows its tesserae (55 m up) instead of standing at the entry's height.</summary>
        [Test]
        public void VenusFollowsItsTesserae()
        {
            System.Func<int, float> venus = x => 250f + (x >= 600 && x < 1100 ? 55f : 0f);
            var d = new BandDatum(Meridian.Planets.PlanetId.Venus, 250f, 64, 250f, W, venus, venus, new int[0]);
            Assert.AreEqual(305f, d.At(850), 1e-3f, "the tessera's top");
            Assert.AreEqual(250f, d.At(300), 1e-3f, "the plain");
            Assert.AreEqual(250f, new BandDatum(Meridian.Planets.PlanetId.Venus, 250f, 64, 250f).At(850), 1e-3f, "without the surfaces (pure tests): the entry's height");
        }

        /// <summary>U-139 (LEAD 16:1x): Mars keeps its U-128 bands and takes its ground POIs' stamped surface (the hauler, the outpost, the beacon)
        /// across each stamp, back over the shoulders; away from the stamps nothing moves.</summary>
        [Test]
        public void MarsTakesItsStampsOnItsBands()
        {
            System.Func<int, float> final = x => x >= 900 && x < 930 ? 352f : 0f;
            var d = new BandDatum(Meridian.Planets.PlanetId.Mars, 340f, 64, 341f, W, null, final, new[] { 900, 30 });
            var bands = new BandDatum(Meridian.Planets.PlanetId.Mars, 340f, 64, 341f, W);
            Assert.AreEqual(352f, d.At(915), 1e-3f, "on the hauler's stamp: its ground");
            Assert.AreEqual(bands.At(2000), d.At(2000), 1e-4f, "away from the stamps: the bands as they were");
            Assert.AreEqual(bands.At(64), d.At(64), 1e-4f, "the camp's frames unchanged");
        }

        /// <summary>
        /// U-161 (U-156's 8_snow frame: the taiga's set 6 m over the smoothed ground): on a smooth Earth the stage datum (the sets' painted ground
        /// line) follows the walking curve: on 3 seeds, at every land column of every biome (sampled each 7 m), within 1 m of the curve; over the
        /// sea the water line; the camp keeps its pad surface; and the curve-following datum has no step between neighbouring columns above the
        /// walkable slope. The desert, taiga and tundra draw their own B-179 sets.
        /// </summary>
        [Test]
        public void OnTheSmoothGroundEverySetSitsOnTheWalkingCurve()
        {
            var cfg = UnityEditor.AssetDatabase.LoadAssetAtPath<Meridian.Planets.PlanetConfig>($"{Meridian.EditorTools.PlanetConfigAuthoring.Folder}/Earth.asset");
            Assert.NotNull(cfg, "Earth's config");
            int w = cfg.worldWidth;
            foreach (int seed in new[] { 1969, 7717, 31337 })
            {
                var gen = new Meridian.Terrain.SolidWorldGenerator(cfg, seed);
                var tops = new int[w];
                for (int x = 0; x < w; x++)
                    tops[x] = Meridian.Planet.POI.PoiStamp.JointGround(gen, cfg.datumY, Meridian.Planets.PlanetId.Earth, x, out int g) ? g : gen.SurfaceHeight(x); // TerrainStreamer.WallTop
                System.Func<int, int> top = x => tops[((x % w) + w) % w];
                System.Func<int, int> pad = x => Meridian.Planet.POI.PoiStamp.PadAt(gen, cfg.datumY, Meridian.Planets.PlanetId.Earth, x);
                System.Func<int, float> curve = x => Meridian.Terrain.GroundField.Curve(x, top, pad); // TerrainStreamer.CurveAt
                float spawn = curve(64);
                var d = new BandDatum(Meridian.Planets.PlanetId.Earth, cfg.datumY, 64, spawn, w, null, null, null, curve);
                Assert.IsTrue(d.FollowsCurve);
                Assert.AreEqual(spawn, d.At(64), 0.05f, $"seed {seed}: the camp keeps its pad surface");
                float sea = Meridian.Terrain.EarthBiomes.MeanSurface(Meridian.Terrain.Biome.Ocean, cfg.datumY);
                var worst = new System.Collections.Generic.Dictionary<Meridian.Terrain.Biome, float>();
                float worstStep = 0f;
                for (int x = 0; x < w; x += 7)
                {
                    var b = Meridian.Terrain.EarthBiomes.At(x);
                    float c = curve(x), v = d.At(x);
                    if (b == Meridian.Terrain.Biome.Ocean && c < sea) { Assert.GreaterOrEqual(v, sea - 1f, $"seed {seed} x {x}: over the sea, the water line"); continue; }
                    float err = UnityEngine.Mathf.Abs(v - c);
                    if (!worst.TryGetValue(b, out float e) || err > e) worst[b] = err;
                    Assert.LessOrEqual(err, 1f, $"seed {seed} x {x} ({b}): the set's ground line {v:F2} within 1 m of the walking surface {c:F2}");
                    worstStep = UnityEngine.Mathf.Max(worstStep, UnityEngine.Mathf.Abs(d.At(x + 1) - v));
                }
                Assert.LessOrEqual(worstStep, Meridian.Terrain.GroundField.MaxWalkSlope + 1e-3f, $"seed {seed}: no step in the datum");
                foreach (var kv in worst) NUnit.Framework.TestContext.Out.WriteLine($"[MERIDIAN] u161 seed {seed} {kv.Key}: worst set-to-surface gap {kv.Value:F3} m");
            }
            Assert.AreEqual("desert", CartoonStage.SceneFor(Meridian.Terrain.Biome.Desert));
            Assert.AreEqual("taiga", CartoonStage.SceneFor(Meridian.Terrain.Biome.Taiga));
            Assert.AreEqual("tundra", CartoonStage.SceneFor(Meridian.Terrain.Biome.Tundra));
        }
    }
}
