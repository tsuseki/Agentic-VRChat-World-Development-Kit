#!/usr/bin/env python3
"""Trial event log tools for the AWDK pipeline trial (stdlib only).

Append events (validates them, copies every referenced image into Trial/img/, stamps ts):
    python trial_report.py <project>/Trial --append event.json      # or "-" for stdin
    The input is one JSON object, a JSON array of objects, or JSON lines.

Render reports:
    python trial_report.py <project>/Trial                 -> Trial/report.html (whole trial)
    python trial_report.py <project>/Trial --stage C.1     -> Trial/checkpoints/stage-C1.html
    add --pdf to also print a PDF next to the HTML (headless Chrome)
    add --link to reference images in Trial/img/ instead of embedding them (smaller file)

Schema: .omp/skills/pipeline-trial/SKILL.md "Event log".
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import html
import json
import os
import shutil
import subprocess
import sys
import tempfile
from collections import OrderedDict, defaultdict
from pathlib import Path

REQUIRED = {
    "trial_start": ["kit_commit", "source", "preset"],
    "stage_start": ["stage", "name"],
    "stage_end": ["stage", "status"],
    "decision": ["stage", "id", "point", "chosen", "by", "reason"],
    "attempt": ["stage", "id", "what", "result"],
    "review": ["stage", "id", "reviewer", "verdict"],
    "user_verdict": ["stage", "ref", "agree"],
    "loop_back": ["stage", "id", "to", "reason"],
    "ledger": ["stage", "n", "what", "fix_target"],
    "lock_gap": ["stage", "question", "decided"],
    "timing": ["stage", "what", "seconds"],
    "checkpoint": ["stage", "report"],
}
FIX_KINDS = {"reviewer-criterion", "builder-rule", "gathering-question", "lock-item", "tool", "note", "skill"}
# Pipeline stage IDs (world-pipeline): A concept, B blueprint, C build, D finish.
DEFAULT_STAGES = [
    ("A.1", "Setup"), ("A.2", "Information gathering"), ("A.3", "Concept (shell + art)"),
    ("A.4", "Design Lock"), ("B.1", "Floor plan"), ("B.2", "Greybox"), ("C.1", "Build-out"),
    ("C.2", "Interactions & playability"), ("D.1", "Lighting"), ("D.2", "Performance"), ("D.3", "Ship"), ("D.4", "Retro"),
]


def sid(v) -> str:
    """Normalise a stage ID ('a.3', ' C.1 ') to the canonical form ('A.3', 'C.1')."""
    return str(v).strip().upper()


def _score_ok(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and 0 <= v <= 10


VERDICTS = {"SHIP IT", "MINOR FIXES", "NEEDS WORK", "RANKED"}
DEFAULT_CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp", ".gif": "image/gif"}
THUMB_PX = 960  # embedded preview width; full-size files stay linked


def _thumb(path: Path):
    """Small JPEG preview for embedding (Pillow if installed, else the original bytes)."""
    try:
        from io import BytesIO
        from PIL import Image
    except ImportError:
        return MIME.get(path.suffix.lower(), "application/octet-stream"), path.read_bytes()
    im = Image.open(path)
    im.thumbnail((THUMB_PX, THUMB_PX))
    buf = BytesIO()
    im.convert("RGB").save(buf, "JPEG", quality=78)
    return "image/jpeg", buf.getvalue()


# ---------------------------------------------------------------- append

def _now() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def _parse_input(text: str) -> list[dict]:
    text = text.strip()
    if not text:
        return []
    try:
        data = json.loads(text)
        return data if isinstance(data, list) else [data]
    except json.JSONDecodeError:
        return [json.loads(line) for line in text.splitlines() if line.strip()]


def _validate(ev: dict) -> None:
    t = ev.get("type")
    if t not in REQUIRED:
        raise ValueError(f"unknown event type {t!r}; expected one of {sorted(REQUIRED)}")
    missing = [k for k in REQUIRED[t] if k not in ev]
    if missing:
        raise ValueError(f"{t} event missing {missing}: {json.dumps(ev)[:200]}")
    if t == "ledger":
        kind = ev["fix_target"].get("kind") if isinstance(ev["fix_target"], dict) else None
        if kind not in FIX_KINDS:
            raise ValueError(f"ledger fix_target.kind must be one of {sorted(FIX_KINDS)}")
    if t == "user_verdict" and not isinstance(ev["agree"], bool):
        raise ValueError("user_verdict.agree must be true or false")
    if t == "user_verdict" and "score" in ev and not _score_ok(ev["score"]):
        raise ValueError("user_verdict.score must be a number 0-10")
    if t == "review":
        if str(ev["verdict"]).upper() not in VERDICTS:
            raise ValueError(f"review.verdict must be one of {sorted(VERDICTS)}")
        if str(ev["verdict"]).upper() == "RANKED":
            opts = ev.get("option_scores")
            if not isinstance(opts, dict) or not opts or not all(_score_ok(v) for v in opts.values()):
                raise ValueError("a RANKED review needs option_scores {option id: score 0-10} for every option")
        elif not _score_ok(ev.get("score")):
            raise ValueError("review.score (0-10) is required")
        scores = ev.get("scores")
        if scores is not None and (not isinstance(scores, dict) or set(scores) - {"style", "build"}
                                   or not all(_score_ok(v) for v in scores.values())):
            raise ValueError("review.scores must be {style, build} with numbers 0-10")


def _copy_images(node, trial: Path, prefix: str, key: str | None = None):
    """Copy every path under an `images` list or an `img` field into trial/img/; return the node with relative paths."""
    if isinstance(node, dict):
        return {k: _copy_images(v, trial, prefix, k) for k, v in node.items()}
    if isinstance(node, list):
        if key == "images":
            return [_copy_one(p, trial, prefix) for p in node]
        return [_copy_images(v, trial, prefix) for v in node]
    if key == "img" and isinstance(node, str):
        return _copy_one(node, trial, prefix)
    return node


def _copy_one(path: str, trial: Path, prefix: str) -> str:
    src = Path(path)
    if not src.is_absolute():
        src = trial / src
    src = src.resolve()
    img_dir = (trial / "img").resolve()
    if src.parent == img_dir and src.exists():
        return f"img/{src.name}"
    if not src.exists():
        raise FileNotFoundError(f"image not found: {path}")
    img_dir.mkdir(parents=True, exist_ok=True)
    dest = img_dir / f"{prefix}_{src.name}"
    i = 2
    while dest.exists():
        dest = img_dir / f"{prefix}_{src.stem}-{i}{src.suffix}"
        i += 1
    shutil.copy2(src, dest)
    return f"img/{dest.name}"


def append(trial: Path, source: str) -> int:
    text = sys.stdin.read() if source == "-" else Path(source).read_text(encoding="utf-8")
    events = _parse_input(text)
    for ev in events:
        _validate(ev)
    trial.mkdir(parents=True, exist_ok=True)
    lines = []
    for ev in events:
        ev.setdefault("ts", _now())
        stage = ev.get("stage")
        prefix = ("s" + sid(stage).replace(".", "") if stage is not None else "s__") + "_" + str(ev.get("id") or ev.get("n") or ev["type"])
        lines.append(json.dumps(_copy_images(ev, trial, prefix), ensure_ascii=False))
    with open(trial / "log.jsonl", "a", encoding="utf-8") as f:
        f.write("".join(line + "\n" for line in lines))
    print(f"appended {len(lines)} event(s) to {trial / 'log.jsonl'}")
    return 0


# ---------------------------------------------------------------- model

def _ts(s):
    if not s:
        return None
    try:
        return dt.datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except ValueError:
        return None


def _dur(seconds) -> str:
    if seconds is None:
        return ""
    seconds = int(round(seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}h {m:02d}m" if h else (f"{m}m {s:02d}s" if m else f"{s}s")


def classify(value) -> str:
    v = str(value).strip().upper()
    if v in ("PASS", "OK", "DONE", "AGREE") or "SHIP IT" in v:
        return "pass"
    if v in ("RANKED", "RANK", "INFO"):
        return "info"
    if v in ("PARTIAL", "IN PROGRESS", "RUNNING"):
        return "warn"
    return "fail"


class Trial:
    def __init__(self, trial_dir: Path):
        self.dir = trial_dir
        self.warnings: list[str] = []
        self.events: list[dict] = []
        log = trial_dir / "log.jsonl"
        if not log.exists():
            raise SystemExit(f"no log at {log}")
        for i, line in enumerate(log.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                ev = json.loads(line)
                _validate(ev)
                self.events.append(ev)
            except (json.JSONDecodeError, ValueError) as e:
                self.warnings.append(f"log.jsonl line {i} skipped: {e}")
        self.meta = next((e for e in self.events if e["type"] == "trial_start"), {})
        self.stages: "OrderedDict[str, dict]" = OrderedDict()
        for s in self.meta.get("stages") or [{"n": n, "name": name} for n, name in DEFAULT_STAGES]:
            self._stage(s["n"], s.get("name"))
        self.reviews, self.decisions = {}, {}
        self.ledger: "OrderedDict[str, dict]" = OrderedDict()
        self.lock_gaps: list[dict] = []
        for ev in self.events:
            t = ev["type"]
            if "stage" not in ev:
                continue
            st = self._stage(ev["stage"], ev.get("name") if t == "stage_start" else None)
            st["events"].append(ev)
            if t == "stage_start":
                st["start"] = st["start"] or _ts(ev.get("ts"))
                st["status"] = st["status"] if st["status"] in ("done", "blocked") else "running"
            elif t == "stage_end":
                st["end"] = _ts(ev.get("ts"))
                st["status"] = ev["status"]
                st["summary"] = ev.get("summary", st["summary"])
            elif t == "review":
                self.reviews[ev["id"]] = ev
                if str(ev["verdict"]).upper() == "SHIP IT":
                    bad = [f for f in ev.get("findings", []) if str(f.get("severity", "")).lower() in ("blocker", "should-fix")]
                    if bad or (_score_ok(ev.get("score")) and ev["score"] < 8):
                        self.warnings.append(f"review {ev['id']}: SHIP IT needs score >= 8 and no blocker/should-fix finding")
            elif t == "loop_back":
                target = self._stage(ev["to"])
                target["events"].append(dict(ev, mirrored=True))
                target["status"], target["end"] = "running", None  # reopened until its next stage_end
            elif t == "decision":
                self.decisions[ev["id"]] = ev
            elif t == "ledger":
                key = str(ev["n"])
                merged = dict(self.ledger.get(key, {}))
                merged.update({k: v for k, v in ev.items() if v not in (None, "", [])})
                self.ledger[key] = merged
            elif t == "lock_gap":
                self.lock_gaps.append(ev)
            elif t == "checkpoint":
                st["checkpoint"] = ev
        self.agreement = self._agreement()

    def _stage(self, n, name=None):
        n = sid(n)
        if n not in self.stages:
            self.stages[n] = {"n": n, "name": name or f"Stage {n}", "status": "pending", "start": None,
                              "end": None, "summary": "", "events": [], "checkpoint": None}
        elif name:
            self.stages[n]["name"] = name
        return self.stages[n]

    def _agreement(self) -> list[dict]:
        """One record per judged reviewer decision.

        A user pick with `reviewer_pick` counts as matched when chosen == reviewer_pick. An explicit
        user_verdict on the same review (decision.review) or on the decision itself replaces that record.
        """
        recs: "OrderedDict[str, dict]" = OrderedDict()
        for ev in self.events:
            if ev["type"] == "decision" and ev.get("by") == "user" and ev.get("reviewer_pick") is not None:
                recs[ev.get("review") or ev["id"]] = {"stage": sid(ev["stage"]), "reviewer": ev.get("reviewer", "reviewer"),
                                                     "match": str(ev["chosen"]) == str(ev["reviewer_pick"])}
        for ev in self.events:
            if ev["type"] != "user_verdict":
                continue
            target = self.reviews.get(ev["ref"]) or self.decisions.get(ev["ref"])
            if target is None:
                self.warnings.append(f"user_verdict ref {ev['ref']!r} matches no review or decision")
                continue
            key = target.get("review") if target["type"] == "decision" and target.get("review") in recs else ev["ref"]
            reviewer = target.get("reviewer") or target.get("by", "agent")
            recs[key] = {"stage": sid(ev["stage"]), "reviewer": reviewer, "match": ev["agree"],
                         "user_score": ev.get("score"), "reviewer_score": target.get("score")}
        return list(recs.values())

    def rate(self, stage=None, reviewer=None):
        rows = [a for a in self.agreement if (stage is None or a["stage"] == stage) and (reviewer is None or a["reviewer"] == reviewer)]
        return (sum(a["match"] for a in rows), len(rows))


# ---------------------------------------------------------------- render

CSS = """
:root{--ok:#1f8a4c;--okbg:#e9f7ef;--bad:#c0392b;--badbg:#fdecea;--warn:#b7791f;--warnbg:#fff7e6;--info:#2b6cb0;--infobg:#ebf4ff;
--ink:#1d2330;--mute:#6b7385;--line:#e3e6ee;--card:#fff;--bg:#f5f6fa}
*{box-sizing:border-box}body{margin:0;font:14px/1.5 "Segoe UI",system-ui,-apple-system,sans-serif;color:var(--ink);background:var(--bg)}
main{max-width:1100px;margin:0 auto;padding:28px 24px 60px}
h1{font-size:26px;margin:0 0 4px}h2{font-size:20px;margin:0}h3{font-size:15px;margin:22px 0 8px;color:#39404f;text-transform:uppercase;letter-spacing:.04em;break-after:avoid}tr{break-inside:avoid}
.sub{color:var(--mute);margin:0 0 18px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:16px 0 22px}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px 14px}.kpi b{display:block;font-size:22px}.kpi span{color:var(--mute);font-size:12px}
.progress{display:flex;gap:3px;margin:8px 0 6px}.seg{flex:1;min-width:0;border-radius:6px;padding:7px 6px;font-size:11px;line-height:1.25;color:#fff;background:#c3c8d4;text-decoration:none;overflow:hidden}
.seg b{display:block;font-size:13px}.seg.done{background:var(--ok)}.seg.blocked{background:var(--bad)}.seg.running{background:var(--warn)}.seg.current{outline:3px solid var(--ink);outline-offset:1px}
.legend{font-size:12px;color:var(--mute);margin-bottom:20px}
section.stage{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:20px 22px;margin:22px 0}
.stagehead{display:flex;justify-content:space-between;align-items:baseline;gap:12px;flex-wrap:wrap;border-bottom:1px solid var(--line);padding-bottom:10px}
.badge{display:inline-block;border-radius:999px;padding:1px 10px;font-size:12px;font-weight:600;white-space:nowrap}
.b-pass{background:var(--okbg);color:var(--ok)}.b-fail{background:var(--badbg);color:var(--bad)}.b-warn{background:var(--warnbg);color:var(--warn)}.b-info{background:var(--infobg);color:var(--info)}.b-pending{background:#eef0f4;color:var(--mute)}
table{width:100%;border-collapse:collapse;font-size:13px}th,td{text-align:left;vertical-align:top;padding:6px 8px;border-bottom:1px solid var(--line)}th{color:var(--mute);font-weight:600;font-size:12px}
.timeline{border-left:3px solid var(--line);margin-left:6px;padding-left:16px}
.card{position:relative;border:1px solid var(--line);border-left:6px solid #c3c8d4;border-radius:8px;padding:10px 14px;margin:10px 0;background:#fff;break-inside:avoid}
.card:before{content:"";position:absolute;left:-26px;top:14px;width:11px;height:11px;border-radius:50%;background:#c3c8d4;border:2px solid var(--bg)}
.card.pass{border-left-color:var(--ok);background:var(--okbg)}.card.pass:before{background:var(--ok)}
.card.fail{border-left-color:var(--bad);background:var(--badbg)}.card.fail:before{background:var(--bad)}
.card.warn{border-left-color:var(--warn);background:var(--warnbg)}.card.warn:before{background:var(--warn)}
.card.info{border-left-color:var(--info);background:var(--infobg)}.card.info:before{background:var(--info)}
.cardhead{display:flex;justify-content:space-between;gap:10px}.cardhead .t{font-weight:600}.when{color:var(--mute);font-size:12px;white-space:nowrap}
.card ul{margin:6px 0 2px 18px;padding:0}.card li{margin:3px 0}.sev{font-size:11px;font-weight:700;text-transform:uppercase;margin-right:4px}
.sev-blocker{color:var(--bad)}.sev-should-fix{color:var(--warn)}.sev-nit{color:var(--mute)}
.thumbs{display:flex;flex-wrap:wrap;gap:8px;margin:8px 0 2px}.thumb{display:block;width:170px;text-decoration:none;color:var(--mute);font-size:11px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.thumb img{width:170px;height:106px;object-fit:cover;border-radius:6px;border:1px solid var(--line);display:block;background:#ddd}
.missing{width:170px;height:106px;border:1px dashed var(--bad);border-radius:6px;color:var(--bad);font-size:11px;padding:6px}
.agree{color:var(--ok);font-weight:700}.disagree{color:var(--bad);font-weight:700}.mute{color:var(--mute)}
.rate{font-size:13px}.warnbox{background:var(--warnbg);border:1px solid #f0d9a8;border-radius:8px;padding:8px 12px;font-size:12px}
#lb{display:none;position:fixed;inset:0;background:rgba(10,12,18,.88);z-index:9;align-items:center;justify-content:center;flex-direction:column;cursor:zoom-out}
#lb.on{display:flex}#lb img{max-width:94vw;max-height:88vh;border-radius:6px}#lb figcaption{color:#eee;margin-top:10px;font-size:13px}
@media print{body{background:#fff}main{max-width:none;padding:0}section.stage{border:none;padding:0}section.stage+section.stage,#ledger{break-before:page}
.seg,.card,.badge,.kpi{-webkit-print-color-adjust:exact;print-color-adjust:exact}#lb{display:none!important}.thumb img{width:150px;height:94px}.thumb{width:150px}}
@page{size:A4;margin:12mm}
"""

JS = """
document.addEventListener('click',function(e){var a=e.target.closest('a.thumb');if(!a)return;e.preventDefault();
var lb=document.getElementById('lb');lb.querySelector('img').src=a.querySelector('img').src;lb.querySelector('figcaption').textContent=a.title||'';lb.classList.add('on');});
document.getElementById('lb').addEventListener('click',function(){this.classList.remove('on');});
document.addEventListener('keydown',function(e){if(e.key==='Escape')document.getElementById('lb').classList.remove('on');});
"""


def esc(v) -> str:
    if v is None:
        return ""
    if isinstance(v, (list, tuple)):
        v = ", ".join(str(x) for x in v)
    return html.escape(str(v)).replace("\n", "<br>")


class Renderer:
    def __init__(self, trial: Trial, out: Path, embed: bool):
        self.t, self.out, self.embed = trial, out, embed

    def badge(self, text, cls=None):
        return f'<span class="badge b-{cls or classify(text)}">{esc(text)}</span>'

    def thumbs(self, images, caption=""):
        if not images:
            return ""
        parts = []
        for p in images:
            path = (self.t.dir / p).resolve()
            name = Path(p).name
            if not path.exists():
                self.t.warnings.append(f"missing image {p}")
                parts.append(f'<div class="missing">missing image<br>{esc(p)}</div>')
                continue
            rel = Path(os.path.relpath(path, self.out.parent)).as_posix()
            if self.embed:
                mime, blob = _thumb(path)
                src = f"data:{mime};base64,{base64.b64encode(blob).decode('ascii')}"
                href = rel  # click opens the full-size file next to the report
            else:
                src = href = rel
            title = f"{caption} — {name}" if caption else name
            parts.append(f'<a class="thumb" href="{esc(href)}" title="{esc(title)}"><img src="{src}" alt="{esc(name)}" loading="lazy">{esc(name)}</a>')
        return f'<div class="thumbs">{"".join(parts)}</div>'

    def when(self, ev):
        t = _ts(ev.get("ts"))
        return f'<span class="when">{t.strftime("%m-%d %H:%M")}</span>' if t else ""

    # -- blocks
    def header(self, stage=None):
        t, m = self.t, self.t.meta
        title = f"Checkpoint — stage {stage}: {esc(t.stages[stage]['name'])}" if stage is not None else "Pipeline trial report"
        project = m.get("project") or t.dir.resolve().parent.name
        info = " · ".join(x for x in [esc(project), f"kit {esc(m.get('kit_commit', '?'))}", esc(m.get("host")), esc(m.get("model")),
                                       f"source: {esc(m.get('source'))}", f"preset: {esc(m.get('preset'))}"] if x)
        stages = list(t.stages.values()) if stage is None else [t.stages[stage]]
        attempts = [e for s in stages for e in s["events"] if e["type"] in ("attempt", "review")]
        fails = sum(1 for e in attempts if classify(e.get("result") or e.get("verdict")) == "fail")
        passes = sum(1 for e in attempts if classify(e.get("result") or e.get("verdict")) == "pass")
        ok, n = t.rate(stage=stage)
        ledger = [l for l in t.ledger.values() if stage is None or sid(l["stage"]) == stage]
        gaps = [g for g in t.lock_gaps if stage is None or sid(g["stage"]) == stage]
        done = sum(1 for s in t.stages.values() if s["status"] == "done")
        kpis = [(f"{done}/{len(t.stages)}", "stages done"), (f"{fails} / {passes}", "failed / passed attempts"),
                (f"{100 * ok / n:.0f}%" if n else "—", f"agreement ({ok}/{n} reviewer decisions)"),
                (str(len(ledger)), "ledger entries"), (str(len(gaps)), "lock gaps")]
        cards = "".join(f'<div class="kpi"><b>{a}</b><span>{b}</span></div>' for a, b in kpis)
        gen = dt.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M")
        return f'<h1>{title}</h1><p class="sub">{info}<br>generated {gen}</p><div class="cards">{cards}</div>'

    def progress(self, current=None):
        segs = []
        for s in self.t.stages.values():
            cls = s["status"] if s["status"] in ("done", "blocked", "running") else ""
            cur = " current" if current == s["n"] else ""
            mark = " ✓" if s["checkpoint"] else ""
            href = f'#stage-{s["n"].replace(".", "")}' if current is None else "#"
            segs.append(f'<a class="seg {cls}{cur}" href="{href}" title="{esc(s["name"])} — {esc(s["status"])}"><b>{s["n"]}{mark}</b>{esc(s["name"])}</a>')
        return (f'<div class="progress">{"".join(segs)}</div><div class="legend">green done · amber running · red blocked · '
                f'grey pending · ✓ checkpoint reviewed by the user</div>')

    def agreement_table(self):
        t = self.t
        reviewers = sorted({a["reviewer"] for a in t.agreement})
        if not reviewers:
            return ""
        rows = []
        for r in reviewers:
            ok, n = t.rate(reviewer=r)
            per = " · ".join(f"{s}: {o}/{c}" for s in sorted({a['stage'] for a in t.agreement if a['reviewer'] == r})
                             for o, c in [t.rate(stage=s, reviewer=r)])
            diffs = [a["user_score"] - a["reviewer_score"] for a in t.agreement
                     if a["reviewer"] == r and _score_ok(a.get("user_score")) and _score_ok(a.get("reviewer_score"))]
            diff = f"{sum(diffs) / len(diffs):+.1f} (n={len(diffs)})" if diffs else "—"
            rows.append(f"<tr><td>{esc(r)}</td><td><b>{100 * ok / n:.0f}%</b> ({ok}/{n})</td><td>{diff}</td><td class='mute'>{per}</td></tr>")
        return ("<h3>Agreement with the user, per reviewer</h3><table><tr><th>Reviewer</th><th>Rate</th>"
                "<th>User − reviewer score (mean)</th><th>Per stage (matched/total)</th></tr>"
                + "".join(rows) + "</table>")

    def decisions(self, s):
        rows = []
        for e in s["events"]:
            if e["type"] != "decision":
                continue
            opts = []
            for o in e.get("options", []):
                label = o.get("label", o.get("id", "")) if isinstance(o, dict) else o
                oid = o.get("id") if isinstance(o, dict) else o
                mark = "<b>" if str(oid) == str(e["chosen"]) else ""
                opts.append(f"{mark}{esc(oid)}: {esc(label)}{'</b>' if mark else ''}")
            pick = f"<br><span class='mute'>reviewer pick: {esc(e['reviewer_pick'])}</span>" if e.get("reviewer_pick") is not None else ""
            words = f"<br><span class='mute'>“{esc(e['user_words'])}”</span>" if e.get("user_words") else ""
            imgs = [o["img"] for o in e.get("options", []) if isinstance(o, dict) and o.get("img")] + e.get("images", [])
            rows.append(f"<tr><td><b>{esc(e['point'])}</b><br>{esc(e.get('question'))}</td><td>{'<br>'.join(opts)}</td>"
                        f"<td><b>{esc(e['chosen'])}</b>{pick}</td><td>{esc(e['by'])}</td><td>{esc(e['reason'])}{words}{self.thumbs(imgs, e['point'])}</td></tr>")
        if not rows:
            return ""
        return ("<h3>Decisions</h3><table><tr><th>Point</th><th>Options</th><th>Chosen</th><th>By</th><th>Reason</th></tr>"
                + "".join(rows) + "</table>")

    def card(self, e):
        t = e["type"]
        if t == "attempt":
            cls = classify(e["result"])
            body = (f"<div>{esc(e.get('detail'))}</div>" if e.get("detail") else "") + self.thumbs(e.get("images"), e["what"])
            rnd = f" · round {esc(e['round'])}" if e.get("round") else ""
            return (f'<div class="card {cls}"><div class="cardhead"><span class="t">Attempt: {esc(e["what"])}{rnd}</span>'
                    f'<span>{self.badge(e["result"], cls)} {self.when(e)}</span></div><div class="mute">{esc(e.get("agent"))}</div>{body}</div>')
        if t == "review":
            cls = classify(e["verdict"])
            parts = []
            if e.get("target"):
                parts.append(f"<div class='mute'>target: {esc(e['target'])}</div>")
            if e.get("summary"):
                parts.append(f"<div>{esc(e['summary'])}</div>")
            if e.get("ranking"):
                parts.append(f"<div><b>Ranking:</b> {esc(' > '.join(str(x) for x in e['ranking']))}</div>")
            if e.get("passed_because"):
                parts.append("<div><b>Passed because</b><ul>" + "".join(f"<li>{esc(r)}</li>" for r in e["passed_because"]) + "</ul></div>")
            if e.get("findings"):
                items = []
                for f in e["findings"]:
                    sev = str(f.get("severity", "")).lower()
                    sec = f" <span class='mute'>({esc(f['section'])})</span>" if f.get("section") else ""
                    fix = f"<br><span class='mute'>fix: {esc(f['fix'])}</span>" if f.get("fix") else ""
                    items.append(f"<li><span class='sev sev-{esc(sev)}'>{esc(sev)}</span><b>#{esc(f.get('n'))} {esc(f.get('title'))}</b>{sec}"
                                 f"<br>{esc(f.get('reason'))}{fix}{self.thumbs(f.get('images'), f.get('title', ''))}</li>")
                parts.append("<div><b>Findings</b><ul>" + "".join(items) + "</ul></div>")
            parts.append(self.thumbs(e.get("images"), e["reviewer"]))
            if e.get("report_path"):
                parts.append(f"<div class='mute'>report: {esc(e['report_path'])}</div>")
            rnd = f" · round {esc(e['round'])}" if e.get("round") else ""
            if e.get("option_scores"):
                parts.insert(0, "<div><b>Scores:</b> " + " · ".join(f"{esc(k)} {esc(v)}/10" for k, v in e["option_scores"].items()) + "</div>")
            score = self.score_text(e)
            if score:
                parts.insert(0, f"<div><b>{score}</b></div>")
            return (f'<div class="card {cls}"><div class="cardhead"><span class="t">Review: {esc(e["reviewer"])}'
                    f'{" (" + esc(e["mode"]) + ")" if e.get("mode") else ""}{rnd}</span><span>{self.badge(e["verdict"], cls)} {self.when(e)}</span></div>'
                    + "".join(parts) + "</div>")
        if t == "lock_gap":
            return (f'<div class="card warn"><div class="cardhead"><span class="t">Lock gap: {esc(e["question"])}</span>{self.when(e)}</div>'
                    f'<div>decided: {esc(e["decided"])} <span class="mute">by {esc(e.get("by", "agent"))}</span></div>'
                    f'<div class="mute">proposed A.2 question: {esc(e.get("intake_question"))}</div></div>')
        if t == "timing":
            return f'<div class="card"><div class="cardhead"><span class="t">{esc(e["what"])}</span><span>{_dur(e["seconds"])} {self.when(e)}</span></div></div>'
        if t == "loop_back":
            redo = f"<div class='mute'>D steps to redo: {esc(e.get('redo'))}</div>" if e.get("redo") else ""
            ref = f"<div class='mute'>raised by: {esc(e['ref'])}</div>" if e.get("ref") else ""
            return (f'<div class="card warn"><div class="cardhead"><span class="t">Loop back {esc(e["stage"])} → {esc(e["to"])}</span>'
                    f'{self.when(e)}</div><div>{esc(e["reason"])}</div>{ref}{redo}</div>')
        return ""

    @staticmethod
    def score_text(e) -> str:
        parts = []
        if _score_ok(e.get("score")):
            parts.append(f"Score {e['score']}/10")
        sc = e.get("scores") or {}
        if sc:
            parts.append(" · ".join(f"{k.capitalize()} {v}/10" for k, v in sc.items()))
        return esc(" · ".join(parts))

    def timeline(self, s):
        cards = [self.card(e) for e in s["events"] if e["type"] in ("attempt", "review", "lock_gap", "timing", "loop_back")]
        return f'<h3>Timeline</h3><div class="timeline">{"".join(cards)}</div>' if cards else ""

    def score_trend(self, s):
        """Reviewer scores per target across passes (rounds), oldest first."""
        series: "OrderedDict[tuple, list]" = OrderedDict()
        for e in s["events"]:
            if e["type"] == "review" and _score_ok(e.get("score")):
                series.setdefault((e["reviewer"], e.get("target") or ""), []).append(e)
        if not series:
            return ""
        rows = []
        for (rev, target), evs in series.items():
            steps = " → ".join(f"{esc(e['score'])}" + (f" <span class='mute'>(S{esc(e['scores'].get('style', '–'))}/B{esc(e['scores'].get('build', '–'))})</span>"
                                                     if e.get("scores") else "") for e in evs)
            delta = evs[-1]["score"] - evs[0]["score"]
            rows.append(f"<tr><td>{esc(rev)}</td><td>{esc(target)}</td><td>{len(evs)}</td><td>{steps}</td>"
                        f"<td>{delta:+g}</td><td>{self.badge(evs[-1]['verdict'])}</td></tr>")
        return ("<h3>Score trend across passes</h3><table><tr><th>Reviewer</th><th>Target</th><th>Passes</th>"
                "<th>Score per pass (style/build)</th><th>Change</th><th>Last verdict</th></tr>" + "".join(rows) + "</table>")

    def verdicts(self, s):
        rows = []
        for e in s["events"]:
            if e["type"] != "user_verdict":
                continue
            tgt = self.t.reviews.get(e["ref"]) or self.t.decisions.get(e["ref"]) or {}
            what = f"{esc(tgt.get('reviewer') or tgt.get('point') or '?')}: {esc(tgt.get('verdict') or tgt.get('chosen') or '')}"
            ag = '<span class="agree">agree</span>' if e["agree"] else '<span class="disagree">disagree</span>'
            fnd = ""
            if e.get("findings"):
                fnd = "<br>" + "; ".join(f"#{esc(f.get('n'))} {'agree' if f.get('agree') else 'disagree'}{': ' + esc(f.get('note')) if f.get('note') else ''}"
                                         for f in e["findings"])
            words = f"<br><span class='mute'>“{esc(e['user_words'])}”</span>" if e.get("user_words") else ""
            us, rs = e.get("score"), tgt.get("score")
            sc = ""
            if _score_ok(us):
                sc = f"<br>user {esc(us)}/10" + (f" vs reviewer {esc(rs)}/10 (<b>{us - rs:+g}</b>)" if _score_ok(rs) else "")
            rows.append(f"<tr><td>{esc(e['ref'])}<br><span class='mute'>{what}</span></td><td>{ag}{sc}{fnd}</td><td>{esc(e.get('change'))}</td>"
                        f"<td>{esc(e.get('worked_well'))}{words}</td></tr>")
        ok, n = self.t.rate(stage=s["n"])
        rate = f'<p class="rate">Agreement this stage: <b>{100 * ok / n:.0f}%</b> ({ok}/{n} reviewer decisions matched the user)</p>' if n else ""
        if not rows:
            return rate and f"<h3>User verdicts</h3>{rate}"
        return ("<h3>User verdicts</h3>" + rate + "<table><tr><th>On</th><th>Verdict</th><th>What to change</th><th>What worked well</th></tr>"
                + "".join(rows) + "</table>")

    def ledger(self, stage=None):
        rows = []
        for l in self.t.ledger.values():
            if stage is not None and sid(l["stage"]) != stage:
                continue
            ft = l["fix_target"]
            target = f"<b>{esc(ft.get('kind'))}</b><br>{esc(ft.get('file'))}<br><span class='mute'>{esc(ft.get('change'))}</span>"
            status = l.get("status", "open")
            commit = f"<br><span class='mute'>{esc(l['commit'])}</span>" if l.get("commit") else ""
            rows.append(f"<tr><td>{esc(l['n'])}</td><td>{esc(l['stage'])}</td><td>{esc(l['what'])}{self.thumbs(l.get('images'), 'evidence')}"
                        f"<div class='mute'>{esc(l.get('evidence'))}</div></td><td>{esc(l.get('root_cause'))}</td><td>{target}</td>"
                        f"<td>{self.badge(status, 'pass' if status in ('fixed', 'closed') else 'warn')}{commit}</td></tr>")
        if not rows:
            return "" if stage is not None else "<h2>Ledger</h2><p class='mute'>No entries.</p>"
        head = "<h3>Ledger entries</h3>" if stage is not None else "<h2 id='ledger'>Ledger</h2>"
        return (head + "<table><tr><th>#</th><th>Stage</th><th>What happened / evidence</th><th>Root cause</th><th>Fix target</th><th>Status</th></tr>"
                + "".join(rows) + "</table>")

    def lock_gaps(self):
        if not self.t.lock_gaps:
            return ""
        rows = "".join(f"<tr><td>{esc(g['stage'])}</td><td>{esc(g['question'])}</td><td>{esc(g['decided'])}</td><td>{esc(g.get('intake_question'))}</td></tr>"
                       for g in self.t.lock_gaps)
        return ("<h2 id='gaps'>Lock gaps</h2><table><tr><th>Stage</th><th>Style question the lock did not answer</th><th>Decided</th>"
                "<th>A.2 question to add</th></tr>" + rows + "</table>")

    def stage_section(self, s, standalone=False):
        dur = (s["end"] - s["start"]).total_seconds() if s["start"] and s["end"] else None
        ok, n = self.t.rate(stage=s["n"])
        rate = f" · agreement {100 * ok / n:.0f}%" if n else ""
        status_cls = {"done": "pass", "blocked": "fail", "running": "warn"}.get(s["status"], "pending")
        body = [f'<div class="stagehead"><h2>{esc(s["n"])} — {esc(s["name"])}</h2><span>{self.badge(s["status"], status_cls)} '
                f'<span class="mute">{_dur(dur)}{rate}</span></span></div>']
        if s["summary"]:
            body.append(f"<p>{esc(s['summary'])}</p>")
        body += [self.decisions(s), self.timeline(s), self.score_trend(s), self.verdicts(s)]
        if standalone:
            body.append(self.ledger(stage=s["n"]))
        return f'<section class="stage" id="stage-{s["n"].replace(".", "")}">{"".join(body)}</section>'

    def page(self, stage=None):
        t = self.t
        if stage is None:
            parts = [self.header(), self.progress(), self.agreement_table()]
            parts += [self.stage_section(s) for s in t.stages.values() if s["events"]]
            parts += [self.ledger(), self.lock_gaps()]
        else:
            if stage not in t.stages or not t.stages[stage]["events"]:
                raise SystemExit(f"stage {stage} has no events")
            parts = [self.header(stage), self.progress(stage), self.stage_section(t.stages[stage], standalone=True)]
        if t.warnings:
            parts.append('<h3>Log warnings</h3><div class="warnbox">' + "<br>".join(esc(w) for w in dict.fromkeys(t.warnings)) + "</div>")
        title = f"Trial — stage {stage}" if stage is not None else "Trial report"
        return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{title}</title><style>{CSS}</style></head>'
                f'<body><main>{"".join(parts)}</main><div id="lb"><img alt=""><figcaption></figcaption></div><script>{JS}</script></body></html>')


def print_pdf(html_path: Path, chrome: str) -> Path:
    pdf = html_path.with_suffix(".pdf")
    if not Path(chrome).exists():
        raise SystemExit(f"Chrome not found at {chrome}; pass --chrome")
    with tempfile.TemporaryDirectory() as profile:
        cmd = [chrome, "--headless=new", "--disable-gpu", "--no-first-run", f"--user-data-dir={profile}",
               "--no-pdf-header-footer", f"--print-to-pdf={pdf.resolve()}", html_path.resolve().as_uri()]
        subprocess.run(cmd, check=True, timeout=180, capture_output=True)
    if not pdf.exists():
        raise SystemExit("Chrome exited without writing the PDF")
    return pdf


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("trial_dir", type=Path, help="<project>/Trial")
    ap.add_argument("--append", metavar="FILE", help="append events from a JSON file, or - for stdin")
    ap.add_argument("--stage", type=sid, help="render one stage (e.g. C.1) as a checkpoint report")
    ap.add_argument("--pdf", action="store_true", help="also print a PDF with headless Chrome")
    ap.add_argument("--link", action="store_true", help="link images from Trial/img instead of embedding them")
    ap.add_argument("--out", type=Path, help="output HTML path")
    ap.add_argument("--chrome", default=os.environ.get("CHROME", DEFAULT_CHROME))
    a = ap.parse_args(argv)
    if a.append:
        try:
            return append(a.trial_dir, a.append)
        except (ValueError, FileNotFoundError) as e:
            print(f"error: {e} (nothing appended)", file=sys.stderr)
            return 2
    trial = Trial(a.trial_dir)
    out = a.out or (a.trial_dir / "report.html" if a.stage is None
                    else a.trial_dir / "checkpoints" / f"stage-{a.stage.replace('.', '')}.html")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(Renderer(trial, out, embed=not a.link).page(a.stage), encoding="utf-8")
    print(f"wrote {out}")
    if a.pdf:
        print(f"wrote {print_pdf(out, a.chrome)}")
    for w in dict.fromkeys(trial.warnings):
        print(f"warning: {w}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
