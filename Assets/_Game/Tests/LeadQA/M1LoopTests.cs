using System.Collections;
using Meridian.Core;
using Meridian.Planets;
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
    /// L-010: the M1 loop flown on the ship's own controls, no teleports after boot.
    /// Earth lift-off from rest → Escape Line → top-down flight to Mars (steering around Earth)
    /// → Mars well pull → entry → powered landing ≤ 6 m/s → save → load → same state.
    /// </summary>
    public class M1LoopTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";
        string saveRoot;
        float savedTimeScale, savedCaptureDelta;

        [SetUp]
        public void SetUp()
        {
            saveRoot = System.IO.Path.Combine(Application.temporaryCachePath, "meridian_leadqa_" + System.Guid.NewGuid().ToString("N").Substring(0, 6));
            SaveSystem.RootOverride = saveRoot;
            // 0.6.3's sweep: this loop went red the first time it ran in one process after another class (the space leg used its whole
            // window) and green alone. A Core load does not reset the clock's statics, so the loop sets its own and logs what it found.
            savedTimeScale = Time.timeScale;
            savedCaptureDelta = Time.captureDeltaTime;
            TestContext.Out.WriteLine($"[LEADQA] M1Loop found timeScale {savedTimeScale:F2}, captureDeltaTime {savedCaptureDelta:F4}");
            Time.timeScale = 1f;
            Time.captureDeltaTime = 0f;
        }

        [TearDown]
        public void TearDown()
        {
            Time.timeScale = savedTimeScale;
            Time.captureDeltaTime = savedCaptureDelta;
            SaveSystem.RootOverride = null;
            if (System.IO.Directory.Exists(saveRoot)) System.IO.Directory.Delete(saveRoot, true);
        }

        [UnityTest, Timeout(240000)]
        public IEnumerator EarthToMarsLandingThenSaveLoad()
        {
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 20f;
            while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
            Assert.IsTrue(director.IsReady, "boot");
            for (int i = 0; i < 30; i++) yield return new WaitForFixedUpdate();

            var state = GameState.Instance;
            var transitions = Object.FindAnyObjectByType<TransitionDirector>();
            Assert.AreEqual(PlanetId.Earth, state.currentPlanet, "starts on Earth");

            // 1. Lift off from rest on Earth on full thrust (U-107, D-103: no fuel; thrust-to-weight is the only limit).
            var side = director.PlanetSide;
            var ship = side.ship;
            ship.GetComponent<ShipBoarding>().ForceAboard();
            ship.externalInput = true;
            timeout = Time.realtimeSinceStartup + 10f;
            while (!ship.AtRest && Time.realtimeSinceStartup < timeout) yield return new WaitForFixedUpdate();
            Assert.IsTrue(ship.AtRest, "ship starts at rest on the ground");
            bool escaped = false;
            ship.EscapeLineCrossed += () => escaped = true;
            ship.intent = new ShipSideIntent { thrust = 1f };
            timeout = Time.realtimeSinceStartup + 90f;
            while (!escaped && Time.realtimeSinceStartup < timeout) yield return new WaitForFixedUpdate();
            Assert.IsTrue(escaped, "crossed the Escape Line under Mk1 thrust");
            yield return WaitIdle(transitions, 10f);
            Assert.AreEqual(ViewMode.Space, state.view, "in space after launch");

            // 2. Fly to Mars on the ship's own thrust and rotation.
            var craft = director.Space.GetComponentInChildren<SpaceShip>();
            craft.externalInput = true;
            var earth = craft.world.Find("earth").Value;
            var mars = craft.world.Find("mars").Value;
            Vector2 escapePoint = earth.position + (craft.Position - earth.position).normalized * (earth.WellRadius + 20f);
            bool feltMars = false;
            // D-158 (LEAD, cycle 278): 60 → 90 s. U-149's spool and drag lengthen the Earth climb (19.1 → 20.0 s), so the craft
            // leaves at another longitude and this scripted steering can take the long way round; the assertions are unchanged.
            float spaceLegStart = Time.realtimeSinceStartup;
            float spaceLegGameStart = Time.time;
            int spaceLegFrames = 0;
            timeout = Time.realtimeSinceStartup + 90f;
            while (state.view == ViewMode.Space && !transitions.Busy && Time.realtimeSinceStartup < timeout)
            {
                spaceLegFrames++;
                Vector2 target = mars.position;
                float fromEarth = (craft.Position - earth.position).magnitude;
                if (fromEarth < earth.WellRadius) target = escapePoint;
                else if (SegmentDistance(earth.position, craft.Position, mars.position) < earth.RingRadius + 15f)
                {
                    // Go around Earth on the side the ship is already on.
                    Vector2 toShip = (craft.Position - earth.position).normalized;
                    Vector2 perp = new Vector2(-toShip.y, toShip.x);
                    if (Vector2.Dot(perp, mars.position - earth.position) < 0f) perp = -perp;
                    target = earth.position + (toShip + perp).normalized * (earth.WellRadius + 30f);
                }
                Steer(craft, target, arrive: target == mars.position);
                if (craft.InWellOf == "mars" && craft.LastPull.magnitude > 0f) feltMars = true;
                Assert.IsFalse(craft.Destroyed, "ship survived the flight");
                yield return null;
            }
            TestContext.Out.WriteLine($"[LEADQA] space leg {Time.realtimeSinceStartup - spaceLegStart:F1} s real time (window 90 s)");
            // What the leg looked like when it ended (an entry, or the window running out): enough to tell a slow clock from a craft circling.
            TestContext.Out.WriteLine($"[LEADQA] space leg end: {spaceLegFrames} frames, {Time.time - spaceLegGameStart:F1} s game time, view {state.view}, busy {transitions.Busy}, " +
                $"craft at ({craft.Position.x:F0}, {craft.Position.y:F0}) speed {craft.Velocity.magnitude:F1} heading {craft.Heading:F0}, in the well of '{craft.InWellOf}', " +
                $"{(craft.Position - mars.position).magnitude:F0} from Mars (ring {mars.RingRadius:F0}, well {mars.WellRadius:F0}), {(craft.Position - earth.position).magnitude:F0} from Earth");
            Assert.IsTrue(feltMars, "Mars gravity well pulled the ship");
            yield return WaitIdle(transitions, 15f);
            Assert.AreEqual(ViewMode.PlanetSide, state.view, "entered a planet");
            Assert.AreEqual(PlanetId.Mars, state.currentPlanet, "the planet is Mars");

            // 3. Powered landing on Mars: descend fast high up, slow to ≤ 3 m/s near the ground.
            side = director.PlanetSide;
            ship = side.ship;
            ship.externalInput = true;
            float hull0 = state.hull;
            float? touchdown = null;
            ship.TouchedDown += v => touchdown = v;
            timeout = Time.realtimeSinceStartup + 120f;
            while (touchdown == null && Time.realtimeSinceStartup < timeout)
            {
                float alt = ship.AltitudeAboveGround;
                float targetVy = -Mathf.Clamp(alt * 0.25f, 2f, 15f);
                float vy = ship.Body.linearVelocity.y;
                float accel = (targetVy - vy) * 2f + ship.Gravity; // m/s² wanted from the engine
                ship.intent = new ShipSideIntent { thrust = Mathf.Clamp01(accel / ship.Thrust) };
                yield return new WaitForFixedUpdate();
            }
            ship.intent = default;
            Assert.IsTrue(touchdown.HasValue, "touched down on Mars");
            TestContext.Out.WriteLine($"[LEADQA] Mars touchdown {touchdown.Value:F2} m/s");
            Assert.LessOrEqual(touchdown.Value, 6f, "clean landing (≤ 6 m/s)");
            Assert.AreEqual(hull0, state.hull, 1e-3f, "clean landing does no hull damage");
            for (int i = 0; i < 30; i++) yield return new WaitForFixedUpdate();

            // 4. Save → load → same state.
            var save = SaveSystem.Instance;
            save.Save();
            Assert.IsTrue(save.HasSave, "save written");
            int mark = state.thrusterMark; float hull = state.hull;
            Vector2 shipPos = ship.Body.position;
            state.thrusterMark = 3; state.hull = 1f; // scribble, so the load must restore them
            yield return save.Load();
            timeout = Time.realtimeSinceStartup + 20f;
            while ((save.Loading || director.PlanetSide == null || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
            Assert.AreEqual(PlanetId.Mars, GameState.Instance.currentPlanet, "loaded on Mars");
            Assert.AreEqual(ViewMode.PlanetSide, GameState.Instance.view);
            Assert.AreEqual(mark, GameState.Instance.thrusterMark, "thruster mark restored");
            Assert.AreEqual(hull, GameState.Instance.hull, 1e-3f, "hull restored");
            Assert.AreEqual(shipPos.x, director.PlanetSide.ship.Body.position.x, 0.5f, "ship where it landed");

            LogAssert.NoUnexpectedReceived();
        }

        /// <summary>
        /// The scripted pilot. It steers for the VELOCITY it wants, not for the target's bearing: the thrust goes along
        /// (wanted velocity − current velocity), so sideways speed is cancelled and the craft cannot settle into a circle
        /// round the target. Pointing straight at Mars at full thrust did exactly that in 0.6.3's sweep (seven turns at
        /// 73 units a second, 136 from Mars, outside its well, until the window ran out). With `arrive` the wanted speed
        /// falls with the distance, so the craft comes into the well slowly enough to be caught by it.
        /// </summary>
        static void Steer(SpaceShip craft, Vector2 target, bool arrive = false)
        {
            const float Cruise = 80f, ArriveGain = 0.8f, ArriveFloor = 12f;
            Vector2 to = target - craft.Position;
            float dist = to.magnitude;
            Vector2 dir = dist > 1e-3f ? to / dist : Vector2.right;
            float wantSpeed = arrive ? Mathf.Min(Cruise, Mathf.Max(ArriveFloor, dist * ArriveGain)) : Cruise;
            Vector2 need = dir * wantSpeed - craft.Velocity;
            bool onIt = need.sqrMagnitude < 4f; // within 2 units a second of the wanted velocity: coast, nose on the target
            Vector2 aim = onIt ? to : need;
            float desired = Mathf.Atan2(aim.y, aim.x) * Mathf.Rad2Deg;
            float delta = Mathf.DeltaAngle(craft.Heading, desired);
            craft.intent = new ShipIntent
            {
                rotate = Mathf.Clamp(delta / 20f, -1f, 1f),
                thrust = !onIt && Mathf.Abs(delta) < 30f ? 1f : 0f,
            };
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
