"""Bloom atlas on the same mesh (K-B): an approved leaf atlas gets flowers added by image edit, cell by cell, and the
edit is accepted only if the leaves and twigs stayed where they were. The bloom atlas keeps the cell rects, attach
points and bark strip of the base atlas, so it is a material swap on the same mesh (a `_Bloom` prefab variant).

  python bloom_atlas.py prep    <atlas_RGBA.png> <Cards.json> --out <dir> --key <key> [--cells 0,1,2]
  python bloom_atlas.py edit    <atlas_RGBA.png> <Cards.json> --out <dir> --prompt-file <txt> [--backend <name>]
  python bloom_atlas.py compose <atlas_RGBA.png> <Cards.json> --out <dir> --key <key> --flower-hue LO,HI [--iou 0.9]
  python bloom_atlas.py all     ...   (prep, edit, compose)

prep: each cell (alpha composited over the flat key colour) is padded bottom-centred to a 2:3 portrait canvas (the
  attach point stays on the canvas bottom) and upscaled to 1024 x 1536: <out>/src_<i>.png + src_<i>.json.
edit: `.omp/scripts/tool.py image-edit` per cell with the prompt file and src_<i>.png as the only reference (prompt:
  "add <flowers> on the existing twigs, change nothing else, keep the flat <key> background"), skipping edits that
  exist: <out>/edit_<i>.png. Paid: run it only with the user's approval of the spend.
compose: each edit is keyed (soft matte, the key from --key, despill only in a 4 px band inside the matte edge), scaled
  back to the canvas and registered to the source cell: scales 0.96-1.04 about the attach point and shifts up to
  +-16 px, maximising the IoU of the source's opaque mask (alpha > 115 = the 0.45 cutout) with the edit's opaque
  NON-flower mask. Flower texels = opaque, hue in --flower-hue (deg, wraps), saturation > --flower-sat (0.35), value
  > 0.25. Gate: the 2 px tolerant IoU of those masks >= --iou (default 0.9: the twig network and the leaves did not
  move; texels within 2 px of the other mask count as matched, so the 1-3 px twigs a redraw re-samples don't fail
  it; a mirrored or redrawn spray measured 0.37 strict); a failing cell is
  reported and the atlas is not written (exit 1) unless --keep-going. The bloom cell = the SOURCE cell pixel for
  pixel plus the edit's flower texels (and their soft edge within 2 px) on top, so nothing but the flowers changes;
  then every non-core texel takes the colour of the nearest core texel (no key colour or halo at any mip).
  Reports per cell: iou_t2 (gated), iou (strict), scale, shift, opaque before / after, flower share of the cell (all
  flower texels), floating flowers (flower texels more than 6 px from the source's opaque texels; warn > 0.05).
  Writes <out>/<atlas stem>_Bloom_RGBA.png (the
  whole atlas, bark strip and untouched cells identical) and <out>/bloom_report.json; then run check_key_spill.py on it
  with the same --key, and show it on an approval sheet before any build or prefab uses it.
Prints BLOOMCELL <i> PASS|FAIL iou X ... and BLOOM <png> cells N pass M.
"""
import json, os, subprocess, sys, time
import numpy as np
import matplotlib.colors as mc
from PIL import Image
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import process_gpt_textures as pgt  # noqa: E402  (KEYS)

KIT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))  # the .omp repo
CUT = 115
KEYRGB = {"magenta": (255, 0, 255), "cyan": (0, 255, 255), "blue": (0, 0, 255), "green": (0, 255, 0),
          "yellow": (255, 255, 0)}
GEN = (1024, 1536)


def opt(k, d=None):
    return sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d


def cell_boxes(cards_json, W, H):
    d = json.load(open(cards_json))
    if "layout" in d:
        return [tuple(c) for c in d["layout"]["cells"]]
    out = []
    for c in d["cells"]:
        u0, v0, u1, v1 = c["rect"]
        x0, y0 = int(round(u0 * W)), int(round((1 - v1) * H))
        out.append((x0, y0, int(round(u1 * W)) - x0, int(round((1 - v0) * H)) - y0))
    return out


