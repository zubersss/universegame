// U-095 (Bible §9.4 v4, contract §11.6): the one full-screen film pass. One blit: grain, dust specks and hairline
// scratches from three 512² tiled overlays, a vignette, a ±2 % flicker and a warm/sepia grade. No bloom, no HDR.
Shader "MERIDIAN/FilmPass"
{
    SubShader
    {
        Tags { "RenderType" = "Opaque" "RenderPipeline" = "UniversalPipeline" }
        ZWrite Off Cull Off ZTest Always

        Pass
        {
            Name "Film"

            HLSLPROGRAM
            #include "Packages/com.unity.render-pipelines.core/ShaderLibrary/Common.hlsl"
            #include "Packages/com.unity.render-pipelines.core/Runtime/Utilities/Blit.hlsl"
            #pragma vertex Vert
            #pragma fragment Frag

            TEXTURE2D(_Grain);     SAMPLER(sampler_Grain);
            TEXTURE2D(_Dust);      SAMPLER(sampler_Dust);
            TEXTURE2D(_Scratches); SAMPLER(sampler_Scratches);
            float4 _Tile;     // xy: screen size / 512 (overlay tiles across and down)
            float4 _Offsets;  // xy: grain tile offset (random each 1/12 s), zw: dust drift
            float4 _Offsets2; // xy: scratch jitter, z: flicker factor (0.98..1.02), w: grade amount
            float4 _Amounts;  // x: grain, y: dust, z: scratches, w: vignette

            half4 Frag(Varyings i) : SV_Target
            {
                float2 uv = i.texcoord;
                half3 col = SAMPLE_TEXTURE2D(_BlitTexture, sampler_LinearClamp, uv).rgb;
                float2 t = uv * _Tile.xy;
                half4 g = SAMPLE_TEXTURE2D(_Grain, sampler_Grain, t + _Offsets.xy);
                half4 d = SAMPLE_TEXTURE2D(_Dust, sampler_Dust, t + _Offsets.zw);
                half4 s = SAMPLE_TEXTURE2D(_Scratches, sampler_Scratches, t + _Offsets2.xy);

                // Warm, slightly faded grade: part way to sepia, then a warm tint.
                half lum = dot(col, half3(0.299h, 0.587h, 0.114h));
                half3 sepia = half3(lum * 1.07h, lum * 0.95h, lum * 0.78h);
                half3 graded = lerp(col, sepia, 0.45h) * half3(1.04h, 1.0h, 0.93h);
                col = lerp(col, graded, _Offsets2.w);

                col *= 1.0h + (g.r - 0.5h) * 2.0h * _Amounts.x * g.a;  // grain: ± around 1
                col *= 1.0h - d.a * _Amounts.y;                          // dust specks darken
                col *= 1.0h - s.a * _Amounts.z;                          // hairline scratches darken
                float2 c = uv - 0.5;
                half v = 1.0h - _Amounts.w * smoothstep(0.2, 0.9, dot(c, c) * 2.0);
                col *= v * _Offsets2.z;
                return half4(col, 1.0h);
            }
            ENDHLSL
        }
    }
}
