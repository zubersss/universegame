using System;
using System.Collections;
using System.IO;
using Meridian.Core;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>
    /// Boots Core (Earth) and saves what the side camera sees at 1920×1080 to
    /// logs/capture_&lt;name&gt;.png. Run by tools/unity_capture.ps1 (sets MERIDIAN_CAPTURE); skipped otherwise.
    /// </summary>
    public class SceneCapture
    {
        public const string Variable = "MERIDIAN_CAPTURE";
        const string CorePath = "Assets/_Game/Scenes/Core.unity";

        /// <summary>Top-down view at Earth: saves a frame and asserts ≤ 80 draw calls (Bible §11.1).</summary>
        [UnityTest]
        public IEnumerator CaptureSpace()
        {
            var name = Environment.GetEnvironmentVariable(Variable);
            if (string.IsNullOrEmpty(name)) Assert.Ignore($"Set {Variable} (tools/unity_capture.ps1).");
            if (SystemInfo.graphicsDeviceType == UnityEngine.Rendering.GraphicsDeviceType.Null)
                Assert.Fail("No graphics device: run without -nographics.");
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = UnityEngine.Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 20f;
            while (!director.IsReady && Time.realtimeSinceStartup < timeout) yield return null;
            director.SetView(ViewMode.Space);
            var cam = director.Space.GetComponentInChildren<Camera>();
            cam.orthographicSize = 260f; // Earth, Luna, Mars and both wells in one frame
            for (int i = 0; i < 30; i++) yield return null; // textures load

            using (var draws = Unity.Profiling.ProfilerRecorder.StartNew(Unity.Profiling.ProfilerCategory.Render, "Draw Calls Count"))
            {
                // Batch mode doesn't render cameras on its own: render the view explicitly each frame.
                var rt = new RenderTexture(1920, 1080, 24, RenderTextureFormat.ARGB32);
                cam.targetTexture = rt;
                long worst = 0;
                for (int i = 0; i < 10; i++)
                {
                    cam.Render();
                    yield return null;
                    worst = Math.Max(worst, draws.LastValue);
                }
                cam.targetTexture = null;
                rt.Release();
                TestContext.Out.WriteLine($"[MERIDIAN] Space draw calls: {worst} (recorder valid {draws.Valid})");
                Assert.IsTrue(draws.Valid, "draw call recorder available");
                Assert.Greater(worst, 0, "the recorder actually saw the frame");
                Assert.LessOrEqual(worst, 80, "≤ 80 draw calls top-down");
            }
            yield return Save(cam, name);
        }

        static IEnumerator Save(Camera cam, string name)
        {
            var rt = new RenderTexture(1920, 1080, 24, RenderTextureFormat.ARGB32);
            cam.targetTexture = rt;
            cam.Render();
            var prev = RenderTexture.active;
            RenderTexture.active = rt;
            var tex = new Texture2D(1920, 1080, TextureFormat.RGB24, false);
            tex.ReadPixels(new Rect(0, 0, 1920, 1080), 0, 0);
            tex.Apply();
            RenderTexture.active = prev;
            cam.targetTexture = null;
            Directory.CreateDirectory("logs");
            var output = $"logs/capture_{name}.png";
            File.WriteAllBytes(output, tex.EncodeToPNG());
            TestContext.Out.WriteLine($"[MERIDIAN] CAPTURE OK: {output}");
            UnityEngine.Object.Destroy(tex);
            rt.Release();
            yield return null;
        }

        [UnityTest]
        public IEnumerator CaptureEarthSurface()
        {
            var name = Environment.GetEnvironmentVariable(Variable);
            if (string.IsNullOrEmpty(name)) Assert.Ignore($"Set {Variable} (tools/unity_capture.ps1).");
            if (SystemInfo.graphicsDeviceType == UnityEngine.Rendering.GraphicsDeviceType.Null)
                Assert.Fail("No graphics device: run without -nographics.");

#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#else
            yield return SceneManager.LoadSceneAsync("Core", LoadSceneMode.Single);
#endif
            var director = UnityEngine.Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 20f;
            while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout)
                yield return null;
            Assert.IsTrue(director.PlanetSide.terrain.IsSettled, "terrain settled");

            // Give the player time to be released onto the loaded ground and come to rest.
            for (int i = 0; i < 60; i++) yield return new WaitForFixedUpdate();
            var player = director.PlanetSide.player;
            if (player != null)
                TestContext.Out.WriteLine($"[MERIDIAN] player grounded {player.Grounded} at {player.Body.position}, health {player.Vitals?.health}");
            var cam = director.PlanetSide.sideCamera;
            var follow = cam.GetComponent<Meridian.Player.CameraFollow>();
            if (follow != null) follow.enabled = false;
            Assert.AreEqual(9f, cam.orthographicSize, "default ortho size (Bible §5.1)");
            // Look a little below the surface so the shot shows surface, soil and stone seams.
            cam.transform.position += new Vector3(0f, -5f, 0f);
            for (int i = 0; i < 5; i++) yield return null;

            var rt = new RenderTexture(1920, 1080, 24, RenderTextureFormat.ARGB32);
            cam.targetTexture = rt;
            cam.Render();
            var prev = RenderTexture.active;
            RenderTexture.active = rt;
            var tex = new Texture2D(1920, 1080, TextureFormat.RGB24, false);
            tex.ReadPixels(new Rect(0, 0, 1920, 1080), 0, 0);
            tex.Apply();
            RenderTexture.active = prev;
            cam.targetTexture = null;

            Directory.CreateDirectory("logs");
            var output = $"logs/capture_{name}.png";
            File.WriteAllBytes(output, tex.EncodeToPNG());
            TestContext.Out.WriteLine($"[MERIDIAN] CAPTURE OK: {output}");
            UnityEngine.Object.Destroy(tex);
            rt.Release();
        }
    }
}
