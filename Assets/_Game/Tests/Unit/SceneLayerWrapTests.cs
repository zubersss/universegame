using NUnit.Framework;
using UnityEditor;
using UnityEngine;
using Meridian.EditorTools;

namespace Meridian.Tests
{
    /// <summary>
    /// U-109: a side-scene layer tiles in x only. Imported with Repeat in y, its top texel row bilinear-blended with its bottom row
    /// (ground colour) along the sprite's top edge and drew a 1-px dark line across the sky of every climb frame where a hills layer
    /// ended (u109 2_climb_28m, u103 2_tilted_climb). The starfield's tile_y layer keeps Repeat for SpaceBackdrop's UV tiling.
    /// </summary>
    public class SceneLayerWrapTests
    {
        [Test]
        public void SideSceneLayersClampInYAndTheStarfieldRepeats()
        {
            int seen = 0;
            foreach (var scene in new[] { "plains", "coast", "forest" })
                for (int n = 0; n < 3; n++)
                {
                    string key = $"backgrounds/earth/{scene}/layer{n}";
                    string path = ArtImporter.Active.art + key + "_color.png";
                    var ti = AssetImporter.GetAtPath(path) as TextureImporter;
                    if (ti == null) continue; // a scene not painted yet
                    seen++;
                    Assert.IsFalse(ArtImporter.LayerTilesY(path, key), key + " does not tile in y");
                    Assert.AreEqual(TextureWrapMode.Repeat, ti.wrapModeU, key + " repeats in x (ParallaxLayers tiles it three wide)");
                    Assert.AreEqual(TextureWrapMode.Clamp, ti.wrapModeV, key + " clamps in y (no ground-row bleed along its top edge)");
                }
            Assert.GreaterOrEqual(seen, 3, "the plains layers are in the repo");
            string star = ArtImporter.Active.art + "backgrounds/space/starfield/layer0_color.png";
            Assert.IsTrue(ArtImporter.LayerTilesY(star, "backgrounds/space/starfield/layer0"), "starfield layer0 carries tile_y");
            var sti = AssetImporter.GetAtPath(star) as TextureImporter;
            if (sti != null) Assert.AreEqual(TextureWrapMode.Repeat, sti.wrapModeV, "the starfield repeats in y for SpaceBackdrop's UV tiling");
            Assert.IsFalse(ArtImporter.LayerTilesY(ArtImporter.Active.art + "backgrounds/space/starfield/layer1_color.png", "backgrounds/space/starfield/layer1"), "a nebula card does not tile");
        }
    }
}
