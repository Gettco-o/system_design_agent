# System Design: Food Delivery App (Uber Eats–Like)

## 1) Overview

This document designs a robust, scalable system for a food delivery platform similar to Uber Eats.  
The platform supports three primary personas:
- **Customers** placing orders
- **Restaurants** managing menus and order fulfillment
- **Delivery Partners (couriers)** accepting and delivering orders

Because requirements are ambiguous, assumptions are explicitly stated.

---

## 2) Assumptions (Explicit)

1. **Regions**: Launch in one country with multiple cities, expand globally later.
2. **Scale target (Year 1)**:
   - 2M registered customers
   - 100K daily active users
   - Peak 15K-30K requests/second (read-heavy)
   - 2K-5K concurrent active deliveries during meal peaks
3. **Ordering model**:
   - On-demand (ASAP) delivery is primary.
   - Scheduled delivery supported in V2.
4. **Payment model**:
   - Card/wallet payments through third-party PSP.
   - Cash on delivery optional and region-configurable.
5. **Logistics model**:
   - Platform-managed courier marketplace (independent delivery partners).
   - Restaurant self-delivery may be supported as an optional mode.
6. **SLA goals**:
   - Core order placement availability: 99.95%
   - Dispatch/tracking availability: 99.9%
7. **Consistency requirements**:
   - Order/payment state transitions require strong consistency.
   - Search, restaurant ranking, and analytics can be eventually consistent.
8. **Compliance/Security**:
   - PCI scope minimized through tokenized payments.
   - Regional privacy regulations (GDPR-like) apply.
9. **Platforms**:
   - Customer app: iOS, Android, Web
   - Courier app: iOS/Android
   - Restaurant console: Web + tablet app

---

## 3) Product Goals and Non-Goals

### Goals
- Fast, reliable order placement and checkout
- Accurate ETA and real-time order tracking
- Efficient courier dispatch and route optimization
- High availability during meal-time spikes
- Operational transparency for customers, restaurants, and couriers

### Non-Goals (V1)
- Full grocery marketplace with inventory synchronization from POS at SKU-level depth
- Cross-border delivery operations
- Fully autonomous dynamic pricing experimentation platform

---

## 4) High-Level Architecture

### Client Applications
- Customer App (browse, cart, checkout, live tracking)
- Courier App (online/offline status, offers, navigation, proof of delivery)
- Restaurant App/Console (menu, prep status, order queue)
- Admin Ops Dashboard (support, fraud, live incident controls)

### Edge and Core
1. **API Gateway**
   - Auth, rate limiting, routing, WAF protection, API versioning
2. **Identity Service**
   - Login/signup, token issuance, role-based access (customer/courier/restaurant/admin)
3. **User Profile Service**
   - Addresses, preferences, payment method references, loyalty metadata
4. **Restaurant Service**
   - Store metadata, operating hours, serviceability zones, availability
5. **Menu Service**
   - Categories, items, pricing, modifiers, availability windows
6. **Search & Discovery Service**
   - Text/geospatial search, ranking, cuisine filters, sponsored placement hooks
7. **Cart Service**
   - Cart state, pricing snapshot, coupon application
8. **Pricing Service**
   - Taxes, delivery fee, surge/service fee, promotions, final payable amount
9. **Order Service (critical)**
   - Order lifecycle state machine and idempotent order creation
10. **Payment Service (critical)**
    - PSP integration, authorization/capture, webhook processing, refunds
11. **Dispatch Service (critical)**
    - Courier matching, batching logic, reassignment on timeouts
12. **Courier Location Service**
    - Real-time GPS ingestion, location smoothing, availability state
13. **Tracking Service**
    - Real-time status updates and map feed for customers/restaurant/support
14. **Notification Service**
    - Push, SMS, email for order milestones
15. **Fraud & Risk Service**
    - Velocity checks, account/link analysis, abuse prevention
