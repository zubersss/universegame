using System.Collections;
using Meridian.Core;
using Meridian.Planets;
using Meridian.Ship;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>
    /// U-065, U-107 (PlayMode, D-106): the climb limit is physics alone. Real gravity on a stub pad: Mk1 crawls off Saturn
    /// (net 1.56 m/s², the HUD amber below T/W 1.2), Mk1 and Mk2 stay on Jupiter's pad (12 and 20 &lt; 24.79, the HUD says it
    /// cannot climb), Mk3 lifts off Jupiter. No gate refuses anything: the thrust simply loses to g.
    /// </summary>
    public class ShipMarksPlayTests
    {
        const float X = 120000f;
        Scene scene;
        Vector2 savedGravity;
        PlanetConfig planet;
        int savedMark = -1;

        [SetUp]
        public void SetUp()
        {
            savedGravity = Physics2D.gravity;
            if (GameState.Instance != null) savedMark = GameState.Instance.thrusterMark;
            scene = SceneManager.CreateScene("MarksTest_" + System.Guid.NewGuid().ToString("N").Substring(0, 6));
            SceneManager.SetActiveScene(scene);
            var ground = new GameObject("Ground").AddComponent<BoxCollider2D>();
            ground.size = new Vector2(400f, 1f);
            ground.transform.position = new Vector3(X, -0.5f, 0f);
            planet = ScriptableObject.CreateInstance<PlanetConfig>();
            planet.datumY = 0;
            planet.escapeAltitude = 400;
            planet.worldHeight = 2000;
        }

        [UnityTearDown]
        public IEnumerator TearDown()
        {
            Physics2D.gravity = savedGravity;
            if (GameState.Instance != null && savedMark > 0) GameState.Instance.thrusterMark = savedMark;
            Object.Destroy(planet);
            yield return SceneManager.UnloadSceneAsync(scene);
        }

        static void SetMark(SideShip s, int mark)
        {
            s.thrusterMark = mark;
            if (GameState.Instance != null) GameState.Instance.thrusterMark = mark;
        }

        SideShip Spawn(PlanetId id, float g, int mark, float xOffset = 0f)
        {
            planet.id = id;
            planet.gravity = g;
            Physics2D.gravity = new Vector2(0f, -g);
            var go = new GameObject("Pilgrim");
            go.transform.position = new Vector3(X + xOffset, SideShip.SkidDrop + 0.02f, 0f);
            go.AddComponent<Rigidbody2D>();
            go.AddComponent<BoxCollider2D>();
            var s = go.AddComponent<SideShip>();
            s.externalInput = true;
            // U-169: a leftover Core scene's streamer ticks the static SolidRescue; it would park this synthetic ship over "unloaded ground"
            // (as ShipSideTests).
            Meridian.Terrain.SolidRescue.Unregister(s.Body);
            s.ConfigureFor(planet);
            s.Hull = 100f;
            SetMark(s, mark);
            return s;
        }

        static IEnumerator Steps(int n) { for (int i = 0; i < n; i++) yield return new WaitForFixedUpdate(); }

        /// <summary>D-176: a burn's measures. U-149's throttle spools over 0.35 s and air drags (−DragK·ρ·|v|·v), so the net acceleration is
        /// measured after the spool and judged against the model at the measured mean speed.</summary>
        struct BurnResult { public float climbed, net, model, speed; }

        /// <summary>Holds full thrust for `seconds` from rest on the pad: the height climbed, the net vertical acceleration from just after the
        /// spool to the end, and the model's net (thrust − g − drag at the mean speed of that span, in the ship's air).</summary>
        static IEnumerator Burn(SideShip s, float seconds, float thrust, float g, System.Action<BurnResult> done)
        {
            yield return Steps(30);
            Assert.IsTrue(s.AtRest, "at rest on the pad");
            float y0 = s.Body.position.y, dt = Time.fixedDeltaTime;
            s.intent.thrust = 1f;
            int total = Mathf.RoundToInt(seconds / dt), from = Mathf.CeilToInt((Meridian.Ship.RocketFlight.SpoolUp + 0.05f) / dt);
            float va = 0f;
            for (int i = 1; i <= total; i++) { yield return new WaitForFixedUpdate(); if (i == from) va = s.Body.linearVelocity.y; }
            float vb = s.Body.linearVelocity.y, span = (total - from) * dt, vmid = 0.5f * (va + vb);
            yield return null; // HUD LateUpdate
            done(new BurnResult
            {
                climbed = s.Body.position.y - y0,
                net = (vb - va) / span,
                model = thrust - g - Meridian.Ship.RocketFlight.DragK * s.AirDensity * vmid * Mathf.Abs(vmid),
                speed = vmid,
            });
        }

        [UnityTest]
        public IEnumerator Mk1CrawlsOffSaturnWithTheAmberHud()
        {
            var s = Spawn(PlanetId.Saturn, 10.44f, 1);
            var hud = new GameObject("ShipHud").AddComponent<ShipHud>();
            hud.ship = s;
            BurnResult r = default;
            yield return Burn(s, 2f, ShipMarks.Thrust(1), 10.44f, b => r = b);
            TestContext.Out.WriteLine($"[MERIDIAN] Saturn Mk1: {r.climbed:F2} m in 2 s; net {r.net:F2} m/s² after the spool, the model {r.model:F2} at {r.speed:F2} m/s");
            Assert.Greater(r.climbed, 0.5f, "Mk1 crawls off Saturn's pad");
            Assert.AreEqual(r.model, r.net, 0.3f, "D-176: a slow climb at the model's net (12 − 10.44 − drag)");
            Assert.IsFalse(s.ThrustBelowGravity);
            Assert.AreEqual(ShipHud.TwrState.Amber, hud.State, "T/W 1.15 reads amber (D-106)");
            Assert.IsTrue(hud.Warning.enabled);
            LogAssert.NoUnexpectedReceived();
        }

        [UnityTest]
        public IEnumerator Mk1AndMk2StayOnJupitersPadMk3LiftsOff()
        {
            var hud = new GameObject("ShipHud").AddComponent<ShipHud>();
            for (int mark = 1; mark <= 3; mark++)
            {
                var s = Spawn(PlanetId.Jupiter, 24.79f, mark, mark * 30f);
                hud.ship = s;
                BurnResult r = default;
                yield return Burn(s, 2f, ShipMarks.Thrust(mark), 24.79f, b => r = b);
                float climbed = r.climbed;
                TestContext.Out.WriteLine($"[MERIDIAN] Jupiter Mk{mark}: {climbed:F2} m in 2 s, HUD {hud.State}; net {r.net:F2} m/s² after the spool, the model {r.model:F2} at {r.speed:F2} m/s");
                if (mark < 3)
                {
                    Assert.Less(climbed, 0.05f, $"Mk{mark} ({ShipMarks.Thrust(mark)} m/s²) cannot climb against 24.79");
                    Assert.IsTrue(s.ThrustBelowGravity);
                    Assert.AreEqual(ShipHud.TwrState.CannotClimb, hud.State);
                    Assert.IsTrue(hud.Warning.enabled);
                }
                else
                {
                    Assert.GreaterOrEqual(climbed, 12f, "D-176: Mk3 (35 m/s²) climbs at least 12 m in the burn");
                    Assert.AreEqual(r.model, r.net, 0.3f, "D-176: Mk3's net after the spool (35 − 24.79 − drag)");
                    Assert.IsFalse(s.ThrustBelowGravity);
                    Assert.AreEqual(ShipHud.TwrState.Ok, hud.State, "T/W 1.41");
                    Assert.IsFalse(hud.Warning.enabled);
                }
                s.intent = default;
                Object.Destroy(s.gameObject);
                yield return null;
            }
            LogAssert.NoUnexpectedReceived();
        }
    }
}
