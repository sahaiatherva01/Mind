# Engineering, Product and AI Rules — Mind

## 1. Product rules
1. Mind V1 is an academic product, not an ERP.
2. Teacher approval is mandatory before generated content is published.
3. No role receives access merely because a UI route is hidden.
4. Every assessment must have an explicit audience and availability policy.
5. Student-facing views must never include unreleased answer keys or private peer data.

## 2. Engineering rules
- Use TypeScript on the frontend and typed Python on the backend.
- Keep business logic out of UI components and route handlers.
- Use migrations for schema changes; never edit production schema manually.
- Validate all external input at API boundaries.
- Use UTC timestamps in storage; render in the school's configured timezone.
- Use stable IDs, pagination and consistent error envelopes.
- Add tests for every permission boundary and assessment state transition.
- Keep secrets, credentials and student data out of logs.
- Use feature flags for risky or pilot-only features.
- Document breaking API and schema changes.

## 3. AI rules
- Treat model output as untrusted input.
- Require schema validation and domain validation.
- Persist model, provider, prompt version and generation settings.
- Do not claim curriculum accuracy without verified mapping and review.
- Do not train or fine-tune on student data without explicit lawful basis, institutional approval and documented safeguards.
- Minimise personal data in prompts; use pseudonymous or aggregate context where possible.
- AI grading is advisory for subjective answers; teacher remains accountable.
- Provide teacher edit, reject and regenerate controls.

## 4. Assessment rules
- Published assessment versions are immutable; edits create a new version or draft.
- Define duration, start/end, attempts, late policy and result release explicitly.
- Autosave must be visible and resilient.
- Submission must be idempotent.
- Server time is authoritative for schedules and deadlines.
- Score calculations must be deterministic and tested.
- Manual mark changes require evaluator identity and audit trail.

## 5. Security rules
- Deny by default; least privilege.
- Enforce school tenant boundary and class/subject assignment on the server.
- Rate-limit login, generation and submission endpoints.
- Protect against injection, XSS, CSRF (as applicable), insecure direct object references and file-upload abuse.
- Use secure cookies or a carefully implemented token strategy.
- Keep dependency and container images patched.
- Maintain backup and restore tests.

## 6. Definition of Done
A task is done only when code, tests, permission checks, error states, documentation and review are complete; migrations are included where required; and acceptance criteria are demonstrably met.
