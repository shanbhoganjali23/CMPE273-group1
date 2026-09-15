# 1. Proposed Project Idea: AgentMesh

## Distributed AI Incident Detection and Response Platform

## Project Description

AgentMesh is a distributed AI-assisted platform that monitors multiple independent services, detects failures, analyzes their probable causes, and recommends safe recovery actions.

The project will use a small distributed application consisting of services such as an Order Service, Inventory Service, and Payment Service. These services will communicate over the network and through a message broker.

When a failure occurs in one of the services, AgentMesh will collect relevant logs, metrics, and request traces. An AI agent will analyze this information and explain the likely root cause of the incident. A workflow-based response system will then perform controlled recovery actions such as retrying a request, restarting an unhealthy service, activating a circuit breaker, or reprocessing a failed message.

## Problem Statement

In distributed systems, a failure in one service can affect other services. It can be difficult to determine whether the problem is caused by a crashed service, slow network communication, database failure, faulty deployment, or message-processing issue.

Usually, developers must manually inspect logs and monitoring information to understand the problem. AgentMesh aims to reduce this effort by automatically detecting incidents, analyzing the available system information, and suggesting appropriate recovery actions.

## Proposed Solution

The system will follow this general process:

```text
Detect failure
      ↓
Collect logs, metrics, and traces
      ↓
Use AI to analyze the incident
      ↓
Recommend a recovery action
      ↓
Execute a controlled workflow
      ↓
Verify whether the system recovered
```

The workflow will handle predictable operations such as health checks, retries, timeouts, and service recovery. The AI agent will be used for tasks that require reasoning, such as identifying the probable root cause, comparing the incident with previous incidents, and explaining the recommended action.

The system will use predefined policies to control recovery actions. Risky actions will require human approval instead of being executed automatically.

## Failure Scenarios

The platform will demonstrate how it responds to several common distributed-system failures:

- **Service crash:** A service becomes unavailable or stops responding.
- **High latency:** A service responds very slowly and causes delays in other services.
- **Error spike:** A service begins returning a large number of HTTP 500 errors.
- **Database failure:** A service cannot connect to its database.
- **Message consumer failure:** A worker stops processing messages, causing queue backlog.
- **Faulty deployment:** A new service version causes increased failures and may need to be rolled back.

For each failure, the system will detect the problem, collect supporting information, generate an AI-based diagnosis, recommend a recovery action, and verify whether the system has returned to a healthy state.

## Role of Artificial Intelligence

The AI component will assist with incident analysis by:

- Summarizing relevant logs
- Identifying patterns in error messages
- Analyzing service dependencies
- Comparing current incidents with previous incidents
- Identifying the probable root cause
- Recommending a suitable recovery action
- Explaining the incident in a human-readable format

For example, the AI may determine that an increase in Payment Service failures is related to database connection timeouts that started after a recent deployment.

The AI will provide recommendations based on available evidence rather than making unsupported decisions.

## Distributed-System Concepts

This project will demonstrate:

- Independent services communicating over a network
- Event-driven communication using a message broker
- Partial failure handling
- Service health checks
- Timeouts and retries
- Circuit breakers
- Idempotent request processing
- Message reprocessing and dead-letter queues
- Distributed logging and tracing
- Fault detection and recovery
- Monitoring of service dependencies

## Expected Technologies

- Java Spring Boot for distributed services
- Python for the AI analysis service
- REST APIs for service communication
- Kafka or RabbitMQ for messaging
- PostgreSQL for service data
- Redis for caching and temporary state
- Docker for running independent services
- Prometheus, Grafana, and OpenTelemetry for monitoring
- A large language model and a vector database for AI-based incident analysis

## Expected Demonstration

The demonstration will show a normal request passing through the distributed services. The team will then introduce a controlled failure, such as stopping a service or adding artificial latency.

AgentMesh will detect the failure, collect system information, generate an AI explanation of the probable cause, recommend a recovery action, and verify whether the service recovered successfully.

## Project Goal

The goal of AgentMesh is to demonstrate how AI can assist with monitoring and incident response in distributed systems while maintaining reliability and safety through workflow-based control.

The project combines distributed systems, microservices, event-driven architecture, AI-assisted root-cause analysis, observability, and fault tolerance in a practical application.

# 2. Proposed Project Idea: OrderMesh

## Distributed Order Processing System

## Project Description

OrderMesh is a distributed order-processing platform modeled on a simplified e-commerce checkout flow. It consists of independently deployable microservices — an Order Service, Inventory Service, Payment Service, and Fulfillment Service — that communicate over REST/gRPC and coordinate asynchronously through a message broker to process an order from placement to fulfillment.

