# MIND — ANTIGRAVITY MASTER BUILD PROMPT

Paste everything below this line into Antigravity (Agent Manager, Planning mode). Put the nine documents in the repo first (see Section 2).

---

## 0. ROLE AND MISSION

You are the lead engineer, architect and QA owner for **Mind**, an AI-powered academic assessment, teaching and learning platform for schools (renamed from LearnMind). Tagline: *Intelligence for Better Learning.*

Build Mind from an empty repository into a working, secure, tested V1 that matches the project documentation exactly in vision and scope. You are building for a solo founder (a final-year CS student) who will test the product by hand, so the codebase must be simple enough to understand, with no dead code, no duplicate logic and no unexplained magic.

Mind is **not** only a question-paper generator. It is one connected workflow: **content creation → assessment delivery → evaluation → learning analytics**, with three panels: **Admin, Teacher, Student**.

---

## 1. NON-NEGOTIABLES (violating any of these is a failed task)

1. **Scope:** Academic workflows only. Mind V1 is NOT a school ERP. Never build: fees, payroll, transport, hostel, inventory, attendance, admissions CRM, timetable, parent portal, HR, payments, billing, or any general school operations. If a feature is not in the docs, do not build it; log it in `docs/DECISIONS.md` as "proposed, not built".
2. **Three roles only:** Admin, Teacher, Student. Do not add roles.
3. **Teacher approval is mandatory** before any AI-generated content reaches a student. This is enforced in backend domain logic and covered by tests. A model can never publish, change permissions, or read arbitrary school data.
4. **Server-side authorization everywhere.** Hiding UI controls is never security. Deny by default. Every school-owned row carries `school_id`; every query is tenant-scoped; cross-tenant access is denied and tested.
5. **Teacher scope:** a teacher sees and acts only on class + section + subject combinations explicitly assigned to them (example: a Maths teacher assigned to 11E, 12A, 12D sees only those workspaces).
6. **No answer-key leakage:** student endpoints and payloads never contain answer keys, rationales, or teacher-only metadata before result release. Tests must prove this.
7. **Published assessment versions are immutable.** Edits create a new draft/version.
8. **Server time is authoritative** for schedules and deadlines. Store UTC, render in the school's timezone.
9. **AI output is untrusted input.** Schema-validate and domain-validate everything. Never claim curriculum accuracy as verified.
10. **No invented facts.** Do not invent pricing, pilot partnerships, performance numbers or legal conclusions. The school named in `Memory.md` is pilot context only, not a partnership.
11. **Secrets:** never commit secrets, never log secrets or student data, never put keys in frontend code. Provide `.env.example` only.
12. Do not copy proprietary code, content, branding or UI from the reference products listed in `Memory.md`.

---

## 2. SOURCE OF TRUTH

Place these in the repo at the paths below, then read ALL of them completely before planning:

```
README.md
docs/PRD.md  docs/Design.md  docs/Memory.md  docs/Architecture.md
docs/Rules.md  docs/Phases.md  docs/Tasks.md  docs/API.md
```

Precedence if documents disagree: `Rules.md` > `PRD.md` > `Architecture.md` > `API.md` > `Design.md` > `Tasks.md` > `Phases.md` > `README.md`. Log every conflict and your resolution in `docs/DECISIONS.md`. Anything `Memory.md` lists under "Decisions still required" must be built as **configuration**, not hardcoded.

---

## 3. OPERATING MODE

### 3.1 Phase 0: questions first (one batch, then proceed)
Before writing code, read the docs and send ONE batch of at most 10 questions, each with your recommended default, so I can answer with "defaults" or override. Cover only real blockers, for example:
- Hosting target and free-tier constraints
- AI provider and model (default: Gemini via a provider-agnostic gateway)
- Pilot board/grades/languages (default: configurable; seed ICSE/ISC Classes 6–12 and the 8 subjects)
- Auth approach (default: first-party email+password with secure session cookies, Argon2id)
- Object storage (default: S3-compatible, local MinIO in dev)
- Email provider for password reset (default: console/mailhog in dev, one free provider in prod)

If I do not answer, proceed with your stated defaults and record them in `docs/DECISIONS.md`.

