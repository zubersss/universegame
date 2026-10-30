using Meridian.Core;
using Meridian.Planets;
using NUnit.Framework;
using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>U-004: game clock runs at 72× (Bible §3).</summary>
    public class TimeSystemTests
    {
        [Test]
        public void TimeSystemRunsAt72x()
        {
            var go = new GameObject("time");
            var t = go.AddComponent<TimeSystem>();
            t.Advance(1f);
            Assert.AreEqual(72.0, t.GameSeconds, 1e-6);
            // Earth day = 20 real minutes → after 10 real minutes we are half-way.
            var earth = ScriptableObject.CreateInstance<PlanetConfig>();
            earth.dayLengthRealMinutes = 20f;
            t.SetGameSeconds(0); t.Advance(600f);
            Assert.AreEqual(0.5f, t.DayFraction(earth), 1e-5f);
            Object.DestroyImmediate(earth);
            Object.DestroyImmediate(go);
        }
    }
}
