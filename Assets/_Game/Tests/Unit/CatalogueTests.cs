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

        /// <summary>U-192 (D-187): every site entry carries its icon's key, icons/catalogue/&lt;the POI's label lowercased, spaces as _&gt;
        /// (from the label the entry is named by, never the POI's id), and all eleven icons are in the art folder: B-223's camp and
        /// B-233's ten.</summary>
        [Test]
        public void EverySiteHasItsIconByItsLabel()
        {
            Assert.AreEqual("icons/catalogue/meridian_beacon", Catalogue.SiteIconKey("MERIDIAN BEACON"), "the label, not the id mercury_beacon");
            Assert.AreEqual("icons/catalogue/solarite", Catalogue.SiteIconKey("SOLARITE"), "not solarite_field");
            Assert.AreEqual("icons/catalogue/camp", Catalogue.SiteIconKey("CAMP"), "not spawn_camp");
            Assert.AreEqual("icons/catalogue/launch_complex", Catalogue.SiteIconKey("LAUNCH COMPLEX"), "not coastal_launch_complex");
            var keys = new HashSet<string>();
            foreach (PlanetId p in System.Enum.GetValues(typeof(PlanetId)))
                foreach (var e in Catalogue.For(p))
                {
                    if (e.kind != EntryKind.Site) { if (e.kind == EntryKind.Mineral) Assert.IsNull(e.artKey, e.id + ": a mineral's icon is its item's"); continue; }
                    StringAssert.StartsWith("icons/catalogue/", e.artKey, e.id);
                    Assert.AreEqual(e.artKey, e.artKey.ToLowerInvariant(), e.id + ": lower case");
                    Assert.IsFalse(e.artKey.Contains(" "), e.id + ": no spaces");
                    Assert.IsTrue(System.IO.File.Exists($"Assets/_Game/Art/{e.artKey}_color.png"), $"{e.id}: the icon {e.artKey} is exported");
                    Assert.IsTrue(System.IO.File.Exists($"Assets/_Game/Art/{e.artKey}.json"), $"{e.id}: {e.artKey}'s sidecar");
                    keys.Add(e.artKey);
                }
            CollectionAssert.AreEquivalent(new[]
            {
                "icons/catalogue/camp", "icons/catalogue/survey_archive", "icons/catalogue/launch_complex", "icons/catalogue/halcyon_hauler",
                "icons/catalogue/warden_outpost", "icons/catalogue/flare_shelter", "icons/catalogue/warden_vault", "icons/catalogue/meridian_beacon",
                "icons/catalogue/solarite", "icons/catalogue/meridian_station", "icons/catalogue/vent_harvester",
            }, keys, "the eleven site icons");
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
