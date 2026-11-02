#if UNITY_EDITOR
using NUnit.Framework;
using UnityEditor;
using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>
    /// U-060 diagnosis (EditMode): the 0.3.0 dev build held creature and character sheets as RGBA32/RGB24 although
    /// their Standalone import asks for BC7/BC5. This records, for a few big sheets, the import settings and the
    /// format Unity actually stored for the active build target, so the next run shows where the compression is lost.
    /// </summary>
    public class ArtCompressionTests
    {
        static readonly string[] Sheets =
        {
            "Assets/_Game/Art/creatures/earth/stag_color.png",
            "Assets/_Game/Art/creatures/earth/stag_normal.png",
            "Assets/_Game/Art/characters/surveyor/base_color.png",
        };

        [Test]
        public void BigSheetsImportCompressedForStandalone()
        {
            TestContext.Out.WriteLine($"[MERIDIAN] active target {EditorUserBuildSettings.activeBuildTarget}, " +
                                      $"override compression {EditorUserBuildSettings.overrideTextureCompression}, " +
                                      $"compress on import {EditorPrefs.GetBool("CompressAssetsOnImport", true)}");
            int found = 0;
            foreach (var path in Sheets)
            {
                var ti = AssetImporter.GetAtPath(path) as TextureImporter;
                if (ti == null) { TestContext.Out.WriteLine($"[MERIDIAN] {path}: not found"); continue; }
                found++;
                var ps = ti.GetPlatformTextureSettings("Standalone");
                var tex = AssetDatabase.LoadAssetAtPath<Texture2D>(path);
                TestContext.Out.WriteLine($"[MERIDIAN] {path}: Standalone override {ps.overridden} format {ps.format}; " +
                                          $"automatic {ti.GetAutomaticFormat("Standalone")}; stored {(tex != null ? tex.format.ToString() : "null")} " +
                                          $"{(tex != null ? tex.width + "x" + tex.height : "")}, readable {ti.isReadable}, type {ti.textureType}");
                Assert.IsTrue(ps.overridden, path + ": Standalone override set by ArtImporter");
                Assert.IsTrue(ps.format == TextureImporterFormat.BC7 || ps.format == TextureImporterFormat.BC5, path + ": BC7/BC5 for Standalone");
                // U-060: NPOT + mipmaps stored them uncompressed; ArtImporter v4 keeps mips to POT art only.
                Assert.NotNull(tex, path);
                Assert.IsTrue(tex.format == TextureFormat.BC7 || tex.format == TextureFormat.BC5, $"{path}: stored {tex.format}, expected BC7/BC5");
            }
            Assert.Greater(found, 0, "at least one sheet to check");
        }
    }
}
#endif
