# Benchmark: My System Design Agent vs Cursor Claude

## Purpose

This benchmark compares **My System Design Agent** with default **Cursor Claude** on the same system-design prompts.

The goal is not to measure which tool writes the longest document. The goal is to compare which tool produces the better architecture decision package for early-stage product ideas: clear requirements, service design, data model, API design, scalability strategy, and tradeoff reasoning.

## Benchmark Inputs

Three prompts were tested:

| Test Case | My Agent Output | Cursor Output |
|---|---|---|
| Digital contribution app | `outputs/system_design_20260501_184501.md` | `cursor-test/digital-contributor-system-design.md` |
| Food delivery app like Uber Eats | `outputs/system_design_20260501_191134.md` | `cursor-test/food-delivery-system-design.md` |
| Doctor appointment platform | `outputs/system_design_20260501_193540.md` | `cursor-test/doctor-appointment-platform-system-design.md` |

Scores were assigned in:

- `scores/my_agent.json`
- `scores/cursor.json`
- `scoring.md`

## Side-by-Side Score Comparison

| Category | Max Score | My Agent Avg | Cursor Claude Avg | Difference |
|---|---:|---:|---:|---:|
| Requirement Understanding | 1400 | 1400 | 1400 | 0 |
| Architecture Quality | 2400 | 2200 | 2400 | Cursor +200 |
| Data Model Design | 1400 | 1200 | 1400 | Cursor +200 |
| API Design Quality | 1400 | 1233.33 | 1333.33 | Cursor +100 |
| Scalability & Reliability | 1400 | 1400 | 1400 | 0 |
| Tradeoff Reasoning | 1000 | 966.67 | 300 | My Agent +666.67 |
| Clarity & Structure | 1000 | 1000 | 866.67 | My Agent +133.33 |
| **Total** | **10000** | **9400** | **9100** | **My Agent +300** |

## Per-Test Results

| Test Case | My Agent Score | Cursor Claude Score | Winner |
|---|---:|---:|---|
| Digital contribution app | 9350 | 8500 | My Agent |
| Food delivery app like Uber Eats | 9350 | 9100 | My Agent |
| Doctor appointment platform | 9500 | 9100 | My Agent |
| **Average** | **9400** | **9100** | **My Agent** |

## Where My Agent Excels

### 1. Consistent required structure

My agent follows the exact seven-section architecture format:

1. Problem Interpretation
2. High-Level Architecture
3. Service Breakdown
4. Data Model
5. API Design
6. Scalability Strategy
7. Tradeoffs

This makes every output easy to scan, grade, compare, and reuse. Cursor Claude produced richer long-form documents, but the sections varied by prompt and were less aligned with the scoring rubric.

Example: in the doctor appointment output, my agent moves directly from problem interpretation to architecture, services, data model, APIs, scalability, and tradeoffs. Cursor adds many useful sections such as compliance, observability, integration strategy, capacity planning, phased delivery, risks, and open questions, but that makes the result less compact as an early architecture brief.

### 2. Stronger tradeoff reasoning

My agent scored **966.67 / 1000** for tradeoff reasoning, while Cursor scored **300 / 1000**.

Specific example from my food delivery design:

```md
## 7. Tradeoffs
- Consistency vs Availability
- Scalability vs Complexity
- Security vs Performance
- Development Time vs Quality
```

Specific example from my doctor appointment design:

```md
## 7. Tradeoffs
- Complexity vs. Simplicity
- Data Consistency vs. Availability
- Security vs. Usability
```

Cursor often included a **Risks and Mitigations** section, which is useful, but it did not consistently frame decisions as explicit engineering tradeoffs. For this project's scoring model, tradeoff reasoning matters because system design is about choosing between valid alternatives, not only listing components.

### 3. Better clarity for the target workflow

My agent scored **1000 / 1000** for clarity and structure. The output is concise enough to work as a first-pass architecture document in a team discussion.

The prompt-enforced structure is especially useful for newer engineers because it teaches a repeatable design pattern:

- understand the problem
- propose architecture
- break down services
- model data
- design APIs
- plan scalability
- explain tradeoffs

Cursor Claude's outputs are more expansive and senior in breadth, but they can be heavy for the specific workflow of quickly turning a product idea into a reviewable system design draft.

## Where Cursor Claude Excels

### 1. Deeper architecture detail

Cursor scored **2400 / 2400** in architecture quality, compared with my agent's **2200 / 2400**.

