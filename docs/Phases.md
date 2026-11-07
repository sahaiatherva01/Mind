# Delivery Phases & Roadmap — Mind

Roadmap is capability-based. Dates should be assigned only after team capacity and pilot commitments are known.

## Phase 0 — Discovery and validation
**Outcome:** a validated, narrow pilot definition.
- Interview teachers and school leadership.
- Confirm board, grades, subjects, language and assessment formats.
- Map teacher preparation workflow and pain points.
- Validate content sources/licensing and privacy/consent expectations.
- Define baseline metrics and pilot success criteria.
**Exit gate:** signed-off V1 scope, pilot users, curriculum context and risk checklist.

## Phase 1 — Product foundation
**Outcome:** secure application foundation.
- Repository, environments, CI/CD and coding standards.
- Authentication, school tenancy, roles and audit events.
- Academic year, classes, sections, subjects and assignments.
- Teacher/student/admin shells and access-control tests.
**Exit gate:** users see only authorised school and academic data.

## Phase 2 — AI content studio
**Outcome:** teacher can create a verified draft.
- Question schema and question bank.
- Generation job queue and AI gateway.
- Worksheet, quiz, question and paper generation.
- Structured output validation and prompt versioning.
- Editor, answer key, preview, save and approval.
**Exit gate:** teacher can produce and approve a usable assessment draft.

## Phase 3 — Assessment lifecycle
**Outcome:** assessment can be delivered to students.
- Publish and schedule.
- Student assignment list and assessment player.
- Autosave, attempt limits and submission.
- Objective scoring and teacher evaluation queue.
- Result release controls.
**Exit gate:** end-to-end test from teacher authoring to student result.

## Phase 4 — Analytics and pilot hardening
**Outcome:** pilot-ready product.
- Class and question analytics.
- Topic-level performance insights.
- PDF/CSV export.
- Accessibility, security, load and recovery testing.
- Teacher onboarding and support playbook.
**Exit gate:** pilot acceptance criteria met; no critical security or data-integrity defects.

## Phase 5 — Controlled expansion
**Outcome:** evidence-led product expansion.
- More curriculum/board mappings and languages.
- Approved content library and reuse.
- More advanced evaluation/rubrics.
- Optional personalised practice.
- Institutional integrations only when demanded by validated customers.
**Exit gate:** expansion justified by usage, outcomes and support capacity.

## Release strategy
- Internal alpha → small teacher pilot → limited student cohort → school pilot → broader rollout.
- Use feature flags and staged migrations.
- Keep rollback and data backup plans for every production release.
