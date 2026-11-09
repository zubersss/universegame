#ifndef MERIDIAN_GROUND_TIERS
#define MERIDIAN_GROUND_TIERS

// U-182 (LEAD 21:5x): each tier border wobbles by up to 0.6 m along x (three sines, 2-7 m wavelengths, phased per tier) so it reads as a
// rock boundary, not a straight soft shadow across the strata. SmoothGround.TierWobble is this function in C#.
float4 GroundTierWobble(float x)
{
    const float4 p = float4(0.0, 1.7, 3.4, 5.1);
    return 0.6 * (0.5 * sin(x * 1.71 + p) + 0.32 * sin(x * 0.93 + p * 1.3 + 2.1) + 0.18 * sin(x * 3.1 + p * 0.7 + 4.0));
}

// U-182: the tier weights for a depth under the Surface Line (m) at world x: each of tiers 2..5 fades in across its transition centred on
// its (wobbled) depth, smoothstepped. SmoothGround.TierWeights is this function in C# (GroundTierTests).
float4 GroundTierWeights(float depth, float x)
{
    float4 t = saturate((depth.xxxx + GroundTierWobble(x) - (_TierFrom - 0.5 * _TierBlend)) / max(_TierBlend, 1e-3));
    return t * t * (3.0 - 2.0 * t);
}

// The fill colour at a fill uv (world / 8): tier 1 (_MainTex), crossfaded to tiers 2..5 by the depth under the Surface Line there. The
// weights only rise with depth and the transitions never overlap, so a pixel starts from the deepest tier at full weight and blends at
// most the one tier fading in under it: two samples at most (one at the surface).
half4 GroundTierColor(float2 uv)
{
    float2 w = uv * _LineParams.y;
    float lineY = _LineParams.z + _LineParams.w * SAMPLE_TEXTURE2D_LOD(_LineTex, sampler_LineTex, float2(w.x * _LineParams.x, 0.5), 0).r; // base + span x texel
    float4 k = GroundTierWeights(lineY - w.y, w.x);
    // Every sample sits in a branch: the mip level from the uv's derivatives here (every fill is one _TileTexels-pixel tile), then LOD
    // samples (full rate on the iGPU, where explicit-gradient samples ran at a fraction of it: the perf probe's T3 room).
    float2 dx = ddx(uv) * _TileTexels, dy = ddy(uv) * _TileTexels;
    float lod = 0.5 * log2(max(max(dot(dx, dx), dot(dy, dy)), 1e-8));
    half4 c;
    UNITY_BRANCH if (k.w >= 1.0) c = SAMPLE_TEXTURE2D_LOD(_Tier5Tex, sampler_Tier5Tex, uv, lod);
    else UNITY_BRANCH if (k.z >= 1.0) c = SAMPLE_TEXTURE2D_LOD(_Tier4Tex, sampler_Tier4Tex, uv, lod);
    else UNITY_BRANCH if (k.y >= 1.0) c = SAMPLE_TEXTURE2D_LOD(_Tier3Tex, sampler_Tier3Tex, uv, lod);
    else UNITY_BRANCH if (k.x >= 1.0) c = SAMPLE_TEXTURE2D_LOD(_Tier2Tex, sampler_Tier2Tex, uv, lod);
    else c = SAMPLE_TEXTURE2D_LOD(_MainTex, sampler_MainTex, uv, lod);
    UNITY_BRANCH if (k.x > 0.0 && k.x < 1.0) c = lerp(c, SAMPLE_TEXTURE2D_LOD(_Tier2Tex, sampler_Tier2Tex, uv, lod), k.x);
    else UNITY_BRANCH if (k.y > 0.0 && k.y < 1.0) c = lerp(c, SAMPLE_TEXTURE2D_LOD(_Tier3Tex, sampler_Tier3Tex, uv, lod), k.y);
    else UNITY_BRANCH if (k.z > 0.0 && k.z < 1.0) c = lerp(c, SAMPLE_TEXTURE2D_LOD(_Tier4Tex, sampler_Tier4Tex, uv, lod), k.z);
    else UNITY_BRANCH if (k.w > 0.0 && k.w < 1.0) c = lerp(c, SAMPLE_TEXTURE2D_LOD(_Tier5Tex, sampler_Tier5Tex, uv, lod), k.w);
    return c;
}

#endif
