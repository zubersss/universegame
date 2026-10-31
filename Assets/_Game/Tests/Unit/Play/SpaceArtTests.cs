using System.Collections;
using Meridian.Core;
using Meridian.Space;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>U-034 (PlayMode): every planet key is real art, Saturn has its rings at ≈ 446 u, Luna has its surface, the belt is drawn with the asteroid art.</summary>
    public class SpaceArtTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";
        static readonly string[] Planets = { "sun", "mercury", "venus", "earth", "mars", "jupiter", "saturn", "uranus", "neptune" };

        [UnityTest]
        public IEnumerator SpaceUsesTheRealArt()
        {
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
            var director = Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 30f;
            while (!director.IsReady && Time.realtimeSinceStartup < timeout) yield return null;
            var world = Object.FindAnyObjectByType<SpaceWorld>(FindObjectsInactive.Include);
            Assert.NotNull(world);

            // No placeholder left for any planet key: each address resolves inside Art/.
            foreach (var p in Planets)
            {
                var loc = Addressables.LoadResourceLocationsAsync($"planets/{p}/surface");
                yield return loc;
                Assert.Greater(loc.Result.Count, 0, p);
                StringAssert.Contains("/Art/", loc.Result[0].InternalId.Replace('\\', '/'), $"{p} surface is real art");
                Addressables.Release(loc);
            }

            float until = Time.realtimeSinceStartup + 15f;
            while ((world.Rings == null || world.Rings.sprite == null || world.BeltArt.Count < SpaceWorld.AsteroidKinds) && Time.realtimeSinceStartup < until) yield return null;

            Assert.NotNull(world.Rings, "Saturn's rings");
            Assert.NotNull(world.Rings.sprite);
            float ringWidth = world.Rings.bounds.size.x;
            TestContext.Out.WriteLine($"[MERIDIAN] Saturn rings {ringWidth:F1} u across; belt meshes {world.BeltArt.Count}; glows {world.Glows.Count}");
            Assert.AreEqual(446f, ringWidth, 446f * 0.01f, "rings ≈ 446 u (A-ring outer edge 500 px of 1024, Saturn R 220.4 px, R 96)");

            Assert.AreEqual(SpaceWorld.AsteroidKinds, world.BeltArt.Count, "belt drawn with asteroid_01..06 (one mesh each)");
            foreach (var mr in world.BeltArt)
            {
                var block = new MaterialPropertyBlock();
                mr.GetPropertyBlock(block);
                StringAssert.StartsWith("asteroid_0", block.GetTexture("_MainTex").name, mr.name);
                Assert.Greater(mr.GetComponent<MeshFilter>().sharedMesh.vertexCount, 100, mr.name);
            }

            var luna = world.transform.Find("luna/Disc").GetComponent<MeshRenderer>();
            var lb = new MaterialPropertyBlock();
            until = Time.realtimeSinceStartup + 5f;
            while (Time.realtimeSinceStartup < until) { luna.GetPropertyBlock(lb); if (lb.GetTexture("_MainTex") != null) break; yield return null; }
            Assert.NotNull(lb.GetTexture("_MainTex"), "Luna disc from planets/luna/surface");

            Assert.GreaterOrEqual(world.Glows.Count, 8, "glows behind the Sun and every planet with an atmosphere");
            LogAssert.NoUnexpectedReceived();
        }
    }
}
