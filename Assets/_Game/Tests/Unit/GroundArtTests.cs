using System.IO;
using Meridian.Planets;
using Meridian.View2D;
using NUnit.Framework;
using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>
    /// U-186 (B-215's D1 key audit): every band set of the four inner planets resolves its brink lip (ground_lip_set, or the planet's
    /// ground_lip), its surface decor (ground_decor_set_n, or the base ground_decor_n) and its dig puff (dig_puff_set, or dig_puff) to art on
    /// disk; together they request the audit's 13 lips, 51 decor pieces and 8 variant puffs. The fill decor probe reaches every piece a set has.
    /// </summary>
    public class GroundArtTests
    {
        const string Art = "Assets/_Game/Art/";
        static readonly PlanetId[] Inner = { PlanetId.Earth, PlanetId.Mars, PlanetId.Mercury, PlanetId.Venus };

        static bool OnDisk(string key) => File.Exists(Art + key + ".json");

        [Test]
        public void EveryBandSetResolvesItsLipDecorAndPuff()
        {
            int lips = 0, decor = 0, puffs = 0;
            foreach (var p in Inner)
            {
                var keys = SmoothGround.VariantKeys(p);
                Assert.IsTrue(OnDisk(SmoothGround.LipKey(p, 0)), $"{p}: ground_lip");
                Assert.IsTrue(OnDisk(SmoothGround.PuffKey(p, 0)), $"{p}: dig_puff");
                for (int v = 0; v < keys.Length; v++)
                {
                    if (keys[v] == null) continue;
                    string lip = SmoothGround.LipKey(p, v), puff = SmoothGround.PuffKey(p, v);
                    bool ownLip = OnDisk(lip), ownPuff = OnDisk(puff);
                    if (ownLip) lips++;
                    if (ownPuff && v > 0) puffs++;
                    int pieces = 0;
                    for (int n = 1; n <= SmoothGround.SurfaceDecorPerSet; n++) if (OnDisk(SmoothGround.SurfaceDecorKey(p, v, n))) pieces++;
                    decor += pieces;
                    Assert.IsFalse(OnDisk(SmoothGround.SurfaceDecorKey(p, v, SmoothGround.SurfaceDecorPerSet + 1)), $"{p} set {v}: no decor piece past the probe");
                    Assert.IsTrue(ownLip || OnDisk(SmoothGround.LipKey(p, 0)), $"{p} {keys[v]}: a lip");
                    Assert.IsTrue(pieces > 0 || v > 0, $"{p}: the base surface decor");
                    Assert.IsTrue(ownPuff || OnDisk(SmoothGround.PuffKey(p, 0)), $"{p} {keys[v]}: a puff");
                    TestContext.Out.WriteLine($"[MERIDIAN] u186 {p} {keys[v]}: lip {(ownLip ? lip : "(base)")}, decor {pieces}, puff {(ownPuff ? puff : "(base)")}");
                }
            }
            Assert.AreEqual(13, lips, "the audit's 13 lips");
            Assert.AreEqual(51, decor, "the audit's 51 surface decor pieces");
            Assert.AreEqual(8, puffs, "the audit's 8 variant puffs");
        }

        /// <summary>LEAD 22:1x: a lip sits on a natural brink only, one a brink (the sharpest node of the turn), its tangent the gentle side's,
        /// mirrored for a drop to the left; a gentle slope or a steady steep one is no brink.</summary>
        [Test]
        public void ANaturalBrinkIsItsSharpestNode()
        {
            // flat to x = 10.5, then a 1.2 m a metre fall: the brink at node 10, a drop to the right, level
            System.Func<int, float> cliff = n => n <= 10 ? 50f : 50f - 1.2f * (n - 10);
            int found = 0;
            for (int n = 0; n < 30; n++)
                if (SmoothGround.NaturalBrink(cliff, n, out int side, out float angle)) { found++; Assert.AreEqual(10, n); Assert.AreEqual(1, side); Assert.AreEqual(0f, angle, 1e-3f); }
            Assert.AreEqual(1, found, "one lip for the cliff");
            // the same cliff mirrored: a drop to the left at the first node of the plateau
            System.Func<int, float> left = n => cliff(20 - n);
            found = 0;
            for (int n = 0; n < 30; n++)
                if (SmoothGround.NaturalBrink(left, n, out int side, out _)) { found++; Assert.AreEqual(-1, side); }
            Assert.AreEqual(1, found, "one lip, mirrored");
            // a rising approach of 0.2: the lip turns to that tangent
            System.Func<int, float> rising = n => n <= 10 ? 50f + 0.2f * n : 52f - 1.2f * (n - 10);
            Assert.IsTrue(SmoothGround.NaturalBrink(rising, 10, out _, out float tilt));
            Assert.AreEqual(Mathf.Atan(0.2f) * Mathf.Rad2Deg, tilt, 1e-3f);
            // a 0.45 slope everywhere, and a steady 1.2 fall: no brink anywhere
            for (int n = 0; n < 30; n++)
            {
                Assert.IsFalse(SmoothGround.NaturalBrink(x => 0.45f * x, n, out _, out _), "a walkable slope");
                Assert.IsFalse(SmoothGround.NaturalBrink(x => -1.2f * x, n, out _, out _), "mid-cliff");
            }
        }

        [Test]
        public void TheFillDecorProbeReachesEveryPiece()
        {
            foreach (var p in Inner)
            {
                string name = p.ToString().ToLowerInvariant();
                for (int set = 0; set < SmoothGround.DecorSets; set++)
                {
                    string stem = set == 0 ? "fill_decor_" : set == 1 ? null : $"fill_decor_t{set}_";
                    if (stem == null) continue;
                    int present = 0;
                    for (int n = 1; n <= 9; n++) if (OnDisk($"terrain/{name}/{stem}{n}")) present = n;
                    Assert.LessOrEqual(present, SmoothGround.DecorPerSet, $"{p} {stem}: every piece within the probe ({present})");
                }
            }
        }
    }
}
