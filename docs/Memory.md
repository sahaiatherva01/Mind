# Project Memory & Decision Log — Mind

This file stores durable project context. Update it when a product decision changes; do not treat proposals as confirmed facts.

## 1. Identity and purpose
- Current working product name: **Mind** (renamed from LearnMind).
- Focus: AI-assisted academic assessment and learning for schools.
- Initial context: an engineering/community-service project intended to mature into a scalable product.
- The initial school context discussed was City Montessori School, R.J.P.M. 1. This is context for a pilot discussion, not evidence of a formal partnership or approval.

## 2. Confirmed product direction
- Three primary roles: Admin, Teacher and Student.
- Teacher access is scoped to assigned classes/sections and subjects.
- Example assignment model: a Mathematics teacher assigned to 11E, 12A and 12D sees those academic workspaces.
- Subject catalogue discussed: Physics, Chemistry, Mathematics, Biology, History, Geography, English and Computer Science.
- Core scope: worksheets, quizzes, question papers, custom question generation, class tests/mocks/pre-board papers, scheduling, answer keys and assessment workflows.
- Do not include broad ERP operations in V1.

## 3. Product and business direction discussed
- Schools are the likely primary B2B/B2B2C customer.
- Potential later options: teacher premium tier, student plan, school-wide subscription, enterprise/custom integrations and premium content.
- Earlier pricing exploration was a hypothesis (approximately ₹100–₹1,000+ per teacher/month or school annual pricing), not a validated price. Conduct willingness-to-pay interviews before fixing pricing.
- School outreach should focus on academic utility and feedback; do not present commercial intentions as the purpose of an initial school survey.

## 4. Reference products previously named
- AparAI LMS: https://aparailms.com/
- AparExam: https://aparexam.com/
- AparAcademy: https://aparacademy.com/
These are references for feature discovery, not permission to copy proprietary code, content, branding or UI.

## 5. Constraints and safeguards
- Avoid ERP scope creep.
- Teacher review is required before AI-generated content is published.
- Student privacy and age-appropriate handling are mandatory design concerns.
- Legal/privacy requirements, including applicable Indian data-protection obligations and school/parent consent processes, must be validated with qualified institutional/legal stakeholders before pilot launch.

## 6. Proposed technical defaults (not yet locked)
React + TypeScript, FastAPI/Python, PostgreSQL, Redis/background workers, object storage, provider-agnostic AI gateway and Docker-based deployment.

## 7. Decisions still required
- Pilot board/curriculum, grade range and language(s).
- Verified content sources and content licensing.
- AI provider/model and data-processing terms.
- Hosting region, retention and backup policy.
- Assessment integrity rules (attempts, shuffle, timing, late submissions).
- Student result-release policy.
- Pricing and procurement model.
- Final brand/domain/trademark clearance for “Mind”.
