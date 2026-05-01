# System Design: Digital Contributor App

## 1) Overview

This document proposes a robust, scalable architecture for a **Digital Contributor App**.  
The app enables individuals and organizations to contribute money or effort to campaigns/causes, track impact, and manage recurring contributions.

Because requirements are ambiguous, assumptions are stated explicitly.

---

## 2) Assumptions (Explicit)

1. **Primary use case**: Financial contributions (one-time + recurring) are the first-class workflow.
2. **Secondary use case**: Non-monetary contributions (volunteering, skill-based tasks) are supported but less critical in V1.
3. **Actors**:
   - Contributors (end users)
   - Campaign Owners (create/manage campaigns)
   - Admin/Moderators (compliance, fraud review, support)
4. **Geography**: Multi-region user base, but initial payment settlement in one primary currency with future expansion.
5. **Traffic profile (Year 1 target)**:
   - 1M registered users
   - 80K daily active users
   - 3K-10K peak requests/second (read heavy)
   - 200-500 payment attempts/min at peak
6. **Consistency needs**:
   - Payment ledger data must be strongly consistent.
   - Feed/timeline and analytics can be eventually consistent.
7. **Compliance**:
   - PCI scope minimized via payment processor tokenization.
   - GDPR-like data handling required (consent, deletion/export).
8. **Availability target**: 99.9% for core contribution flow.
9. **Client platforms**: iOS, Android, Web.
10. **Cloud-native deployment** on Kubernetes (or equivalent managed compute platform).

---

## 3) Product Goals and Non-Goals

### Goals
- Frictionless contribution flow (low-latency checkout and retry-safe submissions)
- Transparent impact tracking for trust
- Reliable recurring contributions with reminders and failure recovery
- Horizontal scalability for campaign spikes
- High security and anti-fraud controls

### Non-Goals (V1)
- Full social network features (complex graph ranking, long-form content)
- Real-time bidding ad platform
- Deep accounting suite for campaign owners

---

## 4) High-Level Architecture

### Core Components
1. **API Gateway**
   - Authentication, rate limiting, request routing, WAF integration
2. **Identity Service**
   - Signup/login, OAuth/social login, MFA, session/token management
3. **User Profile Service**
   - Contributor profile, preferences, notification settings
4. **Campaign Service**
   - Campaign creation, metadata, goals, status, category tags
5. **Contribution Service**
   - Contribution intent creation, idempotency, orchestration with Payment Service
6. **Payment Service**
   - Integrates with PSP (e.g., Stripe/Adyen), handles webhooks, retries, reconciliation
7. **Ledger Service**
   - Immutable financial records, settlement states, refunds/chargebacks
8. **Recurring Billing Service**
   - Subscription schedules, retry dunning, payment method updates
9. **Impact/Reporting Service**
   - Campaign progress, contribution history, donor receipts, exports
10. **Notification Service**
    - Email/push/SMS via queue-based fanout
11. **Moderation & Risk Service**
    - Rules engine, risk scores, manual review queue
12. **Search Service**
    - Campaign search/filtering via indexed store
13. **Analytics Pipeline**
    - Event ingestion, stream processing, BI warehouse

### Data/Infra Components
- **OLTP DB** (PostgreSQL or Cloud SQL) for transactional data
- **NoSQL store** (optional) for high-throughput activity feeds
- **Redis** for caching/session/rate-limit counters
- **Message broker** (Kafka/PubSub/SQS+SNS) for async workflows
- **Object storage** for media/documents
- **Search index** (OpenSearch/Elastic)
- **Data warehouse** for analytics/reporting

---

## 5) Architecture Style and Service Boundaries

Use a **modular monolith or small set of services in early phase**, then evolve to microservices by domain pressure.

Recommended domain boundaries:
- **Identity + User** (can stay together initially)
- **Campaign**
- **Contribution + Payment + Ledger** (separate sooner due to criticality)
- **Notifications**
- **Analytics**

Rationale:
- Payment and ledger workloads have strict consistency/security requirements.
- Campaign feed/search and analytics can scale independently and tolerate eventual consistency.

---

## 6) Critical Flows

### A) One-Time Contribution Flow
1. Client creates `ContributionIntent` with idempotency key.
2. Contribution Service validates campaign state and amount limits.
3. Payment Service creates PSP payment intent (tokenized method).
4. Client confirms payment via PSP SDK.
5. PSP webhook received by Payment Service (source of truth).
6. Ledger Service writes immutable transaction record (`PENDING -> SUCCEEDED/FAILED`).
7. Campaign totals updated asynchronously via events.
8. Notification sent (receipt + impact message).

### B) Recurring Contribution Flow
1. User creates recurring plan (monthly/weekly).
2. Recurring Service stores schedule + payment token ref.
3. Scheduler emits due invoices.
4. Payment attempt triggered; webhook confirms outcome.
5. On failure, dunning policy runs (retry cadence + user reminders).
6. After max retries, subscription enters `PAST_DUE` or `CANCELED`.

### C) Campaign Spike Handling
1. Read traffic served from cache + search index.
2. Write-heavy contribution paths protected by queue smoothing.
3. Auto-scaling for API workers and consumers based on lag/RPS.

---

## 7) Data Model (Core Entities)

- `User(user_id, email, auth_provider, kyc_status, created_at, deleted_at)`
- `Campaign(campaign_id, owner_id, title, goal_amount, status, start_at, end_at, currency)`
- `ContributionIntent(intent_id, user_id, campaign_id, amount, currency, idempotency_key, status, created_at)`
- `Payment(payment_id, intent_id, psp_reference, status, failure_code, processed_at)`
- `LedgerEntry(entry_id, payment_id, campaign_id, user_id, type, amount, currency, occurred_at)`
- `Subscription(subscription_id, user_id, campaign_id, interval, next_bill_at, status)`
- `Notification(notification_id, user_id, channel, template, status, sent_at)`
- `AuditLog(event_id, actor_id, action, entity, entity_id, timestamp, metadata)`

