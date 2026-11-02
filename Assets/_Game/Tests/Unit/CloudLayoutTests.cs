using Meridian.Terrain;
using Meridian.Terrain.CloudColumn;
using NUnit.Framework;

namespace Meridian.Tests
{
    /// <summary>U-061 (EditMode): the cloud column's deck bands and its floes per seed (density by deck, never above the Datum or in the Crush).</summary>
    public class CloudLayoutTests
    {
        [Test]
        public void DeckBandsFollowTheBible()
        {
            Assert.AreEqual(CloudBand.Crush, CloudLayout.BandAt(50));
            Assert.AreEqual(CloudBand.Deep, CloudLayout.BandAt(100));
            Assert.AreEqual(CloudBand.Deep, CloudLayout.BandAt(299));
            Assert.AreEqual(CloudBand.Deck3, CloudLayout.BandAt(300));
            Assert.AreEqual(CloudBand.Deck2, CloudLayout.BandAt(600));
            Assert.AreEqual(CloudBand.Deck1, CloudLayout.BandAt(900));
            Assert.AreEqual(CloudBand.Deck1, CloudLayout.BandAt(1099));
            Assert.AreEqual(CloudBand.Sky, CloudLayout.BandAt(1100), "the Datum: 1-bar cloud tops");
            Assert.AreEqual(CloudBand.Space, CloudLayout.BandAt(1800));
        }

        [Test]
        public void FloeDensityFollowsTheDecksAndStaysInBounds()
        {
            const int seed = 1969;
            var count = new System.Collections.Generic.Dictionary<CloudBand, int>();
            int floes = 0;
            foreach (var f in CloudLayout.FloesIn(0, CloudLayout.Width, 0, CloudLayout.Height, seed))
            {
                floes++;
                count[f.band] = count.TryGetValue(f.band, out var n) ? n + 1 : 1;
                Assert.GreaterOrEqual(f.y, CloudLayout.CrushLine + 2, "no floe in the Crush");
                Assert.LessOrEqual(f.y + f.height, CloudLayout.Datum, "no floe above the Datum");
                Assert.AreEqual(TileId.FloeIce, CloudLayout.TileAt(f.x, f.y, seed), "ice skin at the corner");
                if (f.width > 2 && f.height > 2) Assert.AreEqual(TileId.FloeCore, CloudLayout.TileAt(f.x + 1, f.y + 1, seed), "core inside");
            }
            int Per(CloudBand b, int rows) => count.TryGetValue(b, out var n) ? n * 1000 / (rows * (CloudLayout.Width / CloudLayout.SlotW)) : 0;
            int d1 = Per(CloudBand.Deck1, 200 / CloudLayout.SlotH), d2 = Per(CloudBand.Deck2, 300 / CloudLayout.SlotH);
            int d3 = Per(CloudBand.Deck3, 300 / CloudLayout.SlotH), deep = Per(CloudBand.Deep, 200 / CloudLayout.SlotH);
            TestContext.Out.WriteLine($"[MERIDIAN] floes {floes}; per mille of slots: deck1 {d1}, deck2 {d2}, deck3 {d3}, deep {deep}");
            Assert.Greater(d2, d1, "Deck 2 is densest");
            Assert.Greater(d1, deep, "the Deep is sparse");
            Assert.IsFalse(count.ContainsKey(CloudBand.Sky) || count.ContainsKey(CloudBand.Space), "nothing above the Datum");
            Assert.AreEqual(TileId.Air, CloudLayout.TileAt(10, 1500, seed), "open sky");
        }

        [Test]
        public void SameSeedSameFloesAndTheColumnWraps()
        {
            var a = new System.Collections.Generic.List<Floe>(CloudLayout.FloesIn(0, 512, 300, 900, 7));
            var b = new System.Collections.Generic.List<Floe>(CloudLayout.FloesIn(0, 512, 300, 900, 7));
            CollectionAssert.AreEqual(a, b, "deterministic per seed");
            var c = new System.Collections.Generic.List<Floe>(CloudLayout.FloesIn(0, 512, 300, 900, 8));
            CollectionAssert.AreNotEqual(a, c, "another seed, other floes");
            Assert.Greater(a.Count, 0);
            var f = a[0];
            Assert.AreEqual(CloudLayout.TileAt(f.x, f.y, 7), CloudLayout.TileAt(f.x + CloudLayout.Width, f.y, 7), "x wraps");
        }
    }
}
