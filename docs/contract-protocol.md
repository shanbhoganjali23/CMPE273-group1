# Proposed shared wire protocol

Version 0.1.0; all semantics await team review (OQ01–OQ09). OpenAPI 3.1 files use
JSON syntax, which is valid YAML. JSON Schemas use draft 2020-12. No running
services, endpoints or observed results are implied. All examples are synthetic.
Unknown fields are rejected. Changes require provider/consumer review; incompatible
changes need a new major contract version. Event schemaVersion is currently 1.

## Identifiers and keys

Business entity, event, outcome, incident, evidence, diagnosis, request and recovery
execution IDs are UUIDs. Catalogue actionId is the fixed allowlisted string;
recoveryActionId is a UUID execution ID, also passed to Order as recoveryAttemptId.
Trace IDs are 32 lowercase nonzero hex digits; span IDs are 16. Timestamps are UTC
RFC3339 with Z. Evidence IDs identify immutable snapshots, never generated claims.
Graph node ID is traceId:spanId; edge ID is UUID. Endpoints are service relative.

Every HTTP mutation requires Idempotency-Key (1–128 characters), scoped by caller,
operation and resource. Same key/canonical payload returns original status/body;
changed payload returns 409. Proposed retention is the demo lifetime, with durable
records and no expiry while work is unresolved. Outcome additionally deduplicates
outcomeId. Payment business uniqueness is orderId across all event IDs, deliveries,
recovery executions and generations; changing item/quantity for it is 409.
Reservation uniqueness is (orderId,reservationGeneration); release affects only
that generation. Query requires reservationGeneration. Client retries reuse keys.
An ambiguous reserve/payment/control timeout does not prove absence of effects.

## Workflow and compensation proposal

Orders: PENDING → PROCESSING → COMPLETED | FAILED | REVIEW_REQUIRED.
Inventory rejection: PENDING → FAILED, no event. Pending reservation ambiguity
remains pending for same-key reconciliation. Definitive payment failure releases
that generation idempotently before FAILED. Release ambiguity requires reconciliation.
Unknown payment becomes REVIEW_REQUIRED without releasing stock or recharging.
COMPLETED is terminal. Review may reconcile to COMPLETED or a definitive FAILED.

Approved replay checks payment state and eligibility. A released reservation must
be reacquired with generation+1 before PROCESSING and transactional outbox insertion.
Failed reacquisition leaves FAILED and publishes nothing. Initial generation is 0;
newly reserved generations are monotonic and never reused for different payloads.
Retries within a generation increment attempt 1–3. An approved new generation
starts attempt 1 with a new eventId. An eventId identifies one generation's logical
work, remaining stable across retry publications/redelivery. Delivery redelivery
does not itself increment business attempt. Worker deduplication is (eventId,attempt)
with recoverable in-progress records. Stale-generation outcomes return 409 before
any stock/state mutation; identical previously accepted outcome returns its stored
result. Current-generation illegal transitions return 409. Outbox publishing and
broker acknowledgement may duplicate delivery; no exactly-once delivery claim.

## Messaging and trace proposal

RabbitMQ exchange agentmesh.orders; routing key order.created; work queue
orders.process, delayed retry queue orders.retry and dead-letter queue orders.dlq.
Proposed retry routing keys order.retry and order.dead, with durable queues,
persistent payloads, confirms and explicit acknowledgements. Retry queue routes
back to order.created after proposed delays 1 s then 5 s. Preserve eventId and
reservationGeneration; increment attempt only for scheduled business retry.

Producer injects valid version-00 W3C traceparent in context, optional tracestate
(up to 32 W3C members, no secrets). HTTP uses traceparent/tracestate headers.
The schemas enforce the supported traceparent subset and tracestate size; full
tracestate grammar validation belongs to the OTel propagator. Stored outbox context
is restored; publish span context is injected, consumer span extracts remote parent.
Each delivery has a new span. Missing/invalid context violates producer schema;
consumer must handle it safely, record gap, start a new trace, never invent parentage.
Invalid business envelopes are quarantined/dead-lettered with bounded handling.
Partial graph may use typed MESSAGE_CORRELATION edges across traces with eventId,
but those edges do not establish a parent-child relationship. Only actual spans
become nodes; timestamps alone do not establish causality.

## Diagnosis, access and recovery proposal

AnalysisRequest incident/order IDs must match evidence; evidence record IDs are
unique; traceIds include graph.traceId. AVAILABLE output evidenceIds must reference
available input evidence and recommendation must be in allowedActionIds/catalogue
and target the exact input order. Output incidentId and graphCompleteness must match
input. UNAVAILABLE contains no fabricated cause/recommendation. HTTP 200 may carry
stored unavailable diagnosis; failed immediate provider calls use standard
502 invalid output, 503 unavailable, 504 deadline. A timeout can leave mutations
unknown. All API errors use code/message/retryable/correlationId without secrets.
400 malformed input, 401 unauthenticated, 403 unauthorized, 404 absent,
409 key/state/version/generation conflict, 422 semantically invalid evidence/input.

Actions: PENDING_APPROVAL → APPROVED | REJECTED; APPROVED → EXECUTING → VERIFYING
→ SUCCEEDED | FAILED | REVIEW_REQUIRED. Identity comes from authenticated principal,
never user-supplied approver fields. expectedVersion guards approval races; matching
idempotent duplicate returns stored result before version checks. Rejection never
resolves an incident. Catalogue steps are fixed operations, not shell commands.
SUCCEEDED requires completed order, unique successful payment and correct stock.
Incident: OPEN → ANALYZING → AWAITING_APPROVAL → RECOVERING → VERIFYING → RESOLVED;
failures/rejections keep it unresolved with timeline entries. Fault controls are
allowlisted, expire after at most 300 s and reset to none on restart; latency ≤5 s.
Approval/fault/internal routes require authentication and authorization; exact
mechanism and browser permissions are unresolved. Never expose drafts as anonymous
APIs based on their absent OpenAPI security scheme. UUIDs do not grant access.

## Candidate budgets and review gates

HTTP connect/read 2/5 s; at most three business attempts per generation; model 20 s
per attempt, two attempts within 45 s total; graph poll 10 s; verification poll up
to 60 s. Graph ≤200 nodes/400 edges, evidence ≤100 records, ≤10 trace IDs. Strings
≤2048 characters unless constrained further. Proposed detection: five payment
errors in 30 s, correlated by service/fault type, with immutable target order evidence.
These values are proposals, not measured guarantees. Resource sizing, telemetry
retention and precise retryable error-code catalogue still require review.
