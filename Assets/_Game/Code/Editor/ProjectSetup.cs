using System.IO;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace Meridian.EditorTools
{
    /// <summary>
    /// Idempotent one-shot project configuration (U-001). Run from batch:
    /// tools/unity_compile.ps1 -ExecuteMethod Meridian.EditorTools.ProjectSetup.Run
    /// </summary>
    public static class ProjectSetup
    {
        public const string RenderingFolder = "Assets/_Game/Settings/Rendering";
        public const string RendererPath = RenderingFolder + "/MERIDIAN_Renderer2D.asset";
        public const string PipelinePath = RenderingFolder + "/MERIDIAN_URP.asset";

        static readonly string[] Folders =
        {
            "Assets/_Game/Code/Runtime", "Assets/_Game/Code/Editor", "Assets/_Game/Scenes",
            "Assets/_Game/Prefabs", "Assets/_Game/Settings", RenderingFolder, "Assets/_Game/Shaders",
            "Assets/_Game/UI", "Assets/_Game/Audio", "Assets/_Game/Placeholders", "Assets/_Game/Tests/Unit",
        };

        [MenuItem("MERIDIAN/Project Setup")]
        public static void Run()
        {
            foreach (var f in Folders) Directory.CreateDirectory(f);
            AssetDatabase.Refresh();

            var renderer = AssetDatabase.LoadAssetAtPath<Renderer2DData>(RendererPath);
            if (renderer == null)
            {
                renderer = ScriptableObject.CreateInstance<Renderer2DData>();
                AssetDatabase.CreateAsset(renderer, RendererPath);
            }

            var pipeline = AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>(PipelinePath);
            if (pipeline == null)
            {
                pipeline = UniversalRenderPipelineAsset.Create(renderer);
                AssetDatabase.CreateAsset(pipeline, PipelinePath);
            }

            GraphicsSettings.defaultRenderPipeline = pipeline;
            var current = QualitySettings.GetQualityLevel();
            for (int i = 0; i < QualitySettings.names.Length; i++)
            {
                QualitySettings.SetQualityLevel(i, false);
                QualitySettings.renderPipeline = pipeline;
            }
            QualitySettings.SetQualityLevel(current, false);

            PlayerSettings.companyName = "Zubers";
            PlayerSettings.productName = "MERIDIAN";
            PlayerSettings.colorSpace = ColorSpace.Linear;
            PlayerSettings.SetScriptingBackend(UnityEditor.Build.NamedBuildTarget.Standalone, ScriptingImplementation.Mono2x);
            PlayerSettings.defaultScreenWidth = 1920;
            PlayerSettings.defaultScreenHeight = 1080;
            EditorSettings.defaultBehaviorMode = EditorBehaviorMode.Mode2D;

            // 1 = Input System only (Bible §10.1).
            var player = AssetDatabase.LoadAllAssetsAtPath("ProjectSettings/ProjectSettings.asset");
            if (player.Length > 0)
            {
                var so = new SerializedObject(player[0]);
                var prop = so.FindProperty("activeInputHandler");
                if (prop != null && prop.intValue != 1) { prop.intValue = 1; so.ApplyModifiedPropertiesWithoutUndo(); }
            }

            // URP drops its global settings and default volume at Assets/ root; keep them in _Game.
            foreach (var name in new[] { "UniversalRenderPipelineGlobalSettings.asset", "DefaultVolumeProfile.asset" })
            {
                var from = "Assets/" + name;
                if (File.Exists(from)) AssetDatabase.MoveAsset(from, RenderingFolder + "/" + name);
            }

            EditorUtility.SetDirty(pipeline);
            AssetDatabase.SaveAssets();
            Debug.Log("[MERIDIAN] ProjectSetup complete: URP 2D Renderer assigned, Input System active.");
        }
    }
}
