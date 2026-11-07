using Meridian.Flora;
using NUnit.Framework;
using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>U-108 (EditMode): the turn_bounce react squash, pure: a 0.15 s half sine, 12 % deep, area-preserving, nothing outside the window.</summary>
    public class FloraBounceTests
    {
        [Test]
        public void TheBouncePopsOnItsFirstFrameAndEasesBackOverItsWindow()
        {
            Assert.AreEqual(0.15f, FloraRigs.BounceSeconds, 1e-6f, "0.15 s (the card)");
            Assert.AreEqual(0f, FloraRigs.BounceK(-0.01f), 1e-6f, "nothing before the react");
            Assert.AreEqual(FloraRigs.BounceAmount, FloraRigs.BounceK(0f), 1e-6f, "the full pop on the first frame (a 0.33 s batch frame still shows it)");
            Assert.Greater(FloraRigs.BounceK(0.03f), FloraRigs.BounceK(0.06f), "easing back");
            Assert.Greater(FloraRigs.BounceK(0.1f), FloraRigs.BounceK(0.14f), "still easing");
            Assert.Greater(FloraRigs.BounceK(0.14f), 0f, "not gone before the window ends");
            Assert.AreEqual(0f, FloraRigs.BounceK(FloraRigs.BounceSeconds), 1e-6f, "over at the window's end");
            Assert.AreEqual(0f, FloraRigs.BounceK(1f), 1e-6f, "and long after");
        }

        [Test]
        public void TheBounceScaleKeepsTheAreaAndTheFacing()
        {
            var s = FloraRigs.BounceScale(1, 0.12f);
            Assert.AreEqual(1.12f, s.x, 1e-6f); Assert.AreEqual(0.88f, s.y, 1e-6f); Assert.AreEqual(1f, s.z, 1e-6f);
            var left = FloraRigs.BounceScale(-1, 0.12f);
            Assert.AreEqual(-1.12f, left.x, 1e-6f, "the facing sign rides on x");
            Assert.AreEqual(Vector3.one, FloraRigs.BounceScale(1, 0f), "rest = identity");
            Assert.AreEqual(new Vector3(-1f, 1f, 1f), FloraRigs.BounceScale(-1, 0f), "rest, facing left");
        }
    }
}