def canvas_geom(w, h):
    W = max(w, int(np.ceil(h / 1.5))); H = max(h, int(round(W * 1.5)))
    return W, H, (W - w) // 2, H - h


def prep(atlas, boxes, cells, out, key):
    A = np.asarray(Image.open(atlas).convert("RGBA")).astype(np.float32)
    kc = np.array(KEYRGB[key], np.float32)
    for i in cells:
        x, y, w, h = boxes[i]; c = A[y:y + h, x:x + w]; a = c[..., 3:4] / 255.0
        W, H, ox, oy = canvas_geom(w, h)
        can = np.tile(kc, (H, W, 1)); can[oy:oy + h, ox:ox + w] = c[..., :3] * a + kc * (1 - a)
        Image.fromarray(np.clip(can + 0.5, 0, 255).astype(np.uint8)).resize(GEN, Image.LANCZOS).save(f"{out}/src_{i}.png")
        json.dump(dict(cell=i, box=[x, y, w, h], canvas=[W, H], off=[ox, oy]), open(f"{out}/src_{i}.json", "w"))
        print("PREP", i, f"{out}/src_{i}.png", "canvas", W, H)


def edit(cells, out, prompt, backend, quality):
    for i in cells:
        dst = f"{out}/edit_{i}.png"
        if os.path.exists(dst):
            print("SKIP", dst); continue
        cmd = [sys.executable, os.path.join(KIT, "scripts", "tool.py"), "image-edit", "--prompt-file", prompt,
               "--reference", f"{out}/src_{i}.png", "--output", dst, "--quality", quality, "--aspect", "portrait"]
        if backend: cmd += ["--backend", backend]  # the project's required backend (default: tool.py's configured one)
        for w in (0, 60, 180):
            time.sleep(w)
            r = subprocess.run(cmd, capture_output=True, text=True, errors="ignore")
            if r.returncode == 0 and os.path.exists(dst):
                print("EDIT", i, dst); break
            print("RETRY", i, (r.stdout + r.stderr)[-300:])
        else:
            raise SystemExit(f"EDIT FAILED cell {i}")


def key_soft(rgb, key):
    """soft matte + edge-band despill (process_gpt_textures keyness / border threshold); rgb float32 0-255"""
    kf, chans = pgt.KEYS[key]
    kn = kf(rgb[..., 0], rgb[..., 1], rgb[..., 2])
    border = np.concatenate([kn[:8].ravel(), kn[-8:].ravel(), kn[:, :8].ravel(), kn[:, -8:].ravel()])
    thr = np.median(border) * 0.45
    a = np.clip((thr * 1.2 - kn) / (thr * 0.9), 0.0, 1.0)
    solid = a > 0.5; lab, n = ndi.label(solid, np.ones((3, 3)))
    if n:
        sz = ndi.sum(solid, lab, range(1, n + 1)); solid = np.isin(lab, np.nonzero(sz >= 30)[0] + 1)
    a = np.where(ndi.binary_dilation(solid, iterations=2), a, 0.0)
    band = solid & ndi.binary_dilation(~solid, iterations=4)
    ex = np.clip(kn, 0, None) * band
    rgb = rgb.copy()
    for c in chans: rgb[..., c] -= ex
    return np.clip(rgb, 0, 255), a


def flower_mask(rgb, a, hue, sat):
    hsv = mc.rgb_to_hsv(np.clip(rgb / 255.0, 0, 1)); h = hsv[..., 0] * 360
    lo, hi = hue; inb = (h >= lo) & (h <= hi) if lo <= hi else (h >= lo) | (h <= hi)
    return (a * 255 > CUT) & inb & (hsv[..., 1] > sat) & (hsv[..., 2] > 0.25)


