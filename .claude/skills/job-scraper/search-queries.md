# Search Queries for Job Scraper

## Search Sites

Primary (remote-first, international, Africa-friendly):
- **linkedin.com/jobs** — use `-l "Remote"` or Africa/Europe overlap; filter for sponsorship-friendly employers
- **wellfound.com** (AngelList) — startups, often remote-friendly
- **remoteok.com** — remote-only listings
- **weworkremotely.com** — remote tech roles
- **remotive.com** — curated remote jobs
- **himalayas.app** — remote jobs with timezone filters
- **andela.com** — Africa-focused tech talent marketplace
- **devex.com** — development/NGO/impact sector (adjacent opportunities)
- **flexjobs.com** — vetted remote listings (may need subscription)
- **otta.com** — startup roles, some remote
- **arc.dev** — remote developer/ML roles
- **ai-jobs.net** — AI/ML specific
- **google.com/search** — `site:greenhouse.io OR site:lever.co "machine learning" remote sponsorship`

Niche (remote-first + Africa-friendly hiring, added 2026-11):
- **jobgether.com** — remote aggregator with Africa location filters
- **turing.com** — remote dev/ML marketplace, actively vets African engineers
- **gebeya.com** — pan-African tech talent marketplace
- **tunga.io** — African developers placed into remote roles
- **shortlist.net** — East Africa recruiting platform (Kenya focus)
- **reliefweb.int/jobs** — NGO/UN/dev-sector roles, heavy Nairobi + remote data/ML presence
- **impactpool.org** — impact-sector and UN-system jobs, many remote/East Africa
- **workingnomads.com** — curated remote listings
- **dynamitejobs.com** — remote-first companies, global hiring

Secondary (regional / unconventional):
- **brightermonday.co.ke** — Kenya jobs (local + some remote)
- **fuzu.com** — East Africa
- **myjobmag.co.ke** — Kenya
- **jobberman.com** — broader Africa
- Direct company career pages via Google `site:` filters

**Portal outcome tracking:** Record each application source in `job_search_tracker.csv` (`source` column). Update aggregate counts in `job_scraper/portal_outcomes.json` when running `/outcome` so we can compare which boards produce interviews.

**Do NOT prioritize:** Danish-only boards (Jobindex, Jobnet, Jobbank, Jobdanmark) unless user explicitly requests — candidate is remote-first in East Africa.

## Pre-Filter Rules (apply before presenting)

Skip or deprioritize postings that:
- State **no visa sponsorship** / **must have existing work authorization** with no exceptions
- Are **strictly on-site** in US/EU/UK with no remote or relocation path
- Are **unpaid** internships or volunteer full-time roles
- Require **citizenship-only** eligibility

Flag (don't auto-skip) postings that:
- Say "remote" but list US/EU/UK only — may still need sponsorship clarification
- Are contractor-only (C2C/1099) for international hires

## Query Categories

### Priority 1: Core ML / AI / Data Science Roles

```
site:linkedin.com/jobs "machine learning engineer" remote
site:linkedin.com/jobs "AI engineer" remote Africa OR "work from anywhere"
site:remoteok.com machine learning
site:wellfound.com "ML engineer" remote
site:weworkremotely.com "machine learning" OR "data scientist"
site:ai-jobs.net remote
site:andela.com "machine learning" OR "data scientist"
site:jobgether.com remote "data scientist" OR "machine learning" Africa
site:turing.com "machine learning" OR "data scientist" remote
site:workingnomads.com "machine learning" OR "data science"
site:dynamitejobs.com "machine learning" OR "data"
"data scientist" remote "visa sponsorship" OR "sponsor"
"machine learning engineer" remote "international" -"must be authorized" -"no sponsorship"
```

### Priority 2: NLP / LLM / MLOps (strongest technical niche)

```
site:linkedin.com/jobs "NLP engineer" OR "LLM engineer" remote
site:linkedin.com/jobs "MLOps" remote
site:remoteok.com NLP OR LLM OR MLOps
"RAG" "machine learning" remote job
"LangChain" OR "Hugging Face" engineer remote
site:greenhouse.io "machine learning" remote
```

### Priority 3: Health Tech / Digital Transformation / Innovation

```
site:linkedin.com/jobs "health" "machine learning" remote
site:linkedin.com/jobs "digital transformation" AI OR "machine learning"
site:devex.com data OR "machine learning" OR innovation
site:reliefweb.int "data scientist" OR "machine learning" remote OR Nairobi
site:impactpool.org "data scientist" OR "data science" OR "machine learning"
"health informatics" "data scientist" remote
"innovation" "artificial intelligence" remote engineer
```

### Priority 4: Adjacent / Unconventional (transferable skills)

```
site:linkedin.com/jobs "research engineer" machine learning remote
site:linkedin.com/jobs "applied scientist" remote
site:linkedin.com/jobs "technical consultant" AI OR data remote
site:wellfound.com "founding engineer" ML OR AI
"graduate" OR "new grad" "machine learning" remote 2026
site:arc.dev machine learning remote
```

### Priority 5: East Africa + Remote Hybrid

```
site:linkedin.com/jobs "machine learning" Kenya OR Rwanda remote
site:brightermonday.co.ke data scientist OR "machine learning"
site:fuzu.com "data" OR "artificial intelligence"
site:shortlist.net data OR "machine learning"
site:gebeya.com "data" OR "machine learning" OR AI
site:tunga.io "machine learning" OR "data science" OR remote
"remote" "East Africa" "data scientist" OR "ML engineer"
```

## Location Filter

**PASS:**
- Fully remote (global or work-from-anywhere)
- Remote with EAT-friendly overlap (UTC+3)
- Onsite/hybrid in Rwanda or Kenya
- Relocation anywhere **with sponsorship**

**FAIL:**
- Strict location lock + no sponsorship
- US/EU-only on-site without relocation path

**Candidate base:** Rwanda / Kenya (EAT, UTC+3)

## Date Filter

Only include jobs posted within the last 14 days, or with an application deadline that has not yet passed. If a posting date cannot be determined, include it but flag as "date unknown".

## Adapting Queries

If the user specifies a focus area, select queries from the matching category and generate 2-3 custom queries. Examples:
- `/scrape NLP` → Priority 2 queries + custom NLP/RAG/African languages queries
- `/scrape health` → Priority 3 queries + Savannah/GRA-aligned health ML queries
- `/scrape broad` → run all priority categories

## LinkedIn CLI (when available)

Use the repo's linkedin-search skill for structured queries:
```bash
bun run skills/linkedin-search/cli/src/cli.ts search -q "machine learning engineer" -l "Remote"
bun run skills/linkedin-search/cli/src/cli.ts search -q "AI engineer" -l "Kenya"
```
