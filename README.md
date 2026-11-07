# Mind — AI-Powered Academic Assessment & Learning Platform

> **Working product name:** Mind  
> **Product category:** School-focused academic productivity, assessment and learning platform  
> **Primary users:** Teachers, Students and School Administrators  
> **Initial product boundary:** Academic workflows only; not a school ERP.

## 1. Product at a glance

Mind helps schools create, conduct, evaluate and learn from academic assessments through one connected platform. It gives teachers controlled access to curriculum-aligned content and tools to generate worksheets, quizzes, question papers, tests and practice material. Students receive assigned assessments, submit responses, review feedback and practise topics. Administrators configure the academic structure, users, permissions and institutional settings.

Mind is intended to start as a focused engineering/community-service project and evolve into a reliable, scalable product. The initial release should prove that teachers can save meaningful preparation time and that students receive clearer, more useful practice and feedback.

## 2. Product principles

- Teacher-first utility: reduce repetitive preparation and assessment work.
- Curriculum alignment: content must respect class, subject, chapter, topic, board and difficulty context.
- Human control: AI-generated content is a draft until a teacher reviews and approves it.
- Explainability: show answer keys, source/context and generation settings where applicable.
- Student safety: age-appropriate design, minimal data collection and role-based access.
- Reliable assessment: deterministic scheduling, clear attempt rules and auditable grading.
- Modular growth: ship a useful academic product before adding adjacent school operations.

## 3. Initial roles

| Role | Main responsibility |
|---|---|
| Admin | Configure school, academic year, classes, sections, subjects, teacher assignments, users and policies |
| Teacher | Access assigned classes/subjects; create, review, publish and evaluate academic material |
| Student | View assigned work, attempt assessments, submit answers and review permitted feedback |

A teacher should only see classes/sections and subjects assigned to them. For example, a Mathematics teacher assigned to 11E, 12A and 12D can access the relevant Mathematics curriculum and approved JEE-preparation material for those assignments.

## 4. Initial academic scope

Supported subject catalogue (configurable by institution):
- Physics, Chemistry, Mathematics, Biology
- History, Geography, English, Computer Science

Core capabilities:
- AI worksheet and assignment generation
- AI quiz generation (MCQ and short-answer)
- Question-paper generation
- Custom question generation by topic, difficulty, marks, type and count
- Class tests, mocks and pre-board papers
- Test scheduling and publishing
- Answer-key and marking-scheme generation
- Teacher review/edit/approve workflow
- Student attempt and submission
- Basic evaluation and performance analytics

## 5. Explicitly out of scope for V1

Mind is not intended to be a full ERP in its first release. Exclude fee collection, payroll, transport, hostel, inventory, attendance administration, admissions CRM, timetable administration, parent portal, HR and general school operations unless separately approved in a later product decision. Do not let these features delay the academic product.

## 6. Suggested technology direction

- Frontend: React + TypeScript
- Backend: Python + FastAPI
- Database: PostgreSQL
- Cache / background jobs: Redis + worker queue
- File/object storage: S3-compatible storage
- AI layer: provider-agnostic model gateway with prompt/version management
- Retrieval: PostgreSQL full-text initially; vector search when a verified content corpus justifies it
- Authentication: secure session or JWT strategy with refresh rotation; institutional identity integration later
- Deployment: Docker, managed database, object storage, CI/CD and environment-based configuration

These are recommended defaults, not irreversible commitments. Validate hosting cost, team skill and institutional requirements before implementation.

## 7. Main workflows

1. Admin configures academic year, classes, sections, subjects and teacher assignments.
2. Teacher opens an assigned class/subject workspace.
3. Teacher selects content context and generation settings.
4. Mind generates a draft worksheet, quiz or paper.
5. Teacher reviews, edits, checks answer key and approves.
6. Teacher publishes immediately or schedules it.
7. Student receives the assignment, attempts it and submits.
8. Mind evaluates objective items automatically and routes subjective items to teacher review or a clearly disclosed assisted-evaluation workflow.
9. Teacher reviews performance analytics and assigns targeted practice.

## 8. Repository documentation

- `README.md` — project entry point and setup overview
- `PRD.md` — requirements, users, scope and acceptance criteria
- `Design.md` — UX principles, navigation and screen behaviour
- `Memory.md` — durable product decisions and project context
- `Architecture.md` — system architecture and technical boundaries
- `Rules.md` — engineering, AI, content and security rules
- `Phases.md` — staged delivery roadmap
- `Tasks.md` — actionable implementation backlog
- `API.md` — API conventions and endpoint catalogue

## 9. Definition of a successful V1

A pilot teacher can sign in, access only assigned classes/subjects, generate and edit a curriculum-contextualised assessment, publish or schedule it, and review student submissions. A student can securely attempt and submit assigned work. Admin can manage the academic structure and access. The system records audit events, protects student data and remains usable under realistic pilot load.

## 10. Important product caveat

AI output can contain factual errors, ambiguous questions or incorrect answer keys. Mind must never represent generated content as verified merely because a model produced it. Teacher approval is mandatory before student publication.
