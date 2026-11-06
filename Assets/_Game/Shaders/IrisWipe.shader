// U-096 (Bible §9.3 v4): the iris wipe. One full-screen UI quad, no texture: black outside a circle of _Radius (screen
// heights) around _Centre (screen 0..1), nothing inside, a soft _Edge. Drawn on the transition canvas (screen-space overlay).
Shader "MERIDIAN/IrisWipe"
{
    Properties
    {
        _Centre ("Centre (screen 0..1)", Vector) = (0.5, 0.5, 0, 0)
        _Radius ("Radius (screen heights)", Float) = 1.2
        _Aspect ("Aspect (w/h)", Float) = 1.7778
        _Edge ("Edge (screen heights)", Float) = 0.004
        [HideInInspector] _MainTex ("Texture", 2D) = "white" {}
    }
    SubShader
    {
        Tags { "Queue" = "Overlay" "IgnoreProjector" = "True" "RenderType" = "Transparent" "PreviewType" = "Plane" }
        Cull Off Lighting Off ZWrite Off ZTest Always
        Blend SrcAlpha OneMinusSrcAlpha

        Pass
        {
            Name "Iris"
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"

            struct appdata { float4 vertex : POSITION; float2 uv : TEXCOORD0; };
            struct v2f { float4 pos : SV_POSITION; float2 uv : TEXCOORD0; };

            float4 _Centre;
            float _Radius, _Aspect, _Edge;

            v2f vert(appdata v)
            {
                v2f o;
                o.pos = UnityObjectToClipPos(v.vertex);
                o.uv = v.uv;
                return o;
            }

            fixed4 frag(v2f i) : SV_Target
            {
                float2 d = i.uv - _Centre.xy;
                d.x *= _Aspect;
                float r = length(d);
                float a = smoothstep(_Radius - _Edge, _Radius + _Edge, r); // 0 inside the circle, 1 outside
                return fixed4(0, 0, 0, a);
            }
            ENDCG
        }
    }
}
