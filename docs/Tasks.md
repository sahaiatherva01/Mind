# Implementation Backlog — Mind V2

Priorities: P0 = Phase exit blocker, P1 = Phase feature, P2 = Advanced.

---

## Phase 0 — Baseline & Discovery
- [x] P0 Verify backend test suite (21/21 passed) and frontend build (`tsc -b && vite build` clean).
- [x] P0 Save `docs/MIND_V2_SPEC.md` and define parked backlog in `docs/BACKLOG.md`.
- [x] P0 Update documentation package to 5-tier architecture (`README.md`, `PRD.md`, `Architecture.md`, `Rules.md`, `Phases.md`, `Tasks.md`, `API.md`).
- [ ] P0 Produce Baseline Report and wait for `GO PHASE 1`.

---

## Phase 1 — Scoped RBAC Refactor & 5 Tiers
- [x] P0 Implement `RoleAssignment`, `Band`, and `AcademicYear` models.
- [x] P0 Build central `authorize(actor, action, resource)` policy engine in `backend/app/core/policies.py`.
- [x] P0 Construct machine-readable `backend/app/core/permission_matrix.py` and generate comprehensive tests.
- [x] P0 Alembic migration transitioning legacy `users.role` to `RoleAssignment`.
- [x] P0 Platform Admin API & UI: School lifecycle, School Admin & Coordinator provisioning, feature flags.
- [x] P0 School Admin API & UI: School profile/branding, academic structure, class bands, settings.
- [x] P0 Eradicate all legacy `users.role` dependencies.

---

## Phase 2 — Academic Coordinator & Assignment Matrix
- [x] P0 Academic Coordinator dashboard scoped strictly to assigned band.
- [x] P0 Teacher management: CRUD, status toggling, password resets within band.
- [x] P0 Bulk Excel teacher onboarding with pre-commit validation and row-level error reporting.
- [x] P0 Assignment matrix (Teacher × Class × Section × Subject).
- [x] P0 Enforce exactly one Class Teacher per section constraint.
- [x] P0 Band-scoped curriculum chapter and topic viewer.

---

## Phase 3 — Teacher: Students, Rosters & Credentials
- [x] P0 Class Teacher single and CSV student onboarding with roll number assignment.
- [x] P0 Roll number uniqueness constraint per `(school, year, class, section)` on `StudentEnrollment`.
- [x] P0 Roster state machine (`Pending` → `Verified` → `Locked`) and `RosterChangeRequest` workflow.
- [x] P0 Student credential generation using school template, printable login slips, and forced first-login password change.
- [x] P0 Audit trail verification for all roster changes.

---

## Phase 4 — Materials & My Learning
- [x] P0 Implement full `content` module (models, service, router, policies).
- [x] P0 Material upload, tagging (class/subject/chapter), and section distribution.
- [x] P0 Student "My Learning" view with material open event logging.
- [x] P1 Agent Track A1: PDF text extraction and chunking pipeline in background worker.
- [x] P1 Question Extractor LangGraph agent with side-by-side review interface.

---

## Phase 5 — Assignments & Notifications
- [ ] P0 Implement full `notifications` module (in-app store + email backend adapter).
- [ ] P0 Assignment lifecycle (draft → published → submission → evaluation).
- [ ] P1 Agent Track A2: Migrate AI Studio generation to LangGraph `StateGraph` (Worksheets, Quizzes, Papers, Custom Questions).
- [ ] P1 Assignment Generator and Difficulty Tagger agents with structured outputs and SymPy verification.

---

## Phase 6 — Analytics (4 Levels + Cross-Analytics)
- [ ] P0 School Admin analytics (school-wide trends, teacher activity indicators).
- [ ] P0 Coordinator analytics (band summaries, cross-section difficulty comparison).
- [ ] P0 Teacher 4-level analytics (individual, class, subject, cross-analytics) + material engagement correlation.
- [ ] P0 Student personal performance map (strictly private).
- [ ] P1 Agent Track A5: Analytics Insight agent using scoped tool functions with zero text-to-SQL.

---

## Phase 7 — Exams, Calendar, Report Cards & Approvals
- [ ] P0 Academic calendar with exam clash detection and policy limits.
- [ ] P0 Band-wide exam planner with Set A–D generation from common blueprints.
- [ ] P1 Evaluation assistant LangGraph agent for subjective grading suggestions.
- [ ] P0 Resilient exam player with autosave and tab-switch logging.
- [ ] P1 Branded report card designer and PDF generation; gradebook.

---

## Phase 8 — Advanced Non-Parked Workflows
- [ ] P1 Early-warning dashboard and Coordinator intervention list.
- [ ] P1 Smart student groups and one-click remedial assignment generation.
- [ ] P1 Substitution manager with automated temporal access revocation.
- [ ] P2 Student goal tracker, smart revision list, and structured teacher query form.

