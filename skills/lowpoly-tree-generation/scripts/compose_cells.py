"""Sparse "variety" cells (shoot / sprig) composed from several small REAL branchlets cut out of a family's own sprays,
at the kept cells' leaf pixel size (card scale 1), never one branch drawn bigger and shrunk by Cards.json `scale`. No
drawn stems: every texel comes from a spray. Cells: the column_4cells layout (a, b, c, d = layouts/column_4cells.json).
    python compose_cells.py survey <sheet> <out_dir> [--cells abcd] [--needle]
    python compose_cells.py compose <Leaves_RGBA.png> <spec.json> [--cards <Leaves_Cards.json>] [--preview <png>]
Back up the texture folder first; compose rewrites <Leaves_RGBA.png> (and --cards) in place. Then trim_stubs.py on the
composed cells, rebuild the atlas (tree_atlas.py), check_key_spill.py, approval, and a tree REBUILD (not a UV-only swap).
Branch topology: the sheet cell's opaque texels (alpha > 100) are a tree rooted at the stem's bottom texel. Cutting a
twig at point c (a disk of radius r erased) disconnects the subtree beyond c: that subtree is a branchlet, exactly as
drawn, with its own twig down to c. Leaves = foliage components (G > R + 4, alpha > 128, >= 150 px) with >= 60 % of
their texels in the subtree (an olive leaf, a pine needle tuft).
survey: every thin twig texel on a 6 px grid is tried as a cut; the subtrees with 3-20 leaves and 120-450 px extent go to
<out_dir>/candidates.json ({cell: [{cut, r, leaves, ext, n, bbox, cen}]}) and <out_dir>/candidates_<cell>.png (each
subtree tinted on the cell, numbered, cut point marked).
compose (run from the folder the spec paths are relative to). Spec:
  "src": the sheet the pieces are cut from; "measure": "olive_leaf" (leaf length = median PCA major axis of single
  leaves, major/minor >= 2.2, 150-4000 px) or null; "ref_cells": the kept cells the leaf length is matched to
  (measured on src; paste those kept cells back from the same sheet afterwards, pixel-identical);
  "cells": {"a": {"base": {"cell": "c", "keep_d": <geodesic px from the root>} (the source's own trunk and limb
  starts: twig texels, no leaves, within keep_d of the root; sits at the cell's attach point, drawn over the pieces so
  the pieces' cut ends emerge from its limb ends; optional "leaf_mask": "wide" excludes only wide leaf bodies, for
  green-tinted stems that foliage() would cut apart, "none" excludes nothing, for a keep_d short enough to hold no leaf),
  "pieces": [{"cell", "cut": [x, y] (sheet px), "r", "at": [x, y] (cell px, top-left origin), "ang" (deg, 0 = up,
  + = right: direction from the cut to the branchlet's centroid), "mir": bool}]}}.
  Each source cell's pieces are scaled by ref leaf length / that cell's pooled piece leaf length ("measure"), so
  every leaf lands at the kept cells' size. The cell box is cleared and recomposed (premultiplied alpha over).
  With --cards the composed cells' Cards.json entries lose fit_k/src_crop_px/stem_offset_px_before and get
  "composed" = spec path. Prints PIECES, SCALE, and per cell OPAQUE (alpha > 0.45 share, and as a share of the
  ref cells') and LEAFPX (olive_leaf).
  "mode": "needle" (pines; survey --needle): overlapping needle tufts make one opaque blob, so pieces are cut by
  NeedleCell (tuft centres, needle ownership, cheapest root paths through the bark; see its docstring); "leaves" =
  tufts; the base is the cell's own bark (gaps closed) within keep_d of the root.
"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from skimage.graph import MCP_Geometric

CELLS = [(0, 8, 768, 1024), (768, 8, 1536, 1024), (0, 1024, 768, 2040), (768, 1024, 1536, 2040)]  # column_4cells a..d
opt = lambda k: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else None
box = lambda c: CELLS["abcd".index(c)]


def foliage(a):
    a = a.astype(np.int16); return (a[..., 3] > 128) & (a[..., 1] > a[..., 0] + 4)


class Cell:
    """One source cell: opaque mask, root, geodesic distance, foliage components."""
    def __init__(self, sheet, cell):
        x0, y0, x1, y1 = box(cell)
        self.a = sheet[y0:y1, x0:x1]; self.x0, self.y0 = x0, y0
        self.M = self.a[..., 3] > 100
        self.root = (self.M.shape[0] - 1, int(np.nonzero(self.M[-1])[0].mean()))
        self.D = MCP_Geometric(np.where(self.M, 1.0, np.inf)).find_costs([self.root])[0]
        self.LL = ndi.label(foliage(self.a))[0]; self.LA = np.bincount(self.LL.ravel())
        self.yy, self.xx = np.ogrid[:self.M.shape[0], :self.M.shape[1]]

    def subtree(self, c, r):
        """sheet px cut point -> mask (cell px) of the part beyond it"""
        cx, cy = c[0] - self.x0, c[1] - self.y0
        disk = (self.yy - cy) ** 2 + (self.xx - cx) ** 2 <= r * r
        lab = ndi.label(self.M & ~disk, np.ones((3, 3)))[0]
        ring = ndi.binary_dilation(disk, iterations=2) & ~disk
        ids = np.unique(lab[ring]); ids = ids[(ids > 0) & (ids != lab[self.root])]
        return np.isin(lab, ids)

    def leaves(self, sub):
        ids, cnt = np.unique(self.LL[sub & (self.LL > 0)], return_counts=True)
        return int(sum(1 for i, n in zip(ids, cnt) if self.LA[i] >= 150 and n >= 0.6 * self.LA[i]))

    def texels(self, mask):
        """RGBA of the masked texels plus their 1 px antialiased rim"""
        m = ndi.binary_dilation(mask, iterations=1) & (self.a[..., 3] > 0)
        out = self.a.copy(); out[..., 3] = np.where(m, out[..., 3], 0); return out


def _orient(g, sig=1.5, rho=2.5):
    """structure-tensor line direction (rad, image x/y) of every texel"""
    gx = ndi.gaussian_filter(g, sig, order=(0, 1)); gy = ndi.gaussian_filter(g, sig, order=(1, 0))
    jxx, jyy, jxy = (ndi.gaussian_filter(v, rho) for v in (gx * gx, gy * gy, gx * gy))
    return 0.5 * np.arctan2(2 * jxy, jxx - jyy) + np.pi / 2


class NeedleCell(Cell):
    """Pine cell ("mode": "needle"): needle tufts overlap, so the opaque mask is one blob and Cell.subtree leaks.
    Tuft centres = peaks of a Hough vote (every needle texel votes along its own direction, both ways, 4-70 px); each
    foliage texel is owned by the best tuft (inside Rin of its centre, else radially aligned within Rmax). Every tuft
    is reached from the root by the cheapest path (bark texels R > G + 12 cost 1, other opaque texels 6), so the
    paths form the spray's real twig tree. A cut at c takes the tufts whose path passes within r of c, their owned
    needles, the bark tube along their paths beyond c, and the small holes that leaves in a tuft."""
    def __init__(self, sheet, cell, L=70, Rin=26, Rmax=78, cosmin=0.85):
        super().__init__(sheet, cell)
        a = self.a.astype(np.int16); H, W = self.M.shape; yy, xx = np.mgrid[0:H, 0:W]
        op = a[..., 3] > 10; self.op = op
        self.bark = (a[..., 3] > 100) & (a[..., 0] > a[..., 1] + 12); self.fol = op & ~self.bark
        th = _orient(a[..., 3] / 255.0 * self.fol)
        ys, xs = np.nonzero(self.fol & (a[..., 3] > 80)); ys, xs = ys[::2], xs[::2]; t = th[ys, xs]; acc = np.zeros((H, W))
        for r in range(4, L, 2):
            for s in (1, -1):
                px = np.round(xs + s * r * np.cos(t)).astype(int); py = np.round(ys + s * r * np.sin(t)).astype(int)
                ok = (px >= 0) & (py >= 0) & (px < W) & (py < H); np.add.at(acc, (py[ok], px[ok]), 1)
        acc = ndi.gaussian_filter(acc, 3)
        py, px = np.nonzero((acc == ndi.maximum_filter(acc, size=41)) & (acc > acc.max() * 0.15))
        self.P = np.stack([px, py], 1); self.Rin = Rin
        own, best = np.full((H, W), -1), np.full((H, W), -1.0)
        for i, (cx, cy) in enumerate(self.P):
            vx, vy = xx - cx, yy - cy; r = np.hypot(vx, vy) + 1e-9
            al = np.abs(np.cos(th) * vx / r + np.sin(th) * vy / r)
            sc = np.where(r <= Rin, 2.0 - r / Rin, np.where((r <= Rmax) & (al >= cosmin), al - r / 400, -1))
            m = self.fol & (sc > best); own[m] = i; best[m] = sc[m]
        self.own = own
        cost = np.where(self.bark, 1.0, np.where(op, 6.0, np.inf))
        mcp = MCP_Geometric(cost); cc = mcp.find_costs([self.root])[0]; self.cost = cc
        ind = ndi.distance_transform_edt(~np.isfinite(cc), return_indices=True)[1]
        self.paths = [np.array(mcp.traceback((int(ind[0][y, x]), int(ind[1][y, x])))) for x, y in self.P]
        self.dtb = ndi.distance_transform_edt(self.bark)

    def tufts_at(self, c, r):
        """tufts whose root path passes within r of c, minus a tuft sitting on c itself (a sibling at the fork)"""
        cx, cy = c[0] - self.x0, c[1] - self.y0
        return [i for i, p in enumerate(self.paths) if ((p[:, 1] - cx) ** 2 + (p[:, 0] - cy) ** 2 <= r * r).any()
                and math.hypot(self.P[i][0] - cx, self.P[i][1] - cy) > 1.2 * self.Rin]

    def subtree(self, c, r):
        cx, cy = c[0] - self.x0, c[1] - self.y0; T = self.tufts_at(c, r); H, W = self.M.shape
        tube = np.zeros((H, W), bool)
        for i in T:
            p = self.paths[i]; d = (p[:, 1] - cx) ** 2 + (p[:, 0] - cy) ** 2
            seg = p[int(np.nonzero(d <= r * r)[0].max()):]; tube[seg[:, 0], seg[:, 1]] = True
        if not T:
            self.tcore = tube
            return tube
        rr = max(2.0, float(np.median(self.dtb[tube & self.bark])) if (tube & self.bark).any() else 2.0)
        tubed = ndi.binary_dilation(tube, iterations=int(round(rr + 1))) & self.op
        owned = np.isin(self.own, T); others = (self.own >= 0) & ~owned
        core = np.zeros((H, W), bool)
        for i in T:
            core |= (self.yy - self.P[i][1]) ** 2 + (self.xx - self.P[i][0]) ** 2 <= (0.6 * self.Rin) ** 2
        m = owned | (tubed & self.bark) | (tubed & ~others) | (core & self.op & ~others)
        m = ndi.binary_dilation(m, iterations=1) & self.op & ~(others & ~tubed)
        tcore = ndi.binary_dilation(tube, iterations=max(1, int(rr))) & self.op
        m |= tcore  # the twig itself, also where needles cross it
        m = ndi.binary_closing(m, iterations=2) & self.op
        near = (self.yy - cy) ** 2 + (self.xx - cx) ** 2 <= (1.5 * self.Rin) ** 2
        m &= ~(near & self.fol & ~owned & ~tcore)  # other tufts' needles around the cut
        holes = ndi.binary_fill_holes(m) & ~m; hl, nh = ndi.label(holes)
        if nh:
            hs = ndi.sum(holes, hl, range(1, nh + 1)); m |= np.isin(hl, 1 + np.nonzero(hs <= 600)[0]) & self.op
        lab = ndi.label(m, np.ones((3, 3)))[0]  # keep what hangs on the twig; drop detached needle fragments
        ids = np.unique(lab[tcore & m]); m = np.isin(lab, ids[ids > 0])
        disk = (self.yy - cy) ** 2 + (self.xx - cx) ** 2 <= r * r
        self.tcore = tcore  # the twig itself (twig_bark)
        return (m & ~disk) | (tcore & disk)  # the twig runs right up to the cut point, so it meets the base's limb end

    def twig_bark(self, img, sub, c, fl):
        """opt-in spec "feather": the cut piece's own twig near the join (tcore of the last subtree, within geodesic
        fl["join"] px of the cut point c along it, 2 px wide margin) takes the nearest bark texel's colour where it is
        not bark-coloured (R - G < fl["bark_rg"]: olive needle remnants along the twig), and the non-bark wisps beside
        it (alpha <= 160, within 3 px) clear. Tufts never sit on that stretch (cuts are on bare twig)."""
        cx, cy = c[0] - self.x0, c[1] - self.y0
        tube = ndi.binary_dilation(self.tcore & sub, iterations=2) & sub
        seed = (int(min(max(cy, 0), tube.shape[0] - 1)), int(min(max(cx, 0), tube.shape[1] - 1)))
        if not tube[seed]:
            ys, xs = np.nonzero(tube); k = int(np.argmin((ys - cy) ** 2 + (xs - cx) ** 2)); seed = (int(ys[k]), int(xs[k]))
        gd = MCP_Geometric(np.where(tube, 1.0, np.inf)).find_costs([seed])[0]
        near = tube & (gd <= fl.get("join", 40))
        a = img.astype(np.int16); nonbark = (a[..., 3] > 10) & (a[..., 0] - a[..., 1] < fl.get("bark_rg", 25))
        thick = near & nonbark & (a[..., 3] > 160)
        iy, ix = ndi.distance_transform_edt(~(self.bark & sub), return_indices=True)[1]
        out = img.copy(); out[thick, :3] = self.a[iy[thick], ix[thick], :3]
        wisp = ndi.binary_dilation(near, iterations=3) & nonbark & (a[..., 3] <= 160)
        out[wisp, 3] = 0
        self.twigfix = (int(thick.sum()), int(wisp.sum()))
        return out

    def leaves(self, sub):
        return len({int(i) for i in np.unique(self.own[sub & (self.own >= 0)])
                    if sub[max(self.P[i][1] - 3, 0):self.P[i][1] + 4, max(self.P[i][0] - 3, 0):self.P[i][0] + 4].any()})

    def texels(self, mask):
        out = self.a.copy(); out[..., 3] = np.where(mask, out[..., 3], 0); return out

    def base(self, keep_d):
        """the cell's own trunk: bark (gaps closed) within geodesic keep_d of the root"""
        b = (ndi.binary_closing(self.bark, np.ones((3, 3)), iterations=4) & self.op) | self.bark
        lab = ndi.label(b, np.ones((3, 3)))[0]; b = lab == lab[self.root]
        d = MCP_Geometric(np.where(b, 1.0, np.inf)).find_costs([self.root])[0]
        return b & (d <= keep_d)


