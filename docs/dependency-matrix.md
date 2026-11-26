# Proposed interface ownership and dependencies

The user confirmed they are M1 and approved their own contract drafts; see
[the approval record](decisions.md#member-1-approval). Other member assignments,
cross-service acceptance and shared configuration remain pending. No approvals
from M2–M4 have been recorded.

| Lead | Supplies | Consumers / independent starting point |
| --- | --- | --- |
| M1 | Order/event/trace, graph/analysis contracts | M2 uses order-event and callback schemas; M3/M4 use diagnosis/graph examples |
| M2 | Inventory/Payment/Worker contracts and broker proposal | M1 mocks reserve/payment queries; M3 mocks fault controls |
| M3 | Incident/evidence/action/approval contracts | M1 uses evidence snapshot; M4 uses recovery-action fixture |
| M4 | Proposed routing/auth/runtime agreement | Everyone uses configurable service URLs; no host assumed |

| Service name | Proposed local port | Configuration name |
| --- | --- | --- |
| order-service | 8081 | ORDER_BASE_URL |
| inventory-service | 8082 | INVENTORY_BASE_URL |
| payment-service | 8083 | PAYMENT_BASE_URL |
| worker-service | 8084 | WORKER_BASE_URL |
| analysis-service | 8001 | ANALYSIS_BASE_URL |
| control-service | 8002 | CONTROL_BASE_URL |
| gateway | 8080 | APP_BASE_URL |

Ports are unallocated proposals. Candidate gateway prefixes /api/orders,
/api/control, /api/analysis are stripped before service-relative paths; e.g.
/api/orders/orders maps to Order /orders. Team should confirm or simplify this
mapping before UI work. Internal routes must not become public through prefixing.
No environment file or infrastructure is created by these contracts.

Review handoff: each provider and consumer independently constructs a valid request
and response; agree ambiguity, replay, stock rejection, stale outcomes and approval
races. Fixtures enable independent development but do not prove integration.

Run offline validation after installing dependencies (Python 3.11+):

```sh
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pytest tests/contracts -q
git diff --check
```

Full tracestate grammar, runtime state transitions, atomicity, retries, auth and
real telemetry are later implementation/integration checks; schema tests cannot
prove them. Required team decisions/manual handoffs are still pending.

requirements-dev.txt pins the resolved validator environment, including transitive
dependencies, tested with Python 3.11.16. No application runtime selection follows
from those pins. examples/http-exchanges.json supplies a synthetic request/response
for every non-health operation; named examples provide a linked incident journey.
