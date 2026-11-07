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
    /// <summary>U-087 (PlayMode): on Earth at the camp a jump leaves the camera's height unchanged; the camera never rotates.</summary>
    public class StageCameraPlayTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";

        [UnityTest]
        public IEnumerator AJumpAtTheCampLeavesTheCameraHeightUnchanged()
        {
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
            var side = director.PlanetSide;
            var cam = side.sideCamera;
            var follow = cam.GetComponent<CameraFollow>();
            Assert.NotNull(follow, "CameraFollow on the side camera");
            Assert.IsTrue(follow.stage && follow.player != null && follow.terrain != null, "the stage camera is wired");
            for (int i = 0; i < 150; i++) yield return new WaitForFixedUpdate(); // the floor smoothing settles
            var player = side.player;
            Assert.IsTrue(player.Grounded, "standing at the camp");
            float y0 = cam.transform.position.y;
            float frame0 = follow.Stage.Frame;
            Assert.AreEqual(StageCamera.DefaultFrame, frame0, 0.01f, "18 m frame");
            Assert.AreEqual(follow.FloorUnder(player.Body.position) - StageCamera.FloorBelow + frame0 * 0.5f, y0, 0.05f, "frame bottom 3 m below the stage floor");

            player.PressJump();
            float peak = player.Body.position.y, start = player.Body.position.y, travel = 0f;
            float until = Time.realtimeSinceStartup + 4f;
            while (player.Grounded && Time.realtimeSinceStartup < until) yield return new WaitForFixedUpdate();
            Assert.IsFalse(player.Grounded, "took off");
            while (!player.Grounded && Time.realtimeSinceStartup < until)
            {
                yield return null;
                peak = Mathf.Max(peak, player.Body.position.y);
                travel = Mathf.Max(travel, Mathf.Abs(cam.transform.position.y - y0));
            }
            for (int i = 0; i < 10; i++) { yield return null; travel = Mathf.Max(travel, Mathf.Abs(cam.transform.position.y - y0)); }
            TestContext.Out.WriteLine($"[MERIDIAN] stage camera: jump {peak - start:F2} m, camera y moved {travel:F3} m, rotation {cam.transform.rotation.eulerAngles}");
            Assert.Greater(peak - start, 1.5f, "a real jump");
            Assert.AreEqual(0f, travel, 0.01f, "camera y unchanged by the jump");
            Assert.AreEqual(Quaternion.identity, cam.transform.rotation, "the camera never rotates");
            LogAssert.NoUnexpectedReceived();
        }
    }
}
