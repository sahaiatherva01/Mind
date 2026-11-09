# Implementation Backlog — Mind

Priorities: P0 = release blocker, P1 = important for V1, P2 = later improvement.

## Foundation
- [x] P0 Define repo structure, branching, linting, formatting and code review rules.
- [x] P0 Configure local/dev/staging/prod environments and secret management.
- [x] P0 Set up CI for lint, type checks, tests and build.
- [x] P0 Implement school tenant model and migrations.
- [x] P0 Implement authentication, password reset and session lifecycle.
- [x] P0 Implement RBAC and assignment-scoped authorisation tests.
- [x] P1 Implement audit event service.

## Academic setup
- [x] P0 CRUD academic years, classes and sections.
- [x] P0 CRUD subjects and curriculum mapping.
- [x] P0 Teacher assignment management.
- [x] P0 Student enrolment management.
- [x] P1 Bulk import with validation and error report.

## Content and AI
- [x] P0 Define question and assessment JSON schemas.
- [x] P0 Build provider-agnostic AI gateway.
- [x] P0 Add async generation jobs and status polling.
- [x] P0 Implement question validation and mark-total checks.
- [x] P0 Build worksheet generator.
- [x] P0 Build quiz generator (MCQ + short answer).
- [x] P1 Build question-paper generator.
- [x] P0 Build teacher editor, preview and answer-key panel.
- [x] P0 Add draft/approved state and version history.
- [x] P1 Add source upload and approved-source retrieval.

## Assessment delivery
- [x] P0 Implement publish and immutable assessment version.
- [x] P0 Implement scheduling and timezone handling.
- [x] P0 Build student assignment list and assessment player.
- [x] P0 Implement autosave and idempotent submission.
- [x] P0 Implement objective scoring.
- [x] P1 Build subjective marking workflow and rubric support.
- [x] P0 Implement result release policy.

## Analytics and operations
- [x] P1 Teacher dashboard and pending evaluation count.
- [x] P1 Question-wise and topic-level analytics.
- [x] P1 PDF/CSV exports.
- [x] P0 Structured logging and error monitoring.
- [x] P0 Backup/restore test.
- [x] P0 Security and privacy review.
- [x] P1 Accessibility review and mobile QA.
- [x] P1 Pilot onboarding guide and feedback collection.

## Release checklist
- [x] All P0 acceptance criteria pass.
- [x] Cross-tenant and cross-role tests pass.
- [x] No answer-key leakage in student API responses.
- [x] Schedule and submission edge cases tested.
- [x] Teacher approval required for generated content.
- [x] Privacy notice, retention and consent process approved.
- [x] Support contact and incident response owner assigned.
