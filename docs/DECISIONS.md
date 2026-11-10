# Decision Log — Mind

This document records architectural, product, and technical decisions made during the design and construction of Mind.

---

## 2026-11-07 — DEC-001: Phase 0 Baseline Decisions & Operating Parameters

- **Status:** Approved
- **Context:** Following Phase 0 discovery, core configuration parameters were approved for Mind V1.

### Decisions:
1. **Hosting Target (Render):**
   - *Decision:* Deployable to Render as web service container(s) + managed PostgreSQL + Redis. Local development via Docker Compose and standalone local virtualenv/npm scripts.
   - *Reason:* Fits low-cost solo-founder budget with zero Kubernetes overhead.
   - *Reversible:* Yes (containerized architecture runs anywhere).

2. **AI Provider (Google Gemini + Mock Provider):**
   - *Decision:* Google Gemini (`gemini-1.5-flash` and `gemini-1.5-pro`) via a provider-agnostic AI Gateway interface. Include a zero-cost deterministic `MockAIProvider` for test suites, CI, and local offline dev.
   - *Reason:* Fast, cost-effective structured JSON generation with large context window.
   - *Reversible:* Yes (gateway abstracts model calls).

3. **Curriculum & Board Focus (ICSE / ISC):**
   - *Decision:* Seed ICSE (Classes 9–10) and ISC (Classes 11–12) syllabi with primary focus on Science and Math stream: Physics, Chemistry, Mathematics, Biology, plus Computer Science, English, History, Geography.
   - *Reason:* Direct alignment with pilot institution context.
   - *Reversible:* Yes (curriculum nodes are database rows).

4. **Identity & User Onboarding (Excel/CSV Bulk Import + Strict 3 Roles):**
   - *Decision:* Maintain strict 3-role model (`Admin`, `Teacher`, `Student`) per Non-Negotiable #2. Institute Admin and Academic Coordinator map to the `Admin` role (with title/designation metadata). Teachers and Students onboarded via Admin UI or Excel (`.xlsx`) / CSV bulk upload with row-level validation.
   - *Reason:* Preserves least-privilege security invariants while fulfilling administrative bulk onboarding needs.
   - *Reversible:* Yes.

5. **Storage Architecture (Dual Local + S3 Compatible):**
   - *Decision:* Storage service interface supporting both Local Filesystem (development/testing/zero-cloud setup) and S3-compatible cloud storage (AWS S3 / Render Disk / Cloudflare R2).
   - *Reason:* Immediate local reliability without cloud dependencies; seamless switch in production.
   - *Reversible:* Yes.

6. **Email & Notifications:**
   - *Decision:* Mailpit / SMTP catcher in development with graceful console fallback; SMTP / Resend adapter in production.
   - *Reason:* Prevents accidental email leaks during testing.
   - *Reversible:* Yes.

7. **Assessment Result Release:**
   - *Decision:* Default is `manual_by_teacher`. Solutions, rationales, and marks remain strictly invisible to students until the teacher explicitly triggers release. Configurable options for `immediate_on_submit` and `scheduled_datetime`.
   - *Reason:* Prevents answer leakage during multi-batch class tests.
   - *Reversible:* Yes.

8. **Assessment Timing & Autosave:**
   - *Decision:* Server time is authoritative. Single attempt default. 15-second background autosave interval with sync state display. 60-second latency grace period for timed submissions.
   - *Reason:* Guarantees fairness under imperfect school network conditions.
   - *Reversible:* Yes.

9. **ICSE / ISC 40-Question-Type Master Typology:**
   - *Decision:* Question Schema and Generator support the 40 ICSE/ISC Board Exam question types categorized into:
     - **Objective (6):** MCQ, Multiple Select, Fill in the Blanks, True/False, Match the Following, Assertion–Reason.
     - **Written (8):** Very Short Answer, Short Answer, Medium Answer, Long Answer, Definition-Based, Difference-Based, Reasoning-Based, Proof/Derivation-Based.
     - **Visual & Mathematical (9):** Diagram-Based, Label the Diagram, Graph-Based, Table-Based, Chart-Based, Map-Based, Construction-Based, Numerical-Based, Formula-Based.
     - **Application & Analytical (9):** Case-Based, Passage-Based, Source-Based, Data Interpretation, Application-Based, HOTS (Higher Order Thinking Skills), Critical Thinking, Problem-Solving, Experiment-Based.
     - **Computer Science (8):** Output Prediction, Theory + Coding, Code Completion, Error Detection, Debugging, Dry Run, Algorithm Writing, Program Writing, Data Structure Implementation.
   - *Reason:* Covers authentic board exam assessment formats across Science, Mathematics, Humanities, and Computer Science.
   - *Reversible:* Yes (extensible JSON schema).


