using Meridian.Rendering;
using UnityEditor;
using UnityEngine;

namespace Meridian.EditorTools
{
    /// <summary>
    /// U-182: the smooth ground's tier fill material (MERIDIAN/GroundTiers) in the ArtMaterials registry, so builds keep the shader
    /// (SmoothGround clones it per fill texture). Idempotent; CheckSetup runs it, or -ExecuteMethod Meridian.EditorTools.GroundTiersSetup.Run.
    /// </summary>
    public static class GroundTiersSetup
    {
        public const string MaterialPath = "Assets/_Game/Settings/Materials/GroundTiers.mat";
        public const string ShaderName = "MERIDIAN/GroundTiers";

        [MenuItem("MERIDIAN/Rendering/Ground tier fill material (U-182)")]
        public static void Run()
        {
            var shader = Shader.Find(ShaderName);
            if (shader == null) { Debug.LogError($"[MERIDIAN] GroundTiersSetup: shader {ShaderName} not found"); return; }
            var m = AssetDatabase.LoadAssetAtPath<Material>(MaterialPath);
            if (m == null)
            {
                System.IO.Directory.CreateDirectory(System.IO.Path.GetDirectoryName(MaterialPath));
                m = new Material(shader) { name = "GroundTiers" };
                AssetDatabase.CreateAsset(m, MaterialPath);
            }
            else if (m.shader != shader) { m.shader = shader; EditorUtility.SetDirty(m); }
            var reg = AssetDatabase.LoadAssetAtPath<ArtMaterials>(DiscSetup.RegistryPath);
            if (reg == null) { Debug.LogError("[MERIDIAN] GroundTiersSetup: no ArtMaterials registry"); return; }
            if (reg.groundTiers != m) { reg.groundTiers = m; EditorUtility.SetDirty(reg); AssetDatabase.SaveAssets(); Debug.Log($"[MERIDIAN] GroundTiersSetup: {MaterialPath} in the registry"); }
        }
    }
}