def needle_survey(C):
    """every tuft path sampled each 6 px: the shallowest cut per distinct tuft group of 1-6 tufts"""
    best = {}
    for p in C.paths:
        for y, x in p[::6]:
            r = max(3.0, float(C.dtb[y, x]) + 1.5); c = (int(x + C.x0), int(y + C.y0)); T = tuple(C.tufts_at(c, r))
            if 1 <= len(T) <= 6 and (T not in best or C.cost[y, x] < best[T][1]):
                best[T] = ((c, r), C.cost[y, x])
    found = []
    for T, ((c, r), _) in sorted(best.items(), key=lambda kv: (len(kv[0]), kv[0])):
        sub = C.subtree(c, r); sy, sx = np.nonzero(sub)
        if not len(sy):
            continue
        found.append(dict(cut=list(c), r=round(r, 2), leaves=len(T), tufts=list(T), ext=int(max(np.ptp(sy), np.ptp(sx))),
                          n=int(sub.sum()), bbox=[int(sx.min()), int(sy.min()), int(sx.max()), int(sy.max())],
                          cen=[round(float(sx.mean()), 1), round(float(sy.mean()), 1)]))
    return found


def leaf_len(a):
    lab = ndi.label(foliage(a))[0]; L = []
    for i, sl in enumerate(ndi.find_objects(lab), 1):
        ys, xs = np.nonzero(lab[sl] == i)
        if not 150 <= len(ys) <= 4000:
            continue
        X = np.stack([xs, ys], 1).astype(float); X -= X.mean(0)
        v = np.linalg.eigh(np.cov(X.T))[1]; p, q = X @ v[:, -1], X @ v[:, 0]
        if (p.max() - p.min()) / max(q.max() - q.min(), 1) >= 2.2:
            L.append(p.max() - p.min())
    return L


