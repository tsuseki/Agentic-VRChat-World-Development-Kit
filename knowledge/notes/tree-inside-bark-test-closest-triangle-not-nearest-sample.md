---
title: Test leaf points inside thin bark with the signed distance to the closest triangle, not the nearest bark sample
topic: geometry-meshes-uvs
tags: [trees, wind, pass-through, signed distance, thin canes, measurement]
summary: Classifying a leaf point as inside the bark by its nearest bark sample fails near 2–3 cm canes, because a sample on the far side or on a cane cap 8–30 cm away flips the sign (179 of 213 "inside" points were in the open); use the signed distance to the closest of the k nearest bark triangles, averaging shared-edge faces.
---
**Symptom:** A wind pass-through check (leaf cards moving into the bark) reported 3–10 % base slip on cane shrubs that looked clean.

**Cause:** With thin canes (2–3 cm radius) the nearest bark sample can lie on the far side of the cane or on a cane cap 8–30 cm away, so its normal gives the wrong side: 179 of 213 "inside" points were in the open.

**Fix / rule:** Use the signed distance to the closest of the k nearest bark triangles, with face normals oriented by their corner normals. On a shared edge or vertex, average the signed distances of the faces that share it. Re-test exactly at rest and in every frame.

**Verify:** render the flagged points at rest and in a gust frame and check that they really sit inside the bark.
