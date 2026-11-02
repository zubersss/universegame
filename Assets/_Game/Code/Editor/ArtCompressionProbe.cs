using System.IO;
using UnityEditor;
using UnityEngine;

namespace Meridian.EditorTools
{
    /// <summary>
    /// U-060 experiment: the art sheets import as RGBA32/RGB24 although every setting asks for BC7/BC5 (and a
    /// reimport with a graphics device changed 1 of 72). Imports throw-away PNGs under Tests/_TexProbe with one
    /// property changed at a time and logs the stored format, to find the property that stops compression.
    /// Run: tools/unity_compile.ps1 -Graphics -ExecuteMethod Meridian.EditorTools.ArtCompressionProbe.Run
    /// </summary>
    public static class ArtCompressionProbe
    {
        const string Folder = "Assets/_Game/Tests/_TexProbe";

        struct Variant
        {
            public string name; public int w, h; public bool sprite, mips, alphaIsTransparency, normal;
            public TextureImporterFormat format; public int quality;
        }

        public static void Run()
        {
            Directory.CreateDirectory(Folder);
            var variants = new[]
            {
                new Variant { name = "a_sheet_like", w = 1940, h = 1616, sprite = true, mips = true, alphaIsTransparency = true, format = TextureImporterFormat.BC7, quality = 100 },
                new Variant { name = "b_no_mips", w = 1940, h = 1616, sprite = true, mips = false, alphaIsTransparency = true, format = TextureImporterFormat.BC7, quality = 100 },
                new Variant { name = "c_default_type", w = 1940, h = 1616, sprite = false, mips = true, alphaIsTransparency = true, format = TextureImporterFormat.BC7, quality = 100 },
                new Variant { name = "d_no_alpha_transp", w = 1940, h = 1616, sprite = true, mips = true, alphaIsTransparency = false, format = TextureImporterFormat.BC7, quality = 100 },
                new Variant { name = "e_quality_50", w = 1940, h = 1616, sprite = true, mips = true, alphaIsTransparency = true, format = TextureImporterFormat.BC7, quality = 50 },
                new Variant { name = "f_pot_2048", w = 2048, h = 2048, sprite = true, mips = true, alphaIsTransparency = true, format = TextureImporterFormat.BC7, quality = 100 },
                new Variant { name = "g_dxt5", w = 1940, h = 1616, sprite = true, mips = true, alphaIsTransparency = true, format = TextureImporterFormat.DXT5, quality = 100 },
                new Variant { name = "h_small_512", w = 512, h = 512, sprite = true, mips = true, alphaIsTransparency = true, format = TextureImporterFormat.BC7, quality = 100 },
                new Variant { name = "i_normal_bc5", w = 1940, h = 1616, normal = true, mips = true, format = TextureImporterFormat.BC5, quality = 100 },
            };
            Debug.Log($"[MERIDIAN] TexProbe: device {SystemInfo.graphicsDeviceType}, target {EditorUserBuildSettings.activeBuildTarget}");
            foreach (var v in variants)
            {
                var path = $"{Folder}/{v.name}.png";
                var tex = new Texture2D(v.w, v.h, TextureFormat.RGBA32, false);
                var px = new Color32[v.w * v.h];
                for (int y = 0; y < v.h; y++)
                    for (int x = 0; x < v.w; x++)
                        px[y * v.w + x] = new Color32((byte)(x * 255 / v.w), (byte)(y * 255 / v.h), (byte)((x ^ y) & 255), (byte)(x < 8 || y < 8 ? 0 : 255));
                tex.SetPixels32(px);
                File.WriteAllBytes(path, tex.EncodeToPNG());
                Object.DestroyImmediate(tex);
                AssetDatabase.ImportAsset(path, ImportAssetOptions.ForceSynchronousImport);

                var ti = (TextureImporter)AssetImporter.GetAtPath(path);
                ti.textureType = v.normal ? TextureImporterType.NormalMap : v.sprite ? TextureImporterType.Sprite : TextureImporterType.Default;
                if (!v.normal) { ti.sRGBTexture = true; ti.alphaIsTransparency = v.alphaIsTransparency; }
                ti.mipmapEnabled = v.mips;
                ti.npotScale = TextureImporterNPOTScale.None;
                ti.maxTextureSize = 2048;
                ti.textureCompression = TextureImporterCompression.CompressedHQ;
                var p = ti.GetPlatformTextureSettings("Standalone");
                p.overridden = true; p.format = v.format; p.compressionQuality = v.quality; p.maxTextureSize = 2048;
                ti.SetPlatformTextureSettings(p);
                var t0 = System.DateTime.Now;
                ti.SaveAndReimport();
                var ms = (System.DateTime.Now - t0).TotalMilliseconds;
                var stored = AssetDatabase.LoadAssetAtPath<Texture2D>(path);
                Debug.Log($"[MERIDIAN] TexProbe: {v.name} {v.w}x{v.h} sprite {v.sprite} normal {v.normal} mips {v.mips} alphaT {v.alphaIsTransparency} {v.format} q{v.quality} → stored {(stored != null ? stored.format.ToString() : "null")} in {ms:F0} ms");
            }
            AssetDatabase.DeleteAsset(Folder);
            Debug.Log("[MERIDIAN] TexProbe: done (folder removed)");
        }
    }
}
