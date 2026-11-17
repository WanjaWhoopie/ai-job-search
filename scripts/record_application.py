#!/usr/bin/env python3
"""Single owner of job-application state writes.

Used by /batch-apply, /nightly and /outcome so the agent never hand-edits
job_search_tracker.csv or job_scraper/portal_outcomes.json.

Modes:
  insert (default)  record a new application
  --mark-submitted  flip a ready_for_manual row to applied (+ portal count)
  --record-outcome  update row status + portal aggregate on a transition

Always prints one JSON line to stdout.
Exit codes: 0 ok, 2 state/file error, 4 bad args, 6 duplicate row.
"""
import argparse
import csv
import json
import re
import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TRACKER = REPO / "job_search_tracker.csv"
PORTALS = REPO / "job_scraper" / "portal_outcomes.json"
HEADER = ["date", "company", "sector", "role", "role_type", "channel", "status",
          "contact_person", "fit_rating", "notes", "cv_file", "cover_letter_file", "source"]

DOMAIN_PORTAL = {
    "linkedin.com": "linkedin", "wellfound.com": "wellfound", "remoteok.com": "remoteok",
    "weworkremotely.com": "weworkremotely", "remotive.com": "remotive",
    "himalayas.app": "himalayas", "andela.com": "andela", "devex.com": "devex",
    "flexjobs.com": "flexjobs", "greenhouse.io": "greenhouse", "lever.co": "lever",
}

# tracker status -> portal_outcomes counter incremented on transition into it
OUTCOME_FIELD = {"interview": "interviews", "offer": "offers",
                 "rejected": "rejections", "no_response": "no_response"}


def out(obj, code=0):
    print(json.dumps(obj, ensure_ascii=False))
    sys.exit(code)


def slug(text):
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def portal_from_url(url):
    for domain, key in DOMAIN_PORTAL.items():
        if domain in (url or ""):
            return key
    return "other"


