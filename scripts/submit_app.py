#!/usr/bin/env python3
"""Probe and submit public ATS application forms (Greenhouse, Lever).

Direct HTTP against server-rendered forms — no browser. CAPTCHA-protected or
JS-only boards are reported as terminal (exit 3) so the caller downgrades the
job to the manual queue instead of retrying.

Himalayas and SmartRecruiters are probe-only (submission there is bot-gated
and/or barred by ToS, so it stays manual): their probes use the portals'
public, permitted APIs to resolve a Himalayas job's external apply URL
(`resolved_apply_url` — re-probe it with the normal flow) and to report
whether a SmartRecruiters posting is still live (`posting_active`).

  probe  --url <apply_url>
  submit --url <apply_url> --answers answers.json --resume cv.pdf
         [--cover-letter cl.pdf] [--dry-run]

answers.json maps form field names to values, e.g.
  {"first_name": "Whoopie", "email": "...", "question_123": "..."}
Unlisted non-required fields are left empty; file fields are filled from
--resume / --cover-letter by field-name heuristics.

Always prints one JSON line to stdout.
Exit codes: 0 ok, 3 captcha/unsupported (terminal), 4 validation error
(retriable after fixing answers), 5 network error (retriable), 6 bad args.
"""
import argparse
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, urljoin

import requests

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
TIMEOUT = 30
CAPTCHA_MARKERS = ["g-recaptcha", "h-captcha", "hcaptcha.com", "recaptcha/api", "cf-turnstile"]


def out(obj, code=0):
    print(json.dumps(obj, ensure_ascii=False))
    sys.exit(code)


def detect_portal(url):
    host = urlparse(url).netloc.lower()
    if host.endswith("boards.greenhouse.io"):
        return "greenhouse"
    if host == "job-boards.greenhouse.io":
        return "greenhouse_react"  # React embed, no server-rendered form
    if host.endswith("jobs.lever.co"):
        return "lever"
    if host in ("himalayas.app", "www.himalayas.app"):
        return "himalayas"
    if host == "jobs.smartrecruiters.com":
        return "smartrecruiters"
    return "unsupported"


def api_get_json(url, params=None):
    """GET a public JSON API; exits 5 on network trouble. Returns (status, json|None)."""
    try:
        resp = requests.get(url, params=params, headers={"User-Agent": UA}, timeout=TIMEOUT)
    except requests.RequestException as e:
        out({"ok": False, "error_code": "network", "message": str(e)}, 5)
    if resp.status_code >= 500:
        out({"ok": False, "error_code": "network", "message": f"HTTP {resp.status_code} from {url}"}, 5)
    try:
        return resp.status_code, resp.json()
    except ValueError:
        return resp.status_code, None


def probe_himalayas(url):
    """Himalayas apply is Turnstile-gated and its ToS bars scripted applications,
    so submission is always manual. But the public jobs API (expressly permitted
    for programmatic use) carries each job's applicationLink: when that link
    leaves himalayas.app, the real application lives on an external ATS, and the
    caller should re-probe the resolved URL with the normal flow."""
    m = re.match(r"https?://(?:www\.)?himalayas\.app/companies/([^/]+)/jobs/([^/?#]+)", url)
    if not m:
        out({"ok": False, "error_code": "manual_portal", "portal": "himalayas",
             "message": "unrecognized himalayas.app URL shape — apply manually"}, 3)
    company_slug, job_slug = m.group(1), m.group(2)
    resolved = None
    for page in (1, 2):
        status, data = api_get_json("https://himalayas.app/jobs/api/search",
                                    {"q": job_slug.replace("-", " "), "page": page})
        jobs = (data or {}).get("jobs", []) if isinstance(data, dict) else []
        for job in jobs:
            link = job.get("applicationLink", "")
            if company_slug in link and job_slug in link:
                resolved = link.split("?")[0]
                break
        if resolved or not jobs:
            break
    if resolved and urlparse(resolved).netloc.lower() not in ("himalayas.app", "www.himalayas.app"):
        out({"ok": False, "error_code": "manual_portal", "portal": "himalayas",
             "resolved_apply_url": resolved,
             "message": "application actually lives on an external ATS — "
                        "re-probe resolved_apply_url with the normal flow"}, 3)
    out({"ok": False, "error_code": "manual_portal", "portal": "himalayas",
         "resolved_apply_url": None,
         "message": "Himalayas-hosted application (Turnstile-gated, ToS bars scripted "
                    "apply) — submit manually in a browser"}, 3)


