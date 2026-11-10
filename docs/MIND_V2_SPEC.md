# MIND v2: 5-Tier Authority Structure and Full Feature Set

## 1. The hierarchy

```
PLATFORM ADMIN (you)             → controls every school
 └─ SCHOOL ADMIN (per school)    → controls one school + all its analytics
 └─ ACADEMIC COORDINATOR         → controls one section band
     (per school, per band)         (1–5 / 6–8 / 9–10 / 11–12)
         └─ TEACHER              → teaches assigned class + section + subject
             └─ STUDENT          → identified by roll number
```

### The authority chain

| Step | Who acts | What they create | Constraint |
|---|---|---|---|
| 1 | Platform Admin | School (tenant), School Admin, Academic Coordinators | Coordinators are tied to a band |
| 2 | Academic Coordinator | Teacher accounts, with subject, class and section assignments | Only inside their own band |
| 3 | Teacher (Class Teacher) | Students, with roll numbers | Only in the sections they are assigned to |

- **Who can add students:** Only the Class Teacher of a section can add students. Subject teachers get read access.
- **Roster verification:** Teacher-added students start as *Pending Verification*. The Coordinator approves the roster, or the Class Teacher "locks" it. After that, edits need a Coordinator-approved request (`RosterChangeRequest`).

### Scoped permissions (the core technical change)

Replace 3 flat roles with roles evaluated alongside scope:

| Role | Scope | Example |
|---|---|---|
| Platform Admin | Global | All schools |
| School Admin | `school_id` | DPS Lucknow |
| Academic Coordinator | `school_id` + `band` | DPS Lucknow, Class 9–10 |
| Teacher | `school_id` + `class` + `section` + `subject` + `year` | 10-B Physics |
| Class Teacher (flag on Teacher) | `school_id` + `class` + `section` | 10-B roster owner |
| Student | `school_id` + `enrollment` | 10-B, Roll 23 |

Every API check evaluates role and scope together. The Coordinator for Class 9–10 must never see Class 11 data, even in the same school.

**Roll number rules:**
- Unique per `(school, academic year, class, section)`.
- Login ID is generated via school template: default uses admission number; configurable to school code + class-section + roll number.
- Roll numbers are re-issued each academic year, but the student's internal `user_id` never changes across promotions.

---

## 2. Platform Admin panel

**Basic features:**
- Schools: Create, edit, suspend, archive schools; school code; board; academic year
- School Admin & Coordinator management: Create, reset, deactivate; assign Coordinators to bands
- Platform dashboard: Total schools, users, active users, storage, AI usage, exams run
- Platform audit log: Every cross-school action
- Feature flags: Enable or disable modules per school

**Advanced features (see parked items in Section 4 of master loop prompt for V1 exclusions):**
- Support mode (consented impersonation) [Parked]
- Quota and cost control [Parked in V1]
- Template library
- Tenant health monitor [Parked]

---

## 3. School Admin panel

Full control and visibility over one school.

**Basic features:**
- Dashboard: Students, teachers, classes, assessments, pending evaluations, activity
- School profile & branding: Logo, name, address, board, academic year, PDF letterhead
- Academic structure: Classes, sections, subjects per class, academic years, bands
- Staff view: All Coordinators and Teachers, with their assignments
- Student directory: Class and section-wise, search by name or roll number
- Assessment overview: Everything scheduled, running, completed
- Reports: Class, section, subject, teacher
- Audit logs: Within the school
- Settings: Password policy, grading scale, notification rules, login ID template

**Analytics:**
- School: Overall average, pass %, trend across terms, grade distribution
- Class & section: Section-vs-section comparison, topper list, at-risk count
- Subject: Subject averages across classes, weakest chapters school-wide
- Teacher: Content uploaded, assessments created, evaluation turnaround time, class results under their teaching (labeled as activity data, not a verdict on teaching quality)
- Student: Any student's full profile (read-only)

---

## 4. Academic Coordinator panel

Run one band (6–8, 9–10, 11–12) day to day.

**Basic features:**
- Band dashboard: Classes, sections, teachers, students, upcoming exams in the band
- Teacher management: Add teachers, edit, deactivate, reset passwords, bulk Excel import
- Assignment matrix: Teacher × Class × Section × Subject grid
- Class Teacher designation: Exactly one Class Teacher per section
- Roster oversight: Verify or lock section rosters; approve roster change requests
- Curriculum: Chapters and topics per subject in the band
- Section analytics: Band-wide performance and section comparisons

---

## 5. Teacher panel

- Class Teacher student management: Add students (single + CSV) with roll numbers, trigger roster verification/locking, issue credential slips.
- Learning materials: Upload, tag, and distribute PDFs to assigned sections.
- AI Studio: Generate worksheets, quizzes, question papers, custom questions, practice sets, case studies using LangGraph pipeline. Draft until approved.
- Question Bank: Curated, curriculum-mapped repository.
- Assessments & Assignments: Delivery, timer, scheduling.
- Evaluation Centre: Split-view grading, rubric support, evaluation assistant suggestions (teacher finalizes).
- 4-Level Analytics: Individual student, class, subject, cross-analytics (section-vs-section, subject-vs-subject, material engagement correlation).

---

## 6. Student panel

- Dashboard & Upcoming Tests
- My Learning: Teacher-shared materials & PDFs
- Assignments & Exam Player: Low-bandwidth, autosave, reconnect-resilient
- Results & Performance: Topic-wise strength meter, answer review (after release)
- Announcements & Notifications
- Privacy: View only own marks, never named classmate rankings

---

## 7. Cross-panel rules

| Action | Platform Admin | School Admin | Coordinator | Teacher | Student |
|---|---|---|---|---|---|
| Create school | ✔ | ✘ | ✘ | ✘ | ✘ |
| Add School Admin / Coordinator | ✔ | ✘ | ✘ | ✘ | ✘ |
| Define classes, sections, subjects | Template | ✔ | Propose (band) | ✘ | ✘ |
| Add teachers and assign subjects | ✘ | View / override | ✔ (band) | ✘ | ✘ |
| Designate Class Teacher | ✘ | ✔ | ✔ (band) | ✘ | ✘ |
| Add students and roll numbers | ✘ | View / emergency edit | Verify / lock | ✔ (Class Teacher) | ✘ |
| Upload and share PDFs | ✘ | ✘ | View (band) | ✔ | View only |
| Create assessments | ✘ | ✘ | Approve band-wide papers | ✔ | ✘ |
| Evaluate | ✘ | Monitor | Monitor | ✔ | ✘ |
| Release results | ✘ | ✘ | Policy approval | ✔ | View |
| Analytics reach | All schools | Whole school | Band | Assigned classes | Own |

Core rules:
1. No role can grant a role above or equal to its own.
2. Every create, edit, deactivate and share action is audit-logged with before/after values.
3. Deactivation, not deletion, for users and academic records.

---

## 8. Data model additions

- `RoleAssignment`: `user_id`, `role`, `school_id`, `band_id`, `effective_from`, `effective_to`, `status`
- `Band`: Configurable class range per school (e.g. 6–8, 9–10, 11–12)
- `AcademicYear`: Explicit entity linked across schools, assignments, rosters
- `TeacherAssignment`: `teacher_id`, `subject_id`, `class_id`, `section_id`, `year_id`, `is_class_teacher`, `status`
- `RosterStatus`: Pending / Verified / Locked per section
- `RosterChangeRequest`: Post-lock edit workflow
- `ApprovalRequest`: Generic approval queue
- `Cohort`: Groupings for cross-analytics
