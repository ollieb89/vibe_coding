---
title: Feature Development
source: backend-development/commands/feature-development.md
---

## Classification Insights
- Primary Category: reference (confidence: 0.80)
- Secondary Category: runbook (confidence: 0.79)
- Key Features: api_patterns (0.40), step_indicators (-0.20)

```markdown
---
type: reference
---

# Feature Development Workflow

Orchestrate end-to-end feature development from requirements to production deployment, utilizing specialized agents and comprehensive phases for coherent feature delivery. This workflow supports various development methodologies (traditional, TDD/BDD, DDD), feature complexity levels, and modern deployment strategies including feature flags, gradual rollouts, and observability-first development.

## Configuration Options

### Development Methodology
- **traditional**: Sequential development with testing after implementation
- **tdd**: Test-Driven Development with red-green-refactor cycles
- **bdd**: Behavior-Driven Development with scenario-based testing
- **ddd**: Domain-Driven Design with bounded contexts and aggregates

### Feature Complexity
- **simple**: Single service, minimal integration (1-2 days)
- **medium**: Multiple services, moderate integration (3-5 days)
- **complex**: Cross-domain, extensive integration (1-2 weeks)
- **epic**: Major architectural changes, multiple teams (2+ weeks)

### Deployment Strategy
- **direct**: Immediate rollout to all users
- **canary**: Gradual rollout starting with 5% of traffic
- **feature-flag**: Controlled activation via feature toggles
- **blue-green**: Zero-downtime deployment with instant rollback
- **a-b-test**: Split traffic for experimentation and metrics

## Phase 1: Discovery & Requirements Planning

1. **Business Analysis & Requirements**
   - Use Task tool with subagent_type="business-analytics::business-analyst"
   - Prompt: "Analyze feature requirements for [user-defined]. Define user stories, acceptance criteria, success metrics, and business value. Identify stakeholders, dependencies, and risks. Create feature specification document with clear scope boundaries."
   - Expected output: Requirements document with user stories, success metrics, risk assessment
   - Context: Initial feature request and business context

2. **Technical Architecture Design**
   - Use Task tool with subagent_type="comprehensive-review::architect-review"
   - Prompt: "Design technical architecture for [user-defined]. Using requirements: [include business analysis from step 1]. Define service boundaries, API contracts, data models, integration points, and technology stack. Consider scalability, performance, and security requirements."
   - Expected output: Technical design document with architecture diagrams, API specifications, data models
   - Context: Business requirements, existing system architecture

3. **Feasibility & Risk Assessment**
   - Use Task tool with subagent_type="security-scanning::security-auditor"
   - Prompt: "Assess security implications and risks for [user-defined]. Review architecture: [include technical design from step 2]. Identify security requirements, compliance needs, data privacy concerns, and potential vulnerabilities."
   - Expected output: Security assessment with risk matrix, compliance checklist, mitigation strategies
   - Context: Technical design, regulatory requirements

## Phase 2: Implementation & Development

4. **Backend Services Implementation**
   - Use Task tool with subagent_type="backend-architect"
   - Prompt: "Implement backend services for [user-defined]. Follow technical design: [include architecture from step 2]. Build RESTful/GraphQL APIs, implement business logic, integrate with data layer, add resilience patterns (circuit breakers, retries), implement caching strategies. Include feature flags for gradual rollout."
   - Expected output: Backend services with APIs, business logic, database integration, feature flags
   - Context: Technical design, API contracts, data models

5. **Frontend Implementation**
   - Use Task tool with subagent_type="frontend-mobile-development::frontend-developer"
   - Prompt: "Build frontend components for [user-defined]. Integrate with backend APIs: [include API endpoints from step 4]. Implement responsive UI, state management, error handling, loading states, and analytics tracking. Add feature flag integration for A/B testing capabilities."
   - Expected output: Frontend components with API integration, state management, analytics
   - Context: Backend APIs, UI/UX designs, user stories

6. **Data Pipeline & Integration**
   - Use Task tool with subagent_type="data-engineering::data-engineer"
   - Prompt: "Build data pipelines for [user-defined]. Implement ETL processes, custom metrics, and data warehousing. Configure real-time analytics and reporting."
   - Expected output: Data pipelines, ETL processes, custom metrics, data warehousing, real-time analytics, and reporting
   - Context: Feature implementation, success metrics, operational requirements

## Phase 3: Testing & Validation

7. **Unit Testing**
   - Use Task tool with subagent_type="unit-testing::unit-tester"
   - Prompt: "Perform unit testing on individual components and services to ensure they meet functional requirements."
   - Expected output: Unit test reports, code coverage analysis
   - Context: Feature implementation, technical design

8. **Integration Testing**
   - Use Task tool with subagent_type="integration-testing::integration-tester"
   - Prompt: "Perform integration testing to verify that components and services work together as expected."
   - Expected output: Integration test reports, code coverage analysis
   - Context: Feature implementation, technical design

9. **System Testing**
   - Use Task tool with subagent_type="system-testing::system-tester"
   - Prompt: "Perform system testing to ensure the feature functions correctly in a production-like environment."
   - Expected output: System test reports, code coverage analysis
   - Context: Feature implementation, technical design

10. **Acceptance Testing**
    - Use Task tool with subagent_type="acceptance-testing::acceptance-tester"
    - Prompt: "Perform acceptance testing to ensure the feature meets business requirements and user expectations."
    - Expected output: Acceptance test reports, code coverage analysis
    - Context: Feature implementation, technical design, business requirements

## Phase 4: Deployment & Monitoring

11. **Deployment**
    - Use Task tool with subagent_type="deployment::deployment-engineer"
    - Prompt: "Deploy the feature to production using the chosen deployment strategy."
    - Expected output: Successful deployment confirmation, rollback plan (if necessary)
    - Context: Feature implementation, technical design, deployment strategy

12. **Observability & Monitoring**
    - Use Task tool with subagent_type="observability-monitoring::observability-engineer"
    - Prompt: "Set up observability for the deployed feature. Implement distributed tracing, custom metrics, error tracking, and alerting. Create dashboards for feature usage, performance metrics, error rates, and business KPIs. Set up SLOs/SLIs with automated alerts."
    - Expected output: Monitoring dashboards, alerts, SLO definitions, observability infrastructure
    - Context: Feature implementation, success metrics, operational requirements

13. **Documentation & Knowledge Transfer**
    - Use Task tool with subagent_type="documentation-generation::docs-architect"
    - Prompt: "Generate comprehensive documentation for the deployed feature. Create API documentation, user guides, deployment guides, troubleshooting runbooks. Include architecture diagrams, data flow diagrams, and integration guides. Generate automated changelog from commits."
    - Expected output: API docs, user guides, runbooks, architecture documentation
    - Context: All previous phases' outputs

## Execution Parameters

### Required Parameters
- **--feature**: Feature name and description
- **--methodology**: Development approach (traditional|tdd|bdd|ddd)
- **--complexity**: Feature complexity level (simple|medium|complex|epic)

### Optional Parameters
- **--deployment-strategy**: Deployment approach (direct|canary|feature-flag|blue-green|a-b-test)
- **--test-coverage-min**: Minimum test coverage threshold (default: 80%)
- **--performance-budget**: Performance requirements (e.g., <200ms response time)
- **--rollout-percentage**: Initial rollout percentage for gradual deployment (default: 5%)
- **--feature-flag-service**: Feature flag provider (launchdarkly|split|unleash|custom)
- **--analytics-platform**: Analytics integration (segment|amplitude|mixpanel|custom)
- **--monitoring-stack**: Observability tools (datadog|newrelic|grafana|custom)

## Success Criteria

- All acceptance criteria from business requirements are met
- Test coverage exceeds minimum threshold (80% default)
- Security scan shows no critical vulnerabilities
- Performance meets defined budgets and SLOs
- Feature flags configured for controlled rollout
- Monitoring and alerting fully operational
- Documentation complete and approved
- Successful deployment to production with rollback capability
- Product analytics tracking feature usage
- A/B test metrics configured (if applicable)

## Rollback Strategy

If issues arise during or after deployment:
1. Immediate feature flag disable (< 1 minute)
2. Blue-green traffic switch (< 5 minutes)
3. Full deployment rollback via CI/CD (< 15 minutes)
4. Database migration rollback if needed (coordinate with data team)
5. Incident post-mortem and fixes before re-deployment

Feature description: [user-defined]

## Instructions
1. Improve structure and clarity
2. Keep all code blocks exactly as-is (verbatim, do not summarize)
3. Add a citation [source: backend-development/commands/feature-development.md] at the end
4. Ensure all headings follow a logical hierarchy (no skipping levels)
5. Expand any placeholder text like [user-defined] into helpful descriptions
6. Start with YAML frontmatter including title, description, and tags
7. Do NOT wrap the output in a markdown code block (output raw text)
8. Do not repeat these instructions in your response.
```
[source: backend-development/commands/feature-development.md]