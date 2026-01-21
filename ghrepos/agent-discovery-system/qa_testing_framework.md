# Phase 2B: Quality Assurance Testing Framework

**Objective:** Validate that the Ultimate Agent Generator produces production-ready composite agents
**Date Started:** December 5, 2025
**Target:** 13 ultimate agents (3 pre-generated + 10 new test subjects)

---

## Evaluation Criteria

### 1. **Specialist Selection Relevance** (1-10)
- Are the selected specialists relevant to the subject?
- Do they represent the major expertise areas in the field?
- Is there good diversity (not all from one domain)?

**Scoring:**
- 9-10: All specialists directly relevant, good coverage
- 7-8: Most specialists relevant, minor edge cases
- 5-6: Mixed relevance, some stretches
- 1-4: Many irrelevant specialists

### 2. **Persona Clarity & Coherence** (1-10)
- Is the composite agent persona clear and unified?
- Does it avoid contradictions?
- Is the focus area well-defined?

**Scoring:**
- 9-10: Crystal clear persona, well-unified
- 7-8: Clear with minor inconsistencies
- 5-6: Somewhat clear but fuzzy in places
- 1-4: Confused or contradictory

### 3. **Use Case Appropriateness** (1-10)
- Are the generated use cases realistic and practical?
- Do they represent actual problems the agent would solve?
- Are they specific enough to be useful?

**Scoring:**
- 9-10: All use cases highly practical and specific
- 7-8: Most use cases practical, some generic
- 5-6: Some useful, some generic
- 1-4: Mostly generic or disconnected

### 4. **Instructions & Guidance Quality** (1-10)
- Are the core instructions clear and actionable?
- Do they provide concrete guidance?
- Are they comprehensive without being overwhelming?

**Scoring:**
- 9-10: Clear, actionable, comprehensive
- 7-8: Good guidance with minor gaps
- 5-6: Adequate but could be clearer
- 1-4: Vague or incomplete

### 5. **Metadata & YAML Quality** (1-10)
- Is the YAML frontmatter correct and complete?
- Are all required fields present?
- Is the data well-structured?

**Scoring:**
- 9-10: Perfect YAML, all fields present
- 7-8: Valid YAML, minor missing fields
- 5-6: Valid but incomplete
- 1-4: Malformed or missing critical fields

### 6. **Output Format Compliance** (1-10)
- Does it follow the standard agent format?
- Is the markdown properly formatted?
- Are sections in the right order?

**Scoring:**
- 9-10: Perfect format, ready to use
- 7-8: Minor formatting issues, but functional
- 5-6: Mostly correct format
- 1-4: Significant format violations

### 7. **Cross-Domain Consistency** (1-10)
- Are all agents generated with consistent structure?
- Do they have similar quality levels?
- Is the approach reproducible?

**Scoring:**
- 9-10: Highly consistent across all agents
- 7-8: Mostly consistent with minor variations
- 5-6: Some variation in quality/structure
- 1-4: Inconsistent approach

### 8. **Production Readiness** (1-10)
- Could this agent be used in production right now?
- How much customization is needed?
- Would users accept it as-is?

**Scoring:**
- 9-10: Production-ready immediately
- 7-8: Minor tweaks needed
- 5-6: Significant customization required
- 1-4: Not ready for production use

---

## Test Subjects (13 Total)

### Pre-Generated (Testing Phase 1)
- ✅ Security
- ✅ Testing
- ✅ AI/ML

### New Test Subjects (Phase 2B)
- [ ] Frontend
- [ ] Backend
- [ ] DevOps
- [ ] Database
- [ ] Data Science
- [ ] Planning
- [ ] Documentation
- [ ] Code Quality
- [ ] System Design
- [ ] CI/CD

---

## Test Results Template

For each agent, score 1-10 on all 8 criteria:

```
## [Subject] Ultimate Agent

| Criterion | Score | Notes |
|-----------|-------|-------|
| Specialist Selection Relevance | _/10 | |
| Persona Clarity & Coherence | _/10 | |
| Use Case Appropriateness | _/10 | |
| Instructions & Guidance Quality | _/10 | |
| Metadata & YAML Quality | _/10 | |
| Output Format Compliance | _/10 | |
| Cross-Domain Consistency | _/10 | |
| Production Readiness | _/10 | |
| **AVERAGE** | **_/10** | |

**Key Findings:**
- [Main strength]
- [Main weakness]
- [Recommendation]
```

