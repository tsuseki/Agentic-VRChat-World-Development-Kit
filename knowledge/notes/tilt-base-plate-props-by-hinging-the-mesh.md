---
title: A prop with a wide flat foot cannot be tilted as a whole object
topic: geometry-meshes-uvs
tags: [tilt, pivot, base plate, parasol, rotation, sinking]
summary: Rotating a prop that has a wide base plate always drives a plate corner underground; hinge the mesh above a joint instead.
---
**Symptom:** A reviewer asks for a lean on a parasol (15-22 deg). Rotating the GameObject about the mast foot fails at every angle, even 4 deg: a corner of the 0.6 m square base plate sinks into the deck. Re-seating the object afterwards just floats the plate off the deck by the same amount.

**Cause:** The mesh includes the flat foot. Measured cost was **0.033 m of sink per degree** (4 deg -> 0.13 m, 17 deg -> 0.56 m). The relationship is linear and starts failing immediately, so there is no object-space pivot that tilts it legally. Do not hunt for a smaller angle.

**Fix / rule:**
- If the asset is parametric, hinge *inside* the mesh: rotate only the vertices above a joint height about that joint, leave the foot untouched, and add a knuckle collar straddling the cut so the wedge gap never shows. (Example result: 17 deg above z 1.62 m, base plate still flat, canopy centroid 0.20 m off the mast axis.)
- If the asset is not parametric, say so and deliver the variation another way (a different mesh, a furled variant, different diameters) rather than shipping a floating or sunken base.

**Verify:** Compare the base plate's lowest vertices against the deck height after the change; all corners should sit on the surface.
