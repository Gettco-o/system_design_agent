# System Design: Doctor Appointment Platform

## 1) Overview

This document proposes a robust, scalable architecture for a doctor appointment platform that supports:
- Patient discovery and booking
- Doctor availability and schedule management
- Appointment lifecycle management (book, reschedule, cancel, complete)
- In-person and teleconsultation workflows
- Payments, reminders, and notifications

Given ambiguous requirements, assumptions are explicitly listed.

---

## 2) Assumptions (Explicit)

1. **Primary users**:
   - Patients
   - Doctors
   - Clinic/hospital staff (reception, admin)
   - Platform administrators
2. **Launch scope**:
   - Single country at launch, multi-city support
   - Expand to multi-country in later phases
3. **Visit types**:
   - In-person appointments (V1)
   - Video consultations (V1 or V2 depending on regulation and integration timeline)
4. **Scale target (Year 1)**:
   - 1.5M registered patients
   - 50K active doctors
   - 70K daily active users
   - 5K-12K peak requests/second (read-heavy)
5. **Booking constraints**:
   - Time-slot granularity: 15 minutes
   - Appointment duration varies by specialty/doctor (15-60 minutes)
6. **Consistency requirements**:
   - Slot reservation and booking must be strongly consistent (no double booking).
   - Search/discovery and analytics can be eventually consistent.
7. **Compliance**:
   - Healthcare data privacy regulations apply (HIPAA-like/GDPR-like depending region).
   - Audit logging required for sensitive access and changes.
8. **Availability target**:
   - Booking and scheduling APIs: 99.95%
   - Non-critical analytics/reporting: 99.9%
9. **Integration assumptions**:
   - Optional integration with EHR/EMR and insurance verification providers.
10. **Payments**:
    - Co-pay/consultation fee can be paid online or at clinic (configurable by provider).

---

## 3) Product Goals and Non-Goals

### Goals
- Fast and reliable appointment discovery and booking
- Correct scheduling with no slot conflicts
- Clear communication (reminders, updates, instructions)
- Secure handling of patient medical data
- Operational support for clinics and providers at scale

### Non-Goals (V1)
- Full hospital information system replacement
- Advanced medical record authoring workflow
- In-depth insurance claim adjudication engine

---

## 4) High-Level Architecture

### Core Services
1. **API Gateway**
   - Auth enforcement, routing, throttling, WAF, request tracing
2. **Identity and Access Service**
   - Authentication (password/OAuth), MFA, role-based access control
3. **Patient Profile Service**
   - Demographics, contact details, communication preferences, consent flags
4. **Doctor/Provider Service**
   - Doctor profiles, specialty, licenses, clinic affiliations
5. **Clinic Service**
   - Clinic locations, operating hours, room/resource metadata
6. **Search and Discovery Service**
   - Search doctors by specialty, location, language, insurance, rating
7. **Availability Service (critical)**
   - Doctor schedule templates, exceptions, slot generation, slot locks
8. **Appointment Service (critical)**
   - Booking, reschedule, cancellation, lifecycle state machine
9. **Telehealth Service**
   - Video session orchestration, secure meeting links, session audit events
10. **Notification Service**
    - SMS/email/push reminders and transactional updates
11. **Payment and Billing Service**
    - Consultation fee, refunds, payment provider integration
12. **Insurance Verification Service (optional integration)**
    - Eligibility checks and pre-authorization status hooks
13. **Document Service**
    - Prescriptions, lab requests, attachments (encrypted object storage)
14. **Audit and Compliance Service (critical)**
    - Immutable audit trails for access to sensitive records
15. **Admin/Ops Service**
    - Support tooling, disputes, manual override flows
16. **Analytics Platform**
    - Event ingestion, dashboards, operations insights

### Data and Infra Components
- **OLTP DB** (PostgreSQL/MySQL) for transactions
- **Redis** for caching, session/token storage, distributed locks
- **Message broker** (Kafka/PubSub/SQS+SNS) for async workflows
- **Search index** (OpenSearch/Elasticsearch) for doctor discovery
- **Object storage** for documents/media
- **Data warehouse** for BI and reporting

---

## 5) Core Domain Model