def warp(arr, s, dx, dy, ax, ay, order=1):
    """scale s about (ax, ay) then shift (dx, dy), output same shape (zeros outside)"""
    m = np.diag([1.0 / s, 1.0 / s]); off = np.array([ay - (ay + dy) / s, ax - (ax + dx) / s])
    if arr.ndim == 2:
        return ndi.affine_transform(arr, m, offset=off, order=order, mode="constant", cval=0.0)
    return np.stack([ndi.affine_transform(arr[..., k], m, offset=off, order=order, mode="constant", cval=0.0)
                     for k in range(arr.shape[2])], -1)


def iou(a, b):
    u = (a | b).sum()
    return float((a & b).sum() / u) if u else 0.0


def iou_tol(a, b, t=2):
    """IoU with a t px tolerance: texels of either mask within t px of the other count as matched"""
    da, db = ndi.binary_dilation(a, iterations=t), ndi.binary_dilation(b, iterations=t)
    m = ((a & db).sum() + (b & da).sum()) / 2.0; n = a.sum() + b.sum() - m
    return float(m / n) if n else 0.0


def register(src_op, edit_nf, ax, ay, R=16):
    """best (iou, s, dx, dy): coarse at 1/4 resolution over scales and shifts, then refined at full resolution"""
    best = (-1.0, 1.0, 0, 0)
    sm = src_op[::4, ::4]
    for s in (0.96, 0.98, 1.0, 1.02, 1.04):
        e = warp(edit_nf.astype(np.float32), s, 0, 0, ax, ay, order=0)[::4, ::4] > 0.5
        for dy in range(-R // 4, R // 4 + 1):
            for dx in range(-R // 4, R // 4 + 1):
                v = iou(sm, np.roll(np.roll(e, dy, 0), dx, 1))
                if v > best[0]: best = (v, s, dx * 4, dy * 4)
    _, s0, dx0, dy0 = best; best = (-1.0, s0, dx0, dy0)
    for s in (s0 - 0.01, s0, s0 + 0.01):
        e = warp(edit_nf.astype(np.float32), s, 0, 0, ax, ay, order=0) > 0.5
        for dy in range(dy0 - 4, dy0 + 5):
            for dx in range(dx0 - 4, dx0 + 5):
                v = iou(src_op, np.roll(np.roll(e, dy, 0), dx, 1))
                if v > best[0]: best = (v, s, dx, dy)
    return best


def compose(atlas, boxes, cells, out, key, hue, sat, gate, keep_going):
    A = np.asarray(Image.open(atlas).convert("RGBA")).copy()
    rep, ok_all = {}, True
    for i in cells:
        g = json.load(open(f"{out}/src_{i}.json")); x, y, w, h = g["box"]; W, H = g["canvas"]; ox, oy = g["off"]
        e = np.asarray(Image.open(f"{out}/edit_{i}.png").convert("RGB").resize((W, H), Image.LANCZOS)).astype(np.float32)
        erg, ea = key_soft(e, key)
        erg, ea = erg[oy:oy + h, ox:ox + w], ea[oy:oy + h, ox:ox + w]
        src = A[y:y + h, x:x + w].astype(np.float32); s_op = src[..., 3] > CUT
        fl = flower_mask(erg, ea, hue, sat)
        nf = (ea * 255 > CUT) & ~ndi.binary_dilation(fl, iterations=1)
        ax, ay = w / 2.0, h - 1.0  # the attach point (cell bottom centre)
        v0, s, dx, dy = register(s_op, nf, ax, ay)
        def reg(arr, order=1):
            return np.roll(np.roll(warp(arr, s, 0, 0, ax, ay, order), dy, 0), dx, 1)
        ea_r = np.clip(reg(ea), 0, 1); erg_r = reg(erg); fl_r = reg(fl.astype(np.float32), 0) > 0.5
        near = ndi.binary_dilation(fl_r, iterations=2)
        a_new = np.maximum(src[..., 3], np.where(near, ea_r * 255, 0))
        rgb = np.where(fl_r[..., None], erg_r, src[..., :3])
        # flower soft edges take the nearest flower colour; then every non-core texel nearer a flower core than a source
        # core takes that flower core's colour (no halo at any mip); every other texel keeps the source pixel
        edge = near & ~fl_r & (src[..., 3] <= CUT)
        if edge.any() and fl_r.any():
            idx = ndi.distance_transform_edt(~fl_r, return_distances=False, return_indices=True)
            rgb[edge] = erg_r[idx[0][edge], idx[1][edge]]
        core = a_new >= 250; fcore = core & fl_r
        if fcore.any():
            d_f, idx = ndi.distance_transform_edt(~fcore, return_indices=True)
            d_s = ndi.distance_transform_edt(~(core & ~fl_r)) if (core & ~fl_r).any() else np.full(core.shape, np.inf)
            nc = ~core & (d_f < d_s)
            rgb[nc] = rgb[idx[0][nc], idx[1][nc]]
        new_op = a_new > CUT; fl_new = fl_r & ~s_op
        dist = ndi.distance_transform_edt(~s_op)
        flt = float((fl_new & (dist > 6)).sum() / max(fl_new.sum(), 1))
        e_nf = reg(nf.astype(np.float32), 0) > 0.5; v = iou_tol(s_op, e_nf)
        ok = v >= gate; ok_all &= ok
        rep[i] = dict(iou_t2=round(v, 4), iou=round(v0, 4), scale=round(s, 3), shift=[int(dx), int(dy)],
                      opaque_before=round(float(s_op.mean()), 4), opaque_after=round(float(new_op.mean()), 4),
                      flower_share=round(float(fl_r.mean()), 4), floating_flowers=round(flt, 4),
                      status="PASS" if ok else "FAIL")
        print("BLOOMCELL", i, rep[i]["status"], " ".join(f"{k} {vv}" for k, vv in rep[i].items() if k != "status"),
              "WARN floating flowers" if flt > 0.05 else "")
        if ok or keep_going:
            A[y:y + h, x:x + w, :3] = np.clip(rgb + 0.5, 0, 255).astype(np.uint8)
            A[y:y + h, x:x + w, 3] = np.clip(a_new + 0.5, 0, 255).astype(np.uint8)
    stem = os.path.splitext(os.path.basename(atlas))[0]
    dst = f"{out}/{stem[:-5] if stem.endswith('_RGBA') else stem}_Bloom_RGBA.png"
    json.dump(dict(atlas=atlas, out=dst, key=key, flower_hue=list(hue), gate=gate, cells=rep),
              open(f"{out}/bloom_report.json", "w"), indent=1)
    if not ok_all and not keep_going:
        print("BLOOM", "not written: a cell failed the registration gate", f"{out}/bloom_report.json"); sys.exit(1)
    Image.fromarray(A).save(dst)
    print("BLOOM", dst, "cells", len(cells), "pass", sum(r["status"] == "PASS" for r in rep.values()))


def main():
    mode, atlas, cards = sys.argv[1], os.path.abspath(sys.argv[2]), sys.argv[3]
    out = os.path.abspath(opt("--out")); os.makedirs(out, exist_ok=True)
    W, H = Image.open(atlas).size; boxes = cell_boxes(cards, W, H)
    cells = [int(c) for c in opt("--cells", ",".join(map(str, range(len(boxes))))).split(",")]
    key = opt("--key", "magenta")
    if mode in ("prep", "all"):
        prep(atlas, boxes, cells, out, key)
    if mode in ("edit", "all"):
        edit(cells, out, os.path.abspath(opt("--prompt-file")), opt("--backend"), opt("--quality", "high"))
    if mode in ("compose", "all"):
        hue = tuple(float(v) for v in opt("--flower-hue").split(","))
        compose(atlas, boxes, cells, out, key, hue, float(opt("--flower-sat", "0.35")), float(opt("--iou", "0.9")),
                "--keep-going" in sys.argv)


if __name__ == "__main__":
    main()
