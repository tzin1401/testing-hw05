---
name: perf-endpoint-group
description: Run a complete, real performance test on one API endpoint group (auth, read, transactional, or a new group defined in JSON), end to end in one go. It generates the JMeter plan, resets the SUT, runs JMeter non-GUI with a RAM monitor, computes metrics from the raw .jtl, checks the SLO, and writes an analysis whose every number is verified against the log. Use it whenever the user asks to load-test, smoke-test or benchmark an endpoint group or a few endpoints of the EShop SUT (or a similar REST backend). Also use it for "chạy perf cho nhóm X", "test hiệu năng endpoint", "/perf-endpoint-group", or reusing the HW05 workflow on new endpoints, even if they don't say "skill".
---

# Performance test for one endpoint group

This skill packages the HW05 workflow so it can be reused on more endpoints:

> group definition → generated plan → reset SUT → JMeter non-GUI + monitor → numbers computed by a script from the raw JTL → SLO verdict → AI interpretation, checked against those numbers.

The scripts do the measuring. You do the interpretation. Keeping these apart is the point: in HW05 the AI read numbers correctly but proposed thresholds that did not fit the data. So the numbers must always come from `analyze.py`, never from your own arithmetic or memory.

## Inputs

Arguments: `<group> [smoke|load]`.
- `group` is a name in `groups/` (`auth`, `read`, `transactional`) or a path to a group JSON file.
- `smoke` (the default) runs 20 VU, ramp 10 s, 120 s. `load` runs 50 VU, ramp 50 s, 600 s.
- To override the profile, set the environment variables `THREADS`, `RAMPUP` and `DURATION`.

If no group is given, ask once and list the files in `groups/`. Otherwise, do not ask anything: the user expects one command to run from start to finish.

Run from the project root, the folder that contains `data/`. `scripts/reset_sut.sh` is used if it exists. Set `SUT_RESET` to use a different reset script, and `SUT_URL` if the SUT is not at `http://localhost:3000`.

## Steps

1. **Run the pipeline.** Run it in the foreground and stream the output, so the screen recording shows JMeter progress. Do not pipe it through `tail` or `grep`, which would hide the live `summary +` lines. Set the Bash timeout to at least `DURATION + 240` seconds (for smoke, use 600000 ms).
   ```bash
   <skill-dir>/scripts/run.sh <group> [smoke|load]
   ```
   The last lines print `RUN_DIR=...`. The exit code means:
   - 0 = SLO PASS.
   - 1 = SLO FAIL. This is still a valid result, so continue.
   - 2 = setup problem. Report what is missing and stop; do not invent results.

2. **Read `RUN_DIR/summary.json`.** This file is the only source of numbers.

3. **Write `RUN_DIR/report.md`** with exactly these sections:
   ```markdown
   # Performance test – group `<name>` – <PASS|FAIL>
   ## A. Số liệu (script tính từ JTL)
   <paste summary.md content unchanged, without its first heading>
   ## B. Phân tích của AI
   <3–6 bullets: slowest label and by how much, errors and their HTTP codes, whether the SLO margin is
    comfortable or thin, RAM trend. Every number must be copied from summary.json; compare raw values side by side instead of
    computing ratios or differences, because the checker can only verify numbers that exist in the file. Label each cause as
    "giả thuyết" unless the data proves it (a JTL shows *that* something is slow, not *why*).>
   ## C. Người cần kiểm tra
   <checklist for the human: open html/index.html and compare 2–3 numbers; confirm htop was in the recording;
    decide whether the SLO in the group file is right. Leave the boxes unticked.>
   ## D. File
   <plan .jmx, run.jtl, html/, summary.json, summary.md, monitor.csv, jmeter.log>
   ```
   Write sections A, B and C in Vietnamese when the user writes in Vietnamese.

4. **Verify your own claims.**
   ```bash
   python3 <skill-dir>/scripts/check_claims.py <RUN_DIR>
   ```
   If the script lists numbers that are not in `summary.json`, fix section B and run it again until it prints OK. This step exists because a fluent, wrong number is the most common AI failure in log analysis.

5. **AI log.** If the project has an AI-log rule (for example `agent.md`, which requires logging when the prompt contains "ghi vào log"), append the entry the rule asks for. Never fill in the "Human review" field; that belongs to the student.

6. **Final reply.** Give the verdict, the per-label table (from summary.md), up to 3 key findings, the paths, and the section C checklist. Keep it short.

## Rules that protect the evidence

- Never create, edit or "clean" a `.jtl` file. If a run is bad, run it again into a new folder.
- Never add a listener that writes to the same file as `-l`. The generator deliberately adds none, because a second writer duplicates every sample.
- Error % comes from `success=false`. An expected 401/403 (negative login) passes its status-code assertion, so it counts as success. Such steps carry `"slo": false` and are not gated.
- Percentiles are nearest-rank on `elapsed`. They can differ slightly from the JMeter HTML dashboard. Say so if the user compares them; do not "correct" either one.

## Adding a new endpoint group

Copy a file in `groups/` and edit it. The schema is in `references/group-schema.md`. A new group needs no code change: `gen_plan.py` builds the plan from the JSON. Run a short check first:
```bash
THREADS=2 RAMPUP=1 DURATION=15 <skill-dir>/scripts/run.sh path/to/new.json
```
