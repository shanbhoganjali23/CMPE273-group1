# Shared decisions awaiting review

Status: Member 1 contract drafts approved by the user on November 24, 2026;
cross-service agreements and technology choices remain PROPOSED. No approvals
from other members have been received. Local contract validation is distinct
from shared acceptance. All open questions below remain pending.

## Member 1 approval

The user confirmed they are Member 1 and approved their contract drafts:

- Order create/read/outcome/eligible-retry interfaces and the five order states.
- Duplicate-request protection and stable order identity for payment retries.
- Event identifiers, retry attempts, reservation generations and trace context.
- Graph format based on recorded operations, with explicit missing information.
- Provider-independent analysis input/output, evidence references, uncertainty,
  allowlisted recommendations and explicit unavailable results.

This records Member 1's intended interfaces to build against. It does not record
acceptance by connecting service owners or authorize later implementation work.
Worker-to-Payment flow, compensation/re-reservation, replay and broker routing
still need M2 agreement; evidence/action integration needs M3 agreement;
telemetry/routing/ports/authentication need M4 agreement. Provider/model, privacy,
budget and other technology choices remain unselected. Commit, push and PR
creation have not been approved.

## Open team decisions

| ID | Proposed decision / alternatives | Confirmation needed from | Gate |
| --- | --- | --- | --- |
| OQ01 | RabbitMQ; Java 21/Spring Boot; Python 3.11/FastAPI; React/Vite; Jaeger/Loki. Exact runtime versions unselected. Defer Redis/vector retrieval versus retaining README scope. Validator-only pins are in requirements-dev.txt. | All members | Runtime implementation |
| OQ02 | Order reserves Inventory; worker calls Payment versus direct Order→Payment. Inventory rejection fails order without publishing. Ambiguous reservation is queried using same generation before compensation. | M1/M2 | Business workflow |
| OQ03 | One provider/model; no candidate selected. Agree quota, budget, evidence privacy, credentials and structured output support. | M1/user | Live model adapter/calls |
| OQ04 | Single VM/Compose candidate versus managed hosting. Provider, region, resources, budget, domain, TLS and publishing authorization unselected. | M4/user | Provisioning/deployment |
| OQ05 | Replay same failed order with fresh reservation generation versus replacement order. Reconcile unknown payment first; never release inventory on timeout alone. | M1/M2/M3 | Replay implementation |
| OQ06 | Candidate budgets and detection/verification rules in contract-protocol.md; thresholds and sizing need agreement and later measurement. | M1/M2/M3/M4 | Runtime configuration |
| OQ07 | Authenticated principal supplies approver identity. Session/OIDC/token choice, roles, internal service identity and browser read/create access unresolved. No security scheme selected in OpenAPI. | M3/M4 | Auth implementation/public exposure |
| OQ08 | Jaeger query adapter; Prometheus/Loki correlation; backend versions, retention, volumes and memory limits unresolved. | M1/M3/M4 | Telemetry integration |
| OQ09 | M1–M4 are planning labels, not named assignments. Confirm names, ports, ownership, daily integration time, demo length, LMS timezone and report rules. | Team | Shared acceptance/delivery |

The contract-authoring work and new branch were requested by the user. Member 1's
limited approval above does not resolve the open decisions. Team review must include a caller and provider
constructing examples independently, especially stock rejection, unknown payment,
replay, stale outcomes, approval races and missing context. Required decisions and
manual handoffs remain incomplete; do not mark the shared-contract milestone complete.
