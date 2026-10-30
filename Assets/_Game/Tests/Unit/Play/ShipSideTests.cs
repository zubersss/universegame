using System.Collections;
using Meridian.Planets;
using Meridian.Ship;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>U-010 (PlayMode): launch fuel burn, Escape Line event, landing rules (Bible §4.1, §4.3, §5.2).</summary>
    public class ShipSideTests
    {
        const float X = 100000f; // far from any streamed terrain a previous test may have left loaded
        Scene scene;
        Vector2 savedGravity;
        PlanetConfig planet;

        [SetUp]
        public void SetUp()
        {
            savedGravity = Physics2D.gravity;
            scene = SceneManager.CreateScene("ShipTest_" + System.Guid.NewGuid().ToString("N").Substring(0, 6));
            SceneManager.SetActiveScene(scene);
            var ground = new GameObject("Ground").AddComponent<BoxCollider2D>();
            ground.size = new Vector2(400f, 1f);
            ground.transform.position = new Vector3(X, -0.5f, 0f); // top at y = 0

            planet = ScriptableObject.CreateInstance<PlanetConfig>();
            planet.id = PlanetId.Earth;
            planet.gravity = 9.81f;
            planet.escapeVelocityKms = 11.2f; // launch cost 17
            planet.datumY = 0;
            planet.escapeAltitude = 20;       // Escape Line at y = 20 for a short test flight
            planet.worldHeight = 800;
        }

        [UnityTearDown]
        public IEnumerator TearDown()
        {
            Physics2D.gravity = savedGravity;
            Object.Destroy(planet);
            yield return SceneManager.UnloadSceneAsync(scene);
        }

        SideShip Spawn(float g, float height = 0f, float vy = 0f)
        {
            Physics2D.gravity = new Vector2(0f, -g);
            var go = new GameObject("Pilgrim");
            go.transform.position = new Vector3(X, SideShip.SkidDrop + 0.02f + height, 0f);
            go.AddComponent<Rigidbody2D>();
            go.AddComponent<BoxCollider2D>();
            var s = go.AddComponent<SideShip>();
            s.externalInput = true;
            s.ConfigureFor(planet);
            s.Fuel = 100f;
            s.Hull = 100f;
            s.Body.linearVelocity = new Vector2(0f, vy);
            return s;
        }

        static IEnumerator Steps(int n) { for (int i = 0; i < n; i++) yield return new WaitForFixedUpdate(); }

        [UnityTest]
        public IEnumerator LaunchFromEarthCosts17FuelOverFirst3SecondsOfThrust()
        {
            var s = Spawn(9.81f);
            yield return Steps(30);
            Assert.IsTrue(s.AtRest, "landed at rest");
            Assert.AreEqual(100f, s.Fuel, 1e-4f);
            s.intent.thrust = 1f;
            int threeSeconds = Mathf.RoundToInt(3f / Time.fixedDeltaTime);
            yield return Steps(threeSeconds);
            TestContext.Out.WriteLine($"[MERIDIAN] after 3 s of thrust: fuel {s.Fuel:F3}, altitude {s.Body.position.y - SideShip.SkidDrop:F1} m");
            Assert.AreEqual(83f, s.Fuel, 0.05f, "17 units over the first 3 s");
            Assert.Greater(s.Body.position.y, 5f, "climbing (12 m/s² against 9.81)");
            yield return Steps(100);
            Assert.AreEqual(83f, s.Fuel, 0.05f, "atmospheric flight after the burn is free");
        }

        [UnityTest]
        public IEnumerator HalfBurnThenFuelStopsAtTheRightPoint()
        {
            var s = Spawn(9.81f);
            yield return Steps(30);
            s.intent.thrust = 1f;
            yield return Steps(Mathf.RoundToInt(1.5f / Time.fixedDeltaTime));
            Assert.AreEqual(100f - 8.5f, s.Fuel, 0.05f, "half the burn → half the cost");
        }

        [UnityTest]
        public IEnumerator EscapeLineCrossedOnceOnTheWayUpOnly()
        {
            var s = Spawn(9.81f);
            int crossings = 0;
            s.EscapeLineCrossed += () => crossings++;
            yield return Steps(20);
            s.intent.thrust = 1f;
            for (int i = 0; i < 600 && s.Body.position.y < 26f; i++) yield return new WaitForFixedUpdate();
            Assert.Greater(s.Body.position.y, 20f);
            Assert.AreEqual(1, crossings, "raised when the center crosses the line moving up");
            s.intent.thrust = 0f;
            for (int i = 0; i < 600 && s.Body.position.y > 10f; i++) yield return new WaitForFixedUpdate();
            Assert.AreEqual(1, crossings, "falling back through the line raises nothing");
        }

        [UnityTest]
        public IEnumerator TouchdownCleanProportionalAndCrash()
        {
            // Gravity off so each ship meets the ground at exactly its set speed.
            float[] speeds = { 5f, 10.5f, 20f };
            float[] hull = { 100f, 65f, 30f }; // 10.5 m/s: (10.5−6)/9 × 70 = 35 off
            for (int i = 0; i < speeds.Length; i++)
            {
                var s = Spawn(0f, 2f, -speeds[i]);
                s.transform.position += new Vector3(i * 30f, 0f, 0f);
                s.Body.position = s.transform.position;
                for (int k = 0; k < 200 && !s.Grounded; k++) yield return new WaitForFixedUpdate();
                yield return Steps(2);
                TestContext.Out.WriteLine($"[MERIDIAN] touchdown {s.LastTouchdownSpeed:F2} m/s → hull {s.Hull:F1}");
                Assert.AreEqual(speeds[i], s.LastTouchdownSpeed, 0.05f, "impact speed");
                Assert.AreEqual(hull[i], s.Hull, 0.6f, $"hull after {speeds[i]} m/s");
                Object.Destroy(s.gameObject);
            }
            LogAssert.NoUnexpectedReceived();
        }

        [UnityTest]
        public IEnumerator LegsDeployBelowTenMetresAndRetractAbove()
        {
            var s = Spawn(0f, 25f, -5f); // gravity off: constant 5 m/s descent
            var viewGo = new GameObject("View");
            viewGo.transform.SetParent(s.transform, false);
            var view = s.gameObject.AddComponent<ShipLegsView>();
            view.ship = s;
            view.target = viewGo.AddComponent<SpriteRenderer>();
            float timeout = Time.realtimeSinceStartup + 10f;
            while ((view.Retracted == null || view.Deployed == null) && Time.realtimeSinceStartup < timeout) yield return null;
            Assert.NotNull(view.Retracted, "ships/pilgrim/side loaded");
            Assert.NotNull(view.Deployed, "ships/pilgrim/side_legs loaded");

            // Same canvas and pivot (D-025): the hull can't jump when the sprite swaps.
            Assert.AreEqual(view.Retracted.rect.size, view.Deployed.rect.size, "same canvas");
            Assert.That(Vector2.Distance(view.Retracted.pivot, view.Deployed.pivot), Is.LessThanOrEqualTo(1f), "pivot within 1 px");

            yield return new WaitForFixedUpdate(); yield return null;
            Assert.Greater(s.AltitudeAboveGround, 10f);
            Assert.AreSame(view.Retracted, view.target.sprite, "gear retracted above 10 m");
            // Where the hull is drawn relative to its own transform (the body interpolates, so compare in sprite space).
            var drawn = (Vector2)(view.target.bounds.center - view.target.transform.position);

            for (int i = 0; i < 400 && s.AltitudeAboveGround > 10f; i++) yield return new WaitForFixedUpdate();
            yield return null; // LateUpdate applies the swap
            Assert.LessOrEqual(s.AltitudeAboveGround, 10f);
            Assert.AreSame(view.Deployed, view.target.sprite, "legs out at or below 10 m");
            var drawnAfter = (Vector2)(view.target.bounds.center - view.target.transform.position);
            Assert.That(Vector2.Distance(drawn, drawnAfter), Is.LessThanOrEqualTo(1f / 128f), "hull drawn at the same place (±1 px)");

            s.Body.linearVelocity = new Vector2(0f, 5f);
            for (int i = 0; i < 400 && s.AltitudeAboveGround <= 10f; i++) yield return new WaitForFixedUpdate();
            yield return null;
            Assert.Greater(s.AltitudeAboveGround, 10f);
            Assert.AreSame(view.Retracted, view.target.sprite, "legs back in above 10 m");
            LogAssert.NoUnexpectedReceived();
        }

        [Test]
        public void TouchdownRuleBoundaries()
        {
            Assert.AreEqual(100f, SideShip.HullAfterTouchdown(100f, 6f, 100f), "6 m/s is clean");
            Assert.AreEqual(30f, SideShip.HullAfterTouchdown(100f, 15f, 100f), 1e-4f, "15 m/s: full proportional damage");
            Assert.AreEqual(30f, SideShip.HullAfterTouchdown(100f, 15.01f, 100f), 1e-4f, "crash → 30%");
            Assert.AreEqual(20f, SideShip.HullAfterTouchdown(20f, 30f, 100f), "a crash never raises hull");
        }

        [UnityTest]
        public IEnumerator Mk1CannotLiftOffJupiter()
        {
            var s = Spawn(24.79f);
            yield return Steps(30);
            Assert.IsTrue(s.ThrustBelowGravity, "HUD warning condition: thrust 12 < g 24.79");
            float y = s.Body.position.y;
            s.intent.thrust = 1f;
            yield return Steps(100);
            Assert.AreEqual(y, s.Body.position.y, 0.05f, "stays on the ground");
        }
    }
}
