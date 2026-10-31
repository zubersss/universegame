using Meridian.Planets;
using Meridian.Terrain;
using NUnit.Framework;
using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>U-048 (EditMode): Mercury's cold traps (placement, depth, ice, shadow), the terminator band over time, local time of day.</summary>
    public class MercuryWorldTests
    {
        static PlanetConfig Mercury()
        {
            var c = ScriptableObject.CreateInstance<PlanetConfig>();
            c.id = PlanetId.Mercury; c.worldWidth = 2048; c.worldHeight = 500; c.datumY = 320;
            return c;
        }

        [Test]
        public void TwoColdTrapsHalfAWorldApart()
        {
            const int W = 2048;
            int a = MercuryLandforms.ColdTrapCentre(0, W), b = MercuryLandforms.ColdTrapCentre(1, W);
            Assert.AreEqual(W / 2, b - a, "the two poles");
            Assert.IsTrue(MercuryLandforms.InColdTrap(a, W)); Assert.IsTrue(MercuryLandforms.InColdTrap(b, W));
            Assert.IsTrue(MercuryLandforms.PermanentShadow(a, W), "the floor is in permanent shadow");
            Assert.IsFalse(MercuryLandforms.InColdTrap(a + W / 4, W), "plains between them");
            Assert.IsFalse(MercuryLandforms.PermanentShadow(a + MercuryLandforms.ColdTrapHalfWidth - 2, W), "the rim walls see the sun");
        }

        [Test]
        public void ColdTrapFloorsAreDeepAndHoldIce()
        {
            foreach (int seed in new[] { 1969, 7, 424242 })
            {
                var gen = new SolidWorldGenerator(Mercury(), seed);
                for (int i = 0; i < 2; i++)
                {
                    int c = MercuryLandforms.ColdTrapCentre(i, 2048);
                    int floor = gen.SurfaceHeight(c);
                    int rim = Mathf.Max(gen.SurfaceHeight(c - MercuryLandforms.ColdTrapHalfWidth), gen.SurfaceHeight(c + MercuryLandforms.ColdTrapHalfWidth));
                    Assert.Greater(rim - floor, 25, $"seed {seed} trap {i}: a deep bowl ({rim - floor} m)");
                    Assert.AreEqual(TileId.MercuryRegolith, gen.TileAt(c, floor), "a thin regolith skin");
                    int ice = 0;
                    for (int y = floor - 1; y >= floor - 10; y--) if (gen.TileAt(c, y) == TileId.MercuryIce) ice++;
                    Assert.GreaterOrEqual(ice, 8, $"seed {seed} trap {i}: water ice under the skin");
                }
                // No ice on the open plains' surface layer.
                int plain = MercuryLandforms.ColdTrapCentre(0, 2048) + 512;
                Assert.AreNotEqual(TileId.MercuryIce, gen.TileAt(plain, gen.SurfaceHeight(plain) - 1));
            }
        }

        [Test]
        public void SurfaceUsesMercuryMaterials()
        {
            var gen = new SolidWorldGenerator(Mercury(), 1969);
            for (int x = 0; x < 2048; x += 97)
            {
                byte t = gen.TileAt(x, gen.SurfaceHeight(x));
                Assert.That(t == TileId.MercuryRegolith, $"x {x}: regolith on top, got {t}");
            }
        }

        [Test]
        public void BandMovesWithTheSavedClockAndSetsTheTimeOfDay()
        {
            const int W = 2048;
            MercuryTerminator.ClockOffset = 0;
            // The terminator follows the game clock (saved), 1 m per 6 real s = per 432 game s.
            Assert.AreEqual(0f, MercuryTerminator.Dawn(MercuryTerminator.Now(0), W), 1e-3f);
            Assert.AreEqual(1f, MercuryTerminator.Dawn(MercuryTerminator.Now(6 * 72), W), 1e-3f);
            Assert.AreEqual(100f, MercuryTerminator.Dawn(MercuryTerminator.Now(600 * 72), W), 1e-3f, "10 real minutes: 100 m");
            Assert.AreEqual(0.25f, MercuryTerminator.LocalTime(0f, 0, W), 1e-3f, "dawn on the dawn line");
            Assert.AreEqual(0.5f, MercuryTerminator.LocalTime(-W / 4f, 0, W), 1e-3f, "noon a quarter world behind it");
            Assert.AreEqual(0.75f, MercuryTerminator.LocalTime(W / 2f, 0, W), 1e-3f, "dusk on the other line");
            Assert.AreEqual(0f, MercuryTerminator.LocalTime(W / 4f, 0, W), 1e-3f, "midnight ahead of dawn");
        }
    }
}
