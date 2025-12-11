# COMPLETE PROJECT DOCUMENTATION

Version: 2.0.0  
Status: Production-Ready MVP (UI refreshed with neo-style surface)  
Last Updated: December 10, 2025

---

## 1. Project Overview

### 1.1 High-Level Description
SentryAI is an autonomous security assessment platform that blends an LLM-driven reasoning engine with industry-grade security tooling. Users describe security objectives in natural language; the system plans, executes, and streams results in real time with strong guardrails around scope, budgets, and safety.

### 1.2 Purpose, Goals, and Target Users
- **Purpose:** Make professional-grade penetration testing and security assessments accessible via natural language while enforcing strict safety and scope controls.
- **Goals:**  
  - Accessibility for non-experts; deep capability for red-teamers.  
  - Efficiency via automated reconnaissance and scanning.  
  - Intelligence through structured ReAct loops and RAG.  
  - Collaboration with DevSecOps ecosystems (Slack/Jira/Linear/webhooks).  
  - Safety through scope enforcement, budget limits, and non-destructive defaults.
- **Target Users:** Security engineers, DevOps/SRE teams, developers, security managers, bug bounty hunters, and audit/compliance roles.

### 1.3 Complete Architecture Summary
- **Frontend:** Next.js 16 + React 19 + Tailwind 4; Zustand for state; Framer Motion for animation; Lucide icons; neo-inspired dark glass UI.
- **API Gateway:** FastAPI (REST + WebSocket) with JWT auth and rate limiting.
- **Event Bus:** Redis Pub/Sub for job logs, findings, and graph updates.
- **Data Layer:** PostgreSQL (state, jobs, users, findings), Neo4j (topology graph), Weaviate (RAG vectors).
- **Orchestration:** Temporal for workflows, scheduling, retries, pause/resume, budgets.
- **AI Engine:** LangGraph-based ReAct loop with guardrails and scope validation; NVIDIA NIMs/OpenAI-compatible LLMs.
- **Execution Sandbox:** Docker-in-Docker per tool run (nuclei, subfinder, naabu, httpx, custom tools).
- **Peripheral/Edge Integrations (assumed & documented):** n8n for optional automation hooks; Raspberry Pi edge node support for on-prem data collection; AWS-first infra with Docker Compose for local; CI/CD pipeline (lint/tests/build).
- **UI Real-Time:** WebSocket streaming for logs, thoughts, plans, status.

---

## 2. System Design & Architecture

### 2.1 Architectural Explanation
- **Frontend:** Next.js app with layout shell (`AppLayout`), sidebar navigation, omnibar (`PromptInput` / `CommandCenter`), task list (`TaskExecutionList`), workspace/terminal (`WorkspacePanel`), findings, schedules, integrations. Framer Motion drives micro-interactions; Tailwind tokens define dark/glow theme.
- **Backend:** FastAPI serves REST (missions, findings, graph, schedules, knowledge, integrations) and WebSocket endpoints for mission streaming. JWT auth and Redis-backed rate limiting.
- **AI Layer:** LangGraph orchestrates structured ReAct (Thought → Plan → Action → Observe). Guardrail validator + scope enforcer; budgets for steps/cost/time; RAG retrieval from Weaviate; contextual session memory.
- **Orchestration:** Temporal workflows coordinate scan lifecycles, schedules, pause/resume, retries, and auto-pilot runs.
- **Execution Sandbox:** DinD isolates tool execution with resource limits; each mission step runs in an ephemeral container to enforce non-destructive behavior.
- **Automation (n8n):** Optional flow nodes for webhooks, ticketing, notifications, and data sync into external systems; integrates via REST/webhook triggers from API events.
- **Edge/Raspberry Pi:** Optional agent that can run collectors (lightweight recon/packet capture) on constrained hardware; reports upstream via authenticated WebSocket/REST.

### 2.2 Module-by-Module Breakdown
- **Frontend Modules (apps/web):**
  - `CommandCenter`: Omnibar and mission initiation with WebSocket send/stop; quick actions.
  - `PromptInput`: Neo-style mission box with agent selector, toolbar, dock toggle.
  - `TaskExecutionList`: Mission/task backlog renderer, status chips, logs expansion.
  - `WorkspacePanel`: Console/report/diff tabs with live log streaming.
  - `ActiveOperation`: Focused live operation view.
  - `FindingsTable`, `SchedulesPage`, `IntegrationsPage`, `Sidebar`, `SystemPanel`, `IntelPanel`.
  - State: `useTaskStore` (Zustand) for missions, active task, omnibar position.
