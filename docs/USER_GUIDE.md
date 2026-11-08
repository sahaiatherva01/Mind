# Mind V1 — End-to-End User & Operational Guide

*Intelligence for Better Learning*  
Platform Version: 1.0.0  
Date: November 2026

---

## 1. Introduction & Overview

**Mind** is an AI-powered academic assessment, teaching, and learning platform designed specifically for schools following the ICSE and ISC curriculum. Mind bridges the entire academic testing cycle into one coherent workflow:
$$\text{Content Creation} \longrightarrow \text{Assessment Delivery} \longrightarrow \text{Evaluation} \longrightarrow \text{Learning Analytics}$$

### The Three Strict Roles
Mind is deliberately engineered around three canonical roles:
1. **Admin**: Manages school academic setup, bulk onboarding, and security audit logs.
2. **Teacher**: Generates, edits, approves, publishes, and grades assessments for their explicitly assigned classes and subjects.
3. **Student**: Takes scheduled assessments in a secure, distraction-free player with real-time autosave and views released results.

---

## 2. Quick Start & Local Execution

### 2.1 Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- (Optional for containerized run) Docker & Docker Compose

### 2.2 Starting the Platform
```bash
# 1. Setup Python Virtual Environment and Install Backend Dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

# 2. Seed Database with Demo School & ICSE Class 11/12 Workspaces
python database/seed/seed_data.py

# 3. Start Backend Server (runs on http://localhost:8000)
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

# 4. In a separate terminal, Start Frontend (runs on http://localhost:5173)
cd frontend
npm install
npm run dev
```

