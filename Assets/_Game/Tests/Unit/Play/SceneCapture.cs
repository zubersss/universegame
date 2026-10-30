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

            var cam = director.PlanetSide.sideCamera;
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
