# Technical Architecture — Mind

## 1. Architecture goals
Secure multi-school support, strict role/assignment authorisation, reliable assessment delivery, asynchronous AI generation, explainable content provenance and modular evolution without premature microservices.

## 2. Recommended logical architecture

```mermaid
flowchart TB
  U[Admin / Teacher / Student] --> FE[React + TypeScript Web App]
  FE --> API[FastAPI API Layer]
  API --> AUTH[Authentication & RBAC]
  API --> CORE[Academic Domain Services]
  CORE --> DB[(PostgreSQL)]
  CORE --> OBJ[(Object Storage)]
  CORE --> Q[Redis Job Queue]
  Q --> WORKER[Background Workers]
  WORKER --> AI[AI Gateway]
  AI --> LLM[Model Provider(s)]
  WORKER --> DB
  API --> OBS[Logs / Metrics / Traces]
  WORKER --> OBS
```

## 3. Architectural style

Start with a **modular monolith**: one deployable backend with well-separated domain modules. This is simpler to build, test and operate for an early team. Split services only when load, team ownership or reliability needs justify it.

Suggested backend modules:
- identity: users, sessions, password reset, role assignment
- tenancy: schools, academic years, institutional settings
- academics: classes, sections, subjects, curriculum mapping, assignments
- content: source materials, question bank, generated content
- generation: prompt templates, model gateway, job orchestration, validation
- assessments: drafts, versions, publishing, schedules, attempts, submissions
- evaluation: objective scoring, rubrics, teacher marking, result release
- analytics: aggregates and reports
- notifications: in-app and email/push adapters
- audit: security and business event trail

## 4. Tenant and authorisation model

Every school-owned record carries `school_id`. Every request resolves the authenticated user and active school membership. Server-side policies verify:
- Admin: permitted school administration actions.
- Teacher: explicit teacher assignment for class + section + subject.
- Student: active enrolment and explicit assessment audience.
- Cross-school access: denied by default.
Do not rely on hiding UI controls as an authorisation mechanism.

## 5. Data model (logical)

- School(id, name, timezone, settings)
- AcademicYear(id, school_id, label, starts_on, ends_on, status)
- Class(id, school_id, academic_year_id, name)
- Section(id, class_id, name)
- Subject(id, school_id, name, code)
- TeacherAssignment(id, school_id, teacher_id, class_id, section_id, subject_id)
- StudentEnrollment(id, school_id, student_id, class_id, section_id, status)
- CurriculumNode(id, school_id, subject_id, grade, chapter, topic, learning_outcome, source_ref)
- ContentAsset(id, school_id, owner_id, storage_key, metadata)
- Question(id, school_id, author_id, type, prompt, marks, difficulty, topic_id, answer_data, status, version)
- GenerationJob(id, school_id, requester_id, input_json, model, prompt_version, status, output_ref, error_code)
- Assessment(id, school_id, creator_id, class_id, section_id, subject_id, title, type, status, settings, version)
- AssessmentItem(id, assessment_id, question_id, position, marks_override)
- Schedule(id, assessment_id, starts_at, ends_at, timezone)
- Attempt(id, assessment_id, student_id, started_at, submitted_at, status)
- Response(id, attempt_id, assessment_item_id, answer_json, saved_at)
- Evaluation(id, attempt_id, evaluator_id, score, feedback, status)
- AuditEvent(id, school_id, actor_id, action, entity_type, entity_id, timestamp, metadata)

Use UUIDs or equivalent non-guessable identifiers. Add indexes for school_id, assignment lookup, assessment status/schedule and student attempt retrieval.

## 6. AI generation pipeline

1. API validates teacher assignment and request schema.
2. Persist generation job and immutable input snapshot.
3. Queue job; return job ID.
4. Worker assembles only authorised curriculum/source context.
5. AI gateway calls selected model using versioned prompt and structured output schema.
6. Validate JSON schema, question type, mark totals, option completeness and policy rules.
7. Persist draft content with model/provider/prompt metadata.
8. Notify requester; teacher reviews and approves.
9. Publication service snapshots approved assessment version.

Do not let a model directly publish, change permissions, or access arbitrary school data.

## 7. Assessment delivery pipeline

- Publish creates an immutable assessment version and audience mapping.
- Student access checks school, enrolment, schedule and attempt policy.
- Responses autosave with idempotency keys and optimistic concurrency/version checks.
- Submission is transactional and idempotent.
- Objective scoring uses deterministic server-side logic.
- Subjective marking is teacher-controlled; AI assistance is advisory and clearly labelled.
- Results are visible only after configured release.

## 8. API and infrastructure

- REST JSON API under `/api/v1`.
- OpenAPI generated from FastAPI.
- PostgreSQL as source of truth.
- Redis for queue/cache/rate limiting where needed.
- Object storage for uploaded documents and exports.
- Worker process for generation, exports and notifications.
- Docker for reproducible local and production environments.
- CI pipeline: lint, type checks, unit/integration tests, migration checks, dependency/security scans and build.

## 9. Security and privacy

- Password hashing with a modern password-hashing algorithm; secure session/refresh-token handling.
- TLS everywhere; encrypt sensitive stored data and backups.
- Secrets in managed secret storage, never in source control.
- Validate file type/size and scan uploads where feasible.
- Tenant-scoped database queries and tests for cross-tenant leakage.
- Audit admin, publishing, grading and access-sensitive actions.
- Data minimisation, retention/deletion controls and documented subprocessors.
- Review applicable Indian privacy law and school/parent consent requirements before processing children's data.

## 10. Scale and evolution

Begin with one backend deployment and separate worker capacity. Add read replicas, caching, partitioning or service extraction only after metrics demonstrate need. Use provider abstraction for AI portability; do not add multiple model providers before quality/cost evaluation.
