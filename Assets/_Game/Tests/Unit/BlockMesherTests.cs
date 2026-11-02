using Meridian.Terrain;
using NUnit.Framework;
using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>U-073 (EditMode): the chunk block mesher (Bible 2.0 §10.4): exposed faces only, greedy merging, winding, back wall, budget.</summary>
    public class BlockMesherTests
    {
        const int C = BlockMesher.C;
        readonly BlockMesher.Buffers buf = new BlockMesher.Buffers();

        static byte[] Empty() => new byte[C * C];
        static byte[] Full(byte id) { var a = new byte[C * C]; for (int i = 0; i < a.Length; i++) a[i] = id; return a; }

        int Build(byte[] ids, byte outsideTile = TileId.Air, int wallTop = -1)
        {
            BlockMesher.Build(ids, (x, y) => outsideTile, _ => wallTop, 0, 0, buf);
            return buf.Quads;
        }

        [Test]
        public void OneBlockShowsFrontAndFourSidesOnly()
        {
            var ids = Empty();
            ids[10 * C + 10] = TileId.Stone;
            Assert.AreEqual(5, Build(ids), "front + top + bottom + left + right; no back face");
        }

        [Test]
        public void SolidChunkIsOneFrontQuadWhenBuriedAndFiveWhenAlone()
        {
            Assert.AreEqual(1, Build(Full(TileId.Stone), TileId.Stone), "buried: only the merged front");
            Assert.AreEqual(5, Build(Full(TileId.Stone), TileId.Air), "alone: front + one merged run per edge");
        }

        [Test]
        public void MaterialsDontMergeAndTopsWearTheTopLayer()
        {
            var ids = Full(TileId.Soil);
            for (int x = 0; x < C; x++) ids[(C - 1) * C + x] = TileId.Grass; // grass row on top
            // Solid all around except open sky above the chunk.
            BlockMesher.Build(ids, (x, y) => y >= C ? TileId.Air : TileId.Soil, _ => -1, 0, 0, buf);
            int fronts = 0, tops = 0;
            for (int q = 0; q < buf.Quads; q++)
            {
                var n = buf.normals[q * 4];
                if (n == Vector3.back) fronts++;
                if (n == Vector3.up) { tops++; Assert.AreEqual(BlockMesher.TopLayer(TileId.Grass), buf.uv[q * 4].z, "the top face wears grass's top layer"); }
            }
            Assert.AreEqual(2, fronts, "soil body and grass row stay separate rectangles");
            Assert.AreEqual(1, tops, "one merged top run along the grass");
            Assert.AreEqual(3, buf.Quads, "nothing else is exposed");
        }

        [Test]
        public void KnownPatternFaceCount()
        {
            // Ground of soil 0..9 with a grass top row 10, a 3-wide dug hole at x 5..7 rows 8..10 — buried under solid outside.
            var ids = Empty();
            for (int y = 0; y <= 10; y++) for (int x = 0; x < C; x++) ids[y * C + x] = y == 10 ? TileId.Grass : TileId.Soil;
            for (int y = 8; y <= 10; y++) for (int x = 5; x <= 7; x++) ids[y * C + x] = TileId.Air;
            BlockMesher.Build(ids, (x, y) => y < 0 || (y <= 10 && (x < 0 || x >= C)) ? TileId.Soil : TileId.Air, _ => 10, 0, 0, buf);
            int fronts = 0, tops = 0, sides = 0, walls = 0;
            for (int q = 0; q < buf.Quads; q++)
            {
                var n = buf.normals[q * 4];
                float z = buf.vertices[q * 4].z;
                if (n == Vector3.back && z > 0f) walls++;
                else if (n == Vector3.back) fronts++;
                else if (n == Vector3.up) tops++;
                else sides++;
            }
            TestContext.Out.WriteLine($"[MERIDIAN] pattern: {buf.Quads} quads (front {fronts}, top {tops}, sides/bottom {sides}, wall {walls})");
            // Tops: grass x 0..4 and 8..31 (2 runs) + the hole floor (soil row 7 under x 5..7: 1 run) = 3.
            Assert.AreEqual(3, tops, "top runs");
            // Sides: the hole's two walls (x 4 right face, x 8 left face), rows 8..10; each is soil (8–9) then grass (10),
            // and runs break on a material change ⇒ 2 runs per wall. Nothing else is exposed sideways or below.
            Assert.AreEqual(4, sides, "hole walls (soil + grass run each)");
            // Back wall: the 3 hole columns, one run each (rows 8..10 are open and at or below the wall top 10).
            Assert.AreEqual(3, walls, "back wall behind the dug cells");
            Assert.LessOrEqual(fronts, 6, "greedy front rectangles");
        }

        [Test]
        public void EveryTriangleFacesAlongItsNormal()
        {
            var ids = Empty();
            for (int y = 0; y < 12; y++) for (int x = 3; x < 20; x++) if ((x + y) % 5 != 0) ids[y * C + x] = (byte)(TileId.Soil + (x / 6));
            BlockMesher.Build(ids, (x, y) => TileId.Air, _ => 12, 0, 0, buf);
            Assert.Greater(buf.Quads, 10);
            var t = buf.triangles; var v = buf.vertices;
            for (int i = 0; i < t.Count; i += 3)
            {
                var a = v[t[i]]; var b = v[t[i + 1]]; var c = v[t[i + 2]];
                var face = Vector3.Cross(b - a, c - a).normalized;
                var n = buf.normals[t[i]];
                Assert.Greater(Vector3.Dot(face, n), 0.99f, $"triangle {i / 3}: winding {face} vs normal {n}");
            }
        }

        [Test]
        public void UvLayersFollowTheMaterial()
        {
            var ids = Empty();
            ids[0] = TileId.Grass;
            BlockMesher.Build(ids, (x, y) => TileId.Air, _ => -1, 0, 0, buf);
            bool topSeen = false;
            for (int q = 0; q < buf.Quads; q++)
            {
                float layer = buf.uv[q * 4].z;
                if (buf.normals[q * 4] == Vector3.up) { topSeen = true; Assert.AreEqual(BlockMesher.TopLayer(TileId.Grass), layer); }
                else Assert.AreEqual(BlockMesher.SideLayer(TileId.Grass), layer);
            }
            Assert.IsTrue(topSeen);
            Assert.AreEqual(TileId.Count * 2 + 1, BlockMesher.LayerCount);
        }

        [Test]
        public void ChunkRebuildFitsTheBudget()
        {
            // D-019: a dig rebuilds one chunk within the frame; ≤ 2 ms main thread. A noisy worst-ish pattern.
            var ids = Empty();
            var rng = new System.Random(7);
            for (int i = 0; i < ids.Length; i++) ids[i] = rng.NextDouble() < 0.6 ? (byte)(1 + rng.Next(4)) : TileId.Air;
            BlockMesher.Build(ids, (x, y) => TileId.Stone, _ => C - 1, 0, 0, buf); // warm-up
            var sw = System.Diagnostics.Stopwatch.StartNew();
            const int runs = 50;
            for (int r = 0; r < runs; r++) BlockMesher.Build(ids, (x, y) => TileId.Stone, _ => C - 1, 0, 0, buf);
            double ms = sw.Elapsed.TotalMilliseconds / runs;
            TestContext.Out.WriteLine($"[MERIDIAN] block mesh (noisy chunk): {ms:F3} ms, {buf.Quads} quads");
            Assert.Less(ms, 2.0, "≤ 2 ms per chunk rebuild");
        }
    }
}
