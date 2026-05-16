# CONTEXT.md — FluxAgent V2 Domain Glossary

> Used by `improve-codebase-architecture` to anchor architectural suggestions
> in the actual domain language. Every term here has a precise meaning within
> FluxAgent. Do not substitute synonyms.

---

## Core Domain Concepts

**Tenant**
A paying customer (business) that uses FluxAgent. All data, quotas, agents,
and channels are scoped to a Tenant. Identified by `tenant_id` (UUID).
Never mix data across tenants.

**Canal (Channel)**
A messaging integration through which a Tenant communicates with end-users.
Concrete adapters: WhatsApp via Evolution API, Telegram, Meta (Instagram/FB).
A Channel can become `disconnected` — tracked in the Operational State Journal.

**Conversation**
A thread of messages between one end-user and the Tenant's AI Agent, within
a Channel. Has lifecycle: `open → active → handoff_requested → closed`.
Primary aggregate for the messaging domain.

**Message**
A single unit of content within a Conversation. Can be `received` (from
end-user) or `sent` (from agent or human operator).

**Handoff**
The act of escalating a Conversation from an AI Agent to a human operator.
Tracked as a domain event pair: `handoff.requested` → `handoff.completed`.
SLA: must be attended within 15 minutes.

**Agent (AI Agent)**
An autonomous conversational entity configured per Tenant. Has a base prompt,
a set of allowed Tools, and belongs to a domain (sales, support, operations).
Registered in `AgentRegistry`. Three built-in types: `sales`, `support`,
`operations`.

**Tool**
A discrete capability an Agent can invoke during a Conversation (e.g.,
`query_catalog`, `create_quote`, `check_inventory`). Each Tool has a
`ToolContract` that declares its risk level, required permissions, and
input/output schema. Governed by `ToolRuntime`.

**Tool Contract**
The interface definition for a Tool: name, description, input schema,
risk level (`low/medium/high/critical`), required roles, and whether it
requires human approval before execution. Lives in `runtime/tool_contract.py`.

**Quota**
A usage limit enforced per Tenant per billing period (month). Tracked in
Redis with key pattern `billing:{tenant_id}:{YYYY-MM}:{quota_name}`.
Billable quotas: `messages`, `ai_requests`, `images`, `audio_sec`.
Enforced by `PlanManager`.

**Plan**
A subscription tier that defines feature flags and quota limits for a Tenant.
Stored in `flux_plan_features` (PostgreSQL) and cached in Redis.
Tiers: `basic`, `pro`, `enterprise` (enterprise has unlimited quotas).

**Policy Rule**
A governance rule that controls whether an Agent Tool execution is
`allowed`, `denied`, `pending_approval`, or `modified`. Rules are stored
in `flux_policies` (PostgreSQL, JSONB conditions). Evaluated by `PolicyEngine`
in priority order. Priority must be >= 1.

**Action**
A high-impact operational command that a human operator (or AI with approval)
can execute on the system. Examples: `REPLAY_WEBHOOK`, `ISSUE_REFUND`,
`CANCEL_ORDER`, `EXPORT_CUSTOMER_DATA`. Governed by `ActionGovernanceRegistry`.
Every Action has an `ActionPolicy` with allowed roles and approval requirements.

**HITL (Human-in-the-Loop)**
The approval workflow that intercepts high-risk Actions before execution.
Managed by `HITLEngine`. Stores pending approvals as domain events.
Approval can only be granted by a human with a matching role in the
`ActionPolicy.allowed_roles`. `sysadmin` bypasses all approvals.

**Operational State Journal**
An append-only event log that records every significant state transition
across the system (channel disconnections, handoff requests, quota warnings,
payment failures). Consumed by the `OperationalHealthEngine` for the
Mission Control dashboard.

**Outbox**
A transactional outbox pattern table (`flux_outbox`) that buffers domain
events before they are dispatched to downstream systems. Prevents data loss
on partial failures. Replayed via `REPLAY_WEBHOOK` action.

**Reservation**
A temporary hold on inventory for a pending Order. Can become a "ghost
reservation" if the Order is cancelled without releasing it. Freed via
`RELEASE_RESERVATION` action.

**Order**
A confirmed purchase by an end-user. Has lifecycle stages tracked in the
event log. Can be cancelled via `CANCEL_ORDER` action.

**Quote**
A draft Order presented to an end-user before confirmation. Created by
the sales Agent via Tool invocation.

**Connector**
An integration with an external system (ERP, Shopify, MercadoPago).
Forced synchronization available via `SYNC_CONNECTOR` action.

**Workflow**
A multi-step automated sequence of Tool invocations defined per Tenant.
Executed by `WorkflowRuntimeEngine`. Steps have conditions evaluated via
`json_logic`. Has a circuit breaker at 100 steps.

**SLA**
Service Level Agreement threshold. Three tracked SLAs:
- First response: 30 minutes from `message.received`
- Followup delivery: 48 hours from `followup.scheduled`
- Handoff attendance: 15 minutes from `handoff.requested`

---

## Infrastructure Concepts

**EventBus**
Internal in-process pub/sub for domain events. Used by `HITLEngine` to
publish to the `Operational State Journal` without coupling to a specific
broker. Can be backed by Redis pub/sub in production.

**PlanManager**
The module responsible for reading Plan feature flags and enforcing Quota
limits. Source of truth: `flux_plan_features` (DB) + Redis cache.
Never instantiate without both `redis` and `db` dependencies.

**PolicyEngine**
Evaluates `PolicyRule` objects against a Tool execution request.
Returns a `PolicyEngineOutput` with `allowed`, `requires_approval`, and
`applied_modifications`. Has an in-memory cache keyed by `tenant_id:tool_name`.

**OperationalHealthEngine**
Computes the business health report for a Tenant. Queries `event_log`
for SLA breaches, channel disconnections, payment failures, handoff backlog,
and quota usage. Not infrastructure health — business health.

**AgentRegistry**
Bootstrap registry of available Agent definitions. Loaded at application
startup via `lifespan`. Three built-in agents registered at boot.

**ToolRuntime**
The execution engine for Tool invocations. Validates contracts, checks
governance, and dispatches to the concrete Tool implementation.

---

## Key Seams (Architectural Boundaries)

- `PolicyEngine` ↔ `ToolRuntime` — policy evaluation before tool dispatch
- `HITLEngine` ↔ `ActionGovernanceRegistry` — human approval gate
- `PlanManager` ↔ `PolicyEngine` — plan features inform policy decisions
- `EvolutionAdapter` ↔ `Canal` — WhatsApp messaging seam
- `WorkflowRuntimeEngine` ↔ `ToolRuntime` — workflow step execution
- `EventBus` ↔ `OperationalStateJournal` — decoupled event recording

---

## What This Is NOT

- "Service" — use **Module** instead
- "Component" — use **Module** instead
- "Boundary" — use **Seam** instead
- "Microservice" — FluxAgent is a monolith-first architecture
- "Saga" — use **Workflow** for multi-step processes
