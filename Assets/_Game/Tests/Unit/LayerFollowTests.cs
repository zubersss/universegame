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
    }
}
