# Job Evaluation Framework

## Scoring Dimensions

Evaluate each job posting against these five dimensions:

### 1. Technical Skills Match (0-100)
How well do the required/preferred skills align with the candidate's capabilities?

| Score | Meaning |
|-------|---------|
| 80-100 | Core requirements are primary skills |
| 60-79 | Most requirements match, 1-2 gaps that are learnable |
| 40-59 | Partial match, significant upskilling needed |
| 0-39 | Fundamental mismatch |

**Strong match areas:** Python ML/DL (Scikit-learn, TensorFlow, PyTorch), NLP/LLMs (RAG, fine-tuning, Hugging Face, LangChain), MLOps (MLflow, W&B, Docker, CI/CD), Spark/big data, health informatics, REST API serving
**Moderate match areas:** Cloud-specific stacks beyond Azure AI-100 cert, pure software engineering without ML, product management, formal research publications
**Weak match areas:** Roles requiring 5+ years senior/staff title without transferable framing, domains with zero overlap (e.g. pure finance quant with no ML), hardware/embedded with no software ML angle

### 2. Experience Match (0-100)
Does work history align with what they're looking for?

| Score | Meaning |
|-------|---------|
| 80-100 | Direct experience in the same domain and role type |
| 60-79 | Related experience, transferable skills clear |
| 40-59 | Adjacent experience, would need to make the case |
| 0-39 | Unrelated experience |

**Strong:** ML Engineer, Data Scientist, AI Engineer, NLP/LLM engineering, health tech analytics, MLOps, digital transformation with ML component — **4+ years since 2021** including AICE Africa (Data Scientist), Savannah (health analytics), Omdena (clinical NLP), CMU research/teaching
**Moderate:** Innovation roles, technical consulting, data engineering (Spark/Kafka), BDR/client-facing roles with transferable stakeholder skills
**Entry-level:** Not applicable — candidate exceeds typical new-grad experience for data science roles

### 3. Behavioral/Culture Fit (0-100)
Does the role and company culture match the behavioral profile?

| Score | Meaning |
|-------|---------|
| 80-100 | Culture strongly matches behavioral preferences |
| 60-79 | Mixed signals but mostly compatible |
| 40-59 | Some friction areas |
| 0-39 | Significant culture mismatch |

**Red flags to research:** No sponsorship when required, strict geo-lock ("must be in US/EU with no exceptions"), unpaid internships, maintenance-only roles, poor reviews on management/support for international hires

### 4. Location & Logistics (Pass/Fail + Notes)

**Automatic FAIL (deal-breaker):**
- Requires existing work authorization in a country where candidate cannot work without sponsorship, and posting explicitly states **no sponsorship**
- Strict on-site only in a location candidate cannot legally work from, with no relocation/sponsorship path
- Unpaid roles or "volunteer" full-time expectations

**PASS:**
- Fully remote (global or Africa-friendly)
- Remote with reasonable EAT overlap (UTC+3)
- Relocation offered with visa/work authorization sponsorship
- Hybrid/onsite in Rwanda or Kenya without sponsorship barrier

**FLAG (discuss with user):**
- "Remote" but restricted to US/EU/UK only — often still requires sponsorship
- Contractor-only arrangements (1099/C2C) for international hires
- Frequent travel or odd hours with poor overlap with EAT

**Candidate logistics:**
- **Based in:** Rwanda and Kenya (EAT, UTC+3)
- **Work authorization:** Cannot work without sponsorship outside current authorization scope
- **Relocation:** Open anywhere for the right offer with sponsorship
- **Preferred:** Remote-first employers hiring internationally in Africa

### 5. Career Alignment & Motivation (0-100)
Does this role advance career goals and contain tasks that energize?

| Score | Meaning |
|-------|---------|
| 80-100 | Strongly aligned with career direction, clear growth path |
| 60-79 | Good role but only partially aligned with long-term goals |
| 40-59 | Decent job but doesn't build toward career goals |
| 0-39 | Dead end or backwards step |

