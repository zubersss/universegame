using System.Collections.Generic;
using Meridian.Creatures;
using Meridian.Planets;
using Meridian.Survey;
using NUnit.Framework;

namespace Meridian.Tests
{
    /// <summary>U-054 (EditMode): every planet's catalogue comes from its data; first scans pay once; completion counts.</summary>
    public class CatalogueTests
    {
        [Test]
        public void EachPlanetListsItsCreaturesMineralsAndSites()
        {
            var earth = Catalogue.For(PlanetId.Earth);
            Assert.IsNotNull(earth.Find(e => e.id == Catalogue.CreatureId(Species.Stag)), "stag");
            Assert.IsNotNull(earth.Find(e => e.id == Catalogue.CreatureId(Species.GreyWolf)), "wolf");
            Assert.IsNotNull(earth.Find(e => e.id == "mineral:stone"), "stone");
            Assert.IsNotNull(earth.Find(e => e.id == "site:survey_archive"), "the Archive");
            Assert.IsNull(earth.Find(e => e.id == Catalogue.CreatureId(Species.Dustskater)), "Mars creatures stay on Mars");
            var mars = Catalogue.For(PlanetId.Mars);
            Assert.IsNotNull(mars.Find(e => e.id == "mineral:hematite"));
            Assert.IsNotNull(Catalogue.For(PlanetId.Venus).Find(e => e.id == "mineral:vitriol_glass"), "Vitriol Glass on Venus");
            var ids = new HashSet<string>();
            foreach (var e in mars) Assert.IsTrue(ids.Add(e.id), "unique " + e.id);
        }

        [Test]
        public void FirstScanPaysOnceAndCompletionCounts()
        {
            var scanned = new HashSet<string>();
            int dc = 0;
            string stag = Catalogue.CreatureId(Species.Stag);
            Assert.AreEqual(25, Catalogue.Record(PlanetId.Earth, stag, scanned, ref dc));
            Assert.AreEqual(25, dc);
            Assert.AreEqual(0, Catalogue.Record(PlanetId.Earth, stag, scanned, ref dc), "rescans pay nothing");
            Assert.AreEqual(25, dc);
            Assert.AreEqual(0, Catalogue.Record(PlanetId.Earth, "creature:unicorn", scanned, ref dc), "unknown ids pay nothing");
            Assert.AreEqual(50, Catalogue.Record(PlanetId.Earth, "site:survey_archive", scanned, ref dc), "sites pay 50");
            int n = Catalogue.For(PlanetId.Earth).Count;
            Assert.AreEqual(2f / n, Catalogue.Completion(PlanetId.Earth, scanned), 1e-4f);
            Assert.AreEqual(0f, Catalogue.Completion(PlanetId.Mars, scanned));
        }
    }
}
