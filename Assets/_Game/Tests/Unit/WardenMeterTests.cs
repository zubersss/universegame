using Meridian.Creatures.Wardens;
using NUnit.Framework;

namespace Meridian.Tests
{
    /// <summary>U-053 (EditMode): the per-area extraction meter trips once at its threshold near a Warden site, and drains. U-190 (Bible 5.3
    /// §8.1): it meters only within GuardRadius (48 m) of a site; anywhere else (the camp) digging never fills it.</summary>
    public class WardenMeterTests
    {
        [Test]
        public void AwayFromEverySiteDiggingNeverTrips()
        {
            var m = new WardenMeter();
            int trips = 0;
            for (int i = 0; i < 2000; i++) if (m.Dig(52 + i % 3, 0f)) trips++; // a 38 m × 3 shaft's worth and more, at the camp
            Assert.AreEqual(0, trips, "no site: no sentinel, however much is dug");
            Assert.AreEqual(0f, m.Level(52, 0f), "the meter does not even fill");
            m.Guard(184f); // the Survey Archive, 132 m from the camp
            for (int i = 0; i < 200; i++) Assert.IsFalse(m.Dig(52, 0f), "the camp is not within 48 m of the archive");
            Assert.IsTrue(float.IsPositiveInfinity(m.ThresholdAt(52)));
        }

        [Test]
        public void WithinFortyEightMetresOfASiteItTripsOnceAtFifteen()
        {
            var m = new WardenMeter();
            m.Guard(1000f);
            Assert.IsTrue(m.IsGuarded(1048), "48 m: guarded"); Assert.IsFalse(m.IsGuarded(1049), "49 m: not");
            Assert.IsTrue(m.IsGuarded(952)); Assert.IsFalse(m.IsGuarded(951));
            int trips = 0;
            for (int i = 0; i < 60; i++) if (m.Dig(1030 + i % 3, 0f)) trips++; // the shaft 30 m from the vault
            Assert.AreEqual(1, trips, "one trip per area");
            var fresh = new WardenMeter();
            fresh.Guard(1000f);
            for (int i = 0; i < 14; i++) Assert.IsFalse(fresh.Dig(1030, 0f));
            Assert.IsTrue(fresh.Dig(1030, 0f), "the 15th tile 30 m from a vault trips");
            for (int i = 0; i < 100; i++) Assert.IsFalse(fresh.Dig(1049, 0f), "49 m out: never");
        }

        [Test]
        public void TheMeterDrainsAndRearms()
        {
            var m = new WardenMeter();
            m.Guard(5f);
            for (int i = 0; i < 40; i++) m.Dig(5, 0f);
            Assert.AreEqual(40f, m.Level(5, 0f), 1e-3f);
            Assert.AreEqual(20f, m.Level(5, 100f), 1e-3f, "0.2 per second");
            Assert.AreEqual(0f, m.Level(5, 1000f));
            Assert.AreEqual(0f, m.Level(5 + WardenMeter.AreaWidth, 0f), "areas are separate");
            Assert.IsFalse(m.Dig(5, 1000f), "drained below half: re-armed, not tripped yet");
            int trips = 0;
            for (int i = 0; i < 40; i++) if (m.Dig(5, 1000f)) trips++;
            Assert.AreEqual(1, trips, "trips again after draining");
            Assert.AreEqual(-1, WardenMeter.AreaOf(-1));
            Assert.AreEqual(0, WardenMeter.AreaOf(31));
        }
    }
}
