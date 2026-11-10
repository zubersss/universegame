#ifndef MERIDIAN_LIVING_WIND_INCLUDED
#define MERIDIAN_LIVING_WIND_INCLUDED

// U-216 (D-205 / D-206): the living stage's wind in the vertex stage. The same sums as
// Meridian.View2D.Living.LivingWind.Offset (C#), which the tests pin; a number changed here changes there.
// Globals set once a frame by LivingWind.Push(): no constant per piece, so a layer stays one draw call.
float4 _LivingWind;      // direction x, direction y, strength 0..1, the wind's clock (s)
float4 _LivingWindPhase; // the two gust waves' phases (from the seed)
float4 _LivingPush;      // the surveyor's feet x, y; z = 1 while they are on the stage

#define LIVING_TWO_PI 6.28318530718

// The gust at a place s along the wind at time t: about 0.1 in a lull, 1.0 on a crest.
float LivingGust(float s, float t)
{
    return 0.55 + 0.30 * sin(LIVING_TWO_PI * (s - 3.1 * t) / 23.0 + _LivingWindPhase.x)
                + 0.15 * sin(LIVING_TWO_PI * (s - 4.7 * t) / 7.3 + _LivingWindPhase.y);
}

// rootWS: the piece's root in the world (m); weight: the vertex's bend weight (0 at the root, 1 at the farthest tip);
// give: the tip's travel in a full gust (m); phase: the plant's own (0..1). Returns the vertex's offset (m).
float2 LivingOffset(float2 rootWS, float weight, float give, float phase)
{
    float2 dir = _LivingWind.xy;
    float strength = _LivingWind.z;
    float t = _LivingWind.w;
    float along = dir.x >= 0.0 ? 1.0 : -1.0;
    float gust = LivingGust(rootWS.x * along, t);
    float hz = 0.7 + 0.5 * phase;
    float flutter = (0.35 + 0.65 * gust) * 0.18 * sin(LIVING_TWO_PI * (hz * t + phase) + rootWS.x * 0.9);
    float travel = give * weight * strength * (gust + flutter);
    float2 offset = dir * travel;
    offset.y -= abs(travel) * 0.25 * weight;
    // the surveyor passing: plants rooted within 1.4 m of the feet part to either side
    float dx = rootWS.x - _LivingPush.x;
    float up = _LivingPush.y - rootWS.y;
    float k = saturate(1.0 - abs(dx) / 1.4) * step(-0.6, up) * step(up, 1.6) * _LivingPush.z;
    offset.x += (dx >= 0.0 ? 1.0 : -1.0) * 0.28 * k * k * weight * saturate(give / 0.25);
    return offset;
}

// The stage's vertex: uv1 = (root x, root y, weight, give), uv2 = (phase, the normal's x sign, 0, 0); the root in the
// layer's own space (a layer is never turned or scaled, only moved by its parallax).
float3 LivingBend(float3 positionOS, float4 sway, float4 sway2)
{
    float2 rootWS = TransformObjectToWorld(float3(sway.xy, 0.0)).xy;
    positionOS.xy += LivingOffset(rootWS, sway.z, sway.w, sway2.x);
    return positionOS;
}

#endif
