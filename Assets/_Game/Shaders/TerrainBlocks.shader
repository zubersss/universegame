// U-073 (Bible 2.0 §10.4/§10.5): terrain block mesh shader. Albedo comes from a per-planet Texture2DArray indexed by
// the layer in uv0.z (top/side layer per tile material, back wall last; flat placeholder colours until B-080). Lit by
// URP (main light + shadows, additional lights incl. the Forward+ cluster loop, ambient SH, fog). Owner: UNITY.
Shader "MERIDIAN/TerrainBlocks"
{
    Properties
    {
        _BlockArray ("Block layers (colour)", 2DArray) = "" {}
        _BlockNormals ("Block layers (normal)", 2DArray) = "" {}
        _BlockMasks ("Block layers (mask: G AO, A smoothness)", 2DArray) = "" {}
        _Smoothness ("Smoothness (placeholder palette)", Range(0, 1)) = 0.12
        _WallDarken ("Back wall darkening", Range(0, 1)) = 0.55
        _FringeLayer ("Grass side layer (D-067 fringe)", Float) = -10
        _FringeDepth ("Fringe depth (m)", Float) = 0.08
    }
    SubShader
    {
        Tags { "RenderType" = "Opaque" "RenderPipeline" = "UniversalPipeline" "Queue" = "Geometry" }

        HLSLINCLUDE
        #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
        CBUFFER_START(UnityPerMaterial)
            half _Smoothness;
            half _WallDarken;
            float _FringeLayer;
            float _FringeDepth;
        CBUFFER_END
        TEXTURE2D_ARRAY(_BlockArray);
        SAMPLER(sampler_BlockArray);
        TEXTURE2D_ARRAY(_BlockNormals);
        TEXTURE2D_ARRAY(_BlockMasks);
        ENDHLSL

        Pass
        {
            Name "ForwardLit"
            Tags { "LightMode" = "UniversalForward" }
            Cull Back
            ZWrite On

            HLSLPROGRAM
            #pragma target 3.5
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE _MAIN_LIGHT_SHADOWS_SCREEN
            #pragma multi_compile _ _ADDITIONAL_LIGHTS_VERTEX _ADDITIONAL_LIGHTS
            #pragma multi_compile_fragment _ _ADDITIONAL_LIGHT_SHADOWS
            #pragma multi_compile_fragment _ _SHADOWS_SOFT _SHADOWS_SOFT_LOW _SHADOWS_SOFT_MEDIUM _SHADOWS_SOFT_HIGH
            #pragma multi_compile _ _CLUSTER_LIGHT_LOOP
            #pragma multi_compile_fog
            // Real block textures (B-080) vs the flat placeholder palette; set at runtime, so multi_compile (not stripped).
            #pragma multi_compile_local _ _BLOCK_MAPS

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"

            struct Attributes
            {
                float4 positionOS : POSITION;
                float3 normalOS   : NORMAL;
                float3 uv         : TEXCOORD0; // xy: world-planar UV, z: array layer
            };

            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float3 positionWS : TEXCOORD0;
                float3 normalWS   : TEXCOORD1;
                float3 uv         : TEXCOORD2;
                half   fogFactor  : TEXCOORD3;
            };

            Varyings vert(Attributes i)
            {
                Varyings o;
                VertexPositionInputs p = GetVertexPositionInputs(i.positionOS.xyz);
                o.positionCS = p.positionCS;
                o.positionWS = p.positionWS;
                o.normalWS = TransformObjectToWorldNormal(i.normalOS);
                o.uv = i.uv;
                o.fogFactor = ComputeFogFactor(p.positionCS.z);
                return o;
            }

            half4 frag(Varyings i) : SV_Target
            {
                half4 albedo = SAMPLE_TEXTURE2D_ARRAY(_BlockArray, sampler_BlockArray, i.uv.xy, i.uv.z);
                float3 n = normalize(i.normalWS);

                // D-067: on a grass block's side faces (not tops/bottoms), the top colour runs down the top few cm of the
                // cell, so the turf edge reads without a painted fringe. Grass sits at the surface, so its cell top is air.
                if (abs(i.uv.z - _FringeLayer) < 0.5 && abs(n.y) < 0.5)
                {
                    float below = 1.0 - frac(i.positionWS.y);           // metres below the cell's top edge
                    half f = 1.0 - smoothstep(_FringeDepth * 0.5, _FringeDepth, below);
                    half4 topCol = SAMPLE_TEXTURE2D_ARRAY(_BlockArray, sampler_BlockArray, i.uv.xy, _FringeLayer - 1.0);
                    albedo.rgb = lerp(albedo.rgb, topCol.rgb, f);
                }

                // The back wall sits in shade behind the play plane: darker than the blocks of the same rock.
                float wall = step(0.75, i.positionWS.z - unity_ObjectToWorld._m23); // the wall is at z +1; block sides end at +0.5
                albedo.rgb *= lerp(1.0, 1.0 - _WallDarken, wall);

                half smoothness = _Smoothness, occlusion = 1;
                float3 normalWS = n;
            #if defined(_BLOCK_MAPS)
                // Axis-aligned faces: the tangent frame follows the planar UVs (fronts/walls x,y; tops/bottoms x,z; sides z,y).
                float3 t = abs(n.x) > 0.5 ? float3(0, 0, 1) : float3(1, 0, 0);
                float3 b = abs(n.y) > 0.5 ? float3(0, 0, 1) : float3(0, 1, 0);
                half3 nTS = UnpackNormal(SAMPLE_TEXTURE2D_ARRAY(_BlockNormals, sampler_BlockArray, i.uv.xy, i.uv.z));
                normalWS = normalize(t * nTS.x + b * nTS.y + n * nTS.z);
                half4 mask = SAMPLE_TEXTURE2D_ARRAY(_BlockMasks, sampler_BlockArray, i.uv.xy, i.uv.z);
                smoothness = mask.a;
                occlusion = mask.g;
            #endif

                InputData input = (InputData)0;
                input.positionWS = i.positionWS;
                input.positionCS = i.positionCS;
                input.normalWS = normalWS;
                input.viewDirectionWS = GetWorldSpaceNormalizeViewDir(i.positionWS);
                input.shadowCoord = TransformWorldToShadowCoord(i.positionWS);
                input.fogCoord = i.fogFactor;
                input.bakedGI = SampleSH(input.normalWS);
                input.normalizedScreenSpaceUV = GetNormalizedScreenSpaceUV(i.positionCS);
                input.shadowMask = half4(1, 1, 1, 1);

                SurfaceData s = (SurfaceData)0;
                s.albedo = albedo.rgb;
                s.alpha = 1;
                s.metallic = 0;
                s.smoothness = smoothness;
                s.occlusion = occlusion;
                s.normalTS = half3(0, 0, 1);

                half4 color = UniversalFragmentPBR(input, s);
                color.rgb = MixFog(color.rgb, input.fogCoord);
                return color;
            }
            ENDHLSL
        }

        Pass
        {
            Name "ShadowCaster"
            Tags { "LightMode" = "ShadowCaster" }
            ZWrite On
            ZTest LEqual
            ColorMask 0
            Cull Back

            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_vertex _ _CASTING_PUNCTUAL_LIGHT_SHADOW
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Shadows.hlsl"

            float3 _LightDirection;
            float3 _LightPosition;

            struct Attributes { float4 positionOS : POSITION; float3 normalOS : NORMAL; };

            float4 vert(Attributes i) : SV_POSITION
            {
                float3 p = TransformObjectToWorld(i.positionOS.xyz);
                float3 n = TransformObjectToWorldNormal(i.normalOS);
            #if _CASTING_PUNCTUAL_LIGHT_SHADOW
                float3 l = normalize(_LightPosition - p);
            #else
                float3 l = _LightDirection;
            #endif
                float4 c = TransformWorldToHClip(ApplyShadowBias(p, n, l));
            #if UNITY_REVERSED_Z
                c.z = min(c.z, UNITY_NEAR_CLIP_VALUE);
            #else
                c.z = max(c.z, UNITY_NEAR_CLIP_VALUE);
            #endif
                return c;
            }

            half4 frag() : SV_Target { return 0; }
            ENDHLSL
        }

        Pass
        {
            Name "DepthOnly"
            Tags { "LightMode" = "DepthOnly" }
            ZWrite On
            ColorMask R
            Cull Back

            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            struct Attributes { float4 positionOS : POSITION; };
            float4 vert(Attributes i) : SV_POSITION { return TransformObjectToHClip(i.positionOS.xyz); }
            half frag() : SV_Target { return 0; }
            ENDHLSL
        }
    }
    FallBack Off
}
