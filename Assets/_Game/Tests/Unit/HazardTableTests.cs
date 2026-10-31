using Meridian.Hazards;
using Meridian.Planets;
using Meridian.Terrain;
using NUnit.Framework;

namespace Meridian.Tests
{
    /// <summary>U-049 (EditMode): hazard tables per planet (Bible §7), suit tiers, D-048 flares, Mercury's terminator.</summary>
    public class HazardTableTests
    {
        readonly int[] levels = new int[HazardRules.Kinds];
        const float Noon = 0.5f, Midnight = 0f;

        int L(HazardKind k) => levels[(int)k];

        void At(HazardContext c) => HazardTable.Levels(c, levels);

        [Test]
        public void EarthIsMildExceptTundraNights()
        {
            At(new HazardContext { planet = PlanetId.Earth, localTime = Noon });
            CollectionAssert.AreEqual(new[] { 0, 0, 0, 0, 0 }, levels);
            At(new HazardContext { planet = PlanetId.Earth, localTime = Midnight, tundra = true });
            Assert.AreEqual(1, L(HazardKind.Cryo));
        }

        [Test]
        public void MarsThinAirRadiationAndLavaTubes()
        {
            At(new HazardContext { planet = PlanetId.Mars, localTime = Noon });
            Assert.AreEqual(1, L(HazardKind.Cryo)); Assert.AreEqual(1, L(HazardKind.Pressure)); Assert.AreEqual(1, L(HazardKind.Radiation));
            At(new HazardContext { planet = PlanetId.Mars, localTime = Midnight, stormCryo = 1 });
            Assert.AreEqual(3, L(HazardKind.Cryo), "night 2 + storm 1");
            At(new HazardContext { planet = PlanetId.Mars, localTime = Noon, lavaTube = true });
            Assert.AreEqual(0, L(HazardKind.Radiation), "lava tubes are radiation shelters (§7.2)");
        }

        [Test]
        public void MercuryDayNightTwilightAndFlares()
        {
            At(new HazardContext { planet = PlanetId.Mercury, mercury = MercuryZone.Day });
            Assert.AreEqual(3, L(HazardKind.Thermal)); Assert.AreEqual(2, L(HazardKind.Radiation), "Radiation 2 always");
            At(new HazardContext { planet = PlanetId.Mercury, mercury = MercuryZone.Night });
            Assert.AreEqual(3, L(HazardKind.Cryo)); Assert.AreEqual(0, L(HazardKind.Thermal));
            At(new HazardContext { planet = PlanetId.Mercury, mercury = MercuryZone.Twilight });
            Assert.AreEqual(1, L(HazardKind.Thermal)); Assert.AreEqual(1, L(HazardKind.Cryo));

            At(new HazardContext { planet = PlanetId.Mercury, mercury = MercuryZone.Twilight, flare = true });
            Assert.AreEqual(HazardRules.FlareLevel, L(HazardKind.Radiation), "a flare in the open (D-048)");
            At(new HazardContext { planet = PlanetId.Mercury, mercury = MercuryZone.Day, flare = true, underground = true });
            Assert.AreEqual(2, L(HazardKind.Radiation), "rock overhead stops the flare");
            At(new HazardContext { planet = PlanetId.Mercury, mercury = MercuryZone.Day, flare = true, sheltered = true });
            Assert.AreEqual(2, L(HazardKind.Radiation), "a flare shelter stops it");
            At(new HazardContext { planet = PlanetId.Mercury, mercury = MercuryZone.Night, flare = true });
            Assert.AreEqual(2, L(HazardKind.Radiation), "the night side is in shadow");
        }

        [Test]
        public void VenusDeckAndTheDive()
        {
            At(new HazardContext { planet = PlanetId.Venus, y = 770f });
            CollectionAssert.AreEqual(new[] { 0, 0, 0, 1, 0 }, levels, "deck: Toxic 1 only");
            At(new HazardContext { planet = PlanetId.Venus, y = 640f });
            Assert.AreEqual(1, L(HazardKind.Thermal)); Assert.AreEqual(1, L(HazardKind.Pressure)); Assert.AreEqual(1, L(HazardKind.Toxic));
            At(new HazardContext { planet = PlanetId.Venus, y = 590f });
            Assert.AreEqual(2, L(HazardKind.Toxic), "below the acid-rain line");
            At(new HazardContext { planet = PlanetId.Venus, y = 320f });
            Assert.AreEqual(3, L(HazardKind.Thermal)); Assert.AreEqual(3, L(HazardKind.Pressure)); Assert.AreEqual(2, L(HazardKind.Toxic));
        }

        [Test]
        public void SuitTiersLowerEveryHazard()
        {
            var none = new int[HazardRules.Kinds];
            var mk2 = new[] { 2, 2, 2, 2, 2 };
            var mk3 = new[] { 3, 3, 3, 3, 3 };
            At(new HazardContext { planet = PlanetId.Mercury, mercury = MercuryZone.Day });
            Assert.AreEqual(3, HazardTable.Worst(levels, none, out var kind)); Assert.AreEqual(HazardKind.Thermal, kind);
            Assert.AreEqual(1, HazardTable.Worst(levels, mk2, out _), "Mk2 shielding makes the day side 1 (§7.3)");
            Assert.AreEqual(0, HazardTable.Worst(levels, mk3, out _), "Mk3 → 0");
            At(new HazardContext { planet = PlanetId.Mercury, mercury = MercuryZone.Twilight, flare = true });
            Assert.AreEqual(1, HazardTable.Worst(levels, mk3, out kind), "a flare 4 − Mk3 = 1"); Assert.AreEqual(HazardKind.Radiation, kind);
        }

        [Test]
        public void FlareDrainKillsWithinTheFlare()
        {
            Assert.AreEqual(12f, HazardRules.DrainPerSecond(HazardRules.FlareLevel), "D-048");
            float seconds = (HazardRules.SuitMax + 100f) / HazardRules.DrainPerSecond(HazardRules.FlareLevel);
            Assert.Less(seconds, SolarFlares.ActiveSeconds, "dead before the 20 s flare ends");
            Assert.Less(seconds, 30f);
            Assert.AreEqual(6.78f, HazardRules.DrainPerSecond(3), 0.01f, "level 3 unchanged (D-032)");
        }

        [Test]
        public void TerminatorCreepsOneMetrePerSixSeconds()
        {
            const int W = 4000;
            Assert.AreEqual(0f, MercuryTerminator.Dawn(0, W), 1e-4f);
            Assert.AreEqual(10f, MercuryTerminator.Dawn(60, W), 1e-4f, "60 s → 10 m");
            Assert.AreEqual(MercuryZone.Twilight, MercuryTerminator.ZoneAt(150f, 0, W), "inside the 400 m band");
            Assert.AreEqual(MercuryZone.Night, MercuryTerminator.ZoneAt(1000f, 0, W), "ahead of the dawn line");
            Assert.AreEqual(MercuryZone.Day, MercuryTerminator.ZoneAt(3000f, 0, W), "behind it");
            Assert.AreEqual(MercuryZone.Twilight, MercuryTerminator.ZoneAt(W * 0.5f, 0, W), "the dusk band");
            // The dawn line creeps +x into the night: a column just ahead of the band enters it.
            Assert.AreEqual(MercuryZone.Night, MercuryTerminator.ZoneAt(210f, 0, W));
            Assert.AreEqual(MercuryZone.Twilight, MercuryTerminator.ZoneAt(210f, 6 * 20, W), "20 m of creep later");
        }
    }
}
