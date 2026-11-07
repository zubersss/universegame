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
    }
}