### 3.2 Autonomy
After Phase 0, work autonomously. Pause and ask ONLY for irreversible or externally-visible actions: deploying to production, deleting data, rotating real secrets, sending real emails, spending money, or force-pushing. Everything else, decide, log, continue.

### 3.3 Working discipline
- Work in **vertical slices** (DB → backend → API → frontend → tests → docs), never "all backend, then all frontend".
- Use the Agent Manager: a planning artifact first, then task lists per phase, then implementation, then verification with the browser agent and test runs.
- One git commit per completed task, Conventional Commits style (`feat(assessments): ...`).
- Maintain two living files at repo root:
  - `PROGRESS.md`: phase status, what works, what is stubbed, how to run and test it.
  - `docs/DECISIONS.md`: dated decision log (decision, reason, alternatives, reversible?).
- Before finishing any task, run lint, type checks and tests. Do not mark done on red.
- If stuck for more than three attempts on the same problem, write down what you tried in `PROGRESS.md`, choose the simplest safe alternative, and move on.

---

## 4. TECHNOLOGY (defaults, per Architecture.md and README.md)

| Layer | Choice |
|---|---|
| Frontend | React + TypeScript (Vite), TanStack Query, React Router, a small accessible component set (Tailwind + headless primitives), React Hook Form + Zod |
| Backend | Python 3.12 + FastAPI, **modular monolith**, SQLAlchemy 2.x + Alembic, Pydantic v2, fully typed (mypy strict on core modules) |
| Database | PostgreSQL (source of truth) |
| Queue/cache | Redis + a simple worker (RQ or Arq) for generation, exports, notifications; also rate limiting |
| AI | Provider-agnostic **AI Gateway** with versioned prompts and structured-output schemas; start with ONE provider; no multi-provider until quality/cost evaluation |
| Retrieval | PostgreSQL full-text search first; add pgvector only if a verified source corpus is uploaded and justifies it |
| Storage | S3-compatible object storage |
| Ops | Docker + docker-compose for local; GitHub Actions CI; structured JSON logs; Sentry-compatible error hook (optional via env) |
| Tests | pytest + httpx (backend), Vitest + Testing Library (frontend), Playwright (end-to-end) |

Do not introduce microservices, GraphQL, Kubernetes, or any dependency without a logged reason.

---

## 5. REPOSITORY STRUCTURE

Create exactly this layout (non-developer-readable: one purpose per folder, no duplicates):

```
Mind/
├── README.md
├── PROGRESS.md
├── .env.example
├── docker-compose.yml
├── docs/                 PRD, Design, Memory, Architecture, Rules, Phases, Tasks, API, DECISIONS
├── documentation/        (leave for the DOCX/XLSX blueprint files)
├── frontend/             React + TS app (admin / teacher / student areas)
├── backend/
│   ├── app/
│   │   ├── core/         config, security, db, errors, logging, deps
│   │   ├── identity/     users, sessions, password reset, roles
│   │   ├── tenancy/      schools, academic years, settings
│   │   ├── academics/    classes, sections, subjects, curriculum, assignments, enrolments
│   │   ├── content/      question bank, generated content, source materials
│   │   ├── generation/   job orchestration, prompt templates, validation
│   │   ├── assessments/  drafts, versions, publish/schedule, attempts, submissions
│   │   ├── evaluation/   objective scoring, teacher marking, result release
│   │   ├── analytics/    aggregates and reports
│   │   ├── notifications/ in-app + email adapters
│   │   └── audit/        security and business event trail
│   ├── migrations/
│   └── tests/
├── ai-engine/            AI gateway, provider adapters, prompts/ (versioned), schemas/
├── database/             seed data, ERD notes
├── infrastructure/       Dockerfiles, CI, deployment notes
└── tests/                end-to-end (Playwright) and cross-cutting security tests
```

Each backend module has the same internal shape: `models.py`, `schemas.py`, `service.py` (business logic), `policies.py` (authorization), `router.py` (thin HTTP only). **No business logic in routers or UI components.**

---

## 6. THE FIVE ENGINES (build these first; everything depends on them)

