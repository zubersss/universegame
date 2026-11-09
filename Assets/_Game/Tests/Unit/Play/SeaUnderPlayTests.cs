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
