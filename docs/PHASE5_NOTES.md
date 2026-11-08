# Mind V1 — Phase 5 Controlled Expansion Notes

*Intelligence for Better Learning*  
Document Status: Authoritative Architecture Roadmap  
Date: November 2026

---

## 1. Executive Context

Mind V1 strictly limits scope to core academic assessment workflows for ICSE/ISC schools: **content creation → assessment delivery → evaluation → learning analytics**. All general school ERP functions (fees, transport, attendance, HR, timetable) remain excluded.

Phase 5 outlines the architecture path for post-pilot expansion once pilot feedback from the initial ICSE deployment is measured and stabilized.

---

## 2. Curriculum & Board Expansion

### 2.1 Supported Boards Roadmap
1. **ICSE / ISC (Council for the Indian School Certificate Examinations)**: Current V1 baseline (Classes 6–12, 40 question types, science & computer science streams).
2. **CBSE (Central Board of Secondary Education)**:
   - Introduce Class 9–12 NCERT curriculum taxonomies.
   - Support CBSE-specific typology: Case-Based Integrated Questions, Assertion-Reason pairings per CBSE blueprint, Competency-Based Assessments (NEP 2020 alignment).
3. **State Boards (Maharashtra State Board, Karnataka KSEEB/PUE, etc.)**:
   - Bilingual question paper layouts (English + regional language side-by-side).
   - State-specific textbook chapter mappings.

### 2.2 Taxonomy Isolation
- Boards must remain completely configurable via `board_code` in the `schools` table and `curriculum_nodes` hierarchy.
- No board-specific heuristics may be hardcoded into core execution pipelines.

---

## 3. Shared Institutional Question Bank & Collaborative Moderation

### 3.1 Architecture Overview
In V1, questions authored or generated within a school are tenant-isolated (`school_id`). In Phase 5:
- **Global Verified Repository**: High-quality teacher-approved questions can be opted into an anonymized, shared question bank.
- **Peer Moderation Gate**: Questions must undergo 2-teacher peer review before being promoted to the "Board Verified" library.
- **Attribution & Rights**: No proprietary school branding or student context is transferred.

---

## 4. Adaptive Learning & Automated Remediation

### 4.1 Diagnostic Feedback Loops
In V1, the `TeacherAnalytics` module identifies "Critical Gaps" (topics where mastery < 60%). In Phase 5:
- **Targeted Practice Assignment**: Teachers can click one button on a lagging topic to generate a 5-question micro-practice worksheet specifically targeting missed sub-concepts.
- **Difficulty Ladders**: Practice sets adaptively start at easy concept recall (definition/difference) and graduate to application/HOTS questions once 80% mastery is demonstrated.

---

## 5. Multi-Provider AI Fallback & Local Inference

### 5.1 AI Gateway Tiering
Currently, the AI Gateway supports Google Gemini with deterministic `MockAIProvider` for local testing. Phase 5 adds:
- **Cost/Latency Routing**: Low-complexity objective questions (MCQs, True/False) route to lighter models (e.g., Gemini Flash), while complex multi-step physics proofs or code debugging route to reasoning models.
- **On-Premise / Edge Inference**: For institutions with air-gapped data residency mandates, connect local Ollama/vLLM endpoints running open-weights models (e.g., Mistral/Llama 3).

---

## 6. Offline-Capable & Low-Bandwidth Delivery

### 6.1 Progressive Web App (PWA) Offline Player
- Cache published assessment payloads in browser IndexedDB.
- Permit students in rural or unstable network environments to answer questions offline.
- Cryptographically sign local autosave batches and synchronize them with the server when connectivity resumes.