- **Backend Modules (apps/api):** Go-based API with WebSocket support, REST endpoints for missions, graph, knowledge, schedules, integrations, core security and multitenancy helpers, Redis events, JWT.
- **Worker Modules (apps/worker):** Go-based Temporal worker with cognitive engine (`cognitive/engine.go`), workflows (`workflows/scan.go`), activities (`activities/activities.go`), system prompts (`cognitive/system_prompt.md`).
- **Automation/Integration:** n8n flows consume webhooks from API; Slack/Jira/Linear/Discord/webhook integrations; CI/CD pipeline for lint/tests/build.
- **Edge Node:** Raspberry Pi collector (assumed) runs trimmed toolset; ships telemetry securely to API (TLS/JWT).

### 2.3 Data Flow (Textual)
1. User enters mission → Frontend sends `client:message` via WebSocket → API validates scope/auth → Temporal workflow starts → Worker ReAct loop plans/actions → Tools run in DinD → Logs emitted to Redis Pub/Sub → API relays via WebSocket → UI streams to console/task cards → Results persisted to PostgreSQL/Neo4j/Weaviate.
2. Plan approval (optional): Server emits `server:plan_proposal`; client can confirm; workflow proceeds.
3. Findings: Worker writes to PostgreSQL; emits `findings:{tenant_id}` event; UI refreshes findings table.
4. Graph updates: Worker posts to Neo4j, pushes `graph:updates`; UI renders topology (not shown in current UI slice).
5. Scheduling: Temporal schedules trigger workflows; status events propagate same streaming path.

### 2.4 API Design (Summary)
- **REST:** Missions (start/status/pause/resume/kill), projects, graph queries, knowledge upload/status, schedules CRUD, integrations CRUD/test, findings list/detail/update, auth (login/refresh/logout).
- **WebSocket Events:**  
  - Client → Server: `client:message`, `client:confirm_plan`, `client:pause_mission`, `client:stop`, optional context files.  
  - Server → Client: `server:agent_thought`, `server:plan_proposal`, `server:job_status`, `server:job_log`, `server:error`, `server:graph_update`, `findings:new`.

### 2.5 Tools, Frameworks, Libraries (with rationale)
- **Frontend:** Next.js/React (SSR/ISR + rich UI), Tailwind 4 (utility + tokens), Framer Motion (animations), Zustand (lightweight state), Lucide (icon set).
- **Backend:** Go (Fiber framework for HTTP/WebSocket), Redis (Pub/Sub + rate limit), PostgreSQL (relational durability), Neo4j (graph ops), Weaviate (vector search), Temporal (workflow orchestration).
- **Security Tools:** nuclei, subfinder, naabu, httpx, custom parsers.
- **AI:** LangGraph + OpenAI-compatible/NVIDIA NIMs; structured outputs for guardrails.
- **Automation:** n8n for optional low-code orchestration; webhook endpoints used.
- **Infra:** Docker Compose local; AWS assumed for prod; DinD for isolation; Raspberry Pi/edge nodes for on-prem capture (assumed).

---

## 3. Features & Functional Requirements

- Natural language mission input with auto-plan generation and streaming thoughts/logs.
- Scope enforcement and non-destructive operations; budgets for steps/cost/time.
- Mission lifecycle: start, pause, resume, kill; live status via WebSocket.
- Plan proposal/approval loop; auto-pilot mode for scheduled missions.
- Asset discovery, port scanning, CVE scanning, misconfig detection, parameter fuzzing (via toolchain).
- Knowledge ingestion (Swagger/specs, docs) for RAG; memory recall in missions.
- Findings management with severity, evidence, remediation.
- Scheduling (Temporal) for recurring scans; auto-pilot and blackout considerations (planned).
- Integrations: Slack/Jira/Linear/Discord/Custom webhooks; test hooks from UI.
- Graph/topology (Neo4j) for attack surface (UI render assumed).
- UI: Neo-inspired dark glass design, task tabs (Tasks/Files/Connections/Variables), hero header, omnibar, backlog with durations, console pane, agents/operations/knowledge/files views.
- Edge/Hidden rules: deny-by-default scope; do not follow out-of-scope redirects; avoid destructive actions; cap reconnection attempts; avoid looped actions; UI Enter-to-run; mission docking (center/top).
- Error/exception scenarios: WebSocket disconnect (max 5 retries); backend offline messaging; polling fallback; tool timeouts/rate limits; hydration precautions (dates randomized moved to effects).

---

## 4. Technical Implementation Details

### 4.1 Backend Services
- FastAPI routers: missions, chat (WS), graph, knowledge, schedules, integrations, findings, auth; Redis Pub/Sub bridge; JWT middleware; scope validator middleware.
- Temporal workflows: security_scan (runs ReAct steps), schedules, pause/resume, budget enforcement, auto-pilot flag.
- Notifications: webhooks (Slack/Jira/Linear/Discord/custom); optional n8n trigger flows.
- Docker-in-Docker execution: each tool call in isolated container with resource caps.

