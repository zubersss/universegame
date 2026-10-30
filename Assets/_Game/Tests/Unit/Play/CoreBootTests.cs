using System.Collections;
using Meridian.Core;
using Meridian.Planets;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>U-004: Play from Core loads Space (inactive) and PlanetSide (Earth) with a clean console.</summary>
    public class CoreBootTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";

        [UnityTest]
        public IEnumerator CoreLoadsSpaceInactiveAndPlanetSideEarth()
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

            Assert.IsTrue(SceneManager.GetSceneByName(SceneDirector.SpaceScene).isLoaded, "Space loaded");
            Assert.NotNull(director.Space, "SpaceRoot found");
            Assert.IsFalse(director.Space.gameObject.activeSelf, "Space inactive");

            Assert.IsTrue(SceneManager.GetSceneByName(SceneDirector.PlanetSideScene).isLoaded, "PlanetSide loaded");
            Assert.NotNull(director.PlanetSide, "PlanetSideRoot found");
            Assert.AreEqual(PlanetId.Earth, director.PlanetSide.Config.id);
            Assert.AreEqual(-9.81f, Physics2D.gravity.y, 1e-4f, "Earth gravity applied");

            Assert.NotNull(Object.FindAnyObjectByType<TimeSystem>(), "TimeSystem in Core");
            yield return null;
            LogAssert.NoUnexpectedReceived();
        }
    }
}