### 2.3 Preset Test Accounts
When navigating to `http://localhost:5173/login`, you can log in with one click using preset demo accounts:
| Role | Email | Password | Assigned Scope |
|---|---|---|---|
| **Admin** | `admin@minddemo.edu` | `AdminPass123!` | Complete tenant administration |
| **Teacher** | `sarah.physics@minddemo.edu` | `TeacherPass123!` | Class 11E, 12A, 12D (Physics, Science) |
| **Student** | `aarav.11e@minddemo.edu` | `StudentPass123!` | Class 11E Student (Roll #1) |

---

## 3. School Administrator Guide

### 3.1 Academic Structure Setup
1. Log in as **Admin**.
2. Navigate to **Academic Setup** (`/admin/academic-setup`).
3. Create the current **Academic Year** (e.g., `2026-2027`).
4. Define **Classes and Sections** (e.g., Class 11 - Section E, Class 12 - Section A).
5. Add **Curriculum Subjects** (Physics, Chemistry, Mathematics, Biology, Computer Science, etc.).
6. Map **Teacher Assignments**: Select teacher, class, section, and subject.
   > **Security Enforcement**: Teachers will strictly *only* see and author assessments for class-section-subject combinations assigned to them.

### 3.2 Bulk User Onboarding (`.xlsx` / `.csv`)
1. Navigate to **Bulk Import** (`/admin/bulk-import`).
2. Download the pre-formatted Excel template (`mind_onboarding_template.xlsx`).
3. Populate rows with columns: `Role, Full Name, Email, Password, Class, Section, Roll Number, Designation`.
4. Upload the file. The importer will parse each row, validate email formats and role constraints, and output a detailed confirmation report with row-level error feedback.

### 3.3 Security & Audit Event Logs
1. Navigate to **Audit Logs** (`/admin/audit`).
2. Inspect chronological timestamps, actor IDs, IP addresses, and specific events (e.g., `user.login`, `assessment.published`, `results.released`).

---

## 4. Teacher Guide

### 4.1 Navigating Your Assigned Workspaces
When you log in as a Teacher, your **Teacher Dashboard** displays only your assigned classes and subjects. A prominent banner reinforces that **Teacher Approval is Mandatory** before any AI-generated content can reach students.

### 4.2 Generating an Assessment via AI Studio (`/teacher/ai-studio`)
Mind features a 4-step progressive disclosure wizard:
1. **Target Selection**: Pick assigned Class, Section, and Subject.
2. **Assessment Type & Scope**: Choose Worksheet, Quiz, Question Paper, or Custom Set. Enter chapter and topics.
3. **Question Type Master Checklist**: Select from **40 ICSE/ISC Board Exam Question Types** across 5 categories:
   - *Objective*: MCQ, Multiple Select, Fill in the Blanks, True/False, Match the Following, Assertion-Reason.
   - *Written*: Very Short, Short, Medium, Long Answer, Definition, Difference, Reasoning, Derivation.
   - *Visual & Math*: Diagram, Label the Diagram, Graph, Table, Chart, Map, Numerical, Formula.
   - *Application & Analytical*: Case-Based, Passage-Based, Source-Based, Data Interpretation, HOTS, Critical Thinking, Experiment-Based.
   - *Computer Science*: Output Prediction, Theory + Coding, Code Completion, Error Detection, Debugging, Dry Run, Algorithm Writing, Program Writing.
4. **Marks & Difficulty**: Set total marks and difficulty distribution, then click **Generate Draft with AI**.

### 4.3 Reviewing & Editing Drafts in the Assessment Editor
1. Review generated questions in the live editor.
2. Expand confidential answer keys and marking schemes (only visible to teachers).
3. **Edit in place**: Update prompts, change mark allocations, or reorder questions.
4. **Regenerate Single Item**: Click the refresh icon on any question, provide corrective feedback (e.g., *"Make this numerical harder"*), and regenerate without affecting the rest of the paper.
5. **Mandatory Approval Gate**: Click **Approve Assessment Draft** to mark it ready for publishing.

### 4.4 Publishing & Scheduling Delivery
1. In **Assessments** (`/teacher/assessments`), click **Publish / Schedule** on any approved assessment.
2. Configure:
   - Available start time and deadline (UTC authoritative).
   - Exam duration limit (e.g., 60 minutes).
   - Maximum attempt count (default: 1).
   - **Result Release Mode**:
     - `manual_by_teacher`: Students only see scores when you click "Release Results".
     - `immediate_on_submit`: Student sees objective scores immediately upon submission.
     - `scheduled_datetime`: Results unlock automatically at a future timestamp.

### 4.5 Grading Subjective Answers (`/teacher/evaluations`)
1. Navigate to **Evaluation Queue** (`/teacher/evaluations`).
2. Review pending student responses for subjective questions (derivations, definitions, code).
3. View the student's answer alongside the model answer and marking rubric.
4. Enter marks and optional feedback, then click **Submit Grade**.
5. Once all items are graded, release final results to students.

### 4.6 Analytics & Psychometric Item Diagnostics (`/teacher/analytics`)
1. Navigate to **Analytics** (`/teacher/analytics`).
2. **Item Diagnostics Table**: View question accuracy ($P$-value) and discrimination index ($D$). Items with $D \ge 0.40$ demonstrate high diagnostic value; items with $D < 0.20$ are flagged for review.
3. **Score Distribution**: Normalized bell curve visualization across 5 score tiers.
4. **Curriculum Topic Gaps**: Identify topics where class mastery is below 60% with one-click links to generate remedial practice sets.
5. **Exports**: Click **Export Gradebook CSV** or **Print with Marking Scheme** for physical archival.

---

## 5. Student Guide

### 5.1 Viewing Assigned Work
1. Log in as **Student**.
2. The dashboard and **Upcoming Tests** (`/student/tests`) display all tests assigned to your class and section.
3. Assessments show availability windows and duration limits.

### 5.2 Taking an Exam in the Assessment Player
1. Click **Start Test** on an active assessment.
2. The distraction-free Assessment Player opens:
   - **Live Countdown Timer**: Tracks time remaining based on authoritative server clock.
   - **Question Palette**: Jump easily between answered, unanswered, and flagged questions.
   - **Real-Time Autosave**: Every selection and typed keystroke is autosaved with a green checkmark indicator.
3. Click **Submit Test** when finished. Submissions are strictly idempotent.

### 5.3 Reviewing Results
1. After the teacher releases results, navigate to **My Results** (`/student/results/:attemptId`).
2. View your total score, percentage grade, question-by-question breakdown, teacher comments, and verified model answers.

---

## 6. Security & Support Escalation

- **Zero Leakage**: Student browser payloads never contain answer keys or teacher metadata before result release.
- **Support Contact**: For technical incidents or data privacy queries, email `support@mindplatform.edu` or open an issue with the institution administrator.

