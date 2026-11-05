#!/usr/bin/env python3
"""Decision database: every decision, steer and art pick the user makes for one project, searchable.

Database: <project>/STEER.jsonl, one JSON record per line, append-only (never rewritten by hand).
Generated views (rewritten on every write; never edit them):
  STEER.md        full history grouped by world part, superseded records folded away
  DECISIONS.md    what holds now: picked art, rejected art, the design lock, decisions by part.
                  The digest every agent and subagent reads before working on the project.
  DECISIONS.json  the same, machine form; the world-decisions omp extension matches `targets`
                  against tool calls and reminds the agent of the matching decisions.
Picked art: `pick` copies each image into <project>/Design/picks/ (rejected: Design/picks/rejected/)
so a liked image never gets lost in a generation folder.

Record fields
  id          S-0001 ...
  when        "YYYY-MM-DD HH:MM" local (use "~" prefix on the time when estimated)
  stage       pipeline stage (A.3, B.2, C.1 ...) or ""
  affects     WHERE: world parts from <project>/steer_parts.txt (floors, rooms, areas, systems)
  aspect      WHAT KIND: from .omp/templates/steer_aspects.txt (size, layout, design, style, materials,
              lighting, behaviour, audio, script, performance, process)
  targets     the concrete things it governs: object names, scene paths, scripts, assets; globs ok
              (Fumo_*, FumoScream.cs, WORLD/ROOMS/GYM/). Mentioning one in a tool call triggers a reminder.
  topic       stable kebab-case key for the subject; the latest record on a topic holds
  said        the user's exact words, verbatim
  images      image paths the user picked or pointed at (project-relative)
  pick        liked | rejected (art picks only); source = where the image was copied from; feel = what to take from it
  decision    what it means for the build, 1-2 sentences
  status      pending | in progress | done | applied
  supersedes  ids of earlier records on the same topic (filled automatically)
  refs        commits, briefs, files that carried it out

Commands
  add      --affects a,b --aspect x,y --topic t --said "..." [--said "..."] --decision "..."
           [--target T ...] [--stage] [--image p] [--status] [--when] [--ref] [--supersedes S-0012,S-0020]
  pick     --image p [--image p] --affects a --aspect style --topic t --said "..." --decision "..."
           [--reject] [--feel "..."] [--target T ...] ...   copies the art into Design/picks/ and records it
  tag      ID [--aspect x,y] [--affects a,b] [--target T ...]   labels an existing record (appends an update)
  status   ID --status s [--ref r]                              appends a status update (never edits)
  find     [--affects a] [--aspect x] [--target name] [--topic t] [--text words] [--image substr] [--since D] [--all]
  current  [--affects a] [--aspect x] [--target name]           what holds now
  topics                                                        topic -> latest id, count
  render                                                        rewrites STEER.md, DECISIONS.md, DECISIONS.json
Run from the project folder or pass --project.
"""
import argparse, datetime, fnmatch, json, pathlib, shutil, sys

KIT = pathlib.Path(__file__).resolve().parents[1]
TEMPLATES = KIT / "templates"
OPEN = {"pending", "in progress", "open", "queued"}


def stamp():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")


def load(f):
    if not f.exists():
        return []
    return [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]


def vocab(f):
    return [l.strip() for l in f.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]


def parts_of(pf):
    if not pf.exists():
        shutil.copy(TEMPLATES / "steer_parts.txt", pf)
        print(f"created {pf} from the kit template; add this project's own floors, rooms and areas", file=sys.stderr)
    return vocab(pf)


def split(s):
    return [x.strip() for x in (s or "").split(",") if x.strip()]


def check(values, allowed, label, where):
    bad = [x for x in values if x not in allowed]
    if bad:
        sys.exit(f"unknown {label} {bad}; allowed: {', '.join(allowed)} (add new ones to {where})")


def merged(recs):
    """Update records (status / tag) fold into their target; returns decision records only."""
    by = {r["id"]: dict(r) for r in recs if r.get("kind", "steer") == "steer"}
    for r in recs:
        if r.get("kind") == "update" and r.get("target") in by:
            t = by[r["target"]]
            for k in ("status", "aspect", "affects", "targets"):
                if k in r:
                    t[k] = r[k]
            t["refs"] = t.get("refs", []) + r.get("refs", [])
    return list(by.values())


def when_key(r):
    """Sort key for `when`: an estimated time ("~09:30") sorts like the exact one."""
    return r["when"].replace("~", "")


