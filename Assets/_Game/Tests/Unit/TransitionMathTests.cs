using Meridian.Transitions;
using NUnit.Framework;

namespace Meridian.Tests
{
    /// <summary>U-012 (EditMode): longitude ↔ column (Bible §5.2–5.3) round-trips and wraps.</summary>
    public class TransitionMathTests
    {
        [TestCase(0, 4096)] [TestCase(64, 4096)] [TestCase(2048, 4096)] [TestCase(4095, 4096)] [TestCase(1500, 3072)]
        public void ColumnToLongitudeAndBack(int x, int width)
        {
            float lon = TransitionDirector.Longitude(x + 0.5f, width);
            Assert.AreEqual(x, TransitionDirector.ColumnAt(lon, width));
        }

        [Test]
        public void LaunchThenEntryAtTheSameAngleReturnsToTheSameColumn()
        {
            const int width = 4096;
            float rotation = 123.4f;
            float angle = TransitionDirector.Longitude(64.5f, width) + rotation; // launch: longitude + rotation
            int x = TransitionDirector.ColumnAt(angle - rotation, width);          // entry: angle − rotation
            Assert.AreEqual(64, x);
        }

        [Test]
        public void LongitudeWraps()
        {
            Assert.AreEqual(0f, TransitionDirector.Longitude(4096f, 4096), 1e-4f);
            Assert.AreEqual(4095, TransitionDirector.ColumnAt(-0.01f, 4096));
            Assert.AreEqual(90f, TransitionDirector.Longitude(1024f, 4096), 1e-4f);
        }
    }
}
