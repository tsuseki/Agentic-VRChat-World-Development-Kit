# Trial index

One line per pipeline trial. Agreement is user verdicts that matched the reviewer ÷ judged reviewer
decisions (SKILL.md "Agreement rate"), from the trial's final `report.html`; only live trials count
toward calibration. The kit is calibrated after 3 consecutive live trials at ≈100 % (≥ 95 %) for
every reviewer with 0 lock gaps. Score Δ is the mean user − reviewer score from the report's
agreement table; it shows drift before verdicts flip.

| Date | Kit commit | Source (live / persona) | Preset | Outcome | Ledger entries | Lock gaps | D → C loop-backs | Agreement overall | layout-reviewer (agree · score Δ) | dressing-reviewer (agree · score Δ) | final-reviewer (agree · score Δ) |
|---|---|---|---|---|---|---|---|---|---|---|---|
