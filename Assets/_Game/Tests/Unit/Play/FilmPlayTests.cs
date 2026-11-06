using System.Collections;
using Meridian.Core;
using Meridian.Rendering;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>
    /// U-095 (PlayMode, Earth): the Film effects toggle removes the pass (nothing is recorded while it is off), and the
    /// pass costs ≤ 0.6 ms of GPU time at 1080p (FrameTimingManager: GPU frame time with the pass on minus off).
    /// </summary>
    public class FilmPlayTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";
        const float GpuBudgetMs = 0.6f;
        bool filmBefore;

        [SetUp] public void Keep() => filmBefore = GameSettings.FilmEffects;
        [TearDown] public void Restore() => GameSettings.FilmEffects = filmBefore;

        IEnumerator Boot()
        {
            if (SystemInfo.graphicsDeviceType == UnityEngine.Rendering.GraphicsDeviceType.Null)
                Assert.Ignore("No graphics device: the film pass is skipped under -nographics; run with a graphics device (tools/unity_test.ps1 -Graphics).");
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
            for (int i = 0; i < 30; i++) yield return null;
        }

        /// <summary>Batch mode renders the game view only on demand: the tests render the side camera themselves (as the captures do).</summary>
        IEnumerator Render(Camera cam, int frames)
        {
            for (int i = 0; i < frames; i++) { cam.Render(); yield return null; }
        }

        [UnityTest]
        public IEnumerator TheToggleRemovesThePass()
        {
            yield return Boot();
            var cam = Object.FindAnyObjectByType<SceneDirector>().PlanetSide.sideCamera;
            var rt = new RenderTexture(1920, 1080, 24, RenderTextureFormat.ARGB32);
            cam.targetTexture = rt;
            try
            {
                GameSettings.FilmEffects = true;
                yield return Render(cam, 3);
                int a = FilmFeature.FramesRendered;
                yield return Render(cam, 10);
                Assert.GreaterOrEqual(FilmFeature.FramesRendered - a, 10, "the pass records every render while Film effects is on");
                GameSettings.FilmEffects = false;
                yield return Render(cam, 3);
                int b = FilmFeature.FramesRendered;
                yield return Render(cam, 10);
                Assert.AreEqual(b, FilmFeature.FramesRendered, "nothing is recorded while it is off");
                GameSettings.FilmEffects = true;
                yield return Render(cam, 3);
                int c = FilmFeature.FramesRendered;
                yield return Render(cam, 2);
                Assert.Greater(FilmFeature.FramesRendered, c, "back on");
            }
            finally { cam.targetTexture = null; rt.Release(); }
            LogAssert.NoUnexpectedReceived();
        }

        [UnityTest]
        public IEnumerator ThePassCostsUnderPointSixMillisecondsAt1080p()
        {
            yield return Boot();
            var director = Object.FindAnyObjectByType<SceneDirector>();
            var cam = director.PlanetSide.sideCamera;
            var rt = new RenderTexture(1920, 1080, 24, RenderTextureFormat.ARGB32);
            cam.targetTexture = rt; // the pass runs at 1080p whatever the batch game view's size
            try
            {
                float off = 0f, on = 0f, passGpu = 0f;
                yield return Measure(false, (f, p) => off = f);
                yield return Measure(true, (f, p) => { on = f; passGpu = p; });
                float cost = passGpu > 0f ? passGpu : on - off;
                TestContext.Out.WriteLine($"[MERIDIAN] film pass GPU at 1080p: pass sampler {passGpu:F3} ms; frame on {on:F3} ms, off {off:F3} ms (120 frames each)");
                if (passGpu <= 0f && on <= 0f)
                    Assert.Ignore("No GPU timings in this Editor run (FrameTimingManager and the pass Recorder both read 0): the number comes from the dev-build profile (unity_profile -Build, Film pass row).");
                Assert.LessOrEqual(cost, GpuBudgetMs, "≤ 0.6 ms GPU (U-095)");
            }
            finally { cam.targetTexture = null; rt.Release(); }
        }

        /// <summary>Average GPU frame time and the pass's own GPU sampler time (ms) over 120 frames with the film pass on or off, after 30 warm-up frames.</summary>
        IEnumerator Measure(bool film, System.Action<float, float> result)
        {
            UnityEngine.Profiling.Profiler.enabled = true;
            var rec = UnityEngine.Profiling.Recorder.Get("Film pass");
            rec.enabled = true;
            double passSum = 0; int passN = 0;
            GameSettings.FilmEffects = film;
            for (int i = 0; i < 30; i++) { Object.FindAnyObjectByType<SceneDirector>().PlanetSide.sideCamera.Render(); yield return null; }
            var timings = new FrameTiming[1];
            double sum = 0; int n = 0;
            var cam = Object.FindAnyObjectByType<SceneDirector>().PlanetSide.sideCamera;
            for (int i = 0; i < 120; i++)
            {
                cam.Render();
                yield return null;
                FrameTimingManager.CaptureFrameTimings();
                if (FrameTimingManager.GetLatestTimings(1, timings) == 1 && timings[0].gpuFrameTime > 0) { sum += timings[0].gpuFrameTime; n++; }
                if (rec.isValid && rec.gpuElapsedNanoseconds > 0) { passSum += rec.gpuElapsedNanoseconds * 1e-6; passN++; }
            }
            result(n > 0 ? (float)(sum / n) : 0f, passN > 0 ? (float)(passSum / passN) : 0f);
        }
    }
}