def probe_smartrecruiters(url):
    """SmartRecruiters' apply UI is DataDome-protected and its Application API
    needs company-issued credentials, so submission is always manual. The public
    Posting API still tells us whether the posting is live, which stops dead
    postings from reaching the manual queue."""
    m = re.match(r"https?://jobs\.smartrecruiters\.com/([^/]+)/(\d+)", url)
    if not m:
        out({"ok": False, "error_code": "manual_portal", "portal": "smartrecruiters",
             "message": "unrecognized jobs.smartrecruiters.com URL shape — apply manually"}, 3)
    company, posting_id = m.group(1), m.group(2)
    status, data = api_get_json(
        f"https://api.smartrecruiters.com/v1/companies/{company}/postings/{posting_id}")
    if status == 404:
        out({"ok": False, "error_code": "unsupported", "portal": "smartrecruiters",
             "posting_active": False,
             "message": "posting not found via Posting API — likely expired, skip it"}, 3)
    active = bool(data.get("active")) if isinstance(data, dict) else None
    out({"ok": False, "error_code": "manual_portal", "portal": "smartrecruiters",
         "posting_active": active,
         "message": ("posting is live; " if active else "posting may be inactive; ")
                    + "apply UI is DataDome-protected and the Application API needs "
                      "company credentials — submit manually in a browser"}, 3)


