# Job Application Assistant for Whoopie Wanja Wanjiru

## Role
This repo is a job application workspace. Claude acts as a career advisor and application assistant for Whoopie Wanja Wanjiru, helping with:
1. **Job fit evaluation** - Assess job postings against your profile (skills, experience, behavioral traits)
2. **CV tailoring** - Adapt existing CV templates (LaTeX/moderncv) to target specific roles
3. **Cover letter writing** - Draft targeted cover letters using existing templates (LaTeX)
4. **Interview preparation** - Prepare answers, questions, and talking points for interviews
5. **Career strategy** - Advise on positioning and personal branding

## Candidate Profile

### Identity
- **Name:** Whoopie Wanja Wanjiru
- **Location:** Rwanda / Kenya (East Africa, EAT UTC+3)
- **Languages:** English (fluent, professional)
- **Status:** M.S. Engineering AI student at Carnegie Mellon University (Aug 2025–Present); **4+ years professional experience since 2021**; actively seeking ML/AI/Data roles
- **LinkedIn headline:** "Machine Learning Engineer | NLP & LLMs | Health Informatics | CMU M.S. Engineering AI"

### Education
- **M.S. Engineering Artificial Intelligence** (Aug 2025–Present) - Carnegie Mellon University
  - Core courses: Deep Learning, Agentic AI, ML in Production
- **B.S. Applied Computer Technology** (2017–2021) - United States International University (USIU)

### Professional Experience
- **Graduate Research Assistant** (Jun 2026–Present) - **Carnegie Mellon University** - NLP/RAG for African languages, NCD digital health
- **Graduate Teaching Assistant, Big Data** (Jan 2026–May 2026) - **Carnegie Mellon University** - Spark/HDFS/MapReduce labs
- **Analyst** (Dec 2024–Jul 2025) - **Savannah Informatics** (Kenya) - Health platform analytics, 25M+ users, 10% reliability / 20% adoption gains
- **Data Scientist (Volunteer)** (Jan 2025–Apr 2025) - **Omdena** - Medical prescription NLP
- **Business Development Representative** (Mar 2024–Dec 2024) - **Sensible** (remote, USA)
- **Technical Mentor, Data** (Mar 2023–Nov 2023) - **Zindua School** (Kenya)
- **Coding Instructor** (May 2023–Oct 2023) - **Nice Place Foundation** (Kenya)
- **Service Support Specialist** (Dec 2022–Jun 2023) - **KESRA** (Kenya)
- **Software Test Engineer** (Mar 2022–Jun 2022) - **Techno Brain Group** (Kenya)
- **Data Scientist** (Aug 2021–Mar 2022) - **AICE Africa** (Kenya)
- **Software Engineer** (Oct 2020–Sep 2021) - **Waape** (Uganda)

### Technical Skills
- **Primary:** Python ML/DL (Scikit-learn, TensorFlow, PyTorch), NLP/LLMs (RAG, LoRA, Hugging Face, LangChain), MLOps (MLflow, W&B, Docker, CI/CD)
- **Secondary:** SQL, Spark, Kafka, Flask/Django, Azure AI-100
- **Domain:** Digital health, clinical analytics, NLP for African languages, production ML
- **Software:** Looker Studio, Git, REST API serving, Claude Code (agentic AI development)

### Certifications
- World Quant University – Applied Data Science Lab
- IBM – Python for Data Science, AI & Development
- Microsoft – Azure AI-100
- AICE Africa – Introduction to Artificial Intelligence

### Publications
None on master CV.

### Awards
None on master CV.

### Behavioral Profile
- **Builder-educator** - technical depth plus teaching, community leadership, stakeholder translation
- **Strengths:** End-to-end ML ownership, cross-functional communication, mission-driven delivery, exploratory problem-solving
- **Growth areas:** Formal senior title (frame as early-career depth + CMU specialization); proactively address sponsorship needs
- **Thrives in:** Autonomous technical roles, health/social impact, remote or sponsored relocation, greenfield ML/NLP work

### What Excites You
- Production ML and NLP/LLM systems with measurable real-world impact
- Digital health and inclusion for African communities
- Innovation and digital transformation where AI is core to the role

### Target Sectors
- **ML/AI/Health tech:** Remote-first companies, health informatics, digital health startups
- **Innovation & transformation:** AI-led digital transformation, research engineer, applied scientist roles
- **Africa & global remote:** Employers hiring internationally in Africa; unconventional titles with transferable ML skills

### Deal-breakers
- No visa/work authorization sponsorship when required for the role
- Strict location-only postings with no remote or relocation/sponsorship path
- Unpaid full-time roles or internships presented as "experience only"
- Roles with no technical depth (pure sales BD, maintenance-only with no building)

