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
            for (float depth = -5f; depth <= 260f; depth += 0.25f)
            {
                bool nearBorder = false;
                for (int k = 1; k < t.tiers.Length; k++) if (Mathf.Abs(depth - t.tiers[k].fromM) < SmoothGround.TierTransition * 0.5f) nearBorder = true;
                if (nearBorder) continue;
                Assert.AreEqual(t.TierIndex(Mathf.Max(0f, depth)), SmoothGround.TierShown(depth, t), $"the tier at {depth:F2} m");
            }
            for (int k = 1; k < t.tiers.Length; k++)
            {
                var w = SmoothGround.TierWeights(t.tiers[k].fromM, t);
                Assert.AreEqual(0.5f, w[k - 1], 1e-4f, $"half T{k + 1} at its own depth ({t.tiers[k].fromM} m)");
                Assert.AreEqual(k + 1 - 1, SmoothGround.TierShown(t.tiers[k].fromM, t), "the border shows the deeper tier from the half on");
            }
        }

        [Test]
        public void TheTransitionHasNoStep()
        {
            var t = D1Tables.Load();
            var prev = SmoothGround.TierWeights(0f, t);
            for (float depth = 0f; depth <= 210f; depth += 0.02f)
            {
                var w = SmoothGround.TierWeights(depth, t);
                for (int k = 0; k < 4; k++)
                {
                    Assert.GreaterOrEqual(w[k], prev[k] - 1e-6f, "never fades back");
                    Assert.LessOrEqual(w[k] - prev[k], 0.04f, $"no step at {depth:F2} m (T{k + 2})");
                }
                prev = w;
            }
        }
    }
}
