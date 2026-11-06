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
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
            for (int i = 0; i < 30; i++) yield return null;
        }

        [UnityTest]
        public IEnumerator TheToggleRemovesThePass()
        {
            yield return Boot();
            GameSettings.FilmEffects = true;
            for (int i = 0; i < 3; i++) yield return null;
            int a = FilmFeature.FramesRendered;
            for (int i = 0; i < 10; i++) yield return null;
            Assert.Greater(FilmFeature.FramesRendered, a, "the pass records while Film effects is on");
            GameSettings.FilmEffects = false;
            for (int i = 0; i < 3; i++) yield return null;
            int b = FilmFeature.FramesRendered;
            for (int i = 0; i < 10; i++) yield return null;
            Assert.AreEqual(b, FilmFeature.FramesRendered, "nothing is recorded while it is off");
            GameSettings.FilmEffects = true;
            for (int i = 0; i < 3; i++) yield return null;
            int c = FilmFeature.FramesRendered;
            yield return null; yield return null;
            Assert.Greater(FilmFeature.FramesRendered, c, "back on");
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
                float off = 0f, on = 0f;
                yield return Measure(false, v => off = v);
                yield return Measure(true, v => on = v);
                float cost = on - off;
                TestContext.Out.WriteLine($"[MERIDIAN] film pass GPU at 1080p: on {on:F3} ms, off {off:F3} ms, pass {cost:F3} ms (FrameTimingManager, 120 frames each)");
                Assert.Greater(on, 0f, "FrameTimingManager reports GPU time (Frame Timing Stats on in Player settings)");
                Assert.LessOrEqual(cost, GpuBudgetMs, "≤ 0.6 ms GPU (U-095)");
            }
            finally { cam.targetTexture = null; rt.Release(); }
        }

        /// <summary>Average GPU frame time (ms) over 120 frames with the film pass on or off, after 30 warm-up frames.</summary>
        IEnumerator Measure(bool film, System.Action<float> result)
        {
            GameSettings.FilmEffects = film;
            for (int i = 0; i < 30; i++) yield return null;
            var timings = new FrameTiming[1];
            double sum = 0; int n = 0;
            for (int i = 0; i < 120; i++)
            {
                yield return null;
                FrameTimingManager.CaptureFrameTimings();
                if (FrameTimingManager.GetLatestTimings(1, timings) == 1 && timings[0].gpuFrameTime > 0) { sum += timings[0].gpuFrameTime; n++; }
            }
            result(n > 0 ? (float)(sum / n) : 0f);
        }
    }
}
