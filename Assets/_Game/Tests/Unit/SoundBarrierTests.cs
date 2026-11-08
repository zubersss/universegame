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
    /// U-150 (EditMode, D-158 (4)): the sound barrier fires once on an upward crossing of the planet's speed of sound where ρ ≥ 0.1, not in
    /// thinner air, never on Mercury, and re-arms only below 0.8 × that speed. A full-thrust upright climb (spool + drag, the pure model) breaks
    /// it before the Escape Line on every planet with air, an Earth Mk1 40–70 % of the way up; the crossing table goes to the test log.
    /// </summary>
    public class SoundBarrierTests
    {
        const float Dt = 0.02f;

        static PlanetConfig Load(PlanetId id) =>
            AssetDatabase.LoadAssetAtPath<PlanetConfig>($"{PlanetConfigAuthoring.Folder}/{id}.asset");

        static int Sweep(SoundBarrier b, float from, float to, float density, float c)
        {
            int fired = 0;
            float step = from < to ? 0.5f : -0.5f;
            for (float s = from; step > 0f ? s <= to : s >= to; s += step) if (b.Step(s, density, c)) fired++;
            return fired;
        }

        [Test]
        public void FiresOnceOnAnUpwardCrossingInThickEnoughAir()
        {
            var b = new SoundBarrier();
            Assert.AreEqual(1, Sweep(b, 0f, 45f, 0.5f, 30f), "once through 30 m/s");
            Assert.IsFalse(b.Armed, "spent until it re-arms");
            Assert.AreEqual(0, Sweep(b, 45f, 60f, 0.5f, 30f), "not again while faster");

            var thin = new SoundBarrier();
            Assert.AreEqual(0, Sweep(thin, 0f, 45f, SoundBarrier.MinDensity - 0.01f, 30f), "nothing where ρ < 0.1");
            Assert.IsTrue(thin.Armed, "still armed after a crossing in thin air");
        }

        [Test]
        public void ReArmsOnlyBelowEightTenths()
        {
            var b = new SoundBarrier();
            Assert.AreEqual(1, Sweep(b, 0f, 35f, 1f, 30f));
            Assert.AreEqual(0, Sweep(b, 35f, 24.5f, 1f, 30f), "slowing to 24.5 (> 0.8 × 30)");
            Assert.AreEqual(0, Sweep(b, 24.5f, 35f, 1f, 30f), "not re-armed above 24 m/s");
            Assert.AreEqual(0, Sweep(b, 35f, 23.5f, 1f, 30f), "slowing under 24 m/s re-arms");
            Assert.IsTrue(b.Armed);
            Assert.AreEqual(1, Sweep(b, 23.5f, 35f, 1f, 30f), "and the next crossing fires");
            Assert.AreEqual(2, b.Booms);
        }

        [Test]
        public void NeverOnMercury()
        {
            var mercury = Load(PlanetId.Mercury);
            Assert.AreEqual(0f, mercury.SpeedOfSound, 0f, "no speed of sound without air");
            var b = new SoundBarrier();
            Assert.AreEqual(0, Sweep(b, 0f, 200f, mercury.AirDensityAt(mercury.datumY), mercury.SpeedOfSound), "no boom on Mercury");
            Assert.AreEqual(0, Sweep(new SoundBarrier(), 0f, 200f, 1f, 0f), "nor anywhere the speed of sound is 0");
        }

        /// <summary>The thruster mark that climbs a giant comfortably (thrust ≥ 1.25 g); the inner planets fly the Mk1.</summary>
        static int MarkFor(PlanetConfig c)
        {
            if (c.id == PlanetId.Mercury || c.id == PlanetId.Venus || c.id == PlanetId.Earth || c.id == PlanetId.Mars) return 1;
            for (int m = ShipMarks.MinMark; m <= ShipMarks.MaxMark; m++) if (ShipMarks.Thrust(m) >= 1.25f * c.gravity) return m;
            return ShipMarks.MaxMark;
        }

        /// <summary>Where the pad stands above the Datum for the table: Venus's station deck (768), a giant's floe 150 m under it, else the Datum.</summary>
        static float PadFor(PlanetConfig c) => c.id == PlanetId.Venus ? 768f - c.datumY : c.datumY >= 1000 ? -150f : 0f;

        [Test]
        public void AClimbBreaksItBeforeTheEscapeLine()
        {
            var log = new System.Text.StringBuilder("[MERIDIAN] U-150 sound barrier table (full thrust, upright, spool + drag):\n| Planet | Mark | speed of sound | crossing h above the Datum | of the way from the pad | ρ there | t |\n|---|---|---|---|---|---|---|\n");
            foreach (PlanetId id in Enum.GetValues(typeof(PlanetId)))
            {
                var c = Load(id);
                int mark = MarkFor(c);
                float h0 = PadFor(c), h = h0, v = 0f, t = 0f, thrust = ShipMarks.Thrust(mark);
                var f = new RocketFlight();
                var b = new SoundBarrier();
                float at = float.NaN, rhoAt = 0f, tAt = 0f;
                while (t < 300f && h < c.escapeAltitude)
                {
                    f.StepThrottle(1f, Dt);
                    v += (f.ThrustAccel(f.Throttle, thrust).y - c.gravity) * Dt;
                    float rho = c.AirDensityAt(c.datumY + h);
                    v += RocketFlight.DragAccel(new Vector2(0f, v), rho).y * Dt;
                    if (h <= h0 && v < 0f) v = 0f;
                    h += v * Dt; t += Dt;
                    if (b.Step(Mathf.Abs(v), rho, c.SpeedOfSound) && float.IsNaN(at)) { at = h; rhoAt = rho; tAt = t; }
                }
                float frac = float.IsNaN(at) ? float.NaN : (at - h0) / (c.escapeAltitude - h0);
                log.Append(float.IsNaN(at)
                    ? $"| {id} | Mk{mark} | {c.SpeedOfSound:0} m/s | never | | | |\n"
                    : $"| {id} | Mk{mark} | {c.SpeedOfSound:0} m/s | {at:F0} m | {frac * 100f:F0} % | {rhoAt:F2} | {tAt:F1} s |\n");
                if (id == PlanetId.Mercury) { Assert.IsTrue(float.IsNaN(at), "no boom on Mercury"); continue; }
                Assert.IsFalse(float.IsNaN(at), $"{id}: the Mk{mark} climb breaks the barrier before the Escape Line");
                Assert.GreaterOrEqual(rhoAt, SoundBarrier.MinDensity, $"{id}: where the air is ρ ≥ 0.1");
                if (id == PlanetId.Earth) Assert.That(frac, Is.InRange(0.40f, 0.70f), "an Earth Mk1 breaks it 40–70 % of the way to the Escape Line");
            }
            TestContext.Out.WriteLine(log.ToString());
        }
    }
}
