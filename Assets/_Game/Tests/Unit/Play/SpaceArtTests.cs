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
    /// U-034 / U-078 / U-103 (PlayMode, D-098): every planet key is real art; every planet draws as its painted disc sheet
    /// scaled so radius_u is its visual radius (the Sun keeps its lit spheroid); Saturn's painted rings sit behind and in
    /// front of its disc at the disc scale with the disc_rig wobble; Luna's disc lives under Earth; the belt is drawn with
    /// the six asteroid models within the triangle budget; the waystations are models.
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
            // The Space root wakes on the view switch: DockingBay.Start creates the waystations then.
            director.SetView(ViewMode.Space);
            yield return null;
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

            // U-103 (D-098): every body with a disc sheet is a DiscSprite scaled so radius_u draws as its visual radius; the Sun keeps its spheroid.
            until = Time.realtimeSinceStartup + 20f;
            while (Time.realtimeSinceStartup < until)
            {
                bool ready = world.Discs.Count >= 8;
                foreach (var d in world.Discs) ready &= d.Ready;
                if (ready && world.RingsBack != null && world.RingsBack.sprite != null && world.RingsFront != null && world.RingsFront.sprite != null && world.SaturnWobble != null) break;
                yield return null;
            }
            Assert.GreaterOrEqual(world.Discs.Count, 8, $"the eight planets draw as discs (have {world.Discs.Count})");
            foreach (var d in world.Discs)
            {
                var b = world.Find(d.transform.parent.name).Value;
                Assert.IsTrue(d.Ready, b.name + " disc sheet + sidecar loaded");
                Assert.NotNull(d.Renderer.sprite, b.name + " drawing");
                Assert.AreEqual(3f, d.Renderer.sprite.pixelsPerUnit, 1e-3f, b.name + " imported at space_ppu 3");
                Assert.AreEqual(b.radius / d.Json.radius_u, d.transform.localScale.x, 1e-4f, b.name + ": scale = visual radius / radius_u (a wrong radius_u mis-sizes the planet)");
                Assert.IsNull(d.transform.parent.Find("Atmo"), b.name + ": no atmosphere shell over a painted disc");
                Assert.AreEqual(SpaceWorld.DiscKey(b), d.Key, b.name + " key");
                Assert.Greater(d.FrameCount, 8, b.name + " idle frames (9 or 12)");
            }
            var sunDisc = world.transform.Find("sun/Disc");
            Assert.NotNull(sunDisc, "the Sun's spheroid");
            Assert.NotNull(sunDisc.GetComponent<MeshFilter>(), "the Sun keeps its lit spheroid (no disc sheet, B-119)");

            // Saturn's painted rings: behind and in front of the disc at its scale, breathing per disc_rig.json; the B-090 mesh retired.
            Assert.NotNull(world.RingsBack, "rings_back"); Assert.NotNull(world.RingsFront, "rings_front");
            Assert.NotNull(world.RingsBack.sprite, "rings_back drawing"); Assert.NotNull(world.RingsFront.sprite, "rings_front drawing");
            Assert.IsTrue(world.RingsReady, "both painted rings in");
            Assert.IsNull(world.Rings, "the B-090 ring mesh retired where the painted rings exist");
            Assert.Less(world.RingsBack.sortingOrder, 10, "rings_back behind the disc"); Assert.Greater(world.RingsFront.sortingOrder, 10, "rings_front in front");
            Assert.AreEqual(3f, world.RingsBack.sprite.pixelsPerUnit, 1e-3f, "rings at the disc scale (PPU 3, cycle-243 review fix)");
            var saturn = world.Find("saturn").Value;
            var saturnDisc = world.Discs.Find(d => d.transform.parent.name == "saturn");
            Assert.NotNull(saturnDisc, "Saturn's disc");
            yield return null;
            Assert.AreEqual(saturnDisc.Scale, world.RingsBack.transform.localScale.x, 1e-4f, "rings scaled with the disc");
            Assert.NotNull(world.SaturnWobble, "disc_rig.json wobble parsed");
            float ringWidth = world.RingsBack.sprite.bounds.size.x * world.RingsBack.transform.localScale.x;
            TestContext.Out.WriteLine($"[MERIDIAN] Saturn painted rings {ringWidth:F1} u across (R {saturn.radius}), wobble ±{world.SaturnWobble.scale_y} / ±{world.SaturnWobble.rotate_deg}°; discs {world.Discs.Count}; belt kinds {world.Belt.Count}, rocks {world.BeltRocks}; glows {world.Glows.Count}");

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

            var lunaDisc = world.Discs.Find(d => d.transform.parent.name == "luna");
            Assert.NotNull(lunaDisc, "Luna draws from planets/earth/luna (a moon's sheet lives under its parent, D-098)");
            Assert.AreEqual("planets/earth/luna", lunaDisc.Key);
            Assert.IsTrue(lunaDisc.Ready && lunaDisc.Renderer.sprite != null, "Luna disc loaded");

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