- `Patient(patient_id, name, dob, gender, contact, consent_flags, created_at)`
- `Doctor(doctor_id, name, specialty, license_id, years_exp, status)`
- `Clinic(clinic_id, name, address, timezone, contact)`
- `DoctorClinicMap(doctor_id, clinic_id, consultation_modes, active)`
- `ScheduleTemplate(template_id, doctor_id, clinic_id, weekday, start_time, end_time, slot_interval)`
- `ScheduleException(exception_id, doctor_id, clinic_id, start_at, end_at, reason, action)`
- `Appointment(appointment_id, patient_id, doctor_id, clinic_id, mode, start_at, end_at, status, created_at)`
- `AppointmentEvent(event_id, appointment_id, prev_state, new_state, actor, ts, metadata)`
- `SlotHold(hold_id, doctor_id, clinic_id, slot_start, slot_end, expires_at, patient_id)`
- `Payment(payment_id, appointment_id, amount, currency, status, provider_ref)`
- `InsuranceEligibility(check_id, patient_id, payer_id, appointment_id, status, checked_at)`
- `Notification(notification_id, user_id, channel, template, status, sent_at)`
- `AuditLog(log_id, actor_id, action, entity, entity_id, ts, metadata)`

Notes:
- `Appointment` write path and slot reservation are transactionally consistent.
- `SlotHold` has short TTL to avoid race conditions and abandoned checkout.

---

## 6) Scheduling and Double-Booking Prevention

### Booking Strategy
1. Patient selects doctor + date + slot.
2. Platform creates `SlotHold` with short TTL (e.g., 2-5 minutes).
3. On confirmation/payment, `Appointment` is committed and hold is consumed.
4. If hold expires, slot is released automatically.

### Data Consistency Mechanisms
- Unique constraint on `(doctor_id, clinic_id, slot_start, slot_end)` for active appointments.
- Optimistic concurrency control with version checks for rescheduling.
- Distributed lock (Redis) + DB transaction for high-contention slots.
- Idempotency keys on booking/reschedule APIs.

---

## 7) Appointment State Machine

Typical states:
`REQUESTED -> HELD -> CONFIRMED -> REMINDER_SENT -> CHECKED_IN -> IN_CONSULTATION -> COMPLETED`

Alternate/terminal states:
- `CANCELED_BY_PATIENT`
- `CANCELED_BY_PROVIDER`
- `NO_SHOW`
- `RESCHEDULED`
- `PAYMENT_FAILED`
- `REFUNDED` (financial dimension may be tracked separately)

Rules:
- Only valid transitions allowed.
- Every transition logged in `AppointmentEvent`.
- State change events drive notifications and downstream workflows.

---

## 8) Critical Flows

### A) Doctor Search and Discovery
1. Patient queries by location/specialty/insurance.
2. Search Service returns ranked doctors/clinics.
3. Availability snapshot joined from cache/indexed view.
4. User selects slot and proceeds to booking.

### B) Book Appointment
1. Create slot hold.
2. Validate patient profile/consent requirements.
3. Optional insurance eligibility pre-check.
4. Optional payment pre-auth (if required).
5. Confirm appointment and emit `appointment.confirmed`.
6. Send confirmation notification.

### C) Reschedule/Cancel
1. Validate policy window and actor authorization.
2. Release old slot and acquire new slot atomically (reschedule).
3. Update appointment state and payment/refund policy as needed.
4. Trigger notifications for patient + provider.

### D) Teleconsultation
1. Create secure video session token/link per appointment.
2. Enforce join rules (time window, authenticated participants).
3. Persist session events (join/leave/disconnect).
4. Mark consultation complete and trigger summary workflow.

---

## 9) API Design (Representative)

### Patient APIs
- `GET /v1/doctors?specialty=&lat=&lon=&insurance=&language=`
- `GET /v1/doctors/{id}/availability?date=`
- `POST /v1/appointments/holds`
- `POST /v1/appointments`
- `PATCH /v1/appointments/{id}/reschedule`
- `POST /v1/appointments/{id}/cancel`
- `GET /v1/appointments/{id}`
- `GET /v1/me/appointments`

### Doctor/Clinic APIs
- `POST /v1/doctors/{id}/schedule/templates`
- `POST /v1/doctors/{id}/schedule/exceptions`
- `GET /v1/provider/appointments?date=`
- `POST /v1/provider/appointments/{id}/check-in`
- `POST /v1/provider/appointments/{id}/complete`

### Telehealth APIs
- `POST /v1/telehealth/sessions`
- `GET /v1/telehealth/sessions/{appointmentId}/token`

### Internal/Event APIs
- `appointment.held`, `appointment.confirmed`, `appointment.canceled`
- `slot.released`, `notification.requested`, `payment.succeeded`, `payment.failed`

---

## 10) Scalability Strategy

### Read Scaling
- Cache frequently accessed doctor profiles and availability summaries
- Search index optimized for geo + specialty filters
- Read replicas for non-transactional query paths
- CDN for static assets and public profile content

### Write Scaling
- Partition appointment tables by clinic/city and date ranges
- Use async event-driven workers for reminders, analytics, and document tasks
- Backpressure controls on high-demand slot windows
- Queue-based retry + dead-letter for failed async jobs

