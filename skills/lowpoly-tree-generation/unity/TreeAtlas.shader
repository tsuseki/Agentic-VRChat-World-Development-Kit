// One material for a whole tree: bark and leaf cards share one atlas (tree_atlas.py).
//
// Leaf cards use their UVs directly (alpha cutout, double-sided, like FoliageCutout).
// Bark faces are tagged by the exporter with u >= _BarkTag (tile-space UVs shifted by _BarkTag): they are
// wrapped into _BarkRect with frac() and sampled with tex2Dgrad on the unwrapped UVs, so the bark tiles along
// the trunk like a repeating texture with no mip seam, and bark never clips (the atlas gutter is alpha 0).
// Back faces of leaves keep the mesh (crown-volume) normals when _UseMeshNormalsBothSides is on.
Shader "LowPolyTrees/TreeAtlas"
{
    Properties
    {
        _Color("Tint", Color) = (1,1,1,1)
        _MainTex("Atlas (RGB) Alpha (A)", 2D) = "white" {}
        [NoScaleOffset][Normal] _BumpMap("Atlas normal", 2D) = "bump" {}
        _BarkRect("Bark rect in atlas (u0, v0, u1, v1)", Vector) = (0.52344, 0.02344, 0.97656, 0.47656)
        _BarkTag("Bark UV tag (u offset)", Float) = 100
        _Cutoff("Leaf alpha cutoff", Range(0,1)) = 0.45
        _Glossiness("Leaf smoothness", Range(0,1)) = 0.0
        _BarkGlossiness("Bark smoothness", Range(0,1)) = 0.1
        _BarkNormalStrength("Bark normal strength", Range(0,2)) = 1
        [Toggle] _UseMeshNormalsBothSides("Leaves: mesh normals on both sides (no VFACE flip)", Float) = 1
        [Toggle] _AlphaToCoverage("Alpha to coverage (MSAA)", Float) = 0
    }
    SubShader
    {
        Tags { "RenderType"="Opaque" "Queue"="Geometry+50" }
        Cull Off
        AlphaToMask [_AlphaToCoverage]
        LOD 200

        CGPROGRAM
        #pragma surface surf Standard fullforwardshadows addshadow keepalpha
        #pragma target 3.0

        sampler2D _MainTex;
        sampler2D _BumpMap;
        struct Input { float2 uv_MainTex; float facing : VFACE; };

        fixed4 _Color;
        float4 _BarkRect;
        float _BarkTag;
        half _Cutoff, _Glossiness, _BarkGlossiness, _BarkNormalStrength;
        half _UseMeshNormalsBothSides, _AlphaToCoverage;

        void surf (Input IN, inout SurfaceOutputStandard o)
        {
            float2 uv = IN.uv_MainTex;
            o.Alpha = 1;
            o.Metallic = 0;
            if (uv.x >= _BarkTag * 0.5)
            {
                float2 t = uv - float2(_BarkTag, 0);
                float2 sz = _BarkRect.zw - _BarkRect.xy;
                float2 auv = _BarkRect.xy + frac(t) * sz;
                float2 dx = ddx(t) * sz, dy = ddy(t) * sz;
                o.Albedo = tex2Dgrad(_MainTex, auv, dx, dy).rgb * _Color.rgb;
                fixed3 n = UnpackNormal(tex2Dgrad(_BumpMap, auv, dx, dy));
                n.xy *= _BarkNormalStrength;
                o.Normal = normalize(n);
                o.Smoothness = _BarkGlossiness;
                return;
            }
            fixed4 c = tex2D(_MainTex, uv) * _Color;
        #if defined(UNITY_PASS_SHADOWCASTER) || defined(UNITY_PASS_META)
            clip(c.a - _Cutoff);
        #else
            if (_AlphaToCoverage > 0.5)
            {
                half a = (c.a - _Cutoff) / max(fwidth(c.a), 1e-4) + 0.5;
                clip(a);
                o.Alpha = saturate(a);
            }
            else
            {
                clip(c.a - _Cutoff);
            }
        #endif
            o.Albedo = c.rgb;
            o.Normal = (IN.facing > 0 || _UseMeshNormalsBothSides > 0.5) ? fixed3(0, 0, 1) : fixed3(0, 0, -1);
            o.Smoothness = _Glossiness;
        }
        ENDCG
    }
    FallBack "Legacy Shaders/Transparent/Cutout/Diffuse"
}
