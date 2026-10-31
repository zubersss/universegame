using System.Linq;
using Meridian.EditorTools;
using Meridian.Planets;
using Meridian.Terrain;
using NUnit.Framework;
using UnityEditor;

namespace Meridian.Tests
{
    /// <summary>U-007: world generation, wrapping and autotiling (EditMode, no scene).</summary>
    public class TerrainTests
    {
        static PlanetConfig Load(PlanetId id) =>
            AssetDatabase.LoadAssetAtPath<PlanetConfig>($"{PlanetConfigAuthoring.Folder}/{id}.asset");

        [Test]
        public void BlobTableHas47CanonicalVariants()
        {
            var indices = Enumerable.Range(0, 256).Select(m => (int)BlobAutotile.Index(m)).Distinct().ToList();
            Assert.AreEqual(47, indices.Count);
            Assert.AreEqual(0, BlobAutotile.Index(0), "isolated tile");
            Assert.AreEqual(46, BlobAutotile.Index(0xFF), "fully surrounded tile");
            // A corner without both edges is ignored.
            Assert.AreEqual(BlobAutotile.Index(BlobAutotile.N), BlobAutotile.Index(BlobAutotile.N | BlobAutotile.NE));
        }

        [TestCase(PlanetId.Earth)]
        [TestCase(PlanetId.Mars)]
        public void GenerationIsDeterministic(PlanetId id)
        {
            var c = Load(id);
            var a = new SolidWorldGenerator(c, 42);
            var b = new SolidWorldGenerator(c, 42);
            var other = new SolidWorldGenerator(c, 43);
            bool differs = false;
            for (int x = 0; x < c.worldWidth; x += 37)
            for (int y = 0; y < c.worldHeight; y += 23)
            {
                Assert.AreEqual(a.TileAt(x, y), b.TileAt(x, y));
                differs |= a.TileAt(x, y) != other.TileAt(x, y);
            }
            Assert.IsTrue(differs, "a different seed gives a different world");
        }

        [TestCase(PlanetId.Earth)]
        [TestCase(PlanetId.Mars)]
        public void SurfaceStaysNearDatumAndWrapsSmoothly(PlanetId id)
        {
            var c = Load(id);
            var g = new SolidWorldGenerator(c, 1969);
            for (int x = 0; x < c.worldWidth; x++)
            {
                int h = g.SurfaceHeight(x);
                // Earth: down to the ocean trench (≥ 120 m deep, D-010 water to 250; U-037), up to tundra/taiga hills.
                int low = id == PlanetId.Earth ? c.datumY - 250 : c.datumY - 40, high = id == PlanetId.Earth ? c.datumY + 50 : c.datumY + 40;
                Assert.That(h, Is.InRange(low, high), $"x={x}");
                int next = g.SurfaceHeight((x + 1) % c.worldWidth);
                Assert.LessOrEqual(System.Math.Abs(next - h), 3, $"cliff between x={x} and the next column (wrap included)");
            }
        }

        [Test]
        public void EarthHasSeaBelowDatumAndGrassOrSandOnTop()
        {
            var c = Load(PlanetId.Earth);
            var g = new SolidWorldGenerator(c, 1969);
            int water = 0;
            for (int x = 0; x < c.worldWidth; x++)
            {
                int h = g.SurfaceHeight(x);
                var top = g.TileAt(x, h);
                Assert.That(new[] { TileId.Grass, TileId.Sand, TileId.Snow }, Has.Member(top), $"top tile at x={x}");
                if (h < c.datumY) { Assert.AreEqual(TileId.Water, g.TileAt(x, c.datumY)); water++; }
                Assert.AreEqual(TileId.Air, g.TileAt(x, c.datumY + 60));
            }
            Assert.Greater(water, 0, "some ocean exists");
        }

        [Test]
        public void ChunkDataWrapsAcrossTheSeam()
        {
            var c = Load(PlanetId.Earth);
            var g = new SolidWorldGenerator(c, 1969);
            int last = c.worldWidth / TerrainConstants.ChunkSize - 1;
            var wrapped = ChunkBuffer.Rent(-1, 10); wrapped.Generate(g);
            var real = ChunkBuffer.Rent(last, 10); real.Generate(g);
            CollectionAssert.AreEqual(real.ids, wrapped.ids);
            CollectionAssert.AreEqual(real.blob, wrapped.blob);
            ChunkBuffer.Return(wrapped); ChunkBuffer.Return(real);
        }

        [Test]
        public void AutotileSeesNeighborChunkAcrossTheBorder()
        {
            var c = Load(PlanetId.Earth);
            var g = new SolidWorldGenerator(c, 1969);
            const int C = TerrainConstants.ChunkSize;
            var left = ChunkBuffer.Rent(3, 9); left.Generate(g);
            var right = ChunkBuffer.Rent(4, 9); right.Generate(g);
            int checkedTiles = 0;
            for (int y = 0; y < C; y++)
            {
                byte a = left.ids[y * C + C - 1], b = right.ids[y * C];
                if (!TileId.IsSolid(a)) continue;
                bool eastBit = (BlobAutotile.MaskOfIndex[left.blob[y * C + C - 1]] & BlobAutotile.E) != 0;
                Assert.AreEqual(TileId.IsSolid(b), eastBit, $"row {y}");
                checkedTiles++;
            }
            Assert.Greater(checkedTiles, 0);
            ChunkBuffer.Return(left); ChunkBuffer.Return(right);
        }
    }
}