The project will use a small distributed application in which a single customer order triggers a multi-step workflow across services: inventory is checked and reserved, payment is authorized, and fulfillment is scheduled. Each step can fail independently, and the system must guarantee the order either completes correctly end-to-end or is safely and visibly rolled back.

## Problem Statement

In a distributed order pipeline, a single logical transaction (placing an order) spans multiple independent services and a database each. A failure partway through — a payment timeout, an inventory service crash, a duplicate retry — can leave the system in an inconsistent state: money charged with no inventory reserved, inventory reserved with no payment taken, or duplicate orders created from retried requests.

Coordinating correctness across independently failing, independently scaling services without a single shared database transaction is a central challenge in distributed systems, and doing it safely requires careful choices around consistency, idempotency, and failure recovery.

## Proposed Solution

The system will follow this general process for each order:

```text
Place order
      ↓
Reserve inventory (Inventory Service)
      ↓
Authorize payment (Payment Service)
      ↓
Schedule fulfillment (Fulfillment Service)
      ↓
Confirm order / emit completion event
      ↓
On failure at any step: compensate prior steps (saga rollback)
```

The order workflow will be implemented as a saga: each step publishes an event on success, and a failure at any step triggers compensating actions on the steps that already succeeded (e.g., releasing reserved inventory if payment fails). All requests will be idempotent, so retries from timeouts or network partitions never cause duplicate charges or duplicate inventory reservations.

## Failure Scenarios

The platform will demonstrate how it responds to several common distributed-system failures:

- **Service crash:** The Payment Service becomes unavailable mid-transaction.
- **High latency:** The Inventory Service responds slowly, triggering timeouts downstream.
- **Duplicate/retried requests:** A client retries an order request after a timeout, and the system must not double-charge or double-reserve.
- **Partial failure requiring rollback:** Inventory is reserved but payment fails, requiring a compensating release of inventory.
- **Message consumer failure:** A fulfillment worker stops processing events, causing a backlog that must be recovered without losing orders.
- **Region/replica failure:** A replica of the Inventory Service goes down, and traffic must continue to be served by remaining replicas under the chosen consistency model.

For each scenario, the system will demonstrate detection, safe compensation or retry, and a return to a consistent state.

## Distributed-System Concepts

This project will demonstrate:

- Independent services communicating over gRPC/REST
- Event-driven communication using a message broker
- Logical/vector clocks for ordering events across services
- Saga-based distributed transactions (in place of two-phase commit)
- Idempotent request processing
- Replication and consistency trade-offs (quorum reads/writes, eventual vs. strong consistency)
- Database sharding/partitioning by customer or region
- Timeouts, retries, and circuit breakers around service calls
- Chaos-style failure injection and recovery verification
- Distributed tracing across the full order flow
- Autoscaling under load

## Expected Technologies

- Java Spring Boot or Node.js for distributed services
- gRPC and REST for service communication
- Kafka or RabbitMQ for event-driven messaging and saga orchestration
- PostgreSQL for order/inventory/payment data (sharded by customer or region)
- Redis for caching and idempotency-key tracking
- Docker and Kubernetes for deployment and autoscaling
- OpenTelemetry, Prometheus, and Grafana for distributed tracing and monitoring
- A chaos-testing approach (manual fault injection or a lightweight chaos tool) for resilience validation

## Expected Demonstration

The demonstration will show a normal order flowing end-to-end through inventory reservation, payment authorization, and fulfillment scheduling, with a distributed trace visualized across all services.

The team will then introduce a controlled failure — such as killing the Payment Service mid-order or duplicating a request — and show the saga correctly compensating (releasing reserved inventory) or the idempotency layer correctly rejecting the duplicate, with the system returning to a consistent, observable state.

## Project Goal

The goal of OrderMesh is to demonstrate how a distributed transaction can be coordinated safely and consistently across independently failing services without a shared database transaction, using saga-based compensation, idempotency, replication, and observability to maintain correctness under real-world failure conditions.

The project combines distributed systems, microservices, event-driven architecture, consistency and consensus trade-offs, fault tolerance, and cloud-native deployment in a practical application.

# 3. Proposed Project Idea: AgentFlow

## Multi-Agent Distributed Task Orchestrator

## Project Description

AgentFlow is a distributed orchestration platform that coordinates multiple specialized AI agents to complete a multi-step task collaboratively. Rather than a single monolithic model handling everything, the system splits work across independent agents — for example, a research agent, a coding agent, and a review agent — each communicating with a central orchestrator over a well-defined protocol.

