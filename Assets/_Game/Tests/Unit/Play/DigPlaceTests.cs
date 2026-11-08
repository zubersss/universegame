using System.Collections;
using System.IO;
using Meridian.Core;
using Meridian.Planets;
using Meridian.Rig;
using Meridian.Terrain;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace Meridian.Tests
{
    /// <summary>
    /// U-008, rewritten for U-157 (D-162 (2), (3), (6); D-165): on Earth's smooth ground the Beam carves a round scoop (every solid tile within
    /// the brush, each dropping its item; the traced outline sinks into a rounded hole) and the Builder piles a round mound of the planet's
    /// ground material, spending one carried ground item per tile with no block chosen, and never over a body; both persist through save → load.
    /// </summary>
    public class DigPlaceTests
    {
        const string CorePath = "Assets/_Game/Scenes/Core.unity";

        static IEnumerator Boot(System.Action<PlanetSideRoot> done)
        {
#if UNITY_EDITOR
            yield return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode(
                CorePath, new LoadSceneParameters(LoadSceneMode.Single));
#else
            yield return SceneManager.LoadSceneAsync("Core", LoadSceneMode.Single);
#endif
            var director = Object.FindAnyObjectByType<SceneDirector>();
            float timeout = Time.realtimeSinceStartup + 10f;
            while (!director.IsReady && Time.realtimeSinceStartup < timeout) yield return null;
            Assert.IsTrue(director.IsReady);
            yield return Settle(director.PlanetSide.terrain);
            done(director.PlanetSide);
        }

        static IEnumerator Settle(TerrainStreamer t)
        {
            float timeout = Time.realtimeSinceStartup + 20f;
            while (!t.IsSettled && Time.realtimeSinceStartup < timeout) yield return null;
            Assert.IsTrue(t.IsSettled, "terrain settled");
        }

        /// <summary>The outline's height under world x (the chunks' edge colliders), from `from` down.</summary>
        static float Outline(float x, float from)
        {
            foreach (var h in Physics2D.RaycastAll(new Vector2(x, from), Vector2.down, 20f))
                if (h.collider is EdgeCollider2D && h.collider.GetComponent<TerrainChunk>() != null) return h.point.y;
            return float.NaN;
        }

        [UnityTest]
        public IEnumerator TheBrushDigsARoundScoopPilesAMoundAndBothPersist()
        {
            PlanetSideRoot side = null;
            yield return Boot(s => side = s);
            var t = side.terrain;
            var rig = side.rig;
            Assert.NotNull(rig, "Rig on PlanetSide");
            Assert.IsTrue(rig.Brush, "Earth's Rig works the round brush (D-162)");
            side.creatures.autoSpawn = false;
            side.creatures.DespawnAll();

            // The scoop: a stroke aimed at the ground on a column seam, 3 m from the surveyor (both columns' top tiles in the brush). D-168: the
            // disc is exact, so it must reach the surface to open it (aimed 1.1 m under it, it leaves a 0.2 m roof: a buried bubble).
            int x = side.spawnX - 3, top = t.TopSolidY(x);
            var p = new Vector2(x, t.SurfaceAt(x) - 0.25f);
            var cells = RigTools.BrushCells(p);
            int solid = 0;
            foreach (var c in cells) if (TileId.IsSolid(t.GetTile(c.x, c.y))) solid++;
            Assert.Greater(solid, 1, "the stroke covers more than one solid tile");
            float before = Outline(x, top + 4f);
            int drops = rig.drops.Live.Count;
            Assert.IsTrue(rig.Dig(p), "the Beam carves");
            foreach (var c in cells) Assert.AreEqual(TileId.Air, t.GetTile(c.x, c.y), $"tile {c} carved");
            Assert.GreaterOrEqual(rig.drops.Live.Count - drops, solid, "one item per carved tile (plus any only-here bonus)");
            yield return new WaitForFixedUpdate();
            float after = Outline(x, top + 4f);
            TestContext.Out.WriteLine($"[MERIDIAN] u157 scoop: {cells.Count} tiles in the brush, {solid} carved, outline {before:F2} → {after:F2}");
            Assert.Less(after, before - 0.5f, "the traced ground sinks into the scoop");

            // The mound: no block is chosen; the Builder spends carried ground items, one per tile, and piles the ground material.
            var inv = GameState.Instance.inventory;
            inv.Clear();
            int soil = Meridian.Items.ItemRegistry.DropOf(TileId.Soil);
            inv.Add(soil, 10);
            Assert.AreEqual(TileId.Soil, rig.GroundMaterial, "Earth's ground material");
            Assert.AreEqual(TileId.Soil, rig.SelectedTile, "the Builder's material while ground items are carried, whatever slot is selected");
            int mx = side.spawnX + 4, mtop = t.TopSolidY(mx); // within the Rig's 5 m reach, clear of the Pilgrim
            var m = new Vector2(mx, mtop + 1f); // a tile corner on the ground: the open tiles round it
            var open = RigTools.BrushCells(m);
            Assert.IsTrue(rig.Place(m), "the Builder piles a mound");
            int filled = 0;
            foreach (var c in open) if (t.GetTile(c.x, c.y) == TileId.Soil) filled++;
            Assert.Greater(filled, 0, "earth piled");
            Assert.AreEqual(10 - filled, inv.Count(soil), "one ground item per piled tile");

            // D-165: a stroke at the surveyor's chest leaves every cell the surveyor stands in open, and spends only for what it piled.
            var at = side.player.Body.position + new Vector2(0f, 0.9f);
            var near = RigTools.BrushCells(at);
            var was = near.ConvertAll(c => t.GetTile(c.x, c.y));
            int carried = inv.Count(soil), bodyCells = 0, changed = 0;
            rig.Place(at);
            for (int i = 0; i < near.Count; i++)
            {
                var c = near[i];
                bool body = false;
                foreach (var hit in Physics2D.OverlapBoxAll(new Vector2(c.x + 0.5f, c.y + 0.5f), Vector2.one * 0.9f, 0f))
                    if (hit.attachedRigidbody == side.player.Body) body = true;
                byte now = t.GetTile(c.x, c.y);
                if (now != was[i]) changed++;
                if (body) { bodyCells++; Assert.AreEqual(was[i], now, $"no earth piled into the surveyor at {c}"); }
            }
            Assert.Greater(bodyCells, 0, "the stroke reached the surveyor");
            Assert.AreEqual(changed, carried - inv.Count(soil), "spent only for what was piled");

            // Save the diffs, start a fresh session, load them, rebuild the planet.
            var path = Path.Combine(Application.temporaryCachePath, "meridian_test", "terrain_earth.bin");
            t.Edits.SaveFile(path);
            yield return Boot(s => side = s);
            t = side.terrain;
            Assert.IsTrue(TileId.IsSolid(t.GetTile(cells[0].x, cells[0].y)), "a fresh session starts from the seed");
            GameState.Instance.EditsFor(PlanetId.Earth).LoadFile(path);
            side.Configure(side.Config);
            yield return Settle(t);
            foreach (var c in cells) Assert.AreEqual(TileId.Air, t.GetTile(c.x, c.y), $"the scoop's tile {c} still carved after load");
            Assert.Greater(open.FindAll(c => t.GetTile(c.x, c.y) == TileId.Soil).Count, 0, "the mound still there after load");
            File.Delete(path);
            LogAssert.NoUnexpectedReceived();
        }

        /// <summary>
        /// U-157 P-54 (D-167 (4)): dug walls are round at any size, not only a lone scoop. A 4 m tunnel of strokes on the tile centres and a second,
        /// off-grid row above it make one hole of seven strokes; every outline point round it (the chunks' edge chains, under the surface band)
        /// lies within BrushRadius ± 0.10 m of its nearest stroke centre (D-168: the strokes' discs held at the quarter-metre sub-nodes). Without the fill levels the walls follow the 1 m tile faces (a
        /// lone stroke's wall at 0.5 m, a stack's straight faces on the column lines), far outside that band.
        /// </summary>
        [UnityTest]
        public IEnumerator DugWallsAreRoundAtAnySize()
        {
            PlanetSideRoot side = null;
            yield return Boot(s => side = s);
            var t = side.terrain;
            var rig = side.rig;
            Assert.IsTrue(rig.Brush);
            int x0 = side.spawnX + 30;
            for (int k = 0; k < 80; k++, x0++)
            {
                bool clear = true;
                for (int c = x0 - 2; c <= x0 + 6; c++) if (t.PadTop(c) != int.MinValue || t.GetTile(c, t.OriginalTop(c) + 1) == TileId.Water) clear = false;
                if (clear) break;
            }
            int top = t.OriginalTop(x0);
            var strokes = new System.Collections.Generic.List<Vector2>();
            for (int i = 0; i < 4; i++) strokes.Add(new Vector2(x0 + 0.5f + i, top - 3.5f));
            for (int i = 0; i < 3; i++) strokes.Add(new Vector2(x0 + 0.8f + i * 0.7f, top - 2.4f));
            var owner = rig.owner;
            rig.owner = null;
            try { foreach (var p in strokes) rig.Dig(p); }
            finally { rig.owner = owner; }
            yield return new WaitForFixedUpdate();
            yield return null;
            float lo = float.MaxValue, hi = 0f; int n = 0;
            foreach (var chunk in Object.FindObjectsByType<TerrainChunk>())
                foreach (var e in chunk.GetComponents<EdgeCollider2D>())
                {
                    var pts = e.points;
                    for (int k = 0; k < pts.Length; k++)
                    {
                        var w = (Vector2)e.transform.TransformPoint(pts[k] + e.offset);
                        if (w.y > top - 1f || w.x < x0 - 3f || w.x > x0 + 7f) continue;
                        float d = float.MaxValue;
                        foreach (var p in strokes) d = Mathf.Min(d, (w - p).magnitude);
                        if (d > RigTools.BrushRadius + 0.6f) continue;
                        lo = Mathf.Min(lo, d); hi = Mathf.Max(hi, d); n++;
                    }
                }
            TestContext.Out.WriteLine($"[MERIDIAN] p54 hole at x {x0}, top {top}: {n} outline points, nearest-stroke distance {lo:F3}..{hi:F3} m (brush {RigTools.BrushRadius})");
            Assert.Greater(n, 16, "the hole's outline traced");
            Assert.GreaterOrEqual(lo, RigTools.BrushRadius - 0.10f, "no wall pulled in onto a tile face");
            Assert.LessOrEqual(hi, RigTools.BrushRadius + 0.10f, "no wall left standing out on a tile face");
            LogAssert.NoUnexpectedReceived();
        }

        /// <summary>
        /// U-157 (D-168): one Beam stroke off the grid, deep in natural ground, traces a circle: in each of 16 directions round the stroke the
        /// outline (the chunks' edge chains, what draws and collides) lies within BrushRadius ± 0.06 m of its centre.
        /// </summary>
        [UnityTest]
        public IEnumerator AStrokeIsRoundInSixteenDirections()
        {
            PlanetSideRoot side = null;
            yield return Boot(s => side = s);
            var t = side.terrain;
            var rig = side.rig;
            // Solid rock all round (no natural cavity within 2 m: the 10:4x run met one 1.28 m off), off the grid.
            int x0 = side.spawnX + 30;
            for (int k = 0; k < 80 && t.PadTop(x0) != int.MinValue; k++) x0++;
            var p = new Vector2(x0 + 0.37f, t.OriginalTop(x0) - 4.3f);
            for (int tries = 0; tries < 40; tries++)
            {
                bool rock = true;
                for (int k = 0; k < 24 && rock; k++)
                    for (float r = 0f; r <= 2f && rock; r += 0.25f)
                        rock = t.FieldAt(p + r * new Vector2(Mathf.Cos(k * Mathf.PI / 12f), Mathf.Sin(k * Mathf.PI / 12f))) >= 0.9f;
                if (rock) break;
                p += tries % 2 == 0 ? new Vector2(0f, -1.13f) : new Vector2(2.71f, 1.13f);
            }
            var owner = rig.owner;
            rig.owner = null;
            try { Assert.IsTrue(rig.Dig(p), "the stroke carves"); }
            finally { rig.owner = owner; }
            yield return new WaitForFixedUpdate();
            yield return null;
            var best = new float[16];
            var bestAngle = new float[16];
            for (int k = 0; k < 16; k++) { best[k] = float.NaN; bestAngle[k] = float.MaxValue; }
            int n = 0;
            foreach (var chunk in Object.FindObjectsByType<TerrainChunk>())
                foreach (var e in chunk.GetComponents<EdgeCollider2D>())
                {
                    var pts = e.points;
                    for (int k = 0; k < pts.Length; k++)
                    {
                        var w = (Vector2)e.transform.TransformPoint(pts[k] + e.offset);
                        var v = w - p;
                        if (v.magnitude > RigTools.BrushRadius + RigTools.BrushRamp) continue; // past the disc's ramp the stroke changes nothing
                        n++;
                        float d = v.magnitude;
                        Assert.AreEqual(RigTools.BrushRadius, d, 0.06f, $"outline point ({w.x:F3}, {w.y:F3}) at {Mathf.Atan2(v.y, v.x) * Mathf.Rad2Deg:F0}°");
                        float ang = Mathf.Repeat(Mathf.Atan2(v.y, v.x) * Mathf.Rad2Deg, 360f);
                        int dir = Mathf.RoundToInt(ang / 22.5f) % 16;
                        float off = Mathf.Abs(Mathf.DeltaAngle(ang, dir * 22.5f));
                        if (off < bestAngle[dir]) { bestAngle[dir] = off; best[dir] = d; }
                    }
                }
            var line = new System.Text.StringBuilder();
            for (int k = 0; k < 16; k++)
            {
                Assert.IsFalse(float.IsNaN(best[k]), $"an outline point toward {k * 22.5f}°");
                line.Append($" {k * 22.5f:F0}°:{best[k]:F3}");
            }
            TestContext.Out.WriteLine($"[MERIDIAN] d168 stroke at ({p.x:F2}, {p.y:F2}): {n} outline points; radius by direction{line}");
            LogAssert.NoUnexpectedReceived();
        }
    }
}
