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
    /// U-065 (PlayMode): on Saturn (g 10.44, launch cost 53) a Thruster Mk1 refuses to lift off and the ship HUD
    /// says so; a Mk2 lifts off. Stub scene like ShipSideTests (the cloud column itself arrives with U-061).
    /// </summary>
    public class ShipMarksPlayTests
    {
        const float X = 120000f;
        Scene scene;
        Vector2 savedGravity;
        PlanetConfig saturn;
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
            saturn = ScriptableObject.CreateInstance<PlanetConfig>();
            saturn.id = PlanetId.Saturn;
            saturn.gravity = 10.44f;
            saturn.escapeVelocityKms = 35.5f;
            saturn.datumY = 0;
            saturn.escapeAltitude = 400;
            saturn.worldHeight = 2000;
        }

        [UnityTearDown]
        public IEnumerator TearDown()
        {
            Physics2D.gravity = savedGravity;
            if (GameState.Instance != null && savedMark > 0) GameState.Instance.thrusterMark = savedMark;
            Object.Destroy(saturn);
            yield return SceneManager.UnloadSceneAsync(scene);
        }

        static void SetMark(SideShip s, int mark)
        {
            s.thrusterMark = mark;
            if (GameState.Instance != null) GameState.Instance.thrusterMark = mark;
        }

        SideShip Spawn()
        {
            Physics2D.gravity = new Vector2(0f, -saturn.gravity);
            var go = new GameObject("Pilgrim");
            go.transform.position = new Vector3(X, SideShip.SkidDrop + 0.02f, 0f);
            go.AddComponent<Rigidbody2D>();
            go.AddComponent<BoxCollider2D>();
            var s = go.AddComponent<SideShip>();
            s.externalInput = true;
            s.ConfigureFor(saturn);
            s.Fuel = 100f;
            s.Hull = 100f;
            return s;
        }

        static IEnumerator Steps(int n) { for (int i = 0; i < n; i++) yield return new WaitForFixedUpdate(); }

        [UnityTest]
        public IEnumerator Mk1RefusesOnSaturnWithTheHudLineMk2LiftsOff()
        {
            var s = Spawn();
            SetMark(s, 1);
            var hud = new GameObject("ShipHud").AddComponent<ShipHud>();
            hud.ship = s;
            yield return Steps(30);
            Assert.IsTrue(s.AtRest, "landed at rest");
            Assert.IsFalse(s.CanLaunchHere, "§4.3: Mk1 can't launch from Saturn");

            s.intent.thrust = 1f;
            yield return Steps(60);
            yield return null; // HUD LateUpdate
            Assert.IsTrue(s.LaunchRefused, "lift refused");
            Assert.Less(s.Body.position.y, SideShip.SkidDrop + 0.2f, "still on the ground");
            Assert.AreEqual(100f, s.Fuel, 1e-3f, "a refused launch burns nothing");
            Assert.IsTrue(hud.Warning.enabled);
            Assert.AreEqual("THRUSTER MK1 CAN'T LIFT OFF HERE", hud.Warning.text);

            s.intent.thrust = 0f;
            SetMark(s, 2);
            yield return Steps(10);
            Assert.IsTrue(s.CanLaunchHere, "Mk2 can launch from Saturn");
            s.intent.thrust = 1f;
            yield return Steps(Mathf.RoundToInt(2f / Time.fixedDeltaTime));
            yield return null;
            Assert.IsFalse(s.LaunchRefused);
            Assert.Greater(s.Body.position.y, SideShip.SkidDrop + 3f, "Mk2 (20 m/s²) climbs against 10.44");
            Assert.Less(s.Fuel, 100f, "the launch burn is paid");
            Assert.IsFalse(hud.Warning.enabled && hud.Warning.text.StartsWith("THRUSTER"), "no refusal line in flight");
            LogAssert.NoUnexpectedReceived();
        }
    }
}
