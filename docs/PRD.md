# Product Requirements Document (PRD) — Mind

**Version:** 1.0 | **Status:** Product baseline for V1 planning

## 1. Problem statement

Teachers spend substantial time preparing worksheets, quizzes, class tests, mock papers and answer keys. The work is repetitive, often spread across documents and tools, and difficult to personalise by class, topic and difficulty. Students may receive assessments without timely, actionable feedback. Schools need a controlled academic tool that supports teachers without introducing the complexity of a full ERP.

## 2. Product vision

Make high-quality academic assessment creation and practice faster, more consistent and more useful through teacher-controlled AI assistance.

## 3. Goals and non-goals

### Goals
1. Reduce time required to prepare common academic material.
2. Keep generated material aligned to class, subject, chapter and topic.
3. Give teachers full review and approval control.
4. Support assignment publishing, scheduling, attempts and submissions.
5. Provide understandable assessment-level and topic-level performance insights.
6. Enforce school, class, subject and role boundaries.

### Non-goals for V1
- Full school ERP or finance suite.
- Replacement for teacher judgement.
- Unsupervised AI grading of high-stakes subjective examinations.
- Public student social network or open content marketplace.
- Automated claims of board/curriculum compliance without verified content mapping.

## 4. Personas (5-Tier Authority Structure)

### 1. Platform Admin
Controls every school across the platform: provisions schools, creates School Admins, assigns Academic Coordinators to bands, monitors platform metrics and audit logs.

### 2. School Admin
Controls a single school tenant: manages school profile, branding, academic years, configurable class bands, staff overview, student directory, policies, and school-wide analytics.

### 3. Academic Coordinator
Controls one academic band (e.g. 6–8, 9–10, 11–12): creates teachers, manages assignment matrix (Teacher × Class × Section × Subject), designates Class Teachers, verifies/locks rosters, and approves band-wide papers.

### 4. Teacher (with Class Teacher Designation)
Teaches assigned class + section + subject. Uses AI Studio, Question Bank, delivers assessments, and conducts evaluations. **Class Teachers** uniquely own their section roster (create students with roll numbers, trigger verification/locking, issue login credential slips).

### 5. Student
Identified by roll number and school-scoped login ID. Attempts assigned assessments, accesses teacher-shared materials in My Learning, reviews released results and feedback.

## 5. Functional requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-01 | Platform Admin can provision schools, create School Admins and assign Coordinators to bands | Must |
| FR-02 | School Admin can configure school profile, academic years, class bands, classes, sections, and subjects | Must |
| FR-03 | Academic Coordinator can create teachers and assign Class/Section/Subject combinations within their band | Must |
| FR-04 | Academic Coordinator designates exactly one Class Teacher per section; verifies and locks section rosters | Must |
| FR-05 | Class Teacher can add students (single/CSV) with roll numbers and print credential slips | Must |
| FR-06 | Users authenticate and receive role-scoped access via centralized `authorize()` engine | Must |
| FR-07 | Teacher sees only assigned classes, sections and subjects; Coordinator sees only their band | Must |
| FR-08 | Teacher can generate curriculum-grounded assessments via LangGraph AI Studio pipeline | Must |
| FR-09 | Teacher can edit, regenerate selected items, save drafts and approve content before publishing | Must |
| FR-10 | Teacher can publish now or schedule an assessment to assigned sections | Must |
| FR-11 | Student can view assigned work, access My Learning materials, and attempt tests | Must |
| FR-12 | System autosaves answers and records submission timestamps with server time authoritative | Must |
| FR-13 | Objective questions are automatically evaluated by deterministic engine (no LLM) | Must |
| FR-14 | Subjective evaluation supports teacher marking with AI-assisted suggestions confirmed by teacher | Should |
| FR-15 | 4-Level Analytics: Individual student, class, subject, and cross-analytics (section-vs-section) | Should |
| FR-16 | Teacher can assign targeted remedial practice based on performance gaps | Should |
| FR-17 | Audit logs record every administrative, roster, and publishing action | Must |
| FR-18 | Export/print assessment and results in PDF/CSV; printable report cards | Should |


## 6. AI generation requirements

Generation input should include:
- Grade/class, section (where applicable), subject
- Board/curriculum and academic year where configured
- Chapter, topic and learning objective
- Output type: worksheet, quiz, paper or question set
- Question types, count, marks and difficulty distribution
- Language and any teacher-provided instructions
- Optional approved source material

Generation output should be structured, validated and editable. Each item should include stable ID, type, prompt, options where relevant, expected answer, marks, difficulty, topic tags and explanation/rationale where supported. Do not expose hidden answer keys to students before release.

### AI quality controls
- Validate required fields and mark totals.
- Detect missing MCQ correct option, duplicate options and malformed questions.
- Flag uncertain or source-less factual claims.
- Keep prompt/model/version metadata for reproducibility.
- Require teacher approval before publication.
- Provide retry/regenerate at item level without discarding teacher edits.
- Avoid sending unnecessary student personal data to model providers.

## 7. Non-functional requirements

- Security: least privilege, tenant isolation, secure secrets, encryption in transit and at rest where supported.
- Privacy: data minimisation, retention policy, access logging and institution-approved notices/consents.
- Reliability: transactional publishing/submission; resilient background generation.
- Performance: common dashboard/API requests should feel responsive; long AI jobs run asynchronously.
- Accessibility: keyboard navigation, readable contrast, clear validation and responsive layouts.
- Maintainability: modular services, typed contracts, tests and documented migrations.
- Observability: structured logs, metrics, traces for critical workflows and AI cost tracking.

## 8. Key user journeys

### Teacher creates a test
Login → select assigned class/subject → choose test → configure topics, marks, duration and difficulty → generate draft → review/edit → approve → publish or schedule.

### Student attempts a test
Login → open assigned test → read instructions → start attempt → answer questions with autosave → submit → see submission confirmation → view results only when released.

### Admin configures school
Create academic year → classes/sections → subjects → users → teacher assignments → student enrolments → verify access.

## 9. Success metrics

- Median time from generation request to usable teacher-approved draft.
- Percentage of generated assessments approved with minor edits.
- Teacher weekly active usage and repeat generation rate.
- Assignment completion and submission rates.
- Assessment delivery reliability and autosave success.
- Teacher-reported preparation time saved.
- AI cost per approved assessment.
- Content issue rate reported by teachers.

Set numerical targets after a baseline pilot; do not invent performance claims before measurement.

## 10. Acceptance criteria for V1

1. Role and assignment boundaries are enforced server-side.
2. A teacher can generate, edit, save, approve and publish an assessment.
3. Published assessments respect configured start/end time, duration and attempt limits.
4. Students cannot access unpublished assessments or answer keys.
5. Responses are autosaved and submission is idempotent.
6. Objective scoring is reproducible and covered by tests.
7. Subjective marks can be entered and audited by a teacher.
8. Admin changes and critical assessment events are auditable.
9. Errors are actionable and do not expose secrets or other students' data.
10. A pilot can be onboarded using documented setup and support procedures.

## 11. Assumptions and open decisions

- Initial pilot board/curriculum and content source must be selected with the school.
- Whether students can see solutions immediately or only after teacher release is configurable.
- AI provider, hosting region, retention period and consent workflow require institutional/legal review.
- Exact grading rubrics and supported languages require pilot validation.
- The product name “Mind” is a working name; domain, trademark and company-name availability are not verified.
