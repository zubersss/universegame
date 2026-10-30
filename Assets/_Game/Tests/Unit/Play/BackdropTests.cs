using System.Collections;
using Meridian.Core;
using Meridian.Planet;
using Meridian.Planets;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>U-024 (PlayMode): Earth and Mars load their three parallax layers and sky; layers scroll at distinct rates.</summary>
    public class BackdropTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";

        [UnityTest]
        public IEnumerator EarthAndMarsLoadThreeLayersWithTheirSky()
        {
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while (!director.IsReady && Time.realtimeSinceStartup < timeout) yield return null;
            var backdrop = director.PlanetSide.backdrop;
            Assert.NotNull(backdrop, "PlanetBackdrop on the side camera");

            yield return WaitLayers(backdrop);
            Assert.AreEqual(PlanetId.Earth, backdrop.Planet);
            Assert.AreEqual(3, backdrop.LayersLoaded, "Earth layer0..2");
            Assert.AreEqual(PlanetBackdrop.Tinted(PlanetBackdrop.SkyColor(PlanetId.Earth), backdrop.Tint), director.PlanetSide.sideCamera.backgroundColor, "sky color × day/night tint");
            AssertLayersTileInX(backdrop);

            var mars = GameState.Instance.catalog.Get(PlanetId.Mars);
            yield return director.LoadPlanetSide(mars);
            yield return WaitLayers(backdrop);
            Assert.AreEqual(PlanetId.Mars, backdrop.Planet);
            Assert.AreEqual(3, backdrop.LayersLoaded, "Mars layer0..2");
            Assert.AreEqual(PlanetBackdrop.Tinted(PlanetBackdrop.SkyColor(PlanetId.Mars), backdrop.Tint), director.PlanetSide.sideCamera.backgroundColor, "sky color × day/night tint");
            AssertLayersTileInX(backdrop);
            LogAssert.NoUnexpectedReceived();
        }

        [Test]
        public void FarLayersScrollSlowerThanNearOnes()
        {
            float f0 = PlanetBackdrop.ScreenShiftPerMetre(0), f1 = PlanetBackdrop.ScreenShiftPerMetre(1), f2 = PlanetBackdrop.ScreenShiftPerMetre(2);
            Assert.That(f0, Is.GreaterThan(0f).And.LessThan(f1), "layer0 slowest");
            Assert.Less(f1, f2, "layer2 fastest");
            Assert.Less(f2, 1f, "even the near layer moves slower than the terrain");
        }

        static IEnumerator WaitLayers(PlanetBackdrop b)
        {
            float timeout = Time.realtimeSinceStartup + 10f;
            while (b.LayersLoaded < 3 && Time.realtimeSinceStartup < timeout) yield return null;
        }

        static void AssertLayersTileInX(PlanetBackdrop b)
        {
            int quads = 0;
            foreach (var mr in b.GetComponentsInChildren<MeshRenderer>(true)) if (mr.name.StartsWith("Backdrop")) quads++;
            Assert.AreEqual(1, quads, "one quad, one pass for sky + 3 layers");
            for (int i = 0; i < 3; i++)
            {
                var tex = b.LayerTexture(i);
                Assert.NotNull(tex, $"layer{i}");
                Assert.AreEqual(TextureWrapMode.Repeat, tex.wrapModeU, $"layer{i} wraps in x (no seam)");
            }
        }
    }
}
