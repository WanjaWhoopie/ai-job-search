# /batch-apply - Apply to Multiple Shortlisted Jobs and Submit

You are applying to several ranked jobs in one pass, then submitting each through the **Submission Procedure** below. `/nightly` reuses that procedure in headless mode — it is the single source of truth for how an application leaves this machine.

## Step 0: Parse Input

`$ARGUMENTS` may contain:

- Numbers (e.g. `/batch-apply 1 3 5`) → those entries from the current shortlist
- `--top <N>` → the N highest-ranked shortlist entries not yet applied to
- `--auto` → skip the per-job "should I proceed?" gates (fit floor still applies)
- `--dry-run` → run everything but stop before any real submission (`submit_app.py --dry-run`, drafts still written)
- `--flush-manual` → skip applying entirely; walk `job_scraper/manual_queue.json`, show each prepared item, and for each one the user confirms they submitted, run `python scripts/record_application.py --mark-submitted --company <c> --role <r>` and remove it from the queue. Then stop.

## Step 1: Load the Shortlist

1. Read `job_scraper/shortlist.json`. If missing, fall back to entries with `status: ranked` in `job_scraper/seen_jobs.json` (sorted by `rank_score`). If neither exists, tell the user to run `/scrape` + `/rank` first and stop.
2. Exclude any job whose company+role is already in `job_search_tracker.csv` (any status).
3. Resolve the selection (numbers or `--top N`) against the remaining list and confirm it with the user (in `--auto` mode, just state it).

## Step 2: Apply Loop

For each selected job, run the full `/apply` workflow from `.claude/commands/apply.md` Steps 0–5 (evaluate → draft → reviewer agent → revise → compile & inspect PDFs → ATS check).

- Interactive mode: keep apply.md's gates (fit evaluation shown, user approves drafting).
- `--auto` mode: replace the gate with the rule from `/nightly` — proceed only if the evaluation is moderate fit or better AND no deal-breaker is triggered; otherwise skip with a one-line reason.
- A job that fails evaluation or drafting is reported and skipped; it never blocks the rest of the batch.

Then run the Submission Procedure below for the job, and continue to the next.

## Step 3: Summarize

After the batch, report one line per job: `applied` / `ready_for_manual (<reason>)` / `skipped (<reason>)`, plus where drafts and queues live (`job_scraper/email_drafts.json`, `job_scraper/manual_queue.json`).

---

## Submission Procedure

*(Shared: `/batch-apply` runs this interactively; `/nightly` runs it headless. In headless mode never ask questions — apply the stated defaults. In interactive mode, always show what will be submitted and get an explicit yes before any real `submit_app.py submit` call.)*

**Inputs per job:** company, role, posting URL, the apply mechanism extracted from the posting, compiled `cv/main_<company>.pdf` and `cover_letters/cover_<company>_<role>.pdf`.

### 1. Classify the channel

- Posting says to apply **by email** (an application email address is given) → **email path**
- Apply URL host is `boards.greenhouse.io` or `jobs.lever.co` → **ATS path**
- Apply URL host is `himalayas.app` → `python scripts/submit_app.py probe --url <url>` first. If the result carries a non-null `resolved_apply_url` on `boards.greenhouse.io` or `jobs.lever.co`, continue on the **ATS path with that resolved URL**; otherwise **manual path** (Himalayas-hosted applications are Turnstile-gated and their ToS bars scripted apply — never automate).
- Apply URL host is `jobs.smartrecruiters.com` → `python scripts/submit_app.py probe --url <url>` first. If `posting_active` is false or the posting is not found, **skip** the job with reason `expired` instead of queueing it; otherwise **manual path** (the apply UI is DataDome-protected and the Application API needs company credentials — never automate).
- Anything else — LinkedIn Easy Apply, Workday, `job-boards.greenhouse.io`, any login-walled portal, or unknown → **manual path** (never automate these; LinkedIn automation violates ToS)

### 2. Email path

1. Compose a tailored application email in the posting's language: subject `Application: <Role> — Whoopie Wanja Wanjiru`; body is a condensed version of the cover letter (greeting, 2 short paragraphs, closing) — never new claims, only content already verified in the drafts.
2. Append to `job_scraper/email_drafts.json` (create as `[]` if missing):

```json
{
  "company": "...", "role": "...", "date": "YYYY-MM-DD",
  "to": "jobs@company.com",
  "subject": "Application: <Role> — Whoopie Wanja Wanjiru",
  "body": "...",
  "attachments": ["cv/main_<company>.pdf", "cover_letters/cover_<company>_<role>.pdf"],
  "status": "draft"
}
```

3. Status is `ready_for_manual` — **nothing is ever auto-sent.** The user reviews the draft and sends it themselves.

### 3. ATS path (Greenhouse / Lever)

1. `python scripts/submit_app.py probe --url <apply_url>` — exit 3 (CAPTCHA or unsupported board) → go to the manual path immediately, no retries burned.
2. Map the returned `fields` to answers in `documents/applications/<company>_<role>/answers.json`:
   - Fill from the candidate profile only — **never fabricate**.
   - Optional demographic/EEOC questions → the "decline to answer" option.
   - Required free-text questions → 2–4 honest sentences from the profile.
   - A required question that cannot be answered truthfully from the profile → manual path, quote the question in the report/summary.
3. `python scripts/submit_app.py submit --url <url> --answers <answers.json> --resume <cv.pdf> --cover-letter <cover.pdf>` (add `--dry-run` when dry-running). **Max 2 submit attempts total:**
   - Exit 4 (validation): fix the named fields in answers.json, retry once.
   - Exit 5 (network): retry once.
   - Exit 3 at any point, or a second failure → manual path.
4. Exit 0 → status `applied`.

### 4. Manual path

Append to `job_scraper/manual_queue.json` (create as `[]` if missing): `{company, role, url, reason, date, prepared: {cv_pdf, cover_pdf, answers_json?, email_draft?}}`. Status `ready_for_manual`.

### 5. Record (every path)

```
python scripts/record_application.py --company "<Company>" --role "<Role>" \
  --status <applied|ready_for_manual> --channel <email|ats_form|manual> \
  --source-url "<posting url>" --cv-file "cv/main_<company>.tex" \
  --cover-letter-file "cover_letters/cover_<company>_<role>.tex" \
  --fit-rating "<score>" --notes "<one line: channel + what happened>"
```

Then: copy the posting text to `documents/applications/<company>_<role>/job_posting.md` and the drafts as `cv_draft.tex` / `cover_letter.tex` (the `/outcome` archive convention), and set the job's entry in `job_scraper/seen_jobs.json` to `"status": "applied"` or `"ready_for_manual"`.

### 6. Missing site credential

If a portal needs a login credential referenced as `<SITE>_USER` / `<SITE>_PASSWORD` in `.env`:
- Interactive: ask the user for the values, append them to `.env` with Write/Edit (never echo them back, never commit; offer "I'll add it myself" as an option).
- Headless: never prompt — manual path, and flag the missing variable **name** (never a value) in the report.