16. **Support/Operations Service**
    - Cancellations, compensations, manual intervention controls
17. **Ratings & Reviews Service**
    - Post-delivery ratings and issue tagging
18. **Analytics & Data Platform**
    - Event ingestion, streaming metrics, BI warehouse, experimentation telemetry

### Data and Infrastructure
- **OLTP database** (PostgreSQL/MySQL) for orders/payments/core entities
- **Redis** for hot reads, sessions, rate limiting, and short-lived workflow state
- **Message broker** (Kafka/PubSub/SQS+SNS) for async workflow orchestration
- **Search index** (OpenSearch/Elasticsearch) for discovery
- **Time-series/geospatial store** for high-frequency courier locations
- **Object storage** for receipts/proof-of-delivery media
- **Data warehouse** for reporting/ML features

---

## 5) Core Domain Models

- `Customer(customer_id, name, phone, email, default_address_id, status, created_at)`
- `Restaurant(restaurant_id, name, zone_id, open_status, rating, prep_time_baseline)`
- `MenuItem(item_id, restaurant_id, name, base_price, availability, modifier_schema)`
- `Cart(cart_id, customer_id, restaurant_id, items_json, quote_id, updated_at)`
- `Order(order_id, customer_id, restaurant_id, courier_id, status, totals, address, created_at)`
- `OrderEvent(event_id, order_id, prev_state, new_state, actor, ts, metadata)`
- `Payment(payment_id, order_id, psp_ref, amount, status, captured_at)`
- `Courier(courier_id, vehicle_type, online_status, zone_id, rating)`
- `CourierLocation(courier_id, lat, lon, speed, heading, ts)`
- `DispatchOffer(offer_id, order_id, courier_id, status, expires_at)`
- `Promotion(promo_id, type, constraints, budget, active_window)`
- `AuditLog(log_id, actor_id, action, entity, entity_id, timestamp, metadata)`

Key constraints:
- `order_id` globally unique and immutable.
- Order status transitions validated via state machine.
- Payment and order writes executed atomically where required.

---

## 6) Order State Machine

Example states:
`CREATED -> PAYMENT_PENDING -> CONFIRMED -> RESTAURANT_ACCEPTED -> PREPARING -> READY_FOR_PICKUP -> COURIER_ASSIGNED -> PICKED_UP -> EN_ROUTE -> DELIVERED`

Terminal/exception states:
- `PAYMENT_FAILED`
- `RESTAURANT_REJECTED`
- `CANCELED_BY_USER`
- `CANCELED_BY_SYSTEM`
- `DELIVERY_FAILED`
- `REFUNDED` (financial state may be orthogonal)

Rules:
- Each transition is idempotent and version-checked.
- Invalid transitions are rejected and audited.
- Customer-visible timeline derived from order events.

---

## 7) Critical Flows

### A) Browse and Discover
1. Customer sends location + filters.
2. Search Service queries geospatial index for serviceable restaurants.
3. Ranking combines relevance, ETA, fee, rating, conversion signals.
4. Results cached aggressively with short TTL.

### B) Checkout and Order Placement
1. Cart Service validates menu availability and rebuilds price quote.
2. Pricing Service computes tax/fees/promotions and returns signed quote.
3. Order Service creates order with idempotency key.
4. Payment Service performs auth/capture via PSP.
5. On success, order transitions to `CONFIRMED`; restaurant notified.
6. On failure, order transitions to `PAYMENT_FAILED` with retry options.

### C) Restaurant Fulfillment
1. Restaurant receives order and accepts/rejects.
2. Prep milestone updates emitted (`PREPARING`, `READY_FOR_PICKUP`).
3. Dispatch Service aligns courier assignment with prep ETA.

### D) Courier Dispatch and Delivery
1. Dispatch Service selects courier candidates by distance, ETA, reliability score.
2. Offer sent with timeout; fallback to next candidates on rejection/expiry.
3. Courier accepts, navigates to restaurant, then to customer.
4. Location updates stream to Tracking Service.
5. Delivery completion triggers payout accounting and feedback prompt.

