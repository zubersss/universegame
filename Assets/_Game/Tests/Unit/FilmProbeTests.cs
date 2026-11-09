using Meridian.Perf;
using NUnit.Framework;

namespace Meridian.Tests
{
    /// <summary>D-180: the probe's Film pass row is the median of interleaved on / off pairs; more pairs while they spread over 0.3 ms.</summary>
    public class FilmProbeTests
    {
        [Test]
        public void TheRowIsTheMedianOfThePairedDifferences()
        {
            Assert.AreEqual(0.35f, MemoryProbe.Median(new[] { 0.2f, 0.9f, 0.3f, 0.4f }), 1e-5f, "even: the middle two's mean");
            Assert.AreEqual(0.3f, MemoryProbe.Median(new[] { 0.9f, 0.3f, 0.1f }), 1e-5f, "odd: the middle one");
            Assert.AreEqual(0f, MemoryProbe.Median(new float[0]));
            // one drifted pair (the morning's 0.774-style reading) does not move the row
            Assert.Less(MemoryProbe.Median(new[] { 0.31f, 0.28f, 0.79f, 0.33f }), 0.6f);
        }

        [Test]
        public void TheSpreadAsksForMorePairs()
        {
            Assert.AreEqual(0.7f, MemoryProbe.Spread(new[] { 0.2f, 0.9f, 0.3f, 0.4f }), 1e-5f);
            Assert.AreEqual(0f, MemoryProbe.Spread(new float[0]));
            Assert.AreEqual(4, MemoryProbe.FilmPairsMin);
            Assert.AreEqual(300, MemoryProbe.FilmBlockFrames);
            Assert.AreEqual(0.3f, MemoryProbe.FilmSpreadMs, 1e-6f);
            Assert.Greater(MemoryProbe.FilmPairsMax, MemoryProbe.FilmPairsMin);
        }
    }
}
