#!/usr/bin/env python3
"""Local dashboard for the job-search pipeline. Stdlib only.

  python scripts/dashboard.py            -> http://127.0.0.1:8765

Serves scripts/dashboard.html, aggregates the pipeline's state files as JSON,
and toggles job_scraper/config.json's scraping_enabled flag. Binds to
localhost only - this is personal data.
"""
import csv
import json
import re
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

REPO = Path(__file__).resolve().parent.parent
SCRAPER = REPO / "job_scraper"
CONFIG = SCRAPER / "config.json"
PORT = 8765


def read_json(path, default):
    try:
        # utf-8-sig tolerates the BOM that PowerShell's `-Encoding utf8` writes
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return default


def read_config():
    return read_json(CONFIG, {"scraping_enabled": True})


def collect():
    tracker = []
    tracker_path = REPO / "job_search_tracker.csv"
    if tracker_path.exists():
        with open(tracker_path, newline="", encoding="utf-8") as f:
            tracker = list(csv.DictReader(f))

    seen = read_json(SCRAPER / "seen_jobs.json", {"seen": {}})["seen"]
    counts = {}
    for job in seen.values():
        counts[job.get("status", "unknown")] = counts.get(job.get("status", "unknown"), 0) + 1

    reports = sorted(p.name for p in (SCRAPER / "reports").glob("nightly_*.md")) \
        if (SCRAPER / "reports").exists() else []

    return {
        "config": read_config(),
        "counts": counts,
        "seen": seen,
        "shortlist": read_json(SCRAPER / "shortlist.json", {}),
        "manual_queue": read_json(SCRAPER / "manual_queue.json", []),
        "email_drafts": read_json(SCRAPER / "email_drafts.json", []),
        "portal_outcomes": read_json(SCRAPER / "portal_outcomes.json", {}).get("portals", {}),
        "tracker": tracker,
        "reports": reports,
    }


class Handler(BaseHTTPRequestHandler):
    def _send(self, body, ctype="application/json", code=200):
        data = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", f"{ctype}; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        url = urlparse(self.path)
        if url.path in ("/", "/index.html"):
            html = (REPO / "scripts" / "dashboard.html").read_bytes()
            self._send(html, "text/html")
        elif url.path == "/api/data":
            self._send(collect())
        elif url.path == "/api/report":
            name = parse_qs(url.query).get("name", [""])[0]
            if not re.fullmatch(r"nightly_\d{4}-\d{2}-\d{2}\.md", name):
                self._send({"error": "bad report name"}, code=400)
                return
            path = SCRAPER / "reports" / name
            if path.exists():
                self._send({"name": name, "markdown": path.read_text(encoding="utf-8")})
            else:
                self._send({"error": "not found"}, code=404)
        else:
            self._send({"error": "not found"}, code=404)

    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/api/toggle":
            cfg = read_config()
            cfg["scraping_enabled"] = not cfg.get("scraping_enabled", True)
            CONFIG.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
            self._send(cfg)
        elif path in ("/api/mark-submitted", "/api/dismiss"):
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0)) or 0) or "{}")
            company, role = body.get("company", ""), body.get("role", "")
            if not company:
                self._send({"ok": False, "error": "company required"}, code=400)
                return
            dismiss = path == "/api/dismiss"
            # record_application.py is the single owner of tracker/portal writes
            proc = subprocess.run(
                [sys.executable, str(REPO / "scripts" / "record_application.py"),
                 "--dismiss" if dismiss else "--mark-submitted",
                 "--company", company, "--role", role],
                capture_output=True, text=True, cwd=REPO)
            try:
                result = json.loads(proc.stdout.strip() or "{}")
            except ValueError:
                result = {"ok": False, "error": proc.stdout or proc.stderr}
            # a row that already left ready_for_manual = stale queue entry; still clean up
            stale = "row status is" in str(result.get("error", ""))
            if result.get("ok") or stale:
                queue = read_json(SCRAPER / "manual_queue.json", [])
                urls = [q.get("url") for q in queue
                        if q.get("company") == company and q.get("role") == role]
                queue = [q for q in queue
                         if not (q.get("company") == company and q.get("role") == role)]
                (SCRAPER / "manual_queue.json").write_text(
                    json.dumps(queue, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                drafts = read_json(SCRAPER / "email_drafts.json", [])
                for d in drafts:
                    if d.get("company") == company and d.get("role") == role:
                        d["status"] = "expired" if dismiss else "sent"
                (SCRAPER / "email_drafts.json").write_text(
                    json.dumps(drafts, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                seen_path = SCRAPER / "seen_jobs.json"
                seen = read_json(seen_path, {"seen": {}})
                for job in seen["seen"].values():
                    if (job.get("url") in urls) or (job.get("company") == company and role
                                                    and role.lower() in job.get("title", "").lower()):
                        job["status"] = "expired" if dismiss else "applied"
                seen_path.write_text(json.dumps(seen, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                result.setdefault("ok", True)
                result["queue_cleaned"] = True
            self._send(result, code=200 if result.get("ok") else 422)
        else:
            self._send({"error": "not found"}, code=404)

    def log_message(self, *args):
        pass  # keep the console quiet


if __name__ == "__main__":
    print(f"Job search dashboard: http://127.0.0.1:{PORT}")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
