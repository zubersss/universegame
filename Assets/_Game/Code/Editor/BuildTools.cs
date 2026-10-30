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

        public static string OutputFolder => $"Build/{GameInfo.Product}_{GameInfo.Version}";

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

            var aa = UnityEditor.AddressableAssets.AddressableAssetSettingsDefaultObject.Settings;
            if (aa != null)
            {
                AddressableAssetSettings.BuildPlayerContent(out var aaResult);
                if (!string.IsNullOrEmpty(aaResult.Error))
                {
                    Debug.LogError($"[MERIDIAN] BUILD FAILED: Addressables: {aaResult.Error}");
                    return false;
                }
            }

            var options = new BuildPlayerOptions
            {
                scenes = scenes,
                locationPathName = $"{OutputFolder}/{GameInfo.Product}.exe",
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
            Debug.Log($"[MERIDIAN] BUILD OK: {options.locationPathName} · {s.totalSize / (1024 * 1024)} MB · {s.totalTime.TotalSeconds:F0} s");
            return true;
        }
    }
}