def survey(sheet_path, out):
    os.makedirs(out, exist_ok=True)
    sheet = np.asarray(Image.open(sheet_path).convert("RGBA")); res = {}
    for cell in opt("--cells") or "abcd":
        if "--needle" in sys.argv:
            C = NeedleCell(sheet, cell); found = needle_survey(C)
            res[cell] = found
        else:
            C = Cell(sheet, cell); found = []
            dt = ndi.distance_transform_edt(C.M); twig = C.M & ~foliage(C.a) & (dt >= 1) & (dt <= 4.5) & np.isfinite(C.D)
            ys, xs = np.nonzero(twig); k = (ys % 6 == 0) & (xs % 6 == 0)
            for y, x in zip(ys[k], xs[k]):
                r = float(dt[y, x] + 1.5); sub = C.subtree((x + C.x0, y + C.y0), r)
                if sub.sum() < 800:
                    continue
                sy, sx = np.nonzero(sub); ext = int(max(np.ptp(sy), np.ptp(sx))); nl = C.leaves(sub)
                if 3 <= nl <= 20 and 120 <= ext <= 450:
                    found.append(dict(cut=[int(x + C.x0), int(y + C.y0)], r=round(r, 2), leaves=nl, ext=ext, n=int(sub.sum()),
                                      bbox=[int(sx.min()), int(sy.min()), int(sx.max()), int(sy.max())],
                                      cen=[round(float(sx.mean()), 1), round(float(sy.mean()), 1)], D=round(float(C.D[y, x]))))
            res[cell] = found
        vis = Image.new("RGBA", C.M.shape[::-1], (255, 255, 255, 255))
        vis.alpha_composite(Image.fromarray(C.a, "RGBA")); vis = vis.convert("RGB"); va = np.asarray(vis).copy()
        rng = np.random.default_rng(1)
        for f in found:
            sub = C.subtree(f["cut"], f["r"]); col = rng.integers(40, 255, 3)
            va[sub] = (va[sub] * 0.5 + col * 0.5).astype(np.uint8)
        vis = Image.fromarray(va); d = ImageDraw.Draw(vis)
        for i, f in enumerate(found):
            x, y = f["cut"][0] - C.x0, f["cut"][1] - C.y0
            d.ellipse([x - 3, y - 3, x + 3, y + 3], outline=(255, 0, 0)); d.text((x + 4, y - 6), str(i), fill=(0, 0, 0))
        vis.save(f"{out}/candidates_{cell}.png")
        print("SURVEY", cell, "candidates", len(found))
    json.dump(res, open(f"{out}/candidates.json", "w"), indent=1)


