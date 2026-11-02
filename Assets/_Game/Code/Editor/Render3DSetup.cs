using System.IO;
using Meridian.Rendering;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering.Universal;

namespace Meridian.EditorTools
{
    /// <summary>
    /// U-072 (D-062, Bible 2.0 §10.1/§10.5): switches MERIDIAN_URP to a Universal (3D) Renderer with Forward+ and
    /// adds URP/Lit materials to the ArtMaterials registry. The 2D renderer asset stays in the project (archive
    /// branch only) but leaves the renderer list. Idempotent. Run: tools/unity_compile.ps1 -ExecuteMethod
    /// Meridian.EditorTools.Render3DSetup.Run
    /// </summary>
    public static class Render3DSetup
    {
        const string UrpPath = "Assets/_Game/Settings/Rendering/MERIDIAN_URP.asset";
        const string RendererPath = "Assets/_Game/Settings/Rendering/MERIDIAN_Renderer3D.asset";
        const string MatDir = "Assets/_Game/Settings/Materials";

        [MenuItem("MERIDIAN/Rendering/Switch to 3D renderer (U-072)")]
        public static void Run()
        {
            var urp = AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>(UrpPath);
            if (urp == null) { Debug.LogError($"[MERIDIAN] Render3DSetup: no URP asset at {UrpPath}"); return; }

            var data = AssetDatabase.LoadAssetAtPath<UniversalRendererData>(RendererPath);
            if (data == null)
            {
                data = ScriptableObject.CreateInstance<UniversalRendererData>();
                AssetDatabase.CreateAsset(data, RendererPath);
            }
            data.renderingMode = RenderingMode.ForwardPlus;
            EditorUtility.SetDirty(data);

            // The renderer list is serialized-only: make the 3D renderer the only (default) entry.
            var so = new SerializedObject(urp);
            var list = so.FindProperty("m_RendererDataList");
            list.arraySize = 1;
            list.GetArrayElementAtIndex(0).objectReferenceValue = data;
            so.FindProperty("m_DefaultRendererIndex").intValue = 0;
            so.ApplyModifiedPropertiesWithoutUndo();
            urp.supportsHDR = true;               // bloom on emission (U-074)
            urp.shadowCascadeCount = 1;           // Bible §11.1: one cascade
            urp.shadowDistance = 30f;             // §10.5: 30 m
            EditorUtility.SetDirty(urp);

            var reg = AssetDatabase.LoadAssetAtPath<ArtMaterials>("Assets/_Game/Settings/Resources/ArtMaterials.asset");
            if (reg != null)
            {
                reg.meshLit = LitMaterial("Mesh_Lit", false);
                reg.meshLitEmissive = LitMaterial("Mesh_LitEmissive", true);
                reg.terrainBlocks = TerrainBlocksMaterial();
                EditorUtility.SetDirty(reg);
            }
            else Debug.LogError("[MERIDIAN] Render3DSetup: no ArtMaterials registry");

            AssetDatabase.SaveAssets();
            Debug.Log($"[MERIDIAN] Render3DSetup: {UrpPath} → {RendererPath} ({data.renderingMode}), HDR {urp.supportsHDR}, cascades {urp.shadowCascadeCount}, shadow distance {urp.shadowDistance}; registry meshLit {(reg != null && reg.meshLit != null)}");
        }

        /// <summary>U-073: the block mesh material (the per-planet Texture2DArray is set at runtime).</summary>
        static Material TerrainBlocksMaterial()
        {
            var path = $"{MatDir}/Terrain_Blocks.mat";
            var m = AssetDatabase.LoadAssetAtPath<Material>(path);
            var shader = Shader.Find("MERIDIAN/TerrainBlocks");
            if (shader == null) { Debug.LogError("[MERIDIAN] Render3DSetup: shader MERIDIAN/TerrainBlocks not found"); return null; }
            if (m == null)
            {
                m = new Material(shader) { name = "Terrain_Blocks" };
                AssetDatabase.CreateAsset(m, path);
            }
            else m.shader = shader;
            m.enableInstancing = false;
            EditorUtility.SetDirty(m);
            return m;
        }

        static Material LitMaterial(string name, bool emissive)
        {
            var path = $"{MatDir}/{name}.mat";
            var m = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (m == null)
            {
                var shader = Shader.Find("Universal Render Pipeline/Lit");
                m = new Material(shader) { name = name };
                AssetDatabase.CreateAsset(m, path);
            }
            m.SetFloat("_Smoothness", 0.3f);
            if (emissive)
            {
                m.EnableKeyword("_EMISSION");
                m.SetColor("_EmissionColor", Color.white);
                m.globalIlluminationFlags = MaterialGlobalIlluminationFlags.RealtimeEmissive;
            }
            EditorUtility.SetDirty(m);
            return m;
        }
    }
}
