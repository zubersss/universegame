using System.Collections;
using System.Collections.Generic;
using Meridian.CameraRig;
using Meridian.Core;
using Meridian.Planets;
using Meridian.Player;
using Meridian.Ship;
using Meridian.Transitions;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>
    /// U-148 (D-158 (1), (2)): the climb out of the atmosphere is smooth and the ship has its own frame. On Earth and on Mars the Pilgrim is
    /// boarded on its pad (the frame eases to the 30 m ship frame, the hull low in it with sky ahead), then flies pad → Escape Line under scripted
    /// full thrust at a steady 60 fps (Time.captureDeltaTime) against the 50 Hz physics step. A probe that runs after the camera records, on every
    /// rendered frame, the hull's drawn centre in 1080p screen space against the camera's unshaken centre; after the first second of the climb its
    /// frame-to-frame second difference stays ≤ 2 px, the hull stays inside the middle band and the frame follows the speed (30 → 45 m). The same
    /// run reports the judder the old follow carried: the drawn hull against the 50 Hz Body pose in the old 16.875 m frame.
    /// </summary>
    public class ClimbSmoothPlayTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";
        /// <summary>The acceptance bound (U-148): the hull's screen-space second difference per rendered frame, px at 1080p.</summary>
        public const float MaxSecondDifferencePx = 2f;

        /// <summary>Records after every LateUpdate (the camera's included): the hull as drawn, the 50 Hz Body pose, the camera's unshaken centre and frame.</summary>
        [DefaultExecutionOrder(32000)]
        sealed class HullProbe : MonoBehaviour
        {
            public SideShip ship;
            public Camera cam;
            public CameraFollow follow;
            public bool recording;
            public readonly List<Vector2> drawn = new List<Vector2>(4096), stepped = new List<Vector2>(4096), centre = new List<Vector2>(4096);
            public readonly List<float> frame = new List<float>(4096), speed = new List<float>(4096);

            void LateUpdate()
            {
                if (!recording || ship == null || cam == null) return;
                float lift = SideShip.Height * 0.5f - SideShip.SkidDrop;
                var t = ship.transform;
                drawn.Add((Vector2)t.position + (Vector2)t.up * lift);
                stepped.Add(ship.Body.position + RocketFlight.UpAxis(ship.Body.rotation) * lift);
                var shake = follow != null ? follow.Stage.Shake : Vector2.zero;
                centre.Add((Vector2)cam.transform.position - shake);
                frame.Add(cam.orthographic ? cam.orthographicSize * 2f : SideView.HalfHeight(cam) * 2f);
                speed.Add(ship.Body.linearVelocity.magnitude);
            }
        }

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

        [UnityTest, Timeout(300000)]
        public IEnumerator EarthClimbIsSmoothInTheShipFrame()
        {
            SceneDirector director = null;
            yield return Boot(d => director = d);
            yield return Climb(director, PlanetId.Earth);
        }

        [UnityTest, Timeout(300000)]
        public IEnumerator MarsClimbIsSmoothInTheShipFrame()
        {
            SceneDirector director = null;
            yield return Boot(d => director = d);
            yield return director.LoadPlanetSide(GameState.Instance.catalog.Get(PlanetId.Mars));
            float timeout = Time.realtimeSinceStartup + 30f;
            while (!director.PlanetSide.terrain.IsSettled && Time.realtimeSinceStartup < timeout) yield return null;
            for (int i = 0; i < 30; i++) yield return new WaitForFixedUpdate();
            yield return Climb(director, PlanetId.Mars);
        }

        static IEnumerator Climb(SceneDirector director, PlanetId planet)
        {
            var side = director.PlanetSide;
            Assert.AreEqual(planet, side.Config.id);
            if (side.hazards != null) side.hazards.enabled = false;
            var ship = side.ship;
            var cam = side.sideCamera;
            var follow = cam.GetComponent<CameraFollow>();
            Assert.NotNull(follow, "CameraFollow on the side camera");
            var transitions = Object.FindAnyObjectByType<TransitionDirector>();
            var probe = new GameObject("U148HullProbe").AddComponent<HullProbe>();
            probe.ship = ship; probe.cam = cam; probe.follow = follow;
            float savedCapture = Time.captureDeltaTime;
            try
            {
                Time.captureDeltaTime = 1f / 60f; // a steady 60 fps against the 50 Hz step: the beat that showed the judder
                ship.externalInput = true;
                ship.intent = default;
                ship.GetComponent<ShipBoarding>().ForceAboard();

                // ---- On the pad: the frame eases from the walking frame to the 30 m ship frame within ~1 s, the hull low in it. ----
                for (int i = 0; i < 90; i++) yield return null; // 1.5 s
                float padFrame = follow.Stage.Frame;
                float lift = SideShip.Height * 0.5f - SideShip.SkidDrop;
                var hull = (Vector2)ship.transform.position + (Vector2)ship.transform.up * lift;
                float offsetY = follow.Stage.Y - hull.y;
                TestContext.Out.WriteLine($"[MERIDIAN] u148 {planet} pad: frame {padFrame:F2} m, camera {offsetY:F2} m over the hull's centre, easing {follow.Stage.FrameEasing}");
                Assert.AreEqual(StageCamera.ShipFrame, padFrame, 0.5f, "the 30 m ship frame on the pad, 1.5 s after boarding");
                Assert.Greater(offsetY, 0f, "on the pad the hull sits low in the frame, sky ahead of it");

                // ---- Pad → Escape Line under full thrust, every rendered frame recorded after the camera. ----
                ship.intent.thrust = 1f;
                probe.recording = true;
                float line = side.Config.EscapeLineY;
                int frames = 0;
                while (frames < 60 * 180)
                {
                    yield return null;
                    frames++;
                    if (transitions != null && transitions.Busy) break;
                    if (ship.Body.position.y >= line) break;
                }
                probe.recording = false;
                int n = probe.drawn.Count;
                Assert.Greater(n, 120, $"the climb ran ({n} frames recorded)");
                Assert.GreaterOrEqual(probe.drawn[n - 1].y, line - 30f, $"the climb reached the Escape Line ({probe.drawn[n - 1].y:F0} of {line:F0})");

                // The hull's screen position (1080p px) against the unshaken camera, and the old follow's judder for the report.
                float worst = 0f, worstOld = 0f, worstBand = 0f;
                int worstAt = -1;
                var p = new Vector2[n];
                var old = new Vector2[n];
                for (int k = 0; k < n; k++)
                {
                    float px = 1080f / probe.frame[k];
                    p[k] = (probe.drawn[k] - probe.centre[k]) * px;
                    old[k] = (probe.drawn[k] - probe.stepped[k]) * (1080f / Meridian.View2D.SheetClock.FrameHeight);
                    float band = Mathf.Max(Mathf.Abs(probe.drawn[k].x - probe.centre[k].x), Mathf.Abs(probe.drawn[k].y - probe.centre[k].y)) / probe.frame[k];
                    worstBand = Mathf.Max(worstBand, band);
                }
                for (int k = 62; k < n; k++) // after the first second of the climb
                {
                    float d2 = (p[k] - 2f * p[k - 1] + p[k - 2]).magnitude;
                    if (d2 > worst) { worst = d2; worstAt = k; }
                    worstOld = Mathf.Max(worstOld, (old[k] - 2f * old[k - 1] + old[k - 2]).magnitude);
                }
                float topSpeed = 0f; foreach (var s in probe.speed) topSpeed = Mathf.Max(topSpeed, s);
                float endFrame = probe.frame[n - 1];
                TestContext.Out.WriteLine($"[MERIDIAN] u148 {planet} climb: {n} frames, {n / 60f:F1} s to {probe.drawn[n - 1].y:F0} (line {line:F0}); hull second difference max {worst:F3} px at frame {worstAt} (bound {MaxSecondDifferencePx}); the old 50 Hz follow's judder {worstOld:F2} px at 16.875 m; top speed {topSpeed:F1} m/s; frame {probe.frame[0]:F1} → {endFrame:F1} m (goal {StageCamera.ShipFrameFor(StageCamera.ShipFrame, probe.speed[n - 1]):F1}); hull within {worstBand * 100f:F1} % of the frame from the centre");

                Assert.LessOrEqual(worst, MaxSecondDifferencePx, $"the hull's screen-space second difference ≤ {MaxSecondDifferencePx} px after the first second (worst at frame {worstAt})");
                Assert.LessOrEqual(worstBand, StageCamera.MiddleBand * 0.5f + 0.01f, "the hull stays inside the middle band");
                for (int k = 0; k < n; k++)
                    Assert.IsTrue(probe.frame[k] >= StageCamera.ShipFrameMin - 0.01f && probe.frame[k] <= StageCamera.ShipFrameMax + 0.01f, $"frame {k}: {probe.frame[k]:F2} m inside the ship range");
                // The frame trails its speed goal by the 0.8 s SmoothDamp while the hull accelerates: at least half way there, never past it.
                float goal = StageCamera.ShipFrameFor(StageCamera.ShipFrame, probe.speed[n - 1]);
                Assert.GreaterOrEqual(endFrame, StageCamera.ShipFrame + 0.5f * (goal - StageCamera.ShipFrame) - 0.01f, $"the frame widens with speed ({endFrame:F1} m toward {goal:F1})");
                Assert.LessOrEqual(endFrame, goal + 0.5f, "the frame never overshoots its speed goal");
                LogAssert.NoUnexpectedReceived();
            }
            finally
            {
                Time.captureDeltaTime = savedCapture;
                if (probe != null) Object.Destroy(probe.gameObject);
            }
        }
    }
}
