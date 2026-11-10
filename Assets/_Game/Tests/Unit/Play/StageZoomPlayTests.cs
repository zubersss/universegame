using System.Collections;
using Meridian.CameraRig;
using Meridian.Core;
using Meridian.Player;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>
    /// U-213 (3) (D-202 (3)), PlayMode on the cartoon path: with the close camera's flag on, the surveyor on foot at the camp is framed
    /// at 96 px a metre (1080 px = 11.25 m); at the floor of a 10 m shaft the frame eases back to the shipped 64 (16.875 m) in about
    /// a second with no cut, and closes in again at the surface; the reticle's marks keep their size on the screen; with the flag off
    /// the frame is the shipped one everywhere.
    /// </summary>
    public class StageZoomPlayTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";
        const float Shipped = 1080f / 64f, Close = 1080f / 96f;

        [UnityTest, Timeout(300000)]
        public IEnumerator TheCloseCameraAtTheSurfaceEasesToTheShippedFrameUnderground()
        {
            bool wasCartoon = Meridian.View2D.CartoonStage.Enabled, wasZoom = StageZoom.Enabled;
            float wasPpm = StageZoom.SurfacePxPerMetre;
            Meridian.View2D.CartoonStage.Enabled = true;
            StageZoom.Enabled = false;
            Meridian.Rig.RigTools rig = null; Transform owner = null;
            PlayerController player = null;
            try
            {
#if UNITY_EDITOR
                yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                    CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
                var director = Object.FindAnyObjectByType<SceneDirector>();
                float timeout = Time.realtimeSinceStartup + 30f;
                while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
                var side = director.PlanetSide;
                var t = side.terrain;
                Assert.IsTrue(t.SmoothGround, "Earth on the smooth ground");
                if (side.hazards != null) side.hazards.enabled = false;
                side.creatures.autoSpawn = false; side.creatures.DespawnAll();
                var cam = side.sideCamera;
                var follow = cam.GetComponent<CameraFollow>();
                Assert.NotNull(follow); Assert.IsTrue(follow.Cartoon, "the cartoon frame");
                player = side.player;
                player.externalInput = true; player.intent = default;
                var input = player.GetComponent<PlayerRigInput>();
                rig = side.rig; owner = rig.owner;
                var body = player.Body;

                IEnumerator Stand(Vector2 feet)
                {
                    body.position = feet; player.transform.position = feet; body.linearVelocity = Vector2.zero;
                    yield return null;
                    float until = Time.realtimeSinceStartup + 20f;
                    while (!t.IsSettled && Time.realtimeSinceStartup < until) yield return null;
                    for (int k = 0; k < 40; k++) yield return new WaitForFixedUpdate();
                }
                // follows the frame for `seconds`: its least and greatest height, the largest change in one frame, when it came within 2 % of `goal`
                float lo = 0f, hi = 0f, worst = 0f, reached = -1f;
                IEnumerator Watch(float seconds, float goal, float from)
                {
                    lo = hi = follow.Stage.Frame; worst = 0f; reached = -1f;
                    float last = follow.Stage.Frame, clock = 0f;
                    while (clock < seconds)
                    {
                        yield return null;
                        clock += Time.deltaTime;
                        float f = follow.Stage.Frame;
                        worst = Mathf.Max(worst, Mathf.Abs(f - last)); last = f;
                        lo = Mathf.Min(lo, f); hi = Mathf.Max(hi, f);
                        if (reached < 0f && Mathf.Abs(f - goal) <= 0.02f * Mathf.Abs(goal - from)) reached = clock;
                    }
                }

                // the flag off: the shipped frame at the camp
                float sx = side.spawnX + 14.5f;
                yield return Stand(new Vector2(sx, t.SurfaceAt(sx) + 0.05f));
                follow.SnapToTarget();
                for (int k = 0; k < 30; k++) yield return null;
                Assert.AreEqual(Shipped, follow.Stage.Frame, 0.01f, "the flag off: 16.875 m, 64 px a metre");
                Assert.AreEqual(Shipped * 0.5f, cam.orthographicSize, 0.01f);
                Assert.IsFalse(follow.Underground);

                // the flag on at the surface: the frame closes in to 96 px a metre over about a second
                StageZoom.Enabled = true; StageZoom.SurfacePxPerMetre = 96f;
                yield return Watch(2.5f, Close, Shipped);
                TestContext.Out.WriteLine($"[MERIDIAN] u213 at the camp: frame {follow.Stage.Frame:0.000} m ({1080f / follow.Stage.Frame:0.0} px a metre), within 2 % after {reached:0.00} s, the largest change in a frame {worst:0.000} m; depth {follow.DepthNow:0.00} m, underground {follow.Underground}");
                Assert.AreEqual(Close, follow.Stage.Frame, 0.02f, "11.25 m: 96 px a metre on foot at the surface");
                Assert.AreEqual(Close * 0.5f, cam.orthographicSize, 0.02f, "the camera draws it");
                Assert.That(reached, Is.InRange(0.6f, 1.6f), "about a second");
                Assert.Less(worst, 0.45f, "never a cut (a frame of this batch run may be long: under half a metre in any one)");
                Assert.IsFalse(follow.Underground);
                // the frame's bottom keeps the ground's share: 2 m under the stage floor at 96
                float floorY = follow.FloorUnder(body.position);
                Assert.AreEqual(floorY - StageCamera.FloorBelow * (2f / 3f) + Close * 0.5f, cam.transform.position.y, 0.08f, "the frame's bottom 2 m under the floor: the ground's share of the frame as shipped");
                // the reticle's marks keep their size on the screen
                input.module = Meridian.Rig.RigModule.Beam;
                input.AimAt(body.position + new Vector2(1.1f, -0.3f));
                for (int k = 0; k < 30; k++) yield return null;
                var view = input.ToolView;
                Assert.AreEqual(2f / 3f, view.MarkScale, 0.01f, "the marks' own size follows the close camera");
                if (view.Bracket(0) != null && view.Bracket(0).enabled) Assert.AreEqual(2f / 3f, view.Bracket(0).transform.localScale.x, 0.01f, "a bracket is as long on the screen as at 64 px a metre");

                // a 10 m shaft beside the camp, the surveyor on its floor: the frame eases out to the shipped 64 with no cut
                float ax = sx + 5f, top = t.SurfaceAt(ax), bottom = Mathf.Floor(top) - 10f;
                rig.owner = null; // the staging's reach
                int bored = 0;
                for (float y = bottom + 0.7f; y <= top + 0.5f + 1e-3f; y += 0.5f)
                    foreach (float dx in new[] { -1.1f, -0.55f, 0f, 0.55f, 1.1f })
                        if (rig.Dig(new Vector2(ax + dx, y))) bored++;
                rig.owner = owner;
                yield return new WaitForFixedUpdate();
                Assert.Greater(bored, 20, "the shaft is dug");
                body.position = new Vector2(ax, bottom + 1.2f); player.transform.position = body.position; body.linearVelocity = Vector2.zero;
                yield return Watch(3f, Shipped, Close);
                TestContext.Out.WriteLine($"[MERIDIAN] u213 at the shaft's floor: depth {follow.DepthNow:0.00} m, underground {follow.Underground}, roofed {follow.Roofed(body.position)}; frame {follow.Stage.Frame:0.000} m, within 2 % after {reached:0.00} s, the largest change in a frame {worst:0.000} m, least {lo:0.000}");
                Assert.IsTrue(follow.Underground, "9 m down an open shaft: underground by depth");
                Assert.Greater(follow.DepthNow, 8f);
                Assert.AreEqual(Shipped, follow.Stage.Frame, 0.02f, "the shipped 64 px a metre underground");
                Assert.That(reached, Is.InRange(0.6f, 1.8f), "about a second after the surveyor is under");
                Assert.Less(worst, 0.45f, "never a cut");
                Assert.GreaterOrEqual(lo, Close - 0.02f, "the frame only opened");
                Assert.AreEqual(1f, view.MarkScale, 0.01f, "the marks at their shipped size underground");

                // back at the surface it closes in again
                yield return Stand(new Vector2(sx, t.SurfaceAt(sx) + 0.05f));
                yield return Watch(2.5f, Close, Shipped);
                Assert.IsFalse(follow.Underground);
                Assert.AreEqual(Close, follow.Stage.Frame, 0.02f, "96 px a metre again at the surface");

                // the closer trial: 128 px a metre
                StageZoom.SurfacePxPerMetre = 128f;
                yield return Watch(2.5f, 1080f / 128f, Close);
                Assert.AreEqual(1080f / 128f, follow.Stage.Frame, 0.02f, "8.4375 m: 128 px a metre");

                // the flag off again: the shipped frame, eased
                StageZoom.Enabled = false;
                yield return Watch(2.5f, Shipped, 1080f / 128f);
                Assert.AreEqual(Shipped, follow.Stage.Frame, 0.02f, "the flag off: the shipped frame");
                Assert.AreEqual(1f, view.MarkScale, 1e-6f);
                LogAssert.NoUnexpectedReceived();
            }
            finally
            {
                StageZoom.Enabled = wasZoom; StageZoom.SurfacePxPerMetre = wasPpm;
                Meridian.View2D.CartoonStage.Enabled = wasCartoon;
                if (rig != null) rig.owner = owner;
                if (player != null) { player.externalInput = false; player.intent = default; }
            }
        }
    }
}