Notes:
- `LedgerEntry` is append-only.
- `idempotency_key` unique constraint per user and operation type.
- Soft delete plus data retention policies for compliance.

---

## 8) API Design (Representative)

### Public APIs
- `POST /v1/contributions/intents`
- `POST /v1/contributions/intents/{id}/confirm`
- `GET /v1/campaigns/{id}`
- `GET /v1/campaigns?query=&category=&sort=`
- `POST /v1/subscriptions`
- `PATCH /v1/subscriptions/{id}`
- `GET /v1/me/contributions`
- `GET /v1/me/receipts/{paymentId}`

### Internal/Event APIs
- `payment.succeeded`
- `payment.failed`
- `ledger.entry.created`
- `campaign.metrics.updated`
- `notification.dispatch.requested`

Principles:
- Idempotent write endpoints
- Versioned APIs
- Request tracing headers (e.g., `x-request-id`)
- Backward compatibility for mobile clients

---

## 9) Scalability Strategy

### Read Scaling
- CDN for static assets and public campaign pages
- Redis cache for campaign details and leaderboard-like stats
- Search index for campaign discovery
- Read replicas for non-critical analytical queries

### Write Scaling
- Partition high-write tables by time/campaign when needed
- Queue asynchronous side effects (notifications, metrics recompute)
- Apply backpressure and admission control during spikes
- Use idempotency + dedupe in consumers

### Data Growth Strategy
- Hot/cold storage split for events
- Archive old audit logs and raw events to object storage
- Warehouse ETL for long-term analytics

---

## 10) Reliability and Fault Tolerance

- Multi-AZ deployment for stateless services and DB
- Circuit breakers and timeouts on downstream calls
- Retry policies with exponential backoff + jitter
- Dead-letter queues for poison messages
- Webhook signature verification and replay protection
- Exactly-once effect for financial state via idempotent state transitions

Disaster recovery targets (assumed):
- **RPO**: <= 5 minutes
- **RTO**: <= 30 minutes

---

## 11) Security and Compliance

- OAuth2/OIDC + short-lived JWT access tokens
- MFA for campaign owners/admins
- Encryption in transit (TLS 1.2+) and at rest (KMS-managed keys)
- Secrets in managed vault, never in code
- Least privilege IAM per service
- PII tokenization/redaction in logs
- Admin actions recorded in immutable audit trail
- Fraud controls: velocity checks, device fingerprint signals, anomaly scoring
- Compliance workflows: DSAR export/delete, consent tracking, retention enforcement

---

## 12) Observability and Operations

- Centralized structured logging
- Metrics: RPS, p95/p99 latency, payment success ratio, queue lag, cache hit rate
- Distributed tracing across gateway/services/DB
- SLOs + alerting:
  - Contribution success rate
  - Payment webhook processing delay
  - Ledger write failure rate
- Runbooks for:
  - PSP outage
  - Queue backlog growth
  - Elevated payment failures by issuer/bin/country

---

## 13) Suggested Tech Stack (One Viable Option)

- Backend: TypeScript (Node.js/NestJS) or Go
- API: REST + async events (Kafka/PubSub)
- DB: PostgreSQL (transactional), Redis (cache), OpenSearch (search)
- Infra: Kubernetes, managed ingress, autoscaling
- Data: BigQuery/Snowflake for analytics
- Mobile/Web: React Native + React web (or native apps)

---

## 14) Capacity Planning (Initial)

Assume peak 10K RPS total, 90% reads, 10% writes:
- API stateless tier: horizontally scale to ~30-60 pods (size-dependent)
- Redis cluster sized for hot campaign/user keys with >90% hit rate target
- Postgres:
  - Primary tuned for write path (payments/ledger)
  - 1-2 read replicas for read-heavy endpoints
- Queue consumers autoscale on lag and processing latency

Perform load testing for:
- Normal peak
- 5x campaign burst
- PSP webhook replay storm

---

## 15) Phased Delivery Plan

### Phase 1 (MVP)
- Identity, campaign creation/listing, one-time contributions, receipts
- Basic moderation and anti-fraud rules
- Dashboard with campaign totals

### Phase 2
- Recurring contributions + dunning
- Enhanced analytics and segmentation
- Search relevance improvements

### Phase 3
- Multi-currency and regional payment expansion
- Advanced trust signals and risk models
- Partner APIs/webhooks for campaign ecosystems

---

## 16) Risks and Mitigations

1. **Payment provider downtime**
   - Mitigation: queued retries, graceful degradation, multi-PSP roadmap
2. **Fraud and abuse**
   - Mitigation: risk scoring, velocity limits, manual review workflows
3. **Inconsistent campaign totals under high load**
   - Mitigation: ledger as source of truth, async projection repair jobs
4. **Regulatory expansion complexity**
   - Mitigation: compliance-by-design, region-aware policy engine
5. **Operational complexity from premature microservices**
   - Mitigation: start modular, split only by clear scaling/ownership need

---

## 17) Open Questions

1. What exact definition of "contributor" is required (financial only vs financial + effort/time)?
2. Do campaigns require legal/KYC verification before accepting funds?
3. Is marketplace-style payout needed (platform holds funds then disburses)?
4. What regions/currencies must be supported at launch?
5. What trust/reporting requirements matter most for users (real-time impact vs periodic reports)?

