using System.Collections;
using Meridian.Core;
using Meridian.Space;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>U-011 (PlayMode): cruise/boost caps, an Earth → Mars flight, the Sun's kill zone.</summary>
    public class SpaceFlightTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";

        static IEnumerator BootSpace(System.Action<SpaceShip> done)
        {
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#else
            yield return SceneManager.LoadSceneAsync("Core", LoadSceneMode.Single);
#endif
            var director = Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 10f;
            while (!director.IsReady && Time.realtimeSinceStartup < timeout) yield return null;
            director.SetView(ViewMode.Space);
            yield return null;
            var ship = director.Space.GetComponentInChildren<SpaceShip>();
            Assert.NotNull(ship, "ship in Space");
            Assert.IsTrue(ship.world.Built, "SpaceWorld built");
            ship.externalInput = true;
            ship.intent = default;
            done(ship);
        }

        static IEnumerator Seconds(float s)
        {
            int steps = Mathf.CeilToInt(s / Time.fixedDeltaTime);
            for (int i = 0; i < steps; i++) yield return new WaitForFixedUpdate();
        }

        [UnityTest]
        public IEnumerator CruiseAndBoostCaps()
        {
            SpaceShip ship = null;
            yield return BootSpace(s => ship = s);
            ship.Position = new Vector2(0f, 9000f); // empty space, no wells
            ship.Velocity = Vector2.zero;
            ship.Heading = 0f;
            ship.intent.thrust = 1f;
            yield return Seconds(4f);
            Assert.AreEqual(80f, ship.Velocity.magnitude, 0.5f, "cruise 80 u/s");
            float fuelBefore = GameState.Instance.fuel;
            ship.intent.boost = true;
            yield return Seconds(4f);
            Assert.AreEqual(160f, ship.Velocity.magnitude, 0.5f, "boost 160 u/s");
            Assert.Less(GameState.Instance.fuel, fuelBefore, "boost burns main fuel");
            LogAssert.NoUnexpectedReceived();
        }

        [UnityTest]
        public IEnumerator EarthToMarsFlightReachesMarsRing()
        {
            SpaceShip ship = null;
            yield return BootSpace(s => ship = s);
            ship.PlaceAtWaystation("earth");
            var mars = ship.world.Find("mars").Value;
            bool felt = false;
            float t = 0f;
            float reached = -1f;
            while (t < 15f)
            {
                var to = mars.position - ship.Position;
                ship.Heading = Mathf.Atan2(to.y, to.x) * Mathf.Rad2Deg; // simple autopilot: nose at Mars
                ship.intent.thrust = 1f;
                yield return new WaitForFixedUpdate();
                t += Time.fixedDeltaTime;
                if (ship.InWellOf == "mars") felt = true;
                if (to.magnitude <= mars.RingRadius) { reached = t; break; }
            }
            TestContext.Out.WriteLine($"[MERIDIAN] Earth waystation → Mars Atmosphere Ring in {reached:F2} s");
            Assert.Greater(reached, 0f, "reached Mars' Atmosphere Ring within 15 s");
            Assert.IsTrue(felt, "Mars' Gravity Well pulled on the way in");
            Assert.IsFalse(ship.Destroyed);
            LogAssert.NoUnexpectedReceived();
        }

        [UnityTest]
        public IEnumerator Mk1ShipEscapesFromMercurysRing()
        {
            SpaceShip ship = null;
            yield return BootSpace(s => ship = s);
            var mercury = ship.world.Find("mercury").Value;
            var outward = mercury.position.normalized; // away from the Sun
            ship.Position = mercury.position + outward * mercury.RingRadius;
            ship.Velocity = Vector2.zero;
            ship.Heading = Mathf.Atan2(outward.y, outward.x) * Mathf.Rad2Deg;
            ship.intent.thrust = 1f;
            float t = 0f;
            while (t < 30f && ship.Position.magnitude <= 1300f && !ship.Destroyed)
            {
                yield return new WaitForFixedUpdate();
                t += Time.fixedDeltaTime;
            }
            TestContext.Out.WriteLine($"[MERIDIAN] Mercury ring → r 1300 in {t:F2} s (Mk1, D-022)");
            Assert.IsFalse(ship.Destroyed);
            Assert.Greater(ship.Position.magnitude, 1300f, "escaped the Sun's pull from Mercury with Mk1");
            LogAssert.NoUnexpectedReceived();
        }

        [UnityTest]
        public IEnumerator SunKillsInsideOnePointTwoR()
        {
            SpaceShip ship = null;
            yield return BootSpace(s => ship = s);
            bool died = false;
            ship.SunDeath += () => died = true;
            ship.Position = new Vector2(600f, 0f); // deep in the Sun's well, no thrust
            ship.Velocity = Vector2.zero;
            yield return Seconds(8f);
            Assert.IsTrue(died, "fell into the Sun");
            Assert.IsTrue(ship.Destroyed);
            Assert.AreEqual(0f, GameState.Instance.hull);
            Assert.GreaterOrEqual(ship.Position.magnitude, 360f - 80f * Time.fixedDeltaTime - 1f, "dies at the 1.2R line");
        }
    }
}
