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
    /// land set is untouched and sea_under draws nothing; between them the weight crossfades over 3 m. At smoke_43's frame no back wall
    /// stands over the shore's curve.
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

        /// <summary>U-205 (B-225): a shore layer (sea_under's shallow seabed, shore_m 40) is whole to 32 m out and gone from 40 m; the distance
        /// is to the nearest land column's edge on either side.</summary>
        [Test]
        public void TheShallowsShowByTheShoreOnly()
        {
            System.Func<int, bool> sea = x => x >= 100 && x < 400; // land up to 99, the sea, land again from 400
            Assert.AreEqual(0f, CartoonStage.ShoreDistance(99.5f, 40, sea), "on land");
            Assert.AreEqual(0.5f, CartoonStage.ShoreDistance(100.5f, 40, sea), 1e-4f, "half a metre out from the land column's edge at 100");
            Assert.AreEqual(10.25f, CartoonStage.ShoreDistance(110.25f, 40, sea), 1e-4f);
            Assert.AreEqual(5.5f, CartoonStage.ShoreDistance(394.5f, 40, sea), 1e-4f, "the far shore's edge at 400");
            Assert.AreEqual(41f, CartoonStage.ShoreDistance(250f, 40, sea), 1e-4f, "no land within reach: reach + 1");
            Assert.AreEqual(1f, CartoonStage.ShallowsWeight(0f, 40f));
            Assert.AreEqual(1f, CartoonStage.ShallowsWeight(32f, 40f), 1e-4f, "whole to shore_m less the fade");
            Assert.AreEqual(0.5f, CartoonStage.ShallowsWeight(36f, 40f), 1e-4f);
            Assert.AreEqual(0f, CartoonStage.ShallowsWeight(40f, 40f));
            Assert.AreEqual(0f, CartoonStage.ShallowsWeight(41f, 40f));
            Assert.AreEqual(1f, CartoonStage.ShallowsWeight(500f, 0f), "a layer with no shore_m is not a shore layer");
            // LEAD 11-09 23:2x: a backdrop for the shallows only: whole while the camera is 2 m or more over its painted ground line,
            // gone at the line (the swimmer the camera follows is then never under the line while the layer is whole)
            Assert.AreEqual(1f, CartoonStage.ShallowsDepthWeight(5f, 0f), "the camera well above the layer's ground line");
            Assert.AreEqual(1f, CartoonStage.ShallowsDepthWeight(2f, 0f), "2 m above: still whole");
            Assert.AreEqual(0.5f, CartoonStage.ShallowsDepthWeight(1f, 0f), 1e-5f, "1 m above: half");
            Assert.AreEqual(0f, CartoonStage.ShallowsDepthWeight(0f, 0f), "at the line: gone");
            Assert.AreEqual(0f, CartoonStage.ShallowsDepthWeight(-9f, 0f), "and under it");
        }

        /// <summary>U-205 (B-225): sea_under's shallow seabed (layer4, draw_before 3) draws over the two seabeds and under the surface seen from
        /// below; a set that states no draw_before draws by n exactly as before.</summary>
        [Test]
        public void TheShallowSeabedDrawsBeforeTheSurfaceLayer()
        {
            var sea = SceneLayout.Parse("{\"layers\":[{\"n\":0},{\"n\":1},{\"n\":2},{\"n\":3},{\"n\":4,\"shore_m\":40.0,\"draw_before\":3}]}").layers;
            Assert.AreEqual(5, sea.Length);
            Assert.AreEqual(40f, sea[4].shore_m); Assert.AreEqual(3, sea[4].draw_before);
            int[] want = { 0, 1, 2, 4, 3 };
            for (int i = 0; i < sea.Length; i++) Assert.AreEqual(want[i], SceneLayout.DrawOrder(sea, i), $"layer {sea[i].n}");
            var plain = SceneLayout.Parse("{\"layers\":[{\"n\":0},{\"n\":2},{\"n\":4}]}").layers;
            for (int i = 0; i < plain.Length; i++) Assert.AreEqual(plain[i].n, SceneLayout.DrawOrder(plain, i), "no draw_before: by n");
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

                // U-205 (B-225): the set's json now carries five layers. The surface seen from below (layer3) is 2 m tall with its top on the
                // water line; the shallow seabed (layer4: shore_m 40, draw_before 3) shows by the shore only, under layer3 and over the seabeds.
                var seaSet = stage.SeaUnder;
                Assert.AreEqual(5, seaSet.Layout.layers.Length, "sea_under's five layers (B-225)");
                SpriteRenderer LayerOf(int n) { for (int i = 0; i < seaSet.Layout.layers.Length; i++) if (seaSet.Layout.layers[i].n == n) return seaSet.renderers[i]; return null; }
                var surface = LayerOf(3); var shallows = LayerOf(4);
                Assert.NotNull(surface); Assert.NotNull(shallows);
                Assert.AreEqual(2f, surface.size.y, 0.01f, "the surface seen from below is 128 px: a light ceiling 2 m deep");
                Assert.AreEqual(water, surface.bounds.max.y, 0.05f, "its top row on the water line");
                Assert.AreEqual(ParallaxLayers.BackOrder + CartoonStage.SeaUnderOrder + 3, shallows.sortingOrder, "the shallow seabed over the near seabed");
                Assert.AreEqual(ParallaxLayers.BackOrder + CartoonStage.SeaUnderOrder + 4, surface.sortingOrder, "the surface layer over the shallow seabed");
                Assert.AreEqual(ParallaxLayers.BackOrder + CartoonStage.SeaUnderOrder + 2, LayerOf(2).sortingOrder, "the near seabed where it was");
                int first = os - 12;
                while (first < os + len && !gen.SeaAt(first)) first++;
                Assert.IsTrue(gen.SeaAt(first) && !gen.SeaAt(first - 1), "the shore's first sea column");
                // A body held with its physics off keeps its last grounded flag, and the stage camera frames the floor under a grounded
                // surveyor: over deep water that is the seabed far below, not the swimmer. These holds put the camera on the swimmer
                // (1.5 m over it, as it follows one in play), since the shallow seabed now fades with the camera's depth.
                IEnumerator HoldSwim(Vector2 at)
                {
                    yield return Hold(at);
                    if (follow != null) follow.enabled = false;
                    cam.transform.position = new Vector3(at.x, at.y + 1.5f, cam.transform.position.z);
                    for (int i = 0; i < 30; i++) yield return null;
                }
                // 10 m out, 3 m under: whole
                yield return HoldSwim(new Vector2(first + 10.5f, water - 3f));
                TestContext.Out.WriteLine($"[MERIDIAN] u205 shallows at {first} + 10.5: shore distance {stage.ShoreDistanceNow:0.00} m, layer4 alpha {seaSet.LayerAlphaOf(4):0.00} x the set's {seaSet.alpha:0.00}, drawn {shallows.enabled}, colour a {shallows.color.a:0.00}");
                Assert.AreEqual(10.5f, stage.ShoreDistanceNow, 0.01f);
                Assert.AreEqual(1f, seaSet.LayerAlphaOf(4), 1e-4f, "the shallow seabed whole 10 m out");
                Assert.IsTrue(shallows.enabled, "drawn");
                Assert.AreEqual(seaSet.alpha, shallows.color.a, 0.01f);
                Assert.IsFalse(seaSet.placeholders.Contains(true), "all five layers' art in (layer4 imported)");
                // LEAD 11-09 23:0x (u205/3_sea_10m: a flat sand wall behind the surveyor): by the shore but deep, the camera well under the
                // layer's painted ground line: the shallow seabed is not drawn
                Assert.IsFalse(float.IsNaN(stage.ShallowsGroundY), "the shallow seabed's ground line is placed");
                Assert.GreaterOrEqual(cam.transform.position.y, stage.ShallowsGroundY + CartoonStage.ShallowsDepthFade, "3 m under, the camera on the swimmer is 2 m or more over the layer's ground line");
                yield return HoldSwim(new Vector2(first + 19.5f, water - 12f));
                TestContext.Out.WriteLine($"[MERIDIAN] u205 shallows 19.5 m out, 12 m under: the camera at {cam.transform.position.y - water:0.0} m, the layer's ground line at {stage.ShallowsGroundY - water:0.0} m, layer4 alpha {seaSet.LayerAlphaOf(4):0.00}, drawn {shallows.enabled}");
                Assert.Less(cam.transform.position.y, stage.ShallowsGroundY, "the camera under the layer's ground line");
                Assert.AreEqual(0f, seaSet.LayerAlphaOf(4), 1e-4f, "deep by the shore: the shallow seabed is gone");
                Assert.IsFalse(shallows.enabled, "and not drawn");
                // 36 m out: fading
                yield return HoldSwim(new Vector2(first + 36f, water - 3f));
                Assert.AreEqual(36f, stage.ShoreDistanceNow, 0.01f);
                Assert.AreEqual(0.5f, seaSet.LayerAlphaOf(4), 0.01f, "half gone 36 m out");
                Assert.AreEqual(seaSet.alpha * 0.5f, shallows.color.a, 0.02f);
                // 45 m out: not drawn at all, nor its continued strip
                yield return HoldSwim(new Vector2(first + 45.5f, water - 3f));
                TestContext.Out.WriteLine($"[MERIDIAN] u205 shallows at {first} + 45.5: shore distance {stage.ShoreDistanceNow:0.00} m, layer4 alpha {seaSet.LayerAlphaOf(4):0.00}, drawn {shallows.enabled}");
                Assert.Greater(stage.ShoreDistanceNow, 40f);
                Assert.AreEqual(0f, seaSet.LayerAlphaOf(4), 1e-4f, "gone past 40 m");
                Assert.IsFalse(shallows.enabled, "not drawn out at sea");
                int shallowOrder = ParallaxLayers.BackOrder + CartoonStage.SeaUnderOrder + 3;
                foreach (var r in seaSet.GetComponentsInChildren<SpriteRenderer>()) if (r.enabled) Assert.AreNotEqual(shallowOrder, r.sortingOrder, $"{r.name}: nothing of the shallow seabed draws out at sea");
                if (follow != null) follow.enabled = true;

                // the shore above the water: untouched
                int shore = os - 12;
                yield return Hold(new Vector2(shore + 0.5f, side.terrain.SurfaceAt(shore + 0.5f) + 0.5f));
                Assert.AreEqual(0f, stage.SeaWeight, 1e-4f, "on land");
                Assert.AreEqual(1f, stage.Layers.nearAlpha, 1e-4f, "the land set whole");
                Assert.IsFalse(stage.SeaUnder.gameObject.activeSelf, "sea_under draws nothing");

                // smoke_43's frame (3 m under, off the shore's steep slope): no back-wall triangle stands over its column's surface curve (LEAD's
                // read: a 1 m wedge of wall poked out of the slope into the water where the curve crossed a chunk's bottom edge).
                int swim = os + 16;
                for (int x = os + 16; x < os + 400; x++) if (gen.SurfaceHeight(x) <= side.Config.datumY - 4) { swim = x; break; }
                yield return Hold(new Vector2(swim + 0.5f, water - 3f));
                int backTris = 0;
                foreach (var chunk in Object.FindObjectsByType<TerrainChunk>())
                {
                    MeshFilter mf = null;
                    foreach (var f in chunk.GetComponentsInChildren<MeshFilter>()) if (f.name == "SmoothGround") mf = f;
                    if (mf == null || mf.sharedMesh == null || mf.sharedMesh.subMeshCount == 0) continue;
                    var vs = mf.sharedMesh.vertices;
                    var tri = mf.sharedMesh.GetTriangles(0); // SmoothGround's submesh 0: the back wall
                    float wy0 = chunk.cy * TerrainConstants.ChunkSize;
                    for (int t = 0; t < tri.Length; t += 3)
                    {
                        Vector3 mid = (vs[tri[t]] + vs[tri[t + 1]] + vs[tri[t + 2]]) / 3f;
                        float fi = mid.x + 0.5f;
                        int i = Mathf.Clamp(Mathf.FloorToInt(fi), 0, TerrainConstants.ChunkSize - 1);
                        float a = chunk.SurfaceCurve[i], b = chunk.SurfaceCurve[i + 1];
                        if (float.IsNaN(a) || float.IsNaN(b)) continue;
                        float curve = Mathf.Lerp(a, b, Mathf.Clamp01(fi - i)) - wy0;
                        Assert.LessOrEqual(mid.y, curve + 0.02f, $"chunk ({chunk.cx}, {chunk.cy}): a back-wall triangle at local ({mid.x:0.00}, {mid.y:0.00}) over the curve ({curve:0.00})");
                        backTris++;
                    }
                }
                TestContext.Out.WriteLine($"[MERIDIAN] u171 smoke_43 frame at {swim}: {backTris} back-wall triangles, all under the curve");
                Assert.Greater(backTris, 0, "the shore's chunks laid a back wall (the sea's columns)");
                // ...and the sea's tint fades into the shore along the datum row (LEAD's read: it stopped on a box edge): from the last water cell
                // inland, each step drops at most 1/(ShoreFade + 1) of the water's alpha
                const int C = TerrainConstants.ChunkSize;
                int datum = side.Config.datumY;
                float TintAt(int x)
                {
                    int cx = Mathf.FloorToInt((float)x / C), cy = Mathf.FloorToInt((float)datum / C);
                    foreach (var chunk in Object.FindObjectsByType<TerrainChunk>())
                    {
                        if (chunk.cx != cx || chunk.cy != cy) continue;
                        foreach (var tm in chunk.GetComponentsInChildren<UnityEngine.Tilemaps.Tilemap>())
                        {
                            if (tm.name != "Liquid") continue;
                            var cell = new Vector3Int(x - cx * C, datum - cy * C, 0);
                            return tm.HasTile(cell) ? tm.GetColor(cell).a : 0f;
                        }
                    }
                    return -1f;
                }
                int edge = swim;
                while (edge > swim - 40 && side.terrain.GetTile(edge - 1, datum) == TileId.Water) edge--;
                Assert.Less(edge, swim, "water on the datum row at the swim column");
                var ramp = new System.Text.StringBuilder();
                float prev = TintAt(edge);
                Assert.AreEqual(1f, prev, 1e-3f, "the last water cell whole");
                for (int x = edge - 1; x >= edge - TerrainChunk.ShoreFade - 2; x--)
                {
                    float a = TintAt(x);
                    ramp.Append($" {a:0.00}");
                    Assert.GreaterOrEqual(a, 0f, $"x {x}: its chunk resident");
                    Assert.LessOrEqual(prev - a, 1f / (TerrainChunk.ShoreFade + 1f) + 0.01f, $"x {x}: the tint steps from {prev:0.00} to {a:0.00}");
                    prev = a;
                }
                TestContext.Out.WriteLine($"[MERIDIAN] u171 the shore's tint inland from the water's edge at {edge}:{ramp}");
                player.Body.simulated = true;
                LogAssert.NoUnexpectedReceived();
            }
            finally { CartoonStage.Enabled = was; }
        }
    }
}
