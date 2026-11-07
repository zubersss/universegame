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
        bool wasCartoon = true;
        // D-132: PlanetBackdrop is the 3D path's sky and biome sets; the game runs Earth on the cartoon path, so this class switches it off for its run and restores it.
        [SetUp] public void ThreeDPath() { wasCartoon = Meridian.View2D.CartoonStage.Enabled; Meridian.View2D.CartoonStage.Enabled = false; }
        [TearDown] public void RestoreCartoon() { Meridian.View2D.CartoonStage.Enabled = wasCartoon; }

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
            Assert.IsTrue(backdrop.SetReady(backdrop.MainSet), $"Earth layer0..2 loaded ({backdrop.MainSet})");
            Assert.AreEqual(backdrop.DepthBandsOn ? 1 : 3, backdrop.LayersLoaded, "drawn layers: the sky only under the depth bands (U-076), else all three");
            Assert.AreEqual(PlanetBackdrop.Tinted(PlanetBackdrop.SkyColor(PlanetId.Earth), backdrop.Tint), director.PlanetSide.sideCamera.backgroundColor, "sky color × day/night tint");
            AssertLayersTileInX(backdrop);

            var mars = GameState.Instance.catalog.Get(PlanetId.Mars);
            yield return director.LoadPlanetSide(mars);
            yield return WaitLayers(backdrop);
            Assert.AreEqual(PlanetId.Mars, backdrop.Planet);
            Assert.IsTrue(backdrop.SetReady(backdrop.MainSet), $"Mars layer0..2 loaded ({backdrop.MainSet})");
            Assert.AreEqual(backdrop.DepthBandsOn ? 1 : 3, backdrop.LayersLoaded, "drawn layers per the depth bands (U-076)");
            Assert.AreEqual(PlanetBackdrop.Tinted(PlanetBackdrop.SkyColor(PlanetId.Mars), backdrop.Tint), director.PlanetSide.sideCamera.backgroundColor, "sky color × day/night tint");
            AssertLayersTileInX(backdrop);
            LogAssert.NoUnexpectedReceived();
        }

        [Test]
        public void EarthBiomesPickTheirBackdropSets()
        {
            Meridian.Terrain.EarthBiomes.Range(Meridian.Terrain.Biome.Desert, out int desert, out int dl);
            Meridian.Terrain.EarthBiomes.Range(Meridian.Terrain.Biome.Taiga, out int taiga, out int tl);
            Meridian.Terrain.EarthBiomes.Range(Meridian.Terrain.Biome.Ocean, out int ocean, out int ol);
            Assert.AreEqual("earth", PlanetBackdrop.SetFor(PlanetId.Earth, 64), "forest");
            Assert.AreEqual("earth_desert", PlanetBackdrop.SetFor(PlanetId.Earth, desert + dl / 2));
            Assert.AreEqual("earth_taiga", PlanetBackdrop.SetFor(PlanetId.Earth, taiga + tl / 2));
            Assert.AreEqual("earth_coast", PlanetBackdrop.SetFor(PlanetId.Earth, ocean + ol / 2));
            Assert.AreEqual("mars", PlanetBackdrop.SetFor(PlanetId.Mars, desert + dl / 2), "other planets: one set");
        }

        /// <summary>U-038: at the plains/desert border the desert set fades in over 20 m with one extra quad; past it the desert set is the backdrop.</summary>
        [UnityTest]
        public IEnumerator BiomeBorderCrossFades()
        {
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while (!director.IsReady && Time.realtimeSinceStartup < timeout) yield return null;
            var side = director.PlanetSide;
            var b = side.backdrop;
            var cam = side.sideCamera;
            cam.GetComponent<Meridian.Player.CameraFollow>().enabled = false;
            Meridian.Terrain.EarthBiomes.Range(Meridian.Terrain.Biome.Desert, out int border, out _);
            float y = cam.transform.position.y;

            // Approach: the desert set loads ahead (≤ 60 m), so the border itself never waits on a sheet.
            cam.transform.position = new Vector3(border - 50f, y, cam.transform.position.z);
            float until = Time.realtimeSinceStartup + 10f;
            yield return null;
            while (Time.realtimeSinceStartup < until && !(b.MainSet == "earth" && b.SetReady("earth"))) yield return null;
            until = Time.realtimeSinceStartup + 10f;
            while (!b.SetReady("earth_desert") && Time.realtimeSinceStartup < until) yield return null; // preloaded ≤ 60 m ahead
            Assert.IsTrue(b.SetReady("earth_desert"), "the desert set is loaded before the border");
            Assert.AreEqual("earth", b.MainSet);
            Assert.IsNull(b.OverlaySet, "no fade 50 m from the border");

            cam.transform.position = new Vector3(border + 0.5f, y, cam.transform.position.z);
            yield return null;
            yield return null;
            Assert.AreEqual("earth", b.MainSet, "left of the window: plains set underneath");
            Assert.AreEqual("earth_desert", b.OverlaySet, "desert set fading in");
            Assert.That(b.FadeWeight, Is.InRange(0.45f, 0.6f), "half-way through the 20 m window");
            int quads = 0;
            foreach (var r in cam.GetComponentsInChildren<MeshRenderer>())
                if (r.enabled && r.sortingOrder <= -199) quads++;
            Assert.AreEqual(2, quads, "the fade costs one extra backdrop quad (≤ +3 draw calls)");

            cam.transform.position = new Vector3(border + 15f, y, cam.transform.position.z);
            yield return null;
            yield return null;
            Assert.AreEqual("earth_desert", b.MainSet, "past the window the desert set is the backdrop");
            Assert.IsNull(b.OverlaySet);
            Assert.IsTrue(b.SetReady("earth_desert"), "already loaded: no pop-in");
            Assert.AreEqual(b.DepthBandsOn ? 1 : 3, b.LayersLoaded, "drawn layers per the depth bands (U-076)");
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
            while (!(b.MainSet != null && b.SetReady(b.MainSet)) && Time.realtimeSinceStartup < timeout) yield return null;
        }

        static void AssertLayersTileInX(PlanetBackdrop b)
        {
            int quads = 0;
            foreach (var mr in b.GetComponentsInChildren<MeshRenderer>(true)) if (mr.name.StartsWith("Backdrop")) quads++;
            Assert.AreEqual(1, quads, "one quad, one pass for sky + 3 layers");
            // U-076: under the depth bands only the sky layer is applied to the quad (layers 1–2 are meshes); D-124.
            for (int i = 0; i < (b.DepthBandsOn ? 1 : 3); i++)
            {
                var tex = b.LayerTexture(i);
                Assert.NotNull(tex, $"layer{i}");
                Assert.AreEqual(TextureWrapMode.Repeat, tex.wrapModeU, $"layer{i} wraps in x (no seam)");
            }
        }
    }
}
