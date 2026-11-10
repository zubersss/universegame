// LivingStage (U-216, D-205 / D-206; the piece format of contract §12): one mesh a layer, every vertex carrying its
// piece's root, bend weight, give and phase; the wind moves them here from a few global constants (LivingWind.hlsl).
// Unlit by default: the painted light is in the colour. With LIVING_LIT the 2D renderer's lights are taken through the
// normal map (the pilot's "one lit piece"), an added light held back where the paint is already near white.
// The passes and includes are URP 17.6's Sprite-Lit-Default as GroundTiers.shader uses them on a MeshRenderer.
Shader "MERIDIAN/LivingStage"
{
    Properties
    {
        _MainTex("Diffuse", 2D) = "white" {}
        _MaskTex("Mask", 2D) = "white" {}
        _NormalMap("Normal Map", 2D) = "bump" {}
        _HoldBack("Added light held back on bright paint", Range(0, 1)) = 1
        [Toggle(LIVING_LIT)] _Lit("Takes the 2D lights", Float) = 0

        [HideInInspector] _Color("Tint", Color) = (1,1,1,1)
    }

    SubShader
    {
        Tags {"Queue" = "Transparent" "RenderType" = "Transparent" "RenderPipeline" = "UniversalPipeline" }

        Blend SrcAlpha OneMinusSrcAlpha, One OneMinusSrcAlpha
        Cull Off
        ZWrite Off

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
            #pragma shader_feature_local _ LIVING_LIT

            struct Attributes
            {
                COMMON_2D_INPUTS
                half4 color        : COLOR;
                float4 sway        : TEXCOORD1;
                float4 sway2       : TEXCOORD2;
            };

            struct Varyings
            {
                COMMON_2D_LIT_OUTPUTS
                half4 color        : COLOR;
            };

            #include "Packages/com.unity.render-pipelines.universal/Shaders/2D/Include/Lit2DCommon.hlsl"

            CBUFFER_START(UnityPerMaterial)
                half4 _Color;
                half _HoldBack;
            CBUFFER_END

            #include "LivingWind.hlsl"

            Varyings LitVertex(Attributes input)
            {
                input.positionOS = LivingBend(input.positionOS, input.sway, input.sway2);
                Varyings o = CommonLitVertex(input);
                o.color = input.color * _Color;
                return o;
            }

            half4 LitFragment(Varyings input) : SV_Target
            {
                const half4 main = input.color * SAMPLE_TEXTURE2D(_MainTex, sampler_MainTex, input.uv);
            #if defined(LIVING_LIT)
                const half4 mask = half4(1, 1, 1, 1);
                const half3 normalTS = half3(0, 0, 1); // the lights read the normals pass; this one is the debug view's
                SurfaceData2D surfaceData;
                InputData2D inputData;
                InitializeSurfaceData(main.rgb, main.a, mask, normalTS, surfaceData);
                InitializeInputData(input.uv, input.lightingUV, inputData);
            #if defined(DEBUG_DISPLAY)
                SETUP_DEBUG_TEXTURE_DATA_2D_NO_TS(inputData, input.positionWS, input.positionCS, _MainTex);
                surfaceData.normalWS = input.normalWS;
            #endif
                half4 lit = CombinedShapeLightShared(surfaceData, inputData);
                // D-206: the painted light is in the colour; what the game's lights ADD is held back where the paint is near white
                half3 added = max(lit.rgb - main.rgb, 0);
                half bright = smoothstep(0.6, 1.0, dot(main.rgb, half3(0.299, 0.587, 0.114)));
                lit.rgb -= added * bright * _HoldBack;
                return lit;
            #else
                return main;
            #endif
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
                COMMON_2D_INPUTS
                float4 color        : COLOR;
                float4 sway         : TEXCOORD1;
                float4 sway2        : TEXCOORD2;
            };

            struct Varyings
            {
                float4 positionCS   : SV_POSITION;
                float2 uv           : TEXCOORD0;
                half   side         : TEXCOORD1;
                half4  color        : COLOR;
                UNITY_VERTEX_OUTPUT_STEREO
            };

            TEXTURE2D(_MainTex);
            SAMPLER(sampler_MainTex);
            TEXTURE2D(_NormalMap);
            SAMPLER(sampler_NormalMap);

            CBUFFER_START(UnityPerMaterial)
                half4 _Color;
                half _HoldBack;
            CBUFFER_END

            #include "LivingWind.hlsl"

            Varyings NormalsRenderingVertex(Attributes input)
            {
                Varyings o = (Varyings)0;
                UNITY_SETUP_INSTANCE_ID(input);
                UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(o);
                input.positionOS = LivingBend(input.positionOS, input.sway, input.sway2);
                o.positionCS = TransformObjectToHClip(input.positionOS);
                o.uv = input.uv;
                o.side = input.sway2.y;
                o.color = input.color * _Color;
                return o;
            }

            half4 NormalsRenderingFragment(Varyings input) : SV_Target
            {
                const half4 main = input.color * SAMPLE_TEXTURE2D(_MainTex, sampler_MainTex, input.uv);
                half3 normalTS = UnpackNormal(SAMPLE_TEXTURE2D(_NormalMap, sampler_NormalMap, input.uv));
                // the stage faces the camera: tangent +x, bitangent +y, the face's normal toward the viewer (-z);
                // a mirrored instance (foreground and far only) mirrors the normal's x
                half3 normalWS = half3(normalTS.x * input.side, normalTS.y, -normalTS.z);
                half4 normalColor;
                normalColor.rgb = 0.5 * (normalWS + 1);
                normalColor.a = main.a; // used for blending
                return normalColor;
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
                float4 sway  : TEXCOORD1;
                float4 sway2 : TEXCOORD2;
            };

            struct Varyings
            {
                COMMON_2D_OUTPUTS
                half4 color : COLOR;
            };

            #include "Packages/com.unity.render-pipelines.universal/Shaders/2D/Include/2DCommon.hlsl"

            #pragma multi_compile_instancing
            #pragma multi_compile _ DEBUG_DISPLAY

            CBUFFER_START(UnityPerMaterial)
                half4 _Color;
                half _HoldBack;
            CBUFFER_END

            #include "LivingWind.hlsl"

            Varyings UnlitVertex(Attributes input)
            {
                input.positionOS = LivingBend(input.positionOS, input.sway, input.sway2);
                Varyings o = CommonUnlitVertex(input);
                o.color = input.color * _Color;
                return o;
            }

            half4 UnlitFragment(Varyings input) : SV_Target
            {
                return CommonUnlitFragment(input, input.color);
            }
            ENDHLSL
        }
    }
}