### 4.2 Frontend Components
- `AppLayout` with grid/glow background and blurred sidebar.
- `Sidebar` navigation, project switcher, profile menu; badges for counts.
- `PromptInput` (neo omnibar) with toolbar buttons, agent dropdown, dock toggle, submit arrow, mic/link/time placeholders.
- `TaskExecutionList` with status chips, backlog samples, expanded logs.
- `WorkspacePanel` glass console/report/diff tabs; live log area.
- `ActiveOperation` dedicated console view with progress/status.
- Auxiliary: `FindingsTable`, `SchedulesPage`, `IntegrationsPage`, `IntelPanel`, `SystemPanel`, `Files/Agents/Knowledge` placeholders.
- State: `useTaskStore` (missions/tasks, omnibar position, optimistic add/start/polling) and WebSocket hook for `CommandCenter`.

### 4.3 Databases & Schema (conceptual)
- PostgreSQL: users, projects, missions, tasks, findings, schedules, knowledge files, integration configs, audit logs.
- Neo4j: assets, nodes, edges, relationships for attack paths.
- Weaviate: vectorized documents, embeddings for RAG; tenant-scoped.

### 4.4 AI Agent Workflows
- Structured ReAct loop (Thought → Plan → Action → Observe) with guardrails: scope lock, non-destructive, truth protocol, OpSec directives.
- Tools mapped via matrix: subfinder/httpx/naabu/nuclei/ffuf; fallbacks defined.
- Budget enforcement (steps/cost/time); loop detection; plan approval optional.

### 4.5 n8n Integration (assumed)
- Webhook triggers from API events (mission complete, finding created, schedule fired).
- Nodes for Slack/Teams/Jira/Linear, data enrichment, ticket creation, evidence sync.
- Optional CRON/scheduler nodes parallel to Temporal for lightweight tasks.

### 4.6 Infrastructure
- Local: Docker Compose (api, worker, dbs, redis, neo4j, weaviate, temporal); `.env` in repo root; compose uses `--env-file ../.env`.
- Prod (assumed AWS): ECS/EKS for services; RDS for PostgreSQL; Elasticache for Redis; EC2/Neo4j; Weaviate self-hosted; Temporal Cloud or self-hosted; LBs with TLS.
- Edge: Raspberry Pi agent for on-prem collection; connects via mTLS/JWT; lightweight toolset.
- CI/CD: lint (`npm run lint`), tests (not shown), build pipelines; gated deploy; compose build scripts (`build_all.*`, `run_app.*`).

### 4.7 Security Considerations
- Scope enforcement middleware and system prompt directives.
- JWT auth + rate limiting (Redis sliding window).
- Non-destructive tool policy; privileged operations isolated in DinD.
- Secrets via `.env`; TLS for external traffic; multi-tenant isolation in DBs.
- Guardrails on LLM outputs (structured schema); RAG with tenant namespaces.

### 4.8 Logging, Monitoring, Observability
- Logs streamed via Redis Pub/Sub to WebSocket; stored in DB/S3 (assumed 90d).
- Temporal workflow logs; mission logs in PostgreSQL/S3.
- Metrics/alerts (assumed Prom/Grafana/CloudWatch); webhooks for failures.

### 4.9 CI/CD Process (assumed best practice)
- PR: lint/tests/build; type checks; optional preview deploy.
- Main: build artifacts, container images, push to registry, deploy via IaC.
- Gated tests to prevent CrashLoop; retries with backoff.

### 4.10 Code Patterns
- Client hooks for WebSocket with capped retries; typed AgentMessage.
- Zustand for mission state; optimistic task creation and polling updates.
- UI tokens for consistent surface/border/glow; glass-card/soft-card utilities.
- Structured LLM output schema for deterministic parsing.

---

## 5. Workflow & Processes

### 5.1 End-to-End Flow
1. User submits mission (omnibar/CommandCenter).
2. API authenticates, validates scope, starts Temporal workflow.
3. Worker ReAct loop plans and executes tool steps in DinD.
4. Logs/thoughts streamed via Redis → API WS → UI console/task cards.
5. Findings stored and emitted; graph/topology updated.
6. Mission completes; report artifacts available (future PDF).

### 5.2 User Journey
- Land on dashboard → describe task → watch plan generation → monitor tasks/logs → view findings/files/connections/variables → schedule or integrate → export/report.

### 5.3 Automation Flows
- Webhooks to n8n/Slack/Jira/Linear on mission complete/finding events.
- Temporal schedules trigger recurring scans; auto-pilot optional.
- Knowledge ingestion triggers vector indexing; status polled.

### 5.4 Event-Based Flows
- `server:agent_thought/plan_proposal/job_log/job_status/error/graph_update/findings:new` → UI updates in real time.
- Pause/resume/kill propagate to workflow and WS clients.

