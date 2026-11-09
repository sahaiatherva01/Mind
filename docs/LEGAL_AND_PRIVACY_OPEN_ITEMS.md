# Mind V1 — Legal & Privacy Open Items & Compliance Guide

*Intelligence for Better Learning*  
Target Regulatory Framework: **Digital Personal Data Protection Act, 2023 (DPDP Act, India)**  
Document Status: Authoritative Compliance Guidance  
Date: November 2026

---

## 1. Regulatory Status & Classification

Under the Digital Personal Data Protection Act, 2023 (DPDP Act) of India:
- **The School / Educational Institution** is the **Data Fiduciary**. The school determines the purpose and means of processing personal data of teachers and students.
- **Mind (the platform)** operates strictly as a **Data Processor** acting solely under written data processing agreements (DPA) with the school.

---

## 2. Processing Children's Personal Data (Section 9 DPDP Act)

Because students enrolled in Classes 6–12 are predominantly minors (under 18 years of age), Section 9 mandates stringent safeguards:

### 2.1 Verifiable Parental Consent
- **Pre-Enrollment Requirement**: Before activating student accounts, schools must obtain verifiable consent from the parent or lawful guardian.
- **School-Mediated Consent Model**: In school enterprise software deployments, schools typically collect written parent consent during annual school admission/enrollment. Mind requires the School Admin to certify that valid parental consent is on file prior to executing bulk student roster imports (`.xlsx` / `.csv`).

### 2.2 Statutory Prohibitions
Section 9 strictly prohibits:
1. **Behavioral Tracking & Targeted Advertising**: Mind contains ZERO advertisements, third-party marketing trackers, tracking pixels, or cross-site profiling.
2. **Detrimental Processing**: No profiling or automated processing that could adversely affect the physical or mental well-being of a child is permitted. Mind's analytics are strictly academic and diagnostic, visible only to authorized teachers and parents/students themselves.

---

## 3. Data Minimization & AI Privacy Protection

### 3.1 Non-Negotiable Principle: Zero Student Data to External AI
Mind enforces a strict domain boundary:
- **Generation Pipelines**: AI models (e.g., Google Gemini) receive **only** curriculum parameters: board, grade, chapter, topic, learning objective, and pedagogical style instructions.
- **Never Transmit Student PII**: Student names, roll numbers, individual answers, biometric data, or behavioral profiles are **never** transmitted to external AI providers.
- **AI Gateway Safeguard**: All outbound prompts passing through `ai_engine/adapters/gateway.py` are audited for absence of PII.

---

## 4. Data Retention, Storage & Archival Policy

### 4.1 Storage Location & Data Localization
- All primary databases (PostgreSQL), caches (Redis), and document storage (S3/MinIO) are hosted within Indian data regions (e.g., AWS ap-south-1 Mumbai / Render regional cluster) to ensure compliance with Indian data sovereignty standards.

### 4.2 Retention Lifecycle
| Data Category | Retention Period | Deletion / Archival Action |
|---|---|---|
| Active Session Tokens | 7 days of inactivity | Hard deleted from `sessions` table |
| Audit Trail Logs | 365 days | Archived to encrypted, immutable audit logs |
| Student Responses & Marks | Academic Year + 90 days | Cold encrypted archival upon school sign-off |
| Ephemeral AI Generation Jobs | 48 hours | Automatic purge from job queue |

---

## 5. Data Principal Rights (Sections 11–14 DPDP Act)

The platform provides administrative tools for schools to fulfill student and teacher rights:
1. **Right to Access & Summary**: The CSV export service provides complete transcripts of all student attempts, scores, and timestamps upon request.
2. **Right to Correction & Erasure**: School Admins have the ability to deactivate or purge user accounts. Deleting a student marks their records inactive and scrubs personally identifiable fields.
3. **Right of Grievance Redressal**: The school must designate a Data Protection Officer (DPO) whose contact information is displayed on the platform login footer.

---

## 6. Security & Breach Response

- **Encryption**: TLS 1.3 in transit; AES-256 for persistent object storage and backups.
- **Password Security**: Argon2id with unique cryptographic salts.
- **Incident Response Plan**: In the event of a personal data breach, Mind's automated audit trail enables tracing affected records. Mind will notify the school within 24 hours of confirmation, enabling the school to fulfill the mandatory statutory notification to the Data Protection Board of India.