def holds(recs):
    """What holds now: per topic, the newest record by `when` (file order breaks ties) among the records
    no other record lists in `supersedes`. Backfilled old records therefore never override newer ones."""
    retired = {s for r in recs for s in r.get("supersedes", [])}
    latest = {}
    for r in recs:
        if r["id"] in retired:
            continue
        cur = latest.get(r["topic"])
        if cur is None or when_key(r) >= when_key(cur):
            latest[r["topic"]] = r
    return set(id(r) for r in latest.values()), latest


def hits_target(r, name):
    n = name.lower()
    return any(fnmatch.fnmatch(n, p.lower()) or n in p.lower() for p in r.get("targets", []))


def labels(r):
    bits = [", ".join(r.get("aspect", [])) or "no aspect", ", ".join(r["affects"])]
    if r.get("stage"):
        bits.append(r["stage"])
    return " · ".join(bits)


def line(r, now=True):
    imgs = f" · images: {', '.join(r['images'])}" if r.get("images") else ""
    pick = f" · **{r['pick']} art**" if r.get("pick") else ""
    tg = f"\n  - targets: {', '.join(f'`{t}`' for t in r['targets'])}" if r.get("targets") else ""
    said = " / ".join(f"“{s}”" for s in r["said"])
    tag = "" if now else " ~~(superseded)~~"
    return (f"- **{r['id']}** {r['when']} · `{r['topic']}` · {labels(r)}{pick}{tag}"
            f"\n  - said: {said}{imgs}{tg}\n  - means: {r['decision']} ({r.get('status', '')})")


def next_id(recs):
    return f"S-{sum(1 for r in recs if r.get('kind', 'steer') == 'steer') + 1:04d}"


def append(jf, rec):
    with jf.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


def new_record(args, recs, pf, rid, images, extra):
    aff = split(args.affects)
    check(aff, parts_of(pf), "world part(s)", pf.name)
    asp = split(args.aspect)
    check(asp, vocab(TEMPLATES / "steer_aspects.txt"), "aspect(s)", ".omp/templates/steer_aspects.txt")
    known = {r["id"] for r in merged(recs)}
    extra_sup = split(args.supersedes)
    if [x for x in extra_sup if x not in known]:
        sys.exit(f"unknown ids in --supersedes: {[x for x in extra_sup if x not in known]}")
    when = args.when or stamp()
    # Only records at or before this one's time are replaced: a backfilled old decision never retires a newer one.
    prev = [r["id"] for r in merged(recs)
            if r["topic"] == args.topic and when_key(r) <= when.replace("~", "")] + extra_sup
    rec = {"kind": "steer", "id": rid, "when": when, "stage": args.stage,
           "affects": aff, "aspect": asp, "targets": args.target, "topic": args.topic, "said": args.said,
           "images": images, "decision": args.decision, "status": args.status, "supersedes": prev, "refs": args.ref}
    rec.update(extra)
    return rec


def copy_picks(root, rid, sources, rejected):
    dest = root / "Design" / "picks" / ("rejected" if rejected else "")
    dest.mkdir(parents=True, exist_ok=True)
    out = []
    for src in sources:
        s = pathlib.Path(src)
        s = (s if s.is_absolute() else root / s).resolve()
        if not s.is_file():
            sys.exit(f"image not found: {s}")
        if dest.resolve() in s.parents:
            d = s
        else:
            d = dest / f"{rid}_{s.name}"
            shutil.copy2(s, d)
        out.append(d.relative_to(root).as_posix())
    return out


