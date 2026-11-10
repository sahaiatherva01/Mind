# Mind V2 — Progress & Status Tracker

Last Updated: 2026-11-10  
Working Product Name: **Mind**  
Tagline: *Intelligence for Better Learning*

---

## 1. Overall Phase Status (V2 5-Tier Scoped Authority Model)

| Phase | Description | Status | Exit Gate Criteria |
|---|---|---|---|
| **Phase 0** | Baseline & Discovery Report | **COMPLETE** | Full repo audit, baseline tests (21/21 passed), docs package updated, Phase 1 plan approved. |
| **Phase 1** | Scoped RBAC Refactor & 5 Tiers | **COMPLETE** | `RoleAssignment`, `Band`, `AcademicYear`, `authorize()` central engine, 25/25 tests green, zero legacy role references. |
| **Phase 2** | Academic Coordinator & Assignment Matrix | **COMPLETE** | Band dashboard, teacher creation within band, assignment matrix, 1 Class Teacher constraint enforced, 33/33 tests green. |
| **Phase 3** | Teacher: Students, Rosters & Credentials | **COMPLETE** | Class Teacher student onboarding, unique roll numbers, roster lock, credential slips, first-login password change, 40/40 tests green. |
| **Phase 4** | Materials & My Learning | **NEXT** | `content` module, PDF chunking, Question Extractor agent, student My Learning view. |
| **Phase 5** | Assignments & Notifications | PENDING | `notifications` module, assignment lifecycle, LangGraph AI Studio generation graph. |
| **Phase 6** | Analytics (4 Levels + Cross Analytics) | PENDING | School, Coordinator, Teacher (4 levels), Student views; Analytics Insight agent. |
| **Phase 7** | Exams, Calendar, Report Cards, Approvals | PENDING | Clash detection, Set A–D builder, blueprint validator, subjective evaluation assistant, branded report card PDF. |
| **Phase 8** | Advanced Non-Parked Workflows | PENDING | Early warning, smart groups, remedial generation, substitution manager. |

---

## 2. Test & Build Verification (Phase 3 Status)
- **Backend Tests:** 40/40 passing (`.venv/bin/pytest backend/tests/ -v` in 17.56s).
- **Frontend Build:** Clean compilation with 0 TypeScript/Vite errors (`npm run build --prefix frontend` in 1.68s).
- **Database Migrations:** Baseline `f0506b03ca22` + Phase 1 `766e3fbe416b_feat_rbac_5_tier_role_assignments_and_bands.py` stamped at head.
- **Git State:** `main` branch, working tree modified for manual review. All changes uncommitted.

---

## 3. What Works Right Now

### Backend Core & APIs
- **Multi-Tenancy & Authorization**: Every entity carries `school_id`. Strict deny-by-default server-side authorization. Platform Admin operates cross-school (`school_id=None`).
- **Identity & 5-Tier Scoped RBAC**:
  - `Platform Admin`: Global system controller.
  - `School Admin`: School-scoped control (`school_id`).
  - `Academic Coordinator`: Band-scoped control (`school_id` + `band_id`).
  - `Teacher`: Explicit class + section + subject scoped assignments + `is_class_teacher` flag.
  - `Student`: Section enrollment + unique roll number.
- **Machine-Readable Permission Matrix**: `backend/app/core/permission_matrix.py` defining fine-grained actions and scope rules, validated with `test_permission_matrix.py`.
- **Central Authorization Engine**: `backend/app/core/policies.py` evaluates actor roles, assignments, and resource bounds together.
- **Platform Admin APIs**: `/api/v1/platform/dashboard`, `/platform/schools`, `/platform/schools/{id}/admins`, `/platform/schools/{id}/coordinators`, `/platform/audit-logs`.
- **School Admin APIs**: `/api/v1/schools/{id}/bands`, `/schools/{id}/profile`, `/schools/{id}/settings`.
- **Academic Setup**: Years, Classes, Sections, Subjects, Enrollments, and Curriculum nodes.
- **Bulk Excel (.xlsx) & CSV Importer**: Processes files, creates users and assignments with row-level error reporting.
- **Audit Trail**: Records logins, creations, and administrative actions under `/api/v1/audit-events`.
- **Database Seeding**: Comprehensive seed script in `database/seed/seed_data.py`.
- **Canonical Question Schema**: Supports the 40 ICSE/ISC Board Exam question types spanning 5 categories.
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
- **Vite + React + TypeScript + Tailwind CSS**: Responsive academic workspace design.
- **5-Role Navigation Layout**: Dedicated sidebars and route guards for Platform Admin, School Admin, Academic Coordinator, Teacher, and Student.
- **Quick Demo Logins**:
  - **Platform Admin**: `platform.admin@mind.local` / `PlatformPass123!`
  - **School Admin**: `admin@mind.local` / `AdminPass123!`
  - **Academic Coordinator (11-12)**: `coord.senior@mind.local` / `CoordPass123!`
  - **Maths Teacher**: `maths.teacher@mind.local` / `TeacherPass123!` (Assigned: 11E, 12A, 12D; Class Teacher: 11E)
  - **Physics Teacher**: `physics.teacher@mind.local` / `TeacherPass123!` (Assigned: 11E, 12A)
  - **Student (11E)**: `student.aarav@mind.local` / `StudentPass123!` (Enrolled: 11E, Roll: 11E-01)
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
