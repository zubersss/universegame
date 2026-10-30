using System.Collections;
using Meridian.Core;
using Meridian.Planets;
using Meridian.Ship;
using Meridian.Space;
using Meridian.Transitions;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>U-012 (PlayMode): launch Earth → ring and entry ring → Mars, through the real Core flow.</summary>
    public class TransitionTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";

        static IEnumerator Boot(System.Action<SceneDirector> done)
        {
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 20f;
            while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
            for (int i = 0; i < 30; i++) yield return new WaitForFixedUpdate();
            done(director);
        }

        static IEnumerator WaitIdle(TransitionDirector t, float seconds)
        {
            float timeout = Time.realtimeSinceStartup + seconds;
            while (!t.Busy && Time.realtimeSinceStartup < timeout) yield return null; // wait for it to start
            while (t.Busy && Time.realtimeSinceStartup < timeout) yield return null;
        }

        /// <summary>Boards the ship and puts it just under the Escape Line climbing; the next steps launch it.</summary>
        static IEnumerator LaunchFromEarth(SceneDirector director, TransitionDirector transitions)
        {
            var side = director.PlanetSide;
            var ship = side.ship;
            ship.GetComponent<ShipBoarding>().ForceAboard();
            ship.externalInput = true;
            var p = new Vector2(ship.Body.position.x, side.Config.EscapeLineY - 0.5f);
            ship.Body.position = p;
            ship.transform.position = p;
            ship.Body.linearVelocity = new Vector2(0f, 12f);
            yield return WaitIdle(transitions, 10f);
        }

        [UnityTest]
        public IEnumerator LaunchPutsShipOnEarthsRingAtItsLongitudeWithStateCarried()
        {
            SceneDirector director = null;
            yield return Boot(d => director = d);
            var transitions = Object.FindAnyObjectByType<TransitionDirector>();
            var state = GameState.Instance;
            state.hull = 87f; state.fuel = 64.5f;
            state.cargo.Add(new CargoStack { itemId = 3, count = 12 });
            var side = director.PlanetSide;
            float x = side.ship.Body.position.x;
            int width = side.Config.worldWidth;
            var time = Object.FindAnyObjectByType<TimeSystem>();

            yield return LaunchFromEarth(director, transitions);

            Assert.AreEqual(ViewMode.Space, state.view, "now in space");
            Assert.IsNull(director.PlanetSide, "PlanetSide unloaded");
            TestContext.Out.WriteLine($"[MERIDIAN] launch took {transitions.LastLaunchSeconds:F2} s");
            Assert.LessOrEqual(transitions.LastLaunchSeconds, 1.5f, "launch ≤ 1.5 s total");

            var earth = transitions.LaunchBody.Value;
            Assert.AreEqual(PlanetId.Earth, earth.planet);
            var offset = transitions.LaunchPlacement - earth.position;
            Assert.AreEqual(earth.RingRadius, offset.magnitude, 0.01f, "on the Atmosphere Ring");
            float placedAngle = Mathf.Repeat(Mathf.Atan2(offset.y, offset.x) * Mathf.Rad2Deg, 360f);
            Assert.AreEqual(transitions.LastLaunchAngle, placedAngle, 0.05f);
            float lonOnly = TransitionDirector.Longitude(x, width);
            float rotationNow = time.DayFraction(state.catalog.Get(PlanetId.Earth)) * 360f;
            Assert.AreEqual(0f, Mathf.DeltaAngle(lonOnly + rotationNow, placedAngle), 0.5f,
                "angle = longitude + planet rotation (rotation drifts < 0.5° during the test)");
            var radial = Vector2.Dot(transitions.LaunchVelocity, offset.normalized);
            Assert.AreEqual(20f, radial, 0.01f, "20 u/s outward");
            Assert.AreEqual(20f, transitions.LaunchVelocity.magnitude, 0.01f, "purely radial");

            Assert.AreEqual(87f, state.hull, 1e-4f, "hull carried");
            Assert.AreEqual(64.5f, state.fuel, 1e-4f, "fuel carried");
            Assert.AreEqual(1, state.cargo.Count);
            Assert.AreEqual(12, state.cargo[0].count, "cargo carried");
            LogAssert.NoUnexpectedReceived();
        }

        [UnityTest]
        public IEnumerator EntryIntoMarsArrivesAtEscapeLinePlus20Descending15()
        {
            SceneDirector director = null;
            yield return Boot(d => director = d);
            var transitions = Object.FindAnyObjectByType<TransitionDirector>();
            yield return LaunchFromEarth(director, transitions);
            var state = GameState.Instance;
            float fuel = state.fuel;

            var ship = director.Space.GetComponentInChildren<SpaceShip>();
            ship.externalInput = true;
            ship.intent = default;
            var mars = ship.world.Find("mars").Value;
            // Just outside Mars' ring, moving inward: the next step crosses it.
            ship.Position = mars.position + new Vector2(0f, mars.RingRadius + 0.5f);
            ship.Velocity = new Vector2(0f, -40f);
            yield return new WaitForSeconds(1.1f); // past the launch invulnerability
            ship.Position = mars.position + new Vector2(0f, mars.RingRadius + 0.5f);
            ship.Velocity = new Vector2(0f, -40f);
            yield return WaitIdle(transitions, 15f);

            TestContext.Out.WriteLine($"[MERIDIAN] entry took {transitions.LastEntrySeconds:F2} s");
            Assert.AreEqual(ViewMode.PlanetSide, state.view);
            Assert.AreEqual(PlanetId.Mars, state.currentPlanet);
            var side = director.PlanetSide;
            Assert.NotNull(side, "PlanetSide loaded");
            Assert.AreEqual(PlanetId.Mars, side.Config.id);
            Assert.IsTrue(side.LastArrival.HasValue);
            var arrival = side.LastArrival.Value;
            Assert.AreEqual(570f + 20f, arrival.shipPosition.y, 1e-3f, "Escape Line + 20 m");
            Assert.AreEqual(-15f, arrival.shipVelocity.y, 1e-3f, "descending 15 m/s");
            Assert.AreEqual(-3.72f, Physics2D.gravity.y, 1e-4f, "Mars gravity on");
            Assert.AreEqual(fuel, state.fuel, 1e-4f, "fuel unchanged");
            Assert.IsTrue(side.ship.GetComponent<ShipBoarding>().Aboard, "surveyor aboard");
            Assert.LessOrEqual(transitions.LastEntrySeconds, 4f, "planet load ≤ 4 s (Bible §11.1)");

            // The ship then flies down under Mars gravity (sanity: it is descending, not frozen).
            float y0 = side.ship.Body.position.y;
            for (int i = 0; i < 20; i++) yield return new WaitForFixedUpdate();
            Assert.Less(side.ship.Body.position.y, y0, "descending");
            LogAssert.NoUnexpectedReceived();
        }
    }
}
