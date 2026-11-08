using System;
using Meridian.EditorTools;
using Meridian.Planets;
using Meridian.Ship;
using NUnit.Framework;
using UnityEditor;
using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>
    /// U-149 (EditMode, D-158 (3)): the Pilgrim flies with weight, on the pure model at the 50 Hz step. The throttle spools (0 → 0.9 in
    /// 0.30–0.40 s, 1 → 0.1 in 0.15–0.25 s); the tilt has angular inertia (full steer reaches 30° in 0.45–0.70 s, never more than 2° a step)
    /// and returns upright on a damped spring (35° → under 2° within 0.6 s, overshoot ≤ 3°); quadratic air drag thins to nothing at the
    /// Escape Line, is zero on Mercury, holds an Earth Mk1 at 45 ± 3 m/s at the Datum and never stops a climb (D-106: Neptune's Mk1 crawl
    /// reaches its line within 120 s). The per-planet climb table (before / after) goes to the test log.
    /// </summary>
    public class FlightModelTests
    {
        const float Dt = 0.02f;

        static PlanetConfig Load(PlanetId id) =>
            AssetDatabase.LoadAssetAtPath<PlanetConfig>($"{PlanetConfigAuthoring.Folder}/{id}.asset");

        [Test]
        public void TheThrottleSpoolsUpWithAnEaseInAndDownQuickly()
        {
            var f = new RocketFlight();
            float t = 0f, first = -1f, prev = 0f;
            bool eased = false;
            for (int i = 0; i < 100 && first < 0f; i++)
            {
                f.StepThrottle(1f, Dt); t += Dt;
                if (i == 1) eased = f.Throttle - prev > prev; // the second step adds more than the first: an ease-in
                prev = f.Throttle;
                if (f.Throttle >= 0.9f) first = t;
            }
            TestContext.Out.WriteLine($"[MERIDIAN] spool up: 0.9 at {first:F2} s");
            Assert.That(first, Is.InRange(0.30f, 0.40f), "0 → 0.9 within 0.30–0.40 s");
            Assert.IsTrue(eased, "an ease-in, not a step");
            for (int i = 0; i < 50; i++) f.StepThrottle(1f, Dt);
            Assert.AreEqual(1f, f.Throttle, 1e-5f, "a held key reaches full thrust");
            t = 0f; first = -1f;
            for (int i = 0; i < 100 && first < 0f; i++) { f.StepThrottle(0f, Dt); t += Dt; if (f.Throttle <= 0.1f + 1e-4f) first = t; }
            TestContext.Out.WriteLine($"[MERIDIAN] spool down: 0.1 at {first:F2} s");
            Assert.That(first, Is.InRange(0.15f, 0.25f), "1 → 0.1 within 0.15–0.25 s");
            for (int i = 0; i < 50; i++) f.StepThrottle(0.5f, Dt);
            Assert.AreEqual(0.5f, f.Throttle, 1e-5f, "a trigger's value is the target");
        }

        [Test]
        public void TheTiltHasAngularInertiaAndASpringBackUpright()
        {
            var f = new RocketFlight();
            float t = 0f, reached = -1f, maxStep = 0f;
            for (int i = 0; i < 100; i++)
            {
                float before = f.Tilt;
                f.StepTilt(-1f, false, Dt); t += Dt; // A: nose left (positive)
                maxStep = Mathf.Max(maxStep, Mathf.Abs(f.Tilt - before));
                if (reached < 0f && f.Tilt >= 30f) reached = t;
            }
            TestContext.Out.WriteLine($"[MERIDIAN] full steer: 30° at {reached:F2} s, largest step {maxStep:F2}°");
            Assert.That(reached, Is.InRange(0.45f, 0.70f), "full steer reaches 30° in 0.45–0.70 s");
            Assert.LessOrEqual(maxStep, 2f, "no step above 2° per 20 ms");
            Assert.AreEqual(RocketFlight.MaxTilt, f.Tilt, 1e-4f, "it lands on 35°, no overshoot");

            float under = -1f, overshoot = 0f;
            t = 0f;
            for (int i = 0; i < 60; i++)
            {
                f.StepTilt(0f, false, Dt); t += Dt;
                overshoot = Mathf.Max(overshoot, -f.Tilt);
                if (under < 0f && Mathf.Abs(f.Tilt) < 2f) under = t;
            }
            TestContext.Out.WriteLine($"[MERIDIAN] release: under 2° at {under:F2} s, overshoot {overshoot:F2}°");
            Assert.That(under, Is.GreaterThan(0f).And.LessThanOrEqualTo(0.6f), "35° → under 2° within 0.6 s");
            Assert.LessOrEqual(overshoot, 3f, "overshoot ≤ 3°");
        }

        [Test]
        public void DragIsZeroOnMercuryAndAtTheEscapeLineEverywhere()
        {
            foreach (PlanetId id in Enum.GetValues(typeof(PlanetId)))
            {
                var c = Load(id);
                Assert.NotNull(c, id.ToString());
                float line = c.EscapeLineY;
                Assert.AreEqual(0f, c.AirDensityAt(line), 0f, $"{id}: no air at the Escape Line");
                Assert.AreEqual(0f, c.AirDensityAt(line + 50f), 0f, $"{id}: none above it");
                Assert.AreEqual(Vector2.zero, RocketFlight.DragAccel(new Vector2(3f, 40f), c.AirDensityAt(line)), $"{id}: no drag at the line");
                if (id == PlanetId.Mercury)
                {
                    Assert.AreEqual(0f, c.SurfaceAirDensity, 0f, "Mercury has no air");
                    Assert.AreEqual(0f, c.AirDensityAt(c.datumY), 0f, "none at its Datum");
                    Assert.AreEqual(Vector2.zero, RocketFlight.DragAccel(new Vector2(0f, 40f), c.AirDensityAt(c.datumY - 50f)), "no drag on Mercury at all");
                }
                else
                {
                    Assert.AreEqual(c.SurfaceAirDensity, c.AirDensityAt(c.datumY), 1e-5f, $"{id}: ρ_surface at the Datum");
                    Assert.Greater(c.AirDensityAt(c.datumY + c.escapeAltitude * 0.5f), 0f, $"{id}: air half way up");
                    Assert.Less(c.AirDensityAt(c.datumY + c.escapeAltitude * 0.5f), c.SurfaceAirDensity, $"{id}: thinner half way up");
                    var drag = RocketFlight.DragAccel(new Vector2(0f, -30f), c.AirDensityAt(c.datumY));
                    Assert.Greater(drag.y, 0f, $"{id}: a fall is dragged too");
                }
            }
        }

        [Test]
        public void AnEarthMk1HoldsFortyFiveAtTheDatum()
        {
            var earth = Load(PlanetId.Earth);
            var f = new RocketFlight();
            float v = 0f, rho = earth.AirDensityAt(earth.datumY);
            for (int i = 0; i < Mathf.RoundToInt(90f / Dt); i++)
            {
                f.StepThrottle(1f, Dt);
                v += (f.ThrustAccel(f.Throttle, ShipMarks.Thrust(1)).y - earth.gravity) * Dt;
                v += RocketFlight.DragAccel(new Vector2(0f, v), rho).y * Dt;
            }
            TestContext.Out.WriteLine($"[MERIDIAN] Earth Mk1 terminal at the Datum: {v:F2} m/s");
            Assert.AreEqual(45f, v, 3f, "a full-thrust upright Mk1 tends to 45 ± 3 m/s at Earth's Datum");
        }

        /// <summary>The full-thrust upright climb from `h0` above the Datum to the Escape Line (spool and drag on or off), pure.</summary>
        static (float seconds, float speed) Climb(PlanetConfig c, int mark, float h0, bool weight, float limit = 300f)
        {
            var f = new RocketFlight();
            float h = h0, v = 0f, t = 0f, thrust = ShipMarks.Thrust(mark);
            while (t < limit)
            {
                float throttle = 1f;
                if (weight) { f.StepThrottle(1f, Dt); throttle = f.Throttle; }
                v += (f.ThrustAccel(throttle, thrust).y - c.gravity) * Dt;
                if (weight) v += RocketFlight.DragAccel(new Vector2(0f, v), c.AirDensityAt(c.datumY + h)).y * Dt;
                if (h <= h0 && v < 0f) v = 0f; // the pad
                h += v * Dt; t += Dt;
                if (h >= c.escapeAltitude) return (t, v);
            }
            return (-1f, v);
        }

        [Test]
        public void DragNeverStopsAClimbAndNeptunesCrawlStillLeaves()
        {
            var neptune = Load(PlanetId.Neptune);
            Assert.AreEqual(1, neptune.MinThrusterToClimb, "the Mk1 crawl (net 0.85 m/s²)");
            var (fromDatum, v0) = Climb(neptune, 1, 0f, true);
            var (fromDeck, v1) = Climb(neptune, 1, -300f, true); // a floe 300 m under the Datum: the Datum's density all the way up to it
            TestContext.Out.WriteLine($"[MERIDIAN] Neptune Mk1: from the Datum {fromDatum:F1} s ({v0:F1} m/s at the line), from 300 m under it {fromDeck:F1} s ({v1:F1} m/s)");
            Assert.That(fromDatum, Is.GreaterThan(0f).And.LessThanOrEqualTo(120f), "Neptune's Mk1 reaches its Escape Line within 120 s");
            Assert.That(fromDeck, Is.GreaterThan(0f).And.LessThanOrEqualTo(120f), "even from a floe 300 m under the Datum");

            var log = new System.Text.StringBuilder("[MERIDIAN] U-149 climb table (full thrust, upright, from the Datum; before = no spool, no drag):\n| Planet | Mark | ρ_surface | before: time / speed at the line | after: time / speed at the line |\n|---|---|---|---|---|\n");
            foreach (PlanetId id in Enum.GetValues(typeof(PlanetId)))
            {
                var c = Load(id);
                int mark = c.MinThrusterToClimb;
                var before = Climb(c, mark, 0f, false);
                var after = Climb(c, mark, 0f, true);
                log.Append($"| {id} | Mk{mark} | {c.SurfaceAirDensity:0.##} | {before.seconds:F1} s / {before.speed:F1} m/s | {after.seconds:F1} s / {after.speed:F1} m/s |\n");
                Assert.Greater(after.seconds, 0f, $"{id}: Mk{mark} still climbs to the Escape Line with drag (D-106)");
                Assert.GreaterOrEqual(after.seconds, before.seconds - Dt, $"{id}: the weight never makes the climb faster");
            }
            TestContext.Out.WriteLine(log.ToString());
        }
    }
}
