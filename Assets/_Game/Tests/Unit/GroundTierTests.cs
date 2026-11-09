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
            for (float depth = 0f; depth <= 210f; depth += 0.02f)
            {
                var w = SmoothGround.TierWeights(depth, t, 3.3f);
                for (int k = 0; k < 4; k++)
                {
                    Assert.GreaterOrEqual(w[k], prev[k] - 1e-6f, "never fades back");
                    Assert.LessOrEqual(w[k] - prev[k], 0.04f, $"no step at {depth:F2} m (T{k + 2})");
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
    }
}
