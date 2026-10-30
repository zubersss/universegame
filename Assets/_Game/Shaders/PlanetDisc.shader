// Top-down planet disc (Bible §10.5): equirect texture projected onto a sphere seen as a disc,
// rotation offset, terminator from the Sun direction, atmosphere rim. _Emissive = 1 for the Sun.
// Hand-written HLSL in place of PlanetDisc.shadergraph (UNITY P-12).
Shader "MERIDIAN/PlanetDisc"
{
    Properties
    {
        _MainTex ("Surface (equirect)", 2D) = "white" {}
        _Tint ("Tint", Color) = (1,1,1,1)
        _Rotation ("Rotation (0..1 of a turn)", Float) = 0
        _SunDir ("Sun direction (disc space)", Vector) = (-1,0,0.35,0)
        _AtmoColor ("Atmosphere color", Color) = (0.45,0.65,1,1)
        _AtmoWidth ("Atmosphere width (of radius)", Float) = 0.08
        _Ambient ("Night-side ambient", Float) = 0.06
        _Emissive ("Self-lit (Sun)", Float) = 0
    }
    SubShader
    {
        Tags { "RenderType"="Transparent" "Queue"="Transparent" "RenderPipeline"="UniversalPipeline" }
        Blend SrcAlpha OneMinusSrcAlpha
        ZWrite Off
        Cull Off

        Pass
        {
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

            TEXTURE2D(_MainTex); SAMPLER(sampler_MainTex);
            CBUFFER_START(UnityPerMaterial)
                float4 _MainTex_ST;
                float4 _Tint;
                float _Rotation;
                float4 _SunDir;
                float4 _AtmoColor;
                float _AtmoWidth;
                float _Ambient;
                float _Emissive;
            CBUFFER_END

            struct Attributes { float4 positionOS : POSITION; float2 uv : TEXCOORD0; };
            struct Varyings { float4 positionCS : SV_POSITION; float2 uv : TEXCOORD0; };

            Varyings vert(Attributes v)
            {
                Varyings o;
                o.positionCS = TransformObjectToHClip(v.positionOS.xyz);
                o.uv = v.uv;
                return o;
            }

            half4 frag(Varyings i) : SV_Target
            {
                // The quad spans the disc plus the atmosphere band.
                float outer = 1.0 + _AtmoWidth;
                float2 p = (i.uv * 2.0 - 1.0) * outer;
                float r2 = dot(p, p);
                float3 sun = normalize(_SunDir.xyz);

                if (r2 > 1.0)
                {
                    float r = sqrt(r2);
                    float t = saturate(1.0 - (r - 1.0) / max(_AtmoWidth, 1e-4));
                    float lit = _Emissive > 0.5 ? 1.0 : saturate(dot(normalize(float3(p, 0.0)), sun) * 0.8 + 0.35);
                    return half4(_AtmoColor.rgb, t * t * _AtmoColor.a * lit);
                }

                float z = sqrt(1.0 - r2);
                float3 n = float3(p, z);
                float lon = atan2(p.x, z) / (2.0 * PI) + 0.5 + _Rotation;
                float lat = asin(clamp(p.y, -1.0, 1.0)) / PI + 0.5;
                half3 albedo = SAMPLE_TEXTURE2D(_MainTex, sampler_MainTex, float2(frac(lon), lat)).rgb * _Tint.rgb;

                if (_Emissive > 0.5)
                    return half4(albedo * (0.85 + 0.15 * z), 1.0);

                float light = saturate(dot(n, sun));
                float rim = pow(1.0 - z, 3.0) * saturate(dot(normalize(float3(p, 0.0)), sun) + 0.3);
                half3 color = albedo * (_Ambient + (1.0 - _Ambient) * light) + _AtmoColor.rgb * rim * 0.6;
                return half4(color, 1.0);
            }
            ENDHLSL
        }
    }
}
