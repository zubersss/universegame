using Meridian.Core;
using Meridian.EditorTools;
using Meridian.Planets;
using Meridian.Player;
using NUnit.Framework;
using UnityEditor;
using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>
    /// U-088 (EditMode): the feel mechanics of Bible §4.2 v3 never touch gravity (D-078): jump heights on all 8 planets
    /// to ± 1 cm with the v3 tuning, the dash is 1.62 m everywhere and hands back to g at once, the parry and hit-stop
    /// timings are the table's.
    /// </summary>
    public class FeelTests
    {
        const float Dt = 0.02f; // the fixed step

        static PlanetConfig Load(PlanetId id) => AssetDatabase.LoadAssetAtPath<PlanetConfig>($"{PlanetConfigAuthoring.Folder}/{id}.asset");

        /// <summary>The controller's integration: physics applies g·dt before the move; the jump starts at v₀ + g·dt/2.</summary>
        static float JumpHeight(float g)
        {
            float v = PlayerTuning.JumpStartSpeed(g, Dt), y = 0f, peak = 0f;
            for (int i = 0; i < 4000; i++)
            {
                v -= g * Dt;
                y += v * Dt;
                peak = Mathf.Max(peak, y);
                if (y < 0f) break;
            }
            return peak;
        }

        [Test]
        public void JumpHeightsMatchTheTableOnEveryPlanetWithinOneCentimetre()
        {
            foreach (PlanetId id in System.Enum.GetValues(typeof(PlanetId)))
            {
                var cfg = Load(id);
                Assert.NotNull(cfg, $"{id} config");
                float expected = PlayerTuning.JumpSpeed * PlayerTuning.JumpSpeed / (2f * cfg.gravity);
                float h = JumpHeight(cfg.gravity);
                TestContext.Out.WriteLine($"[MERIDIAN] {id}: g {cfg.gravity:F2} jump {h:F3} m (table {expected:F3} m)");
                Assert.AreEqual(expected, h, 0.01f, $"{id} jump height within 1 cm");
            }
            // The v3 tuning (D-078): accelerations and the jump cut, never v₀.
            Assert.AreEqual(7.00f, PlayerTuning.JumpSpeed, 1e-6f, "v₀ untouched");
            Assert.AreEqual(60f, PlayerTuning.GroundAcceleration); Assert.AreEqual(80f, PlayerTuning.Braking); Assert.AreEqual(30f, PlayerTuning.AirAcceleration);
            Assert.LessOrEqual(2f * PlayerTuning.SprintSpeed / PlayerTuning.TurnAcceleration, 0.08f, "a sprint turn reverses within 0.08 s");
            Assert.AreEqual(0.4f, PlayerTuning.JumpCutFactor, 1e-6f);
        }

        [Test]
        public void TheDashIs162MetresOnEveryPlanetAndHandsBackToGravityAtOnce()
        {
            foreach (PlanetId id in System.Enum.GetValues(typeof(PlanetId)))
            {
                float g = Load(id).gravity;
                var dash = new AirDash();
                Assert.IsFalse(dash.TryStart(false, 1), "never from the ground");
                Assert.IsTrue(dash.TryStart(true, 1), "airborne: starts");
                float x = 0f, y = 0f, vy = 0f, held = 0f;
                int steps = 0;
                while (dash.Step(Dt, false, out float share))
                {
                    steps++;
                    x += dash.Direction * AirDash.Speed * share * Dt;
                    vy = g * Dt * share - g * Dt; // the controller's hold: g·dt before the move leaves the step at 0
                    y += vy * Dt;
                    held = Mathf.Max(held, Mathf.Abs(y));
                }
                Assert.AreEqual(AirDash.Distance, x, 0.02f, $"{id}: 1.62 m");
                Assert.Less(held, 1e-4f, $"{id}: no vertical motion during the dash");
                Assert.IsFalse(dash.TryStart(true, 1), "one per airtime");
                // The next step is plain gravity again.
                vy -= g * Dt;
                Assert.AreEqual(-g * Dt, vy, 1e-5f, $"{id}: g resumes at once");
                TestContext.Out.WriteLine($"[MERIDIAN] {id}: dash {x:F3} m in {steps} steps, g {g:F2} resumes");
                for (int i = 0; i < 2; i++) dash.Step(Dt, true, out _);
                Assert.IsTrue(dash.Available, "landing refreshes it");
                Assert.IsFalse(dash.TryStart(true, 1), "0.35 s cooldown still running");
                for (int i = 0; i < 18; i++) dash.Step(Dt, false, out _);
                Assert.IsTrue(dash.TryStart(true, -1), "after the cooldown");
                Assert.AreEqual(-1, dash.Direction, "faces the way the player faces");
            }
        }

        [Test]
        public void ParryWindowAndRecoveryTimings()
        {
            var p = new Parry();
            Assert.IsTrue(p.TryStart());
            float t = 0f;
            while (p.Active) { p.Step(0.01f); t += 0.01f; }
            Assert.AreEqual(Parry.Window, t, 0.011f, "0.12 s window");
            Assert.IsTrue(p.Recovering, "a whiff recovers");
            Assert.IsFalse(p.TryStart(), "no cancel during recovery");
            float r = 0f;
            while (p.Recovering) { p.Step(0.01f); r += 0.01f; }
            Assert.AreEqual(Parry.Recovery, r, 0.011f, "0.40 s recovery");
            Assert.IsTrue(p.TryStart(), "ready again");
            p.Step(0.05f);
            Assert.IsTrue(p.Catch(), "an attack inside the window is parried");
            Assert.IsFalse(p.Recovering, "a parry costs no recovery");
            Assert.IsTrue(p.Flashing, "0.3 s flash");
            Assert.IsFalse(p.Catch(), "the window closed with the parry");
            Assert.AreEqual(1, p.Parries);
        }

        [Test]
        public void HitStopNeverExceeds90MillisecondsAcrossAFiveHitChain()
        {
            var clock = new HitStopClock();
            float stopped = 0f, t = 0f;
            const float step = 1f / 120f;
            int hits = 0;
            float nextHit = 0f;
            while (t < 1f)
            {
                if (hits < 5 && t >= nextHit) { clock.Request(HitStopClock.LanceHit); hits++; nextHit = t + 0.04f; }
                if (clock.Step(step) <= 0f) stopped += step;
                t += step;
            }
            TestContext.Out.WriteLine($"[MERIDIAN] 5-hit chain: {stopped * 1000f:F0} ms stopped");
            Assert.LessOrEqual(stopped, HitStopClock.ChainCap + step, "≤ 90 ms in any chain");
            Assert.Greater(stopped, HitStopClock.LanceHit - step, "the first hit stopped the clock");
            // A later, separate hit gets its full stop again.
            for (int i = 0; i < 60; i++) clock.Step(step);
            clock.Request(HitStopClock.PlayerHit);
            float again = 0f;
            for (int i = 0; i < 60; i++) if (clock.Step(step) <= 0f) again += step;
            Assert.AreEqual(HitStopClock.PlayerHit, again, step, "a fresh chain: the player hit's 50 ms");
        }
    }
}
