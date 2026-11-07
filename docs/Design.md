# Product Design Specification — Mind

## 1. Experience direction

Mind should feel like a focused academic workspace: calm, dependable, clear and efficient. Avoid the visual complexity of an ERP dashboard. Prioritise the teacher's next action and the student's assigned work.

## 2. Information architecture

### Shared shell
- Sign in / password recovery
- Role-aware home dashboard
- Notifications
- Profile and account settings
- Help / support

### Admin navigation
- Overview
- Academic Setup
- Classes & Sections
- Subjects
- Users
- Teacher Assignments
- Student Enrolments
- Audit & Settings

### Teacher navigation
- Dashboard
- My Classes
- Subject Workspace
- AI Studio
  - Worksheet Generator
  - Quiz Generator
  - Question Paper Generator
  - Question Builder
- Assessments
- Schedule
- Submissions & Evaluation
- Analytics
- Question Library

### Student navigation
- My Learning
- Upcoming Assessments
- Assigned Worksheets
- My Attempts
- Results & Feedback
- Practice (if enabled)

## 3. Core screens and behaviour

### Teacher dashboard
Show assigned classes, upcoming tests, pending evaluations, recent drafts and quick actions. Never show unassigned classes.

### Class/subject workspace
Display class, section, subject, curriculum mapping and relevant content. Example: Mathematics teacher assigned to 11E, 12A and 12D sees those workspaces and their configured resources.

### AI Studio
Use a guided form with progressive disclosure:
1. Select output type.
2. Select class/subject and topic.
3. Set count, marks, difficulty and question types.
4. Add instructions or approved source.
5. Generate draft.
6. Review generated items in an editable list.

Show a generation status and allow the teacher to leave the page while a background job runs. Preserve entered configuration.

### Assessment editor
Support reorder, edit, delete, regenerate item, duplicate item, marks adjustment and preview. Display total marks and validation warnings continuously. Keep answer key in a teacher-only panel.

### Publish/schedule
Show clear audience, availability window, duration, attempts, late-submission rule, result-release rule and confirmation summary. Require explicit confirmation before publishing.

### Student assessment
Provide a distraction-light attempt screen, progress indicator, clear time remaining where timed, autosave state, question navigation and final submission confirmation. Warn before leaving with unsaved content only if autosave has not completed.

### Evaluation and analytics
Separate objective auto-score from teacher-awarded subjective marks. Show question-wise performance, topic strengths/gaps and class distribution without exposing other students' private records.

## 4. Design system guidance

- Typography: highly legible sans-serif; clear hierarchy.
- Layout: responsive, consistent spacing, restrained surfaces.
- Colour: accessible contrast; use colour as status support, never as the only signal.
- Components: buttons, inputs, selectors, chips, cards, tables, tabs, dialogs, toasts, empty states and skeletons.
- Status vocabulary: Draft, Generating, Needs Review, Approved, Scheduled, Published, Closed, Evaluated, Results Released.
- Accessibility: keyboard focus, semantic labels, screen-reader names, error summaries and sufficient contrast.

## 5. Content and trust patterns

- Label AI-generated content clearly.
- Display selected generation settings near the draft.
- Show warning that teacher verification is required.
- Never place hidden answers in student-facing HTML/API payloads.
- Make schedule timezone explicit and use the school's configured timezone.
- Explain why an action is disabled (e.g. missing teacher assignment).

## 6. Responsive behaviour

Teacher authoring should be optimised for laptop/desktop but remain usable on tablets. Student attempt and review flows must work on mobile. Admin setup may be desktop-first but must not break on smaller screens.

## 7. Empty, loading and error states

Every major list needs a useful empty state with a relevant next action. AI generation must distinguish queued, running, completed, failed and cancelled. Errors should preserve user input and provide a retry path without duplicating published assessments.
