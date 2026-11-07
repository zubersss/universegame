// U-100: the flat ink-outlined silhouette the 3D props and the Pilgrim wear in the C0 cartoon scene (one material swap,
// ArtMaterials.cartoon): unlit flat colour (_BaseColor; ModelView's tint block still applies) darkening to ink at the rim.
Shader "MERIDIAN/CartoonSilhouette"
{
    Properties
    {
        _BaseColor ("Flat colour", Color) = (0.47, 0.45, 0.40, 1)
        _InkColor ("Ink", Color) = (0.118, 0.102, 0.090, 1)
        _InkWidth ("Ink width", Range(0.05, 1)) = 0.35
    }
    SubShader
    {
        Tags { "RenderType" = "Opaque" "RenderPipeline" = "UniversalPipeline" "Queue" = "Geometry" }
        Cull Off
        Pass
        {
            Name "Silhouette"
            HLSLPROGRAM
            #pragma vertex Vert
            #pragma fragment Frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

            CBUFFER_START(UnityPerMaterial)
            half4 _BaseColor, _InkColor;
            half _InkWidth;
            CBUFFER_END

            struct Attributes { float4 positionOS : POSITION; float3 normalOS : NORMAL; };
            struct Varyings { float4 positionCS : SV_POSITION; float3 normalWS : TEXCOORD0; float3 viewWS : TEXCOORD1; };

            Varyings Vert(Attributes v)
            {
                Varyings o;
                float3 posWS = TransformObjectToWorld(v.positionOS.xyz);
                o.positionCS = TransformWorldToHClip(posWS);
                o.normalWS = TransformObjectToWorldNormal(v.normalOS);
                o.viewWS = GetWorldSpaceViewDir(posWS);
                return o;
            }

            half4 Frag(Varyings i) : SV_Target
            {
                half facing = abs(dot(normalize(i.normalWS), normalize(i.viewWS)));
                half ink = step(facing, _InkWidth); // a hard ink band where the surface turns away: the outline
                return half4(lerp(_BaseColor.rgb, _InkColor.rgb, ink), 1);
            }
            ENDHLSL
        }
    }
}
