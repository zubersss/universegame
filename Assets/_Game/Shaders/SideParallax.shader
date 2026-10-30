// Side-view backdrop (U-024, Bible §9 Atmosphere): the sky plus three parallax layers composited in ONE
// opaque full-screen pass (three blended full-screen quads pushed Earth p99 from 5.8 to 15.2 ms at 1080p
// on Intel UHD; U-025 BudgetGate).
// Per layer i: _Pi = (tile width, tile height, parallax factor, sheet bottom relative to the camera),
// _Qi = (haze amount, below-sheet mode 0 end / 1 clamp / 2 mirror, loaded 0/1, unused).
// Horizontally a layer scrolls at its factor of the world's speed and repeats; vertically it is framed on
// the camera so its ground stays under the player's feet. _Alpha fades the layers to the sky underground;
// _Tint is the day/night multiplier (U-025).
Shader "MERIDIAN/SideParallax"
{
    Properties
    {
        _Layer0 ("Layer 0 (far)", 2D) = "black" {}
        _Layer1 ("Layer 1 (mid)", 2D) = "black" {}
        _Layer2 ("Layer 2 (near)", 2D) = "black" {}
        _P0 ("Layer 0 tile/factor/base", Vector) = (56, 28, 0.06, -10)
        _P1 ("Layer 1 tile/factor/base", Vector) = (44, 22, 0.22, -10)
        _P2 ("Layer 2 tile/factor/base", Vector) = (32, 16, 0.45, -4)
        _Q0 ("Layer 0 haze/mode/loaded", Vector) = (0.35, 1, 0, 0)
        _Q1 ("Layer 1 haze/mode/loaded", Vector) = (0.2, 0, 0, 0)
        _Q2 ("Layer 2 haze/mode/loaded", Vector) = (0.08, 2, 0, 0)
        _SkyColor ("Sky color", Color) = (0.45, 0.62, 0.85, 1)
        _Tint ("Day/night tint", Color) = (1, 1, 1, 1)
        _Alpha ("Layers alpha", Float) = 1
    }
    SubShader
    {
        Tags { "RenderType"="Opaque" "Queue"="Transparent" "RenderPipeline"="UniversalPipeline" }
        Blend Off
        ZWrite Off
        Cull Off

        Pass
        {
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

            TEXTURE2D(_Layer0); SAMPLER(sampler_Layer0);
            TEXTURE2D(_Layer1); SAMPLER(sampler_Layer1);
            TEXTURE2D(_Layer2); SAMPLER(sampler_Layer2);
            CBUFFER_START(UnityPerMaterial)
                float4 _P0, _P1, _P2;
                float4 _Q0, _Q1, _Q2;
                float4 _SkyColor;
                float4 _Tint;
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

            // False where the layer shows nothing; its uv otherwise.
            bool LayerUV(float2 world, float2 cam, float4 p, float4 q, out float2 uv)
            {
                uv = float2((world.x - cam.x * (1.0 - p.z)) / p.x, (world.y - cam.y - p.w) / p.y);
                if (q.z < 0.5) return false;
                if (uv.y < 0.0)
                {
                    if (q.y < 0.5) return false;   // middle layer: ends
                    if (q.y > 1.5) uv.y = -uv.y;   // near layer: mirrored ground, no streaks
                }
                // Keep v off the very edge rows so clamping never picks up a filtered border.
                uv.y = clamp(uv.y, 0.5 / 1024.0, 1.0 - 0.5 / 1024.0);
                return true;
            }

            half3 Over(half3 col, half4 s, float haze, half3 sky)
            {
                s.rgb = lerp(s.rgb, sky, haze);
                return lerp(col, s.rgb, s.a);
            }

            half4 frag(Varyings i) : SV_Target
            {
                float2 cam = _WorldSpaceCameraPos.xy;
                half3 sky = _SkyColor.rgb;
                half3 col = sky;
                float2 uv;
                if (LayerUV(i.worldXY, cam, _P0, _Q0, uv)) col = Over(col, SAMPLE_TEXTURE2D(_Layer0, sampler_Layer0, uv), _Q0.x, sky);
                if (LayerUV(i.worldXY, cam, _P1, _Q1, uv)) col = Over(col, SAMPLE_TEXTURE2D(_Layer1, sampler_Layer1, uv), _Q1.x, sky);
                if (LayerUV(i.worldXY, cam, _P2, _Q2, uv)) col = Over(col, SAMPLE_TEXTURE2D(_Layer2, sampler_Layer2, uv), _Q2.x, sky);
                col = lerp(sky, col, _Alpha);
                return half4(col * _Tint.rgb, 1);
            }
            ENDHLSL
        }
    }
}
