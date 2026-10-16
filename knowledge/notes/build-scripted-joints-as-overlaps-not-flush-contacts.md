---
title: Scripted assemblies with exactly flush parts z-fight — build joints as overlaps
topic: geometry-meshes-uvs
tags: [z-fighting, coplanar, scripted placement, joints, balustrade, bounds check]
summary: Parts placed so they meet exactly share a face plane and z-fight on every instance; push parts 1–3 cm into each other and assert zero coplanar pairs.
---
**Symptom:** A code-built stair balustrade shows "heavy z-fighting" — 12 fighting seams where rail meets panel, LED meets stringer, stringer meets tread edge.

**Cause:** Exact contact is two coplanar faces sharing a depth value. Hand-modelling hides it (snap and eyeball); scripted placement hits the nominal number every time, so *every* instance fights.

**Fix / rule — build joints as overlaps:**
- Push each part 0.01–0.03 m **into** its neighbour (rail centre at nose+0.93, not +0.92, so the panel top buries 0.03 m into the rail).
- Extend raked/level segments past their end joints (`length += 2*ext`, ext ≈ 0.05–0.10) so runs interpenetrate at landings instead of forming a V-notch of end caps.
- Inset parts from a shared silhouette edge (stringer 0.02 m inside the tread edge) rather than aligning flush.

**Verify:** sweep every renderer pair and flag flush-on-one-axis while overlapping on the other two (a shared face area). Target 0:
```csharp
var ov = new Vector3(Mathf.Min(a.max.x,b.max.x)-Mathf.Max(a.min.x,b.min.x), /* y */, /* z */);
int touching=0, overlapping=0;
for(int k=0;k<3;k++){ if(Mathf.Abs(ov[k])<0.0015f) touching++; else if(ov[k]>0.004f) overlapping++; }
if(touching>=1 && overlapping==2) // coplanar pair
```
Pairs that touch without shared area are correctly ignored. Use a grazing close-up render as the positive control — a distant head-on shot hides z-fighting.
