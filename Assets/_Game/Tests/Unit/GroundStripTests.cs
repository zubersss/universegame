using System.IO;
using Meridian.Terrain;
using Meridian.View2D;
using NUnit.Framework;
using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>
    /// U-111 (B-130): the cartoon ground draws each column from the strip of its top solid tile (grass over soil, bare soil where dug,
    /// stone where the block is stone, sand on the coast); the four sheets share the B-130 frame (64×152, the pivot on the ground line
    /// 128 px up, one frame per column x mod 8, tile: true) so the strip code needs no per-material geometry.
    /// </summary>
    public class GroundStripTests
    {
        [Test]
        public void TheColumnMaterialFollowsTheTopTile()
        {
            Assert.AreEqual(GroundStrip.Grass, GroundStrip.MaterialFor(TileId.Grass));
            Assert.AreEqual(GroundStrip.Sand, GroundStrip.MaterialFor(TileId.Sand), "the coast");
            Assert.AreEqual(GroundStrip.Stone, GroundStrip.MaterialFor(TileId.Stone));
            Assert.AreEqual(GroundStrip.Soil, GroundStrip.MaterialFor(TileId.Soil), "a dug face shows soil");
            Assert.AreEqual(GroundStrip.Soil, GroundStrip.MaterialFor(TileId.Snow), "no snow strip yet: soil");
            Assert.AreEqual(GroundStrip.Soil, GroundStrip.MaterialFor(TileId.Air), "nothing solid: soil (never drawn)");
            Assert.AreEqual(4, GroundStrip.Keys.Length);
            Assert.AreEqual("terrain/earth/ground_strip", GroundStrip.Keys[GroundStrip.Grass]);
            Assert.AreEqual("terrain/earth/ground_strip_sand", GroundStrip.Keys[GroundStrip.Sand]);
        }

        [System.Serializable] internal class Sheet { public int frame_width, frame_height, columns, frames, ground_line_px; public float ppu; public float[] pivot; public bool tile; public string material; }

        [Test]
        public void TheFourStripsShareTheB130Frame()
        {
            var materials = new[] { "grass", "soil", "stone", "sand" };
            for (int m = 0; m < GroundStrip.Keys.Length; m++)
            {
                string path = "Assets/_Game/Art/" + GroundStrip.Keys[m] + ".json";
                Assert.IsTrue(File.Exists(path), path);
                var s = JsonUtility.FromJson<Sheet>(File.ReadAllText(path));
                Assert.AreEqual(64, s.frame_width, path); Assert.AreEqual(152, s.frame_height, path);
                Assert.AreEqual(8, s.frames, path + ": one frame per column, x mod 8");
                Assert.AreEqual(128, s.ground_line_px, path + ": 2 m of material under the line");
                Assert.AreEqual(0.5f, s.pivot[0], 1e-4f); Assert.AreEqual(128f / 152f, s.pivot[1], 1e-3f, path + ": the pivot on the ground line");
                Assert.AreEqual(64f, s.ppu, 1e-4f); Assert.IsTrue(s.tile, path + " tiles");
                Assert.AreEqual(materials[m], s.material, path);
                Assert.IsTrue(File.Exists("Assets/_Game/Art/" + GroundStrip.Keys[m] + "_color.png"), path + " colour map");
            }
            Assert.AreEqual(2f, GroundStrip.StripHeight, 1e-4f, "the strip reaches 2 m under the line, then the fill tile");
        }
    }
}