def place(cv, img, cut, ang, at, sc, mirror):
    """paste img (RGBA, cell-local) rotated/scaled about its cut point so the cut lands at `at` and the cut->centroid
    direction points to `ang`"""
    im = img.astype(float) / 255.0; hs, ws = im.shape[:2]; bx, by = cut
    ys, xs = np.nonzero(im[..., 3] > 0.5); cen = np.array([xs.mean(), ys.mean()])
    if mirror:
        im = im[:, ::-1]; bx = ws - 1 - bx; cen[0] = ws - 1 - cen[0]
    v = cen - [bx, by]; nat = math.degrees(math.atan2(v[0], -v[1]))
    pm = np.concatenate([im[..., :3] * im[..., 3:], im[..., 3:]], -1)
    r = math.radians(ang - nat); R = np.array([[math.cos(r), -math.sin(r)], [math.sin(r), math.cos(r)]])
    ys, xs = np.nonzero(im[..., 3] > 0)
    oc = ((np.stack([xs, ys], 1) - [bx, by]) @ R.T) * sc + at
    X0, Y0 = np.maximum(np.floor(oc.min(0)).astype(int) - 2, 0); X1, Y1 = np.ceil(oc.max(0)).astype(int) + 3
    X1, Y1 = min(X1, cv.shape[1]), min(Y1, cv.shape[0])
    gy, gx = np.mgrid[Y0:Y1, X0:X1]
    q = ((np.stack([gx.ravel() + 0.5, gy.ravel() + 0.5], 1) - at) / sc) @ R + [bx, by] - 0.5
    ix, iy = np.floor(q[:, 0]).astype(int), np.floor(q[:, 1]).astype(int); fx, fy = q[:, 0] - ix, q[:, 1] - iy

    def g(yy, xx):
        ok = (xx >= 0) & (xx < ws) & (yy >= 0) & (yy < hs); o = np.zeros((len(xx), 4)); o[ok] = pm[yy[ok], xx[ok]]
        return o
    smp = (g(iy, ix) * ((1 - fx) * (1 - fy))[:, None] + g(iy, ix + 1) * (fx * (1 - fy))[:, None]
           + g(iy + 1, ix) * ((1 - fx) * fy)[:, None] + g(iy + 1, ix + 1) * (fx * fy)[:, None])
    yy, xx = gy.ravel(), gx.ravel(); cv[yy, xx] = smp + cv[yy, xx] * (1 - smp[:, 3:])
    return int((smp[:, 3] > 0.45).sum())