def main():
    ap = argparse.ArgumentParser(description="Decision database for one project (see module docstring).")
    ap.add_argument("--project", default=".")
    sp = ap.add_subparsers(dest="cmd", required=True)

    def record_args(p):
        p.add_argument("--affects", required=True); p.add_argument("--aspect", required=True)
        p.add_argument("--topic", required=True); p.add_argument("--said", action="append", required=True)
        p.add_argument("--decision", required=True); p.add_argument("--target", action="append", default=[])
        p.add_argument("--stage", default=""); p.add_argument("--image", action="append", default=[])
        p.add_argument("--status", default="pending"); p.add_argument("--when")
        p.add_argument("--ref", action="append", default=[])
        p.add_argument("--supersedes", default="", help="comma-separated ids on other topics this record overrides")

    def filter_args(p):
        p.add_argument("--affects"); p.add_argument("--aspect"); p.add_argument("--target")

    record_args(sp.add_parser("add"))
    pk = sp.add_parser("pick"); record_args(pk)
    pk.add_argument("--reject", action="store_true", help="the user rejected this art: never build like it")
    pk.add_argument("--feel", default="", help="what to take from the image (or avoid, for --reject)")
    t = sp.add_parser("tag"); t.add_argument("id"); t.add_argument("--aspect"); t.add_argument("--affects")
    t.add_argument("--target", action="append")
    s = sp.add_parser("status"); s.add_argument("id"); s.add_argument("--status", required=True)
    s.add_argument("--ref", action="append", default=[])
    f = sp.add_parser("find"); filter_args(f)
    f.add_argument("--topic"); f.add_argument("--text"); f.add_argument("--image"); f.add_argument("--since")
    f.add_argument("--all", action="store_true", help="include superseded records")
    filter_args(sp.add_parser("current"))
    sp.add_parser("topics"); sp.add_parser("render")
    args = ap.parse_args()

    root = pathlib.Path(args.project).resolve()
    jf, pf = root / "STEER.jsonl", root / "steer_parts.txt"
    recs = load(jf)

    if args.cmd in ("add", "pick"):
        rid = next_id(recs)
        if args.cmd == "pick":
            images = copy_picks(root, rid, args.image, args.reject)
            extra = {"pick": "rejected" if args.reject else "liked", "source": args.image, "feel": args.feel}
        else:
            images, extra = args.image, {}
        rec = new_record(args, recs, pf, rid, images, extra)
        append(jf, rec)
        print(rec["id"], ("supersedes " + ", ".join(rec["supersedes"])) if rec["supersedes"] else "",
              ("images: " + ", ".join(images)) if args.cmd == "pick" else "")
        render(merged(load(jf)), root)
        return
    if args.cmd in ("tag", "status"):
        if args.id not in {r["id"] for r in merged(recs)}:
            sys.exit(f"unknown id {args.id}")
        up = {"kind": "update", "target": args.id, "when": stamp()}
        if args.cmd == "status":
            up.update(status=args.status, refs=args.ref)
        else:
            if args.aspect is not None:
                up["aspect"] = split(args.aspect)
                check(up["aspect"], vocab(TEMPLATES / "steer_aspects.txt"), "aspect(s)", "steer_aspects.txt")
            if args.affects is not None:
                up["affects"] = split(args.affects)
                check(up["affects"], parts_of(pf), "world part(s)", pf.name)
            if args.target is not None:
                up["targets"] = args.target
            if len(up) == 3:
                sys.exit("tag needs --aspect, --affects or --target")
        append(jf, up)
        render(merged(load(jf)), root)
        return

    recs = merged(recs)
    now_ids, latest = holds(recs)
    if args.cmd == "render":
        render(recs, root); print(root / "DECISIONS.md"); return
    if args.cmd == "topics":
        cnt = {}
        for r in recs:
            cnt[r["topic"]] = cnt.get(r["topic"], 0) + 1
        for tp, r in sorted(latest.items(), key=lambda kv: kv[1]["when"], reverse=True):
            print(f"{tp:28} {r['id']}  x{cnt[tp]}  {labels(r)}")
        return
    sel = [r for r in recs if args.cmd == "find" and args.all or id(r) in now_ids]
    if args.cmd == "find":
        if args.topic: sel = [r for r in sel if r["topic"] == args.topic]
        if args.image: sel = [r for r in sel if any(args.image.lower() in i.lower() for i in r.get("images", []))]
        if args.since: sel = [r for r in sel if r["when"] >= args.since]
        if args.text:
            words = args.text.lower().split()
            sel = [r for r in sel if all(w in json.dumps(r, ensure_ascii=False).lower() for w in words)]
    if args.affects: sel = [r for r in sel if args.affects in r["affects"]]
    if args.aspect: sel = [r for r in sel if args.aspect in r.get("aspect", [])]
    if args.target: sel = [r for r in sel if hits_target(r, args.target)]
    for r in sel:
        print(line(r, id(r) in now_ids))


def render(recs, root):
    now_ids, _ = holds(recs)
    parts = {}
    for r in recs:
        for p in r["affects"]:
            parts.setdefault(p, []).append(r)
    out = [f"# Steer log: {root.name}", "",
           "Generated from `STEER.jsonl` by `python .omp/scripts/steer.py render`. Never edit by hand; add with `steer.py add` / `pick`.",
           "The latest record on a topic holds (user: \"if I comment on the same thing my last thing holds\"). "
           "What holds now, compact: `DECISIONS.md`.", ""]
    for p in sorted(parts):
        rs = sorted(parts[p], key=lambda r: r["when"], reverse=True)
        out.append(f"## {p}")
        out += [line(r, True) for r in rs if id(r) in now_ids]
        old = [r for r in rs if id(r) not in now_ids]
        if old:
            out.append(f"<details><summary>{len(old)} superseded</summary>\n")
            out += [line(r, False) for r in old]
            out.append("\n</details>")
        out.append("")
    (root / "STEER.md").write_text("\n".join(out), encoding="utf-8")
    render_decisions([r for r in recs if id(r) in now_ids], root)


