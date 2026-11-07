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

        /// <summary>D-146: the fill tile sits one texel inside frame 0's bottom band on every side (the sheets' 4 px gutters are transparent,
        /// and Repeat wraps v onto the sheet's transparent top row: a tile touching either bled under bilinear filtering — the Mercury night
        /// frame's 64 px seams, then the 13:47 frames' horizontal lines) and still spans exactly one 1 m column.</summary>
        [Test]
        public void TheFillTileStaysInsideItsFrameAndSpansOneColumn()
        {
            var frame0 = new Rect(0f, 0f, 64f, 152f);
            var r = GroundStrip.FillRect(frame0);
            Assert.AreEqual(1f, r.xMin, "one texel in from the left (the sheet's far edge wraps there)");
            Assert.AreEqual(63f, r.xMax, "one texel in from the right (the gutter starts at 64)");
            Assert.AreEqual(1f, r.yMin, "one texel up from the frame's bottom edge (v wraps to the sheet's top row there)");
            Assert.AreEqual(7f, r.yMax, "one texel under the band's top (row 7 is still the band; row 8 starts the strip art)");
            Assert.AreEqual(1f, r.width / GroundStrip.FillPpu(frame0, 64f), 1e-5f, "one column wide in world units");
            var frame3 = new Rect(204f, 0f, 64f, 152f);
            Assert.AreEqual(205f, GroundStrip.FillRect(frame3).xMin, "any frame: from its own left edge");
        }

        /// <summary>P-48: every ground strip sheet tiles in x only — Repeat in u, Clamp in v (with Repeat in v each frame's bottom row sampled the
        /// sheet's transparent top row: a faint line 2 m under every ground line); a plain image and an overlay keep their rules.</summary>
        [Test]
        public void TheStripSheetsRepeatInXAndClampInY()
        {
            Assert.IsTrue(Meridian.EditorTools.ArtImporter.ClampsV(new Meridian.EditorTools.ArtImporter.SheetManifest { tile = true, frames = 8, frame_width = 64, frame_height = 152, columns = 8 }), "a tiling frame sheet");
            Assert.IsFalse(Meridian.EditorTools.ArtImporter.ClampsV(new Meridian.EditorTools.ArtImporter.SheetManifest { tile = true }), "a tiling single image (an overlay) keeps v");
            Assert.IsFalse(Meridian.EditorTools.ArtImporter.ClampsV(null), "no sidecar");
            int checkedSheets = 0;
            foreach (var keys in new[] { GroundStrip.Keys, GroundStrip.MarsKeys, GroundStrip.MercuryKeys })
                foreach (var key in keys)
                {
                    var ti = UnityEditor.AssetImporter.GetAtPath($"Assets/_Game/Art/{key}_color.png") as UnityEditor.TextureImporter;
                    if (ti == null) continue;
                    Assert.AreEqual(TextureWrapMode.Repeat, ti.wrapModeU, key + ": repeats in x");
                    Assert.AreEqual(TextureWrapMode.Clamp, ti.wrapModeV, key + ": clamps in y");
                    checkedSheets++;
                }
            Assert.GreaterOrEqual(checkedSheets, 9, "the nine strips (Earth 4, Mars 3, Mercury 2) are on disk");
        }

        /// <summary>U-126 (D-137): a giant's floe is cap + n tiles + cap at any n ≥ 1 — cap_left (frame 8) in the air column just left of the floe,
        /// cap_right (frame 9) just right, the tiles cycling frames 0–7 in between, never a cap inside; an 8-frame strip (Earth, Mars, Mercury,
        /// Venus) never caps; a column ends a floe where the ground beside it falls away.</summary>
        [Test]
        public void AFloeIsCapTilesCapAtAnyLength()
        {
            var frames = new System.Collections.Generic.List<Vector2Int>();
            foreach (int n in new[] { 1, 2, 8 })
            {
                GroundStrip.FloeFrames(100, n, frames);
                Assert.AreEqual(n + 2, frames.Count, $"{n}-tile floe: cap + {n} + cap");
                Assert.AreEqual(new Vector2Int(99, GroundStrip.CapLeft), frames[0], "cap_left just outside the left end");
                Assert.AreEqual(new Vector2Int(100 + n, GroundStrip.CapRight), frames[n + 1], "cap_right just outside the right end");
                for (int i = 1; i <= n; i++)
                {
                    Assert.AreEqual(100 + i - 1, frames[i].x, "the tiles on the floe's own columns");
                    Assert.Less(frames[i].y, GroundStrip.TileFrames, $"{n}-tile floe: no cap inside (column {frames[i].x})");
                }
            }
            GroundStrip.FloeFrames(100, 0, frames);
            Assert.AreEqual(0, frames.Count, "no floe, no caps");
            Assert.AreEqual(0, GroundStrip.TileFrame(8)); Assert.AreEqual(7, GroundStrip.TileFrame(-1)); Assert.AreEqual(3, GroundStrip.TileFrame(11));
            Assert.IsFalse(GroundStrip.HasCaps(8), "Earth's, Mars's, Mercury's and Venus's 8-frame strips never cap");
            Assert.IsTrue(GroundStrip.HasCaps(10), "a giant's 10-frame floe strip does");
            Assert.IsTrue(GroundStrip.FloeEnd(400f, 380f), "the gap beside a floe: an end");
            Assert.IsFalse(GroundStrip.FloeEnd(400f, 399f), "a 1 m step on the same floe: not an end");
            Assert.IsFalse(GroundStrip.FloeEnd(400f, 402f), "higher ground beside: not an end");
        }
    }
}
