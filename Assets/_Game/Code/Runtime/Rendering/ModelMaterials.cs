using UnityEngine;

namespace Meridian.Rendering
{
    /// <summary>
    /// U-075 (contract v2.1 §9.1, D-063): a model's URP/Lit material from its four PNG maps (the glb carries none).
    /// Mask channels: R metallic, G ambient occlusion, B rim (reserved for the interact rim), A smoothness. URP/Lit
    /// reads metallic from R and smoothness from A of _MetallicGlossMap and occlusion from G of _OcclusionMap, so the
    /// mask serves both slots unchanged. Used by ArtImporter v5 at import and by the art preview.
    /// </summary>
    public static class ModelMaterials
    {
        public static Material FromMaps(Texture2D color, Texture2D normal, Texture2D mask, Texture2D emission, string name)
        {
            var reg = ArtMaterials.Active;
            var template = emission != null ? reg?.meshLitEmissive : reg?.meshLit;
            var m = template != null ? new Material(template) : new Material(Shader.Find("Universal Render Pipeline/Lit"));
            m.name = name;
            if (color != null) { m.SetTexture("_BaseMap", color); m.SetColor("_BaseColor", Color.white); }
            if (normal != null) { m.SetTexture("_BumpMap", normal); m.EnableKeyword("_NORMALMAP"); m.SetFloat("_BumpScale", 1f); }
            if (mask != null)
            {
                m.SetTexture("_MetallicGlossMap", mask);
                m.EnableKeyword("_METALLICSPECGLOSSMAP");
                m.SetFloat("_Smoothness", 1f);          // scales the map's A
                m.SetFloat("_GlossMapScale", 1f);
                m.SetTexture("_OcclusionMap", mask);
                m.EnableKeyword("_OCCLUSIONMAP");
                m.SetFloat("_OcclusionStrength", 1f);
            }
            if (emission != null)
            {
                m.SetTexture("_EmissionMap", emission);
                m.EnableKeyword("_EMISSION");
                m.SetColor("_EmissionColor", Color.white);
                m.globalIlluminationFlags = MaterialGlobalIlluminationFlags.RealtimeEmissive;
            }
            else m.DisableKeyword("_EMISSION");
            return m;
        }

        /// <summary>
        /// D-082 (contract v2.6 ruling 10): a model whose sidecar says alpha_clip draws cut-out (cutoff 0.5) and double-sided:
        /// the B-109 canopy cards on the shared flora atlas. URP/Lit alpha clipping keys off _AlphaClip + _ALPHATEST_ON.
        /// </summary>
        public static void SetAlphaClip(Material m)
        {
            m.SetFloat("_AlphaClip", 1f);
            m.SetFloat("_Cutoff", 0.5f);
            m.EnableKeyword("_ALPHATEST_ON");
            m.SetFloat("_Cull", (float)UnityEngine.Rendering.CullMode.Off);
            m.doubleSidedGI = true;
            m.renderQueue = (int)UnityEngine.Rendering.RenderQueue.AlphaTest;
            m.SetOverrideTag("RenderType", "TransparentCutout");
        }
    }
}
