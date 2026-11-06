using Meridian.Transitions;
using NUnit.Framework;
using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>U-096 (EditMode): the iris radius curve: covers every corner at the start of a close, reaches 0 at 0.35 s, mirrors for the open, never overshoots.</summary>
    public class IrisTests
    {
        [Test]
        public void TheCoverRadiusReachesEveryCorner()
        {
            float aspect = 16f / 9f;
            float centred = IrisMath.CoverRadius(new Vector2(0.5f, 0.5f), aspect);
            Assert.AreEqual(Mathf.Sqrt(0.5f * 0.5f * aspect * aspect + 0.25f) + IrisMath.Edge, centred, 1e-5f, "half the diagonal in screen heights");
            float corner = IrisMath.CoverRadius(new Vector2(0f, 0f), aspect);
            Assert.AreEqual(Mathf.Sqrt(aspect * aspect + 1f) + IrisMath.Edge, corner, 1e-5f, "from a corner: the whole diagonal");
            Assert.Greater(IrisMath.CoverRadius(new Vector2(0.9f, 0.1f), aspect), centred, "off-centre needs more");
        }

        [Test]
        public void ACloseShrinksToZeroInPointThreeFiveSecondsAndAnOpenMirrorsIt()
        {
            Assert.AreEqual(0.35f, IrisMath.Seconds, 1e-6f, "0.35 s each way (Bible Â§9.3)");
            const float cover = 1.0137f;
            Assert.AreEqual(cover, IrisMath.Radius(0f, IrisMath.Seconds, true, cover), 1e-6f, "a close starts covering the screen");
            Assert.AreEqual(0f, IrisMath.Radius(IrisMath.Seconds, IrisMath.Seconds, true, cover), 1e-6f, "and is black at 0.35 s");
            Assert.AreEqual(0f, IrisMath.Radius(0f, IrisMath.Seconds, false, cover), 1e-6f, "an open starts black");
            Assert.AreEqual(cover, IrisMath.Radius(IrisMath.Seconds, IrisMath.Seconds, false, cover), 1e-6f, "and covers the screen at 0.35 s");
            float prev = cover;
            for (float t = 0f; t <= IrisMath.Seconds + 1e-4f; t += 0.01f)
            {
                float r = IrisMath.Radius(t, IrisMath.Seconds, true, cover);
                Assert.LessOrEqual(r, prev + 1e-6f, "a close never grows");
                Assert.GreaterOrEqual(r, 0f);
                Assert.AreEqual(r, IrisMath.Radius(IrisMath.Seconds - t, IrisMath.Seconds, false, cover), 1e-4f, "the open is the close played backwards");
                prev = r;
            }
            Assert.AreEqual(0f, IrisMath.Radius(5f, IrisMath.Seconds, true, cover), 1e-6f, "clamped after the end");
            Assert.AreEqual(cover * 0.75f, IrisMath.Radius(IrisMath.Seconds * 0.5f, IrisMath.Seconds, true, cover), 1e-4f, "accelerating: three quarters left at half time");
        }

        [Test]
        public void TheIrisShaderExists()
        {
            Assert.NotNull(Shader.Find(IrisWipe.ShaderName), "MERIDIAN/IrisWipe");
        }
    }
}
