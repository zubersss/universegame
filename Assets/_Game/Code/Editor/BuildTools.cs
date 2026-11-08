using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.AddressableAssets.Settings;
using UnityEditor.Build.Reporting;
using UnityEngine;

namespace Meridian.EditorTools
{
    /// <summary>Batch Windows build used by tools/unity_build.ps1 (U-003).</summary>
    public static class BuildTools
    {
        public const string CoreScene = "Assets/_Game/Scenes/Core.unity";

        /// <summary>U-143: the release player (the owner's build, no Development Build watermark).</summary>
        public static string OutputFolder => $"Build/{GameInfo.Product}_{GameInfo.Version}";
        /// <summary>U-143: the development player sits beside it with this suffix (the memory probe needs its counters).</summary>
        public const string DevSuffix = "_dev";
        /// <summary>The folder a build writes: Build/MERIDIAN_&lt;v&gt;/ for the release, Build/MERIDIAN_&lt;v&gt;_dev/ for the development build. Pure.</summary>
        public static string OutputFolderFor(bool release) => release ? OutputFolder : OutputFolder + DevSuffix;

        /// <summary>Core first, then every other scene under Assets/_Game/Scenes (ArtPreview excluded).</summary>
        public static string[] ScenesToBuild()
        {
            if (!Directory.Exists("Assets/_Game/Scenes")) return Array.Empty<string>();
            var all = Directory.GetFiles("Assets/_Game/Scenes", "*.unity", SearchOption.AllDirectories)
                .Select(p => p.Replace('\\', '/'))
                .Where(p => !p.EndsWith("/ArtPreview.unity"))
                .OrderBy(p => p == CoreScene ? 0 : 1).ThenBy(p => p)
                .ToArray();
            return all;
        }

        public static void BuildFromCommandLine()
        {
            bool release = Environment.GetCommandLineArgs().Contains("-meridianRelease");
            int code = Build(release) ? 0 : 1;
            EditorApplication.Exit(code);
        }

        public static bool Build(bool release)
        {
            var scenes = ScenesToBuild();
            if (scenes.Length == 0) { Debug.LogError("[MERIDIAN] BUILD FAILED: no scenes in Assets/_Game/Scenes"); return false; }

            EditorBuildSettings.scenes = scenes.Select(s => new EditorBuildSettingsScene(s, true)).ToArray();
            PlayerSettings.bundleVersion = GameInfo.Version;
            // U-060: a per-user build override can force uncompressed textures (the 0.3.0 dev build held RGBA32
            // sheets although their Standalone import is BC7). Builds always use the import settings.
            Debug.Log($"[MERIDIAN] texture overrides before build: compression {EditorUserBuildSettings.overrideTextureCompression}, max size {EditorUserBuildSettings.overrideMaxTextureSize}");
            EditorUserBuildSettings.overrideTextureCompression = UnityEditor.Build.OverrideTextureCompression.NoOverride;
            EditorUserBuildSettings.overrideMaxTextureSize = 0;
            // U-044: the app icon (BLENDER ui/app/icon, 1024 px; Windows scales it for the taskbar and title bar).
            var icon = AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/_Game/Art/ui/app/icon_color.png");
            if (icon != null) PlayerSettings.SetIcons(UnityEditor.Build.NamedBuildTarget.Unknown, new[] { icon }, IconKind.Any);
            else Debug.LogWarning("[MERIDIAN] no ui/app/icon art: the build keeps the default icon");

            var aa = UnityEditor.AddressableAssets.AddressableAssetSettingsDefaultObject.Settings;
            if (aa != null)
            {
                // U-060 (LEAD cycle 157): a clean content build every time, so the player never ships stale bundles.
                var started = DateTime.Now;
                AddressableAssetSettings.CleanPlayerContent(aa.ActivePlayerDataBuilder);
                // The build cache copies unchanged bundles with their old timestamps; purge it so every bundle is
                // rebuilt from the current imports (and the freshness check below means something).
                UnityEditor.Build.Pipeline.Utilities.BuildCache.PurgeCache(false);
                AddressableAssetSettings.BuildPlayerContent(out var aaResult);
                if (!string.IsNullOrEmpty(aaResult.Error))
                {
                    Debug.LogError($"[MERIDIAN] BUILD FAILED: Addressables: {aaResult.Error}");
                    return false;
                }
                // Assert the content is fresh: every bundle the content build wrote is newer than this build's start.
                var root = UnityEngine.AddressableAssets.Addressables.BuildPath;
                int stale = 0, total = 0;
                if (System.IO.Directory.Exists(root))
                    foreach (var f in System.IO.Directory.GetFiles(root, "*.bundle", System.IO.SearchOption.AllDirectories))
                    {
                        total++;
                        if (System.IO.File.GetLastWriteTime(f) < started.AddSeconds(-5)) stale++;
                    }
                Debug.Log($"[MERIDIAN] Addressables content: {total} bundles in {root}, {stale} older than this build");
                if (total == 0 || stale > 0)
                {
                    Debug.LogError($"[MERIDIAN] BUILD FAILED: Addressables content not fresh ({stale}/{total} stale bundles in {root})");
                    return false;
                }
            }

            var options = new BuildPlayerOptions
            {
                scenes = scenes,
                locationPathName = $"{OutputFolderFor(release)}/{GameInfo.Product}.exe",
                target = BuildTarget.StandaloneWindows64,
                options = release ? BuildOptions.None : BuildOptions.Development,
            };
            var report = BuildPipeline.BuildPlayer(options);
            var s = report.summary;
            if (s.result != BuildResult.Succeeded)
            {
                Debug.LogError($"[MERIDIAN] BUILD FAILED: {s.result}, {s.totalErrors} errors");
                return false;
            }
            Debug.Log($"[MERIDIAN] BUILD OK: {options.locationPathName} · {(release ? "release" : "development")} · {s.totalSize / (1024 * 1024)} MB · {s.totalTime.TotalSeconds:F0} s");
            return true;
        }
    }
}