class FormParser(HTMLParser):
    """Collects fields of every <form>; caller picks the application form."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.forms = []          # [{action, id, fields: [...]}]
        self._form = None
        self._select = None
        self._textarea = None
        self._label_for = None
        self._label_text = []
        self.labels = {}         # input id -> label text

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "form":
            self._form = {"action": a.get("action", ""), "id": a.get("id", ""), "fields": []}
        elif tag == "label":
            self._label_for = a.get("for")
            self._label_text = []
        elif self._form is not None and tag == "input":
            self._form["fields"].append({
                "name": a.get("name", ""), "id": a.get("id", ""),
                "type": a.get("type", "text"), "value": a.get("value", ""),
                "required": "required" in a or a.get("aria-required") == "true",
            })
        elif self._form is not None and tag == "select":
            self._select = {"name": a.get("name", ""), "id": a.get("id", ""), "type": "select",
                            "required": "required" in a, "options": [], "value": ""}
        elif self._select is not None and tag == "option":
            self._select["options"].append(a.get("value", ""))
        elif self._form is not None and tag == "textarea":
            self._textarea = {"name": a.get("name", ""), "id": a.get("id", ""),
                              "type": "textarea", "required": "required" in a, "value": ""}

    def handle_data(self, data):
        if self._label_for is not None:
            self._label_text.append(data)

    def handle_endtag(self, tag):
        if tag == "form" and self._form is not None:
            self.forms.append(self._form)
            self._form = None
        elif tag == "label" and self._label_for is not None:
            text = " ".join("".join(self._label_text).split())
            if text:
                self.labels[self._label_for] = text
            self._label_for = None
        elif tag == "select" and self._select is not None and self._form is not None:
            self._form["fields"].append(self._select)
            self._select = None
        elif tag == "textarea" and self._textarea is not None and self._form is not None:
            self._form["fields"].append(self._textarea)
            self._textarea = None


def fetch_form(url):
    """Returns (html, form_dict, labels). Raises SystemExit via out() on failure."""
    try:
        resp = requests.get(url, headers={"User-Agent": UA}, timeout=TIMEOUT)
    except requests.RequestException as e:
        out({"ok": False, "error_code": "network", "message": str(e)}, 5)
    if resp.status_code >= 500:
        out({"ok": False, "error_code": "network", "message": f"HTTP {resp.status_code}"}, 5)
    if resp.status_code >= 400:
        out({"ok": False, "error_code": "unsupported",
             "message": f"HTTP {resp.status_code} — posting gone or blocked"}, 3)
    # boards.greenhouse.io often redirects to the React frontend — re-check the final host
    final_portal = detect_portal(resp.url)
    if final_portal in ("unsupported", "greenhouse_react"):
        out({"ok": False, "error_code": "unsupported", "portal": final_portal,
             "message": f"redirected to {resp.url} — no server-rendered form"}, 3)
    html = resp.text
    parser = FormParser()
    parser.feed(html)
    # the application form is the one containing a file input or an email field
    form = None
    for f in parser.forms:
        names = " ".join(fld["name"] for fld in f["fields"])
        types = [fld["type"] for fld in f["fields"]]
        if "file" in types or "email" in names or f["id"] == "application_form":
            form = f
            break
    return html, form, parser.labels


def annotate(form, labels):
    for fld in form["fields"]:
        label = labels.get(fld.get("id", ""), "")
        if label:
            fld["label"] = label
        fld.pop("id", None)
    return [f for f in form["fields"] if f["name"] and f["type"] not in ("submit", "button")]


def cmd_probe(args):
    portal = detect_portal(args.url)
    if portal == "himalayas":
        probe_himalayas(args.url)
    if portal == "smartrecruiters":
        probe_smartrecruiters(args.url)
    if portal in ("unsupported", "greenhouse_react"):
        out({"ok": False, "error_code": "unsupported", "portal": portal,
             "message": "no server-rendered public form for this host"}, 3)
    html, form, labels = fetch_form(args.url)
    captcha = any(m in html for m in CAPTCHA_MARKERS)
    if captcha:
        out({"ok": False, "error_code": "captcha", "portal": portal,
             "message": "CAPTCHA present — submit manually"}, 3)
    if form is None:
        out({"ok": False, "error_code": "unsupported", "portal": portal,
             "message": "no application form found on page"}, 3)
    out({"ok": True, "portal": portal, "captcha": False,
         "action": urljoin(args.url, form["action"] or args.url),
         "fields": annotate(form, labels)})


def build_payload(form, labels, answers, resume, cover_letter):
    data, files, unanswered_required = {}, {}, []
    for fld in form["fields"]:
        name, ftype = fld["name"], fld["type"]
        if not name or ftype in ("submit", "button"):
            continue
        if ftype == "file":
            low = name.lower()
            if "cover" in low and cover_letter:
                files[name] = cover_letter
            elif resume:
                files[name] = resume
            elif fld["required"]:
                unanswered_required.append(name)
        elif ftype == "hidden":
            data[name] = fld["value"]  # CSRF tokens et al. pass through untouched
        elif name in answers:
            data[name] = answers[name]
        elif fld.get("value"):
            data[name] = fld["value"]
        else:
            data[name] = ""
            if fld["required"]:
                unanswered_required.append(name)
    return data, files, unanswered_required


def cmd_submit(args):
    portal = detect_portal(args.url)
    if portal in ("himalayas", "smartrecruiters"):
        out({"ok": False, "error_code": "manual_portal", "portal": portal,
             "message": "probe-only portal — submission is always manual"}, 3)
    if portal in ("unsupported", "greenhouse_react"):
        out({"ok": False, "error_code": "unsupported", "portal": portal}, 3)
    answers = json.loads(Path(args.answers).read_text(encoding="utf-8")) if args.answers else {}
    resume = Path(args.resume) if args.resume else None
    cover = Path(args.cover_letter) if args.cover_letter else None
    for f in (resume, cover):
        if f and not f.exists():
            out({"ok": False, "error_code": "bad_args", "message": f"missing file {f}"}, 6)

    html, form, labels = fetch_form(args.url)  # fresh fetch = fresh CSRF token
    if any(m in html for m in CAPTCHA_MARKERS):
        out({"ok": False, "error_code": "captcha", "portal": portal}, 3)
    if form is None:
        out({"ok": False, "error_code": "unsupported", "portal": portal,
             "message": "no application form found"}, 3)

    data, files, missing = build_payload(form, labels, answers, resume, cover)
    if missing:
        out({"ok": False, "error_code": "validation", "portal": portal,
             "message": f"required fields unanswered: {missing}"}, 4)

    action = urljoin(args.url, form["action"] or args.url)
    if args.dry_run:
        out({"ok": True, "action": "dry_run", "portal": portal, "post_to": action,
             "data": {k: v for k, v in data.items() if "token" not in k.lower()},
             "files": {k: str(v) for k, v in files.items()}})

    file_handles = {k: (v.name, open(v, "rb"), "application/pdf") for k, v in files.items()}
    try:
        resp = requests.post(action, data=data, files=file_handles,
                             headers={"User-Agent": UA, "Referer": args.url},
                             timeout=TIMEOUT, allow_redirects=True)
    except requests.RequestException as e:
        out({"ok": False, "error_code": "network", "message": str(e)}, 5)
    finally:
        for _, fh, _ in file_handles.values():
            fh.close()

    body = resp.text.lower()
    success = (resp.status_code < 400 and
               ("thank" in body or "/thanks" in resp.url or "confirmation" in body
                or "application submitted" in body or "received your application" in body))
    if success:
        out({"ok": True, "action": "submitted", "portal": portal,
             "final_url": resp.url, "http_status": resp.status_code})
    if resp.status_code >= 500:
        out({"ok": False, "error_code": "network", "message": f"HTTP {resp.status_code}"}, 5)
    # extract inline error hints for the retry
    errors = re.findall(r'class="[^"]*(?:error|invalid)[^"]*"[^>]*>([^<]{3,120})', resp.text)
    out({"ok": False, "error_code": "validation", "http_status": resp.status_code,
         "message": "; ".join(dict.fromkeys(e.strip() for e in errors)) or
                    "submission not confirmed by response page"}, 4)


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    pr = sub.add_parser("probe")
    pr.add_argument("--url", required=True)
    sb = sub.add_parser("submit")
    sb.add_argument("--url", required=True)
    sb.add_argument("--answers")
    sb.add_argument("--resume")
    sb.add_argument("--cover-letter")
    sb.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    cmd_probe(args) if args.cmd == "probe" else cmd_submit(args)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        print(json.dumps({"ok": False, "error_code": "internal", "message": str(e)}))
        sys.exit(6)