### Peak Traffic Handling
- Autoscale API/worker pods by CPU, RPS, queue lag
- Prioritize booking APIs over low-priority endpoints under load
- Gracefully degrade recommendation/ranking features if needed

---

## 11) Reliability and Fault Tolerance

- Multi-AZ deployment for critical services and DB
- Transaction retries for transient lock/contention failures
- Circuit breakers for external integrations (video, insurance, payment)
- Timeout and retry budgets with exponential backoff + jitter
- Outbox pattern for reliable event publication from booking transactions
- Periodic reconciliation jobs for external provider state mismatches

Recovery assumptions:
- **RPO** <= 5 minutes
- **RTO** <= 30 minutes for tier-1 booking components

---

## 12) Security, Privacy, and Compliance

- Strong RBAC/ABAC (patient, doctor, clinic staff, admin)
- MFA for provider/admin accounts
- Encryption in transit (TLS) and at rest (KMS-managed keys)
- Field-level encryption for sensitive health data
- Strict audit trail for record access/modification
- Principle of least privilege for service-to-service access
- Signed URLs and short TTL access for medical documents
- Data retention and deletion policies aligned to regulation
- Consent management and purpose-based access controls

---

## 13) Observability and Operations

### Technical Metrics
- API latency (p50/p95/p99), error rates, saturation
- DB lock contention, deadlock rates, replication lag
- Queue lag, consumer throughput, DLQ growth

### Business and Clinical Ops Metrics
- Booking conversion rate
- Slot utilization rate
- Cancellation/no-show rates
- Reschedule turnaround time
- Teleconsultation success rate (join and completion)
- Reminder delivery success rate

### Operational Runbooks
- Provider schedule sync failures
- Booking contention spikes for popular doctors
- Telehealth provider outage fallback
- Payment webhook delay/replay handling

---

## 14) Integration Strategy

### EHR/EMR Integration (Optional)
- Use integration adapter layer per provider standard (FHIR/HL7 where possible)
- Async sync with retry and idempotency guarantees
- Reconciliation dashboard for failed sync events

### Insurance Integration (Optional)
- Real-time eligibility check during booking
- Cache short-lived eligibility responses with explicit expiry
- Fallback workflows if payer endpoints are degraded

### Calendar Sync (Optional)
- Two-way sync for doctor external calendars with conflict safeguards
- External events treated as schedule exceptions, not direct appointment writes

---

## 15) Capacity Planning (Initial)

Assume peak 12K RPS with 85-90% reads:
- API tier autoscaling to ~40-90 instances (size dependent)
- Redis cluster sized for hot keys:
  - doctor profile snapshots
  - day-level availability grids
  - active slot holds
- OLTP:
  - Primary optimized for booking writes
  - 1-2 replicas for read-heavy endpoints
- Worker pool autoscaled by queue lag/reminder volume

Load tests:
- Morning booking spike by city
- Flash demand for top specialists
- Payment and telehealth provider degraded mode
- Multi-hour reminder campaign burst

---

## 16) Phased Delivery Plan

### Phase 1 (MVP)
- Patient/doctor onboarding
- Search + availability
- In-person booking/reschedule/cancel
- Reminder notifications
- Basic payments (optional by clinic policy)

### Phase 2
- Teleconsultation
- Insurance eligibility integration
- Advanced clinic workflows (waitlist, check-in kiosk, staff roles)
- Provider analytics dashboards

### Phase 3
- Multi-country support (timezone + compliance partitioning)
- Deeper EHR interoperability
- AI-assisted scheduling recommendations and no-show prediction

---

## 17) Risks and Mitigations

1. **Double booking under race conditions**
   - Mitigation: hold+commit model, unique constraints, transactional writes
2. **No-show rates impacting utilization**
   - Mitigation: smart reminders, waitlist auto-fill, predictive overbooking policies (carefully governed)
3. **External dependency instability (video/insurance/payment)**
   - Mitigation: circuit breakers, retries, graceful degradation paths
4. **Regulatory non-compliance risk**
   - Mitigation: compliance-by-design, immutable audits, periodic policy reviews
5. **Operational burden from premature microservice split**
   - Mitigation: evolve from modular architecture with clear domain boundaries

---

## 18) Open Questions

1. Is telehealth mandatory in MVP or post-MVP?
2. What are cancellation/refund policies by specialty and clinic type?
3. Are insurance checks blocking or advisory during booking?
4. Is provider schedule source-of-truth internal, external calendar, or EHR?
5. Which regulatory framework(s) must be met at launch (HIPAA/GDPR/local law)?
6. Are walk-in queue management and waitlist features required initially?

