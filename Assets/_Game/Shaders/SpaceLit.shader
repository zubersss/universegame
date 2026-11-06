// U-078 (Bible §10.5 v2): the Space view's one lit surface. Everything in Space is lit by the Sun at the
// origin: the light direction is computed per fragment from the world position (planets, moons, rocks and
// stations each get their own terminator), tilted a little toward the top-down camera (_SunTilt) so the lit
// hemisphere reads from above as the old PlanetDisc did. Modes by property, one shader for the lot:
//   planets  — _MainTex is the equirect surface sampled by the spheroid's UVs (see SpaceMeshes.Spheroid)
//   clouds   — _AlphaFromTex 1: the cloud sheet's alpha is the shell's coverage, slowly turning (_Rotation)
//   atmo     — _AtmoShell 1: no texture, _AtmoColor with a Fresnel alpha (rim) on a slightly larger shell
//   rocks / stations — _MainTex + _EmissionMap on their meshes (GPU instancing for the belt)
//   the Sun  — _Emissive 1: unlit, albedo as is
// Hand-written HLSL as PlanetDisc.shader (UNITY P-12). No scene lights are needed in Space.
Shader "MERIDIAN/SpaceLit"
{
    Properties
    {
        _MainTex ("Albedo", 2D) = "white" {}
        _EmissionMap ("Emission", 2D) = "black" {}
        _Tint ("Tint", Color) = (1,1,1,1)
        _Rotation ("Rotation (0..1 of a turn, u offset)", Float) = 0
        _SunTilt ("Sun tilt toward the camera", Float) = 0.35
        _Ambient ("Night-side ambient", Float) = 0.06
        _Emissive ("Self-lit (Sun)", Float) = 0
        _EmissionScale ("Emission scale", Float) = 1
        _AtmoColor ("Atmosphere color", Color) = (0.45,0.65,1,1)
        _AtmoShell ("Atmosphere shell (Fresnel alpha only)", Float) = 0
        _RimPower ("Rim power", Float) = 3
        _RimStrength ("Rim strength on the surface", Float) = 0.6
        _AlphaFromTex ("Alpha from the albedo texture", Float) = 0
        _Cull ("Cull", Float) = 2
        _Radial ("Radial sampling (ring sheets)", Float) = 0
    }
    SubShader
    {
        Tags { "RenderType"="Transparent" "Queue"="Transparent" "RenderPipeline"="UniversalPipeline" }
        Blend SrcAlpha OneMinusSrcAlpha
        ZWrite Off
        Cull [_Cull]

        Pass
        {
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_instancing
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

            TEXTURE2D(_MainTex); SAMPLER(sampler_MainTex);
            TEXTURE2D(_EmissionMap); SAMPLER(sampler_EmissionMap);
            CBUFFER_START(UnityPerMaterial)
                float4 _MainTex_ST;
                float4 _Tint;
                float _Rotation;
                float _SunTilt;
                float _Ambient;
                float _Emissive;
                float _EmissionScale;
                float4 _AtmoColor;
                float _AtmoShell;
                float _RimPower;
                float _RimStrength;
                float _AlphaFromTex;
                float _Cull;
                float _Radial;
            CBUFFER_END

            struct Attributes
            {
                float4 positionOS : POSITION;
                float3 normalOS : NORMAL;
                float2 uv : TEXCOORD0;
                UNITY_VERTEX_INPUT_INSTANCE_ID
            };
            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float3 positionWS : TEXCOORD0;
                float3 normalWS : TEXCOORD1;
                float2 uv : TEXCOORD2;
                float shade : TEXCOORD3;
                UNITY_VERTEX_INPUT_INSTANCE_ID
            };

            Varyings vert(Attributes v)
            {
                Varyings o;
                UNITY_SETUP_INSTANCE_ID(v);
                UNITY_TRANSFER_INSTANCE_ID(v, o);
                o.positionWS = TransformObjectToWorld(v.positionOS.xyz);
                o.positionCS = TransformWorldToHClip(o.positionWS);
                o.normalWS = TransformObjectToWorldNormal(v.normalOS);
                o.uv = TRANSFORM_TEX(v.uv, _MainTex) + float2(_Rotation, 0.0);
                o.shade = 1.0;
#ifdef UNITY_INSTANCING_ENABLED
                // The belt: a per-rock albedo variation without per-instance data (as the old sprite shades, 185–255).
                uint id = unity_InstanceID;
                o.shade = 0.72 + 0.28 * frac(id * 0.6180339887);
#endif
                return o;
            }

            half4 frag(Varyings i) : SV_Target
            {
                UNITY_SETUP_INSTANCE_ID(i);
                float3 n = normalize(i.normalWS);
                // The Sun sits at the world origin; the light comes from there, tilted toward the camera (-z).
                float2 toSun2 = -i.positionWS.xy;
                float len = max(length(toSun2), 1e-3);
                float3 sun = normalize(float3(toSun2 / len, -_SunTilt));
                float facing = saturate(-n.z); // 1 at the centre of the visible disc, 0 at its edge

                if (_AtmoShell > 0.5)
                {
                    // A halo on the shell: strongest just inside its silhouette, fading to nothing at the very
                    // edge (smoothstep) and inward over the globe (the rim power), lit on the Sun's side.
                    float litRim = saturate(dot(normalize(float3(n.xy, 0.0)), sun) * 0.8 + 0.35);
                    float a = pow(1.0 - facing, _RimPower) * smoothstep(0.0, 0.3, facing) * _AtmoColor.a * litRim;
                    return half4(_AtmoColor.rgb, a);
                }

                half4 tex;
                if (_Radial > 0.5)
                {
                    // U-086: a ring sheet is circles of bands, so sample the planar sheet along four radii and average: the texel
                    // grid never shows as stair steps or moire at any zoom, and the mips still work along the radius.
                    float r = length(i.uv - 0.5);
                    tex = 0.25 * (SAMPLE_TEXTURE2D(_MainTex, sampler_MainTex, float2(0.5 + r, 0.5)) + SAMPLE_TEXTURE2D(_MainTex, sampler_MainTex, float2(0.5 - r, 0.5))
                                + SAMPLE_TEXTURE2D(_MainTex, sampler_MainTex, float2(0.5, 0.5 + r)) + SAMPLE_TEXTURE2D(_MainTex, sampler_MainTex, float2(0.5, 0.5 - r)));
                }
                else tex = SAMPLE_TEXTURE2D(_MainTex, sampler_MainTex, i.uv);
                half3 albedo = tex.rgb * _Tint.rgb * i.shade;
                // _AlphaFromTex 1: the texture's alpha; 2: alpha × luminance (cloud sheets that may be opaque white-on-black).
                float lum = dot(tex.rgb, float3(0.299, 0.587, 0.114));
                float alpha = _AlphaFromTex > 1.5 ? tex.a * lum * _Tint.a : (_AlphaFromTex > 0.5 ? tex.a * _Tint.a : _Tint.a);

                if (_Emissive > 0.5)
                    return half4(albedo * (0.85 + 0.15 * facing), alpha);

                float light = saturate(dot(n, sun));
                float rim = pow(1.0 - facing, _RimPower) * saturate(dot(normalize(float3(n.xy, 0.0)), sun) + 0.3);
                half3 emission = SAMPLE_TEXTURE2D(_EmissionMap, sampler_EmissionMap, i.uv).rgb * _EmissionScale;
                half3 color = albedo * (_Ambient + (1.0 - _Ambient) * light) + _AtmoColor.rgb * rim * _RimStrength + emission;
                return half4(color, alpha);
            }
            ENDHLSL
        }
    }
}
