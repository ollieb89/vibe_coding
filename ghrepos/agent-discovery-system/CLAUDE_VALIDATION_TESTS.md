# Phase 2B: Claude Validation Test Suite

**Purpose:** Verify production readiness of ultimate agents through practical testing in Claude
**Date:** December 5, 2025
**Target:** Test 5 key agents with validation prompts

---

## Test Agent Selection

### Selected Agents for Claude Testing

1. **Ultimate-Security** (Score: 9.1/10 - Excellent reference)
   - Rationale: Highest scoring agent, should serve as quality baseline
   - Expected: Perfect activation and usability
   - Purpose: Confirm excellent agents work as expected

2. **Ultimate-DevOps** (Score: 9.3/10 - Excellent reference)
   - Rationale: Second highest score, full domain expertise
   - Expected: Excellent practical applicability
   - Purpose: Validate another excellent example

3. **Ultimate-Database** (Score: 7.6/10 - Fair/borderline)
   - Rationale: Lower score due to BI specialist mismatch
   - Expected: Still usable, but test for clarity issues
   - Purpose: Verify fair-scored agents still work in practice

4. **Ultimate-Data-Science** (Score: 7.9/10 - Fair)
   - Rationale: Title says "Data Science" but BI-heavy content
   - Expected: Test clarity of persona vs specialist mix
   - Purpose: Identify if branding/naming needs clarification

5. **Ultimate-Frontend** (Score: 8.0/10 - Good)
   - Rationale: Contains one off-topic specialist (backend architect)
   - Expected: Generally usable despite mismatch
   - Purpose: Test how mixed-domain specialists affect usability

---

## Test Validation Prompts

### Prompt Template 1: Overall Quality Assessment

**When:** Use for all 5 agents
**Time:** 2-3 minutes per agent

```
I've generated a composite agent from multiple specialists.
Please evaluate this agent for production readiness:

[PASTE AGENT CONTENT]

Rate 1-10 on these dimensions:
1. Persona Clarity - Is the agent identity clear and coherent?
2. Specialist Fit - Are the specialists well-chosen for this role?
3. Practical Usability - Would you use this agent in real work?
4. Instruction Quality - Are the instructions clear and actionable?
5. Overall Quality - Rate overall production readiness

For each dimension, provide:
- Score (1-10)
- Brief justification
- One specific improvement (if applicable)
```

**What to Look For:**
- Scores 7+/10 on all dimensions indicate good quality
- Scores <7 on any dimension indicate potential issues
- Specific feedback on what works and what doesn't

---

### Prompt Template 2: Activation & Persona Test

**When:** Use for 1-2 key agents (Security, DevOps)
**Time:** 5 minutes per agent

```
I want to activate this composite agent and test it. Here's the definition:

[PASTE AGENT CONTENT]

Now, activate this agent and:

1. Confirm activation
   - "I am now [agent name]" or similar
   - Show that you understand the persona

2. Demonstrate application
   - Give me an example of how you'd apply this agent to a real scenario
   - Show the agent "in action" on a realistic problem
   - Example: For security agent → "I would review your code for OWASP compliance by..."

3. Rate the experience
   - How natural does this persona feel? (1-10)
   - Is anything unclear or contradictory?
   - Would you change anything?
   - How would users perceive this agent?

4. Feedback
   - Is the composite agent better than individual specialists?
   - What's the single biggest strength?
   - What's the single biggest weakness?
```

**What to Look For:**
- Can Claude activate and understand the persona immediately?
- Does the demonstrated example show appropriate expertise?
- Does the composite feel cohesive or fragmented?
- Any contradictions between different specialists?

---

### Prompt Template 3: Specialist Verification

**When:** Use for Database, Data Science (lower scores)
**Time:** 3-4 minutes per agent

```
This composite agent was auto-generated and includes these specialists:

[LIST SPECIALISTS FROM AGENT]

I scored this agent 7.6/10 because I noticed some specialist mismatches.

Please analyze the specialist selection:

1. Domain Alignment
   - For this agent's purpose, which specialists are PERFECT fits?
   - Which specialists are GOOD but not ideal?
   - Which specialists seem TANGENTIAL or off-topic?

2. Coverage Assessment
   - What's the agent STRONG at?
   - What's the agent WEAK at?
   - What expertise is MISSING?

3. Improvement Suggestions
   - If you could replace one specialist, which would it be?
   - What specialist would you ADD?
   - Should we remove any specialists?

4. Overall Verdict
   - Is this agent acceptable as-is? (yes/no/mostly)
   - Would users accept it without customization? (1-10 confidence)
   - What would users likely customize?
```

**What to Look For:**
- Confirmation of observed specialist mismatch
- Specific recommendations for improvements
- Assessment of whether agent is "good enough" as-is
- Clarity on what users would need to change

---

## Test Execution Steps

### Step 1: Copy Agent 1 to Claude

1. Open `/home/ob/Development/Tools/vibe-tools/agent-discovery-system/output/ultimate-security.agent.md`
2. Copy entire content
3. Go to Claude (claude.ai)
4. Start new conversation
5. Paste content
6. Use Prompt Template 1: "Overall Quality Assessment"

### Step 2: Copy Agent 2 (DevOps) to Claude

1. Open `qa_test_output/ultimate-devops.agent.md`
2. Copy entire content
3. New Claude conversation
4. Paste content
5. Use Prompt Template 2: "Activation & Persona Test"
6. Then use Prompt Template 1 for full assessment

