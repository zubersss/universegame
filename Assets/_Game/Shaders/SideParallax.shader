// Side-view backdrop (U-024, Bible §9 Atmosphere): the sky plus three parallax layers composited in ONE
// opaque full-screen pass (three blended full-screen quads pushed Earth p99 from 5.8 to 15.2 ms at 1080p
// on Intel UHD; U-025 BudgetGate).
// Per layer i: _Pi = (tile width, tile height, parallax factor, sheet bottom relative to its anchor),
// _Qi = (haze amount, unused, loaded 0/1, vertical world-follow factor).
// Horizontally a layer scrolls at its factor of the world's speed and repeats. Vertically it hangs off the
// planet Datum (U-039 fix): anchor = Datum + (cameraY − Datum) × (1 − follow), so near the Datum its ground
// sits under the player's feet, while deep in a canyon or high on Olympus the layers stay with the horizon.
// Below a layer's sheet it shows nothing (no clamped or mirrored repeats); under the far horizon the base
// is a hazy ground tone instead of sky. _Alpha fades the layers to the sky underground;
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
        _SeaLevel ("Sea surface (world y; far below = no sea)", Float) = -100000
        _WaterColor ("Water color at the surface", Color) = (0.07, 0.24, 0.36, 1)
        _WaterFade ("Depth (m) over which light falls to 1/e", Float) = 40
        _Datum ("Planet Datum (world y)", Float) = 320
        _HorizonOffset ("Far horizon relative to layer 0's anchor", Float) = -4
        _GroundColor ("Hazy ground below the horizon", Color) = (0.3, 0.25, 0.2, 1)
        _WallMap ("Per column: original ground line, near slot, deep slot (U-040)", 2D) = "black" {}
        _WallOrigin ("World x of the wall map's first column", Float) = 0
        _WallTex0 ("Wall: near-surface sheet", 2D) = "black" {}
        _WallTex1 ("Wall: deep rock sheet", 2D) = "black" {}
        _WallTex2 ("Wall: sand / ice sheet", 2D) = "black" {}
        _WallRect0 ("UV rect of slot 0's interior tile", Vector) = (0, 0, 0, 0)
        _WallRect1 ("UV rect of slot 1's interior tile", Vector) = (0, 0, 0, 0)
        _WallRect2 ("UV rect of slot 2's interior tile", Vector) = (0, 0, 0, 0)
        _WallDark ("Wall brightness", Float) = 0.32
        _WallNear ("Near material depth (m)", Float) = 4
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
            TEXTURE2D(_WallMap); SAMPLER(sampler_point_clamp_WallMap);
            TEXTURE2D(_WallTex0); SAMPLER(sampler_WallTex0);
            TEXTURE2D(_WallTex1); SAMPLER(sampler_WallTex1);
            TEXTURE2D(_WallTex2); SAMPLER(sampler_WallTex2);
            CBUFFER_START(UnityPerMaterial)
                float4 _P0, _P1, _P2;
                float4 _Q0, _Q1, _Q2;
                float4 _SkyColor;
                float4 _Tint;
                float _Alpha;
                float _SeaLevel;
                float4 _WaterColor;
                float _WaterFade;
                float _Datum;
                float _HorizonOffset;
                float4 _GroundColor;
                float _WallOrigin;
                float4 _WallRect0, _WallRect1, _WallRect2;
                float _WallDark;
                float _WallNear;
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
                float anchor = _Datum + (cam.y - _Datum) * (1.0 - q.w);
                uv = float2((world.x - cam.x * (1.0 - p.z)) / p.x, (world.y - anchor - p.w) / p.y);
                if (q.z < 0.5 || uv.y < q.y) return false; // not loaded, or below its own ground line (no hanging silhouettes)
                // Keep v off the very edge rows so clamping never picks up a filtered border.
                uv.y = clamp(uv.y, 0.5 / 1024.0, 1.0 - 0.5 / 1024.0);
                return true;
            }

            half3 Over(half3 col, half4 s, float haze, half3 sky)
            {
                s.rgb = lerp(s.rgb, sky, haze);
                return lerp(col, s.rgb, s.a);
            }

            // U-040 background wall of column c: the material that was there, dark, tiled 1 m per tile.
            half3 Wall(float2 world, float top, float near, float deep)
            {
                float depth = top + 1.0 - world.y;
                float slot = depth < _WallNear ? near : deep;
                float2 f = frac(world);
                half3 c;
                if (slot < 0.5) c = SAMPLE_TEXTURE2D(_WallTex0, sampler_WallTex0, _WallRect0.xy + f * _WallRect0.zw).rgb;
                else if (slot < 1.5) c = SAMPLE_TEXTURE2D(_WallTex1, sampler_WallTex1, _WallRect1.xy + f * _WallRect1.zw).rgb;
                else c = SAMPLE_TEXTURE2D(_WallTex2, sampler_WallTex2, _WallRect2.xy + f * _WallRect2.zw).rgb;
                return c * _WallDark;
            }

            half4 frag(Varyings i) : SV_Target
            {
                float2 cam = _WorldSpaceCameraPos.xy;
                half3 sky = _SkyColor.rgb;
                float horizon = _Datum + _HorizonOffset + (cam.y - _Datum) * (1.0 - _Q0.w);
                half3 col = i.worldXY.y < horizon ? lerp(_GroundColor.rgb, sky, 0.3) : sky;
                float2 uv;
                if (LayerUV(i.worldXY, cam, _P0, _Q0, uv)) col = Over(col, SAMPLE_TEXTURE2D(_Layer0, sampler_Layer0, uv), _Q0.x, sky);
                if (LayerUV(i.worldXY, cam, _P1, _Q1, uv)) col = Over(col, SAMPLE_TEXTURE2D(_Layer1, sampler_Layer1, uv), _Q1.x, sky);
                if (LayerUV(i.worldXY, cam, _P2, _Q2, uv)) col = Over(col, SAMPLE_TEXTURE2D(_Layer2, sampler_Layer2, uv), _Q2.x, sky);
                col = lerp(sky, col, _Alpha);
                // Under the sea (U-037): no landscape, just water darkening with depth (near-black by ~120 m).
                float depth = _SeaLevel - i.worldXY.y;
                if (depth > 0.0) col = _WaterColor.rgb; // the UnderwaterTint overlay darkens it with depth (U-040)
                // Below a column's original ground line: the dark wall of its material (dug holes, caves, tubes).
                float u = (floor(i.worldXY.x) - _WallOrigin + 0.5) / 256.0;
                if (u > 0.0 && u < 1.0 && _WallRect1.z > 0.0)
                {
                    float4 m = SAMPLE_TEXTURE2D_LOD(_WallMap, sampler_point_clamp_WallMap, float2(u, 0.5), 0);
                    if (i.worldXY.y < m.r + 1.0) col = Wall(i.worldXY, m.r, m.g, m.b);
                }
                return half4(col * _Tint.rgb, 1);
            }
            ENDHLSL
        }
    }
}
