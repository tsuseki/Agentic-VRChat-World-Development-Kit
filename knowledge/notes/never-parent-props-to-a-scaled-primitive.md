---
title: Never parent new props under a scaled primitive
topic: placement-layout-design
tags: [SetParent, lossyScale, primitive, blockout, hierarchy]
summary: Parenting built props under a scaled primitive (board, slab, wall) multiplies its scale into them; walk up to a unit-lossyScale ancestor first.
---
**Symptom:** Book stacks parented under a shelf board come out 9 mm tall and 80 mm deep instead of 190 x 220 mm. Nothing errors; only printed bounds give it away.

**Cause:** The board is a Cube primitive with `localScale = (0.32, 0.04, 1.11)`, and the parent's scale multiplies into children. Most blocked-out shell pieces (boards, slabs, walls, plinths, table tops) are scaled primitives; furniture roots are usually unit-scale.

**Fix / rule:** Never `SetParent` a new prop to a transform that carries scale. Find a unit-scale ancestor:
```csharp
System.Func<Transform,string,Transform> SAFEHOST = (target,nm) => {
  var par=target.parent;
  while(par!=null){
    var ls=par.lossyScale;
    if(Mathf.Abs(ls.x-1)<0.005f&&Mathf.Abs(ls.y-1)<0.005f&&Mathf.Abs(ls.z-1)<0.005f) break;
    par=par.parent;
  }
  var g=new GameObject(nm); g.transform.SetParent(par,false);
  g.transform.rotation=Quaternion.identity; return g.transform;
};
```
Position the host in world space and give children local offsets.

**Verify:** Log `lossyScale` of every host before building and assert each finished group's height is within ~20 % of intended.
