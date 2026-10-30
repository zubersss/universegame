using System.Collections;
using Meridian.Core;
using Meridian.Planets;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests.LeadQA
{
    /// <summary>L-007: LEAD's independent smoke test. Boots Core, runs ~2 s of real frames, console stays clean.</summary>
    public class SmokeTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";

        [UnityTest]
        public IEnumerator CoreBootsAndRunsTwoSecondsWithCleanConsole()
        {
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#else
            yield return SceneManager.LoadSceneAsync("Core", LoadSceneMode.Single);
#endif
            var director = Object.FindAnyObjectByType<SceneDirector>();
            Assert.NotNull(director, "SceneDirector in Core");

            float timeout = Time.realtimeSinceStartup + 10f;
            while (!director.IsReady && Time.realtimeSinceStartup < timeout) yield return null;
            Assert.IsTrue(director.IsReady, "SceneDirector ready within 10 s");
            Assert.AreEqual(PlanetId.Earth, director.PlanetSide.Config.id, "starts on Earth");

            var time = Object.FindAnyObjectByType<TimeSystem>();
            Assert.NotNull(time, "TimeSystem in Core");
            double start = time.GameSeconds;

            float end = Time.realtimeSinceStartup + 2f;
            int frames = 0;
            while (Time.realtimeSinceStartup < end) { frames++; yield return null; }

            Assert.Greater(frames, 10, "game kept producing frames");
            Assert.Greater(time.GameSeconds, start, "game clock advances (72x)");
            Assert.AreEqual(-9.81f, Physics2D.gravity.y, 1e-3f, "Earth gravity still applied");
            LogAssert.NoUnexpectedReceived();
        }
    }
}
