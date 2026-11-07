using Meridian.Flora;
using Meridian.Planets;
using Meridian.Terrain;
using Meridian.Terrain.CloudColumn;
using Meridian.View2D;
using NUnit.Framework;

namespace Meridian.Tests
{
    /// <summary>
    /// U-127 slice 1: Jupiter runs the cartoon path. The set follows the camera's band of the cloud column (B-155's deck1 / deck2 / deck3 / deep,
    /// a dead band at each border), each hung off its band's floor (the deep set's CRUSH band on the Crush Line); the Great Red Spot is a 600 m zone
    /// with its overlay faded in; the floes draw B-155's 10-frame strips (ice, core, the spot's brick) with U-126's caps; the plants take the rig
    /// set's vocabulary (deck1 / deck2 / deck3 / red_spot). Pure rules; the art checks bite once B-159 lands.
    /// </summary>
    public class JupiterStageTests
    {
        [Test]
        public void TheSetFollowsTheBandWithADeadBand()
        {
            Assert.IsTrue(CartoonStage.Converted(PlanetId.Jupiter), "U-127: Jupiter is on the cartoon path");
            Assert.AreEqual(CartoonStage.JupiterDeck1, CartoonStage.JupiterSceneAt(1000f));
            Assert.AreEqual(CartoonStage.JupiterDeck1, CartoonStage.JupiterSceneAt(1300f), "above the Datum: deck1's sky");
            Assert.AreEqual(CartoonStage.JupiterDeck2, CartoonStage.JupiterSceneAt(750f));
            Assert.AreEqual(CartoonStage.JupiterDeck3, CartoonStage.JupiterSceneAt(450f));
            Assert.AreEqual(CartoonStage.JupiterDeep, CartoonStage.JupiterSceneAt(200f));
            Assert.AreEqual(CartoonStage.JupiterDeck1, CartoonStage.JupiterSceneFor(890f, CartoonStage.JupiterDeck1), "10 m under deck1's floor: deck1 holds");
            Assert.AreEqual(CartoonStage.JupiterDeck2, CartoonStage.JupiterSceneFor(870f, CartoonStage.JupiterDeck1), "past the hold: deck2");
            Assert.AreEqual(CartoonStage.JupiterDeck2, CartoonStage.JupiterSceneFor(910f, CartoonStage.JupiterDeck2), "10 m over deck2's top: deck2 holds");
            Assert.AreEqual(CartoonStage.JupiterDeck1, CartoonStage.JupiterSceneFor(930f, CartoonStage.JupiterDeck2), "past the hold: deck1");
            Assert.AreEqual(CartoonStage.JupiterDeep, CartoonStage.JupiterSceneFor(150f, null), "no set yet: the band's");
            Assert.AreEqual(CartoonStage.JupiterDeck1, CartoonStage.FallbackFor(PlanetId.Jupiter), "a set not exported yet: deck1 stands in");
        }

        [Test]
        public void EachSetHangsOffItsBandsFloor()
        {
            Assert.AreEqual(CloudLayout.Deck1Bottom, CartoonStage.JupiterFloor(CartoonStage.JupiterDeck1));
            Assert.AreEqual(CloudLayout.Deck2Bottom, CartoonStage.JupiterFloor(CartoonStage.JupiterDeck2));
            Assert.AreEqual(CloudLayout.Deck3Bottom, CartoonStage.JupiterFloor(CartoonStage.JupiterDeck3));
            Assert.AreEqual(CloudLayout.CrushLine, CartoonStage.JupiterFloor(CartoonStage.JupiterDeep), "the deep set's CRUSH band lies on the Crush Line");
            Assert.Less(CartoonStage.JupiterFloor("spot"), 0f, "the overlay is not a band");
        }

        [Test]
        public void TheRedSpotIsASixHundredMetreZoneWithItsOverlay()
        {
            Assert.AreEqual(600, 2 * CloudLayout.RedSpotHalfWidth, "Bible §7.6: a 600 m zone");
            Assert.IsTrue(CloudLayout.InRedSpot(CloudLayout.RedSpotCentre));
            Assert.IsTrue(CloudLayout.InRedSpot(CloudLayout.RedSpotCentre + CloudLayout.RedSpotHalfWidth));
            Assert.IsFalse(CloudLayout.InRedSpot(CloudLayout.RedSpotCentre + CloudLayout.RedSpotHalfWidth + 1));
            Assert.IsTrue(CloudLayout.InRedSpot(CloudLayout.RedSpotCentre - CloudLayout.Width), "the column wraps");
            Assert.AreEqual(1f, CartoonStage.SpotAlpha(CloudLayout.RedSpotCentre), 1e-5f, "inside: the overlay full");
            Assert.AreEqual(0f, CartoonStage.SpotAlpha(CloudLayout.RedSpotCentre + CloudLayout.RedSpotHalfWidth + CartoonStage.SpotFade), 1e-5f, "past the fade: gone");
            float half = CartoonStage.SpotAlpha(CloudLayout.RedSpotCentre + CloudLayout.RedSpotHalfWidth + CartoonStage.SpotFade / 2);
            Assert.Greater(half, 0f); Assert.Less(half, 1f);
            Assert.AreEqual(0f, CartoonStage.SpotAlpha(500), "far from the Spot: none");
        }

        [Test]
        public void TheFloesDrawTheirStripsWithCaps()
        {
            var keys = GroundStrip.KeysFor(PlanetId.Jupiter);
            CollectionAssert.AreEqual(new[] { "terrain/jupiter/floe_strip_ice", "terrain/jupiter/floe_strip_core", "terrain/jupiter/floe_strip_derelict", "terrain/jupiter/floe_strip_spot" }, keys);
            Assert.AreEqual(GroundStrip.FloeIce, GroundStrip.JupiterStripFor(500, TileId.FloeIce), "an ice skin");
            Assert.AreEqual(GroundStrip.FloeCore, GroundStrip.JupiterStripFor(500, TileId.FloeCore), "a core showing on top");
            Assert.AreEqual(GroundStrip.FloeSpot, GroundStrip.JupiterStripFor(CloudLayout.RedSpotCentre, TileId.FloeIce), "the Red Spot's brick floes");
            Assert.IsTrue(GroundStrip.HasCaps(10), "B-155's floe strips are 10 frames: U-126 caps them");
        }

        [Test]
        public void ThePlantsTakeTheRigSetsVocabulary()
        {
            Assert.AreEqual("deck1", FloraRigs.JupiterBiomeFor(500, 1000f));
            Assert.AreEqual("deck2", FloraRigs.JupiterBiomeFor(500, 750f));
            Assert.AreEqual("deck3", FloraRigs.JupiterBiomeFor(500, 400f));
            Assert.IsNull(FloraRigs.JupiterBiomeFor(500, 200f), "the deep grows nothing");
            Assert.AreEqual("red_spot", FloraRigs.JupiterBiomeFor(CloudLayout.RedSpotCentre, 750f), "the Red Spot's floes: phosphor cups");
        }
    }
}
