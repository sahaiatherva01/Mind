# Technical Architecture — Mind

## 1. Architecture goals
Secure multi-school support, strict role/assignment authorisation, reliable assessment delivery, asynchronous AI generation, explainable content provenance and modular evolution without premature microservices.

## 2. Recommended logical architecture

```mermaid
flowchart TB
  U[Platform Admin / School Admin / Coordinator / Teacher / Student] --> FE[React + TypeScript Web App]
  FE --> API[FastAPI API Layer]
  API --> AUTH[Central authorize(actor, action, resource)]
  API --> CORE[Academic Domain Services]
  CORE --> DB[(PostgreSQL)]
  CORE --> OBJ[(Object Storage)]
  CORE --> Q[Redis Job Queue / ARQ]
  Q --> WORKER[Background Workers]
  WORKER --> LG[LangGraph Agent Workflows]
  LG --> AI[AI Gateway]
  AI --> LLM[Google Gemini / Mock Provider]
  WORKER --> DB
  API --> OBS[Logs / Metrics / Traces]
  WORKER --> OBS
```

## 3. Architectural style

Modular monolith with clean domain boundaries:
- `identity`: users, sessions, password reset, `RoleAssignment`
- `tenancy`: schools, academic years, `Band`, institutional settings
- `academics`: classes, sections, subjects, curriculum mapping, `TeacherAssignment`, `StudentEnrollment`, rosters
- `content`: learning materials, PDF text chunking, Question Bank
- `ai`: LangGraph agents (extractor, generator, tagger, insight writer, paper builder, evaluation assist)
- `assessments`: drafts, versions, publishing, schedules, attempts, submissions, blueprints
- `evaluation`: objective deterministic scoring, rubrics, teacher marking assist, result release
- `analytics`: aggregates, psychometrics, 4-level and cross-analytics
- `notifications`: in-app and email adapters
- `audit`: security, administrative, and academic action event trail

## 4. Tenant and authorisation model

The centralized policy engine `authorize(actor, action, resource)` evaluates role and scope together:
- **Platform Admin:** Global platform actions; no `school_id`.
- **School Admin:** School-wide administration for active `school_id`.
- **Academic Coordinator:** Scoped strictly to `school_id` + assigned `band_id` (e.g. Classes 9–10).
- **Teacher:** Scoped to explicit `(school_id, class_id, section_id, subject_id, year_id)`.
- **Class Teacher:** Scoped to `(school_id, class_id, section_id)` for roster ownership and student credentialing.
- **Student:** Scoped to enrolled section and own attempt records.

Cross-tenant and cross-scope access is denied by default.

## 5. Data model (logical V2)

- `School(id, name, slug, timezone, settings)`
- `AcademicYear(id, school_id, label, starts_on, ends_on, status)`
- `Band(id, school_id, name, min_grade, max_grade)`
- `RoleAssignment(id, user_id, role, school_id, band_id, effective_from, effective_to, status)`
- `Class(id, school_id, band_id, academic_year_id, name, grade_level)`
- `Section(id, class_id, name, room)`
- `Subject(id, school_id, name, code)`
- `TeacherAssignment(id, school_id, teacher_id, class_id, section_id, subject_id, academic_year_id, is_class_teacher, status)`
- `StudentEnrollment(id, school_id, student_id, class_id, section_id, academic_year_id, roll_number, status)`
- `RosterStatus(id, section_id, academic_year_id, status, verified_by_id, locked_at)`
- `RosterChangeRequest(id, section_id, requester_id, approver_id, changes_json, status)`
- `ApprovalRequest(id, school_id, request_type, requester_id, approver_id, payload_json, status)`
- `CurriculumNode(id, school_id, subject_id, grade, chapter, topic, learning_outcome, source_ref)`
- `ContentAsset(id, school_id, owner_id, storage_key, metadata)`

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
