using Meridian.Creatures.Wardens;
using NUnit.Framework;

namespace Meridian.Tests
{
    /// <summary>U-053 (EditMode): the per-area extraction meter trips once at its threshold, lower near a Warden site, and drains.</summary>
    public class WardenMeterTests
    {
        [Test]
        public void TripsOnceAtTheThreshold()
        {
            var m = new WardenMeter();
            int trips = 0;
            for (int i = 0; i < 60; i++) if (m.Dig(100 + i % 8, 0f)) trips++;
            Assert.AreEqual(1, trips, "one trip per area");
            Assert.AreEqual(60f, m.Level(100, 0f), 1e-3f);
            var fresh = new WardenMeter();
            for (int i = 0; i < 39; i++) Assert.IsFalse(fresh.Dig(100, 0f));
            Assert.IsTrue(fresh.Dig(100, 0f), "the 40th tile trips");
        }

        [Test]
        public void GuardedAreasTripSooner()
        {
            var m = new WardenMeter();
            m.Guard(1016f);
            Assert.IsTrue(m.IsGuarded(1040));
            Assert.IsFalse(m.IsGuarded(1200));
            for (int i = 0; i < 14; i++) Assert.IsFalse(m.Dig(1030, 0f));
            Assert.IsTrue(m.Dig(1030, 0f), "15 tiles near a vault");
        }

        [Test]
        public void TheMeterDrainsAndRearms()
        {
            var m = new WardenMeter();
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