### E) Cancellations and Refunds
1. Cancellation request validated against policy window and current state.
2. Compensation/refund amount computed by policy engine.
3. Payment Service executes refund (full/partial), writes ledger event.
4. All parties notified with reason and receipt.

---

## 8) API Design (Representative)

### Customer APIs
- `GET /v1/restaurants?lat=&lon=&filters=`
- `GET /v1/restaurants/{id}/menu`
- `POST /v1/carts`
- `POST /v1/carts/{id}/quote`
- `POST /v1/orders` (idempotent via `Idempotency-Key`)
- `GET /v1/orders/{id}`
- `POST /v1/orders/{id}/cancel`
- `GET /v1/orders/{id}/tracking`

### Restaurant APIs
- `POST /v1/restaurant/orders/{id}/accept`
- `POST /v1/restaurant/orders/{id}/reject`
- `POST /v1/restaurant/orders/{id}/status`

### Courier APIs
- `POST /v1/courier/status` (online/offline)
- `POST /v1/courier/location`
- `POST /v1/courier/offers/{id}/accept`
- `POST /v1/courier/offers/{id}/reject`
- `POST /v1/courier/orders/{id}/picked-up`
- `POST /v1/courier/orders/{id}/delivered`

### Webhooks/Internal Events
- `payment.authorized`, `payment.failed`, `payment.refunded`
- `order.created`, `order.confirmed`, `order.canceled`
- `dispatch.offer.created`, `dispatch.offer.expired`, `dispatch.assigned`
- `tracking.location.updated`

---

## 9) Scalability Strategy

### Read Path
- CDN for static content and images
- Redis for restaurant summaries and frequently accessed menus
- Search index for low-latency discovery queries
- Materialized views for customer order history

### Write Path
- Partition orders by city/zone and time (logical sharding path)
- Async processing for non-critical side effects (notifications, analytics, emails)
- Event-driven workflow with retries and DLQ
- Idempotent consumers and dedupe keys

### Peak Handling
- Meal-time autoscaling by:
  - API CPU/RPS
  - Broker lag
  - Dispatch queue depth
  - Active websocket connection count
- Graceful degradation:
  - Temporarily limit far-distance deliveries
  - Disable low-priority recommendations
  - Increase quote TTL validation strictness

---

## 10) Dispatch and ETA Strategy

### Dispatch Inputs
- Courier distance/time to pickup
- Restaurant prep ETA
- Historical courier acceptance probability
- Courier reliability and cancellation history
- Delivery zone boundaries and traffic estimates

### Matching Approach (phased)
1. **V1**: Rule-based nearest-eligible with heuristic scoring
2. **V2**: ML-assisted ranking for acceptance probability and SLA adherence
3. **V3**: Batched dispatch optimization under high load

### ETA Computation
- ETA = prep estimate + pickup travel + drop-off travel + buffer
- Continuously re-estimated using live traffic + courier telemetry
- Expose confidence interval to support operations and (optionally) users

---

## 11) Real-Time Tracking Architecture

- Courier app publishes location every 2-5 seconds when active.
- Ingestion endpoint writes to streaming bus.
- Tracking Service updates latest state store and pushes updates over WebSocket/SSE.
- Customer app subscribes to order tracking channel.
- Backpressure controls:
  - Dynamic sampling in low-priority screens
  - Coalescing updates at server edge
  - Fallback to periodic polling when websocket unavailable

---

## 12) Reliability and Resilience

- Multi-AZ deployment for all critical services
- Blue/green or canary releases for order/payment/dispatch services
- Circuit breakers to PSP/maps/notification providers
- Timeout budgets and bounded retries
- Dead-letter queues with replay tooling
- Outbox/inbox pattern for reliable event publication and consumption
- Data backups and PITR for transactional stores

