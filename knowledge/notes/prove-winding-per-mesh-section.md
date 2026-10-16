---
title: Prove triangle winding for every section of a hand-built mesh
topic: geometry-meshes-uvs
tags: [winding, normals, procedural mesh, end caps, double-sided, backface]
summary: A single facing test passes on the main body and says nothing about caps or flaps; record each section's triangle range and orient each against its own outward direction.
---
**Symptom:** A hand-built multi-part mesh (e.g. a rolled towel) takes many builds; each failure is a winding bug in a different part: barrel inside-out (reads black), then inverted end caps (you see through into the dark), then a double-sided hem showing a black band only on instances rotated to show it, so it looks per-instance.

**Cause:** "Is the first triangle facing out?" only tests the first section.

**Fix / rule:** Record each section's triangle range while building and orient each against its expected outward direction:
```csharp
System.Action<int,int,Vector3,string> Orient = (s,e,want,tag) => {
  var a=vs[tr[s*3]]; var b=vs[tr[s*3+1]]; var c=vs[tr[s*3+2]];
  if (Vector3.Dot(Vector3.Cross(b-a,c-a).normalized, want) < 0)
    for (int i=s;i<e;i++){ int t=tr[i*3+1]; tr[i*3+1]=tr[i*3+2]; tr[i*3+2]=t; }
};
Orient(0, bodyEnd, radialOfFirstVert, "barrel");
Orient(cap0s, cap0e, new Vector3(0,0,-1), "cap -Z");
Orient(cap1s, cap1e, new Vector3(0,0, 1), "cap +Z");
```
Avoid two-sided fabric made of duplicated reversed triangles: coincident opposed faces shade as a black band from one side. Single-sided and slightly proud (4-9 mm) reads correctly at half the cost.

**Verify:** Independently on the finished mesh, count vertices with `Dot(normal, outwardDir) < 0`; it must be 0.
