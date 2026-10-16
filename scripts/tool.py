#!/usr/bin/env python3
"""AWDK tool router: fixed tool names for skills and agents; each user picks the backends.

Skills and agents call one of these names and never a product:

    image-gen    text -> image (concept art, references, texture sheets)
    image-edit   text + reference images -> image (keep a style, object or outfit)
    image-to-3d  image(s) -> GLB model
    blender      run a Python script in headless Blender
    check        show which backend each tool uses and whether it is reachable

Which service actually runs is set per machine in `.omp/local/tools.json` (template:
`.omp/local.example/tools.json`, guide: `.omp/docs/tools.md`). A tool may list several
backends: they are tried in order, so put paid ones first and free ones after as fallbacks.

Examples:
    python .omp/scripts/tool.py image-gen --prompt-file p.txt --aspect landscape --output a.png
    python .omp/scripts/tool.py image-edit --prompt-file p.txt --reference lock.png --output b.png
    python .omp/scripts/tool.py image-to-3d --image front.png --faces 8000 --output chair.glb
    python .omp/scripts/tool.py image-to-3d --front f.png --left l.png --back b.png --right r.png --output x.glb
    python .omp/scripts/tool.py blender --script build.py -- --size 2
    python .omp/scripts/tool.py check

Stdout is one JSON object: {"ok", "tool", "backend", "output", "tried", "meta"}.
Exit codes: 0 done; 1 every backend failed; 2 usage or config error; 3 hand-off (the agent
or the user must do the step, see "handoff"); 4 the backend needs spend approval
(re-run with --approve-spend only after the user approved the spend).
Only the standard library is used. API keys come from environment variables or key files
in `.omp/local/`; they are never printed.
"""
from __future__ import annotations

import argparse
import base64
import json
import math
import mimetypes
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
CONFIG = Path(os.environ.get("AWDK_TOOLS_CONFIG", KIT / "local" / "tools.json"))
TOOLS = ("image-gen", "image-edit", "image-to-3d")
VIEWS = ("front", "left", "back", "right")

ASPECTS = {  # name -> (gpt-image size, gemini ratio, comfyui size: ~1 MP, multiples of 32)
    "square": ((1024, 1024), "1:1", (1024, 1024)),
    "landscape": ((1536, 1024), "3:2", (1248, 832)),
    "portrait": ((1024, 1536), "2:3", (832, 1248)),
    "wide": ((1536, 864), "16:9", (1344, 768)),
    "tall": ((864, 1536), "9:16", (768, 1344)),
}
GEMINI_RATIOS = ("1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9")


class ToolError(Exception):
    """A backend failed; the next backend in the chain is tried."""


class Handoff(Exception):
    def __init__(self, payload: dict):
        super().__init__(payload.get("how", "hand-off"))
        self.payload = payload


class NeedsApproval(Exception):
    pass


# ---------------------------------------------------------------- helpers

def kit_path(p: str) -> Path:
    path = Path(os.path.expandvars(os.path.expanduser(p)))
    return path if path.is_absolute() else KIT / path


def api_key(cfg: dict, default_env: str) -> str:
    if cfg.get("key_file"):
        f = kit_path(cfg["key_file"])
        if not f.is_file():
            raise ToolError(f"key file {cfg['key_file']} not found")
        key = f.read_text(encoding="utf-8").strip()
    else:
        env = cfg.get("key_env", default_env)
        key = os.environ.get(env, "").strip()
        if not key:
            raise ToolError(f"environment variable {env} is not set")
    if not key:
        raise ToolError("API key is empty")
    return key


def http(method: str, url: str, *, headers: dict | None = None, body: bytes | None = None,
         timeout: float = 300) -> bytes:
    req = urllib.request.Request(url, data=body, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:600]
        raise ToolError(f"HTTP {e.code} from {urllib.parse.urlsplit(url).netloc}: {detail}") from None
    except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
        raise ToolError(f"cannot reach {urllib.parse.urlsplit(url).netloc}: {e}") from None


def http_json(method: str, url: str, payload=None, headers: dict | None = None, timeout: float = 300):
    h = dict(headers or {})
    body = None
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        h["Content-Type"] = "application/json"
    raw = http(method, url, headers=h, body=body, timeout=timeout)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        raise ToolError(f"non-JSON reply from {url}: {raw[:200]!r}") from None


