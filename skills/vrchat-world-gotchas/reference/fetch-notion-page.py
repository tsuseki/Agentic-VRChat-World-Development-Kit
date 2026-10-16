import json, sys, time, urllib.request

API = "https://hai-vr.notion.site/api/v3/loadPageChunk"

def post(payload):
    req = urllib.request.Request(API, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json",
                 "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())

blocks = {}

def load_page(pid):
    cursor = {"stack": []}
    chunk = 0
    while True:
        d = post({"pageId": pid, "limit": 200, "cursor": cursor,
                  "chunkNumber": chunk, "verticalColumns": False})
        rm = d.get("recordMap", {}).get("block", {})
        for k, v in rm.items():
            val = v.get("value", {})
            val = val.get("value", val)
            if val:
                blocks[k] = val
        cursor = d.get("cursor", {"stack": []})
        if not cursor.get("stack"):
            break
        chunk += 1
        time.sleep(0.2)

def rich(props, key="title"):
    arr = (props or {}).get(key)
    if not arr:
        return ""
    out = []
    for seg in arr:
        t = seg[0] if seg else ""
        fmts = seg[1] if len(seg) > 1 and seg[1] else []
        link = None
        code = False
        bold = False
        for f in fmts:
            if f[0] == "a":
                link = f[1]
            elif f[0] == "c":
                code = True
            elif f[0] == "b":
                bold = True
        if t == "⁣":  # inline mention placeholder
            for f in fmts:
                if f[0] in ("p", "u"):
                    t = "[[link:%s]]" % f[1]
        if code:
            t = "`%s`" % t
        if bold:
            t = "**%s**" % t
        if link:
            t = "[%s](%s)" % (t, link)
        out.append(t)
    return "".join(out)

MAP = {
    "header": "## ", "sub_header": "### ", "sub_sub_header": "#### ",
    "bulleted_list": "- ", "numbered_list": "1. ", "toggle": "- (toggle) ",
    "quote": "> ", "callout": "> [!] ", "to_do": "- [ ] ",
}

seen = set()

def render(bid, depth=0, out=None):
    if out is None:
        out = []
    if bid in seen:
        return out
    seen.add(bid)
    b = blocks.get(bid)
    if not b:
        return out
    t = b.get("type")
    props = b.get("properties", {})
    ind = "  " * depth
    txt = rich(props)
    if t == "page":
        out.append("\n# %s\n" % txt)
    elif t in MAP:
        out.append(ind + MAP[t] + txt)
    elif t == "text":
        out.append(ind + txt if txt else "")
    elif t == "code":
        lang = rich(props, "language") or ""
        out.append("%s```%s\n%s\n%s```" % (ind, lang, txt, ind))
    elif t == "divider":
        out.append("\n---\n")
    elif t in ("image", "video", "file", "embed"):
        src = rich(props, "source")
        cap = rich(props, "caption")
        out.append("%s[%s: %s] %s" % (ind, t, src, cap))
    elif t == "bookmark":
        out.append("%s[bookmark] %s %s" % (ind, rich(props, "link"), txt))
    elif t in ("column_list", "column"):
        pass
    elif t == "table_of_contents":
        pass
    else:
        if txt:
            out.append("%s(%s) %s" % (ind, t, txt))
    kids = b.get("content", []) or []
    nd = depth + (0 if t in ("page", "column_list", "column", "header", "sub_header", "sub_sub_header") else 1)
    for k in kids:
        if k not in blocks:
            load_page(k)
        render(k, nd, out)
    return out

if __name__ == "__main__":
    pid, dest = sys.argv[1], sys.argv[2]
    load_page(pid)
    lines = render(pid)
    open(dest, "w", encoding="utf-8").write("\n".join(lines))
    print("blocks=%d lines=%d -> %s" % (len(blocks), len(lines), dest))