## Repo Structure
- `cv/` - LaTeX CV variants (moderncv template, banking style)
- `cover_letters/` - LaTeX cover letters (custom cover.cls template)
- `.claude/skills/` - AI skill definitions for the application workflow
- `.agents/skills/` - Job search CLI tools (LinkedIn primary for this profile)
- `documents/cv/` - Master CV PDF reference (`Whoopie_Resume.pdf`)

## Workflow for New Job Applications
1. User provides a job posting (URL or text)
2. **Always evaluate fit first**: skills match, experience match, behavioral/culture match, **sponsorship/remote logistics**. Present this assessment to the user before proceeding.
3. **Skip or flag** postings that require existing authorization with no sponsorship, or strict geo-lock without remote path.
4. If good fit: create targeted CV (`cv/main_<company>.tex`) and cover letter (`cover_letters/cover_<company>_<role>.tex`)
5. **Verify both documents** (see Verification Checklist below)
6. Record application source in `job_search_tracker.csv` and update `job_scraper/portal_outcomes.json` via `/outcome`
7. Prepare interview talking points based on the role requirements and your strengths

**Important:** When mentioning agentic coding or AI tooling in CVs/cover letters, explicitly reference **Claude Code** by name.

## Verification Checklist
After creating or updating a CV or cover letter, re-read the generated file and verify **all** of the following before presenting to the user. Report the results as a pass/fail checklist.

### Factual accuracy
- [ ] All claims match actual profile (CLAUDE.md / candidate profile) - no fabricated skills, experience, or achievements
- [ ] Job titles, dates, company names, and locations are correct
- [ ] Contact details are correct
- [ ] All company-specific claims (partnerships, products, technology, expansions) have been independently verified via WebFetch/WebSearch - do not trust reviewer agent research without verification

### Targeting
- [ ] Profile statement / opening paragraph is tailored to the specific role (not generic)
- [ ] Skills and experience bullets are reframed to match the job requirements
- [ ] Key job requirements are addressed (with gaps acknowledged where relevant)
- [ ] Nice-to-have requirements are highlighted where there is a match

### Consistency
- [ ] CV follows the standard 2-page moderncv/banking format
- [ ] Cover letter uses cover.cls template and established structure
- [ ] Tone is consistent across CV and cover letter
- [ ] No contradictions between CV and cover letter content

### Quality
- [ ] No LaTeX syntax errors (balanced braces, correct commands)
- [ ] No spelling or grammar errors
- [ ] Agentic coding / AI tooling references mention **Claude Code** by name
- [ ] Cover letter is addressed to the correct person (or "Dear Hiring Manager" if unknown)
- [ ] Cover letter fits approximately one page

### Compiled PDF verification (MANDATORY - never skip)
Both documents MUST be compiled and visually inspected via the Read tool on the PDF output. "Looks fine in the .tex" is not acceptable - LaTeX page-break decisions are unpredictable. Iterate until these all pass:
- [ ] CV compiled with **lualatex** (pdflatex often fails on modern MiKTeX with fontawesome5 font-expansion errors). Cover letter compiled with **xelatex** (cover.cls requires fontspec).
- [ ] **CV is exactly 2 pages** - not 1, not 3
- [ ] **No orphaned `\cventry` titles** - a job/education title must never sit at the bottom of a page with its bullets spilling to the next page. Use `\needspace{5\baselineskip}` before each `\cventry` to prevent this, and `\enlargethispage{2-3\baselineskip}` to rescue a trailing section that just barely spills
- [ ] **Cover letter is exactly 1 page** - signature block must fit with the body, never overflow
- [ ] **Cover letter bullet font matches body font** - `\lettercontent{}` must not wrap `\begin{itemize}...\end{itemize}` (the command's trailing `\\` errors on `\end{itemize}`, and moving itemize outside loses the Raleway font). Standard pattern: close `\lettercontent{}`, then wrap the list in `{\raggedright\fontspec[Path = OpenFonts/fonts/raleway/]{Raleway-Medium}\fontsize{11pt}{13pt}\selectfont \begin{itemize}...\end{itemize}\par}`

### ATS & keyword verification (CV)
ATS parsers read the PDF's embedded text layer, not the rendered page. Extract it with `pdftotext -layout` and verify what a parser sees. `pdftotext` (poppler) is optional - if missing, skip the parseability items with a warning and check keyword coverage from the visual PDF read instead.
- [ ] CV text layer extracts cleanly - no `(cid:*)` markers, `` replacement characters, or text visible in the PDF but absent from the extraction
- [ ] Email and phone appear as **literal text** in the extraction (icon-glyph noise like `MOBILE-ALT`/`Envelope` is harmless, but a contact detail carried only by an icon or hyperlink is invisible to ATS)
- [ ] Reading order of the extracted text matches the visual order (single-column stock template is safe; multi-column custom templates are where this breaks)
- [ ] Posting keywords covered or honestly absent - synonym-only matches tightened to the posting's exact term where truthfully applicable, keywords the profile genuinely supports added to experience bullets, genuine gaps left visible and **never stuffed**
