// Side-view background layer (U-024, Bible §9 Atmosphere). The quad covers the camera view.
// Horizontally the layer scrolls at _Factor of the world's speed (0 = fixed on screen, 1 = moves with
// the terrain) and repeats (tileable sheets). Vertically it is framed on the camera: sheet row v sits at
// cameraY + _BaseOffset + v × height, so the content base stays just under the player's feet on any
// terrain height. Below the sheet: the far layer clamps its ground row, the near layer mirrors its ground,
// the middle layer ends. Haze tints far
// layers toward the sky; _Alpha fades the whole layer underground.
Shader "MERIDIAN/SideParallax"
{
    Properties
    {
        _MainTex ("Layer (tileable in x)", 2D) = "black" {}
        _TileSize ("Tile size (world units)", Vector) = (64, 32, 0, 0)
        _Factor ("Horizontal parallax factor", Float) = 0.2
        _BaseOffset ("Sheet bottom relative to the camera (world units)", Float) = -8
        _HazeColor ("Haze color", Color) = (0.7, 0.8, 0.9, 1)
        _HazeAmount ("Haze amount", Float) = 0.3
        _ExtendBelow ("Below the sheet: 0 end, 1 clamp bottom row, 2 mirror", Float) = 0
        _Alpha ("Layer alpha", Float) = 1
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
                float4 _TileSize;
                float _Factor;
                float _BaseOffset;
                float4 _HazeColor;
                float _HazeAmount;
                float _ExtendBelow;
                float _Alpha;
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

            half4 frag(Varyings i) : SV_Target
            {
                float2 cam = _WorldSpaceCameraPos.xy;
                float u = (i.worldXY.x - cam.x * (1.0 - _Factor)) / _TileSize.x;
                float vRaw = (i.worldXY.y - cam.y - _BaseOffset) / _TileSize.y;
                if (vRaw < 0.0)
                {
                    if (_ExtendBelow < 0.5) return half4(0, 0, 0, 0); // middle layer: ends
                    if (_ExtendBelow > 1.5) vRaw = -vRaw;              // near layer: mirrored ground, no streaks
                }
                // Keep v off the very edge rows so clamping never picks up a filtered border.
                float v = clamp(vRaw, 0.5 / 1024.0, 1.0 - 0.5 / 1024.0);
                half4 c = SAMPLE_TEXTURE2D(_MainTex, sampler_MainTex, float2(u, v));
                c.rgb = lerp(c.rgb, _HazeColor.rgb, _HazeAmount);
                c.a *= _Alpha;
                return c;
            }
            ENDHLSL
        }
    }
}
