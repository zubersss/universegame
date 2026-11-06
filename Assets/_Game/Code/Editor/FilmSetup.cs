using Meridian.Rendering;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering.Universal;

namespace Meridian.EditorTools
{
    /// <summary>
    /// U-095: puts the FilmFeature (MERIDIAN/FilmPass material) on the MERIDIAN_Renderer3D renderer and turns HDR off on
    /// the pipeline asset (Bible §9.4 v4: no bloom, no HDR). Idempotent. Run: tools/unity_compile.ps1 -ExecuteMethod
    /// Meridian.EditorTools.FilmSetup.Run, or the MERIDIAN menu.
    /// </summary>
    public static class FilmSetup
    {
        public const string UrpPath = "Assets/_Game/Settings/Rendering/MERIDIAN_URP.asset";
        public const string RendererPath = "Assets/_Game/Settings/Rendering/MERIDIAN_Renderer3D.asset";
        public const string MaterialPath = "Assets/_Game/Settings/Materials/FilmPass.mat";
        public const string ShaderName = "MERIDIAN/FilmPass";

        [MenuItem("MERIDIAN/Rendering/Film pass (U-095)")]
        public static void Run()
        {
            var shader = Shader.Find(ShaderName);
            if (shader == null) { Debug.LogError($"[MERIDIAN] FilmSetup: shader {ShaderName} not found"); return; }
            var material = AssetDatabase.LoadAssetAtPath<Material>(MaterialPath);
            if (material == null)
            {
                material = new Material(shader) { name = "FilmPass" };
                AssetDatabase.CreateAsset(material, MaterialPath);
            }
            else if (material.shader != shader) { material.shader = shader; EditorUtility.SetDirty(material); }

            var data = AssetDatabase.LoadAssetAtPath<UniversalRendererData>(RendererPath);
            if (data == null) { Debug.LogError($"[MERIDIAN] FilmSetup: no renderer data at {RendererPath}"); return; }
            FilmFeature feature = null;
            foreach (var f in data.rendererFeatures) if (f is FilmFeature ff) { feature = ff; break; }
            if (feature == null)
            {
                feature = ScriptableObject.CreateInstance<FilmFeature>();
                feature.name = "Film";
                AssetDatabase.AddObjectToAsset(feature, data);
                AssetDatabase.TryGetGUIDAndLocalFileIdentifier(feature, out _, out long localId);
                var so = new SerializedObject(data);
                var list = so.FindProperty("m_RendererFeatures");
                list.arraySize++;
                list.GetArrayElementAtIndex(list.arraySize - 1).objectReferenceValue = feature;
                var map = so.FindProperty("m_RendererFeatureMap");
                map.arraySize++;
                map.GetArrayElementAtIndex(map.arraySize - 1).longValue = localId;
                so.ApplyModifiedPropertiesWithoutUndo();
            }
            var fso = new SerializedObject(feature);
            fso.FindProperty("material").objectReferenceValue = material;
            fso.ApplyModifiedPropertiesWithoutUndo();
            EditorUtility.SetDirty(feature);
            EditorUtility.SetDirty(data);

            var urp = AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>(UrpPath);
            if (urp != null && urp.supportsHDR) { urp.supportsHDR = false; EditorUtility.SetDirty(urp); }

            AssetDatabase.SaveAssets();
            Debug.Log($"[MERIDIAN] FilmSetup: FilmFeature on {RendererPath} with {MaterialPath}; HDR {(urp != null ? urp.supportsHDR.ToString() : "n/a")}");
        }
    }
}
