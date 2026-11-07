using System.IO;
using Meridian.Art;
using NUnit.Framework;
using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>
    /// U-113 (EditMode, D-117): the six camp props' sheets, once B-131's export is in, carry the frame sizes, pivots and clip sets
    /// of BLENDER's hand-off (pad 128×48 tiling at 2 m, wall 64×64 tiling at 1 m in x and y (D-125), door 88×176 open 6, smelter 112×192 working 8,
    /// crate 80×72, lamp 64×160 flicker 4; ground line 10 px up); SheetProp's fit rules are pure. Until the export the sheet
    /// assertions are skipped with the reason (the glb props still stand).
    /// </summary>
    public class PropSpriteTests
    {
        const string Dir = "Assets/_Game/Art/props/common/";

        [System.Serializable] sealed class Clip { public string name; public int start, length; public bool loop; }
        [System.Serializable] sealed class Sidecar { public string style; public int frame_width, frame_height, columns, frames, fps = 12, ground_line_px; public float ppu, module_m; public float[] pivot; public bool tile, interactable, squash_root; public Clip[] animations; }

        static readonly (string key, int w, int h, float module, bool interactable, (string name, int length, bool loop)? clip)[] Expected =
        {
            ("landing_pad", 128, 48, 2f, false, null),
            ("shelter_wall", 64, 64, 1f, false, null),   // D-125: a 1 × 1 m tile in x and y (was 64×176 before the ruling)
            ("shelter_door", 88, 176, 0f, true, ("open", 6, false)),
            ("smelter", 112, 192, 0f, true, ("working", 8, true)),
            ("storage_crate", 80, 72, 0f, true, null),
            ("lamp", 64, 160, 0f, false, ("flicker", 4, true)),
        };

        [Test]
        public void TheSixCampPropSheetsMatchTheHandOff()
        {
            int present = 0;
            foreach (var e in Expected)
            {
                string json = Dir + e.key + ".json", png = Dir + e.key + "_color.png", glb = Dir + e.key + ".glb";
                if (!File.Exists(json) || !File.Exists(png) || File.Exists(glb)) continue; // not exported yet (or the model still stands)
                present++;
                var s = JsonUtility.FromJson<Sidecar>(File.ReadAllText(json));
                Assert.AreEqual("v3", s.style, e.key);
                Assert.AreEqual(e.w, s.frame_width, $"{e.key} frame width"); Assert.AreEqual(e.h, s.frame_height, $"{e.key} frame height");
                Assert.AreEqual(64f, s.ppu, 1e-4f, $"{e.key} PPU 64");
                Assert.AreEqual(12, s.fps, $"{e.key} on twos");
                Assert.IsFalse(s.squash_root, $"{e.key}: a prop never squashes");
                Assert.AreEqual(e.module > 0f, s.tile, $"{e.key} tile flag");
                if (e.module > 0f) Assert.AreEqual(e.module, s.module_m, 1e-4f, $"{e.key} module");
                Assert.AreEqual(e.interactable, s.interactable, $"{e.key} interactable");
                Assert.AreEqual(e.key == "shelter_wall" ? 0 : 10, s.ground_line_px, $"{e.key}: the ground line 10 px above the frame bottom"); // D-125: the wall tile has no ground-line margin
                Assert.NotNull(s.pivot); Assert.AreEqual(2, s.pivot.Length);
                Assert.AreEqual((e.key == "shelter_wall" ? 0f : 10f) / e.h, s.pivot[1], 1e-3f, $"{e.key}: the pivot on the ground line"); // D-125: the wall tile's pivot is its bottom edge
                // U-113: the sidecar is addressed at <key>/json (ModelSwap probes it for the sheet path); the sheet's controller at <key>/animator when it has clips.
                var jsonEntry = Meridian.EditorTools.ArtImporter.Settings.FindAssetEntry(UnityEditor.AssetDatabase.AssetPathToGUID(json));
                Assert.NotNull(jsonEntry, $"props/common/{e.key}.json is addressed");
                Assert.AreEqual($"props/common/{e.key}/json", jsonEntry.address, $"{e.key}: the sidecar's address");
                if (e.clip.HasValue)
                {
                    var c = System.Array.Find(s.animations ?? new Clip[0], a => a.name == e.clip.Value.name);
                    Assert.NotNull(c, $"{e.key} clip {e.clip.Value.name}");
                    Assert.AreEqual(e.clip.Value.length, c.length, $"{e.key} {c.name} frames");
                    Assert.AreEqual(e.clip.Value.loop, c.loop, $"{e.key} {c.name} loop");
                    Assert.AreEqual(c.length, s.frames, $"{e.key}: the clip is the whole sheet");
                }
                else
                {
                    Assert.AreEqual(1, s.frames, $"{e.key}: one drawing");
                    Assert.IsTrue(s.animations == null || s.animations.Length == 0, $"{e.key}: no clip");
                }
            }
            if (present == 0) Assert.Ignore("B-131's camp prop sheets are not exported yet (D-117): the glb props stand; the sheet rules run once they land.");
            Assert.AreEqual(Expected.Length, present, "all six props exported together (one batch, D-117)");
        }

        [Test]
        public void TheFitRulesArePure()
        {
            var art = new Vector2(1.375f, 2.75f); // the door: 88 × 176 px at 64
            var cells = new Vector2(1f, 2f);
            var height = SheetProp.FitScale(art, cells, false);
            Assert.AreEqual(2f / 2.75f, height.x, 1e-5f); Assert.AreEqual(2f / 2.75f, height.y, 1e-5f, "height fit keeps the proportions");
            var stretch = SheetProp.FitScale(new Vector2(1f, 2.75f), new Vector2(1f, 1f), true);
            Assert.AreEqual(1f, stretch.x, 1e-5f); Assert.AreEqual(1f / 2.75f, stretch.y, 1e-5f, "a stretched piece fills its cells");
            Assert.AreEqual(1f, stretch.z, 1e-5f);
        }
    }
}