def feather(blk, basem, pieces, fl):
    """opt-in spec "feather" (needle cells, review C1-med-spray3 nit 6): blend each piece's join into the base limb end.
    blk: the composed cell (H, W, 4 uint8, edited in place); basem: the base's mask in cell px. Per piece: the base limb
    end E = the base texel nearest the piece's `at`; a tapered bark bridge runs from the limb end's centre (radius 0.9 x
    the limb radius there) to `at` + `reach` px along the piece twig (its own radius), coloured from the nearest base bark
    texels, so the square-cut limb end flows into the twig; green twig texels and green wisps within `clean` px of the
    join (outside the tufts: farther than `tuft` px from any needle-tuft centre) take the nearest bark colour or clear.
    fl = {"reach": 6, "clean": 16, "tuft": 22}. Prints FEATHER per piece."""
    a = blk.astype(np.int16); H, W = a.shape[:2]; yy, xx = np.mgrid[0:H, 0:W]
    op = a[..., 3] > 100; bark = op & (a[..., 0] > a[..., 1] + 12)
    dtb = ndi.distance_transform_edt(basem)
    ny, nx = ndi.distance_transform_edt(~basem, return_indices=True)[1]
    by, bx = ndi.distance_transform_edt(~(bark & basem), return_indices=True)[1]
    allb = ndi.distance_transform_edt(~bark, return_indices=True)[1]
    tc = feather_tufts(blk, fl.get("tuft_px", 14))
    reach, clean, tuft = fl.get("reach", 6), fl.get("clean", 16), fl.get("tuft", 22)
    far_tuft = np.ones((H, W), bool)
    for cx, cy in tc: far_tuft &= (xx - cx) ** 2 + (yy - cy) ** 2 > tuft * tuft
    for p in pieces:
        ax, ay = p["at"]; iy, ix = int(round(min(max(ay, 0), H - 1))), int(round(min(max(ax, 0), W - 1)))
        ey, ex = ny[iy, ix], nx[iy, ix]
        rb = max(1.5, float(dtb[max(ey - 8, 0):ey + 9, max(ex - 8, 0):ex + 9].max()))
        m = basem & ((yy - ey) ** 2 + (xx - ex) ** 2 <= (2 * rb) ** 2)
        P0 = np.array([xx[m].mean(), yy[m].mean()])
        ring = op & ~basem & ((yy - ay) ** 2 + (xx - ax) ** 2 <= 16 ** 2) & ((yy - ay) ** 2 + (xx - ax) ** 2 >= 5 ** 2)
        if ring.any():
            v = np.array([xx[ring].mean() - ax, yy[ring].mean() - ay])
        else:
            t = math.radians(p["ang"]); v = np.array([math.sin(t), -math.cos(t)])
        v = v / max(np.linalg.norm(v), 1e-6); P1 = np.array([ax, ay]) + v * reach
        twig = op & ~basem & ((yy - P1[1]) ** 2 + (xx - P1[0]) ** 2 <= 6 ** 2)
        r1 = max(1.2, min(rb * 0.8, float(ndi.distance_transform_edt(op)[twig].max()) if twig.any() else 1.5))
        r0 = max(r1, 0.9 * rb)
        seg = P1 - P0; L2 = max(float(seg @ seg), 1e-6)
        t = np.clip(((xx - P0[0]) * seg[0] + (yy - P0[1]) * seg[1]) / L2, 0, 1)
        dist = np.hypot(xx - (P0[0] + t * seg[0]), yy - (P0[1] + t * seg[1]))
        rad = r0 + (r1 - r0) * t ** 0.7
        cov = np.clip(rad - dist + 0.5, 0, 1)
        k = cov > 0
        mb = basem & bark & ((yy - ey) ** 2 + (xx - ex) ** 2 <= (3 * rb) ** 2)  # the limb end's median bark tone
        med = np.median(a[mb, :3], 0) if mb.any() else a[by[k], bx[k], :3].mean(0)
        col = 0.5 * a[by[k], bx[k], :3] + 0.5 * med  # texture from the nearest base bark texel, tone from the limb end
        al = np.maximum(a[k, 3], np.round(cov[k] * 255)).astype(np.int16)
        w = cov[k][:, None]
        a[k, :3] = np.round(col * w + a[k, :3] * (1 - w)).astype(np.int16); a[k, 3] = al
        # green twig texels and wisps near the join, outside the tufts
        near = ((yy - ay) ** 2 + (xx - ax) ** 2 <= clean * clean) & far_tuft & ~basem
        green = near & (a[..., 3] > 10) & (a[..., 0] - a[..., 1] < fl.get("bark_rg", 25))
        thick = green & (a[..., 3] > 160)
        ty, tx = allb[0][thick], allb[1][thick]
        a[thick, :3] = a[ty, tx, :3]
        a[green & ~thick, 3] = 0
        print(f"FEATHER at {ax},{ay} end {ex},{ey} rb {rb:.1f} r1 {r1:.1f} bridge {int(k.sum())} px green "
              f"recoloured {int(thick.sum())} cleared {int((green & ~thick).sum())}")
    blk[...] = a.clip(0, 255).astype(np.uint8)