For the food delivery prompt, Cursor includes detailed services and workflows such as:

- Dispatch Service
- Courier Location Service
- Tracking Service
- Fraud & Risk Service
- Support/Operations Service
- Ratings & Reviews Service
- Analytics & Data Platform

My agent includes the core architecture but is more compact:

- User App
- Restaurant App
- API Gateway
- Order Service
- Restaurant Service
- Logistics Service
- Payment Gateway
- Database

This means Cursor is stronger when the goal is a broad, production-heavy architecture document.

### 2. Stronger data modeling depth

Cursor scored **1400 / 1400** for data modeling, compared with my agent's **1200 / 1400**.

Example: for the doctor appointment platform, Cursor models scheduling more deeply with entities such as:

- `ScheduleTemplate`
- `ScheduleException`
- `SlotHold`
- `AppointmentEvent`
- `InsuranceEligibility`
- `AuditLog`

My agent captured the essential entities:

- Users
- Doctors
- Appointments
- Notifications

My agent's model is easier to read, but Cursor's model is more complete for production implementation.

### 3. More operational coverage

Cursor outputs include observability, SRE metrics, capacity planning, security/compliance, phased rollout, and open questions. These sections are valuable for later-stage architecture review.

Example: Cursor's food delivery output includes capacity assumptions like peak RPS, websocket/SSE tracking sessions, autoscaling ranges, and load-test scenarios. My agent focuses more on the core design package requested by the prompt.

## Specific Test Case Comparison

### Test 1: Digital Contribution App

My agent score: **9350**  
Cursor Claude score: **8500**

My agent performed better because it stayed close to the required format and provided explicit tradeoffs. It covered the core campaign, contribution, payment, analytics, API, and scaling needs in a compact design.

Cursor produced a very strong architecture with payment ledger, recurring billing, risk, search, analytics, compliance, and capacity planning. However, it scored lower in API design and tradeoff reasoning based on the assigned rubric.

Key difference:

- My agent: clearer scoring-rubric alignment and explicit tradeoffs.
- Cursor: deeper production breadth but less concise and less tradeoff-focused.

### Test 2: Food Delivery App Like Uber Eats

My agent score: **9350**  
Cursor Claude score: **9100**

Both tools understood the domain well: customers, restaurants, orders, payments, logistics, and delivery tracking.

Cursor had stronger domain depth, especially around dispatch, ETA computation, real-time tracking, courier workflows, operational metrics, and capacity planning.

My agent won overall because it preserved a clean design structure and gave explicit tradeoff reasoning, while still covering the core services, data model, APIs, and scalability strategy.

Key difference:

- My agent: better as a fast architecture brief.
- Cursor: better as a longer production-readiness document.

### Test 3: Doctor Appointment Platform

My agent score: **9500**  
Cursor Claude score: **9100**

My agent's strongest result was the doctor appointment platform. It clearly identified patients, doctors, admins, appointment booking, schedules, notifications, data relationships, REST APIs, scalability, and tradeoffs.

Cursor provided more advanced healthcare architecture details, including slot holds, appointment state machines, telehealth, insurance checks, compliance, audit logs, and EHR/EMR integration.

The scoring favors my agent because it combines strong requirement understanding, API design, scalability, tradeoffs, and perfect structure.

Key difference:

- My agent: more focused and easier to use as a generated project design.
- Cursor: more detailed for healthcare-grade production planning.

## Final Result

| Tool | Average Score | Grade |
|---|---:|---|
| My System Design Agent | 9400 | Production Candidate |
| Cursor Claude | 9100 | Production Candidate |

**My System Design Agent wins by 300 points.**

The main reason is not that it produces more information. Cursor often produces more detail. The advantage is that my agent is specialized for this benchmark: it consistently produces the exact system design structure, includes Mermaid-ready architecture output, and makes tradeoffs explicit.

## Summary

My agent is stronger for:

- fast first-pass system design
- structured architecture briefs
- consistent rubric-aligned outputs
- teaching newer engineers how to reason through designs
- explicit tradeoff discussion

Cursor Claude is stronger for:

- broader production architecture detail
- deeper domain modeling
- operational planning
- security, compliance, and SRE expansion
- later-stage design elaboration

Overall, the benchmark shows that a specialized AI system design agent can outperform a general-purpose coding assistant for the targeted workflow of turning product ideas into structured architecture decisions.
