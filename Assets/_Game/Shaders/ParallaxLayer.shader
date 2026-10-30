// Tiling background layer for parallax (U-022). The quad covers the camera view; the script
// feeds _UVScale (view size in tiles) and _UVOffset (camera position × parallax, in tiles).
Shader "MERIDIAN/ParallaxLayer"
{
    Properties
    {
        _MainTex ("Layer (tileable)", 2D) = "black" {}
        _UVScale ("UV scale", Vector) = (1,1,0,0)
        _UVOffset ("UV offset", Vector) = (0,0,0,0)
        _Tint ("Tint", Color) = (1,1,1,1)
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
                float4 _UVScale;
                float4 _UVOffset;
                float4 _Tint;
            CBUFFER_END

            struct Attributes { float4 positionOS : POSITION; float2 uv : TEXCOORD0; };
            struct Varyings { float4 positionCS : SV_POSITION; float2 uv : TEXCOORD0; };

            Varyings vert(Attributes v)
            {
                Varyings o;
                o.positionCS = TransformObjectToHClip(v.positionOS.xyz);
                o.uv = v.uv * _UVScale.xy + _UVOffset.xy;
                return o;
            }

            half4 frag(Varyings i) : SV_Target
            {
                return SAMPLE_TEXTURE2D(_MainTex, sampler_MainTex, i.uv) * _Tint;
            }
            ENDHLSL
        }
    }
}
