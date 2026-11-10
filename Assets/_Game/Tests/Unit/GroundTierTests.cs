using Meridian.Mining;
using Meridian.View2D;
using NUnit.Framework;
using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>
    /// U-182 (D1; B-203): the fill's tier by depth. The tier the shader shows at a point is its depth's tier (D1_TABLES section 1's tiers,
    /// DigRun.TierAt) everywhere outside the 1 m transitions; at each tier's depth the two fills stand half and half; the weights rise
    /// smoothly (no step).
    /// </summary>
    public class GroundTierTests
    {
        /// <summary>LEAD 20:2x (a diagnostic's switch does not ship as a way to turn the game's drawing off): the perf probe's switches
        /// on the ground are the probe's alone. Outside a capture the tier shader and the walls are on and no probe state is set
        /// (as ShovelTests holds SkillStats.ToolOverride to null).</summary>
        [Test]
        public void ThePerfProbesSwitchesStandAtTheirDefaults()
        {
            Assert.IsTrue(SmoothGround.TierShader, "the tier shader draws the fill (U-182's A/B is the capture's)");
            Assert.IsTrue(SmoothGround.WallsOn, "B-230's walls draw behind dug cells (U-196's A/B is the capture's)");
            Assert.AreEqual(0, SmoothGround.WallProbe, "the walls' material carries the walls");
        }

        [Test]
        public void TheTierShownAtAPointIsItsDepthsTier()
        {
            var t = D1Tables.Load();
            Assert.GreaterOrEqual(t.tiers.Length, 5, "five tiers");
            float margin = SmoothGround.TierTransition * 0.5f + SmoothGround.TierWobbleMax;
            for (float x = 0f; x < 40f; x += 1.37f)
                for (float depth = -5f; depth <= 260f; depth += 0.25f)
                {
                    bool nearBorder = false;
                    for (int k = 1; k < t.tiers.Length; k++) if (Mathf.Abs(depth - t.tiers[k].fromM) < margin) nearBorder = true;
                    if (nearBorder) continue;
                    Assert.AreEqual(t.TierIndex(Mathf.Max(0f, depth)), SmoothGround.TierShown(depth, t, x), $"the tier at {depth:F2} m, x {x:F2}");
                }
            for (int k = 1; k < t.tiers.Length; k++)
            {
                // where the wobble is zero the border sits on the tier's own depth: half and half
                float x0 = 0f;
                for (float x = 0f; x < 20f; x += 0.01f) if (Mathf.Abs(SmoothGround.TierWobble(k - 1, x)) < Mathf.Abs(SmoothGround.TierWobble(k - 1, x0))) x0 = x;
                var w = SmoothGround.TierWeights(t.tiers[k].fromM, t, x0);
                Assert.AreEqual(0.5f, w[k - 1], 0.02f, $"half T{k + 1} at its own depth ({t.tiers[k].fromM} m) where the wobble crosses zero");
            }
            // LEAD 21:5x: the border wobbles (a rock boundary, not a straight shadow): it moves along x by up to the wobble, no more.
            float lo = float.MaxValue, hi = float.MinValue;
            for (float x = 0f; x < 30f; x += 0.05f) { float wob = SmoothGround.TierWobble(0, x); lo = Mathf.Min(lo, wob); hi = Mathf.Max(hi, wob); }
            Assert.Greater(hi - lo, 0.6f, "the border visibly wobbles");
            Assert.LessOrEqual(Mathf.Max(-lo, hi), SmoothGround.TierWobbleMax + 1e-4f, "within its bound");
        }

        [Test]
        public void TheTransitionHasNoStep()
        {
            var t = D1Tables.Load();
            var prev = SmoothGround.TierWeights(0f, t, 3.3f);
            // a smoothstep's steepest rise is 1.5 / its width: over a 0.02 m step no more than that (U-196: the width is 0.35 m, a boundary
            // between two layers, not a metre's smudge)
            Assert.AreEqual(0.35f, SmoothGround.TierTransition, 1e-6f, "the tiers' crossfade (LEAD 17:3x)");
            float most = 1.5f * 0.02f / SmoothGround.TierTransition + 0.01f;
            for (float depth = 0f; depth <= 210f; depth += 0.02f)
            {
                var w = SmoothGround.TierWeights(depth, t, 3.3f);
                for (int k = 0; k < 4; k++)
                {
                    Assert.GreaterOrEqual(w[k], prev[k] - 1e-6f, "never fades back");
                    Assert.LessOrEqual(w[k] - prev[k], most, $"no step at {depth:F2} m (T{k + 2})");
                }
                prev = w;
            }
        }

        /// <summary>U-196 (B-228's F7: under a slope a tier border read as blurred stair-steps): the border keeps all its wobble on level
        /// ground and loses it as the Surface Line slopes, so from a 20-degree hill up the border under the slope falls all the way along
        /// it (the wobble never turns it back uphill: no treads and risers).</summary>
        [Test]
        public void ABorderUnderASlopeDoesNotStep()
        {
            Assert.AreEqual(1f, SmoothGround.WobbleKeep(0f), 1e-6f, "level ground: the whole wobble");
            Assert.Greater(SmoothGround.WobbleKeep(0.03f), 0.9f, "a 2-degree lie keeps it");
            Assert.AreEqual(0.5f, SmoothGround.WobbleKeep(SmoothGround.WobbleSlope0), 1e-6f, "half at the reference slope");
            Assert.AreEqual(1.0264f, SmoothGround.TierWobbleSlopeMax, 1e-3f, "the wobble's steepest run (the three sines' amplitude x frequency)");
            var t = D1Tables.Load();
            float border = t.tiers[1].fromM;
            foreach (float slope in new[] { Mathf.Tan(20f * Mathf.Deg2Rad), 0.65f, 1f, 2f })
            {
                float keep = SmoothGround.WobbleKeep(slope);
                Assert.Less(keep * SmoothGround.TierWobbleSlopeMax, slope, $"slope {slope:0.00}: the kept wobble runs gentler than the hill");
                // the T1 / T2 border's height under a line falling at `slope`: where the T2 weight crosses a half, column by column
                float prev = float.NaN;
                for (float x = 0f; x <= 40f; x += 0.05f)
                {
                    float line = -slope * x, lo = line - border - 2f, hi = line - border + 2f;
                    for (int i = 0; i < 40; i++)
                    {
                        float mid = 0.5f * (lo + hi);
                        if (SmoothGround.TierWeights(line - mid, t, x, keep)[0] >= 0.5f) lo = mid; else hi = mid; // T2 at mid: the border is above it
                    }
                    float y = 0.5f * (lo + hi);
                    Assert.That(y, Is.InRange(line - border - SmoothGround.TierWobbleMax - 0.01f, line - border + SmoothGround.TierWobbleMax + 0.01f), "the border found within its wobble of the tier's depth");
                    if (!float.IsNaN(prev)) Assert.Less(y, prev + 1e-3f, $"slope {slope:0.00}: the border climbs back at x {x:0.00} (a tread)");
                    prev = y;
                }
            }
            // unattenuated, the same border under a 20-degree hill does climb back: the fault
            Assert.Greater(SmoothGround.TierWobbleSlopeMax, Mathf.Tan(20f * Mathf.Deg2Rad), "at full strength the wobble out-runs a 20-degree hill");
        }

        /// <summary>U-196 (D-183): the back wall's depth term: its full shade at the natural surface, 55 % of it from 6 m down, never
        /// darker, nothing above the surface (a mound's back wall is not darkened).</summary>
        [Test]
        public void TheBackWallDarkensWithDepthToItsFloor()
        {
            Assert.AreEqual(1f, SmoothGround.DepthShade(0f), 1e-6f, "at the opening");
            Assert.AreEqual(0.775f, SmoothGround.DepthShade(3f), 1e-4f, "halfway at 3 m");
            Assert.AreEqual(0.55f, SmoothGround.DepthShade(6f), 1e-6f, "55 % at 6 m");
            Assert.AreEqual(0.55f, SmoothGround.DepthShade(60f), 1e-6f, "and no darker below");
            Assert.AreEqual(1f, SmoothGround.DepthShade(-2f), 1e-6f, "nothing darkens above the natural surface");
            float prev = 1f;
            for (float d = 0f; d <= 8f; d += 0.1f) { float s = SmoothGround.DepthShade(d); Assert.LessOrEqual(s, prev + 1e-6f, $"never lighter with depth ({d:0.0} m)"); prev = s; }
        }

        /// <summary>U-196: the open-air term at known cells: 0 extra way down a shaft that sees the sky, one more metre a cell along a
        /// tunnel off its foot, no way at all from a closed pocket; the term falls to 80 % over 3 m of extra way.</summary>
        [Test]
        public void TheBackWallDarkensAwayFromTheOpenSky()
        {
            const int W = 9;
            var air = new bool[W * W]; var lit = new bool[W * W]; var depth = new float[W * W]; var extra = new float[W * W];
            int K(int i, int j) => i + j * W;
            for (int j = 0; j < W; j++)
                for (int i = 0; i < W; i++)
                {
                    depth[K(i, j)] = 7 - j;            // the natural surface at row 7: rows 7 and 8 are the sky
                    if (j >= 7) { air[K(i, j)] = true; lit[K(i, j)] = true; }
                }
            for (int j = 2; j <= 6; j++) { air[K(2, j)] = true; lit[K(2, j)] = true; } // a shaft down column 2: it sees the sky
            for (int i = 3; i <= 7; i++) air[K(i, 2)] = true;                           // a tunnel off its foot along row 2
            air[K(6, 5)] = true; air[K(7, 5)] = true;                                   // a closed pocket
            SmoothGround.AirExtra(W, air, lit, depth, extra);
            for (int j = 2; j <= 6; j++) Assert.AreEqual(0f, extra[K(2, j)], 1e-5f, $"the shaft at row {j}: straight up is the way");
            for (int i = 3; i <= 7; i++) Assert.AreEqual(i - 2, extra[K(i, 2)], 1e-5f, $"the tunnel, {i - 2} m off the shaft");
            Assert.IsTrue(float.IsPositiveInfinity(extra[K(6, 5)]) && float.IsPositiveInfinity(extra[K(7, 5)]), "a closed pocket has no way to the sky");
            Assert.IsTrue(float.IsPositiveInfinity(extra[K(4, 4)]), "solid ground has none");
            Assert.AreEqual(0f, extra[K(5, 8)], 1e-6f, "the sky itself");

            Assert.AreEqual(1f, SmoothGround.AirShade(0f), 1e-6f, "under the open sky");
            Assert.AreEqual(0.9f, SmoothGround.AirShade(1.5f), 1e-5f, "1.5 m into a tunnel");
            Assert.AreEqual(0.8f, SmoothGround.AirShade(3f), 1e-6f, "80 % from 3 m on");
            Assert.AreEqual(0.8f, SmoothGround.AirShade(float.PositiveInfinity), 1e-6f, "a closed room");
            Assert.AreEqual(0.55f * 0.8f, SmoothGround.DepthShade(10f) * SmoothGround.AirShade(5f), 1e-5f, "the darkest a back wall goes: 44 % of its shade");
        }
    }
}
