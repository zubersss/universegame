using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEngine;

namespace Meridian.EditorTools
{
    /// <summary>
    /// U-060: the 0.3.0 build held the big art sheets as RGBA32/RGB24 although their Standalone import asks for
    /// BC7/BC5 (ArtCompressionTests: settings right, stored format uncompressed). Reimports every art PNG whose
    /// stored format is uncompressed and logs before/after, so a run with a graphics device shows whether the
    /// -nographics batch imports were the cause. Run: tools/unity_compile.ps1 -Graphics -ExecuteMethod
    /// Meridian.EditorTools.ArtRecompress.Run
    /// </summary>
    public static class ArtRecompress
    {
        [MenuItem("MERIDIAN/Art/Recompress uncompressed sheets")]
        public static void Run()
        {
            Debug.Log($"[MERIDIAN] ArtRecompress: graphics device {SystemInfo.graphicsDeviceType}, active target {EditorUserBuildSettings.activeBuildTarget}");
            var paths = new List<string>();
            foreach (var guid in AssetDatabase.FindAssets("t:Texture2D", new[] { "Assets/_Game/Art" }))
            {
                var path = AssetDatabase.GUIDToAssetPath(guid);
                if (!path.EndsWith(".png")) continue;
                var tex = AssetDatabase.LoadAssetAtPath<Texture2D>(path);
                if (tex == null || !Uncompressed(tex.format)) continue;
                if (new FileInfo(path).Length < 256 * 1024 && tex.width * tex.height < 512 * 512) continue; // small art: not the memory problem
                paths.Add(path);
            }
            Debug.Log($"[MERIDIAN] ArtRecompress: {paths.Count} uncompressed sheets to reimport");
            int fixedCount = 0;
            foreach (var path in paths)
            {
                AssetDatabase.ImportAsset(path, ImportAssetOptions.ForceUpdate | ImportAssetOptions.ForceSynchronousImport);
                var tex = AssetDatabase.LoadAssetAtPath<Texture2D>(path);
                string after = tex != null ? tex.format.ToString() : "null";
                if (tex != null && !Uncompressed(tex.format)) fixedCount++;
                Debug.Log($"[MERIDIAN] ArtRecompress: {path} → {after}");
            }
            Debug.Log($"[MERIDIAN] ArtRecompress: {fixedCount}/{paths.Count} now compressed");
        }

        static bool Uncompressed(TextureFormat f) =>
            f == TextureFormat.RGBA32 || f == TextureFormat.RGB24 || f == TextureFormat.ARGB32 || f == TextureFormat.BGRA32 || f == TextureFormat.R8 || f == TextureFormat.RG16;
    }
}
