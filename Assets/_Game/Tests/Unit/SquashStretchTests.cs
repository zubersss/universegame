using Meridian.Player;
using NUnit.Framework;
using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>U-089 (EditMode): every squash-and-stretch curve keeps sx·sy·sz = 1 ± 1 % and hits the §4.2 values.</summary>
    public class SquashStretchTests
    {
        const float Dt = 1f / 120f;

        static float RunCurve(SquashStretch s, out float min, out float max, out int steps)
        {
            min = s.Factor; max = s.Factor; steps = 0;
            float worst = Mathf.Abs(s.Scale.x * s.Scale.y * s.Scale.z - 1f);
            while (s.Active)
            {
                var v = s.Step(Dt);
                steps++;
                float volume = v.x * v.y * v.z;
                worst = Mathf.Max(worst, Mathf.Abs(volume - 1f));
                min = Mathf.Min(min, s.Factor);
                max = Mathf.Max(max, s.Factor);
                Assert.Greater(steps, 0);
                if (steps > 2000) Assert.Fail("curve never ended");
            }
            return worst;
        }

        [Test]
        public void EveryCurvePreservesVolume()
        {
            var s = new SquashStretch();
            s.TakeOff(); Assert.Less(RunCurve(s, out float lo, out float hi, out _), 0.01f, "take-off"); Assert.AreEqual(SquashStretch.CrouchScale, lo, 0.01f); Assert.AreEqual(SquashStretch.TakeOffScale, hi, 0.01f);
            s.Land(7f); Assert.Less(RunCurve(s, out lo, out hi, out _), 0.01f, "landing"); Assert.AreEqual(SquashStretch.LandScale, lo, 0.01f); Assert.AreEqual(SquashStretch.LandOvershoot, hi, 0.01f);
            s.Dash(0.18f); Assert.Less(RunCurve(s, out lo, out hi, out _), 0.01f, "dash"); Assert.AreEqual(SquashStretch.DashScale, hi, 0.01f);
            s.Hit(); Assert.Less(RunCurve(s, out lo, out hi, out _), 0.01f, "hit"); Assert.AreEqual(SquashStretch.HitScale, lo, 0.01f);
            Assert.AreEqual(Vector3.one, s.Scale, "back to 1 when the curve ends");
        }

        [Test]
        public void LandingSquashScalesWithImpactAndRecoversInPointOneEight()
        {
            var s = new SquashStretch();
            s.Land(1.5f);
            Assert.IsFalse(s.Active, "no squash below 2 m/s");
            s.Land(4f);
            Assert.AreEqual(Mathf.Lerp(1f, 0.7f, 0.5f), s.Factor, 0.01f, "4 m/s: halfway between 1.0 and 0.7");
            s.Land(7f);
            Assert.AreEqual(0.7f, s.Factor, 0.001f, "0.7 at once at ≥ 6 m/s");
            float t = 0f;
            while (s.Active) { s.Step(Dt); t += Dt; }
            Assert.AreEqual(SquashStretch.LandRecover, t, Dt * 1.5f, "recovered in 0.18 s");
            Assert.AreEqual(1f, s.Factor, 1e-4f);
        }

        [Test]
        public void TheDashStretchesAlongXAndTheHitSquashesHeight()
        {
            var s = new SquashStretch();
            s.Dash(0.18f);
            var v = s.Step(Dt);
            Assert.AreEqual(SquashStretch.DashScale, v.x, 0.01f, "stretched along x");
            Assert.Less(v.y, 1f, "narrower in y");
            s.Hit();
            v = s.Step(Dt);
            Assert.AreEqual(SquashStretch.HitScale, v.y, 0.01f, "squashed in y");
            Assert.Greater(v.x, 1f, "wider in x");
        }
    }
}
