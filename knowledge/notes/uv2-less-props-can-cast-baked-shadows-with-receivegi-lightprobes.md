---
title: Make UV2-less furniture cast baked shadows with ContributeGI + receiveGI = LightProbes
topic: probes-reflection-and-light
tags: [receiveGI, ContributeGI, UV2, light probes, contact shadow, furniture pack]
summary: Setting a UV2-less prop ContributeGI with receiveGI = LightProbes lets it cast and occlude in the lightmap while being lit by probes, with no lightmap UVs or atlas space.
---
**Symptom:** Bought furniture without UV2 is probe-lit and contributes nothing to the bake under Baked-only lights in Built-in RP: every sofa and table meets the floor with a clean edge and no contact darkening, reading as stickers.

**Fix / rule:** Set the renderer **ContributeGI** and **receiveGI = LightProbes**. It then casts shadows and occludes GI into the lightmap while receiving from probes:
```csharp
var prop = typeof(MeshRenderer).GetProperty("receiveGI");
object LP = System.Enum.Parse(prop.PropertyType, "LightProbes");
foreach (var r in root.GetComponentsInChildren<MeshRenderer>(true)) {
    if (!r.enabled) continue;
    GameObjectUtility.SetStaticEditorFlags(r.gameObject, flags | StaticEditorFlags.ContributeGI);
    prop.SetValue(r, LP);
    r.shadowCastingMode = ShadowCastingMode.On;
    r.lightProbeUsage   = LightProbeUsage.BlendProbes;
}
```

**Pitfalls:**
- The enum is `UnityEngine.ReceiveGI`, not `UnityEngine.Rendering.ReceiveGI` (compile error). In a code body without `using` directives, reflection as above is least fragile.
- The flag only matters on ContributeGI objects, and `SetStaticEditorFlags` does not reach children; set it per renderer.

**Verify:** Before baking, count ContributeGI renderers split by `receiveGI`, and assert zero lightmapped renderers lack UV2 (one bad UV2 can poison a whole atlas).
