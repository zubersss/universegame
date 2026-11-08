using Meridian.Flora;
using Meridian.Planets;
using Meridian.Terrain;
using Meridian.Terrain.CloudColumn;
using Meridian.View2D;
using NUnit.Framework;

namespace Meridian.Tests
{
    /// <summary>
    /// U-129 slice 1: Saturn runs the cartoon path on Jupiter's deck machinery (a "decked giant"): B-157's deck1 / deck2 / deck3 / deep by the
    /// camera's band, each off its band's floor; the North Polar Hexagon is a 900 m zone with B-157's hexagon overlay faded in; the floes draw
    /// the ice and ring-rock strips (10 frames, U-126's caps); the plants take the rig set's vocabulary (deck1 / deck2 / deck3 / hexagon).
    /// </summary>
    public class SaturnStageTests
    {
        [Test]
        public void SaturnSharesTheDeckMachinery()
        {
            Assert.IsTrue(CartoonStage.Converted(PlanetId.Saturn), "U-129: Saturn is on the cartoon path");
            Assert.IsTrue(CartoonStage.Decked(PlanetId.Saturn) && CartoonStage.Decked(PlanetId.Jupiter));
            Assert.IsFalse(CartoonStage.Decked(PlanetId.Venus) || CartoonStage.Decked(PlanetId.Earth), "the solid worlds are not decked");
            Assert.AreEqual(CartoonStage.JupiterDeck1, CartoonStage.FallbackFor(PlanetId.Saturn), "deck1 stands in for a set not exported yet");
            Assert.AreEqual(CartoonStage.SaturnHexagonScene, CartoonStage.OverlayFor(PlanetId.Saturn), "Saturn's overlay is the Hexagon");
            Assert.AreEqual(CartoonStage.JupiterSpotScene, CartoonStage.OverlayFor(PlanetId.Jupiter), "Jupiter's the Red Spot");
        }

        [Test]
        public void TheHexagonIsANineHundredMetreZoneWithItsOverlay()
        {
            Assert.AreEqual(900, 2 * CloudLayout.HexagonHalfWidth, "Bible §7.7: a 900 m zone");
            Assert.IsTrue(CloudLayout.InHexagon(CloudLayout.HexagonCentre));
            Assert.IsFalse(CloudLayout.InHexagon(CloudLayout.HexagonCentre + CloudLayout.HexagonHalfWidth + 1));
            Assert.IsFalse(CloudLayout.InHexagon(CloudLayout.RedSpotCentre), "the Hexagon and the Red Spot do not overlap");
            Assert.AreEqual(1f, CartoonStage.OverlayAlpha(PlanetId.Saturn, CloudLayout.HexagonCentre), 1e-5f);
            Assert.AreEqual(0f, CartoonStage.OverlayAlpha(PlanetId.Saturn, CloudLayout.HexagonCentre + CloudLayout.HexagonHalfWidth + CartoonStage.SpotFade), 1e-5f);
            Assert.AreEqual(0f, CartoonStage.OverlayAlpha(PlanetId.Saturn, CloudLayout.RedSpotCentre), 1e-5f, "no Hexagon over the Red Spot's columns");
            Assert.AreEqual(1f, CartoonStage.OverlayAlpha(PlanetId.Jupiter, CloudLayout.RedSpotCentre), 1e-5f, "Jupiter keeps the Spot");
        }

        [Test]
        public void TheFloesAreIceAndRingRock()
        {
            CollectionAssert.AreEqual(new[] { "terrain/saturn/floe_strip_ice", "terrain/saturn/floe_strip_ring" }, GroundStrip.KeysFor(PlanetId.Saturn));
            Assert.AreEqual(GroundStrip.SaturnIce, GroundStrip.SaturnStripFor(TileId.FloeIce));
            Assert.AreEqual(GroundStrip.SaturnRing, GroundStrip.SaturnStripFor(TileId.FloeCore), "the ring-rock floes: the cores");
        }

        [Test]
        public void ThePlantsTakeTheRigSetsVocabulary()
        {
            Assert.AreEqual("deck1", FloraRigs.SaturnBiomeFor(3000, 1000f));
            Assert.AreEqual("deck2", FloraRigs.SaturnBiomeFor(3000, 750f));
            Assert.AreEqual("deck3", FloraRigs.SaturnBiomeFor(3000, 400f));
            Assert.IsNull(FloraRigs.SaturnBiomeFor(3000, 200f), "the deep grows nothing");
            Assert.AreEqual("hexagon", FloraRigs.SaturnBiomeFor(CloudLayout.HexagonCentre, 750f), "the Hexagon's eye: hexmoss");
        }
    }
}
