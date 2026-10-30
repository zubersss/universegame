using System.Collections.Generic;
using System.Linq;
using Meridian.Terrain;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.Tilemaps;

namespace Meridian.Tests
{
    /// <summary>U-020 (EditMode): interior tile variants (D-020) are stable, spread, and absent without art.</summary>
    public class TerrainVariantTests
    {
        readonly List<Object> created = new List<Object>();

        [TearDown]
        public void TearDown()
        {
            foreach (var o in created) if (o != null) Object.DestroyImmediate(o);
            created.Clear();
        }

        List<Sprite> Sheet(int cells)
        {
            var list = new List<Sprite>();
            for (int i = 0; i < cells; i++)
            {
                var s = Sprite.Create(Texture2D.whiteTexture, new Rect(0, 0, 4, 4), new Vector2(0.5f, 0.5f), 4f);
                s.name = "soil_" + i;
                created.Add(s);
                list.Add(s);
            }
            return list;
        }

        [Test]
        public void HashIsStableAndWrapsWithTheWorld()
        {
            const int width = 4096;
            for (int x = 0; x < 200; x += 7)
            for (int y = 280; y < 340; y += 3)
            {
                int a = TerrainTileSet.VariantPick(x, y, 17);
                Assert.AreEqual(a, TerrainTileSet.VariantPick(x, y, 17), "same input, same pick");
                Assert.AreEqual(a, TerrainTileSet.VariantPick(((x + width) % width + width) % width, y, 17), "wrapped column");
            }
        }

        [Test]
        public void PicksSpreadOverAllOptions()
        {
            var counts = new int[17];
            for (int x = 0; x < 256; x++)
            for (int y = 0; y < 64; y++)
                counts[TerrainTileSet.VariantPick(x, y, 17)]++;
            float expected = 256 * 64 / 17f;
            foreach (var c in counts) Assert.That(c, Is.InRange(expected * 0.8f, expected * 1.2f), "each of tile 46 + 16 variants is used about equally");
        }

        [Test]
        public void SheetWithoutVariantsAlwaysDrawsTile46()
        {
            var set = new TerrainTileSet();
            set.LoadFromSprites(TileId.Soil, Sheet(47));
            Assert.AreEqual(0, set.InteriorVariants(TileId.Soil));
            var t46 = set.Get(TileId.Soil, 46);
            for (int x = 0; x < 100; x++)
                Assert.AreSame(t46, set.Get(TileId.Soil, 46, x, 300), "no variant chosen");
            created.AddRange(new[] { (Object)t46 });
        }

        [Test]
        public void SheetWithVariantsMixesThemOnlyIntoInteriorTiles()
        {
            var set = new TerrainTileSet();
            set.LoadFromSprites(TileId.Soil, Sheet(63));
            Assert.AreEqual(16, set.InteriorVariants(TileId.Soil));
            var seen = new HashSet<TileBase>();
            for (int x = 0; x < 300; x++) seen.Add(set.Get(TileId.Soil, 46, x, 300));
            Assert.AreEqual(17, seen.Count, "tile 46 and all 16 variants appear");
            var edge = set.Get(TileId.Soil, 10);
            for (int x = 0; x < 50; x++) Assert.AreSame(edge, set.Get(TileId.Soil, 10, x, 300), "edge tiles never vary");
            Assert.AreSame(set.Get(TileId.Soil, 46, 1234, 310), set.Get(TileId.Soil, 46, 1234, 310), "same position, same tile (save → load)");
            created.AddRange(seen.Cast<Object>());
        }
    }
}