The project will use a small distributed application in which the orchestrator receives a task, decomposes it, assigns sub-tasks to the appropriate agents, tracks shared state and memory across the workflow, and hands off partial results between agents until the task is complete.

## Problem Statement

Coordinating multiple independent AI agents introduces the same challenges as coordinating any distributed system: agents may fail, respond slowly, or return unreliable output; work must be handed off correctly between agents without losing context; and shared state must remain consistent as multiple agents read and write to it concurrently.

On top of these distributed-systems challenges, agentic systems introduce new risks: an agent's tool calls can have real side effects, prompt injection can hijack an agent's behavior, and fully autonomous multi-step execution can compound a small error into a large one if left unchecked.

## Proposed Solution

The system will follow this general process for each incoming task:

```text
Receive task
      ↓
Orchestrator decomposes task into sub-tasks
      ↓
Assign sub-tasks to specialized agents (research, execution, review)
      ↓
Agents call tools via MCP and report results
      ↓
Orchestrator merges results into shared state/memory
      ↓
Guardrail check (policy + optional human approval for risky actions)
      ↓
Return final result or hand off to next agent
```

The orchestrator will manage a shared task state and conversation memory so agents can build on each other's work rather than operating in isolation. Predictable coordination logic (task assignment, retries, timeouts) will be handled by workflow code, while the agents themselves are used only for steps that require reasoning, such as evaluating research findings, generating code, or critiquing another agent's output.

## Failure Scenarios

The platform will demonstrate how it responds to several common failure and safety scenarios:

- **Agent timeout/failure:** A specialized agent hangs or returns malformed output, and the orchestrator must retry or reassign the sub-task.
- **Tool-call failure:** An MCP tool call fails or returns an error, requiring graceful handling instead of orchestrator crash.
- **Prompt injection attempt:** Malicious content in retrieved data attempts to override an agent's instructions, and guardrails must detect and block it.
- **Conflicting agent outputs:** Two agents produce contradictory results for the same sub-task, requiring a resolution or escalation strategy.
- **Risky action requiring approval:** An agent recommends an action outside its policy bounds (e.g., an external write action), which must be routed to a human for approval instead of executing automatically.
- **State/memory inconsistency:** Concurrent updates to shared task state from multiple agents must not silently overwrite each other.

For each scenario, the system will demonstrate detection, safe handling, and a return to correct orchestration state.

## Role of Artificial Intelligence

The AI agents will be used for:

- Researching and summarizing information relevant to a task
- Generating or modifying code based on task requirements
- Reviewing and critiquing another agent's output
- Explaining decisions and handoffs in human-readable form
- Flagging actions that fall outside safe policy bounds for human review

The orchestrator itself remains rule-based and deterministic wherever possible, using AI only where reasoning is genuinely required, and always logging the reasoning behind a recommended action rather than executing unexplained decisions.

## Distributed-System Concepts

This project will demonstrate:

- Independent agent processes communicating over a defined protocol (MCP)
- Task decomposition and orchestrated handoff between independent workers
- Shared state and memory management with concurrency considerations
- Timeouts and retries around agent/tool calls
- Policy-based guardrails and human-in-the-loop approval for risky actions
- Security considerations specific to agentic systems (prompt injection defense, tool-call authorization)
- Observability into multi-agent workflows (tracing which agent did what, and why)

## Expected Technologies

- Python for the orchestrator and agents
- MCP (Model Context Protocol) for agent-to-tool and agent-to-agent communication
- A large language model for each specialized agent role
- Redis or a lightweight database for shared task state and memory
- REST or a message queue for orchestrator-to-agent communication
- Docker for running independent agent processes
- OpenTelemetry or basic structured logging for tracing task flow across agents
- A guardrail/policy layer (rule-based checks) for gating risky tool calls

## Expected Demonstration

The demonstration will show a task submitted to the orchestrator, decomposed into sub-tasks, and routed across the research, execution, and review agents in sequence, with shared state visibly updated at each handoff.

The team will then introduce a failure scenario — such as a simulated tool-call error, an agent timeout, or an attempted prompt-injection payload — and show the orchestrator detecting the issue, applying the appropriate guardrail or retry, and either completing the task safely or correctly escalating to human approval.

## Project Goal

The goal of AgentFlow is to demonstrate how multiple AI agents can be coordinated reliably and safely as a distributed system, applying the same fault-tolerance, state-management, and observability principles used in traditional distributed systems to the emerging challenges of multi-agent, tool-calling AI workflows.

The project combines distributed systems, agent orchestration, shared state management, security in agentic systems, and observability in a practical application.