def multipart(fields: dict, files: dict) -> tuple[bytes, str]:
    boundary = uuid.uuid4().hex
    out = bytearray()
    for k, v in fields.items():
        out += f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode()
    for k, path in files.items():
        p = Path(path)
        ctype = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
        out += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"; "
                f"filename=\"{p.name}\"\r\nContent-Type: {ctype}\r\n\r\n").encode()
        out += p.read_bytes() + b"\r\n"
    out += f"--{boundary}--\r\n".encode()
    return bytes(out), f"multipart/form-data; boundary={boundary}"


def data_url(path: str) -> str:
    p = Path(path)
    ctype = mimetypes.guess_type(p.name)[0] or "image/png"
    return f"data:{ctype};base64,{base64.b64encode(p.read_bytes()).decode()}"


def write_out(path: str, data: bytes) -> str:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)
    return str(p)


def size_for(aspect: str, column: int):
    if aspect in ASPECTS:
        return ASPECTS[aspect][column]
    try:
        w, h = (int(v) for v in aspect.lower().split("x"))
    except ValueError:
        raise SystemExit(f"--aspect must be one of {', '.join(ASPECTS)} or WIDTHxHEIGHT, got {aspect!r}")
    if column == 1:  # nearest supported Gemini ratio
        target = math.log(w / h)
        return min(GEMINI_RATIOS, key=lambda r: abs(math.log(int(r.split(':')[0]) / int(r.split(':')[1])) - target))
    if column == 0:  # gpt-image: multiples of 16
        return (w // 16 * 16, h // 16 * 16)
    return (w // 32 * 32, h // 32 * 32)  # comfyui: latent sizes in multiples of 32


def poll(fetch, done, *, every: float, timeout: float, what: str):
    end = time.monotonic() + timeout
    while True:
        state = fetch()
        result = done(state)
        if result is not None:
            return result
        if time.monotonic() > end:
            raise ToolError(f"{what} still running after {int(timeout)} s; resume it later "
                            "with --resume instead of submitting again")
        time.sleep(every)


def log(msg: str):
    print(msg, file=sys.stderr, flush=True)


# ---------------------------------------------------------------- image backends

def openai_image(cfg: dict, req: dict) -> dict:
    key = api_key(cfg, "OPENAI_API_KEY")
    base = cfg.get("base_url", "https://api.openai.com/v1").rstrip("/")
    w, h = size_for(req["aspect"], 0)
    body = {"model": cfg.get("model", "gpt-image-2.5-sunburst"), "prompt": req["prompt"],
            "size": f"{w}x{h}", "quality": req["quality"], "n": 1, "output_format": "png"}
    if req["transparent"]:
        body["background"] = "transparent"
    body.update(cfg.get("params", {}))
    endpoint = "/images/generations"
    if req["references"]:
        endpoint = "/images/edits"
        body["images"] = [{"image_url": data_url(r)} for r in req["references"]]
    res = http_json("POST", base + endpoint, body, {"Authorization": f"Bearer {key}"},
                    timeout=cfg.get("timeout", 600))
    try:
        img = base64.b64decode(res["data"][0]["b64_json"])
    except (KeyError, IndexError, TypeError):
        raise ToolError(f"no image in reply: {json.dumps(res)[:300]}") from None
    return {"output": write_out(req["output"], img), "meta": {"model": body["model"], "size": body["size"]}}


def find_images(node, found: list):
    """Collect base64 image blocks from any Gemini reply shape."""
    if isinstance(node, dict):
        mime = node.get("mime_type") or node.get("mimeType") or ""
        if isinstance(node.get("data"), str) and mime.startswith("image/"):
            found.append(node["data"])
        for v in node.values():
            find_images(v, found)
    elif isinstance(node, list):
        for v in node:
            find_images(v, found)
    return found


def gemini_image(cfg: dict, req: dict) -> dict:
    key = api_key(cfg, "GEMINI_API_KEY")
    base = cfg.get("base_url", "https://generativelanguage.googleapis.com/v1beta").rstrip("/")
    model = cfg.get("model", "gemini-nano-banana-2.1")
    parts = [{"type": "text", "text": req["prompt"]}]
    for r in req["references"]:
        p = Path(r)
        parts.append({"type": "image", "mime_type": mimetypes.guess_type(p.name)[0] or "image/png",
                      "data": base64.b64encode(p.read_bytes()).decode()})
    body = {"model": model, "input": parts,
            "response_format": {"type": "image", "mime_type": "image/png",
                                "aspect_ratio": size_for(req["aspect"], 1),
                                "image_size": cfg.get("image_size", "2K")}}
    body.update(cfg.get("params", {}))
    res = http_json("POST", base + "/interactions", body, {"x-goog-api-key": key},
                    timeout=cfg.get("timeout", 600))
    imgs = find_images(res, [])
    if not imgs:
        raise ToolError(f"no image in reply: {json.dumps(res)[:300]}")
    meta = {"model": model, "aspect_ratio": body["response_format"]["aspect_ratio"]}
    if req["transparent"]:
        meta["warning"] = "no transparent output; key out a flat background colour instead"
    return {"output": write_out(req["output"], base64.b64decode(imgs[-1])), "meta": meta}


def grow_reference_inputs(workflow: dict, loads: list[str], count: int) -> None:
    """Add LoadImage nodes for extra references on a node with numbered image inputs (image_1, image_2...)."""
    first = loads[0]
    for node in workflow.values():
        ins = node.get("inputs", {})
        for key, val in list(ins.items()):
            m = re.fullmatch(r"(.*?)(\d+)", key)
            if not (m and isinstance(val, list) and str(val[0]) == first and m.group(2) == "1"):
                continue
            for i in range(len(loads) + 1, count + 1):
                new_id = f"{first}_{i}"
                workflow[new_id] = {"class_type": "LoadImage", "inputs": {"image": ""}}
                ins[f"{m.group(1)}{i}"] = [new_id, 0]
            return
    raise ToolError(f"workflow has {len(loads)} LoadImage nodes and no numbered image input to add "
                    f"more; it can't take {count} references")


def ensure_comfyui(cfg: dict, url: str) -> None:
    """Reach ComfyUI; when it is down and the config has "start", launch it detached and wait."""
    try:
        http("GET", url + "/system_stats", timeout=5)
        return
    except ToolError:
        if not cfg.get("start"):
            raise
    if urllib.parse.urlsplit(url).hostname not in ("127.0.0.1", "localhost"):
        raise ToolError(f"ComfyUI at {url} is down; auto-start only runs for a loopback url")
    log_path = kit_path(cfg.get("start_log", "local/comfyui/comfyui.log"))
    log_path.parent.mkdir(parents=True, exist_ok=True)
    flags = (subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP) if os.name == "nt" else 0
    with open(log_path, "ab") as logf:
        proc = subprocess.Popen([os.path.expandvars(a) for a in cfg["start"]],
                                cwd=cfg.get("start_cwd") and kit_path(cfg["start_cwd"]),
                                stdout=logf, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                                creationflags=flags, close_fds=True)
    log(f"comfyui: started (pid {proc.pid}), waiting for {url}")
    end = time.monotonic() + cfg.get("start_timeout", 240)
    while time.monotonic() < end:
        if proc.poll() is not None:
            raise ToolError(f"ComfyUI exited during startup (code {proc.returncode}); see {log_path}")
        try:
            http("GET", url + "/system_stats", timeout=5)
            return
        except ToolError:
            time.sleep(2)
    raise ToolError(f"ComfyUI not ready after {cfg.get('start_timeout', 240)} s; see {log_path}")


def comfy_prompt_node(workflow: dict, link) -> dict | None:
    """Follow a conditioning link back (through ReferenceLatent-style nodes) to the text encoder."""
    for _ in range(6):
        if not isinstance(link, list):
            return None
        ins = workflow[str(link[0])].get("inputs", {})
        if isinstance(ins.get("text"), str) or isinstance(ins.get("prompt"), str):
            return ins
        link = ins.get("conditioning") or ins.get("positive")
    return None


def comfy_fill(workflow: dict, values: dict, refs: list[str]) -> str:
    """Fill {{placeholders}}; whatever has none is mapped onto the standard nodes."""
    text = json.dumps(workflow)
    filled = []
    if "{{image" not in text:
        def node_key(k):
            return [(0, int(p), "") if p.isdigit() else (1, 0, p) for p in re.split(r"[:_]", k)]
        loads = sorted((k for k, n in workflow.items() if n.get("class_type") == "LoadImage"), key=node_key)
        if loads and len(refs) > len(loads):
            grow_reference_inputs(workflow, loads, len(refs))
            loads = sorted((k for k, n in workflow.items() if n.get("class_type") == "LoadImage"), key=node_key)
        if len(loads) != len(refs):
            raise ToolError(f"workflow has {len(loads)} LoadImage nodes but {len(refs)} reference "
                            "images were given; use a workflow made for this many references")
        for node_id, ref in zip(loads, refs):
            workflow[node_id]["inputs"]["image"] = ref
        if refs:
            filled.append("images")
    if "{{" in text:
        def sub(v):
            if isinstance(v, dict):
                return {k: sub(x) for k, x in v.items()}
            if isinstance(v, list):
                return [sub(x) for x in v]
            if isinstance(v, str) and "{{" in v:
                s = v.strip()
                if s.startswith("{{") and s.endswith("}}") and s[2:-2] in values:
                    return values[s[2:-2]]
                for k, x in values.items():
                    v = v.replace("{{" + k + "}}", str(x))
            return v
        workflow.update(sub(workflow))
        left = sorted(set(re.findall(r"\{\{(\w+)\}\}", json.dumps(workflow))))
        if left:
            raise ToolError(f"workflow placeholders without a value: {', '.join(left)}")
        if "{{prompt}}" not in text:
            raise ToolError("workflow uses placeholders but has no {{prompt}}")
        return ",".join(["placeholders", *filled])
    for node in workflow.values():
        ins, cls = node.get("inputs", {}), node.get("class_type", "")
        if cls.startswith("KSampler") or cls == "SamplerCustom":
            for s in ("seed", "noise_seed"):
                if isinstance(ins.get(s), int):
                    ins[s] = values["seed"]
            if "positive" in ins:
                enc = comfy_prompt_node(workflow, ins["positive"])
                if enc is None:
                    raise ToolError("cannot find the positive prompt text in the workflow; put {{prompt}} there")
                enc["text" if isinstance(enc.get("text"), str) else "prompt"] = values["prompt"]
                filled.append("prompt")
        elif cls == "RandomNoise" and isinstance(ins.get("noise_seed"), int):
            ins["noise_seed"] = values["seed"]
        elif "Latent" in cls and cls.startswith("Empty") and isinstance(ins.get("width"), int):
            ins["width"], ins["height"] = values["width"], values["height"]
            filled.append("size")
    if "prompt" not in filled:
        raise ToolError("no sampler with a positive prompt found; put {{prompt}} in the workflow")
    return "auto:" + ",".join(sorted(set(filled)))


def comfyui_image(cfg: dict, req: dict) -> dict:
    url = cfg.get("url", "http://127.0.0.1:8188").rstrip("/")
    if not cfg.get("workflow"):
        raise ToolError("comfyui backend needs \"workflow\": an API-format workflow JSON")
    wf_path = kit_path(cfg["workflow"])
    if not wf_path.is_file():
        raise ToolError(f"workflow {cfg['workflow']} not found")
    workflow = json.loads(wf_path.read_text(encoding="utf-8"))
    if "nodes" in workflow and "links" in workflow:
        raise ToolError("workflow is in UI format; export it with Workflow -> Export (API)")
    ensure_comfyui(cfg, url)
    uploaded = []
    for i, r in enumerate(req["references"], 1):
        body, ctype = multipart({"overwrite": "true"}, {"image": r})
        res = json.loads(http("POST", url + "/upload/image", headers={"Content-Type": ctype}, body=body))
        uploaded.append(f"{res['subfolder']}/{res['name']}" if res.get("subfolder") else res["name"])
    w, h = size_for(req["aspect"], 2)
    values = {"prompt": req["prompt"], "width": w, "height": h,
              "seed": random.randint(0, 2**31 - 1), "negative": cfg.get("negative", "")}
    for i, name in enumerate(uploaded, 1):
        values[f"image{i}"] = name
    how = comfy_fill(workflow, values, uploaded)
    res = http_json("POST", url + "/prompt", {"prompt": workflow, "client_id": uuid.uuid4().hex})
    if res.get("node_errors"):
        raise ToolError(f"ComfyUI rejected the workflow: {json.dumps(res['node_errors'])[:400]}")
    pid = res["prompt_id"]
    log(f"comfyui prompt {pid} queued")

    def done(hist):
        entry = hist.get(pid)
        if not entry:
            return None
        status = entry.get("status", {})
        if status.get("status_str") == "error":
            raise ToolError(f"ComfyUI run failed: {json.dumps(status.get('messages', []))[-400:]}")
        imgs = [im for out in entry.get("outputs", {}).values() for im in out.get("images", [])
                if im.get("type") == "output"]
        if imgs:
            return imgs[0]
        if status.get("completed"):
            raise ToolError("ComfyUI finished without a saved image (no SaveImage node?)")
        return None

    img = poll(lambda: http_json("GET", f"{url}/history/{pid}"), done,
               every=2, timeout=cfg.get("timeout", 900), what=f"ComfyUI prompt {pid}")
    q = urllib.parse.urlencode({"filename": img["filename"], "subfolder": img.get("subfolder", ""), "type": "output"})
    data = http("GET", f"{url}/view?{q}")
    meta = {"workflow": cfg["workflow"], "seed": values["seed"], "filled": how,
            "size": f"{w}x{h}" if "size" in how or "placeholders" in how else "set by the workflow"}
    if req["transparent"]:
        meta["warning"] = "no transparent output; key out a flat background colour instead"
    return {"output": write_out(req["output"], data), "meta": meta}


# ---------------------------------------------------------------- 3D backends

def tripo_model(cfg: dict, req: dict) -> dict:
    key = api_key(cfg, "TRIPO_API_KEY")
    base = cfg.get("base_url", "https://openapi.tripo3d.com/v3").rstrip("/")
    auth = {"Authorization": f"Bearer {key}"}

    def check(res):
        if res.get("code") != 0:
            raise ToolError(f"Tripo error {res.get('code')}: {res.get('message')} {res.get('suggestion', '')}")
        return res["data"]

    task = req.get("resume")
    if not task:
        def upload(path):
            body, ctype = multipart({}, {"file": path})
            res = json.loads(http("POST", base + "/files", headers={**auth, "Content-Type": ctype}, body=body))
            return check(res)["file_token"]
        body = {"model": cfg.get("model", "v3.1-20260211"), "texture": req["texture"]}
        if not req["texture"]:
            body["pbr"] = False
        if req["faces"]:
            body["face_limit"] = req["faces"]
        body.update(cfg.get("params", {}))
        if req["views"]:
            body["inputs"] = [{v: upload(p)} for v, p in req["views"].items()]
            endpoint = "/generation/multiview-to-model"
        else:
            body["input"] = upload(req["images"][0])
            endpoint = "/generation/image-to-model"
        task = check(http_json("POST", base + endpoint, body, auth))["task_id"]
        log(f"tripo task {task} submitted (resume with --resume {task})")

    def done(data):
        st = data.get("status")
        if st == "success":
            return data
        if st in ("failed", "cancelled"):
            raise ToolError(f"Tripo task {task} {st}: {data.get('message', '')}")
        return None

    data = poll(lambda: check(http_json("GET", f"{base}/tasks/{task}", None, auth)), done,
                every=5, timeout=cfg.get("timeout", 900), what=f"Tripo task {task}")
    url = data.get("output", {}).get("model_url")
    if not url:
        raise ToolError(f"Tripo task {task} has no model_url: {json.dumps(data)[:300]}")
    return {"output": write_out(req["output"], http("GET", url, timeout=600)),
            "meta": {"task_id": task, "credits": data.get("credits_consumed")}}


def meshy_model(cfg: dict, req: dict) -> dict:
    key = api_key(cfg, "MESHY_API_KEY")
    base = cfg.get("base_url", "https://api.meshy.ai/openapi/v1").rstrip("/")
    auth = {"Authorization": f"Bearer {key}"}
    images = list(req["views"].values()) if req["views"] else req["images"]
    kind = "multi-image-to-3d" if len(images) > 1 else "image-to-3d"
    task = req.get("resume")
    if task and ":" in task:
        kind, task = task.split(":", 1)
    if not task:
        body = {"ai_model": cfg.get("model", "latest"), "should_texture": req["texture"],
                "target_formats": ["glb"]}
        if req["faces"]:
            body.update({"should_remesh": True, "target_polycount": req["faces"]})
        body.update(cfg.get("params", {}))
        if kind == "multi-image-to-3d":
            body["image_urls"] = [data_url(p) for p in images]
        else:
            body["image_url"] = data_url(images[0])
        task = http_json("POST", f"{base}/{kind}", body, auth)["result"]
        log(f"meshy task {task} submitted (resume with --resume {kind}:{task})")

    def done(data):
        st = data.get("status")
        if st == "SUCCEEDED":
            return data
        if st in ("FAILED", "CANCELED"):
            raise ToolError(f"Meshy task {task} {st}: {data.get('task_error', '')}")
        return None

    data = poll(lambda: http_json("GET", f"{base}/{kind}/{task}", None, auth), done,
                every=5, timeout=cfg.get("timeout", 900), what=f"Meshy task {task}")
    url = data.get("model_urls", {}).get("glb")
    if not url:
        raise ToolError(f"Meshy task {task} has no GLB url")
    return {"output": write_out(req["output"], http("GET", url, timeout=600)), "meta": {"task_id": task}}


# ---------------------------------------------------------------- generic backends

def command_backend(cfg: dict, req: dict) -> dict:
    """Run any local command; placeholders in "args" are filled from the request."""
    args = cfg.get("args")
    if not args:
        raise ToolError("command backend needs \"args\"")
    tmp = None
    prompt_file = req.get("prompt_file") or ""
    if req.get("prompt") and not prompt_file:
        tmp = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8")
        tmp.write(req["prompt"])
        tmp.close()
        prompt_file = tmp.name
    w, h = size_for(req.get("aspect", "square"), 2)
    images = list(req.get("views", {}).values()) or req.get("images", [])
    scalars = {"prompt": req.get("prompt", ""), "prompt_file": prompt_file, "output": req["output"],
               "aspect": req.get("aspect", ""), "width": w, "height": h, "quality": req.get("quality", ""),
               "faces": req.get("faces") or "", "image": images[0] if images else "", "kit": str(KIT),
               **{v: p for v, p in req.get("views", {}).items()}}
    argv = []
    for a in args:
        if a == "{references}":
            for r in req.get("references", []):
                argv += ([cfg["reference_flag"]] if cfg.get("reference_flag") else []) + [r]
        elif a == "{images}":
            for r in images:
                argv += ([cfg["image_flag"]] if cfg.get("image_flag") else []) + [r]
        else:
            try:
                argv.append(os.path.expandvars(a).format(**scalars))
            except KeyError as e:
                raise ToolError(f"unknown placeholder {e} in command args") from None
    if argv and argv[0].endswith(".py") and not cfg.get("python"):
        argv.insert(0, sys.executable)
    elif cfg.get("python"):
        argv.insert(0, str(kit_path(cfg["python"])) if "/" in cfg["python"] or "\\" in cfg["python"] else cfg["python"])
    out = Path(req["output"])
    out.parent.mkdir(parents=True, exist_ok=True)
    before = out.stat().st_mtime if out.exists() else None
    try:
        r = subprocess.run(argv, cwd=cfg.get("cwd") and kit_path(cfg["cwd"]), capture_output=True, text=True,
                           timeout=cfg.get("timeout", 900), env={**os.environ, **cfg.get("env", {})})
    except FileNotFoundError:
        raise ToolError(f"command not found: {argv[0]}") from None
    except subprocess.TimeoutExpired:
        raise ToolError(f"command timed out after {cfg.get('timeout', 900)} s") from None
    finally:
        if tmp:
            os.unlink(tmp.name)
    if r.returncode != 0:
        raise ToolError(f"command exited {r.returncode}: {(r.stderr or r.stdout)[-600:]}")
    if not out.exists() or out.stat().st_size == 0 or out.stat().st_mtime == before:
        raise ToolError(f"command succeeded but did not write {out}: {r.stdout[-300:]}")
    return {"output": str(out), "meta": {"stdout_tail": r.stdout.strip()[-200:]}}


def agent_backend(cfg: dict, req: dict) -> dict:
    raise Handoff({"handoff": "agent", "agent_tool": cfg.get("tool"), "how": cfg.get("how", ""),
                   "args": cfg.get("args", {}), "request": req})


def manual_backend(cfg: dict, req: dict) -> dict:
    raise Handoff({"handoff": "user", "how": cfg.get("how", "ask the user to make this by hand"),
                   "request": req})


BACKENDS = {
    "image-gen": {"openai": openai_image, "gemini": gemini_image, "comfyui": comfyui_image},
    "image-edit": {"openai": openai_image, "gemini": gemini_image, "comfyui": comfyui_image},
    "image-to-3d": {"tripo": tripo_model, "meshy": meshy_model},
}
GENERIC = {"command": command_backend, "agent": agent_backend, "manual": manual_backend}
PAID = {"openai", "gemini", "tripo", "meshy"}


# ---------------------------------------------------------------- config and dispatch

def load_config() -> dict:
    if not CONFIG.is_file():
        raise SystemExit(f"no tool config at {CONFIG}; copy .omp/local.example/tools.json there "
                         "and follow .omp/docs/tools.md")
    try:
        return json.loads(CONFIG.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise SystemExit(f"{CONFIG}: invalid JSON: {e}")


def chain(cfg: dict, tool: str) -> list[dict]:
    entry = cfg.get(tool)
    if not entry:
        raise SystemExit(f"tool {tool!r} is not configured in {CONFIG}; see .omp/docs/tools.md")
    entries = entry if isinstance(entry, list) else [entry]
    for e in entries:
        b = e.get("backend")
        if b not in GENERIC and b not in BACKENDS.get(tool, {}):
            ok = ", ".join(sorted(set(GENERIC) | set(BACKENDS.get(tool, {}))))
            raise SystemExit(f"{tool}: unknown backend {b!r} (choose from {ok})")
    return entries


def run(tool: str, req: dict, args) -> int:
    entries = chain(load_config(), tool)
    if args.backend:
        entries = [e for e in entries if args.backend in (e.get("name"), e.get("backend"))]
        if not entries:
            raise SystemExit(f"{tool}: no backend named {args.backend!r} in the config")
    tried = []
    for e in entries:
        label = e.get("name", e["backend"])
        fn = GENERIC.get(e["backend"]) or BACKENDS[tool][e["backend"]]
        if e.get("confirm_spend") and not args.approve_spend:
            print(json.dumps({"ok": False, "tool": tool, "backend": label, "needs_approval": True,
                              "how": e.get("how", "this backend spends money; ask the user to approve "
                                                  "this generation, then re-run with --approve-spend"),
                              "tried": tried}, indent=1))
            return 4
        if args.dry_run:
            print(json.dumps({"ok": True, "dry_run": True, "tool": tool, "backend": label,
                              "request": req, "tried": tried}, indent=1))
            return 0
        log(f"{tool}: trying {label}")
        try:
            res = fn(e, req)
        except Handoff as h:
            print(json.dumps({"ok": False, "tool": tool, "backend": label, **h.payload, "tried": tried}, indent=1))
            return 3
        except ToolError as err:
            tried.append({"backend": label, "error": str(err)})
            log(f"{tool}: {label} failed: {err}")
            continue
        meta = res.get("meta", {})
        fmt = sniff(res["output"])
        want = "glb" if tool == "image-to-3d" else "png"
        if fmt != want:
            meta["format_warning"] = f"output is {fmt.upper()}, not {want.upper()}; convert it if the next step needs {want.upper()}"
        print(json.dumps({"ok": True, "tool": tool, "backend": label, "output": res["output"],
                          "format": fmt, "tried": tried, "meta": meta}, indent=1))
        return 0
    print(json.dumps({"ok": False, "tool": tool, "error": "every backend failed", "tried": tried}, indent=1))
    return 1


def sniff(path: str) -> str:
    head = Path(path).read_bytes()[:12]
    if head.startswith(b"\x89PNG"):
        return "png"
    if head.startswith(b"\xff\xd8"):
        return "jpeg"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "webp"
    if head.startswith(b"glTF"):
        return "glb"
    return Path(path).suffix.lstrip(".").lower() or "unknown"


def blender_path(cfg: dict) -> str:
    b = cfg.get("blender", {}).get("path") or "blender"
    found = shutil.which(b) or (b if Path(b).is_file() else None)
    if not found:
        raise SystemExit(f"Blender not found at {b!r}; set \"blender\": {{\"path\": ...}} in {CONFIG}")
    return found


def run_blender(args, extra: list[str]) -> int:
    exe = blender_path(load_config())
    argv = [exe, "-b", "--factory-startup"]
    if args.blend:
        argv.append(args.blend)
    argv += ["--python", args.script, "--", *extra]
    log("running: " + " ".join(argv))
    try:
        return subprocess.run(argv, timeout=args.timeout or None).returncode
    except subprocess.TimeoutExpired:
        log(f"Blender timed out after {args.timeout} s")
        return 1


def check(tools: list[str]) -> int:
    cfg = load_config()
    rows, bad = [], False
    for tool in tools or [*TOOLS, "blender"]:
        if tool == "blender":
            try:
                exe = blender_path(cfg)
                v = subprocess.run([exe, "-b", "--factory-startup", "--version"], capture_output=True,
                                   text=True, timeout=60).stdout.splitlines()
                rows.append({"tool": "blender", "backend": exe, "status": v[0] if v else "ok"})
            except (SystemExit, subprocess.TimeoutExpired, OSError) as e:
                rows.append({"tool": "blender", "status": f"missing: {e}"})
                bad = True
            continue
        if not cfg.get(tool):
            rows.append({"tool": tool, "status": "not configured"})
            bad = True
            continue
        for e in chain(cfg, tool):
            b, status = e["backend"], "ok"
            try:
                if b in PAID:
                    api_key(e, {"openai": "OPENAI_API_KEY", "gemini": "GEMINI_API_KEY",
                                "tripo": "TRIPO_API_KEY", "meshy": "MESHY_API_KEY"}[b])
                    status = "key present (not spent)" + (", needs approval per use" if e.get("confirm_spend") else "")
                elif b == "comfyui":
                    if not kit_path(e.get("workflow", "")).is_file():
                        raise ToolError(f"workflow {e.get('workflow')} not found")
                    try:
                        http("GET", e.get("url", "http://127.0.0.1:8188").rstrip("/") + "/system_stats", timeout=5)
                        status = "server up, workflow found"
                    except ToolError:
                        if not e.get("start"):
                            raise
                        exe = os.path.expandvars(e["start"][0])
                        if not (shutil.which(exe) or Path(exe).is_file()):
                            raise ToolError(f"server down and start command {exe} not found")
                        status = "server down, starts on first use; workflow found"
                elif b == "command":
                    first = os.path.expandvars((e.get("args") or [""])[0]).replace("{kit}", str(KIT))
                    for exe in filter(None, [e.get("python"), first]):
                        if not (shutil.which(exe) or Path(exe).is_file() or kit_path(exe).is_file()):
                            raise ToolError(f"{exe} not found")
                    if e.get("cwd") and not kit_path(e["cwd"]).is_dir():
                        raise ToolError(f"cwd {e['cwd']} not found")
                    status = "command found"
                else:
                    status = f"hand-off to {'the agent' if b == 'agent' else 'the user'}"
            except ToolError as err:
                status, bad = f"FAIL: {err}", True
            rows.append({"tool": tool, "backend": e.get("name", b), "status": status})
    print(json.dumps({"config": str(CONFIG), "tools": rows}, indent=1))
    return 1 if bad else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="tool", required=True)

    def common(p):
        p.add_argument("--output", required=True, help="file to write (PNG for images, GLB for models)")
        p.add_argument("--backend", help="use only this backend (its name or type) from the config")
        p.add_argument("--approve-spend", action="store_true",
                       help="the user approved this paid generation (needed when confirm_spend is set)")
        p.add_argument("--dry-run", action="store_true", help="show the backend and request, call nothing")

    for name in ("image-gen", "image-edit"):
        p = sub.add_parser(name)
        g = p.add_mutually_exclusive_group(required=True)
        g.add_argument("--prompt")
        g.add_argument("--prompt-file")
        p.add_argument("--reference", action="append", default=[],
                       help="reference image (repeatable, order matters)" if name == "image-edit" else argparse.SUPPRESS)
        p.add_argument("--aspect", default="square", help=f"{', '.join(ASPECTS)} or WIDTHxHEIGHT")
        p.add_argument("--quality", default="medium", choices=("low", "medium", "high"))
        p.add_argument("--transparent", action="store_true")
        common(p)
    p = sub.add_parser("image-to-3d")
    p.add_argument("--image", action="append", default=[], help="single input image")
    for v in VIEWS:
        p.add_argument(f"--{v}", help=f"{v} view for multiview generation")
    p.add_argument("--faces", type=int, help="face limit")
    p.add_argument("--no-texture", action="store_true")
    p.add_argument("--resume", help="task id printed by an earlier run; download it instead of submitting")
    common(p)
    p = sub.add_parser("blender")
    p.add_argument("--script", required=True)
    p.add_argument("--blend", help=".blend file to open first")
    p.add_argument("--timeout", type=int, default=0)
    p = sub.add_parser("check")
    p.add_argument("tools", nargs="*")

    argv = sys.argv[1:] if argv is None else argv
    extra = []
    if "--" in argv:
        i = argv.index("--")
        argv, extra = argv[:i], argv[i + 1:]
    args = ap.parse_args(argv)

    if args.tool == "check":
        return check(args.tools)
    if args.tool == "blender":
        return run_blender(args, extra)

    def must_exist(paths):
        for path in paths:
            if not Path(path).is_file():
                raise SystemExit(f"input not found: {path}")

    req: dict = {"output": str(Path(args.output).resolve())}
    if args.tool in ("image-gen", "image-edit"):
        prompt = args.prompt if args.prompt is not None else Path(args.prompt_file).read_text(encoding="utf-8")
        if args.tool == "image-edit" and not args.reference:
            raise SystemExit("image-edit needs at least one --reference")
        must_exist(args.reference)
        size_for(args.aspect, 0)
        req.update({"prompt": prompt.strip(), "references": [str(Path(r).resolve()) for r in args.reference],
                    "aspect": args.aspect, "quality": args.quality, "transparent": args.transparent})
        if args.prompt_file:
            req["prompt_file"] = str(Path(args.prompt_file).resolve())
    else:
        views = {v: str(Path(getattr(args, v)).resolve()) for v in VIEWS if getattr(args, v)}
        if views and args.image:
            raise SystemExit("use either --image or --front/--left/--back/--right")
        if views and "front" not in views:
            raise SystemExit("multiview generation needs --front")
        if not views and len(args.image) != 1 and not args.resume:
            raise SystemExit("give one --image, or --front plus other views")
        must_exist([*args.image, *views.values()])
        req.update({"images": [str(Path(i).resolve()) for i in args.image], "views": views,
                    "faces": args.faces, "texture": not args.no_texture, "resume": args.resume})
    return run(args.tool, req, args)


if __name__ == "__main__":
    sys.exit(main())