def render_decisions(cur, root):
    cur = sorted(cur, key=lambda r: r["when"], reverse=True)

    def ab(rel):
        return str((root / rel).resolve())

    def said(r, limit=320):
        s = " / ".join(f"“{x}”" for x in r["said"])
        return s if len(s) <= limit else s[:limit].rstrip() + "…”"

    def tail(r):
        bits = []
        if r.get("targets"):
            bits.append("targets: " + ", ".join(f"`{t}`" for t in r["targets"]))
        if r.get("status") in OPEN:
            bits.append(f"_{r['status']}_")
        return (" · " + " · ".join(bits)) if bits else ""

    def art(r):
        imgs = "\n".join(f"  - `{ab(i)}`" for i in r.get("images", []))
        feel = f" Take from it: {r['feel']}" if r.get("feel") else ""
        return (f"- **{r['topic']}** · {labels(r)} ({r['id']}, {r['when'][:10]}): {r['decision']}{feel}"
                f" — user: {said(r)}{tail(r)}\n{imgs}")

    liked = [r for r in cur if r.get("pick") == "liked"]
    rejected = [r for r in cur if r.get("pick") == "rejected"]
    rest = [r for r in cur if not r.get("pick")]
    out = [f"# Decisions in force: {root.name}", "",
           "Generated from `STEER.jsonl` by `python .omp/scripts/steer.py render` (runs on every add, pick, tag and status). Never edit by hand.",
           "",
           "**Binding for every agent and subagent.** These are the user's own decisions. They override workspace defaults, "
           "skill defaults and briefs. Before working on a part of this world, read its section and open the picked art for it. "
           "If a task would contradict a decision, stop and ask the user (quiet hours: skip that item and report it). "
           "A change needs a new record in the user's words (`steer.py add` / `steer.py pick`). Full history: `STEER.md`. "
           "Search: `steer.py find --affects <part> --aspect <kind> --target <object|script>`.", ""]
    if liked:
        out += ["## Art the user picked", "Build to these. Open the images for the part you work on before building, briefing or reviewing.", ""]
        out += [art(r) for r in liked] + [""]
    lock = root / "Design" / "lock" / "lock.json"
    if lock.exists():
        out += ["## Design lock", f"From `{lock}`.", ""]
        for e in json.loads(lock.read_text(encoding="utf-8")):
            words = f" — user: “{e['user_words']}”" if e.get("user_words") else ""
            out.append(f"- `{lock.parent / e['file']}` — {e.get('caption', '')}{words}")
        out.append("")
    if rejected:
        out += ["## Art the user rejected", "Never build like these.", ""]
        out += [art(r) for r in rejected] + [""]
    by_part = {}
    for r in rest:
        by_part.setdefault(r["affects"][0] if r["affects"] else "unsorted", []).append(r)
    if by_part:
        out += ["## Decisions by part", "Each decision is listed once, under its first part; its labels name every part it affects.", ""]
        for p in sorted(by_part):
            out.append(f"### {p}")
            for r in by_part[p]:
                imgs = (" · images: " + ", ".join(f"`{ab(i)}`" for i in r["images"])) if r.get("images") else ""
                out.append(f"- **{r['topic']}** · {labels(r)} ({r['id']}, {r['when'][:10]}): {r['decision']}"
                           f" — user: {said(r)}{imgs}{tail(r)}")
            out.append("")
    (root / "DECISIONS.md").write_text("\n".join(out), encoding="utf-8")
    machine = {"project": root.name, "generated": stamp(), "records": [
        {"id": r["id"], "when": r["when"], "topic": r["topic"], "affects": r["affects"], "aspect": r.get("aspect", []),
         "targets": r.get("targets", []), "pick": r.get("pick", ""), "decision": r["decision"], "said": said(r, 240),
         "images": [ab(i) for i in r.get("images", [])], "status": r.get("status", "")} for r in cur]}
    (root / "DECISIONS.json").write_text(json.dumps(machine, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