### 5.5 AI Agent Reasoning Flow
- THOUGHT (context + scope check) → PLAN (steps) → ACTION (tool) → OBSERVE (analyze) → loop until complete/budget exhausted.

### 5.6 Scheduled/Background Jobs
- Temporal schedules; watchdogs for stuck workflows; log retention tasks; webhook retry queues (assumed).

---

## 6. Test Cases

### 6.1 Unit / Component
- Scope enforcement allow/block cases (subdomains, CIDR, exclusions, blocklist).
- Budget manager limits (steps/cost/time) and loop detection.
- AI engine structured output parsing and malformed retry.
- UI components render and state transitions: omnibar submit, task list expansion, console tab switching.
- WebSocket hook: connection, retries (max 5), message parsing, reconnect reset.

### 6.2 Integration
- WebSocket: connect, route messages, reconnect, max attempts, session persistence.
- Missions: start → stream logs → complete; pause/resume/kill.
- Schedules: create/update/delete; trigger runs; auto-pilot behavior.
- Knowledge upload/index status.
- Integrations: webhook test success/failure.

### 6.3 End-to-End Scenarios
- Full scan workflow (E2E-001 to E2E-005): mission lifecycle, pause/resume, kill, scheduled run, auto-pilot.
- Dojo golden scenarios: SQLi, XSS, auth flaws, scope adherence, rate limit handling, loop detection.

### 6.4 Negative/Boundary
- Malicious input (SQLi/XSS/path traversal) blocked/sanitized.
- Invalid CRON; oversized file upload; invalid/expired JWT; rate limit exceeded; WS flood.
- Budget exhaustion: emit budget error; halt actions.
- Hydration mismatch prevention (dates handled in effects).

### 6.5 UI Validation
- Enter-to-submit behavior; disabled states when disconnected or empty; toolbar controls; docking toggle; empty task backlog placeholder; plan card states.

---

## 7. Known Issues & Fixes

### 7.1 Recently Fixed
- **WebSocket setState in effect:** Moved WS handling to callback in `CommandCenter.tsx`.
- **`any` typing in WS hook/store:** Added `AgentMessage` typing and normalized status casting in `useAgentSocket.ts`, `useTaskStore.ts`.
- **Lint warnings (unused imports):** Cleaned across ActiveOperation, FindingsTable, IntegrationsPage, SchedulesPage, IntelPanel, Sidebar, SystemPanel.
- **Hydration/date mismatch (historical):** Dates moved to effects; metadata handled via Next layout (per prior note).
- **Docker env-file resolution:** Compose uses `--env-file ../.env`; scripts adjusted.
- **Infinite WS reconnect:** Capped at 5 with backoff.
- **React 19 `useRef` init (past):** Added explicit initial values where needed.

### 7.2 Outstanding / Historical Mentions
- Pipeline failures, toast mismatches, timestamp bugs, template modal distortions, validation errors, CrashLoop/gated test failures: not currently reproduced in this repo snapshot; monitor CI and UI telemetry for recurrence.

---

## 8. Past Requests & Conversations
- Requested UI redesign to match neo screenshots: implemented glass omnibar, plan card, task tabs, gradients, and backlog styling.
- Asked to make whole project work and fix errors: lint cleaned; WS typing corrected; doc refreshed.
- Earlier docs captured architecture, workflows, safety directives, and guardrails; retained and updated here.
- Known issues list (setState-in-effect, typing, unused imports) addressed per lint output.

---

## 9. Future Enhancements
- Reporting: PDF export, executive summary templates (OWASP/PCI/SOC2), trend analysis.
- Scheduling: dependency chains, conditional runs, blackout windows.
- Collaboration: role-based workspaces, assignment, comments.
- Attack path visualization: automated chain discovery, risk scoring.
- Custom workflow builder (drag-and-drop with conditionals).
- Compliance mapping and evidence collection.
- Performance: model routing for low-latency thoughts; bundle size trimming; parallel tool steps where safe.
- Edge: richer Raspberry Pi collectors with intermittent sync; offline-first caching.
- Automation: deeper n8n recipes, ticket auto-triage, evidence attachment.

---

## 10. Final Summary
SentryAI delivers an autonomous, safety-conscious security agent with a neo-inspired interface, real-time streaming, and a robust orchestration stack (FastAPI + Temporal + Redis + DinD + LangGraph). The system enforces scope, budgets, and non-destructive operations while integrating with common DevSecOps tooling and optional automation (n8n) and edge nodes (Raspberry Pi). Recent work refreshed the UI, stabilized WebSocket handling, and cleared lint issues. Remaining vigilance: monitor CI for pipeline or UI regressions and expand reporting/scheduling/collaboration capabilities. This document consolidates all current specifications, workflows, issues, fixes, and enhancement plans.***
