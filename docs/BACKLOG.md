# Mind V2 — Product & Engineering Backlog (Parked Items)

This document tracks items that are intentionally out of scope for V1/V2 implementation per Section 4 of the Master Loop Prompt. **Do not implement these without explicit human approval at a phase gate.**

---

## 1. Parked Platform Administration & Tenant Ops
- **Platform Admin Support Mode / Impersonation:** Consented cross-school impersonation session with time limits and audit trail.
- **Tenant Export & Backup Tooling:** Automated self-serve tenant export for DPDP/contract end.
- **Release Management:** Phased rollouts to pilot schools first.
- **Per-School AI Provider Routing:** Dynamic provider switching per school or per feature.
- **Security Centre:** Anomaly detection on failed logins, bulk downloads, and suspicious traffic.
- **Tenant Health Monitor:** Cross-school worker queue health, error spikes, and export latency metrics.

## 2. Parked Academic Operations (Non-Negotiable Scope Guardrails)
- **School ERP Modules:** Fee collection, payroll, transport, hostel, inventory, attendance administration, admissions CRM, timetable administration, parent portal, HR.
- **Independent (Non-School) Students:** B2C or direct student onboarding without an enrolled school.
- **Payments & Billing:** Invoicing, subscription gateways (Stripe/Razorpay), payment processing.

## 3. Parked Academic & Coordinator Features
- **Cross-Band Assignment Requests (`CrossBandRequest`):** Requests between coordinators across different class bands (Coordinators manage strictly within their assigned band for V1).
- **Workload Balancer:** Automated teacher period calculation and overload warnings.
- **Scheduled Emailed Reports:** Cron-based automated delivery of PDF reports to school heads.
- **Plagiarism & Similarity Flags:** Cross-submission linguistic similarity detection.

## 4. Parked Security & Auth Enhancements
- **Multi-Factor Authentication (MFA):** SMS/TOTP MFA enforcement (strong password policies are used instead).
- **Auth0 / External Identity Provider:** Kept parked in favor of first-party Argon2id session-cookie auth.
- **Malware & Virus Scanning:** Antivirus scanning hook for PDF uploads.

## 5. Parked AI & Generation Capabilities
- **Student-Facing AI Tutor Chatbot:** Direct student conversational AI interactions (Mind remains an assessment/materials platform).
- **Model Fine-Tuning (LoRA / QLoRA):** Training custom checkpoints on school content.
- **MCP Servers:** Model Context Protocol runtime integration.
- **Daily AI Tokens / Quotas:** Hard per-user token quotas.