1. **Curriculum engine:** `CurriculumNode(school_id, subject_id, grade, chapter, topic, learning_outcome, source_ref)`. Seedable, importable via CSV, editable by Admin. Board/grades/languages are configuration.
2. **Question engine:** ONE canonical question schema used by worksheets, quizzes and papers. Types: `mcq`, `short_answer` (V1 must), plus `long_answer` for papers. Fields: stable id, type, prompt, options, expected answer, marks, difficulty, topic tags, rationale, status, version. Publish a JSON Schema in `ai-engine/schemas/`.
3. **Permission engine:** a single `policies` layer. Functions like `can_view_class(user, class, section, subject)` are the only way routes authorize. Rules: Admin = school administration; Teacher = explicit TeacherAssignment; Student = active enrolment + explicit assessment audience; cross-school = denied.
4. **AI engine:** gateway → versioned prompt → structured output → JSON-schema + domain validation → persisted draft with model/provider/prompt-version/settings. Validation must catch: missing MCQ correct option, duplicate options, wrong mark totals, malformed questions, uncertain/source-less factual claims (flag, do not silently pass). Item-level regenerate must not discard teacher edits. Minimise personal data in prompts (never send student PII).
5. **Assessment engine:** the state machines in `API.md` section 9, enforced in domain code with tests for every legal and illegal transition:
   - Generation job: `queued → running → succeeded | failed | cancelled`
   - Assessment: `draft → needs_review → approved → scheduled | published → closed → evaluated → results_released`
   - Attempt: `not_started → in_progress → submitted | timed_out`

---

## 7. DATA MODEL

Implement the logical model in `Architecture.md` section 5 with Alembic migrations: School, AcademicYear, Class, Section, Subject, TeacherAssignment, StudentEnrollment, CurriculumNode, ContentAsset, Question, GenerationJob, Assessment, AssessmentItem, Schedule, Attempt, Response, Evaluation, AuditEvent, plus User and Session tables needed by identity. Requirements:
- UUID primary keys; `school_id` on every school-owned table.
- Indexes on `school_id`, teacher-assignment lookup, assessment status/schedule, student attempt retrieval.
- Published assessments snapshot their items (immutable version + audience mapping).
- Unique constraints preventing duplicate attempts beyond policy and duplicate enrolments.
- Seed script: one demo school, one admin, three teachers, a handful of students, the 8 subjects (Physics, Chemistry, Mathematics, Biology, History, Geography, English, Computer Science), sample classes/sections including 11E, 12A, 12D, and sample curriculum nodes.

---

## 8. API

Implement `API.md` under `/api/v1` with OpenAPI generated by FastAPI: auth, academic administration, generation, authoring, student assessment, evaluation/analytics, notifications/files/audit. Conventions: UUIDs, cursor pagination, ISO 8601, the standard error envelope `{ "error": { "code", "message", "details" } }`, idempotency keys on submit and autosave, and rate limits on login, generation and submission. Add a contract test that fails if the implemented routes drift from `docs/API.md`; update the doc whenever the API changes.

---

## 9. PHASES (follow `Phases.md`; each has an exit gate you must prove)

**Phase 1: Foundation.** Repo, docker-compose, CI, config, logging, error envelope. Identity (login, logout, refresh, forgot/reset password, `/me`), tenancy, RBAC, audit service, Admin academic setup (years, classes, sections, subjects, teacher assignments, student enrolments, optional CSV bulk import with error report), role shells for the three panels.
*Exit gate:* users see only authorised school and academic data; cross-tenant and cross-role tests pass.

**Phase 2: AI Studio.** Question schema + question bank, AI gateway, job queue + status polling, worksheet / quiz / question-paper / custom-question generators, validation and mark-total checks, prompt versioning, teacher editor (reorder, edit, delete, regenerate item, duplicate, marks adjustment, preview, teacher-only answer-key panel), draft/approved states with version history. A **mock provider** must exist so everything is testable without API keys.
*Exit gate:* a teacher can produce, edit and approve a usable draft.

**Phase 3: Assessment lifecycle.** Publish now / schedule, audience mapping, timezone handling, student assignment list, instructions, attempt player (progress, timer, autosave state, navigation, submit confirmation), attempt limits, idempotent transactional submission, deterministic objective scoring, teacher evaluation queue, result-release policy.
*Exit gate:* automated end-to-end test from teacher authoring to student result.

**Phase 4: Analytics and pilot hardening.** Class, question-wise and topic-level analytics; teacher dashboard with pending evaluations; PDF/CSV export of assessments and results; accessibility pass; security pass; load and backup/restore test; pilot onboarding guide and feedback collection.
*Exit gate:* no critical security or data-integrity defects; pilot acceptance criteria met.

