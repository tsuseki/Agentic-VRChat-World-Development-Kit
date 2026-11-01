"""Offline Unity scene YAML summary, read-only: top-level roots, and per second-level path the prefab-instance counts
by source prefab (names resolved through the project's .prefab.meta / .fbx.meta GUID map). ~2 s per scene.

Use it to plan while another agent owns the live editor; never edit scene YAML (drive the editor through MCP).

    python .omp/skills/unity-mcp-scripting/scripts/scene_tree.py <project>/Assets/<path>/<Scene>.unity
"""
import re, sys, collections, pathlib


def project_root(scene):
    p = pathlib.Path(scene).resolve()
    for d in p.parents:
        if (d / "Assets").is_dir() and (d / "ProjectSettings").is_dir():
            return d
    sys.exit("no Unity project (Assets + ProjectSettings) above " + str(p))


def guid_map(root):
    m = {}
    for p in (root / "Assets").rglob("*.prefab.meta"):
        g = re.search(r"guid: (\w+)", p.read_text(errors="ignore"))
        if g: m[g.group(1)] = p.name[:-12]
    for p in (root / "Assets").rglob("*.fbx.meta"):
        g = re.search(r"guid: (\w+)", p.read_text(errors="ignore"))
        if g: m[g.group(1)] = p.name[:-5]
    return m


def parse(path):
    txt = open(path, encoding="utf-8", errors="ignore").read()
    docs = re.split(r"\n--- !u!(\d+) &(\d+)( stripped)?\n", txt)
    objs = {}
    for i in range(1, len(docs) - 3, 4):
        cls, fid, stripped, body = docs[i], docs[i + 1], docs[i + 2], docs[i + 3]
        objs[fid] = (int(cls), bool(stripped), body)
    return objs


def main(path):
    gm = guid_map(project_root(path))
    objs = parse(path)
    name = {}; tr_go = {}; go_tr = {}; father = {}; pi_parent = {}; pi_src = {}; pi_name = {}; stripped_tr_pi = {}
    for fid, (cls, st, b) in objs.items():
        if cls == 1 and not st:
            m = re.search(r"m_Name: (.*)", b); name[fid] = m.group(1).strip() if m else "?"
        elif cls in (4, 224):
            g = re.search(r"m_GameObject: \{fileID: (\d+)", b); f = re.search(r"m_Father: \{fileID: (\d+)", b)
            if st:
                p = re.search(r"m_PrefabInstance: \{fileID: (\d+)", b)
                if p: stripped_tr_pi[fid] = p.group(1)
            else:
                if g: tr_go[fid] = g.group(1); go_tr[g.group(1)] = fid
                if f: father[fid] = f.group(1)
        elif cls == 1001:
            p = re.search(r"m_TransformParent: \{fileID: (\d+)", b); s = re.search(r"m_SourcePrefab: \{fileID: \d+, guid: (\w+)", b)
            n = re.search(r"propertyPath: m_Name\s+value: (.*)", b)
            pi_parent[fid] = p.group(1) if p else "0"; pi_src[fid] = gm.get(s.group(1), s.group(1)[:8]) if s else "?"
            pi_name[fid] = n.group(1).strip() if n else pi_src[fid]

    def tname(t):
        if t in tr_go: return name.get(tr_go[t], "?")
        if t in stripped_tr_pi: return pi_name.get(stripped_tr_pi[t], "?")
        return "?"

    def tpath(t, depth=0):
        if depth > 40: return "…"
        if t in father:
            f = father[t]
        elif t in stripped_tr_pi:
            f = pi_parent.get(stripped_tr_pi[t], "0")
        else:
            f = "0"
        return tname(t) if f == "0" else tpath(f, depth + 1) + "/" + tname(t)

    cnt = collections.defaultdict(collections.Counter)
    for pi, par in pi_parent.items():
        p = tpath(par) if par != "0" else "<root>"
        key = "/".join(p.split("/")[:2])
        cnt[key][pi_src[pi]] += 1
    roots = [tname(t) for t, f in father.items() if f == "0"] + [pi_name[p] for p, par in pi_parent.items() if par == "0"]
    print("ROOTS:", sorted(collections.Counter(roots).items()))
    for k in sorted(cnt):
        tot = sum(cnt[k].values())
        print(f"{k}: {tot} instances; top: {cnt[k].most_common(8)}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
