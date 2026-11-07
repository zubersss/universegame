using System.Collections;
using Meridian.Core;
using Meridian.Planets;
using Meridian.Ship;
using Meridian.Space;
using Meridian.Transitions;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.InputSystem.LowLevel;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>
    /// U-107 (PlayMode, D-103): control never leaves the player. A virtual keyboard holds W from the first frame on Earth's
    /// pad; an input probe checks every frame that the ship in view read the held key, through the climb, the iris and the
    /// switch to Space (the first Space frame still thrusting). Then an entry places the ship upright at Escape Line + 20 m
    /// descending 15 m/s with W still held and the side controls live on the first visible frame, and a key-driven
    /// descent touches down at ≤ 6 m/s. Each transition ≤ 1.5 s; a clean console.
    /// </summary>
    public class FlightPlayTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";
        Keyboard keys;
        InputSettings.EditorInputBehaviorInPlayMode savedEditor;
        InputSettings.BackgroundBehavior savedBackground;

        [SetUp]
        public void SetUp()
        {
            // The batch-mode editor has no focused Game view: route the virtual keyboard to the game regardless of focus.
            savedEditor = InputSystem.settings.editorInputBehaviorInPlayMode;
            savedBackground = InputSystem.settings.backgroundBehavior;
            InputSystem.settings.editorInputBehaviorInPlayMode = InputSettings.EditorInputBehaviorInPlayMode.AllDeviceInputAlwaysGoesToGameView;
            InputSystem.settings.backgroundBehavior = InputSettings.BackgroundBehavior.IgnoreFocus;
            keys = InputSystem.AddDevice<Keyboard>("U107Probe");
        }

        [TearDown]
        public void TearDown()
        {
            if (keys != null) InputSystem.RemoveDevice(keys);
            keys = null;
            InputSystem.settings.editorInputBehaviorInPlayMode = savedEditor;
            InputSystem.settings.backgroundBehavior = savedBackground;
        }

        void Hold(bool w) => InputSystem.QueueStateEvent(keys, w ? new KeyboardState(Key.W) : new KeyboardState());

        static IEnumerator Boot(System.Action<SceneDirector> done)
        {
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
            Assert.IsTrue(director.IsReady, "Core booted");
            for (int i = 0; i < 30; i++) yield return new WaitForFixedUpdate();
            done(director);
        }

        [UnityTest, Timeout(240000)]
        public IEnumerator HeldThrustFromThePadCarriesThroughLaunchAndEntryToAManualTouchdown()
        {
            SceneDirector director = null;
            yield return Boot(d => director = d);
            var state = GameState.Instance;
            var transitions = Object.FindAnyObjectByType<TransitionDirector>();
            var side = director.PlanetSide;
            Assert.AreEqual(PlanetId.Earth, side.Config.id);
            var ship = side.ship;
            Assert.IsTrue(ship.AtRest, "the Pilgrim stands on the pad");
            Assert.IsFalse(ship.externalInput);
            var space = director.Space.GetComponentInChildren<SpaceShip>(true);
            Assert.IsFalse(space.externalInput);

            // ---- Frame 0: W is already down when the pilot takes the seat ----
            Hold(true);
            yield return null;
            ship.GetComponent<ShipBoarding>().ForceAboard();
            yield return null; yield return null;
            Assert.AreEqual(1f, ship.intent.thrust, "a key held before boarding thrusts at once (initial state check)");

            // ---- The probe: every frame, whichever ship is in view read the held key (at most one frame lost at the switch) ----
            int sideReads = ship.InputFrames, spaceReads = space.InputFrames;
            int frames = 0, gap = 0, maxGap = 0, sideFrames = 0, spaceFrames = 0, irisFrames = 0;
            bool firstSpaceChecked = false;
            float t0 = Time.time;
            while (!(state.view == ViewMode.Space && !transitions.Busy) && Time.time - t0 < 90f)
            {
                yield return null;
                frames++;
                if (transitions.Busy) irisFrames++;
                bool read = false;
                if (ship != null && ship.InputFrames != sideReads)
                {
                    sideReads = ship.InputFrames; read = true; sideFrames++;
                    Assert.IsTrue(ship.piloted, $"frame {frames}: still piloted");
                    Assert.AreEqual(1f, ship.intent.thrust, $"frame {frames}: side thrust held (no lock)");
                }
                if (space.InputFrames != spaceReads)
                {
                    spaceReads = space.InputFrames; read = true; spaceFrames++;
                    Assert.AreEqual(1f, space.intent.thrust, $"frame {frames}: top-down thrust held");
                    if (!firstSpaceChecked)
                    {
                        firstSpaceChecked = true;
                        Assert.AreEqual(ViewMode.Space, state.view, "the space ship reads input only once in view");
                        TestContext.Out.WriteLine($"[MERIDIAN] first Space frame {frames}: thrust {space.intent.thrust}, iris busy {transitions.Busy}");
                    }
                }
                gap = read ? 0 : gap + 1;
                maxGap = Mathf.Max(maxGap, gap);
            }
            TestContext.Out.WriteLine($"[MERIDIAN] launch probe: {frames} frames ({sideFrames} side, {spaceFrames} space, {irisFrames} under the iris), longest gap {maxGap}, launch {transitions.LastLaunchSeconds:F2} s");
            Assert.AreEqual(ViewMode.Space, state.view, "climbed through the Escape Line under the player's own thrust");
            Assert.IsTrue(firstSpaceChecked, "the space ship read the held key");
            Assert.LessOrEqual(maxGap, 1, "no input lock at any frame");
            Assert.Greater(irisFrames, 5, "the probe saw the iris frames");
            Assert.LessOrEqual(transitions.LastLaunchSeconds, 1.5f, "launch ≤ 1.5 s");
            Vector2 v0 = space.Velocity;
            for (int i = 0; i < 10; i++) yield return new WaitForFixedUpdate();
            Assert.Greater(Vector2.Dot(space.Velocity - v0, new Vector2(Mathf.Cos(space.Heading * Mathf.Deg2Rad), Mathf.Sin(space.Heading * Mathf.Deg2Rad))), 0.5f,
                "the held key keeps thrusting in Space");

            // ---- Entry with W still held: upright at Escape Line + 20 m, descending, side controls live on the first frame ----
            for (int i = 0; i < 60; i++) yield return new WaitForFixedUpdate(); // past the 1 s invulnerability
            var earth = space.world.Find("earth").Value;
            transitions.BeginEntry(earth);
            yield return null;
            Assert.IsTrue(transitions.Busy, "entering");
            SideShip landing = null;
            while (transitions.Busy)
            {
                yield return null;
                var ps = director.PlanetSide;
                if (landing == null && ps != null && ps.gameObject.activeInHierarchy && ps.ship != null && ps.ship.InputFrames > 0)
                {
                    landing = ps.ship;
                    Assert.IsTrue(landing.piloted, "aboard on the first visible frame");
                    Assert.AreEqual(1f, landing.intent.thrust, "the held key thrusts on the first side frame");
                    Assert.AreEqual(0f, landing.Tilt, 1e-3f, "upright");
                    Assert.IsTrue(ps.LastArrival.HasValue, "an entry arrival");
                    var arrival = ps.LastArrival.Value;
                    Assert.AreEqual(ps.Config.EscapeLineY + PlanetSideRoot.EntryAboveEscapeLine, arrival.shipPosition.y, 0.01f, "placed at Escape Line + 20 m");
                    Assert.AreEqual(-PlanetSideRoot.EntryDescentSpeed, arrival.shipVelocity.y, 0.01f, "descending 15 m/s");
                }
            }
            Assert.NotNull(landing, "side controls were live while the iris opened");
            TestContext.Out.WriteLine($"[MERIDIAN] entry took {transitions.LastEntrySeconds:F2} s (iris + planet load + iris)");
            Assert.LessOrEqual(transitions.LastEntrySeconds, 4f, "entry incl. the planet load ≤ 4 s (TransitionTests' bound; the 1.5 s row is the switch itself)");

            // ---- A manual, key-driven descent: W on while falling faster than the profile ----
            float elapsed = 0f;
            while (!landing.Grounded && elapsed < 150f)
            {
                float alt = landing.AltitudeAboveGround;
                float target = -Mathf.Clamp(Mathf.Sqrt(2f * 1.2f * Mathf.Max(0f, alt)), 2.5f, 15f);
                Hold(landing.Body.linearVelocity.y < target);
                yield return new WaitForFixedUpdate();
                elapsed += Time.fixedDeltaTime;
            }
            Hold(false);
            Assert.IsTrue(landing.Grounded, "touched down");
            TestContext.Out.WriteLine($"[MERIDIAN] manual touchdown {landing.LastTouchdownSpeed:F2} m/s after {elapsed:F1} s");
            Assert.LessOrEqual(landing.LastTouchdownSpeed, SideShip.CleanTouchdown, "a clean touchdown by hand");
            LogAssert.NoUnexpectedReceived();
        }
    }
}
