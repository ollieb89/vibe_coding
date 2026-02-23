---
title: Agent Types Reference
source: skills/loki-mode/references/agent-types.md
---

## Agent Types Reference

Complete definitions and capabilities for all 37 specialized agent types used within Loki Mode.

---

## Overview

Loki Mode offers a collection of 37 predefined agent types organized into 7 specialized swarms. The orchestrator spawns only the agents required for your project, with simple applications using 5-10 agents and complex startups potentially utilizing over 100 agents working concurrently.

---

## Engineering Swarm (8 types)

| Agent | Capabilities |
|-------|-------------|
| `eng-frontend` | React/Vue/Svelte, TypeScript, Tailwind, accessibility, responsive design, state management |
| `eng-backend` | Node/Python/Go, REST/GraphQL, auth, business logic, middleware, validation |
| `eng-database` | PostgreSQL/MySQL/MongoDB, migrations, query optimization, indexing, backups |
| `eng-mobile` | React Native/Flutter/Swift/Kotlin, offline-first, push notifications, app store preparation |
| `eng-api` | OpenAPI specs, SDK generation, versioning, webhooks, rate limiting, documentation |
| `eng-qa` | Unit/integration/E2E tests, coverage, automation, test data management |
| `eng-perf` | Profiling, benchmarking, optimization, caching, load testing, memory analysis |
| `eng-infra` | Docker, K8s manifests, IaC review, networking, security hardening [source: skills/loki-mode/references/agent-types.md]

---

## Operations Swarm (8 types)

| Agent | Capabilities |
|-------|-------------|
| `ops-devops` | CI/CD pipelines, GitHub Actions, GitLab CI, Jenkins, build optimization |
| `ops-sre` | Reliability, SLOs/SLIs, capacity planning, on-call, runbooks |
| `ops-security` | SAST/DAST, pen testing, vulnerability management, security reviews |
| `ops-monitor` | Observability, Datadog/Grafana, alerting, dashboards, log aggregation |
| `ops-incident` | Incident response, runbooks, RCA, post-mortems, communication |
| `ops-release` | Versioning, changelogs, blue-green, canary, rollbacks, feature flags |
| `ops-cost` | Cloud cost optimization, right-sizing, FinOps, reserved instances |
| `ops-compliance` | SOC2, GDPR, HIPAA, PCI-DSS, audit preparation, policy enforcement [source: skills/loki-mode/references/agent-types.md]

---

## Business Swarm (8 types)

| Agent | Capabilities |
|-------|-------------|
| `biz-marketing` | Landing pages, SEO, content, email campaigns, social media |
| `biz-sales` | CRM setup, outreach, demos, proposals, pipeline management |
| `biz-finance` | Billing (Stripe), invoicing, metrics, runway, pricing strategy |
| `biz-legal` | ToS, privacy policy, contracts, IP protection, compliance documents |
| `biz-support` | Help docs, FAQs, ticket system, chatbot, knowledge base |
| `biz-hr` | Job posts, recruiting, onboarding, culture documents, team structure |
| `biz-investor` | Pitch decks, investor updates, data room, cap table management |
| `biz-partnerships` | BD outreach, integration partnerships, co-marketing, API partnerships [source: skills/loki-mode/references/agent-types.md]

---

## Data Swarm (3 types)

| Agent | Capabilities |
|-------|-------------|
| `data-ml` | Model training, MLOps, feature engineering, inference, model monitoring |
| `data-eng` | ETL pipelines, data warehousing, dbt, Airflow, data quality |
| `data-analytics` | Product analytics, A/B tests, dashboards, insights, reporting [source: skills/loki-mode/references/agent-types.md]

---

## Product Swarm (3 types)

| Agent | Capabilities |
|-------|-------------|
| `prod-pm` | Backlog grooming, prioritization, roadmap, specs, stakeholder management |
| `prod-design` | Design system, Figma, UX patterns, prototypes, user research |
| `prod-techwriter` | API docs, guides, tutorials, release notes, developer experience [source: skills/loki-mode/references/agent-types.md]

---

## Growth Swarm (4 types)

| Agent | Capabilities |
|-------|-------------|
| `growth-hacker` | Growth experiments, viral loops, referral programs, acquisition |
| `growth-community` | Community building, Discord/Slack, ambassador programs, events |
| `growth-success` | Customer success, health scoring, churn prevention, expansion |
| `growth-lifecycle` | Email lifecycle, in-app messaging, re-engagement, onboarding [source: skills/loki-mode/references/agent-types.md]

---

## Agent Lifecycle

```
SPAWN -> INITIALIZE -> POLL_QUEUE -> CLAIM_TASK -> EXECUTE -> REPORT -> POLL_QUEUE
           |              |                        |          |
           |         circuit open?             timeout?    success?
           |              |                        |          |
           v              v                        v          v
     Create state    WAIT_BACKOFF              RELEASE    UPDATE_STATE
                          |                    + RETRY         |
                     exponential                              |
                       backoff                                v
                                                    NO_TASKS --> IDLE (5min)
                                                                    |
                                                             idle > 30min?
                                                                    |
                                                                    v
                                                               TERMINATE
```

---

## Dynamic Scaling Rules

| Condition | Action | Cooldown |
|-----------|--------|----------|
| Queue depth > 20 | Spawn 2 agents of bottleneck type | 5min |
| Queue depth > 50 | Spawn 5 agents, alert orchestrator | 2min |
| Agent idle > 30min | Terminate agent | - |
| Agent failed 3x consecutive | Terminate, open circuit breaker | 5min |
| Critical task waiting > 10min | Spawn priority agent | 1min |
| Circuit breaker half-open | Spawn 1 test agent | - |
| All agents of type failed | HALT, request human intervention | - |

---

## Agent Context Preservation

### Lineage Rules
1. **Immutable Inheritance:** Agents CANNOT modify inherited context
2. **Decision Logging:** All decisions MUST be logged to agent context file
3. **Lineage Reference:** All commits MUST reference parent agent ID
4. **Context Handoff:** When agent completes, context is archived but lineage preserved

### Preventing Context Drift
1. Read `.agent/sub-agents/${parent_id}.json` before spawning
2. Inherit immutable context (tech stack, constraints, decisions)
3. Log all new decisions to own context file
4. Reference lineage in all commits
5. Periodic context sync: check if inherited context has been updated upstream [source: skills/loki-mode/references/agent-types.md]