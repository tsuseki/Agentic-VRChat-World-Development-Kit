"""Off-is-identical proof for a new builder option: build unrelated trees with the committed (HEAD) kit scripts and with
the working copy, then compare the FBXs vertex by vertex (fbx_compare.py). Run from the workspace root:
    python .omp/skills/lowpoly-tree-generation/scripts/kit_option_check.py <work_dir> <Name>:<tex_dir>:<config.py> [...]
           [--extra "<builder args>"]        (default --extra "--lod1")
Pick 3 species that do not set the new option and differ in form (e.g. a broadleaf, a rosette palm, a shrub).
Steps: `git -C .omp show HEAD:<file>` for every tracked file under skills/lowpoly-tree-generation/scripts into
<work_dir>/kit_head/ (same relative layout); each tree built twice through `tool.py blender` into <work_dir>/head/<Name>
and <work_dir>/new/<Name>; fbx_compare.py on every FBX pair.
PASS = every pair `moved_verts 0`, every uv / col diff 0 and `topology_same Y`; normal_max_deg ~0.04 is import noise.
Prints the FBXCMP lines and KITCHECK PASS|FAIL. Headless Blender exits 0 on a Python traceback, so the build output is
checked for `Traceback` and `FAMILY_OK`.
"""
import os, re, shlex, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_REL = "skills/lowpoly-tree-generation/scripts"
KIT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))          # the .omp repo
TOOL = [sys.executable, os.path.join(KIT, "scripts", "tool.py"), "blender"]


def git(*a):
    return subprocess.run(["git", "-C", KIT, *a], capture_output=True, check=True).stdout


def export_head(dst):
    for rel in git("ls-files", SKILL_REL).decode().split():
        out = os.path.join(dst, os.path.relpath(rel, SKILL_REL))
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "wb") as f:
            f.write(git("show", f"HEAD:{rel}"))


def build(kit_dir, name, tex, cfg, out, extra):
    os.makedirs(out, exist_ok=True)
    cmd = TOOL + ["--script", os.path.join(kit_dir, "tree_family_build.py"), "--", name, "--tex", os.path.abspath(tex),
                  "--out", out, "--blend", out, "--config", os.path.abspath(cfg), *extra]
    r = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
    log = r.stdout + r.stderr
    open(os.path.join(out, "build.log"), "w", encoding="utf-8").write(log)
    if r.returncode or "Traceback" in log or "FAMILY_OK" not in log:
        raise SystemExit(f"BUILD FAILED {kit_dir} {name}: see {out}/build.log")


def main():
    args = sys.argv[1:]; extra = ["--lod1"]
    if "--extra" in args:
        i = args.index("--extra"); extra = shlex.split(args[i + 1]); del args[i:i + 2]
    work, trees = os.path.abspath(args[0]), [t.split(":") for t in args[1:]]
    if not trees or any(len(t) != 3 for t in trees):
        raise SystemExit(__doc__)
    shutil.rmtree(work, ignore_errors=True)
    head = os.path.join(work, "kit_head"); export_head(head)
    pairs = []
    for name, tex, cfg in trees:
        for tag, kd in (("head", head), ("new", HERE)):
            build(kd, name, tex, cfg, os.path.join(work, tag, name), extra)
        hd = os.path.join(work, "head", name)
        for f in sorted(os.listdir(hd)):
            if f.lower().endswith(".fbx"):
                pairs += [os.path.join(hd, f), os.path.join(work, "new", name, f)]
    r = subprocess.run(TOOL + ["--script", os.path.join(HERE, "fbx_compare.py"), "--", *pairs],
                       capture_output=True, text=True, errors="replace")
    lines = [l for l in (r.stdout + r.stderr).splitlines() if l.startswith("FBXCMP")]
    ok = len(lines) == len(pairs) // 2 and bool(lines)
    for l in lines:
        print(l)
        diffs = re.findall(r":\s*([0-9.eE+-]+)[,}]", l.split("| uv", 1)[-1].split("| normal", 1)[0])
        if ("topology_same Y" not in l or "moved_verts 0 " not in l or "channels" in l
                or any(float(d) != 0.0 for d in diffs)):
            ok = False
    print("KITCHECK", "PASS" if ok else "FAIL", f"{len(lines)} pairs")


if __name__ == "__main__":
    main()
