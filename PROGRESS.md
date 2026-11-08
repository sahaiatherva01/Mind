# Mind V1 — Progress & Status Tracker

Last Updated: 2026-11-08  
Working Product Name: **Mind**  
Tagline: *Intelligence for Better Learning*

---

## 1. Overall Phase Status

| Phase | Description | Status | Exit Gate Criteria |
|---|---|---|---|
| **Phase 0** | Discovery & Operational Baselines | **COMPLETED** | Baseline decisions documented in `docs/DECISIONS.md`. |
| **Phase 1** | Product Foundation (Tenancy, Identity, Academics, Audit, Shells) | **COMPLETED** | Multi-tenant boundary enforced; RBAC and assignment-scoped tests pass (11/11 tests green). |
| **Phase 2** | AI Content Studio (40 Question Types, AI Gateway, Review/Approval) | **COMPLETED** | Teacher can generate, edit, and approve usable draft (14/14 tests green). |
| **Phase 3** | Assessment Delivery (Publish, Player, Autosave, Grading, Release) | **COMPLETED** | End-to-end authoring to student attempt and evaluation (16/16 tests green). |
| **Phase 4** | Analytics & Pilot Hardening (Reports, Exports, Hardening, Audit) | **COMPLETED** | Psychometrics, CSV/PDF exports, and security hardening (17/17 tests green). |
| **Phase 5** | Controlled Expansion Notes & Compliance Documentation | **COMPLETED** | `docs/PHASE5_NOTES.md`, `docs/LEGAL_AND_PRIVACY_OPEN_ITEMS.md`, `docs/USER_GUIDE.md` complete. |

---

## 2. What Works Right Now

### Backend Core & APIs
- **Multi-Tenancy & Authorization**: Every entity carries `school_id`. Strict deny-by-default server-side authorization.
- **Identity & RBAC**: Argon2id password hashing, session management via HttpOnly cookies and Bearer tokens, password reset flow, and `/me`.
- **Three Roles Only**: `Admin`, `Teacher`, `Student`.
- **Teacher Assignment Scoping**: Teachers only see and act on explicitly assigned Class + Section + Subject combinations.
- **Academic Setup**: Years, Classes, Sections, Subjects, Enrollments, and Curriculum nodes.
- **Bulk Excel (.xlsx) & CSV Importer**: Processes files, creates users and assignments with row-level error reporting.
- **Audit Trail**: Records logins, creations, and administrative actions under `/api/v1/audit-events`.
- **Database Seeding**: Comprehensive seed script in `database/seed/seed_data.py`.
- **Canonical Question Schema**: Supports the 40 ICSE/ISC Board Exam question types spanning 5 categories (Objective, Written, Visual/Mathematical, Application/Analytical, Computer Science).
- **AI Gateway & Adapters**: Modular architecture supporting Google Gemini and deterministic `MockAIProvider` for zero-cost offline testing and CI.
- **Generation Pipelines**: Worksheets, Quizzes, Question Papers, and Custom Question Sets.
- **Domain Validations**: Mark total auto-balancing, MCQ option completeness, duplicate choice detection, valid answer key matching, and factual uncertainty detection.
- **Assessment Review & Approval**: State machine transition `needs_review` → `approved`, item reordering, item deletion, and single-item regeneration with teacher feedback.
- **Assessment Delivery & Idempotent Autosave**: Student-safe player with real-time countdown timer, palette, automatic response autosaving, and idempotent submit.
- **Evaluation & Grading Queue**: Teacher subjective grading queue with model answer & rubric reference.
- **Result Release Workflow**: Teacher-controlled result release policy with zero answer-key leakage before release.
- **Psychometric Diagnostics & Item Analysis**: Item difficulty ($P$-value), item discrimination index ($D$), and score distribution histogram.
- **Curriculum Gap Analysis**: Aggregates mastery by topic and flags critical gaps (<60%) for remedial practice.
- **Assessment Exports (FR-18)**: Printable Board-exam HTML/PDF papers (with optional teacher marking scheme) and RFC 4180-compliant CSV gradebook roster.
- **Legal & Compliance Baseline**: Complete alignment with India's Digital Personal Data Protection Act, 2023 (DPDP Act).

### Frontend Application
- **Vite + React + TypeScript + Tailwind CSS**: Responsive, clean academic workspace design.
- **Role-Aware Shells**: Dedicated navigation layouts for Admin, Teacher, and Student per `Design.md`.
- **Interactive Pages**:
  - `LoginPage` with one-click preset test accounts.
  - `AdminDashboard`, `AcademicSetup`, `BulkImport`, `AuditLogs`.
  - `TeacherDashboard` highlighting assigned workspaces (11E, 12A, 12D) and human-in-the-loop assurance banner.
  - `TeacherClasses` showing curriculum modules.
  - `AIStudio`: 4-step progressive disclosure generator wizard with 40-question-type checklist.
  - `AssessmentEditor`: Live draft editor with item reorder, inline prompt/mark edits, single-item regenerate modal, collapsible teacher answer keys, and approval button.
  - `TeacherAssessments` with publish/schedule modal.
  - `TeacherEvaluationQueue` with subjective response grading.
  - `TeacherAnalytics` with item discrimination, score distribution, and topic mastery.
  - `StudentDashboard` with enrolled class details.
  - `StudentUpcomingTests` with live assessment availability roster.
  - `AssessmentPlayer` distraction-free test player with timer and autosave.
  - `StudentResults` score breakdown with teacher feedback.
- **Clean Build**: `tsc -b && vite build` succeeds with 0 errors in 860ms.

---

## 3. How to Run and Test

### Backend (Local)
```bash
source .venv/bin/activate
pip install -r backend/requirements.txt
python database/seed/seed_data.py
pytest backend/tests -v
```

### Frontend (Local)
```bash
cd frontend
npm install
npm run build
npm run dev
```

### Credentials for Testing
- **Admin**: `admin@mind.local` / `AdminPass123!`
- **Maths Teacher**: `maths.teacher@mind.local` / `TeacherPass123!` (Assigned: 11E, 12A, 12D)
- **Physics Teacher**: `physics.teacher@mind.local` / `TeacherPass123!` (Assigned: 11E, 12A)
- **Student**: `student.aarav@mind.local` / `StudentPass123!` (Enrolled: 11E)
