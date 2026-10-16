"""Search and download Blendkit (formerly BlenderKit) assets without opening Blender.

    python blendkit.py search "wooden chair" [--type model] [--max-faces 20000] [--free] [--limit 10] [--json]
    python blendkit.py download <assetBaseId> [--out DIR] [--file-type gltf|blend|resolution_2K ...]
    python blendkit.py inspect <file.glb>      # real tris, materials, UV sets, texture sizes

Search is anonymous. Downloads of free assets are anonymous too; Full-plan assets need the
API key, read from BLENDKIT_API_KEY or from the Blender add-on's saved login
(~/blenderkit_data/config/preferences.json, written once you log in inside Blender).

Models download as GLB (`gltf` file type). HDRIs default to `resolution_2K`. Materials and
scenes only ship as .blend: pass --file-type blend and convert in Blender.
Every download writes blendkit.json next to the file (name, author, licence, page URL,
faces, dimensions) so the licence travels with the asset.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import struct
import sys
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

API = "https://www.blenderkit.com/api/v1"
UA = {"User-Agent": "awdk-blendkit/1"}
# Default download root: <ASSET_LIBRARY>/World/Blendkit (the asset-library from .omp/local/config.md),
# else ./Blendkit in the current directory.
DEFAULT_OUT = (Path(os.environ["ASSET_LIBRARY"]) / "World" / "Blendkit") if os.environ.get("ASSET_LIBRARY") else Path("Blendkit")
DEFAULT_FILE = {"model": "gltf", "hdr": "resolution_2K"}


def api_key() -> str:
    key = os.environ.get("BLENDKIT_API_KEY", "").strip()
    if key:
        return key
    home = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~")
    prefs = Path(home) / "blenderkit_data" / "config" / "preferences.json"
    if prefs.is_file():
        return str(json.loads(prefs.read_text(encoding="utf-8")).get("api_key", "")).strip()
    return ""


def get(url: str, key: str = "") -> dict:
    headers = dict(UA)
    if key:
        headers["Authorization"] = f"Bearer {key}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=60) as r:
        return json.load(r)


def search(query: str, asset_type: str, max_faces: int | None, free: bool, limit: int, key: str) -> list[dict]:
    q = f"{query} asset_type:{asset_type} order:_score"
    if max_faces:
        q += f" faceCount_lte:{max_faces}"
    if free:
        q += " is_free:true"
    url = f"{API}/search/?" + urllib.parse.urlencode({"query": q, "page_size": limit, "dict_parameters": 1})
    return get(url, key)["results"]


def summary(r: dict) -> dict:
    p = r.get("dictParameters", {})
    dims = [p.get(f"dimension{a}") for a in "XYZ"]
    return {
        "id": r["assetBaseId"],
        "name": r["name"],
        "author": " ".join(filter(None, [r.get("author", {}).get("firstName"), r.get("author", {}).get("lastName")])),
        "licence": r.get("license"),
        "free": r.get("isFree"),
        "faces": p.get("faceCount"),
        "dims_m": [round(d, 3) for d in dims] if all(d is not None for d in dims) else None,
        "tex_max": p.get("textureResolutionMax"),
        "style": p.get("modelStyle"),
        "files": sorted({f["fileType"] for f in r.get("files", []) if f["fileType"] != "thumbnail"}),
        "page": f"https://www.blendkit.com/asset-gallery-detail/{r['assetBaseId']}/",
        "thumbnail": r.get("thumbnailMiddleUrl") or r.get("thumbnailLargeUrl"),
    }


def cmd_search(a: argparse.Namespace) -> None:
    rows = [summary(r) for r in search(a.query, a.type, a.max_faces, a.free, a.limit, api_key())]
    if a.json:
        print(json.dumps(rows, indent=1))
        return
    for s in rows:
        dims = "x".join(f"{d:.2f}" for d in s["dims_m"]) + " m" if s["dims_m"] else "?"
        print(f"{s['name']}  [{s['licence']}, {'free' if s['free'] else 'FULL PLAN'}]")
        print(f"  id {s['id']}  faces {s['faces']}  {dims}  tex {s['tex_max']}  files {','.join(s['files'])}")
        print(f"  {s['page']}")


def cmd_download(a: argparse.Namespace) -> None:
    key = api_key()
    url = f"{API}/search/?" + urllib.parse.urlencode({"query": f"asset_base_id:{a.id}", "dict_parameters": 1})
    results = get(url, key)["results"]
    if not results:
        sys.exit(f"no asset with assetBaseId {a.id}")
    r = results[0]
    if not r.get("isFree") and not key:
        sys.exit("Full-plan asset: log in to Blendkit inside Blender (or set BLENDKIT_API_KEY) first")
    ftype = a.file_type or DEFAULT_FILE.get(r["assetType"], "blend")
    files = {f["fileType"]: f for f in r.get("files", [])}
    if ftype not in files:
        sys.exit(f"no '{ftype}' file; available: {', '.join(sorted(files))}")
    signed = get(files[ftype]["downloadUrl"] + "?scene_uuid=" + str(uuid.uuid4()), key).get("filePath")
    if not signed:
        sys.exit(f"download refused for '{ftype}' (licence/plan?)")
    slug = re.sub(r"[^A-Za-z0-9]+", "_", r["name"]).strip("_")
    out = Path(a.out) if a.out else DEFAULT_OUT / f"{slug}_{a.id[:8]}"
    out.mkdir(parents=True, exist_ok=True)
    dest = out / (slug + Path(urllib.parse.urlparse(signed).path).suffix)
    with urllib.request.urlopen(urllib.request.Request(signed, headers=UA), timeout=600) as resp, open(dest, "wb") as f:
        while chunk := resp.read(1 << 20):
            f.write(chunk)
    meta = summary(r) | {"file_type": ftype, "file": dest.name}
    (out / "blendkit.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    print(dest)


def image_size(data: bytes) -> tuple[int, int] | None:
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", data[16:24])
    if data[:2] == b"\xff\xd8":
        i = 2
        while i + 9 < len(data):
            marker, length = data[i + 1], struct.unpack(">H", data[i + 2 : i + 4])[0]
            if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
                h, w = struct.unpack(">HH", data[i + 5 : i + 9])
                return w, h
            i += 2 + length
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        chunk = data[12:16]
        if chunk == b"VP8 ":
            w, h = struct.unpack("<HH", data[26:30])
            return w & 0x3FFF, h & 0x3FFF
        if chunk == b"VP8L":
            b = int.from_bytes(data[21:25], "little")
            return (b & 0x3FFF) + 1, ((b >> 14) & 0x3FFF) + 1
        if chunk == b"VP8X":
            return int.from_bytes(data[24:27], "little") + 1, int.from_bytes(data[27:30], "little") + 1
    return None


def inspect_glb(path: Path) -> dict:
    raw = path.read_bytes()
    if raw[:4] != b"glTF":
        sys.exit(f"{path} is not a GLB")
    jlen = struct.unpack("<I", raw[12:16])[0]
    g = json.loads(raw[20 : 20 + jlen])
    blob = raw[20 + jlen + 8 :]
    acc = g.get("accessors", [])
    tris = 0
    for m in g.get("meshes", []):
        for p in m["primitives"]:
            if p.get("mode", 4) != 4:
                continue
            n = acc[p["indices"]]["count"] if "indices" in p else acc[p["attributes"]["POSITION"]]["count"]
            tris += n // 3
    # instanced meshes count once per node that references them
    uses: dict[int, int] = {}
    for n in g.get("nodes", []):
        if "mesh" in n:
            uses[n["mesh"]] = uses.get(n["mesh"], 0) + 1
    placed = 0
    for mi, m in enumerate(g.get("meshes", [])):
        t = sum(
            (acc[p["indices"]]["count"] if "indices" in p else acc[p["attributes"]["POSITION"]]["count"]) // 3
            for p in m["primitives"]
            if p.get("mode", 4) == 4
        )
        placed += t * uses.get(mi, 0)
    images = []
    for img in g.get("images", []):
        size = None
        if "bufferView" in img:
            bv = g["bufferViews"][img["bufferView"]]
            off = bv.get("byteOffset", 0)
            size = image_size(blob[off : off + bv["byteLength"]])
        images.append({"name": img.get("name"), "mime": img.get("mimeType"), "size": size})
    uv_sets = max(
        (sum(1 for k in p["attributes"] if k.startswith("TEXCOORD_")) for m in g.get("meshes", []) for p in m["primitives"]),
        default=0,
    )
    return {
        "file": str(path),
        "mb": round(len(raw) / 1e6, 2),
        "tris_placed": placed,
        "tris_unique": tris,
        "meshes": len(g.get("meshes", [])),
        "nodes_with_mesh": sum(uses.values()),
        "materials": len(g.get("materials", [])),
        "uv_sets": uv_sets,
        "skinned": bool(g.get("skins")),
        "animations": len(g.get("animations", [])),
        "images": images,
        "webp": any(i["mime"] == "image/webp" for i in images),
    }


def cmd_inspect(a: argparse.Namespace) -> None:
    print(json.dumps(inspect_glb(Path(a.file)), indent=1))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search")
    s.add_argument("query")
    s.add_argument("--type", default="model", choices=["model", "material", "hdr", "scene", "brush"])
    s.add_argument("--max-faces", type=int)
    s.add_argument("--free", action="store_true", help="free-plan assets only")
    s.add_argument("--limit", type=int, default=10)
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_search)
    d = sub.add_parser("download")
    d.add_argument("id", help="assetBaseId from search")
    d.add_argument("--out", help=f"directory (default {DEFAULT_OUT}{os.sep}<name>_<id8>)")
    d.add_argument("--file-type", help="gltf (models), resolution_1K/2K/4K (HDRIs), blend")
    d.set_defaults(fn=cmd_download)
    i = sub.add_parser("inspect")
    i.add_argument("file", help="downloaded .glb")
    i.set_defaults(fn=cmd_inspect)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
