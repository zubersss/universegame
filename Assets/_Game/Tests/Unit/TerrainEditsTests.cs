using System.IO;
using Meridian.EditorTools;
using Meridian.Planets;
using Meridian.Terrain;
using NUnit.Framework;
using UnityEditor;
using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>U-008: terrain diffs are per chunk, revert cleanly, and survive a file round trip.</summary>
    public class TerrainEditsTests
    {
        [Test]
        public void DiffsAreStoredPerChunkAndRevertWhenRestored()
        {
            var e = new TerrainEdits();
            e.Set(5, 330, TileId.Air, TileId.Grass);
            e.Set(40, 330, TileId.Soil, TileId.Air); // a different chunk (x 32..63)
            Assert.AreEqual(2, e.Count);
            Assert.AreEqual(2, e.ChunkCount);
            Assert.IsTrue(e.TryGet(5, 330, out var id)); Assert.AreEqual(TileId.Air, id);

            e.Set(5, 330, TileId.Grass, TileId.Grass); // back to generated → diff removed
            Assert.IsFalse(e.TryGet(5, 330, out _));
            Assert.AreEqual(1, e.ChunkCount);
        }

        [Test]
        public void FileRoundTripKeepsEveryDiff()
        {
            var e = new TerrainEdits();
            for (int i = 0; i < 100; i++) e.Set(i * 13, 300 + i % 7, (byte)(i % 3), 255);
            var path = Path.Combine(Application.temporaryCachePath, "meridian_test", "terrain_earth.bin");
            e.SaveFile(path);

            var loaded = new TerrainEdits();
            loaded.LoadFile(path);
            Assert.AreEqual(e.Count, loaded.Count);
            for (int i = 0; i < 100; i++)
            {
                Assert.IsTrue(loaded.TryGet(i * 13, 300 + i % 7, out var id));
                Assert.AreEqual((byte)(i % 3), id);
            }
            File.Delete(path);
        }

        [Test]
        public void EditedWorldOverlaysDiffsOnTheSeededWorld()
        {
            var earth = AssetDatabase.LoadAssetAtPath<PlanetConfig>($"{PlanetConfigAuthoring.Folder}/Earth.asset");
            var gen = new SolidWorldGenerator(earth, 1969);
            var edits = new TerrainEdits();
            var world = new EditedWorld(gen, edits);
            int x = 100, y = gen.SurfaceHeight(100);
            Assert.IsTrue(TileId.IsSolid(world.TileAt(x, y)));
            edits.Set(x, y, TileId.Air, gen.TileAt(x, y));
            Assert.AreEqual(TileId.Air, world.TileAt(x, y));
            Assert.AreEqual(gen.TileAt(x, y - 1), world.TileAt(x, y - 1), "neighbors untouched");
        }
    }
}