Target recovery assumptions:
- **RPO** <= 5 minutes
- **RTO** <= 30 minutes for tier-1 services

---

## 13) Security, Privacy, and Compliance

- OAuth2/OIDC-based authentication, short-lived access tokens
- Role-based access control per persona and tenant/store boundaries
- End-to-end TLS and encryption at rest via KMS
- Tokenized payment methods; no raw PAN storage
- PII minimization and redaction in logs
- Device risk and account takeover protection (MFA for sensitive actions)
- Immutable audit logs for admin/support actions
- Data subject rights workflows (export/delete where legally applicable)

---

## 14) Observability and SRE

### Golden Signals
- Latency, traffic, error rate, saturation by service and city

### Business-Critical KPIs
- Order conversion rate
- Checkout failure rate
- Dispatch time to assignment
- On-time delivery %
- Cancellation rate by stage
- Payment success/refund latency

### Tooling
- Centralized logs with correlation IDs
- Distributed tracing across request + event boundaries
- SLO alerts with city-level drill-down
- Incident runbooks for:
  - PSP outage
  - Maps provider degradation
  - Dispatch queue backlog
  - Restaurant-side mass rejection spike

---

## 15) Data and Analytics Platform

- Event schema registry for stable analytics contracts
- Near-real-time stream processing for ops dashboards
- Warehouse models for cohort, retention, LTV, courier performance
- Feature store candidates:
  - ETA prediction features
  - Dispatch acceptance features
  - Fraud anomaly features

Governance:
- Ownership and SLA per dataset
- PII classification and access controls

---

## 16) Capacity Planning (Initial)

Assume peak 30K RPS:
- 85-90% read, 10-15% write
- 200K+ concurrent websocket/SSE tracking sessions during extreme peaks

Initial sizing assumptions:
- API tier: autoscale to 80-150 instances (workload dependent)
- Redis cluster: enough memory for hot menus/restaurant cards/order sessions
- OLTP primary + replicas:
  - Primary for strict order/payment writes
  - Replicas for read-heavy customer history and dashboards
- Broker throughput sized for order + location events with 2x headroom

Load tests:
- Normal lunch/dinner peaks
- 3x city-level traffic surge (sporting event)
- PSP webhook delay/replay storm
- Partial region failover test

---

## 17) Phased Delivery Plan

### Phase 1 (MVP)
- Customer browse/cart/checkout
- Restaurant accept/reject and prep updates
- Courier assignment and basic tracking
- Payments + receipts + cancellations

### Phase 2
- Scheduled orders
- Advanced dispatch scoring
- Promotions and loyalty
- Support tooling and automated compensations

### Phase 3
- Multi-region/multi-currency expansion
- ML-enhanced ETA and dynamic dispatch batching
- Deep merchant integrations (POS/menu sync)

---

## 18) Risks and Mitigations

1. **Dispatch inefficiency at peak**
   - Mitigation: zone-based throttling, batching controls, fallback heuristics
2. **ETA inaccuracies reduce trust**
   - Mitigation: frequent recalculation, confidence scoring, route telemetry feedback loop
3. **Payment disruptions**
   - Mitigation: robust retries, async reconciliation, multi-PSP strategy roadmap
4. **Fraud/abuse (coupon abuse, account farming)**
   - Mitigation: risk scoring, limits, device/link analysis, manual review
5. **Operational complexity from over-fragmented services**
   - Mitigation: start with clear bounded services and evolve with measurable bottlenecks

---

## 19) Open Questions

1. Should we support both marketplace logistics and restaurant self-delivery at launch?
2. What are the city-level SLA targets for delivery time and assignment latency?
3. Is scheduled delivery required in MVP?
4. Which payment methods and refund windows are required per region?
5. What level of POS integration is required for restaurant onboarding?
6. Is surge/dynamic delivery fee acceptable for launch markets?

