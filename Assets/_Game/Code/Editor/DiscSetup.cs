using Meridian.Rendering;
using UnityEditor;
using UnityEngine;

namespace Meridian.EditorTools
{
    /// <summary>
    /// U-117 (cycle 257): the painted planet discs' material (MERIDIAN/Sprite_LitDisc) in the ArtMaterials registry. The 64-px disc
    /// frames carry a hard one-texel alpha limb; at the near-range zoom the plain lit sprite material drew it as 10-px stairs
    /// (space_6_pilgrim). The disc shader resolves the sampled alpha at its 0.5 iso-line with a one-pixel anti-aliased edge: alpha
    /// blend, no cutoff. Idempotent; CheckSetup runs it, or -ExecuteMethod Meridian.EditorTools.DiscSetup.Run, or the menu.
    /// </summary>
    public static class DiscSetup
    {
        public const string MaterialPath = "Assets/_Game/Settings/Materials/Sprite_LitDisc.mat";
        public const string ShaderName = "MERIDIAN/Sprite_LitDisc";
        public const string RegistryPath = "Assets/_Game/Settings/Resources/ArtMaterials.asset";

        [MenuItem("MERIDIAN/Rendering/Planet disc material (U-117)")]
        public static void Run()
        {
            var shader = Shader.Find(ShaderName);
            if (shader == null) { Debug.LogError($"[MERIDIAN] DiscSetup: shader {ShaderName} not found"); return; }
            var m = AssetDatabase.LoadAssetAtPath<Material>(MaterialPath);
            if (m == null)
            {
                System.IO.Directory.CreateDirectory(System.IO.Path.GetDirectoryName(MaterialPath));
                m = new Material(shader) { name = "Sprite_LitDisc" };
                AssetDatabase.CreateAsset(m, MaterialPath);
            }
            else if (m.shader != shader) { m.shader = shader; EditorUtility.SetDirty(m); }
            var reg = AssetDatabase.LoadAssetAtPath<ArtMaterials>(RegistryPath);
            if (reg == null) { Debug.LogError("[MERIDIAN] DiscSetup: no ArtMaterials registry"); return; }
            if (reg.disc != m) { reg.disc = m; EditorUtility.SetDirty(reg); AssetDatabase.SaveAssets(); Debug.Log($"[MERIDIAN] DiscSetup: {MaterialPath} in the registry"); }
        }
    }
}
