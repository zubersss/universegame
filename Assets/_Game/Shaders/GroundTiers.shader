// GroundTiers (U-182, D1; B-203's ground_fill_t2..t5): the smooth ground's fill by depth tier. URP 2D Sprite-Lit (as Sprite_LitEmissive,
// D-023), the base colour blended from five fill textures by the depth under the Surface Line: _LineTex is one texel per world column holding
// the line's world height there (built once per planet, SmoothGround.LineTexture), sampled bilinearly at u = x / columns (Repeat: the
// planet wraps), so the bands follow the curved line. The mesh's uv is world / 8 (B-175's fill mapping, 8 m a tile): the world point is
// uv * 8. Each tier fades in across its transition (B-203's transition_m) centred on its depth (D1_TABLES §1), smoothstepped: no step.
Shader "MERIDIAN/GroundTiers"
{
    Properties
    {
        _MainTex("Tier 1 (ground_fill)", 2D) = "white" {}
        _Tier2Tex("Tier 2", 2D) = "white" {}
        _Tier3Tex("Tier 3", 2D) = "white" {}
        _Tier4Tex("Tier 4", 2D) = "white" {}
        _Tier5Tex("Tier 5", 2D) = "white" {}
        _LineTex("Surface Line by column (world y)", 2D) = "black" {}
        _LineParams("1 / columns, uv to world, line base, line span", Vector) = (0.000244, 8, 0, 1)
        _TierFrom("Tiers 2-5 from (m under the line)", Vector) = (10, 40, 100, 200)
        _TierBlend("Tiers 2-5 transition (m)", Vector) = (1, 1, 1, 1)
        _TileTexels("A fill tile's texels across", Float) = 512
        _RowShift("A tile row's shift along u (the back walls; 0 on the fills)", Float) = 0
        _MaskTex("Mask", 2D) = "white" {}
        _NormalMap("Normal Map", 2D) = "bump" {}
        [MaterialToggle] _ZWrite("ZWrite", Float) = 0

        [HideInInspector] _Color("Tint", Color) = (1,1,1,1)
        [HideInInspector] _RendererColor("RendererColor", Color) = (1,1,1,1)
        [HideInInspector] _AlphaTex("External Alpha", 2D) = "white" {}
        [HideInInspector] _EnableExternalAlpha("Enable External Alpha", Float) = 0
    }

    HLSLINCLUDE
        // The tier blend, shared by the lit and unlit passes. The tier textures are sampled with explicit gradients inside the branches.
        #define GROUND_TIERS_DECLS \
            TEXTURE2D(_Tier2Tex); SAMPLER(sampler_Tier2Tex); \
            TEXTURE2D(_Tier3Tex); SAMPLER(sampler_Tier3Tex); \
            TEXTURE2D(_Tier4Tex); SAMPLER(sampler_Tier4Tex); \
            TEXTURE2D(_Tier5Tex); SAMPLER(sampler_Tier5Tex); \
            TEXTURE2D(_LineTex); SAMPLER(sampler_LineTex);
    ENDHLSL

    SubShader
    {
        Tags {"Queue" = "Transparent" "RenderType" = "Transparent" "RenderPipeline" = "UniversalPipeline" }

        Blend SrcAlpha OneMinusSrcAlpha, One OneMinusSrcAlpha
        Cull Off
        ZWrite [_ZWrite]

        Pass
        {
            Tags { "LightMode" = "Universal2D" }

            HLSLPROGRAM
            #include "Packages/com.unity.render-pipelines.universal/Shaders/2D/Include/Core2D.hlsl"

            #pragma vertex LitVertex
            #pragma fragment LitFragment

            #include_with_pragmas "Packages/com.unity.render-pipelines.universal/Shaders/2D/Include/ShapeLightShared.hlsl"

            #pragma multi_compile_instancing
            #pragma multi_compile _ DEBUG_DISPLAY

            struct Attributes
            {
                COMMON_2D_INPUTS
                half4 color        : COLOR;
                UNITY_SKINNED_VERTEX_INPUTS
            };

            struct Varyings
            {
                COMMON_2D_LIT_OUTPUTS
                half4 color        : COLOR;
            };

            #include "Packages/com.unity.render-pipelines.universal/Shaders/2D/Include/Lit2DCommon.hlsl"

            GROUND_TIERS_DECLS

            CBUFFER_START(UnityPerMaterial)
                half4 _Color;
                float4 _LineParams;
                float4 _TierFrom;
                float4 _TierBlend;
                float _TileTexels;
                float _RowShift;
            CBUFFER_END

            #include "GroundTiers.hlsl"

            Varyings LitVertex(Attributes input)
            {
                UNITY_SKINNED_VERTEX_COMPUTE(input);
                SetUpSpriteInstanceProperties();
                Varyings o = CommonLitVertex(input);
                o.color = input.color * _Color * unity_SpriteColor;
                return o;
            }

            half4 LitFragment(Varyings input) : SV_Target
            {
                const half4 main = input.color * GroundTierColor(input.uv);
                // The fills carry no mask or normal map: their defaults (white, flat) as constants, two samples a pixel saved.
                const half4 mask = half4(1, 1, 1, 1);
                const half3 normalTS = half3(0, 0, 1);
                SurfaceData2D surfaceData;
                InputData2D inputData;
                InitializeSurfaceData(main.rgb, main.a, mask, normalTS, surfaceData);
                InitializeInputData(input.uv, input.lightingUV, inputData);
            #if defined(DEBUG_DISPLAY)
                SETUP_DEBUG_TEXTURE_DATA_2D_NO_TS(inputData, input.positionWS, input.positionCS, _MainTex);
                surfaceData.normalWS = input.normalWS;
            #endif
                return CombinedShapeLightShared(surfaceData, inputData);
            }
            ENDHLSL
        }

        Pass
        {
            Tags { "LightMode" = "NormalsRendering"}

            HLSLPROGRAM
            #include "Packages/com.unity.render-pipelines.universal/Shaders/2D/Include/Core2D.hlsl"

            #pragma vertex NormalsRenderingVertex
            #pragma fragment NormalsRenderingFragment

            #pragma multi_compile_instancing

            struct Attributes
            {
                COMMON_2D_NORMALS_INPUTS
                float4 color        : COLOR;
                UNITY_SKINNED_VERTEX_INPUTS
            };

            struct Varyings
            {
                COMMON_2D_NORMALS_OUTPUTS
                half4   color           : COLOR;
            };

            #include "Packages/com.unity.render-pipelines.universal/Shaders/2D/Include/Normals2DCommon.hlsl"

            CBUFFER_START( UnityPerMaterial )
                half4 _Color;
                float4 _LineParams;
                float4 _TierFrom;
                float4 _TierBlend;
                float _TileTexels;
                float _RowShift;
            CBUFFER_END

            Varyings NormalsRenderingVertex(Attributes input)
            {
                UNITY_SKINNED_VERTEX_COMPUTE(input);
                SetUpSpriteInstanceProperties();
                Varyings o = CommonNormalsVertex(input);
                o.color = input.color * _Color * unity_SpriteColor;
                return o;
            }

            half4 NormalsRenderingFragment(Varyings input) : SV_Target
            {
                SetUpSpriteInstanceProperties();
                return CommonNormalsFragment(input, input.color);
            }
            ENDHLSL
        }

        Pass
        {
            Tags { "LightMode" = "UniversalForward" "Queue"="Transparent" "RenderType"="Transparent"}

            HLSLPROGRAM
            #include "Packages/com.unity.render-pipelines.universal/Shaders/2D/Include/Core2D.hlsl"

            #pragma vertex UnlitVertex
            #pragma fragment UnlitFragment

            struct Attributes
            {
                COMMON_2D_INPUTS
                half4 color : COLOR;
                UNITY_SKINNED_VERTEX_INPUTS
            };

            struct Varyings
            {
                COMMON_2D_OUTPUTS
                half4 color : COLOR;
            };

            #include "Packages/com.unity.render-pipelines.universal/Shaders/2D/Include/2DCommon.hlsl"

            #pragma multi_compile_instancing
            #pragma multi_compile _ DEBUG_DISPLAY

            GROUND_TIERS_DECLS

            CBUFFER_START(UnityPerMaterial)
                half4 _Color;
                float4 _LineParams;
                float4 _TierFrom;
                float4 _TierBlend;
                float _TileTexels;
                float _RowShift;
            CBUFFER_END

            #include "GroundTiers.hlsl"

            Varyings UnlitVertex(Attributes input)
            {
                UNITY_SKINNED_VERTEX_COMPUTE(input);
                SetUpSpriteInstanceProperties();
                Varyings o = CommonUnlitVertex(input);
                o.color = input.color *_Color * unity_SpriteColor;
                return o;
            }

            half4 UnlitFragment(Varyings input) : SV_Target
            {
                return input.color * GroundTierColor(input.uv);
            }
            ENDHLSL
        }
    }
}
