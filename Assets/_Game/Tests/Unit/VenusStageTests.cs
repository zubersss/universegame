using Meridian.Flora;
using Meridian.Planets;
using Meridian.Terrain;
using Meridian.View2D;
using NUnit.Framework;
using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>
    /// U-125: Venus runs the cartoon path. The set follows the camera's height (B-152's cloud deck above, the surface dive below, with a dead band so a
    /// hover on the line never flickers); the deck set hangs off the cloud deck, the surface set off the ground; the strips are B-153's basalt crust on the
    /// ground and the deck planks along the floating station; the plants take the rig set's vocabulary (vent_fields / surface_plains on the ground); the
    /// Vent eel is a den species (D-126). Pure rules; the art checks bite once B-152 / B-153 / B-154 land.
    /// </summary>
    public class VenusStageTests
    {
        [Test]
        public void TheSetFollowsTheCamerasHeightWithADeadBand()
        {
            Assert.IsTrue(CartoonStage.Converted(PlanetId.Venus), "U-125: Venus is on the cartoon path");
            Assert.AreEqual(CartoonStage.VenusSurfaceScene, CartoonStage.VenusSceneFor(300f, null), "on the ground: the surface dive");
            Assert.AreEqual(CartoonStage.VenusDeckScene, CartoonStage.VenusSceneFor(VenusLandforms.DeckY, null), "on the station: the cloud deck");
            Assert.AreEqual(CartoonStage.VenusDeckScene, CartoonStage.VenusSceneFor(CartoonStage.VenusDeckEnterY, CartoonStage.VenusSurfaceScene), "the deck takes over at its line");
            Assert.AreEqual(CartoonStage.VenusSurfaceScene, CartoonStage.VenusSceneFor(CartoonStage.VenusDeckLeaveY, CartoonStage.VenusDeckScene), "and hands back at the lower line");
            float mid = (CartoonStage.VenusDeckEnterY + CartoonStage.VenusDeckLeaveY) * 0.5f;
            Assert.AreEqual(CartoonStage.VenusSurfaceScene, CartoonStage.VenusSceneFor(mid, CartoonStage.VenusSurfaceScene), "inside the band a climb keeps the surface");
            Assert.AreEqual(CartoonStage.VenusDeckScene, CartoonStage.VenusSceneFor(mid, CartoonStage.VenusDeckScene), "and a descent keeps the deck: no flicker");
            Assert.AreEqual(CartoonStage.VenusSurfaceScene, CartoonStage.FallbackFor(PlanetId.Venus), "a set not exported yet: the surface stands in");
            Assert.Less(CartoonStage.VenusDeckEnterY, VenusLandforms.DeckY - VenusLandforms.DeckHalfBand + 15f, "the deck set is up before the station's band");
        }

        [Test]
        public void EachSetHangsOffItsOwnLevel()
        {
            Assert.AreEqual(VenusLandforms.DeckY - 2f, CartoonStage.VenusDatumFor(CartoonStage.VenusDeckScene, 250f), "the deck set off the cloud deck");
            Assert.AreEqual(250f, CartoonStage.VenusDatumFor(CartoonStage.VenusSurfaceScene, 250f), "the surface set off the ground's band datum");
        }

        [Test]
        public void TheCrustLinesTheGroundAndThePlanksTheStation()
        {
            CollectionAssert.AreEqual(new[] { "terrain/venus/ground_strip", "terrain/venus/ground_strip_deck" }, GroundStrip.KeysFor(PlanetId.Venus), "B-153's two kinds");
            foreach (var tile in new[] { TileId.VenusBasalt, TileId.Tessera, TileId.Sulfur, TileId.VentGlass })
                Assert.AreEqual(GroundStrip.VenusCrust, GroundStrip.MaterialFor(PlanetId.Venus, tile), $"tile {tile}: the crust (the planks are never a column's)");
            var decks = GroundStrip.DecksFor(PlanetId.Venus);
            Assert.AreEqual(1, decks.Count, "one floating station: the Meridian station");
            var station = Meridian.Planet.POI.PoiCatalog.MeridianStation;
            Assert.AreEqual(station.x, decks[0].x, "the run starts at the station's x");
            Assert.AreEqual(station.x + station.floatWidth, decks[0].y, "and spans its deck");
            Assert.AreEqual(station.floatY + Meridian.Planet.POI.PoiCatalog.DeckTop, decks[0].z, 1e-4f, "on the aerostat decks' top");
            Assert.AreEqual(0, GroundStrip.DecksFor(PlanetId.Earth).Count, "no floating decks elsewhere");
            Assert.AreEqual(0, GroundStrip.DecksFor(PlanetId.Mercury).Count);
        }

        [Test]
        public void ThePlantsTakeTheRigSetsVocabulary()
        {
            int vent = (VenusLandforms.Vents[0].x0 + VenusLandforms.Vents[0].x1) / 2;
            Assert.AreEqual("vent_fields", FloraRigs.BiomeNameAt(PlanetId.Venus, vent), "over a vent field");
            Assert.AreEqual("surface_plains", FloraRigs.BiomeNameAt(PlanetId.Venus, 300), "on the plains");
            int tessera = (VenusLandforms.Tesserae[0].x0 + VenusLandforms.Tesserae[0].x1) / 2;
            Assert.AreEqual("surface_plains", FloraRigs.BiomeNameAt(PlanetId.Venus, tessera), "the tesserae count as plains for the plants");
            Assert.AreEqual("cloud_deck", FloraRigs.VenusDeck);
            Assert.AreEqual("station_rails", FloraRigs.VenusRails);
        }

        [Test]
        public void TheVentEelDensAndTheDeckSpeciesStayOnTheDeck()
        {
            var eel = Meridian.Creatures.SpeciesSpec.Get(Meridian.Creatures.Species.VentEel);
            Assert.AreEqual(PlanetId.Venus, eel.planet);
            Assert.AreEqual("creatures/venus/vent_eel", eel.artKey);
            Assert.IsTrue(eel.HasDen);
            Assert.AreEqual("props/venus/vent_mouth", eel.den, "D-126: the vent mouth is a separate prop drawn in front (B-154)");
            Assert.IsFalse(Meridian.Creatures.SpeciesSpec.Get(Meridian.Creatures.Species.PressureCrab).HasDen, "the crab walks the open plain");
            Assert.AreEqual("creatures/venus/sulfur_drifter", Meridian.Creatures.SpeciesSpec.Get(Meridian.Creatures.Species.SulfurDrifter).artKey, "the drifter takes its sheet by key");
            Assert.AreEqual("creatures/venus/acidmoth", Meridian.Creatures.SpeciesSpec.Get(Meridian.Creatures.Species.Acidmoth).artKey);
            // B-168: a v3 deck carries its standing row in its json; the catalog's 128 px/m row is only the fallback.
            Assert.AreEqual(37, Meridian.Planet.POI.PoiPlacer.StandRow("{\"key\":\"props/venus/aerostat_deck\",\"top_row\":37,\"stand_line\":2.14}"));
            Assert.AreEqual(-1, Meridian.Planet.POI.PoiPlacer.StandRow("{\"key\":\"props/venus/station_hull_a\"}"), "no top_row: the catalog's");
            Assert.AreEqual(-1, Meridian.Planet.POI.PoiPlacer.StandRow(null));
        }
    }
}
