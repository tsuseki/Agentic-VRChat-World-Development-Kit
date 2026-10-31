// SoftCrown: one material for a whole tree; bark and leaf cards share one atlas (tree_atlas.py).
//
// Column layout (_AtlasLayout 1, tree_atlas.py --layout column): plain UVs that any shader can use. The bark is a
// full-height column at u >= _BarkU0 that repeats vertically (texture wrap U Clamp, V Repeat). No normal map: one
// texture per family (low-poly trees; in VR the stereo view shows a normal map's relief as flat anyway).
// Quadrant layout (_AtlasLayout 0, legacy): bark faces are tagged by the exporter with u >= _BarkTag (tile-space
// UVs shifted by _BarkTag); the albedo is wrapped into _BarkRect with frac() and sampled with tex2Dgrad on the
// unwrapped UVs, and the bark normal map is its own Repeat texture sampled on the same unwrapped UVs.
// Leaf cards: alpha cutout, double-sided; back faces keep the mesh (crown-volume) normals when
// _UseMeshNormalsBothSides is on. Bark never clips (alpha 1 in the bark area).
// VR anti-shimmer: leaves that shrink to ~1 px flicker as the head moves. Both knobs act only on far foliage (leaf
// texture minified past mip 1), so near leaves stay crisp: _LeafMipBias blurs the leaf texture by up to that many
// extra mip levels, and with _AlphaToCoverage on (VRChat runs MSAA 4x by default) _A2CFarCutoffDrop lowers the
// cutoff, which steadies the edges and keeps far crowns as full as a supersampled render. Measured on an olive
// (bias 0.35, drop 0.05): flicker above a 4x supersampled render drops ~45-70 % at 6-40 m, near leaves unchanged.
// The property defaults are the recommended tree settings (column atlas, edge fade and anti-shimmer on).
//
// Wind: a port of the wind in Silent's Crispy Foliage (MIT, gitlab.com/s-ilent/crispy-foliage): Unity's terrain
// grass wave (four sines over world XZ, each raised to the 4th power, so the crown swings in uneven, gusty pushes,
// mostly downwind with short swings back, whose crests roll across the world) plus the Horizon Zero Dawn leaf
// tremble (along the normal on trees; horizontal on plants up to 3 m, see below); the normals bend with
// the offset, so the leaves shimmer in the light as they move. Adapted: the gust frame follows _WindDirection, the
// push is scaled by tree height, and the weights come from the vertex colour (tree_wind_data.py). Displacement is
// in world space, so it also works on static-batched trees, where the object transform is gone.
//   R  tree height / 32 m (one value per tree): gust push scales with the tree's size
//   G  tremble weight: 0 on bark and on every card's stem edge, rising with the distance from them
//   B  tremble phase: a smooth noise of the position (0 on bark); on plants up to 3 m also the tremble direction
//   A  gust weight ("wind pinning"): 0 at the trunk base, (height / tree height)^2 to 1 at the top; a smooth field
//      over the bark; on leaves raised toward the stem heights of the cards around (hanging strands swing from
//      above). Also the single sway mask for other foliage shaders (Crispy Foliage: Wind Pinning Source = Vertex
//      Colour (A)).
// Neighbouring cards move together: every weight is a function of position, not of the card, so crossing cards share
// them where they cross; and the displacement field is smooth over a card's size (cards are 1-2 big triangles, the GPU
// interpolates between their corners): the tremble phase drifts 0.5 rad/m in world space (Crispy: 2.65, a 1.4 m wave
// across one card) and Wave Size defaults to 0.5. The gust field is smooth in position and the tremble is 0 where
// cards attach: bark and leaves stay joined.
// No breathing: with the phase shared across a small crown, a tremble along crown-gradient normals moves every leaf
// outward at once and a bush grows and shrinks. Plants up to 3 m tall (vertex R) tremble horizontally (wind turned by
// +-90 degrees with B), blending to the normal by 6 m; tall trees keep the normal (sideways tremble lets their big
// vertical cards cross more).
// The meta pass skips the wind, so lightmaps are baked at the rest pose; the shadow caster sways with the tree.
Shader "SoftCrown"
{
    Properties
    {
        _Color("Tint", Color) = (1,1,1,1)
        _MainTex("Atlas (RGB) Alpha (A)", 2D) = "white" {}
        [NoScaleOffset][Normal] _BumpMap("Quadrant only: tiling bark normal", 2D) = "bump" {}
        [Enum(Quadrant legacy,0,Column,1)] _AtlasLayout("Atlas layout", Float) = 1
        _BarkU0("Column: bark starts at u", Float) = 0.76
        _BarkRect("Quadrant: bark rect in atlas (u0, v0, u1, v1)", Vector) = (0.52344, 0.02344, 0.97656, 0.47656)
        _BarkTag("Quadrant: bark UV tag (u offset)", Float) = 100
        _Cutoff("Leaf alpha cutoff", Range(0,1)) = 0.45
        _Glossiness("Leaf smoothness", Range(0,1)) = 0.0
        _BarkGlossiness("Bark smoothness", Range(0,1)) = 0.1
        _BarkNormalStrength("Quadrant only: bark normal strength", Range(0,2)) = 1
        [Toggle] _UseMeshNormalsBothSides("Leaves: mesh normals on both sides (no VFACE flip)", Float) = 1
        [Toggle] _AlphaToCoverage("Alpha to coverage (MSAA)", Float) = 1
        _A2CFarCutoffDrop("Alpha to coverage: cutoff drop on far foliage (keeps far crowns full)", Range(0, 0.2)) = 0.05
        _EdgeFade("Leaves: fade cards seen edge-on (0 = off)", Range(0, 1)) = 1
        _EdgeFadeAngle("Edge fade: fully faded below this |cos| view-to-card", Range(0.01, 0.5)) = 0.12
        _LeafMipBias("Leaves: extra mip bias on far foliage (minified past mip 1); near leaves stay sharp", Range(0, 2)) = 0.35
        [Enum(UnityEngine.Rendering.CullMode)] _Cull("Cull (Off for trees, Back for the 6-view billboard)", Float) = 0
        [Header(Wind)]
        [Toggle(_WIND_ON)] _Wind("Wind", Float) = 1
        _WindDirection("Wind direction (world XZ)", Vector) = (1, 0, 0.3, 0)
        _WindStrength("Gust push (% of tree height at the top)", Range(0, 10)) = 3
        _WindSpeed("Wind speed", Range(0, 4)) = 1
        _WindWaveSize("Wave size (higher = shorter gust waves)", Range(0.1, 4)) = 0.5
        _FlutterStrength("Leaf tremble (m at full tremble weight)", Range(0, 0.3)) = 0.06
        _FlutterSpeed("Leaf tremble speed", Range(0, 4)) = 1
    }
    SubShader
    {
        // TransparentCutout: the Progressive lightmapper then reads _MainTex alpha + _Cutoff, so leaves bake leaf-shaped
        // shadows (with "Opaque" every card bakes as a solid rectangle)
        Tags { "RenderType"="TransparentCutout" "Queue"="Geometry+50" }
        Cull [_Cull]
        AlphaToMask [_AlphaToCoverage]
        LOD 200

        CGPROGRAM
        #pragma surface surf Standard fullforwardshadows addshadow keepalpha vertex:vert
        #pragma target 3.0
        #pragma shader_feature_local _WIND_ON

        sampler2D _MainTex;
        sampler2D _BumpMap;
        // camRel: position relative to the camera, written in vert. Small numbers keep its screen derivatives exact far
        // from the world origin (an interpolated worldPos 1-2 km out is quantised to ~0.1 mm, so the edge-fade normal
        // turns to per-pixel noise on near leaves at 4K or supersampled renders: scattered single-pixel holes)
        struct Input { float2 uv_MainTex; float facing : VFACE; float3 camRel; };

        fixed4 _Color;
        float4 _BarkRect;
        float _BarkTag, _AtlasLayout, _BarkU0;
        half _Cutoff, _Glossiness, _BarkGlossiness, _BarkNormalStrength;
        half _UseMeshNormalsBothSides, _AlphaToCoverage, _A2CFarCutoffDrop, _EdgeFade, _EdgeFadeAngle, _LeafMipBias;
        float4 _MainTex_TexelSize;
        float4 _WindDirection;
        float _WindStrength, _WindSpeed, _WindWaveSize, _FlutterStrength, _FlutterSpeed;

        void vert (inout appdata_full v, out Input o)
        {
            UNITY_INITIALIZE_OUTPUT(Input, o);
        #if defined(_WIND_ON) && !defined(UNITY_PASS_META)
            float3 wp = mul(unity_ObjectToWorld, v.vertex).xyz;
            float2 d2 = _WindDirection.xz;
            d2 = dot(d2, d2) > 1e-6 ? normalize(d2) : float2(1, 0);
            float3 dir = float3(d2.x, 0, d2.y), side = float3(-d2.y, 0, d2.x);
            // gust waves (Crispy Foliage WaveGrass in the wind frame; px is negated so the crests roll downwind,
            // the way the push goes)
            float px = -dot(wp.xz, d2), pz = dot(wp.xz, side.xz);
            float4 waves = px * float4(0.012, 0.02, 0.06, 0.024) * _WindWaveSize
                         + pz * float4(0.006, 0.02, 0.02, 0.05) * _WindWaveSize
                         + (_Time.x * _WindSpeed) * float4(0.3, 0.5, 0.4, 1.23) * 4; // 1.23 (Silent: 1.2): the gust
                                                                                    // sequence no longer repeats every 25 s
            float4 s = sin(frac(waves) * 6.2831853 - 3.1415927);
            s *= s; s *= s;                                   // sin^4: uneven, gusty pushes
            float push = dot(s, float4(0.012, 0.02, -0.06, 0.048) * 2) / 0.16; // 1 = the strongest gust
            float across = dot(s, float4(0.006, 0.02, -0.02, 0.1)) / 0.16;
            float amount = v.color.a * v.color.r * 32 * _WindStrength * 0.01;   // metres at push 1
            float3 waveOff = (dir * push - side * across) * amount; // Silent pushes toward -z, where its crests travel
            // leaf tremble (Horizon Zero Dawn, as in Crispy Foliage TrembleGrass); the phase drifts slowly in world
            // space (0.5 rad/m) plus the smooth noise phase in B. Direction: normal on trees, horizontal up to 3 m tall
            float3 nw = UnityObjectToWorldNormal(v.normal);
            float ta = (v.color.b - 0.5) * 3.1415927;
            float3 hd = dir * cos(ta) + side * sin(ta);
            float3 tdir = lerp(nw, hd, saturate((6 - v.color.r * 32) / 3));
            float tr = sin(0.5 * (wp.x + wp.y + wp.z) + 2.65 * _Time.y * _FlutterSpeed + v.color.b * 6.2831853);
            float3 trembleOff = tdir * tr * v.color.g * _FlutterStrength;
            float3 off = waveOff + trembleOff;
            v.vertex.xyz = mul(unity_WorldToObject, float4(wp + off, 1)).xyz;
            // bend the normals and tangents with the offset (the light shimmer on moving leaves); capped at 0.3 so
            // a tall tree's big push doesn't swing its lighting further than a small tree's
            float3 offObj = mul((float3x3)unity_WorldToObject, off * min(1, 0.3 / max(length(off), 1e-4)));
            v.normal = normalize(v.normal + offObj);
            v.tangent.xyz = normalize(v.tangent.xyz + offObj);
        #endif
            // object origin minus camera first: the large-number subtraction happens once per object, not per pixel
            float3 op = float3(unity_ObjectToWorld[0].w, unity_ObjectToWorld[1].w, unity_ObjectToWorld[2].w);
            o.camRel = mul((float3x3)unity_ObjectToWorld, v.vertex.xyz) + (op - _WorldSpaceCameraPos);
        }
        void surf (Input IN, inout SurfaceOutputStandard o)
        {
            float2 uv = IN.uv_MainTex;
            o.Alpha = 1;
            o.Metallic = 0;
            if (_AtlasLayout > 0.5 && uv.x >= _BarkU0)
            {
                o.Albedo = tex2D(_MainTex, uv).rgb * _Color.rgb;
                o.Smoothness = _BarkGlossiness;
                return;
            }
            if (_AtlasLayout < 0.5 && uv.x >= _BarkTag * 0.5)
            {
                float2 t = uv - float2(_BarkTag, 0);
                float2 sz = _BarkRect.zw - _BarkRect.xy;
                float2 auv = _BarkRect.xy + frac(t) * sz;
                float2 dx = ddx(t) * sz, dy = ddy(t) * sz;
                o.Albedo = tex2Dgrad(_MainTex, auv, dx, dy).rgb * _Color.rgb;
                fixed3 n = UnpackNormal(tex2D(_BumpMap, t)); // own Repeat texture: tiles on the unwrapped UVs
                n.xy *= _BarkNormalStrength;
                o.Normal = normalize(n);
                o.Smoothness = _BarkGlossiness;
                return;
            }
            // far foliage: once the leaf texture is minified past mip 1 (beyond a few metres) `far` ramps to 1 over one
            // mip level. It adds up to _LeafMipBias extra mip blur, so sub-pixel leaves stop flickering while close
            // leaves stay sharp, and (A2C path) lowers the cutoff by _A2CFarCutoffDrop, which keeps far crowns as
            // full as the cutout's (A2C's averaging thins them ~10 % otherwise)
            float2 dx = ddx(uv), dy = ddy(uv);
            float lod = 0.5 * log2(max(dot(dx, dx), dot(dy, dy)) * _MainTex_TexelSize.z * _MainTex_TexelSize.w);
            float far = saturate(lod - 1);
            float g = exp2(_LeafMipBias * far);
            fixed4 c = tex2Dgrad(_MainTex, uv, dx * g, dy * g) * _Color;
            // edge fade: a card seen edge-on shows as a dotted streak past the crown (worse with big cards). Its true
            // face normal comes from the screen derivatives (the mesh normals are the crown proxy's, not the card's);
            // alpha ramps to 0 as |cos| between view and card drops from 2.5x to 1x _EdgeFadeAngle. A degenerate
            // derivative pair (sub-pixel slivers) gets no fade.
            float3 fc = cross(ddy(IN.camRel), ddx(IN.camRel));
            float fl = dot(fc, fc);
            float cosv = fl > 1e-24 ? abs(dot(fc * rsqrt(fl), normalize(-IN.camRel))) : 1;
            half fade = lerp(1, saturate((cosv - _EdgeFadeAngle) / (1.5 * _EdgeFadeAngle)), _EdgeFade);
        #if defined(UNITY_PASS_META)
            clip(c.a - _Cutoff); // bakes keep the whole leaf silhouette
        #elif defined(UNITY_PASS_SHADOWCASTER)
            // light shadow maps keep the whole silhouette. The camera depth texture (drawn with this pass; the
            // screen-space shadows read it) must match the faded colour, or a faded card still occludes the ground
            // behind it in the shadow collector and shows as a bright ghost sliver over shadowed ground.
            // Unity zeroes unity_LightShadowBias for the camera depth pass.
            if (unity_LightShadowBias.z == 0 && unity_LightShadowBias.x == 0) c.a *= fade;
            clip(c.a - _Cutoff);
        #else
            c.a *= fade;
            if (_AlphaToCoverage > 0.5)
            {
                half a = (c.a - (_Cutoff - _A2CFarCutoffDrop * far)) / max(fwidth(c.a), 1e-4) + 0.5;
                clip(a);
                o.Alpha = saturate(a);
            }
            else
            {
                clip(c.a - _Cutoff);
            }
        #endif
            o.Albedo = c.rgb;
            float sgn = (IN.facing > 0 || _UseMeshNormalsBothSides > 0.5) ? 1 : -1;
            o.Normal = fixed3(0, 0, sgn);
            o.Smoothness = _Glossiness;
        }
        ENDCG
    }
    FallBack "Legacy Shaders/Transparent/Cutout/Diffuse"
}
