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
    /// <summary>
    /// U-034 / U-078 (PlayMode): every planet key is real art; the planets are SpaceLit spheroids with atmosphere
    /// shells (and Earth's cloud shell); Saturn has the B-090 ring mesh at 2 × 2.269 R; Luna has its surface; the
    /// belt is drawn with the six asteroid models within the triangle budget; the waystations are models.
    /// </summary>
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
            while ((!world.RingsReady || !world.BeltReady) && Time.realtimeSinceStartup < until) yield return null;

            // Spheroids: every body's "Disc" is the SpaceLit spheroid, scaled to its diameter.
            foreach (var b in world.Bodies)
            {
                var disc = world.transform.Find(b.name + "/Disc");
                Assert.NotNull(disc, b.name + " spheroid");
                Assert.AreEqual(SpaceMeshes.Spheroid(), disc.GetComponent<MeshFilter>().sharedMesh, b.name + " uses the shared spheroid");
                Assert.AreEqual(2f * b.radius, disc.localScale.x, 1e-3f, b.name + " diameter");
                StringAssert.Contains("SpaceLit", disc.GetComponent<MeshRenderer>().sharedMaterial.shader.name, b.name + " shader");
            }
            Assert.NotNull(world.transform.Find("earth/Atmo"), "Earth's atmosphere shell");
            Assert.NotNull(world.transform.Find("jupiter/Atmo"), "Jupiter's atmosphere shell");
            Assert.IsNull(world.transform.Find("sun/Atmo"), "the Sun has no atmosphere shell");
            Assert.IsNull(world.transform.Find("mercury/Atmo"), "Mercury has no atmosphere shell");
            until = Time.realtimeSinceStartup + 5f;
            while (world.transform.Find("earth/Clouds") == null && Time.realtimeSinceStartup < until) yield return null;
            Assert.NotNull(world.transform.Find("earth/Clouds"), "Earth's cloud shell from planets/earth/clouds");

            // Saturn's rings: the B-090 annulus (1.239–2.269 R, modelled for R 96) scaled to Saturn's R, in the view plane.
            Assert.NotNull(world.Rings, "Saturn's ring mesh");
            Assert.IsTrue(world.RingsReady, "ring texture loaded");
            float saturnR = world.Find("saturn").Value.radius;
            float ringWidth = world.Rings.bounds.size.x;
            TestContext.Out.WriteLine($"[MERIDIAN] Saturn rings {ringWidth:F1} u across (R {saturnR}); belt kinds {world.Belt.Count}, rocks {world.BeltRocks}; glows {world.Glows.Count}; shells {world.Shells.Count}");
            Assert.AreEqual(2f * SpaceWorld.RingOuterR * saturnR, ringWidth, 2f * SpaceWorld.RingOuterR * saturnR * 0.01f, "rings span 2 × 2.269 R (B-090 ring_mesh)");
            Assert.Less(world.Rings.bounds.size.z, 1f, "the ring lies in the view plane");

            // The belt: one instanced draw per asteroid model, rocks within the triangle budget.
            Assert.AreEqual(SpaceWorld.AsteroidKinds, world.Belt.Count, "belt drawn with asteroid_01..06 (one instanced draw each)");
            int rocks = 0, triangles = 0;
            foreach (var k in world.Belt)
            {
                Assert.NotNull(k.mesh, k.key);
                Assert.Greater(k.triangles, 50, k.key + " triangles");
                Assert.NotNull(k.material.GetTexture("_MainTex"), k.key + " albedo from its generated material");
                Assert.IsTrue(k.material.enableInstancing, k.key + " instanced");
                rocks += k.count;
                triangles += k.count * k.triangles;
            }
            Assert.AreEqual(world.BeltRocks, rocks, "every rock placed");
            Assert.Greater(rocks, 100, "enough rocks to read as a belt");
            Assert.LessOrEqual(triangles, SpaceWorld.BeltTriangleBudget, "belt within its triangle budget (§11.1)");

            var luna = world.transform.Find("luna/Disc").GetComponent<MeshRenderer>();
            var lb = new MaterialPropertyBlock();
            until = Time.realtimeSinceStartup + 5f;
            while (Time.realtimeSinceStartup < until) { luna.GetPropertyBlock(lb); if (lb.GetTexture("_MainTex") != null) break; yield return null; }
            Assert.NotNull(lb.GetTexture("_MainTex"), "Luna disc from planets/luna/surface");

            Assert.GreaterOrEqual(world.Glows.Count, 8, "glows behind the Sun and every planet with an atmosphere");

            // Waystations: the B-090 models, Size u across in the view plane, SpaceLit with their emission map.
            until = Time.realtimeSinceStartup + 10f;
            while (Time.realtimeSinceStartup < until)
            {
                bool all = Meridian.Trade.Waystation.All.Count > 0;
                foreach (var w in Meridian.Trade.Waystation.All) all &= w.Ready;
                if (all) break;
                yield return null;
            }
            Assert.Greater(Meridian.Trade.Waystation.All.Count, 0, "waystations exist");
            foreach (var w in Meridian.Trade.Waystation.All)
            {
                Assert.IsTrue(w.Ready, w.name + " model loaded (" + w.ModelKey + ")");
                var r = w.Model.GetComponentInChildren<Renderer>();
                StringAssert.Contains("SpaceLit", r.sharedMaterial.shader.name, w.name + " shader");
                Assert.NotNull(r.sharedMaterial.GetTexture("_EmissionMap"), w.name + " emission map (docking lights)");
                float across = Mathf.Max(r.bounds.size.x, r.bounds.size.y);
                Assert.AreEqual(Meridian.Trade.Waystation.Size, across, Meridian.Trade.Waystation.Size * 0.05f, w.name + " is Size u across in the view plane");
                Assert.Less(r.bounds.size.z, Meridian.Trade.Waystation.Size * 0.3f, w.name + " lies flat in the view plane");
            }
            LogAssert.NoUnexpectedReceived();
        }
    }
}
