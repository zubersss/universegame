using Meridian.Core;
using Meridian.Planet.Lighting;
using Meridian.Planets;
using NUnit.Framework;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering.Universal;

namespace Meridian.Tests
{
    /// <summary>U-025: day/night lighting values (Bible §3 day lengths, §9 sunlight).</summary>
    public class DayNightTests
    {
        const float Noon = 0.5f, Midnight = 0f, Dawn = 0.25f, Dusk = 0.75f;

        [Test]
        public void EarthNoonAndMidnightIntensitiesMatchBible()
        {
            Assert.AreEqual(1.0f, DayNightMath.SunIntensity(PlanetId.Earth, Noon), 1e-5f, "Earth sunlight 1.0 at noon (§9)");
            Assert.AreEqual(0f, DayNightMath.SunIntensity(PlanetId.Earth, Midnight), 1e-5f, "no sun at midnight");
            Assert.AreEqual(DayNightMath.DayAmbient * 1.0f, DayNightMath.AmbientIntensity(PlanetId.Earth, Noon), 1e-5f, "noon ambient");
            Assert.AreEqual(DayNightMath.NightAmbient, DayNightMath.AmbientIntensity(PlanetId.Earth, Midnight), 1e-5f, "night ambient");
            Assert.Greater(DayNightMath.AmbientIntensity(PlanetId.Earth, Noon), DayNightMath.AmbientIntensity(PlanetId.Earth, Midnight));
        }

        [Test]
        public void EveryPlanetNoonSunlightIsItsBibleValue()
        {
            var expected = new (PlanetId, float)[]
            {
                (PlanetId.Mercury, 1.6f), (PlanetId.Venus, 1.2f), (PlanetId.Earth, 1.0f), (PlanetId.Mars, 0.75f),
                (PlanetId.Jupiter, 0.45f), (PlanetId.Saturn, 0.35f), (PlanetId.Uranus, 0.25f), (PlanetId.Neptune, 0.2f),
            };
            foreach (var (id, v) in expected)
            {
                Assert.AreEqual(v, DayNightMath.SunIntensity(id, Noon), 1e-5f, $"{id} noon");
                Assert.AreEqual(0f, DayNightMath.SunIntensity(id, Midnight), 1e-5f, $"{id} midnight");
            }
        }

        [Test]
        public void SunRisesLeftCrossesOverheadSetsRight()
        {
            AssertVec(new Vector2(-1f, 0f), DayNightMath.SunDirection(Dawn), "dawn: left horizon");
            AssertVec(new Vector2(0f, 1f), DayNightMath.SunDirection(Noon), "noon: overhead");
            AssertVec(new Vector2(1f, 0f), DayNightMath.SunDirection(Dusk), "dusk: right horizon");
            AssertVec(new Vector2(0f, -1f), DayNightMath.SunDirection(Midnight), "midnight: below");
            float prev = -1f;
            for (float t = 0f; t <= Noon + 1e-4f; t += 0.01f)
            {
                float d = DayNightMath.Daylight(t);
                Assert.GreaterOrEqual(d, prev - 1e-6f, $"daylight rises toward noon (t {t:F2})");
                prev = d;
            }
            Assert.Greater(DayNightMath.Twilight(Dawn + 0.02f), 0.5f, "sunrise color just after dawn");
            Assert.AreEqual(0f, DayNightMath.Twilight(Noon), 1e-5f, "no sunrise color at noon");
        }

        [Test]
        public void MarsSunsetIsBlueEarthsIsOrange()
        {
            var mars = DayNightMath.SunColor(PlanetId.Mars, Dusk - 0.02f);
            var earth = DayNightMath.SunColor(PlanetId.Earth, Dusk - 0.02f);
            Assert.Greater(mars.b, mars.r, "Mars dusk light is blue");
            Assert.Greater(earth.r, earth.b, "Earth dusk light is orange");
        }

        [Test]
        public void NewGameStartsInTheMorning()
        {
            float t = DayNightMath.LocalTime(0f);
            Assert.That(t, Is.GreaterThan(Dawn).And.LessThan(Noon), "clock 0 is morning");
            Assert.Greater(DayNightMath.Daylight(t), 0.9f, "full daylight at start");
        }

        [Test]
        public void EarthDayIs20MinutesAndMarsDayIs20Point5()
        {
            var earth = AssetDatabase.LoadAssetAtPath<PlanetConfig>("Assets/_Game/Settings/Planets/Earth.asset");
            var mars = AssetDatabase.LoadAssetAtPath<PlanetConfig>("Assets/_Game/Settings/Planets/Mars.asset");
            Assert.AreEqual(20f, earth.dayLengthRealMinutes, 1e-4f);
            Assert.AreEqual(20.5f, mars.dayLengthRealMinutes, 1e-4f);
            var go = new GameObject("Clock");
            try
            {
                var time = go.AddComponent<TimeSystem>();
                time.Advance(10f * 60f); // 10 real minutes
                Assert.AreEqual(0.5f, time.DayFraction(earth), 1e-4f, "half an Earth day");
                Assert.AreEqual(10f / 20.5f, time.DayFraction(mars), 1e-4f, "Mars runs 20.5 min");
            }
            finally { Object.DestroyImmediate(go); }
        }

        [Test]
        public void UpdatingTheLightsAllocatesNothing()
        {
            var root = new GameObject("DayNight");
            var planet = ScriptableObject.CreateInstance<PlanetConfig>();
            try
            {
                planet.id = PlanetId.Mars;
                planet.dayLengthRealMinutes = 20.5f;
                var time = root.AddComponent<TimeSystem>();
                var lighting = root.AddComponent<DayNightLighting>();
                lighting.time = time;
                lighting.ambient = new GameObject("Ambient").AddComponent<Light2D>();
                lighting.sun = new GameObject("Sun").AddComponent<Light2D>();
                lighting.ambient.transform.SetParent(root.transform);
                lighting.sun.transform.SetParent(root.transform);
                lighting.view = new GameObject("View").AddComponent<Camera>();
                lighting.view.transform.SetParent(root.transform);
                lighting.ConfigureFor(planet);
                for (int i = 0; i < 10; i++) { time.Advance(1f); lighting.Apply(); } // warm
                long before = System.GC.GetAllocatedBytesForCurrentThread();
                for (int i = 0; i < 300; i++) { time.Advance(4.1f); lighting.Apply(); } // a full Mars day
                long bytes = System.GC.GetAllocatedBytesForCurrentThread() - before;
                Assert.AreEqual(0, bytes, "0 B over 300 updates");
                Assert.AreEqual(DayNightMath.AmbientIntensity(PlanetId.Mars, lighting.LocalTime), lighting.ambient.intensity, 1e-5f);
            }
            finally
            {
                Object.DestroyImmediate(root);
                Object.DestroyImmediate(planet);
            }
        }

        static void AssertVec(Vector2 e, Vector2 a, string msg)
        {
            Assert.AreEqual(e.x, a.x, 1e-4f, msg + " x");
            Assert.AreEqual(e.y, a.y, 1e-4f, msg + " y");
        }
    }
}
