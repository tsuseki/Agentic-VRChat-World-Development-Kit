// Double-sided alpha-cutout foliage.
//
// Two problems this solves that the stock/vendored shaders do not:
//   * Standard culls backfaces, so a leaf card is invisible from behind.
//   * Some vendored cutout variants tag RenderType "Opaque", so the Progressive lightmapper
//     bakes the whole quad as a shadow caster instead of the leaf silhouette.
// Tagging TransparentCutout + alphatest:_Cutoff with addshadow fixes both, and keeping the
// surface shader's meta pass means these still contribute correctly to GI.
//
// Cull Off alone is not enough: a back-facing leaf keeps the front face's normal, so the half
// of every plant whose normal points at bright (HDR) background glazing reads that huge environment
// term at full strength and burns out to pure white. `VFACE` flips the normal per face so a
// back face is shaded as the surface a viewer actually sees.
//
// Two opt-in toggles (both default off, so existing materials render exactly as before):
//   _UseMeshNormalsBothSides  skip the VFACE flip. For cards that carry smooth crown-volume
//                             normals (olives): flipping them on back faces makes the crown patchy.
//   _AlphaToCoverage          MSAA alpha-to-coverage with an fwidth-sharpened alpha, so cutout
//                             edges are anti-aliased instead of stair-stepped. Shadow caster and
//                             meta passes keep the plain clip.
Shader "Custom/FoliageCutout"
{
    Properties
    {
        _Color("Tint", Color) = (1,1,1,1)
        _MainTex("Albedo (RGB) Alpha (A)", 2D) = "white" {}
        _BumpMap("Normal", 2D) = "bump" {}
        _Cutoff("Alpha cutoff", Range(0,1)) = 0.45
        _Glossiness("Smoothness", Range(0,1)) = 0.18
        _Metallic("Metallic", Range(0,1)) = 0.0
        [Toggle] _UseMeshNormalsBothSides("Mesh normals on both sides (no VFACE flip)", Float) = 0
        [Toggle] _AlphaToCoverage("Alpha to coverage (MSAA)", Float) = 0
    }
    SubShader
    {
        Tags { "RenderType"="Opaque" "Queue"="Geometry+50" }
        Cull Off
        AlphaToMask [_AlphaToCoverage]
        LOD 200

        CGPROGRAM
        // `clip()` in the surf body instead of the `alphatest:_Cutoff` pragma. The pragma routes
        // the shader through Unity's cutout path, which leaves the leaf blending against the
        // framebuffer: over bright HDR glazing every plant burned out to pure white,
        // while the same material over plaster read correctly. An explicit clip keeps the pass
        // fully opaque, so a leaf either occludes the background or is discarded.
        // keepalpha: o.Alpha reaches the framebuffer (only used for alpha-to-coverage; it is 1
        // whenever the toggle is off, which is the old output).
        #pragma surface surf Standard fullforwardshadows addshadow keepalpha
        #pragma target 3.0

        sampler2D _MainTex;
        sampler2D _BumpMap;

        struct Input { float2 uv_MainTex; float facing : VFACE; };

        half _Glossiness;
        half _Metallic;
        fixed4 _Color;
        half _Cutoff;
        half _UseMeshNormalsBothSides;
        half _AlphaToCoverage;

        void surf (Input IN, inout SurfaceOutputStandard o)
        {
            fixed4 c = tex2D(_MainTex, IN.uv_MainTex) * _Color;
            o.Alpha = 1;
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
            fixed3 n = UnpackNormal(tex2D(_BumpMap, IN.uv_MainTex));
            o.Normal = (IN.facing > 0 || _UseMeshNormalsBothSides > 0.5) ? n : -n;
            o.Metallic = _Metallic;
            o.Smoothness = _Glossiness;
        }
        ENDCG
    }
    FallBack "Legacy Shaders/Transparent/Cutout/Diffuse"
}
