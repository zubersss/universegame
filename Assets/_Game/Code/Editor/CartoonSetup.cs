using Meridian.Rendering;
using UnityEditor;
using UnityEngine;

namespace Meridian.EditorTools
{
    /// <summary>U-100: the silhouette material (MERIDIAN/CartoonSilhouette) in the ArtMaterials registry. Idempotent; run with -ExecuteMethod Meridian.EditorTools.CartoonSetup.Run or the menu.</summary>
    public static class CartoonSetup
    {
        public const string MaterialPath = "Assets/_Game/Settings/Materials/Cartoon_Silhouette.mat";
        public const string ShaderName = "MERIDIAN/CartoonSilhouette";

        [MenuItem("MERIDIAN/Rendering/Cartoon silhouette material (U-100)")]
        public static void Run()
        {
            var shader = Shader.Find(ShaderName);
            if (shader == null) { Debug.LogError($"[MERIDIAN] CartoonSetup: shader {ShaderName} not found"); return; }
            var m = AssetDatabase.LoadAssetAtPath<Material>(MaterialPath);
            if (m == null) { m = new Material(shader) { name = "Cartoon_Silhouette" }; AssetDatabase.CreateAsset(m, MaterialPath); }
            else if (m.shader != shader) { m.shader = shader; EditorUtility.SetDirty(m); }
            var reg = AssetDatabase.LoadAssetAtPath<ArtMaterials>("Assets/_Game/Settings/Resources/ArtMaterials.asset");
            if (reg == null) { Debug.LogError("[MERIDIAN] CartoonSetup: no ArtMaterials registry"); return; }
            if (reg.cartoon != m) { reg.cartoon = m; EditorUtility.SetDirty(reg); }
            AssetDatabase.SaveAssets();
            Debug.Log($"[MERIDIAN] CartoonSetup: {MaterialPath} in the registry");
        }
    }
}