**Career goals:**
- Build and deploy production ML/NLP systems with real-world impact, especially in health and Africa
- Deepen expertise in LLMs, agentic AI, and MLOps at scale
- Join organizations doing innovation or digital transformation where ML is central, not peripheral

**Motivation filter:** Evaluate not just whether you *can* do the tasks, but whether the tasks will *energize* you. Consider:
- Tasks that energize: building ML/NLP pipelines, RAG/LLM systems, model evaluation and deployment, health/social-impact applications, teaching and enabling others, greenfield technical problems
- Tasks that drain: pure ticket maintenance with no model building, roles with no technical depth, unpaid work, opaque sales-only KPIs
- Non-task factors: sponsorship clarity, remote flexibility, mission alignment, autonomy, growth into AI/ML IC track

**Life situation alignment:** Consider personal constraints:
- **Security:** M.S. student graduating December 2026; prioritizing paid roles with clear authorization path
- **Flexibility:** Remote or relocatable; EAT timezone base
- **Professional development:** CMU coursework in Deep Learning, Agentic AI, ML in Production — seek roles that use and extend this

### 6. Salary Benchmark (Optional)

If the salary lookup tool is configured (`salary_data.json` exists), look up the company:
```
python salary_lookup.py "<Company Name>" --json
```

If a city is known from the posting, add `--city "<City>"` to narrow results.

If the salary tool is not configured, skip this section.

## Output Format

Present the evaluation as:

```
## Job Fit Evaluation: [Role] at [Company]

| Dimension | Score | Notes |
|-----------|-------|-------|
| Technical Skills | XX/100 | [brief note] |
| Experience Match | XX/100 | [brief note] |
| Behavioral Fit | XX/100 | [brief note] |
| Location | PASS/FAIL | [brief note] |
| Career Alignment | XX/100 | [brief note] |

**Overall Score: XX/100** (weighted average of scored dimensions)

### Verdict: [Strong Fit / Good Fit / Moderate Fit / Weak Fit / Poor Fit]

### Key Strengths for This Role
- [bullet points]

### Gaps to Address
- [bullet points]

### Recommendation
[1-2 sentences: apply/skip/apply with caveats]

### Company Research Checklist
- [ ] Checked company website (mission, values, recent news)
- [ ] Checked review sites (Glassdoor, etc.)
- [ ] Checked LinkedIn for team size, recent hires, connections
- [ ] Verified sponsorship / remote policy for international candidates in Africa
- [ ] Identified network contacts who may know the team/manager
```

## Weighting
- Technical Skills: 30%
- Experience Match: 25%
- Behavioral Fit: 15%
- Career Alignment: 30%

(Location is pass/fail, not weighted)

## Thresholds
- **Strong Fit** (75+): Definitely apply, tailor everything
- **Good Fit** (60-74): Apply, address gaps in cover letter
- **Moderate Fit** (45-59): Consider carefully, discuss with user
- **Weak Fit** (30-44): Probably skip unless strategic reasons
- **Poor Fit** (<30): Skip

## Unconventional Roles

Whoopie is open to unconventional titles if transferable skills are clear (innovation, digital transformation, technical program, research engineer, applied scientist, etc.). Score on underlying tasks, not title alone. If the role is 50%+ ML/building/analytics, treat as in-scope even if the title is non-standard.

## Pre-Application: Call the Employer (Best Practice)

Before writing the application, consider whether the candidate should call the contact person listed in the posting. **Only call if there are substantive questions** - never call just to "be remembered."

### When to Suggest Calling
- Sponsorship or remote-from-Africa policy is unclear
- The posting has unclear or ambiguous requirements
- It's unclear which competencies are essential vs. nice-to-have

### Good Questions to Ask
- "Do you sponsor work authorization for candidates based in East Africa?"
- "Is this role fully remote globally, or restricted to specific countries?"
- "What are the primary challenges in this role?"
- "Which competencies are most critical for success in this position?"

### Rules for the Call
- Prepare a 30-second elevator pitch about ML/NLP + health tech background
- The call's purpose is **gathering information**, not delivering a pitch
- Take notes - use what you learn to tailor the application
