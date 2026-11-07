using System.Collections;
using Meridian.Planets;
using Meridian.Ship;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>
    /// U-010, U-107 (PlayMode): the upright rocket on a stub pad with real physics: lift-off and hover at thrust = g, tilt
    /// clamp and spring back, the tilted-touchdown tip-over, Escape Line event, landing rules (Bible §4.3 v4.1, §5.2).
    /// </summary>
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
            planet.escapeVelocityKms = 11.2f;
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
            s.Hull = 100f;
            s.Body.linearVelocity = new Vector2(0f, vy);
            return s;
        }

        static IEnumerator Steps(int n) { for (int i = 0; i < n; i++) yield return new WaitForFixedUpdate(); }

        [UnityTest]
        public IEnumerator LiftsOffEarthThenHoversWhereThrustEqualsG()
        {
            var s = Spawn(9.81f);
            yield return Steps(30);
            Assert.IsTrue(s.AtRest, "landed at rest");
            s.intent.thrust = 1f; // no fuel, no burn window: thrust is simply held (D-103)
            yield return Steps(Mathf.RoundToInt(2f / Time.fixedDeltaTime));
            Assert.Greater(s.Body.position.y, SideShip.SkidDrop + 3f, "climbing (12 m/s² against 9.81)");
            s.intent.thrust = 9.81f / s.Thrust; // throttle so thrust = g
            yield return Steps(2);
            float v0 = s.Body.linearVelocity.y;
            yield return Steps(Mathf.RoundToInt(3f / Time.fixedDeltaTime));
            float dv = s.Body.linearVelocity.y - v0;
            TestContext.Out.WriteLine($"[MERIDIAN] hover: Δv {dv:F4} m/s over 3 s at throttle {s.intent.thrust:F3}");
            Assert.AreEqual(0f, dv, 0.01f * 9.81f * 3f, "hovers: velocity holds within 1 % of g·t");
            Assert.AreEqual(0f, s.Tilt, 1e-4f, "upright without steering");
        }

        [UnityTest]
        public IEnumerator TiltClampsAt35SpringsBackAndThrustFollowsTheNose()
        {
            var s = Spawn(0f, 20f); // gravity off, well above the ground
            s.intent = new ShipSideIntent { lateral = 1f }; // D: nose to the right
            yield return Steps(Mathf.RoundToInt(1f / Time.fixedDeltaTime));
            Assert.AreEqual(-RocketFlight.MaxTilt, s.Tilt, 1e-3f, "clamped at 35°");
            Assert.AreEqual(-RocketFlight.MaxTilt, Mathf.DeltaAngle(0f, s.Body.rotation), 1f, "the hull is turned");
            s.intent = new ShipSideIntent { thrust = 1f, lateral = 1f };
            yield return Steps(25);
            Assert.Greater(s.Body.linearVelocity.x, 1f, "thrust along the tilted nose pushes right");
            s.intent = new ShipSideIntent { lateral = -1f };
            yield return Steps(Mathf.RoundToInt(1f / Time.fixedDeltaTime));
            Assert.AreEqual(RocketFlight.MaxTilt, s.Tilt, 1e-3f, "A: clamped at +35°");
            s.intent = default;
            yield return Steps(Mathf.RoundToInt(0.6f / Time.fixedDeltaTime));
            Assert.Less(Mathf.Abs(s.Tilt), 1f, "springs back upright on release");
            Assert.Less(Mathf.Abs(Mathf.DeltaAngle(0f, s.Body.rotation)), 1.5f, "the hull follows");
            LogAssert.NoUnexpectedReceived();
        }

        [UnityTest]
        public IEnumerator TiltedTouchdownTipsAndRightsInHalfASecondWithoutDamage()
        {
            var s = Spawn(3.72f, 3f); // Mars g, 3 m up: a slow, clean drop
            int tipped = 0;
            s.TippedOver += () => tipped++;
            s.intent = new ShipSideIntent { lateral = -1f }; // A: nose left, leaning past 20°
            for (int k = 0; k < 300 && !s.Grounded; k++) yield return new WaitForFixedUpdate();
            Assert.IsTrue(s.Grounded, "touched down");
            s.intent = default;
            TestContext.Out.WriteLine($"[MERIDIAN] tilted touchdown at {s.LastTouchdownSpeed:F2} m/s, tilt {s.Tilt:F1}°");
            Assert.AreEqual(1, tipped, "a touchdown past 20° tips the ship");
            Assert.IsTrue(s.Flight.Righting);
            bool swungPast = false;
            int steps = Mathf.CeilToInt(RocketFlight.RightingSeconds / Time.fixedDeltaTime);
            for (int k = 0; k < steps; k++) { yield return new WaitForFixedUpdate(); if (s.Tilt < -0.5f) swungPast = true; }
            yield return Steps(2);
            Assert.IsTrue(swungPast, "it wobbles past upright");
            Assert.IsFalse(s.Flight.Righting, "righted within 0.5 s");
            Assert.AreEqual(0f, s.Tilt, 1e-4f);
            yield return Steps(10);
            Assert.Less(Mathf.Abs(Mathf.DeltaAngle(0f, s.Body.rotation)), 1f, "standing upright");
            Assert.AreEqual(100f, s.Hull, 1e-4f, "tipping does no damage");
            LogAssert.NoUnexpectedReceived();
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
            while (view.Probing && Time.realtimeSinceStartup < timeout) yield return null;
            if (view.UsesRig)
            {
                // U-103 (D-111): the drawn rig replaces the two sprites; the fins are the legs, always drawn, flexed on touchdown.
                while (!view.RigReady && Time.realtimeSinceStartup < timeout) yield return null;
                Assert.IsTrue(view.RigReady, "ships/pilgrim/rig built");
                Assert.AreEqual(6, view.Rig.Bones.Length, "pilgrim_side has six bones");
                Assert.AreEqual(-SideShip.SkidDrop, view.Rig.Root.localPosition.y, 1e-4f, "the rig origin sits on the skid line");
                Assert.AreEqual(new Vector2(0f, 0.85f), view.Rig.Socket("tail_exhaust", Vector2.zero), "tail_exhaust socket from the json");
                Assert.AreEqual(ShipLegsView.FinWobble, view.Rig.Playing, "fins wobble in flight");
                Assert.IsFalse(view.target.enabled, "the legacy sprite renderer is off");
                yield return new WaitForFixedUpdate(); yield return null;
                Assert.Greater(s.AltitudeAboveGround, 10f);
                Assert.IsFalse(view.ShowingLegs, "above 10 m: LegsDeployed false");
                for (int i = 0; i < 400 && s.AltitudeAboveGround > 10f; i++) yield return new WaitForFixedUpdate();
                yield return null;
                Assert.IsTrue(view.ShowingLegs, "at or below 10 m: LegsDeployed true");
                LogAssert.NoUnexpectedReceived();
                yield break;
            }
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
        public IEnumerator Mk1CannotClimbJupiter()
        {
            var s = Spawn(24.79f);
            yield return Steps(30);
            Assert.IsTrue(s.ThrustBelowGravity, "HUD condition: thrust 12 < g 24.79 (D-106: physics alone)");
            float y = s.Body.position.y;
            s.intent.thrust = 1f;
            yield return Steps(100);
            Assert.AreEqual(y, s.Body.position.y, 0.05f, "stays on the ground");
        }
    }
}
