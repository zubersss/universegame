using Meridian.Hazards;
using Meridian.Planets;
using NUnit.Framework;

namespace Meridian.Tests
{
    /// <summary>U-068 (EditMode): giant-world hazard bands (Bible §7.5–7.9), one height per band per giant.</summary>
    public class GiantBandsTests
    {
        readonly int[] levels = new int[HazardRules.Kinds];

        // One height inside each band (CloudLayout: Datum 1100, Deck 1 900, Deck 2 600, Deck 3 300, Crush 100).
        const float SkyY = 1300, Deck1Y = 1000, Deck2Y = 750, Deck3Y = 450, DeepTopY = 280, DeepLowY = 120, CrushY = 50;

        // Expected rows: Thermal, Cryo, Radiation, Toxic, Pressure.
        void Expect(PlanetId p, float y, params int[] row)
        {
            GiantBands.For(p, y, levels);
            CollectionAssert.AreEqual(row, levels, $"{p} at y {y}");
            // HazardTable routes the giants through the same lookup.
            HazardTable.Levels(new HazardContext { planet = p, y = y, localTime = 0.5f }, levels);
            CollectionAssert.AreEqual(row, levels, $"{p} at y {y} via HazardTable");
            for (int k = 0; k < HazardRules.Kinds; k++)
                Assert.AreEqual(row[k], GiantBands.Level(p, y, (HazardKind)k), $"{p} y {y} {(HazardKind)k}");
        }

        [Test]
        public void JupiterRadiationBeltsCryoDeck1ThermalDeep()
        {
            Expect(PlanetId.Jupiter, SkyY, 0, 2, 3, 0, 1);
            Expect(PlanetId.Jupiter, Deck1Y, 0, 2, 3, 0, 1);   // Radiation 3 above Deck 2, Cryo 2 in Deck 1
            Expect(PlanetId.Jupiter, Deck2Y, 0, 0, 1, 0, 1);   // shielded to 1 from Deck 2 down
            Expect(PlanetId.Jupiter, Deck3Y, 0, 0, 1, 0, 2);
            Expect(PlanetId.Jupiter, DeepTopY, 2, 0, 1, 0, 2); // Thermal 2 in the Deep
            Expect(PlanetId.Jupiter, DeepLowY, 2, 0, 1, 0, 3); // pressure 2 → 3 toward the Crush Line
            Expect(PlanetId.Jupiter, CrushY, 3, 0, 1, 0, 3);
        }

        [Test]
        public void SaturnCryoDeck1NoRadiation()
        {
            Expect(PlanetId.Saturn, Deck1Y, 0, 2, 0, 0, 1);
            Expect(PlanetId.Saturn, Deck2Y, 0, 0, 0, 0, 1);
            Expect(PlanetId.Saturn, Deck3Y, 0, 0, 0, 0, 2);
            Expect(PlanetId.Saturn, DeepTopY, 2, 0, 0, 0, 2);
        }

        [Test]
        public void UranusAndNeptuneCryo3AboveDeck3()
        {
            foreach (var p in new[] { PlanetId.Uranus, PlanetId.Neptune })
            {
                Expect(p, SkyY, 0, 3, 0, 0, 1);
                Expect(p, Deck1Y, 0, 3, 0, 0, 1);
                Expect(p, Deck2Y, 0, 3, 0, 0, 1);
                Expect(p, Deck3Y, 0, 2, 0, 0, 2);
                Expect(p, DeepTopY, 2, 0, 0, 0, 2);
                Expect(p, DeepLowY, 2, 0, 0, 0, 3);
            }
        }

        [Test]
        public void EveryGiantHasOneRowPerBandAndOthersHaveNone()
        {
            foreach (var p in new[] { PlanetId.Jupiter, PlanetId.Saturn, PlanetId.Uranus, PlanetId.Neptune })
            {
                Assert.IsTrue(GiantBands.IsGiant(p));
                Assert.AreEqual(GiantBands.BandRows, GiantBands.RowCount(p), p.ToString());
            }
            foreach (var p in new[] { PlanetId.Mercury, PlanetId.Venus, PlanetId.Earth, PlanetId.Mars })
            {
                Assert.IsFalse(GiantBands.IsGiant(p));
                GiantBands.For(p, Deck1Y, levels);
                CollectionAssert.AreEqual(new[] { 0, 0, 0, 0, 0 }, levels, p.ToString());
            }
        }

        [Test]
        public void SuitTiersLowerTheBandsLikeEverywhereElse()
        {
            // The suit model (U-049): tier k lowers every level by k. Jupiter's belts: Mk2 leaves Radiation 1, Mk3 clears it.
            GiantBands.For(PlanetId.Jupiter, Deck1Y, levels);
            var protection = new int[HazardRules.Kinds];
            for (int i = 0; i < protection.Length; i++) protection[i] = 2;
            Assert.AreEqual(1, HazardTable.Worst(levels, protection, out var kind));
            Assert.AreEqual(HazardKind.Radiation, kind);
            for (int i = 0; i < protection.Length; i++) protection[i] = 3;
            Assert.AreEqual(0, HazardTable.Worst(levels, protection, out _));
        }
    }
}
