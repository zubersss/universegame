using System.Collections;
using Meridian.Core;
using Meridian.Creatures;
using Meridian.Planet.Weather;
using Meridian.Planets;
using Meridian.Player;
using Meridian.Rig;
using Meridian.Save;
using Meridian.Ship;
using Meridian.Space;
using Meridian.Transitions;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests.LeadQA
{
    /// <summary>
    /// L-011: M2 soak. Earth at night with creatures and a dig, then the ship flies to Mars
    /// on its own controls, lands, and rides out a forced dust storm. Over 10 game minutes
    /// in one run with a clean console.
    /// </summary>
    public class M2SoakTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";
        string saveRoot;

        [SetUp]
        public void SetUp()
        {
            saveRoot = System.IO.Path.Combine(Application.temporaryCachePath, "meridian_leadqa_m2_" + System.Guid.NewGuid().ToString("N").Substring(0, 6));
            SaveSystem.RootOverride = saveRoot;
        }

        [TearDown]
        public void TearDown()
        {
            SaveSystem.RootOverride = null;
            if (System.IO.Directory.Exists(saveRoot)) System.IO.Directory.Delete(saveRoot, true);
        }

        [UnityTest, Timeout(600000)]
        public IEnumerator EarthNightCreaturesDigThenMarsStormLanding()
        {
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 20f;
            while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
            Assert.IsTrue(director.IsReady, "boot");
            var state = GameState.Instance;
            var time = Object.FindAnyObjectByType<TimeSystem>();
            var transitions = Object.FindAnyObjectByType<TransitionDirector>();
            double gameStart = time.GameSeconds;

            // 1. Earth: jump to just after midnight, let the night run, creatures appear.
            var earth = director.PlanetSide.Config;
            double day = earth.dayLengthRealMinutes * 60.0 * TimeSystem.GameSecondsPerRealSecond;
            time.SetGameSeconds((System.Math.Floor(time.GameSeconds / day) + 1.0) * day + 0.02 * day);
            timeout = Time.realtimeSinceStartup + 30f;
            while (Object.FindObjectsByType<Creature>(FindObjectsSortMode.None).Length == 0 && Time.realtimeSinceStartup < timeout) yield return null;
            int creatures = Object.FindObjectsByType<Creature>(FindObjectsSortMode.None).Length;
            TestContext.Out.WriteLine($"[LEADQA] Earth night creatures: {creatures}");
            Assert.Greater(creatures, 0, "creatures spawn on Earth at night");

            // 2. Dig next to the surveyor.
            var player = Object.FindAnyObjectByType<PlayerController>();
            var rig = Object.FindAnyObjectByType<RigTools>();
            Assert.NotNull(player, "player"); Assert.NotNull(rig, "rig");
            bool dug = false;
            Vector2 feet = player.transform.position;
            for (int dx = -3; dx <= 3 && !dug; dx++)
                dug = rig.Dig(feet + new Vector2(dx, -0.5f));
            Assert.IsTrue(dug, "dug a tile next to the surveyor");
            for (int i = 0; i < 60; i++) yield return null;

            // 3. Lift off from the pad on full thrust and cross the Escape Line.
            var ship = director.PlanetSide.ship;
            ship.GetComponent<ShipBoarding>().ForceAboard();
            ship.externalInput = true;
            bool escaped = false;
            ship.EscapeLineCrossed += () => escaped = true;
            ship.intent = new ShipSideIntent { thrust = 1f };
            timeout = Time.realtimeSinceStartup + 90f;
            while (!escaped && Time.realtimeSinceStartup < timeout) yield return new WaitForFixedUpdate();
            Assert.IsTrue(escaped, "escaped Earth");
            yield return WaitIdle(transitions, 10f);
            Assert.AreEqual(ViewMode.Space, state.view, "in space");

            // 4. Fly to Mars, steering around Earth.
            var craft = director.Space.GetComponentInChildren<SpaceShip>();
            craft.externalInput = true;
            var earthBody = craft.world.Find("earth").Value;
            var mars = craft.world.Find("mars").Value;
            Vector2 escapePoint = earthBody.position + (craft.Position - earthBody.position).normalized * (earthBody.WellRadius + 20f);
            timeout = Time.realtimeSinceStartup + 60f;
            while (state.view == ViewMode.Space && !transitions.Busy && Time.realtimeSinceStartup < timeout)
            {
                Vector2 target = mars.position;
                if ((craft.Position - earthBody.position).magnitude < earthBody.WellRadius) target = escapePoint;
                else if (SegmentDistance(earthBody.position, craft.Position, mars.position) < earthBody.RingRadius + 15f)
                {
                    Vector2 toShip = (craft.Position - earthBody.position).normalized;
                    Vector2 perp = new Vector2(-toShip.y, toShip.x);
                    if (Vector2.Dot(perp, mars.position - earthBody.position) < 0f) perp = -perp;
                    target = earthBody.position + (toShip + perp).normalized * (earthBody.WellRadius + 30f);
                }
                Steer(craft, target);
                yield return null;
            }
            yield return WaitIdle(transitions, 15f);
            Assert.AreEqual(PlanetId.Mars, state.currentPlanet, "entered Mars");

            // 5. Powered landing on Mars.
            ship = director.PlanetSide.ship;
            ship.externalInput = true;
            float? touchdown = null;
            ship.TouchedDown += v => touchdown = v;
            timeout = Time.realtimeSinceStartup + 120f;
            while (touchdown == null && Time.realtimeSinceStartup < timeout)
            {
                float targetVy = -Mathf.Clamp(ship.AltitudeAboveGround * 0.25f, 2f, 15f);
                float accel = (targetVy - ship.Body.linearVelocity.y) * 2f + ship.Gravity;
                ship.intent = new ShipSideIntent { thrust = Mathf.Clamp01(accel / ship.Thrust) };
                yield return new WaitForFixedUpdate();
            }
            ship.intent = default;
            Assert.IsTrue(touchdown.HasValue, "landed on Mars");
            Assert.LessOrEqual(touchdown.Value, 6f, "clean landing");

            // 6. Ride out a forced dust storm on Mars.
            var storm = Object.FindAnyObjectByType<DustStorm>();
            Assert.NotNull(storm, "DustStorm on Mars");
            storm.Force(61f, 30f);
            timeout = Time.realtimeSinceStartup + 75f;
            while (storm.Phase != StormPhase.Storm && Time.realtimeSinceStartup < timeout) yield return null;
            Assert.AreEqual(StormPhase.Storm, storm.Phase, "storm started");
            float stormEnd = Time.realtimeSinceStartup + 10f;
            while (Time.realtimeSinceStartup < stormEnd) yield return null;

            double gameMinutes = (time.GameSeconds - gameStart) / 60.0;
            TestContext.Out.WriteLine($"[LEADQA] M2 soak: {gameMinutes:F1} game min, Mars touchdown {touchdown.Value:F2} m/s");
            Assert.GreaterOrEqual(gameMinutes, 10.0, "≥ 10 game minutes in one run");
            LogAssert.NoUnexpectedReceived();
        }

        static void Steer(SpaceShip craft, Vector2 target)
        {
            Vector2 to = target - craft.Position;
            float delta = Mathf.DeltaAngle(craft.Heading, Mathf.Atan2(to.y, to.x) * Mathf.Rad2Deg);
            craft.intent = new ShipIntent { rotate = Mathf.Clamp(delta / 20f, -1f, 1f), thrust = Mathf.Abs(delta) < 30f ? 1f : 0f };
        }

        static float SegmentDistance(Vector2 p, Vector2 a, Vector2 b)
        {
            Vector2 ab = b - a;
            float t = Mathf.Clamp01(Vector2.Dot(p - a, ab) / Mathf.Max(ab.sqrMagnitude, 1e-6f));
            return (a + ab * t - p).magnitude;
        }

        static IEnumerator WaitIdle(TransitionDirector t, float seconds)
        {
            float timeout = Time.realtimeSinceStartup + seconds;
            while (!t.Busy && Time.realtimeSinceStartup < timeout) yield return null;
            while (t.Busy && Time.realtimeSinceStartup < timeout) yield return null;
        }
    }
}
