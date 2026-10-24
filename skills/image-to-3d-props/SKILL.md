---
name: image-to-3d-props
description: >-
  Make custom VRChat world props with image generation + image-to-3D (e.g. Tripo):
  grey-box at real dimensions, capture orthographic views, restyle the front with
  image-to-image, generate consistent multiview references, get human design approval,
  then generate, import (GLB via glTFast), add lightmap UV2, scale and place correctly.
  Use when no suitable existing asset is found and a furniture piece or hero prop needs
  to be created from references.
---

# Image-to-3D props for VRChat worlds

Single-view generation must infer hidden sides and loses detail. Consistent multiview
input with correct proportions gives much better results for furniture and hero props.
The blockout locks dimensions, image generation establishes style, and the 3D service
reconstructs.

For simple/organic props (a rock, a plant, a cushion) skip straight to step 4 with a single
image or a text prompt — the full pipeline is for pieces where proportions and style matter.

Before generating anything, check whether a suitable asset already exists — see
[worldbuilding-assets](../worldbuilding-assets/SKILL.md).

A plush or fumo of a character or avatar has its own pipeline:
[fumo-plushie](../fumo-plushie/SKILL.md).

## 1. Blockout in Unity at reference-scale dimensions

Grey-box the prop at its **reference-scale dimensions**: real-world size ×k (k = 0.8,
fixed; props scale like everything else; check it beside a capsule at the WORLD.md reference, default 1.3 m eye) in a
scratch scene. Simple cubes/cylinders are enough — it only needs silhouette and
proportions. Remove primitive auto-colliders.

## 2. Capture four ortho-ish views

Screenshot the blockout from **front, left, back, right** with an orthographic or long-lens
camera, neutral plain background, no shadows, consistent camera scale. Save e.g.
`blockouts/<prop>_front.png`. Left/right are **subject-relative**.

## 3. Reference images (image-to-image)

1. **Front first:** image-to-image the front blockout into the target style. Prompt pattern:
   *"turn this grey blockout into a photorealistic <object>: <materials, details>. Keep the
   EXACT proportions and silhouette of the blockout. Straight-on front view, neutral
   light-grey studio background, soft even lighting."*
2. **Remaining views:** pass the **finished front image first** plus the blockout of the new
   angle: *"the same <object> as in the first image, now seen directly from the back,
   matching the second image's angle and proportions. Same materials, same lighting,
   neutral background."* Repeat for left/right so every view depicts the same object.
3. Lock pose, silhouette, scale, materials, colour blocks and asymmetry. One complete
   silhouette per file; no labels, contact sheets or cast shadows.
4. **Look at every image together before continuing** — if a view drifted (different object,
   wrong angle), regenerate it. Bad refs make bad meshes.

A reusable style block per world (one paragraph of materials/mood) keeps props consistent.

## 4. Human approval gate

A human approves the design (the reference set) **before** any paid 3D generation. Setup
or access checks do not authorize generation. Never purchase credits, upgrade a plan or
accept a charge without explicit authorization.

## 5. Generate the 3D model

- **Studio (web UI) and API billing are separate** on Tripo — subscription credits do not
  fund API calls and vice versa. Pick the route deliberately; check the current price of the
  operation in the official docs rather than hardcoding estimates.
- Multiview API input order is **[front, left, back, right]**; leave a missing side slot as an
  empty entry rather than shifting the others. Choose the model version explicitly for
  reproducibility.
- **Face limits:** world props ~2000–8000 faces; hero props up to ~20000 (with a low-poly
  topology mode where available). Set an overall triangle budget for all furniture in a room
  and stay within it.
- Submit once; on a timeout, find the existing task rather than resubmitting. Signed
  download URLs expire — re-query the task for a fresh URL instead of regenerating.
- Inspect the generated mesh from all sides; a preview image alone is not quality proof.
- Never print, paste or commit API keys, auth files, tokens or request headers. Keep any
  key in a gitignored local file read only by your wrapper script.

Tripo also offers an official **DCC Bridge** that sends an already-generated Studio model to
Unity or Blender. It transfers; it is not a generation API. It recognizes only the first
launched editor instance — confirm the receiving project. Keep **Generate Colliders = false**.

### Running it: the `image-to-3d` tool

Generate with `python .omp/scripts/tool.py image-to-3d` (`.omp/docs/tools.md`): `--image` for one
view, or `--front/--left/--back/--right` for multiview, `--faces` for the face limit, `--output
<prop>.glb`. The user's `.omp/local/tools.json` decides which service runs. Exit 4 means the
backend spends money: get the user's approval for this generation (the design approval of step 4
is not a spend approval unless they said so), then re-run with `--approve-spend`. Exit 3 hands the
step to you or the user. A printed task id lets `--resume` fetch a timed-out task without paying
again. Reference images come from the `image-gen` / `image-edit` tools. Face limits and low-poly
modes constrain geometry, not final rigging quality. Avatar clothing needs fitting and skinning on
a duplicate, not static lightmapping (`.omp/agents/blender-modeler.md` "Avatar work").

## 6. Import into Unity

1. Import GLB with the project's installed **glTFast** workflow (FBX imports natively).
   Drive the open Editor through Unity MCP tools, never scene YAML.
2. **Check lightmap UV2.** Generated GLBs may lack it. For static lightmapped props without
   UV2: duplicate the mesh, run `UnityEditor.Unwrapping.GenerateSecondaryUVSet(mesh)`, save
   it as a `.asset`, and assign it to the MeshFilter. Verify a long unwrap actually
   completed before retrying.
3. Confirm materials match the project's render pipeline and installed shaders; PBR maps
   may need manual material setup. Magenta = shader/pipeline mismatch.
4. GLB sub-asset textures can ship uncompressed — re-encode them as compressed Unity
   texture assets before shipping (see
   [vrchat-world-optimization](../vrchat-world-optimization/SKILL.md)).
5. No MeshCollider and no prop colliders; strip any imported seat stations.

## 7. Scale and place correctly

Generated models usually have **centered pivots** and an arbitrary forward axis.

1. With the object at **identity rotation**, measure its renderer bounds.
2. Compute **per-axis local scale** = target dimension / measured dimension. World-ratio scaling
   after rotation distorts models.
3. **Rotate last**, after scaling, to the desired facing.
4. **Position** by bounds: seat the object so `bounds.min.y` sits on the floor (a centered
   pivot placed at floor height sinks half the object; start at half-height and seat by the
   bounds delta). Rounded bases may need a small sink after raycast seating.
5. **Confirm the forward axis with a screenshot** from a known camera angle — generated
   forward axes vary.
6. Set appropriate static flags for unmoving props; after any lighting bake, bake
   reflection probes.

## 8. Review

Get an independent visual review: composition after placement, final-render after
lighting. A downloaded mesh is not yet a finished world prop. Report separately what was
actually verified (references, approval, generation, download, import, UV2, placement).
