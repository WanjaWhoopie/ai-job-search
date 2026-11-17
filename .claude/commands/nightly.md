# /nightly - Unattended Scrape → Rank → Apply → Submit Pipeline

You are running **unattended** (launched by `scripts/run-pipeline.ps1`, usually from Task Scheduler at 22:00). This command is a thin orchestrator: every phase reuses an existing workflow file with the headless substitutions listed here. Do not re-derive logic those files already define.

## Headless rules (override everything below)

1. **Never** use AskUserQuestion or wait for confirmation. Where a referenced workflow says "ask the user", apply the decision rule given in this file instead.
2. Before starting each new application, check the clock (`date +%H:%M`). If past `cutoff`, stop starting new work and jump to Step 6 (report). Always produce the report, even after errors.
3. A failure in one job never aborts the run — record the error for the report and continue with the next job.
4. Honesty rules from `apply.md` and `batch-apply.md` hold: never fabricate profile claims or form answers.
5. The helper scripts **exist** at `scripts/record_application.py` and `scripts/submit_app.py` — call them exactly as documented in `batch-apply.md`. Never hand-edit `job_search_tracker.csv` or `job_scraper/portal_outcomes.json`; if a script call fails, quote its JSON error in the report instead of working around it.

## Step 0: Parse Arguments

`$ARGUMENTS` is space-separated `key=value` pairs:

- `dry_run=true|false` (default false) — propagate to the Submission Procedure (`submit_app.py --dry-run`; email/manual queue files still written, marked `"dry_run": true`)
- `top=<N>` (default 5) — max applications this run
- `shortlist=<N>` (default 30) — shortlist size
- `cutoff=<HH:mm>` — stop starting new applications after this time
- `shortlist_only=true` — scrape + rank + report only, zero applications
- `job=<seen_jobs key or URL>` — smoke test: skip Steps 1–3, apply to exactly this job

## Step 1: Scrape

Follow `.claude/skills/job-scraper/SKILL.md` Steps 0–4 in headless mode (skip Step 5 presentation and Step 6). Run the top 3 priority categories from `search-queries.md` **plus Priority 5 (East Africa + remote hybrid — always relevant to this profile)**, plus the LinkedIn CLI for the two strongest query categories:

```bash
bun run .agents/skills/linkedin-search/cli/src/cli.ts search -q "<query>" -l "Remote" --jobage 14 --limit 25 --format json
```

Merge CLI results through the same dedup (`seen_jobs.json` + tracker). Only postings from the last 14 days.

## Step 2: Rank

Follow `.claude/commands/rank.md` Steps 1–4 verbatim (parallel scoring agents, location veto, tracker exclusion, `seen_jobs.json` updates), ranking all `new` jobs. Skip its Step 5 (presentation).

## Step 3: Shortlist

Write `job_scraper/shortlist.json`:

```json
{
  "generated": "<ISO timestamp>",
  "params": {"top": 5, "shortlist": 30},
  "jobs": [
    {"key": "...", "rank": 1, "score": 78, "verdict": "Strong Fit", "title": "...",
     "company": "...", "url": "...", "location": "...", "deadline": null,
     "action": "auto_apply", "result": null}
  ]
}
```

- `jobs` = the top `shortlist` ranked jobs (highest score first).
- `action: "auto_apply"` for the top `top` jobs with **score ≥ 60 and location PASS**; everything else `"listed"`. If fewer than `top` clear the floor, apply to fewer — **never pad with weaker jobs.**
- If `shortlist_only=true`, skip to Step 6.

## Step 4: Apply

For each `auto_apply` job (best score first, cutoff check between jobs): run `.claude/commands/apply.md` Steps 0–5 with one substitution — Step 1's "Should I proceed?" gate becomes:

> Proceed only if the full evaluation lands at moderate fit or better AND no deal-breaker (sponsorship/location/unpaid) is triggered. Otherwise mark the job `result: "skipped:<reason>"` and promote the highest-scoring `listed` job that clears the floor into the auto-apply set.

Everything else in apply.md runs unchanged: drafter → reviewer agent → revise → compile (lualatex/xelatex) → PDF inspection loop → ATS check. Skip only its final "present to user" prose.

## Step 5: Submit

For each completed application, execute the **Submission Procedure** in `.claude/commands/batch-apply.md` in headless mode, passing `dry_run` through. Record each job's outcome in shortlist.json's `result` field (`applied`, `ready_for_manual`, or `skipped:<reason>`).

## Step 6: Report

Write `job_scraper/reports/nightly_YYYY-MM-DD.md`:

```markdown
# Nightly Run — YYYY-MM-DD

**Summary:** scraped <N> new / ranked <N> / applied <N> / ready-for-manual <N> / skipped <N> / errors <N> (dry_run: <bool>)

## Applied automatically
| Company | Role | Score | Channel | Evidence |
(final URL or confirmation text from submit_app.py)

## Ready for manual — action needed
Per item: posting link, why it was downgraded, and exact paths (CV pdf, cover letter pdf, answers.json or email draft entry in job_scraper/email_drafts.json).

## Shortlist (top <N>)
| # | Score | Verdict | Title | Company | Location | Deadline |

## Skipped / vetoed
One line each with the reason.

## Errors
Anything that failed, with enough detail to debug from the log.
```

If a report for today already exists (a second run), append a `## Run 2 — HH:mm` section instead of overwriting.

Finish by printing exactly: the report path, then a one-line summary (this lands in the wrapper's log and is all the user sees in the terminal).
