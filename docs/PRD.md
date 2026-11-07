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

## 4. Personas

### Admin
Needs to configure the institution, academic year, classes, sections, subjects, user accounts, teacher assignments and access policies.

### Teacher
Needs to prepare reliable academic material quickly, customise it, review answer keys, publish/schedule tests and understand student performance.

### Student
Needs a simple place to find assigned work, understand instructions, complete attempts, submit answers and review released results/feedback.

## 5. Functional requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-01 | Admin can create/manage academic years, classes and sections | Must |
| FR-02 | Admin can create subjects and assign teachers to class/section/subject combinations | Must |
| FR-03 | Users authenticate and receive role-scoped access | Must |
| FR-04 | Teacher sees only assigned classes, sections and subjects | Must |
| FR-05 | Teacher can generate worksheets with curriculum and difficulty context | Must |
| FR-06 | Teacher can generate quizzes containing MCQs and short answers | Must |
| FR-07 | Teacher can generate question papers with marks and section structure | Must |
| FR-08 | Teacher can generate individual questions with topic/type/difficulty/count controls | Must |
| FR-09 | Teacher can edit, regenerate selected items, save drafts and approve content | Must |
| FR-10 | Teacher can publish now or schedule an assessment | Must |
| FR-11 | Student can view assigned work and attempt within availability rules | Must |
| FR-12 | System autosaves answers and records submission timestamps | Must |
| FR-13 | Objective questions can be automatically evaluated | Must |
| FR-14 | Subjective evaluation supports teacher marking and optional AI-assisted suggestions | Should |
| FR-15 | Teacher can view scores, question analysis and topic-level trends | Should |
| FR-16 | Teacher can assign targeted practice based on performance | Could |
| FR-17 | Admin can view audit logs and manage user status | Should |
| FR-18 | Export/print assessment and results in PDF/CSV | Should |

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
