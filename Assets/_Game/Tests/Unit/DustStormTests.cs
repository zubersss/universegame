using Meridian.Core;
using Meridian.Hazards;
using Meridian.Planet.Weather;
using Meridian.Planets;
using NUnit.Framework;

namespace Meridian.Tests
{
    /// <summary>U-026: dust storm schedule (Bible §7.2) and the Cryo +1.</summary>
    public class DustStormTests
    {
        const double MarsDay = 20.5 * 60.0 * TimeSystem.GameSecondsPerRealSecond;
        const double G = TimeSystem.GameSecondsPerRealSecond;

        [Test]
        public void EveryStormComesAfter4To7DaysAndLasts2To6Minutes()
        {
            double prevEnd = 0;
            double minGap = double.MaxValue, maxGap = 0, minLen = double.MaxValue, maxLen = 0;
            for (int k = 0; k < 200; k++)
            {
                var s = DustStormSchedule.Get(1969, k, MarsDay);
                Assert.AreEqual(prevEnd, s.after, 1e-6, $"storm {k} follows storm {k - 1}");
                double gapDays = (s.start - s.after) / MarsDay, lenMin = s.Duration / G / 60.0;
                Assert.That(gapDays, Is.InRange(4.0, 7.0), $"storm {k} gap");
                Assert.That(lenMin, Is.InRange(2.0, 6.0), $"storm {k} length");
                Assert.AreEqual(60.0, (s.start - s.WarningStart) / G, 1e-9, "warning 60 real seconds ahead");
                minGap = System.Math.Min(minGap, gapDays); maxGap = System.Math.Max(maxGap, gapDays);
                minLen = System.Math.Min(minLen, lenMin); maxLen = System.Math.Max(maxLen, lenMin);
                prevEnd = s.end;
            }
            TestContext.Out.WriteLine($"[MERIDIAN] 200 storms: gap {minGap:F2}–{maxGap:F2} days, length {minLen:F2}–{maxLen:F2} min");
            Assert.Less(minGap, 4.3, "the whole range is used (low end)");
            Assert.Greater(maxGap, 6.7, "the whole range is used (high end)");
        }

        [Test]
        public void CursorLookupMatchesLookupFromScratch()
        {
            var cursor = default(DustStormSchedule.Storm);
            for (double now = 0; now < 60 * MarsDay; now += MarsDay * 0.37)
            {
                cursor = DustStormSchedule.Current(1969, now, MarsDay, cursor);
                var fresh = DustStormSchedule.Current(1969, now, MarsDay, default);
                Assert.AreEqual(fresh.index, cursor.index, $"t {now}");
                Assert.Greater(cursor.end, now);
            }
            // The clock going back (an older save) starts the walk over.
            var back = DustStormSchedule.Current(1969, MarsDay, MarsDay, cursor);
            Assert.AreEqual(DustStormSchedule.Current(1969, MarsDay, MarsDay, default).index, back.index);
        }

        [Test]
        public void PhasesFollowTheStormTimes()
        {
            var s = DustStormSchedule.Get(7, 0, MarsDay);
            Assert.AreEqual(StormPhase.Clear, DustStormSchedule.PhaseAt(s, s.WarningStart - 1));
            Assert.AreEqual(StormPhase.Warning, DustStormSchedule.PhaseAt(s, s.WarningStart));
            Assert.AreEqual(StormPhase.Storm, DustStormSchedule.PhaseAt(s, s.start));
            Assert.AreEqual(StormPhase.Clear, DustStormSchedule.PhaseAt(s, s.end));
        }

        [Test]
        public void SameSeedSameWeatherOtherSeedOtherWeather()
        {
            Assert.AreEqual(DustStormSchedule.Get(1969, 5, MarsDay).start, DustStormSchedule.Get(1969, 5, MarsDay).start);
            Assert.AreNotEqual(DustStormSchedule.Get(1969, 5, MarsDay).start, DustStormSchedule.Get(2024, 5, MarsDay).start);
        }

        [Test]
        public void StormRaisesCryoByOne()
        {
            const float noon = 0.5f, midnight = 0f;
            Assert.AreEqual(1, Cryo.Level(PlanetId.Mars, noon, 0), "Mars day: Cryo 1");
            Assert.AreEqual(2, Cryo.Level(PlanetId.Mars, midnight, 0), "Mars night: Cryo 2");
            Assert.AreEqual(2, Cryo.Level(PlanetId.Mars, noon, 1), "storm by day: 2");
            Assert.AreEqual(3, Cryo.Level(PlanetId.Mars, midnight, 1), "storm by night: 3");
            Assert.AreEqual(Cryo.Max, Cryo.Level(PlanetId.Mars, midnight, 5), "clamped at 3");
            Assert.AreEqual(0, Cryo.Level(PlanetId.Earth, noon, 0));
        }
    }
}
