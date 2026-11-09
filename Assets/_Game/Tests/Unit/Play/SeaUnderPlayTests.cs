using System.Collections;
using Meridian.Core;
using Meridian.Terrain;
using Meridian.View2D;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>
    /// U-171 (B-200's read, B-202's sea_under): Earth's sea from below. Out at sea under the water line the land set's nearest layer and its
    /// continued strip are gone (no beach or meadow on or under the water) and sea_under's water column covers the frame below the surface,
    /// over every land-set layer still drawn there; at 3 m the far layers still show above the surface; at the shore, above the water, the
    /// land set is untouched and sea_under draws nothing; between them the weight crossfades over 3 m.
    /// </summary>
    public class SeaUnderPlayTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";

        [Test]
        public void TheSeaShareCrossfadesOverThreeMetres()
        {
            System.Func<int, bool> sea = x => x >= 100;
            Assert.AreEqual(0f, CartoonStage.SeaShare(90f, sea));
            Assert.AreEqual(1f, CartoonStage.SeaShare(110f, sea));
            float mid = CartoonStage.SeaShare(100f, sea);
            Assert.Greater(mid, 0.3f); Assert.Less(mid, 0.8f);
            Assert.Less(CartoonStage.SeaShare(99f, sea), mid); Assert.Greater(CartoonStage.SeaShare(101f, sea), mid);
            Assert.AreEqual(0f, CartoonStage.SeaShare(98.4f, sea), "1.5 m out: land");
        }

        [UnityTest, Timeout(300000)]
        public IEnumerator UnderTheSeaNoLandSetPixelShows()
        {
            bool was = CartoonStage.Enabled;
            CartoonStage.Enabled = true;
            try
            {
#if UNITY_EDITOR
                yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#endif
                var director = Object.FindAnyObjectByType<SceneDirector>();
                float timeout = Time.realtimeSinceStartup + 30f;
                while ((!director.IsReady || !director.PlanetSide.terrain.IsSettled) && Time.realtimeSinceStartup < timeout) yield return null;
                var side = director.PlanetSide;
                if (side.hazards != null) side.hazards.enabled = false;
                side.creatures.autoSpawn = false; side.creatures.DespawnAll();
                var stage = Object.FindAnyObjectByType<CartoonStage>();
                Assert.NotNull(stage, "the cartoon stage");
                var player = side.player;
                var gen = (SolidWorldGenerator)side.terrain.BaseGenerator;
                float water = side.Config.datumY + 1f;
                EarthBiomes.Range(Biome.Ocean, out int os, out int len);
                int deep = os + 40;
                for (int x = os + 20; x < os + len - 20; x++) if (gen.SeaAt(x) && gen.SurfaceHeight(x) <= water - 18) { deep = x; break; }
                var cam = side.sideCamera;
                var follow = cam.GetComponent<Meridian.Player.CameraFollow>();
                IEnumerator Hold(Vector2 at)
                {
                    player.Body.simulated = false; // held where the frame is wanted (the sea would lift a swimmer)
                    player.Body.position = at; player.transform.position = at;
                    float until = Time.realtimeSinceStartup + 10f;
                    yield return null;
                    while (!side.terrain.IsSettled && Time.realtimeSinceStartup < until) yield return null;
                    if (follow != null) follow.SnapToTarget();
                    for (int i = 0; i < 90; i++) yield return null; // the sets load and settle
                }

                // out at sea, 10 m under
                yield return Hold(new Vector2(deep + 0.5f, water - 10f));
                Assert.AreEqual(1f, stage.SeaWeight, 1e-4f, "out at sea");
                Assert.AreEqual(0f, stage.Layers.nearAlpha, 1e-4f, "the land set's nearest layer gone");
                Assert.NotNull(stage.SeaUnder); Assert.IsTrue(stage.SeaUnder.gameObject.activeSelf, "sea_under on");
                Assert.AreEqual("backgrounds/earth/sea_under", stage.SeaUnder.SceneKey);
                float until2 = Time.realtimeSinceStartup + 10f;
                while (stage.SeaUnder.placeholders.Contains(true) && Time.realtimeSinceStartup < until2) yield return null;
                float half = Meridian.CameraRig.SideView.HalfHeight(cam), halfW = half * cam.aspect;
                var c = cam.transform.position;
                var under = Rect.MinMaxRect(c.x - halfW, c.y - half, c.x + halfW, Mathf.Min(water, c.y + half));
                // the water column (layer0 and its strip) covers the frame under the surface
                int waterOrder = ParallaxLayers.BackOrder + CartoonStage.SeaUnderOrder + 0;
                float covTop = float.MinValue, covBottom = float.MaxValue, covLeft = float.MaxValue, covRight = float.MinValue;
                foreach (var r in stage.SeaUnder.GetComponentsInChildren<SpriteRenderer>())
                {
                    if (!r.enabled || r.sortingOrder != waterOrder || r.color.a < 0.99f) continue;
                    var b = r.bounds;
                    covTop = Mathf.Max(covTop, b.max.y); covBottom = Mathf.Min(covBottom, b.min.y); covLeft = Mathf.Min(covLeft, b.min.x); covRight = Mathf.Max(covRight, b.max.x);
                }
                TestContext.Out.WriteLine($"[MERIDIAN] u171 at {deep}, 10 m under: the frame under the surface {under}, the water column {covLeft:0.0}..{covRight:0.0} x {covBottom:0.0}..{covTop:0.0}");
                Assert.LessOrEqual(covLeft, under.xMin); Assert.GreaterOrEqual(covRight, under.xMax);
                Assert.LessOrEqual(covBottom, under.yMin); Assert.GreaterOrEqual(covTop, under.yMax - 0.05f, "the water column reaches the surface");
                // every land-set layer still drawn there sits under it
                int landDrawn = 0;
                foreach (var r in stage.Layers.GetComponentsInChildren<SpriteRenderer>())
                {
                    if (!r.enabled || r.color.a < 0.01f || !r.bounds.Intersects(new Bounds(under.center, under.size))) continue;
                    landDrawn++;
                    Assert.Less(r.sortingOrder, waterOrder, $"{r.name}: under the water column");
                }
                TestContext.Out.WriteLine($"[MERIDIAN] u171 land-set layers behind the water column: {landDrawn}");

                // 3 m under: the land set's far layers still above the surface, the nearest gone
                yield return Hold(new Vector2(deep + 0.5f, water - 3f));
                Assert.AreEqual(0f, stage.Layers.nearAlpha, 1e-4f);
                Assert.IsTrue(stage.SeaUnder.gameObject.activeSelf);

                // the shore above the water: untouched
                int shore = os - 12;
                yield return Hold(new Vector2(shore + 0.5f, side.terrain.SurfaceAt(shore + 0.5f) + 0.5f));
                Assert.AreEqual(0f, stage.SeaWeight, 1e-4f, "on land");
                Assert.AreEqual(1f, stage.Layers.nearAlpha, 1e-4f, "the land set whole");
                Assert.IsFalse(stage.SeaUnder.gameObject.activeSelf, "sea_under draws nothing");
                player.Body.simulated = true;
                LogAssert.NoUnexpectedReceived();
            }
            finally { CartoonStage.Enabled = was; }
        }
    }
}
