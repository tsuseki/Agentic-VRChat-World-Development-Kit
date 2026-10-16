// Used by ZFightRender. Globals are set per draw from a command buffer:
//   _ZTieId   renderer ID colour      _ZTieCull  the renderer's cull mode
//   _ZTieA, _ZTieB, _ZTieK, _ZTieMinTol   tie tolerance = max(_ZTieMinTol, _ZTieA + _ZTieB * depth + _ZTieK * depth^2)
// Pass 0 (visible layer): ID colour to target 0, linear eye depth to target 1, normal depth test.
// Pass 1 (ties): for every fragment of a renderer other than the visible one at that pixel, output
//   its ID when its eye depth is within the tolerance of the visible surface; discard otherwise.
Shader "Hidden/AWDK/ZTieId"
{
    CGINCLUDE
    #include "UnityCG.cginc"
    float4 _ZTieId;
    struct v2f { float4 pos : SV_POSITION; float eye : TEXCOORD0; };
    v2f vert(float4 vertex : POSITION)
    {
        v2f o;
        o.pos = UnityObjectToClipPos(vertex);
        o.eye = -UnityObjectToViewPos(vertex.xyz).z;
        return o;
    }
    ENDCG

    SubShader
    {
        Tags { "RenderType" = "Opaque" }
        Pass
        {
            ZWrite On
            ZTest LEqual
            Cull [_ZTieCull]
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma target 3.5
            struct f2o { float4 id : SV_Target0; float4 depth : SV_Target1; };
            f2o frag(v2f i)
            {
                f2o o;
                o.id = _ZTieId;
                o.depth = float4(i.eye, 0, 0, 1);
                return o;
            }
            ENDCG
        }
        Pass
        {
            ZWrite Off
            ZTest Always
            Cull [_ZTieCull]
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma target 3.5
            Texture2D _ZTieIds;
            Texture2D _ZTieDepth;
            float _ZTieA;
            float _ZTieB;
            float _ZTieK;
            float _ZTieMinTol;
            float4 frag(v2f i) : SV_Target
            {
                int3 p = int3(i.pos.xy, 0);
                float d1 = _ZTieDepth.Load(p).r;
                if (d1 <= 0) discard;
                float3 visible = round(_ZTieIds.Load(p).rgb * 255.0);
                if (all(visible == round(_ZTieId.rgb * 255.0))) discard;
                float tol = max(_ZTieMinTol, _ZTieA + _ZTieB * d1 + _ZTieK * d1 * d1);
                if (abs(i.eye - d1) > tol) discard;
                return _ZTieId;
            }
            ENDCG
        }
    }
}