def load_tracker():
    if not TRACKER.exists():
        return []
    # utf-8-sig tolerates BOMs left by PowerShell Set-Content/Export-Csv
    with open(TRACKER, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def save_tracker(rows):
    with open(TRACKER, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=HEADER)
        writer.writeheader()
        writer.writerows(rows)


def find_row(rows, company, role=None):
    matches = [r for r in rows if r["company"].strip().lower() == company.strip().lower()]
    if role:
        narrowed = [r for r in matches if role.strip().lower() in r["role"].strip().lower()]
        matches = narrowed or matches
    return matches


def bump_portal(portal, field):
    data = json.loads(PORTALS.read_text(encoding="utf-8-sig")) if PORTALS.exists() else {"portals": {}}
    entry = data["portals"].setdefault(portal, {
        "applications": 0, "interviews": 0, "offers": 0,
        "rejections": 0, "no_response": 0, "notes": ""})
    entry[field] = entry.get(field, 0) + 1
    PORTALS.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return entry


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--company", required=True)
    p.add_argument("--role")
    p.add_argument("--status")
    p.add_argument("--portal")
    p.add_argument("--channel", choices=["email", "ats_form", "manual"])
    p.add_argument("--source-url", default="")
    p.add_argument("--sector", default="")
    p.add_argument("--role-type", default="")
    p.add_argument("--cv-file", default="")
    p.add_argument("--cover-letter-file", default="")
    p.add_argument("--notes", default="")
    p.add_argument("--fit-rating", default="")
    p.add_argument("--mark-submitted", action="store_true")
    p.add_argument("--record-outcome", action="store_true")
    p.add_argument("--dismiss", action="store_true",
                   help="posting closed before submission: row -> expired, no portal count")
    args = p.parse_args()

    rows = load_tracker()
    today = date.today().isoformat()

    if args.mark_submitted:
        if not args.role and not args.company:
            out({"ok": False, "error": "need --company (and ideally --role)"}, 4)
        matches = find_row(rows, args.company, args.role)
        if len(matches) != 1:
            out({"ok": False, "error": f"{len(matches)} rows match; narrow with --role"}, 2)
        row = matches[0]
        if row["status"] != "ready_for_manual":
            out({"ok": False, "error": f"row status is '{row['status']}', not ready_for_manual"}, 2)
        row["status"] = "applied"
        row["notes"] = (row["notes"] + "; " if row["notes"] else "") + f"{today} submitted manually"
        save_tracker(rows)
        portal = portal_from_url(row["source"])
        counts = bump_portal(portal, "applications")
        out({"ok": True, "action": "mark_submitted", "company": row["company"],
             "role": row["role"], "portal": portal, "portal_counts": counts})

    if args.dismiss:
        matches = find_row(rows, args.company, args.role)
        if len(matches) != 1:
            out({"ok": False, "error": f"{len(matches)} rows match; narrow with --role"}, 2)
        row = matches[0]
        if row["status"] not in ("ready_for_manual", "ready"):
            out({"ok": False, "error": f"row status is '{row['status']}' - only unsubmitted rows can be dismissed"}, 2)
        row["status"] = "expired"
        row["notes"] = (row["notes"] + "; " if row["notes"] else "") + f"{today} posting closed before submission"
        save_tracker(rows)
        out({"ok": True, "action": "dismiss", "company": row["company"], "role": row["role"]})

    if args.record_outcome:
        if args.status not in OUTCOME_FIELD:
            out({"ok": False, "error": f"--status must be one of {list(OUTCOME_FIELD)}"}, 4)
        matches = find_row(rows, args.company, args.role)
        if len(matches) != 1:
            out({"ok": False, "error": f"{len(matches)} rows match; narrow with --role"}, 2)
        row = matches[0]
        if row["status"] == args.status:
            out({"ok": True, "action": "record_outcome", "changed": False,
                 "note": f"status already '{args.status}', aggregate not re-counted"})
        row["status"] = args.status
        if args.notes:
            row["notes"] = (row["notes"] + "; " if row["notes"] else "") + f"{today} {args.notes}"
        save_tracker(rows)
        portal = portal_from_url(row["source"])
        counts = bump_portal(portal, OUTCOME_FIELD[args.status])
        out({"ok": True, "action": "record_outcome", "changed": True, "company": row["company"],
             "role": row["role"], "status": args.status, "portal": portal, "portal_counts": counts})

    # default mode: insert a new application
    if not (args.role and args.status and args.channel):
        out({"ok": False, "error": "insert needs --role, --status, --channel"}, 4)
    if args.status not in ("applied", "ready_for_manual"):
        out({"ok": False, "error": "--status must be applied or ready_for_manual"}, 4)
    if find_row(rows, args.company, args.role):
        out({"ok": False, "error_code": "duplicate",
             "error": f"tracker already has {args.company} / {args.role}"}, 6)

    portal = args.portal or portal_from_url(args.source_url)
    rows.append({
        "date": today, "company": args.company, "sector": args.sector, "role": args.role,
        "role_type": args.role_type, "channel": args.channel, "status": args.status,
        "contact_person": "", "fit_rating": args.fit_rating, "notes": args.notes,
        "cv_file": args.cv_file, "cover_letter_file": args.cover_letter_file,
        "source": args.source_url,
    })
    save_tracker(rows)

    archive = REPO / "documents" / "applications" / f"{slug(args.company)}_{slug(args.role)}"
    archive.mkdir(parents=True, exist_ok=True)

    counts = None
    if args.status == "applied":
        counts = bump_portal(portal, "applications")

    out({"ok": True, "action": "insert", "company": args.company, "role": args.role,
         "status": args.status, "portal": portal, "archive": str(archive.relative_to(REPO)),
         "portal_counts": counts})


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:  # any unexpected state error
        print(json.dumps({"ok": False, "error": str(e)}))
        sys.exit(2)