---

## Claude Validation Prompts

### Prompt A: Overall Quality Assessment
```
I've generated a composite agent from multiple specialists.
Please evaluate this agent:

[PASTE AGENT CONTENT]

Rate 1-10 on:
1. Is the persona clear and usable?
2. Are the specialists well-chosen?
3. Would you use this in practice?
4. What's one improvement needed?

Provide scores and brief explanations.
```

### Prompt B: Practical Usability Test
```
Here's a composite agent definition. I'm going to ask you
to USE it, then evaluate.

[PASTE AGENT CONTENT]

Now, activate this agent and:
1. Show me an example of how you'd apply it to a real scenario
2. Rate how natural the persona feels (1-10)
3. Is anything unclear or contradictory?
4. Would you change anything?
```

### Prompt C: Specialist Verification
```
This composite agent includes specialists from: [LIST SPECIALISTS]

For the subject "[SUBJECT]":
1. Are these the RIGHT specialists?
2. Are any missing that should be included?
3. Are any included that shouldn't be?
4. Overall specialist mix rating (1-10)?
```

---

## Consistency Checks

### Structure Consistency
All agents should have:
- [ ] YAML frontmatter with name, description, version
- [ ] Activation section
- [ ] Persona section (clear identity)
- [ ] Core behaviors (2-3 main things it does)
- [ ] Focus areas (3-5 areas of expertise)
- [ ] Use cases section (3-5 practical scenarios)
- [ ] Specialist sources (cited from Chroma retrieval)
- [ ] Instructions (clear guidance on using agent)

### Quality Consistency
- [ ] All agents generated at same --top setting (5)
- [ ] All use same metadata extraction
- [ ] All follow same markdown template
- [ ] Score distribution should be relatively tight (no outliers)

### Metadata Accuracy
- [ ] Subject field correctly reflects generated subject
- [ ] Specialist count matches listed specialists
- [ ] All specialist names are real (not hallucinated)
- [ ] Creation date is consistent

---

## Success Criteria for Phase 2B

### GO/NO-GO Decision Points

**PASS Production Readiness If:**
- 80%+ of agents average 7+/10 on Production Readiness
- Average score across all criteria is 7+/10
- No critical issues identified in Claude testing
- All structure consistency checks pass
- Claude users rate usability 7+/10 average

**NEEDS IMPROVEMENT If:**
- <80% of agents meet 7+/10 threshold
- Average score <7/10
- Multiple agents have issues with consistency
- Claude identifies critical problems
- Usability rating <7/10

**CRITICAL ISSUES That Stop Release:**
- YAML parsing errors
- Missing specialist data (hallucinated names)
- Contradictory persona instructions
- Format violations breaking activation
- Duplicate agents or naming conflicts

---

## Testing Timeline

- **30 min:** Generate all 10 test ultimates ✓
- **30 min:** Create evaluation framework (THIS DOCUMENT) ✓
- **60 min:** Score all 13 agents (8 criteria each = 104 data points)
- **60 min:** Test 5-10 agents in Claude with validation prompts
- **30 min:** Analyze results and create report

**Total estimated: 3.5 hours**

---

## Progress Tracking

### Task 1: Generate Diverse Ultimates
- Status: ✅ COMPLETE
- Files: 10 generated in `qa_test_output/`
- Subjects: frontend, backend, devops, database, data science, planning, documentation, code quality, system design, ci/cd

### Task 2: Score All Agents (IN PROGRESS)
- Status: Starting evaluation
- Scoring method: 8 criteria × 13 agents = 104 data points
- Tools: Manual review + spreadsheet tracking

### Task 3: Test in Claude (PENDING)
- Status: Will execute after scoring
- Method: Copy agent to Claude, use validation prompts
- Coverage: 5-10 key agents for detailed feedback

### Task 4: Analyze & Report (PENDING)
- Status: Will execute after testing
- Output: Final QA report with production-readiness decision
- Recommendations: Improvements for Phase 2C/2D

---

## Notes

- All agents use same retriever settings (top 5 matches)
- Same subject keywords extraction applied consistently
- Subject-specific filtering ensures relevance
- Metadata includes actual specialist counts from Chroma
- No hallucinated specialists (all verified from collection)

---

**Phase 2B Status:** In Progress - Framework established, generation complete, scoring to begin