def feather_tufts(blk, rmin):
    """needle-tuft centres of a composed pine cell: solid foliage cores (opening radius rmin/3) of >= rmin^2 px"""
    a = blk.astype(np.int16); fol = (a[..., 3] > 100) & (a[..., 1] > a[..., 0] + 4)
    core = ndi.binary_opening(fol, iterations=max(1, rmin // 3))
    lab, n = ndi.label(core)
    if not n: return []
    sz = ndi.sum(core, lab, range(1, n + 1)); cen = ndi.center_of_mass(core, lab, range(1, n + 1))
    return [(c[1], c[0]) for c, s in zip(cen, sz) if s >= rmin * rmin]


def drop_detached(blk, min_px):
    """opt-in spec "drop_detached_px" (review C1-med-spray3 nit 8): clear every opaque component (alpha > 100,
    8-connected) that does not hold the cell's stem bottom and is smaller than min_px, with its soft rim"""
    m = blk[..., 3] > 100; lab, n = ndi.label(m, np.ones((3, 3)))
    bot = np.nonzero(m[-1])[0]; keep = set(lab[-1, bot].tolist()) - {0}
    sz = ndi.sum(m, lab, range(1, n + 1)); gone = [i for i in range(1, n + 1) if i not in keep and sz[i - 1] < min_px]
    if gone:
        g = np.isin(lab, gone); rim = ndi.binary_dilation(g, iterations=2) & (blk[..., 3] <= 100) & ~ndi.binary_dilation(m & ~g, iterations=1)
        blk[g | rim, 3] = 0
    print("DETACHED cleared", len(gone), "components", [int(sz[i - 1]) for i in gone])


def compose(leaves, spec_path):
    spec = json.load(open(spec_path))
    src = np.asarray(Image.open(spec["src"]).convert("RGBA"))
    out = np.asarray(Image.open(leaves).convert("RGBA")).copy()
    cells = {}
    needle = spec.get("mode") == "needle"
    get = lambda c: cells[c] if c in cells else cells.setdefault(c, (NeedleCell if needle else Cell)(src, c))
    olive = spec.get("measure") == "olive_leaf"
    ref_cells = spec.get("ref_cells", "")
    ref_op = np.mean([(src[box(c)[1]:box(c)[3], box(c)[0]:box(c)[2], 3] / 255 > 0.45).mean() for c in ref_cells]) if ref_cells else None
    pieces = {}  # (cell, cut) -> (img, cut local)
    for cs in spec["cells"].values():
        for p in cs["pieces"]:
            C = get(p["cell"]); sub = C.subtree(p["cut"], p["r"])
            ys, xs = np.nonzero(sub); x0, y0, x1, y1 = xs.min() - 2, ys.min() - 2, xs.max() + 3, ys.max() + 3
            x0, y0 = max(x0, 0), max(y0, 0)
            img = C.texels(sub)
            if needle and spec.get("feather"):
                img = C.twig_bark(img, sub, p["cut"], spec["feather"]); print("TWIGBARK", p["cell"], p["cut"], "recoloured/cleared", C.twigfix)
            img = img[y0:y1, x0:x1]
            pieces[(p["cell"], tuple(p["cut"]))] = (img, (p["cut"][0] - C.x0 - x0, p["cut"][1] - C.y0 - y0), C.leaves(sub))
    scale = {}
    if olive:
        tgt = float(np.median([x for c in ref_cells for x in leaf_len(src[box(c)[1]:box(c)[3], box(c)[0]:box(c)[2]])]))
        for c in sorted({k[0] for k in pieces}):
            L = [x for k, v in pieces.items() if k[0] == c for x in leaf_len(v[0])]
            scale[c] = tgt / float(np.median(L))
            print("SCALE src cell", c, "piece leaf_px", round(float(np.median(L)), 1), "n", len(L), "ref", ref_cells,
                  round(tgt, 1), "scale", round(scale[c], 4))
    cards = json.load(open(opt("--cards"))) if opt("--cards") else None
    for cell, cs in spec["cells"].items():
        x0, y0, x1, y1 = box(cell); W, H = x1 - x0, y1 - y0
        cv = np.zeros((H, W, 4)); n_leaves = 0
        for p in cs["pieces"]:
            img, cut, nl = pieces[(p["cell"], tuple(p["cut"]))]; n_leaves += nl
            place(cv, img, cut, p["ang"], np.array(p["at"], float), scale.get(p["cell"], 1.0), p.get("mir", False))
        b = cs["base"]; C = get(b["cell"])
        if needle:
            bm = C.base(b["keep_d"])
        else:
            lf = foliage(C.a)
            if b.get("leaf_mask") == "wide":  # green-tinted stems: exclude only leaf bodies, thin stems/petioles survive
                lf = ndi.binary_dilation(ndi.binary_opening(lf, iterations=3), iterations=2) & lf
            elif b.get("leaf_mask") == "none":  # no foliage exclusion: a small keep_d that holds only the stem
                lf = np.zeros_like(lf)
            bm = C.M & ~lf & (C.D <= b["keep_d"])
            lab = ndi.label(bm, np.ones((3, 3)))[0]
            if lab[C.root] == 0 and lab.any():  # green-tinted stem bottom (G > R + 4) drops the root texel itself
                iy, ix = ndi.distance_transform_edt(lab == 0, return_indices=True)[1]
                k = lab[iy[C.root], ix[C.root]]
            else:
                k = lab[C.root]
            bm = (lab == k) & (k > 0)
        bimg = C.texels(bm).astype(float) / 255.0
        sh = W // 2 - C.root[1]  # the base's root onto the cell's attach point (bottom centre)
        bimg = np.roll(bimg, sh, axis=1)
        pm = np.concatenate([bimg[..., :3] * bimg[..., 3:], bimg[..., 3:]], -1)
        cv = pm + cv * (1 - pm[..., 3:])
        a = cv[..., 3:]; rgb = np.where(a > 1e-6, cv[..., :3] / np.maximum(a, 1e-6), 0)
        out[y0:y1, x0:x1] = np.round(np.concatenate([rgb, a], -1) * 255).clip(0, 255).astype(np.uint8)
        blk = out[y0:y1, x0:x1]
        if needle and spec.get("feather"):
            feather(blk, np.roll(bm, sh, axis=1), cs["pieces"], spec["feather"])
        for ex, ey, er in spec.get("erase", {}).get(cell, []):  # opt-in: flat needle-mass flecks cleared by hand (cell px),
            yy, xx = np.ogrid[:H, :W]; bk = blk.astype(np.int16)  # bark texels (R - G >= 25) stay so a twig is never cut
            blk[((yy - ey) ** 2 + (xx - ex) ** 2 <= er * er) & (bk[..., 0] - bk[..., 1] < 25), 3] = 0
            print("ERASE", cell, ex, ey, er)
        if spec.get("drop_detached_px"):
            drop_detached(blk, spec["drop_detached_px"])
        op = float((blk[..., 3] / 255 > 0.45).mean())
        msg = f"OPAQUE {cell} {op:.3f}" + (f" = {op / ref_op:.2f} x ref cells {ref_cells} ({ref_op:.3f})" if ref_op else "")
        msg += f" pieces {len(cs['pieces'])} leaves {n_leaves}"
        if olive:
            L = leaf_len(blk); msg += f" LEAFPX {np.median(L):.1f} n {len(L)}"
        bot = np.nonzero(blk[-1, :, 3] > 128)[0]
        print(msg, "stem bottom px", int(bot.min()), int(bot.max()), "attach x", W // 2)
        if cards is not None:
            c = cards["cells"]["abcd".index(cell)]
            for k in ("fit_k", "src_crop_px", "stem_offset_px_before"):
                c.pop(k, None)
            c["stem_offset_px_after"] = round(float(bot.mean() + 0.5 - W / 2), 2); c["composed"] = spec_path
    Image.fromarray(out, "RGBA").save(leaves)
    if cards is not None:
        json.dump(cards, open(opt("--cards"), "w"), indent=1)
    if opt("--preview"):
        bg = Image.new("RGBA", out.shape[1::-1], (235, 235, 235, 255)); bg.alpha_composite(Image.fromarray(out, "RGBA"))
        bg.convert("RGB").save(opt("--preview"))
    print("SAVED", leaves)


if __name__ == "__main__":
    {"survey": lambda: survey(sys.argv[2], sys.argv[3]), "compose": lambda: compose(sys.argv[2], sys.argv[3])}[sys.argv[1]]()