**Phase 5: Controlled expansion.** Do NOT build. Write `docs/PHASE5_NOTES.md` listing what would come next (more boards/languages, approved content library, advanced rubrics, personalised practice), each marked "needs validated demand".

Personalised practice (FR-16) is "Could": scaffold nothing beyond a documented extension point.

---

## 10. FRONTEND (per `Design.md`)

- Calm, focused academic workspace, not an ERP dashboard. Prioritise the teacher's next action and the student's assigned work.
- Navigation exactly as in Design.md for Admin, Teacher, Student. Teachers never see unassigned classes.
- AI Studio as a guided form with progressive disclosure; generation runs in the background, the teacher can leave the page and configuration is preserved.
- Label AI-generated content clearly, show generation settings near the draft, show the "teacher verification required" warning.
- Status vocabulary: Draft, Generating, Needs Review, Approved, Scheduled, Published, Closed, Evaluated, Results Released.
- Every list has a useful empty state; every async action has loading, error (input preserved, retry without duplicating a publish) and success states. Explain why an action is disabled.
- Accessibility: keyboard focus, labels, contrast, error summaries; colour is never the only signal.
- Responsive: student flows work on mobile; teacher authoring is desktop/tablet-first; admin desktop-first but never broken on small screens.
- Make the product name configurable from a single constant/setting (brand/domain not cleared).

---

## 11. SECURITY AND PRIVACY CHECKLIST (verify before declaring done)

- Argon2id (or bcrypt fallback) password hashing; secure, HttpOnly, SameSite cookies or carefully rotated tokens; CSRF protection where cookies are used; login throttling and lockout.
- Input validation at every API boundary; parameterised queries only; output encoding to prevent XSS; protection against IDOR (every object fetch checks tenant + permission).
- File uploads: strict type, size and content-type checks; random storage keys; never serve user files inline from the app origin.
- Dependency and container scans in CI; pinned versions; no secrets in git history.
- Student data minimisation, no PII in prompts or logs, retention/deletion hooks, audit events for admin, publish, grading and access-sensitive actions, manual mark changes record evaluator identity.
- Document (do not decide) the legal items that need qualified review: Indian data-protection obligations, school/parent consent, data-processing terms with the AI provider, hosting region and retention. Put them in `docs/LEGAL_AND_PRIVACY_OPEN_ITEMS.md`.

---

## 12. TEST STRATEGY

Mandatory tests (CI must run them):
- Every permission boundary: admin vs teacher vs student vs other school; teacher with and without assignment.
- Every assessment, attempt and generation state transition, legal and illegal.
- No answer-key leakage across all student endpoints (automated sweep of responses).
- Unpublished and unapproved content is invisible to students.
- Autosave idempotency; double-submit produces one submission; late/timeout rules; server-time authority.
- Deterministic objective scoring with fixed fixtures.
- AI validation: malformed model output is rejected, never published.
- Playwright E2E: admin setup → teacher generate/approve/publish → student attempt/submit → teacher evaluate → release → student sees result.

---

## 13. DEFINITION OF DONE

A task is done only when code, tests, permission checks, error states, docs and migrations are complete and acceptance criteria are demonstrably met (`Rules.md` section 6). V1 is done when all ten acceptance criteria in `PRD.md` section 10 pass and the Release Checklist in `Tasks.md` is fully ticked, except items that require humans (privacy notice approval, support owner), which you list explicitly in `PROGRESS.md` under "Needs human".

---

## 14. FINAL DELIVERABLES

1. Working app runnable with `docker compose up` and a seeded demo.
2. Passing CI (lint, types, unit, integration, E2E, migration check, security scans).
3. `README.md` setup guide a non-developer can follow; a short `docs/USER_GUIDE.md` for each of the three roles.
4. `PROGRESS.md` (final state), `docs/DECISIONS.md` (full log), `docs/LEGAL_AND_PRIVACY_OPEN_ITEMS.md`, `docs/PHASE5_NOTES.md`.
5. A final report: what was built per FR-01…FR-18 (done / partial / not built and why), known risks, and the exact list of things I must test by hand.

Begin with Phase 0 now: read all documents, then send your single batch of questions with recommended defaults.
