---
name: pipeline-trial
description: Wear-test and calibrate AWDK itself — run the full world pipeline (A.1 Setup to D.4 Retro) in a fresh project with a user checkpoint after every stage, log every decision, attempt, review verdict and score, D → C loop-back and user verdict to Trial/log.jsonl, render HTML/PDF progress reports, and track how often (and by how many points) the user agrees with the reviewers until the kit can run unattended. Use when asked to "test the pipeline", "do a trial run", "calibrate the reviewers", or after a large change to the kit.
---

# Pipeline trial

A trial proves the kit, not a world. The world it produces is evidence; the **ledger** and the
**agreement rate** are the deliverables.

The goal is a kit whose reviewers judge exactly as the user would. Then the only user decisions
left are the taste calls settled in information gathering and the Design Lock (A.2–A.4) and the
D.3 upload, and the build runs to the end with no stops or corrections. Each trial measures how far
the kit is from that and turns every gap into a fix.

## Stages

| Phase | Stages |
|---|---|
| A · Concept | A.1 Setup · A.2 Information gathering · A.3 Concept (shell layout + concept art) · A.4 Design Lock |
| B · Blueprint | B.1 Floor plan · B.2 Greybox |
| C · Build | C.1 Build-out · C.2 Interactions & playability |
| D · Finish | D.1 Lighting · D.2 Performance · D.3 Ship · D.4 Retro |

Stage IDs are strings (`"A.3"`, `"C.1"`) in every event and on the command line. The report's
default stage list is exactly this table.

## Setup

1. Fresh world project (see `.omp/docs/new-world.md`), `com.awdk.agenttools` installed, console clean.
   Never trial inside a project someone is working in.
2. Create `<project>/Trial/` with `TRIAL.md` (kit commit hash, agent host and model, date, source
   and persona) and an empty `log.jsonl`. Log `trial_start` first (schema below); `stages` is only
   needed if the run deviates from the stage table.
3. Information source, one of:
   - **Live**: the real user supplies the brief, answers the A.2 gap questions and gives every
     checkpoint verdict. Only live trials count toward the agreement rate and calibration.
   - **Scripted**: a written persona (purpose, capacity, avatar height, mood, style answers,
     likes/dislikes) answered by a separate agent that only sees the persona and the questions.
     Keep the persona in `TRIAL.md` so the run is reproducible. Scripted trials test the process
     (tools, timings, review loops, lock gaps), not the reviewers' taste.
4. Involvement preset: **Every step** (world-pipeline skill "Involvement"): a checkpoint after every
   stage, including the B review of the floor plan and greybox, which the default preset skips.

## Run

Follow `.omp/skills/world-pipeline/SKILL.md` exactly, start to finish. Every subagent brief names
the trial directory and says "trial run: log your events" (each builder and reviewer agent has a
one-line hook pointing here). The orchestrator logs `stage_start` and `stage_end`, every
`decision`, every `lock_gap`, every `loop_back` and `timing` for the long steps; builders log
`attempt`s (one per pass, with the logged pass plan in `detail`); reviewers log `review`s with their
score. Do not patch the kit mid-run unless the run is blocked; if you must, log the patch as a
ledger entry and say so.

### D → C loop-back

When a D review (or the user) needs a change that is build work, the orchestrator logs a
`loop_back` event in the D stage (`to`: the C stage, `reason`, `ref`: the review that raised it,
`redo`: the D steps to repeat). The report reopens that C stage until its next `stage_end`. The C
fix is logged in the C stage as usual (`stage_start`, attempts, reviews, `stage_end`), then the
affected D steps are redone and logged again (rebake the area and the probes, re-measure, rerun the
final review). Each loop-back gets its own checkpoint.

## Checkpoints (after every stage, A.1–D.4)

1. Log `stage_end` with a one-paragraph summary.
2. Render the checkpoint report: `python .omp/skills/pipeline-trial/scripts/trial_report.py
   <project>/Trial --stage C.1 --pdf` (writes `Trial/checkpoints/stage-C1.html` and `.pdf`).
3. **Stop.** Give the user the report path and show the stage's key images inline. For **every
   reviewer decision** in the stage (each `review` event, and each `decision` taken by an agent),
   ask: agree or disagree; their own score out of 10 (optional); what should change; what worked
   well. Also ask what the reviewers missed: an issue the user sees in something a reviewer passed
   is a disagreement with that pass. For dressing-reviewer, ask which half they disagree with
   (style or build).
