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
| **Phase 2** | AI Content Studio (40 Question Types, AI Gateway, Review/Approval) | **IN PROGRESS** | Teacher can generate, edit, and approve usable draft. |
| **Phase 3** | Assessment Delivery (Publish, Player, Autosave, Grading, Release) | Queued | End-to-end authoring to student attempt and evaluation. |
| **Phase 4** | Analytics & Pilot Hardening (Reports, Exports, Hardening, Audit) | Queued | Zero critical security or data-integrity defects; pilot-ready. |
| **Phase 5** | Controlled Expansion Notes | Queued | `docs/PHASE5_NOTES.md` completed. |

---

## 2. What Works Right Now

### Backend Core & APIs
- **Multi-Tenancy & Authorization**: Every entity carries `school_id`. Strict deny-by-default server-side authorization.
- **Identity & RBAC**: Argon2id password hashing, session management via HttpOnly cookies and Bearer tokens, password reset flow, and `/me`.
- **Three Roles Only**: `Admin`, `Teacher`, `Student` (Academic Coordinator and Institute Admin mapped to `Admin` role with metadata).
- **Teacher Assignment Scoping**: Teachers only see and act on explicitly assigned Class + Section + Subject combinations (e.g. Maths teacher assigned to 11E, 12A, 12D).
- **Academic Setup**: Years, Classes, Sections, Subjects, Enrollments, and Curriculum nodes.
- **Bulk Excel (.xlsx) & CSV Importer**: Processes files, creates users and assignments with row-level error reporting.
- **Audit Trail**: Records logins, creations, and administrative actions under `/api/v1/audit-events`.
- **Database Seeding**: Comprehensive seed script in `database/seed/seed_data.py`.

### Frontend Application
- **Vite + React + TypeScript + Tailwind CSS**: Responsive, clean academic workspace design.
- **Role-Aware Shells**: Dedicated navigation layouts for Admin, Teacher, and Student per `Design.md`.
- **Interactive Pages**:
  - `LoginPage` with one-click preset test accounts for rapid evaluation.
  - `AdminDashboard` with academic overview statistics and quick links.
  - `AcademicSetup` with tabs for Classes, Subjects, and Teacher Scope assignments.
  - `BulkImport` with drag-and-drop file upload and live error reporting.
  - `AuditLogs` for security tracking.
  - `TeacherDashboard` highlighting assigned workspaces (11E, 12A, 12D) and human-in-the-loop assurance banner.
  - `TeacherClasses` showing curriculum modules.
  - `StudentDashboard` with enrolled class details and assessment overview.
- **Clean Build**: `tsc -b && vite build` succeeds with 0 errors.

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