### Step 3: Copy Agent 3 (Database) to Claude

1. Open `qa_test_output/ultimate-database.agent.md`
2. Copy entire content
3. New Claude conversation
4. Use Prompt Template 3: "Specialist Verification"
5. Then Prompt Template 1 for overall quality

### Step 4: Copy Agent 4 (Data Science) to Claude

1. Open `qa_test_output/ultimate-data science.agent.md` (note space in filename)
2. Copy entire content
3. New Claude conversation
4. Use Prompt Template 3: "Specialist Verification"
5. Focus on: Is this BI or ML? Should it be renamed?

### Step 5: Copy Agent 5 (Frontend) to Claude

1. Open `qa_test_output/ultimate-frontend.agent.md`
2. Copy entire content
3. New Claude conversation
4. Use Prompt Template 1 for assessment
5. Ask specifically: "The backend architect specialist seems off-topic. Does this hurt the agent?"

---

## Expected Findings

### Security Agent (9.1/10)
Expected: Excellent results
- Activation: Immediate, natural
- Specialist fit: All 5 directly security-related
- Usability: 9+/10
- Issues: None expected
- Confirmation: This is a production-ready baseline

### DevOps Agent (9.3/10)
Expected: Excellent results
- Activation: Clear, strong persona
- Specialist fit: All 5 DevOps-related
- Usability: 9+/10
- Issues: None expected
- Confirmation: This demonstrates peak quality

### Database Agent (7.6/10)
Expected: Usable but with observations
- Activation: Works but persona unclear
- Specialist fit: BI experts don't align with "Database" title
- Usability: 7-8/10
- Issues: "Should this be Ultimate-Analytics instead?"
- Confirmation: Fair-scored agents still usable

### Data Science Agent (7.9/10)
Expected: Works but needs clarification
- Activation: Works but feels like Analytics
- Specialist fit: All Power BI, no ML experts
- Usability: Depends on user expectations
- Issues: Title/content mismatch (BI vs ML)
- Recommendation: Rename to "Ultimate-Analytics" or retool

### Frontend Agent (8.0/10)
Expected: Good, with minor mismatch noted
- Activation: Works well
- Specialist fit: 4/5 perfect, 1 off-topic (backend)
- Usability: 8+/10
- Issues: Backend architect specialist seems like retrieval artifact
- Verdict: Still very usable despite mismatch

---

## Success Criteria

### PASS Criteria (Production Ready)
- ✅ All 5 agents activate successfully in Claude
- ✅ All agents score 7+/10 on overall quality assessment
- ✅ Claude feedback confirms usability for stated purpose
- ✅ No critical issues or contradictions identified
- ✅ Users would accept agents as-is without major changes

### WATCH Criteria (Monitor)
- ⚠️ Database/Data Science agents get 7-8/10 (expected, fair quality)
- ⚠️ Claude identifies specialist mismatches (expected, noted in scoring)
- ⚠️ Recommendations for naming/titling clarifications (expected)

### FAIL Criteria (Stop Release)
- ❌ Any agent scores <7/10 on practical usability
- ❌ Claude identifies contradictory instructions
- ❌ Activation fails or persona is unclear
- ❌ Hallucinated specialists or wrong content
- ❌ Format issues that break agent functionality

---

## Recording Results

### Template for Each Agent Test

```
## Agent: [Ultimate-Name]

### Prompt Template Used
[Which template: 1, 2, or 3]

### Claude Ratings

| Dimension | Score | Notes |
|-----------|-------|-------|
| [Criterion 1] | _/10 | |
| [Criterion 2] | _/10 | |
| [Criterion 3] | _/10 | |
| Overall | _/10 | |

### Key Findings
- Strength 1:
- Strength 2:
- Issue 1 (if any):
- Recommendation (if any):

### Pass/Fail
- Production Ready: YES / NEEDS REFINEMENT / NO
- Confidence: [HIGH / MEDIUM / LOW]

### Claude's Verdict
[Paste Claude's overall assessment or key quote]
```

---

## Time Estimate

- Agent 1 (Security): 3 minutes
- Agent 2 (DevOps): 5 minutes (longer template)
- Agent 3 (Database): 4 minutes
- Agent 4 (Data Science): 4 minutes
- Agent 5 (Frontend): 3 minutes
- **Total: ~20 minutes** (tests can run in parallel or sequentially)

---

## Integration with Final Report

After Claude validation, compile results into final report:

1. **Validation Results Summary**
   - All agents tested: ✅
   - Pass rate: X/5 agents
   - Average Claude quality score: X.X/10

2. **Individual Agent Results**
   - Each agent's Claude feedback
   - Any issues identified
   - Recommendations for improvement

3. **Overall Conclusion**
   - Production readiness: ✅ GO / ❌ NO-GO
   - Confidence level: HIGH (8.5+/10) / MEDIUM / LOW
   - Recommendation: Release now / Test more / Refine first

4. **Phase 2B Summary**
   - Automated scoring: 8.55/10 average
   - Claude validation: Results
   - Combined verdict: PRODUCTION READY

---

## Notes for Claude Testing

- Copy entire agent definition including YAML frontmatter
- Let Claude read full content before asking questions
- Be specific about dimension ratings (1-10 not just "good/bad")
- Record Claude's specific feedback, not just scores
- Use multiple test conversations (one per agent) for clarity

---

**Status:** Ready for Claude validation
**Next:** Copy agents to Claude and run through prompts
**Final Step:** Compile results into Phase 2B QA Report