4. Log one `user_verdict` per reviewer decision, with the user's exact words and `score` if given.
5. Every disagreement becomes a `ledger` entry with a **fix target**:
   - `reviewer-criterion`: the reviewer judged wrong or missed it (edit that reviewer's criteria);
   - `builder-rule`: the builder did it wrong and no rule said otherwise (edit the builder agent or
     the stage skill);
   - `gathering-question`: the user's taste was never asked (a new A.2 information-gathering
     question in intake.md);
   - `lock-item`: the lock didn't cover it (a new Design Lock item or board);
   - or `tool`, `note`, `skill` for the other kit targets.
6. Act on the verdict in the world: a disagreement with a pass is a new finding, fixed and
   re-reviewed before the next stage (log those attempts and reviews too). The kit itself is fixed
   after the trial, from the ledger.
7. Log a `checkpoint` event (report path), then start the next stage.

In A.3 (shell layouts), B.1 (floor plan) and B.2 (greybox), all ranked by layout-reviewer, a user
pick is already a verdict on the reviewer's ranking: log the `decision` with `reviewer_pick` and the
ranking's `review` id, and the report counts the match. Still ask what to change and what worked well in the reviewer's
reasons. A.3 style rounds have no reviewer: log the pick as a plain user `decision`.

**A.3 tracks.** The style track is text → image only and the layout track is plain shell-blockout
captures (no paint-overs). Log every A.3 pick in a `decision` (`chosen` names the track and
option, e.g. `layout:B` or `style:C`) with the user's reason in `user_words`.

## Agreement rate

