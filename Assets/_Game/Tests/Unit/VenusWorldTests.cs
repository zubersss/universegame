using Meridian.Planet.Weather;
using Meridian.Planets;
using Meridian.Terrain;
using NUnit.Framework;
using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>U-050 (EditMode): Venus landforms and materials, the super-rotation wind profile and cycle.</summary>
    public class VenusWorldTests
    {
        static PlanetConfig Venus()
        {
            var c = ScriptableObject.CreateInstance<PlanetConfig>();
            c.id = PlanetId.Venus; c.worldWidth = 4096; c.worldHeight = 1000; c.datumY = 320;
            return c;
        }

        [Test]
        public void VentFieldsAreGlassUnderSulfurAndTesseraeStandHigh()
        {
            var gen = new SolidWorldGenerator(Venus(), 1969);
            var vent = VenusLandforms.Vents[0];
            int vx = (vent.x0 + vent.x1) / 2, top = gen.SurfaceHeight(vx);
            Assert.AreEqual(VenusFeature.VentField, VenusLandforms.At(vx));
            Assert.AreEqual(TileId.Sulfur, gen.TileAt(vx, top), "sulfur crust");
            Assert.AreEqual(TileId.VentGlass, gen.TileAt(vx, top - 2), "Vitriol Glass under it (§7.4)");
            var t = VenusLandforms.Tesserae[0];
            int tx = (t.x0 + t.x1) / 2;
            Assert.AreEqual(TileId.Tessera, gen.TileAt(tx, gen.SurfaceHeight(tx)));
            float plains = 0f; int n = 0;
            for (int x = 1800; x < 2300; x += 10) { plains += gen.SurfaceHeight(x); n++; }
            Assert.Greater(gen.SurfaceHeight(tx), plains / n + 25f, "highlands stand above the plains");
            Assert.AreEqual(VenusFeature.Plains, VenusLandforms.At(2000));
        }

        [Test]
        public void WindIsCalmBelowAndStreamsOneWayOnTheDeck()
        {
            Assert.AreEqual(0f, VenusWind.SpeedAt(320f, 0), 1e-4f, "calm at the surface");
            Assert.AreEqual(0f, VenusWind.SpeedAt(VenusWind.CalmBelow - 1f, 1234), 1e-4f);
            float deckLow = VenusWind.SpeedAt(VenusLandforms.DeckY, 0);
            float deckHigh = VenusWind.SpeedAt(VenusLandforms.DeckY, VenusWind.CycleRealSeconds * 0.5);
            Assert.AreEqual(VenusWind.BaseSpeed, deckLow, 1e-3f, "the floor of the cycle");
            Assert.AreEqual(VenusWind.BaseSpeed + VenusWind.SwellSpeed, deckHigh, 1e-3f, "the swell 40 minutes later");
            Assert.AreEqual(deckLow, VenusWind.SpeedAt(VenusLandforms.DeckY, VenusWind.CycleRealSeconds), 1e-3f, "an 80-minute cycle");
            for (double s = 0; s < VenusWind.CycleRealSeconds; s += 300) Assert.Greater(VenusWind.SpeedAt(760f, s), 0f, "never reverses");
        }
    }
}
