# Implementation Backlog — Mind

Priorities: P0 = release blocker, P1 = important for V1, P2 = later improvement. Owners and dates are intentionally unassigned until the team is confirmed.

## Foundation
- [ ] P0 Define repo structure, branching, linting, formatting and code review rules.
- [ ] P0 Configure local/dev/staging/prod environments and secret management.
- [ ] P0 Set up CI for lint, type checks, tests and build.
- [ ] P0 Implement school tenant model and migrations.
- [ ] P0 Implement authentication, password reset and session lifecycle.
- [ ] P0 Implement RBAC and assignment-scoped authorisation tests.
- [ ] P1 Implement audit event service.

## Academic setup
- [ ] P0 CRUD academic years, classes and sections.
- [ ] P0 CRUD subjects and curriculum mapping.
- [ ] P0 Teacher assignment management.
- [ ] P0 Student enrolment management.
- [ ] P1 Bulk import with validation and error report.

## Content and AI
- [ ] P0 Define question and assessment JSON schemas.
- [ ] P0 Build provider-agnostic AI gateway.
- [ ] P0 Add async generation jobs and status polling.
- [ ] P0 Implement question validation and mark-total checks.
- [ ] P0 Build worksheet generator.
- [ ] P0 Build quiz generator (MCQ + short answer).
- [ ] P1 Build question-paper generator.
- [ ] P0 Build teacher editor, preview and answer-key panel.
- [ ] P0 Add draft/approved state and version history.
- [ ] P1 Add source upload and approved-source retrieval.

## Assessment delivery
- [ ] P0 Implement publish and immutable assessment version.
- [ ] P0 Implement scheduling and timezone handling.
- [ ] P0 Build student assignment list and assessment player.
- [ ] P0 Implement autosave and idempotent submission.
- [ ] P0 Implement objective scoring.
- [ ] P1 Build subjective marking workflow and rubric support.
- [ ] P0 Implement result release policy.

## Analytics and operations
- [ ] P1 Teacher dashboard and pending evaluation count.
- [ ] P1 Question-wise and topic-level analytics.
- [ ] P1 PDF/CSV exports.
- [ ] P0 Structured logging and error monitoring.
- [ ] P0 Backup/restore test.
- [ ] P0 Security and privacy review.
- [ ] P1 Accessibility review and mobile QA.
- [ ] P1 Pilot onboarding guide and feedback collection.

## Release checklist
- [ ] All P0 acceptance criteria pass.
- [ ] Cross-tenant and cross-role tests pass.
- [ ] No answer-key leakage in student API responses.
- [ ] Schedule and submission edge cases tested.
- [ ] Teacher approval required for generated content.
- [ ] Privacy notice, retention and consent process approved.
- [ ] Support contact and incident response owner assigned.
