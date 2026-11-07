using Meridian.Creatures;
using Meridian.Planets;
using Meridian.Terrain;
using NUnit.Framework;

namespace Meridian.Tests
{
    /// <summary>U-055 (EditMode): the inner-planet roster, its spawn rules (Mercury zones and cold traps, Venus features and deck) and the apex rules.</summary>
    public class InnerCreatureRuleTests
    {
        const int MercuryWidth = 4000;

        static SpawnSite Mercury(int x, MercuryZone zone, float localTime) =>
            new SpawnSite { x = x, planet = PlanetId.Mercury, worldWidth = MercuryWidth, zone = zone, localTime = localTime, surfaceY = 200 };

        [Test]
        public void TheRosterHasItsArtAndOneOfEachApex()
        {
            int mercury = 0, venus = 0;
            foreach (Species s in System.Enum.GetValues(typeof(Species)))
            {
                var spec = SpeciesSpec.Get(s);
                Assert.AreEqual(s, spec.id, "table order");
                Assert.IsTrue(System.IO.File.Exists($"Assets/_Game/Art/{spec.artKey}.json"), spec.artKey);
                if (spec.nightArtKey != null) Assert.IsTrue(System.IO.File.Exists($"Assets/_Game/Art/{spec.nightArtKey}.json"), spec.nightArtKey);
                if (spec.apex) Assert.AreEqual(1, spec.maxAlive, s + " is one of a kind");
                if (spec.planet == PlanetId.Mercury) mercury++;
                if (spec.planet == PlanetId.Venus) venus++;
            }
            Assert.AreEqual(5, mercury, "glassback, cinderling, flarewing, shadewyrm, Cinderhulk");
            Assert.AreEqual(5, venus, "sulfur drifter, acidmoth, pressure crab, vent eel, Veil Serpent");
            Assert.IsTrue(SpeciesSpec.Get(Species.Flarewing).Flies && SpeciesSpec.Get(Species.Acidmoth).Flies && SpeciesSpec.Get(Species.VeilSerpent).Flies);
            Assert.IsFalse(SpeciesSpec.Get(Species.PressureCrab).Flies || SpeciesSpec.Get(Species.Cinderhulk).Flies);
        }

        [Test]
        public void MercurySpawnsFollowTheTerminatorAndTheColdTraps()
        {
            int trap = MercuryLandforms.ColdTrapCentre(0, MercuryWidth);
            int open = trap + 600;
            Assert.IsFalse(MercuryLandforms.InColdTrap(open, MercuryWidth));
            Assert.IsTrue(SpeciesSpec.Get(Species.Glassback).Allows(Mercury(open, MercuryZone.Twilight, 0.27f)), "glassback rides the band");
            Assert.IsFalse(SpeciesSpec.Get(Species.Glassback).Allows(Mercury(open, MercuryZone.Day, 0.4f)));
            Assert.IsTrue(SpeciesSpec.Get(Species.Cinderling).Allows(Mercury(open, MercuryZone.Twilight, 0.25f)), "cinderlings at dawn");
            Assert.IsFalse(SpeciesSpec.Get(Species.Cinderling).Allows(Mercury(open, MercuryZone.Twilight, 0.75f)), "not at dusk");
            Assert.IsTrue(SpeciesSpec.Get(Species.Flarewing).Allows(Mercury(open, MercuryZone.Day, 0.45f)));
            Assert.IsFalse(SpeciesSpec.Get(Species.Flarewing).Allows(Mercury(open, MercuryZone.Night, 0f)));
            Assert.IsTrue(SpeciesSpec.Get(Species.Shadewyrm).Allows(Mercury(trap, MercuryZone.Night, 0f)), "shadewyrm in the cold trap");
            Assert.IsFalse(SpeciesSpec.Get(Species.Shadewyrm).Allows(Mercury(open, MercuryZone.Night, 0f)));
            Assert.IsFalse(SpeciesSpec.Get(Species.Cinderhulk).Allows(Mercury(open, MercuryZone.Twilight, 0.74f)), "U-138 (D-150): the Cinderhulk left the spawn table (the Cinderling is its re-ink)");
            Assert.IsFalse(SpeciesSpec.Get(Species.Cinderhulk).Allows(Mercury(trap, MercuryZone.Twilight, 0.25f)));
        }

        [Test]
        public void VenusSpawnsKeepToTheDeckThePlainsAndTheVents()
        {
            var vent = VenusLandforms.Vents[0];
            int plains = VenusLandforms.Tesserae[0].x1 + 100;
            Assert.AreNotEqual(VenusFeature.VentField, VenusLandforms.At(plains));
            var surface = new SpawnSite { planet = PlanetId.Venus, surfaceY = 330, playerY = 335 };
            surface.x = plains;
            Assert.IsTrue(SpeciesSpec.Get(Species.PressureCrab).Allows(surface), "crab on the plains");
            Assert.IsFalse(SpeciesSpec.Get(Species.VentEel).Allows(surface));
            Assert.IsFalse(SpeciesSpec.Get(Species.SulfurDrifter).Allows(surface), "no drifters at the surface");
            surface.x = vent.x0 + 10;
            Assert.IsTrue(SpeciesSpec.Get(Species.VentEel).Allows(surface), "eel in the vents");
            Assert.IsFalse(SpeciesSpec.Get(Species.PressureCrab).Allows(surface));
            var deck = new SpawnSite { planet = PlanetId.Venus, x = plains, surfaceY = 766, playerY = 772 }; // a station platform counts as top solid
            Assert.IsTrue(SpeciesSpec.Get(Species.SulfurDrifter).Allows(deck));
            Assert.IsTrue(SpeciesSpec.Get(Species.Acidmoth).Allows(deck));
            Assert.IsTrue(SpeciesSpec.Get(Species.VeilSerpent).Allows(deck));
            Assert.IsFalse(SpeciesSpec.Get(Species.PressureCrab).Allows(deck), "no crabs on the stations");
        }

        [Test]
        public void ApexKillRules()
        {
            Assert.IsFalse(ApexRules.CinderhulkVulnerable(MercuryZone.Day, 0f), "white-hot shell on the day side");
            Assert.IsFalse(ApexRules.CinderhulkVulnerable(MercuryZone.Twilight, 10f));
            Assert.IsTrue(ApexRules.CinderhulkVulnerable(MercuryZone.Night, 0f), "cracks as it crosses into night");
            Assert.IsTrue(ApexRules.CinderhulkVulnerable(MercuryZone.Night, 119.9f));
            Assert.IsFalse(ApexRules.CinderhulkVulnerable(MercuryZone.Night, 120.1f), "sealed again after 2 minutes");
            Assert.IsFalse(ApexRules.CinderhulkVulnerable(MercuryZone.Night, float.PositiveInfinity), "never crossed: no window");
            Assert.IsFalse(ApexRules.CanHurt(Species.VeilSerpent, false, MercuryZone.Day, 0f), "plain rounds glance off");
            Assert.IsTrue(ApexRules.CanHurt(Species.VeilSerpent, true, MercuryZone.Day, 0f), "Cryo rounds bite");
            Assert.IsTrue(ApexRules.CanHurt(Species.Glassback, false, MercuryZone.Day, 0f));
        }
    }
}
