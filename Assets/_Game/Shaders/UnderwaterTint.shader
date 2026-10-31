// Underwater tint (U-040, LEAD): a camera-covering quad drawn over the world (terrain, seabed, water,
// surveyor) that multiplies everything below sea level by a blue that darkens with depth, so the seabed
// doesn't render as bright as dry land. Above the sea surface it multiplies by 1 (no change).
Shader "MERIDIAN/UnderwaterTint"
{
    Properties
    {
        _SeaLevel ("Sea surface (world y)", Float) = 321
        _Tint ("Shallow-water tint", Color) = (0.55, 0.78, 0.95, 1)
        _Fade ("Depth (m) over which light falls to 1/e", Float) = 45
        _Floor ("Darkest multiplier", Float) = 0.06
    }
    SubShader
    {
        Tags { "RenderType"="Transparent" "Queue"="Transparent" "RenderPipeline"="UniversalPipeline" }
        Blend DstColor Zero
        ZWrite Off
        Cull Off

        Pass
        {
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

            CBUFFER_START(UnityPerMaterial)
                float _SeaLevel;
                float4 _Tint;
                float _Fade;
                float _Floor;
            CBUFFER_END

            struct Attributes { float4 positionOS : POSITION; };
            struct Varyings { float4 positionCS : SV_POSITION; float worldY : TEXCOORD0; };

            Varyings vert(Attributes v)
            {
                Varyings o;
                float3 ws = TransformObjectToWorld(v.positionOS.xyz);
                o.positionCS = TransformWorldToHClip(ws);
                o.worldY = ws.y;
                return o;
            }

            half4 frag(Varyings i) : SV_Target
            {
                float depth = _SeaLevel - i.worldY;
                if (depth <= 0.0) return half4(1, 1, 1, 1);
                float k = max(_Floor, exp(-depth / _Fade));
                return half4(_Tint.rgb * k, 1);
            }
            ENDHLSL
        }
    }
}