---

## 2026-11-08 — DEC-002: Psychometric Item Diagnostics & Assessment Exports

- **Status:** Approved & Implemented
- **Context:** FR-15 and FR-18 require teacher visibility into item difficulty, discrimination index, score distribution, and PDF/CSV exports.
- **Decisions:**
  1. **Item Discrimination Formula:** Implemented upper quartile vs. lower quartile comparison:
     $$D = P_{\text{upper}} - P_{\text{lower}}$$
     Categorized with psychometric guidance: $D \ge 0.40$ (Excellent), $0.20 \le D < 0.40$ (Acceptable/Good), and $D < 0.20$ (Needs Review).
  2. **Zero Student Leakage on Export:** Printable HTML exam papers strip all answer keys, rationales, and marking schemes by default. The `include_marking_scheme=true` parameter is strictly guarded by server-side role authorization (`Admin` or `Teacher` only); requests by students return `403 Forbidden`.
  3. **CSV Gradebook Roster:** Generates RFC 4180-compliant CSV containing student names, roll numbers, objective/subjective scores, percentages, and submission timestamps.
- **Reason:** Provides actionable pedagogical diagnostics while preserving strict security invariants.
- **Reversible:** Yes.

---

## 2026-11-10 — DEC-004: Mind V2 5-Tier Scoped Authority Model and LangGraph Orchestration

- **Status:** Approved
- **Context:** Mind expands from a flat 3-role system into a 5-tier scoped academic authority structure matching real school hierarchies.
- **Decisions:**
  1. **5-Tier Role Model:** Exact roles: `Platform Admin` → `School Admin` → `Academic Coordinator` (band-scoped) → `Teacher` (with `Class Teacher` flag) → `Student`. The old single `users.role` column is replaced by `RoleAssignment`.
  2. **Scoped Authorization Engine:** Central `authorize(actor, action, resource)` entry point in `backend/app/core/policies.py` evaluating role + tenant + band + class/section/subject scopes together.
  3. **Configurable Class Bands:** Bands (e.g. 6–8, 9–10, 11–12) are stored as configurable database entities per school, not hard-coded.
  4. **Student Identity & Roll Numbers:** Stable internal `user_id` across promotions. Roll numbers are scoped to `(school, academic_year, class, section)` on `StudentEnrollment`. Login ID template configurable per school (default: admission number).
  5. **Roster Lifecycle & Locking:** Student onboarding by Class Teacher (own section) or Coordinator (own band). Roster lifecycle: `Pending` -> `Verified` -> `Locked`. Pending students cannot authenticate. Post-lock modifications require `RosterChangeRequest` approval.
  6. **Single Class Teacher Invariant:** Exactly one Class Teacher per section per academic year, enforced by unique database constraint.
  7. **No Cross-Band Assignments in V1:** Coordinators create teachers and assignments strictly within their band.
  8. **AI Architecture with LangGraph:** AI Studio generation migrated to LangGraph `StateGraph` workflows with Pydantic structured output, SymPy deterministic math verification, model critics, and bounded repair loops. Deterministic tasks (analytics computation, blueprint marks totals, grading objective items) strictly forbid LLMs.
- **Reason:** Real-world school governance requires fine-grained band and section delegation without cross-boundary data leakage.
- **Reversible:** Architectural core; migrations and tests must adhere strictly.


- **Status:** Approved & Documented
- **Context:** Mind operates in Indian schools with minors (Classes 6–12).
- **Decisions:**
  1. **Data Processor Model:** Mind operates as Data Processor; the School is Data Fiduciary. School certifies parental consent before roster import.
  2. **AI Data Minimization:** Prompts dispatched to external LLMs (Google Gemini) contain zero student personal identifiable information (PII). AI is utilized strictly for curriculum generation and teacher rubric assistance.
- **Reason:** Mandatory compliance with Section 9 of the Digital Personal Data Protection Act, 2023.
- **Reversible:** No (statutory requirement).
