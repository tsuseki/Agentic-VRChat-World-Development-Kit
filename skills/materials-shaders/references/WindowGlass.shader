// AWDK window/panel glass for the Built-in Render Pipeline: a see-through pane with a soft, blurred reflection.
// Reflection model of Unity Standard's premultiplied transparent glass (Fresnel = lerp(F0, grazing, Pow4(1 - N.V)),
// as in UNITY_BRDF_PBS) with the strength exposed: _ReflectHeadOn = F0 (linear), _ReflectGrazing = the edge-on value.
// Defaults are the tested look: F0 0.04 (real glass), grazing 0.71, smoothness 0.70 (samples a GGX-convolved probe mip,
// so the reflection is a blur, not a blocky 256 px cubemap), with the glass's exterior probes at intensity 3.0.
// Recipe, probe rig and tuning: .omp/skills/materials-shaders/references/window-glass.md
// Premultiplied transparency, no depth write, no shadow caster, no meta pass: glass stays out of the bake.
Shader "AWDK/WindowGlass"
{
    Properties
    {
        _Color ("Tint (A = coverage)", Color) = (0.06, 0.065, 0.07, 0.14)
        _Glossiness ("Smoothness (reflection blur)", Range(0, 1)) = 0.7
        _ReflectHeadOn ("Reflection facing the pane (F0, linear)", Range(0, 1)) = 0.04
        _ReflectGrazing ("Reflection edge-on", Range(0, 1)) = 0.71
        [Enum(UnityEngine.Rendering.CullMode)] _Cull ("Cull", Float) = 2
    }
    SubShader
    {
        Tags { "Queue" = "Transparent" "RenderType" = "Transparent" "IgnoreProjector" = "True" }
        Pass
        {
            Tags { "LightMode" = "ForwardBase" }
            Blend One OneMinusSrcAlpha
            ZWrite Off
            Cull [_Cull]

            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_fog
            #pragma multi_compile_instancing
            #pragma target 3.0
            #include "UnityCG.cginc"
            #include "UnityStandardUtils.cginc"
            #include "UnityImageBasedLighting.cginc"

            fixed4 _Color;
            half _Glossiness;
            half _ReflectHeadOn;
            half _ReflectGrazing;

            struct appdata
            {
                float4 vertex : POSITION;
                float3 normal : NORMAL;
                UNITY_VERTEX_INPUT_INSTANCE_ID
            };

            struct v2f
            {
                float4 pos : SV_POSITION;
                float3 worldPos : TEXCOORD0;
                float3 worldNormal : TEXCOORD1;
                UNITY_FOG_COORDS(2)
                UNITY_VERTEX_OUTPUT_STEREO
            };

            v2f vert (appdata v)
            {
                v2f o;
                UNITY_SETUP_INSTANCE_ID(v);
                UNITY_INITIALIZE_OUTPUT(v2f, o);
                UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(o);
                o.pos = UnityObjectToClipPos(v.vertex);
                o.worldPos = mul(unity_ObjectToWorld, v.vertex).xyz;
                o.worldNormal = UnityObjectToWorldNormal(v.normal);
                UNITY_TRANSFER_FOG(o, o.pos);
                return o;
            }

            half3 SampleProbe(UNITY_ARGS_TEXCUBE(tex), half4 hdr, float3 dir, half mip)
            {
                half4 c = UNITY_SAMPLE_TEXCUBE_LOD(tex, dir, mip);
                return DecodeHDR(c, hdr);
            }

            fixed4 frag (v2f i, fixed facing : VFACE) : SV_Target
            {
                float3 n = normalize(i.worldNormal) * (facing > 0 ? 1.0 : -1.0);
                float3 v = normalize(UnityWorldSpaceViewDir(i.worldPos));
                float3 r = reflect(-v, n);
                half nv = saturate(dot(n, v));

                half perceptualRoughness = 1.0h - _Glossiness;
                half mip = perceptualRoughnessToMipmapLevel(perceptualRoughness);

                float3 r0 = r;
                #if UNITY_SPECCUBE_BOX_PROJECTION
                r0 = BoxProjectedCubemapDirection(r, i.worldPos, unity_SpecCube0_ProbePosition, unity_SpecCube0_BoxMin, unity_SpecCube0_BoxMax);
                #endif
                half3 env = SampleProbe(UNITY_PASS_TEXCUBE(unity_SpecCube0), unity_SpecCube0_HDR, r0, mip);
                #if UNITY_SPECCUBE_BLENDING
                float blend = unity_SpecCube0_BoxMin.w;
                if (blend < 0.99999)
                {
                    float3 r1 = r;
                    #if UNITY_SPECCUBE_BOX_PROJECTION
                    r1 = BoxProjectedCubemapDirection(r, i.worldPos, unity_SpecCube1_ProbePosition, unity_SpecCube1_BoxMin, unity_SpecCube1_BoxMax);
                    #endif
                    half3 env1 = SampleProbe(UNITY_PASS_TEXCUBE_SAMPLER(unity_SpecCube1, unity_SpecCube0), unity_SpecCube1_HDR, r1, mip);
                    env = lerp(env1, env, blend);
                }
                #endif

                half f = 1.0h - nv;
                f *= f;
                f *= f;
                half refl = lerp(_ReflectHeadOn, _ReflectGrazing, f);

                half3 ambient = max(half3(0, 0, 0), ShadeSH9(half4(n, 1)));
                half3 col = _Color.rgb * ambient * _Color.a + env * refl;
                // Standard premultiplied: alpha = 1 - oneMinusReflectivity * (1 - a), reflectivity from F0 (not Fresnel).
                half alpha = saturate(1.0h - (1.0h - _ReflectHeadOn) * (1.0h - _Color.a));
                fixed4 o = fixed4(col, alpha);
                UNITY_APPLY_FOG_COLOR(i.fogCoord, o, fixed4(0, 0, 0, 0));
                return o;
            }
            ENDCG
        }
    }
    Fallback Off
}
