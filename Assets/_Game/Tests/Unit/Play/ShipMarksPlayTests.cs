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

        /// <summary>Holds full thrust for `seconds` from rest on the pad; returns the height climbed through `climbed`.</summary>
        static IEnumerator Burn(SideShip s, float seconds, System.Action<float> climbed)
        {
            yield return Steps(30);
            Assert.IsTrue(s.AtRest, "at rest on the pad");
            float y0 = s.Body.position.y;
            s.intent.thrust = 1f;
            yield return Steps(Mathf.RoundToInt(seconds / Time.fixedDeltaTime));
            yield return null; // HUD LateUpdate
            climbed(s.Body.position.y - y0);
        }

        [UnityTest]
        public IEnumerator Mk1CrawlsOffSaturnWithTheAmberHud()
        {
            var s = Spawn(PlanetId.Saturn, 10.44f, 1);
            var hud = new GameObject("ShipHud").AddComponent<ShipHud>();
            hud.ship = s;
            float climbed = 0f;
            yield return Burn(s, 2f, h => climbed = h);
            TestContext.Out.WriteLine($"[MERIDIAN] Saturn Mk1: {climbed:F2} m in 2 s (net {12f - 10.44f:F2} m/s²)");
            Assert.AreEqual(0.5f * 1.56f * 4f, climbed, 0.6f, "a slow climb at net 1.56 m/s²");
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
                float climbed = 0f;
                yield return Burn(s, 2f, h => climbed = h);
                TestContext.Out.WriteLine($"[MERIDIAN] Jupiter Mk{mark}: {climbed:F2} m in 2 s, HUD {hud.State}");
                if (mark < 3)
                {
                    Assert.Less(climbed, 0.05f, $"Mk{mark} ({ShipMarks.Thrust(mark)} m/s²) cannot climb against 24.79");
                    Assert.IsTrue(s.ThrustBelowGravity);
                    Assert.AreEqual(ShipHud.TwrState.CannotClimb, hud.State);
                    Assert.IsTrue(hud.Warning.enabled);
                }
                else
                {
                    Assert.Greater(climbed, 15f, "Mk3 (35 m/s²) climbs at net 10.21 m/s²");
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
