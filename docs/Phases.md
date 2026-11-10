# Delivery Phases & Roadmap — Mind V2

Roadmap is capability-based, structured into 8 discrete human-gated phases. Each phase ends at a human test and approval gate.

---

## Phase 0 — Baseline & Discovery
**Outcome:** Full baseline audit, doc package synchronization, and clean test execution.
- Baseline test pass confirmation.
- Refactor surface cataloging for 5-tier role hierarchy.
- Creation of `PROGRESS.md`, `DECISIONS.md`, and `docs/BACKLOG.md`.
**Exit gate:** Baseline report delivered; human approves `GO PHASE 1`.

---

## Phase 1 — Scoped RBAC Refactor & 5 Tiers
**Outcome:** 5-tier authority model active; legacy role column eradicated.
- `RoleAssignment`, `Band`, `AcademicYear` database entities.
- Central `authorize(actor, action, resource)` policy engine in `core/policies.py`.
- Platform Admin: Provision schools, School Admins, and Academic Coordinators.
- School Admin: School settings, branding, academic structure, and configurable class bands.
- Machine-readable `permission_matrix.py` with generated test suite.
**Exit gate:** All permission matrix tests green; zero paths read the legacy role column.

---

## Phase 2 — Academic Coordinator & Assignment Matrix
**Outcome:** Band-level management operational.
- Coordinator dashboard scoped strictly to band classes (e.g. 9–10).
- Teacher management: create, edit, deactivate, and bulk Excel import with pre-commit validation.
- Assignment matrix (Teacher × Class × Section × Subject).
- Exactly one Class Teacher designated per section.
**Exit gate:** Coordinator cannot access cross-band data; duplicate Class Teacher assignment rejected.

---

## Phase 3 — Teacher: Students, Rosters & Credentials
**Outcome:** Class Teacher student management and end-to-end authority chain.
- Single and CSV student addition by Class Teacher (own section) or Coordinator (own band).
- Roll number uniqueness per `(school, year, class, section)` on enrollment.
- Roster lifecycle: `Pending` → `Verified` → `Locked`; `RosterChangeRequest` post-lock workflow.
- Printable credential slips; forced password change on first student login.
**Exit gate:** Complete authority chain operational (Platform Admin → Coordinator → Teacher → Student login); every action audit-logged.

---

## Phase 4 — Materials & My Learning
**Outcome:** Curriculum-grounded learning materials and AI Question Extractor.
- Complete `content` module: upload, tag, share with sections, expiry.
- Student "My Learning" view with open-event tracking for engagement.
- Agent Track A1: PDF text extraction, chunking, and Question Extractor LangGraph agent with side-by-side human review screen.
**Exit gate:** Student sees only shared materials; teacher cannot share to unassigned sections; question extractor draft items verified.

---

## Phase 5 — Assignments & Notifications
**Outcome:** Assignment lifecycle and LangGraph AI Studio pipeline.
- Complete `notifications` module (in-app + email adapters).
- Assignment authoring, publishing, student submission, and evaluation.
- Agent Track A2: AI Studio migration to LangGraph StateGraph (Worksheets, Quizzes, Papers, Custom Questions, Assignment Generator, Difficulty Tagger).
**Exit gate:** Assignment lifecycle functions end-to-end; all AI generation outputs run through the graph with audit-linked run records.

---

## Phase 6 — Analytics (4 Levels + Cross-Analytics)
**Outcome:** Deep multi-level analytics and empirical difficulty calibration.
- School Admin: School, class, subject, and teacher activity metrics.
- Coordinator: Band-wide cross-section comparisons.
- Teacher: 4-level analytics (individual, class, subject, cross-analytics) + material engagement correlation.
- Student: Personal performance map.
- Agent Track A5: Analytics Insight agent reading strictly from scoped tool functions (no text-to-SQL).
**Exit gate:** Analytics endpoints pass strict scope tests; insights adhere to pedagogical honesty rules.

---

## Phase 7 — Exams, Calendar, Report Cards & Approvals
**Outcome:** High-stakes exam management, clash detection, and evaluation assist.
- Academic calendar with exam clash detection and exam policy controls.
- Band-wide exam planner with Set A–D generation from common blueprints.
- Subjective evaluation assistant graph (teacher confirms every mark).
- Exam player with autosave and reconnect resilience; tab-switch logging (no auto-fail).
- Branded report card designer with downloadable PDF; gradebook.
**Exit gate:** Coordinator-approved band paper published across sections in multiple sets; report card PDF generates cleanly.

---

## Phase 8 — Advanced Non-Parked Workflows
**Outcome:** High-leverage pedagogical aids.
- Early-warning dashboard and Coordinator intervention list.
- Smart groups and one-click remedial assignment generation.
- Substitution manager with automatic access expiry.
- Student extras: Goal tracker, smart revision list, structured teacher queries.
**Exit gate:** All advanced features covered by unit and scope tests with human test scripts.

- Keep rollback and data backup plans for every production release.
