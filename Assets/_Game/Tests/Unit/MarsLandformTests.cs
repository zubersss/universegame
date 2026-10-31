using Meridian.Planets;
using Meridian.Terrain;
using NUnit.Framework;
using UnityEditor;

namespace Meridian.Tests
{
    /// <summary>U-039: Mars landforms (Bible §7.2, scaled per P-22) at their positions and sizes, for several seeds.</summary>
    public class MarsLandformTests
    {
        static PlanetConfig Mars() => AssetDatabase.LoadAssetAtPath<PlanetConfig>("Assets/_Game/Settings/Planets/Mars.asset");

        [Test]
        public void FeaturesSitWhereTheyShouldAndLeaveThePoisOnPlains()
        {
            Assert.AreEqual(MarsFeature.PolarCap, MarsLandforms.At(0));
            Assert.AreEqual(MarsFeature.PolarCap, MarsLandforms.At(3071));
            Assert.AreEqual(MarsFeature.Canyon, MarsLandforms.At(1450));
            Assert.AreEqual(MarsFeature.Olympus, MarsLandforms.At(MarsLandforms.OlympusCenter));
            Assert.AreEqual(MarsFeature.Plains, MarsLandforms.At(915), "Halcyon hauler");
            Assert.AreEqual(MarsFeature.Plains, MarsLandforms.At(2012), "Warden outpost");
        }

        [Test]
        public void CanyonIsDeepWithJumpableLedges([Values(1969, 7, 424242)] int seed)
        {
            var c = Mars();
            var g = new SolidWorldGenerator(c, seed);
            int rim = (g.SurfaceHeight(MarsLandforms.CanyonStart - 5) + g.SurfaceHeight(MarsLandforms.CanyonEnd + 5)) / 2;
            int floor = int.MaxValue, maxRiser = 0, run = 1, shortestLedge = int.MaxValue;
            for (int x = MarsLandforms.CanyonStart; x < MarsLandforms.CanyonEnd; x++)
            {
                int h = g.SurfaceHeight(x), n = g.SurfaceHeight(x + 1);
                floor = System.Math.Min(floor, h);
                int step = System.Math.Abs(n - h);
                maxRiser = System.Math.Max(maxRiser, step);
                bool inWall = x < MarsLandforms.CanyonStart + MarsLandforms.CanyonWall;
                if (inWall) { if (step >= 4) { shortestLedge = System.Math.Min(shortestLedge, run); run = 1; } else run++; }
            }
            TestContext.Out.WriteLine($"[MERIDIAN] seed {seed}: canyon {rim - floor} m deep, tallest riser {maxRiser} m, narrowest ledge {shortestLedge} cols");
            Assert.GreaterOrEqual(rim - floor, 150, "deep (Bible: 180 m; scaled 160)");
            Assert.LessOrEqual(maxRiser, (int)MarsLandforms.LedgeStep + 3, "every riser jumpable at Mars g (6.6 m)");
            Assert.GreaterOrEqual(shortestLedge, 3, "ledges wide enough to land on");
        }

        [Test]
        public void OlympusRisesUnderTheEscapeLineWithACaldera([Values(1969, 7, 424242)] int seed)
        {
            var c = Mars();
            var g = new SolidWorldGenerator(c, seed);
            int foot = g.SurfaceHeight(MarsLandforms.OlympusCenter - MarsLandforms.OlympusHalfWidth - 20);
            int peak = int.MinValue, peakX = 0;
            for (int x = MarsLandforms.OlympusCenter - MarsLandforms.OlympusHalfWidth; x <= MarsLandforms.OlympusCenter + MarsLandforms.OlympusHalfWidth; x++)
                if (g.SurfaceHeight(x) > peak) { peak = g.SurfaceHeight(x); peakX = x; }
            int center = g.SurfaceHeight(MarsLandforms.OlympusCenter);
            TestContext.Out.WriteLine($"[MERIDIAN] seed {seed}: Olympus {peak - foot} m above its foot, caldera {peak - center} m deep, summit y {peak} (Escape Line {c.EscapeLineY})");
            Assert.GreaterOrEqual(peak - foot, 180, "a tall shield");
            Assert.Less(peak, c.EscapeLineY - 10, "summit under the Escape Line");
            Assert.GreaterOrEqual(peak - center, 20, "a caldera at the top");
        }

        [Test]
        public void PolarCapIsFrostOverIce([Values(0, 3071, 100)] int x)
        {
            var g = new SolidWorldGenerator(Mars(), 1969);
            int s = g.SurfaceHeight(x);
            Assert.AreEqual(TileId.Snow, g.TileAt(x, s), "CO₂ frost on top");
            Assert.AreEqual(TileId.Ice, g.TileAt(x, s - 4), "water ice under it");
        }

        [Test]
        public void LavaTubesAreOpenTunnelsWithASkylight([Values(1969, 7)] int seed)
        {
            var g = new SolidWorldGenerator(Mars(), seed);
            System.Func<int, int> surf = x => g.SurfaceHeight(((x % 3072) + 3072) % 3072);
            foreach (var t in MarsLandforms.Tubes)
            {
                int ceiling = MarsLandforms.TubeCeiling(t, surf);
                for (int x = t.x0; x <= t.x1; x += 10)
                {
                    for (int y = ceiling - MarsLandforms.TubeHeight + 1; y <= ceiling; y++)
                        Assert.AreEqual(TileId.Air, g.TileAt(x, y), $"tube {t.x0}: open at ({x},{y})");
                    Assert.IsTrue(TileId.IsSolid(g.TileAt(x, ceiling - MarsLandforms.TubeHeight)), $"tube {t.x0}: floor at x={x}");
                }
                int sx = t.x0 + MarsLandforms.SkylightInset;
                for (int y = ceiling; y <= g.SurfaceHeight(sx); y++)
                    Assert.AreEqual(TileId.Air, g.TileAt(sx, y), $"tube {t.x0}: skylight open at y={y}");
                Assert.IsTrue(MarsLandforms.InTube(t.x0 + 40, ceiling - 1, surf), "flagged as a tube (Radiation 0 in M3)");
            }
        }
    }
}
