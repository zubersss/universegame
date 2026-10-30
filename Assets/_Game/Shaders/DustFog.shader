// Mars dust storm fog (U-026, Bible §7.2): a camera-covering quad drawn over the world while a storm
// blows. Thin dust near the player, opaque dust beyond _Visibility metres from _Center (the player's
// chest), with drifting streaks. One blended pass, enabled only during storms. _Flash brightens it for
// static discharges.
Shader "MERIDIAN/DustFog"
{
    Properties
    {
        _Center ("Center (world xy)", Vector) = (0, 0, 0, 0)
        _Visibility ("Visibility (m)", Float) = 15
        _Intensity ("Intensity 0..1", Float) = 1
        _DustColor ("Dust color", Color) = (0.72, 0.5, 0.33, 1)
        _Flash ("Discharge flash", Float) = 0
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

            CBUFFER_START(UnityPerMaterial)
                float4 _Center;
                float _Visibility;
                float _Intensity;
                float4 _DustColor;
                float _Flash;
            CBUFFER_END

            struct Attributes { float4 positionOS : POSITION; };
            struct Varyings { float4 positionCS : SV_POSITION; float2 worldXY : TEXCOORD0; };

            Varyings vert(Attributes v)
            {
                Varyings o;
                float3 ws = TransformObjectToWorld(v.positionOS.xyz);
                o.positionCS = TransformWorldToHClip(ws);
                o.worldXY = ws.xy;
                return o;
            }

            float Hash(float2 p) { return frac(sin(dot(p, float2(127.1, 311.7))) * 43758.5453); }

            float Noise(float2 p)
            {
                float2 i = floor(p), f = frac(p);
                f = f * f * (3.0 - 2.0 * f);
                return lerp(lerp(Hash(i), Hash(i + float2(1, 0)), f.x), lerp(Hash(i + float2(0, 1)), Hash(i + float2(1, 1)), f.x), f.y);
            }

            half4 frag(Varyings i) : SV_Target
            {
                float d = distance(i.worldXY, _Center.xy);
                // Wind-stretched streaks drifting right to left.
                float2 p = float2(i.worldXY.x * 0.12 + _Time.y * 1.9, i.worldXY.y * 0.45);
                float n = Noise(p) * 0.65 + Noise(p * 2.7 + 13.1) * 0.35;
                float far = smoothstep(_Visibility * 0.45, _Visibility, d);
                float a = _Intensity * saturate(0.18 + 0.82 * far + (n - 0.5) * 0.25 * (1.0 - far));
                half3 col = _DustColor.rgb * (0.9 + 0.2 * n) * (1.0 + 1.5 * _Flash);
                return half4(col, a);
            }
            ENDHLSL
        }
    }
}