For a stage or a reviewer: **user verdicts that matched the reviewer ÷ all judged reviewer
decisions**. One record per decision: a `user_verdict` on a review or agent decision (matched when
`agree` is true), or a user `decision` with `reviewer_pick` (matched when the user chose the
reviewer's pick). An explicit `user_verdict` replaces the pick-based record for the same review. The
report computes it per stage, per reviewer and overall.

**Score difference**: when the user gives a score, the report shows user − reviewer per verdict and
the mean per reviewer. Agreement is the calibration gate; the score difference shows the direction
of a drift (a reviewer that is consistently 2 points too generous) before verdicts start to flip.

**Calibrated** means: across **3 consecutive live trials**, the agreement rate is about 100 % for
every reviewer (at least 95 %, and every remaining disagreement is a taste call that has been moved
into the lock) **and** no lock gaps were logged. Then the kit is trusted to run unattended on the
default preset "Design lock, then autopilot". Track it in [trials.md](trials.md).

## Event log (`<project>/Trial/log.jsonl`)

One JSON object per line. Append with the script (it validates the event, stamps `ts`, and copies
every referenced image into `Trial/img/`, rewriting the path):

```bash
python .omp/skills/pipeline-trial/scripts/trial_report.py <project>/Trial --append - <<'EOF'
{"type": "review", "stage": "C.1", "id": "r-c1-lounge-1", "reviewer": "dressing-reviewer", "round": 1,
 "verdict": "NEEDS WORK", "score": 5, "scores": {"style": 7, "build": 4}, "target": "Lounge",
 "findings": [{"n": 1, "severity": "blocker", "title": "Sofa 0.6 m off its placeholder transform",
   "reason": "lounge-sofa at (2.2, 6.2), greybox placeholder (2.2, 5.6); blocks the hall path", "section": "§5.2",
   "fix": "move to the placeholder transform", "images": ["C:/Temp/world-review/C1-lounge-01/02_eyelevel.png"]}]}
EOF
```

Input may be one object, an array or JSON lines. A missing required field or image fails the whole
append. Common fields: `type`, `ts` (ISO 8601 with offset; stamped when absent), `stage` (stage ID
such as `"C.1"`), `agent` (who logged it). Every list named `images` and every field named `img`
holds image paths.

| `type` | Required | Optional |
|---|---|---|
| `trial_start` | `kit_commit`, `source` (live / persona name), `preset` | `project`, `host`, `model`, `stages` [{`n` (stage ID), `name`}] |
| `stage_start` | `stage`, `name` | |
| `stage_end` | `stage`, `status` (done / blocked) | `summary` |
| `decision` | `stage`, `id`, `point` (the stage ID, LOCK, or a round such as `A.3 palette round 2`), `chosen`, `by` (user / agent), `reason` | `question`, `options` [{`id`, `label`, `img`}], `reviewer`, `reviewer_pick`, `review` (the ranking's review id), `user_words`, `images` |
| `attempt` | `stage`, `id`, `what` (what was tried), `result` (pass / fail / partial / error) | `detail`, `round`, `images` |
| `review` | `stage`, `id`, `reviewer`, `verdict` (SHIP IT / MINOR FIXES / NEEDS WORK, or RANKED for a ranking), `score` (0–10; not on RANKED) | `scores` {`style`, `build`} (dressing-reviewer), `option_scores` {option id: 0–10} (required on RANKED: every option), `mode` (rank / judge), `round`, `target`, `summary`, `ranking` [ids, best first], `passed_because` [reasons], `findings` [{`n`, `severity`, `title`, `reason`, `fix`, `section`, `images`}], `images`, `report_path` |
| `user_verdict` | `stage`, `ref` (a review or decision id), `agree` (true / false) | `score` (the user's own, 0–10), `change`, `worked_well`, `user_words`, `findings` [{`n`, `agree`, `note`}] |
| `loop_back` | `stage` (the D stage), `id`, `to` (the C stage), `reason` | `ref` (review id), `redo` [D stage IDs], `by` (agent / user) |
| `ledger` | `stage`, `n`, `what`, `fix_target` {`kind`, `file`, `change`} | `evidence`, `images`, `root_cause`, `status` (open / fixed / closed), `commit` |
| `lock_gap` | `stage`, `question`, `decided` | `by`, `options`, `intake_question` |
| `timing` | `stage`, `what`, `seconds` | |
| `checkpoint` | `stage`, `report` | `pdf` |

A SHIP IT needs a score ≥ 8 and no blocker or should-fix finding; the report lists any review that
breaks this under "Log warnings" (the score never overrides findings).

`fix_target.kind` is one of `reviewer-criterion`, `builder-rule`, `gathering-question`, `lock-item`,
`tool`, `note`, `skill`. A later `ledger` event with the same `n` updates that entry (status,
commit). Stage durations come from `stage_start`/`stage_end`; `timing` is for the steps inside a
stage (a bake, a generation round, a review).

## Reports

```bash
python .omp/skills/pipeline-trial/scripts/trial_report.py <project>/Trial          # Trial/report.html
python .omp/skills/pipeline-trial/scripts/trial_report.py <project>/Trial --pdf    # + report.pdf
python .omp/skills/pipeline-trial/scripts/trial_report.py <project>/Trial --stage A.3 --pdf # checkpoint
```

The page is self-contained (images embedded; `--link` references `Trial/img/` instead, for large
trials): a progress bar of stages (done, running, blocked, pending, ✓ when the checkpoint was
reviewed), headline numbers, the agreement table per reviewer (with the mean user − reviewer score),
then per stage its decisions table, a timeline of attempts, reviews and loop-backs (failures red,
passes green, each review with its score (style/build), option scores, findings, reasons and
thumbnails; click a thumbnail for the full image), the score trend across passes per target, the
user verdicts with their scores and the stage's agreement rate, and finally the ledger and the
lock gaps. The PDF is printed by headless Chrome
(`--chrome PATH` or `CHROME` overrides the default install path); each stage starts a new page.

## Grade

Grading is done by a **separate** agent that did not run the pipeline:

1. **World**: `final-reviewer` on the whole world (its verdict and findings go in the ledger), and
   `perf-optimizer` measure-only (worst viewpoint ms, visible tris, VRAM).
2. **Brief and lock fit**: the grader compares the world against WORLD.md, the A.2 answers and
   every A.3 concept and style image and `SHELL_PICK`, and lists every place the agent guessed wrong. For a live trial, ask the
   person: "what would you have chosen differently?". Their answers are the most valuable ledger
   entries.
3. **Process**: stages that needed more than three review rounds, gates that passed something the
   user or final reviewer later rejected (a gate that "cannot see its defect"), D → C loop-backs,
   tool failures, editor freezes or timeouts, unclear docs the agent misread, questions A.2 should
   have asked, lock gaps.

## Close

Turn each ledger entry into a concrete change in the kit: an edit to a reviewer's criteria or a
builder rule, a new A.2 question or lock item, a new check in `com.awdk.agenttools` with a
positive-control test, or a knowledge note. Log a `ledger` update with `status` and `commit`.
Every lock gap becomes a line in intake.md "Lock-gap questions". Entries that need the user's taste
decision stay open and are listed for them. Render the final `report.html` and `report.pdf`, and
add the trial's line to [trials.md](trials.md).

## Rules

- Lessons only count when the evidence shows the failure, never on the trial agent's own opinion.
- A trial that passes everything with zero ledger entries is suspicious: check that the grader
  actually ran the reviewers and looked at the screenshots.
- Never skip a checkpoint or answer one for the user; a scripted trial's persona agent answers its
  own.
- Keep `Trial/` with the project.
