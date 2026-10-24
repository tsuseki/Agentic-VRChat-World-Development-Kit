# Concept views: references and prompt templates

Four portrait views (front, left, right, back) of one fumo-style plush, made with the `image-edit` tool.
The front is made first and approved by the user; the other three are edits of the approved front.

## 1. References

Put these in `<run>/refs/` and crops in `<run>/work/`. Image references never go into the kit.

| File | What | From |
|---|---|---|
| `ref_front.png` | full-body front of the avatar, cropped with margin | user's avatar screenshots |
| `ref_face.png` | face close-up: eyes, brows, marks, make-up | same |
| `ref_side.png`, `ref_back.png` | side and back: hair at the back, tails, bags | same (skip if not given) |
| `style_real_fumo.png` | photo of a real fumo-style plush: construction reference | user-supplied |
| `approved_plush_front.png` | the approved front view of a plush already in this world | earlier run (skip for the first plush) |

Before writing the prompt, list what identifies the character: hair colour and cut, ears, tails, eye
colours, marks, accessories, outfit colours and key pieces. Ask the user only for what the
screenshots don't show.

## 2. Front view

```
python .omp/scripts/tool.py image-edit --prompt-file prompts/front_v1.txt \
  --reference work/ref_front.png --reference work/ref_face.png \
  --reference refs/style_real_fumo.png [--reference refs/approved_plush_front.png] \
  --aspect portrait --quality medium --output views/front_v1.png
```

`front_v1.txt` (fill the `<...>`; drop the "image 4" sentence for the first plush):

```
Make an official Touhou Project 'Gift fumo' plush doll of the character from the CHARACTER reference
images (image 1 is the full-body front view, image 2 a face close-up). Image 3 is a real fumo (copy its
construction, not its character) and image 4 is an approved plush of ours: copy its exact proportions,
felt/minky look, simplicity, pose and rendering style, not its character. Rules: very simple, made of a
few flat felt/minky fabric pieces with clean edges; big round head about half the height; short stubby
body; hair is smooth fabric, NO individual strands, NO fur texture, NO detailed sculpted hair; face is
flat machine embroidery like images 3 and 4: two big simple eyes, each a solid colour iris with a dark
outline thicker on top and ONE small white dot highlight, a thin brow line, a tiny thin closed smile
line, no nose, no lashes, no gradients, faint pink blush; stubby rounded arms at the sides, short
chunky cylinder legs forward, seated upright like image 4. Clothes as flat colour blocks with only the
character's key accents (simplify patterns to a few large shapes or a plain colour).

Character details to keep (these must read at a glance): <hair colour and cut, ears, tails, eye
colours, marks, accessories, outfit pieces and colours, legwear, footwear, skin tone>.

Straight-on FRONT view at eye level, whole doll centred with generous margin, plain pure white
background, soft even light, no shadow, no text, one doll.
```

- Asymmetric features by **image side**: "the eye on the LEFT side of the image is sky blue", "a
  braid over the doll's shoulder on the RIGHT side of the image".
- Busy patterns (plaid, prints, paint splatter) become a few large shapes.
- Legs are chunky stubby cylinders with round ends, covered by the legwear colour.

## 3. Fixing one detail of an approved front

Edit the approved image itself; never regenerate from scratch:

```
The reference image is an approved fumo plush doll. Reproduce EXACTLY the same doll, same camera,
same framing, same colours, <list every feature>. Change ONLY <the detail>: <what it becomes>. Plain
pure white background, soft even light, no shadow, no text, one doll.
```

## 4. Left, right and back views

Reference 1 = the approved front, reference 2 = the matching character view (`ref_side` / `ref_back`,
else `ref_front`).

```
python .omp/scripts/tool.py image-edit --prompt-file prompts/left_v1.txt \
  --reference views/front_v2.png --reference work/ref_side.png \
  --aspect portrait --quality medium --output views/left_v1.png
```

Side (left; for right swap LEFT/RIGHT and "left edge"/"right edge"):

```
The first reference image is the approved front view of a simple Gift-fumo plush doll. Show EXACTLY
the same doll, seen exactly from the doll's own LEFT side (strict 90-degree side profile, camera at the
doll's eye level), so the doll faces toward the LEFT edge of the image. The legs stretch toward the
left. Keep the same very simple construction (flat felt pieces, smooth hair cap with large flaps, no
strands, no fur texture), identical proportions, colours and seated pose, same scale in frame. Plain
pure white background, soft even light, no shadow, no text, one doll with generous margin.
```

Back:

```
The first reference image is the approved front view of a simple Gift-fumo plush doll. Show EXACTLY
the same doll, seen directly from BEHIND (exact back view, camera at the doll's eye level, 180 degrees
from the front view). We see the back of the head and hair, the back of the ears, the back of the
outfit and the tail if any; the face is not visible. Keep the same very simple construction (flat felt
pieces, smooth hair cap with large flaps, no strands, no fur texture), identical proportions, colours
and seated pose, same scale in frame. Plain pure white background, soft even light, no shadow, no
text, one doll with generous margin.
```

## 5. Approval sheet

Show the four views side by side (front, left, right, back) with the character screenshot. Look for
drift first: a different hairstyle, an accessory that moved sides, changed proportions. Regenerate
the drifting view. The user approves the set; record the approved file names and the prompts in
`<run>/BRIEF.md`.
