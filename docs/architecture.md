# Proposed contract architecture

No services or infrastructure are implemented. Review decisions.md before relying
on these drafts. README remains the original project proposal.

Order → Inventory reserves stock; Order outbox → broker → Worker → Payment;
Worker → Order reports generation-specific outcomes. Telemetry → Control evidence
→ Analysis graph/diagnosis → Control approval/execution → fixed Payment/Order
controls → independent business verification. Provider outage cannot block ordering.
Graph represents observed spans and typed relationships, including explicit gaps.

Proposed PostgreSQL ownership/constraints (documentation only, no migrations):

| Owner | Tables and constraints |
| --- | --- |
| Order | orders: UUID PK, unique client key/payload hash, state/generation/version; outbox_events: eventId PK atomically written with order; order_outcomes: outcomeId unique; recovery_attempts: attemptId unique |
| Inventory | stock: nonnegative quantity; reservations: unique (orderId,generation), quantity/state/version, atomic stock mutation |
| Payment | payments: unique orderId business effect, payload hash, durable status/paymentId |
| Worker | processing_attempts: unique (eventId,attempt), resumable processing/retry/DLQ state |
| Control | incidents: one active correlation key; incident_events: append-only; evidence_snapshots: immutable; diagnoses: versioned; recovery_actions/action_events: unique request key, principal, version, lease/checkpoints, verification |

Separate service databases/users, no direct cross-service table access. Analysis is
initially stateless; Control stores snapshots/results. Backups, retention, gateway,
credentials, TLS, hosting and telemetry versions remain undecided. No secrets belong
in evidence, fixtures or logs.
