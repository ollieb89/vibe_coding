---
title: Prompt Template Library
source: llm-application-dev/skills/prompt-engineering-patterns/assets/prompt-template-library.md
---

## Classification Insights
- Primary Category: reference (confidence: 0.52)
- Secondary Category: howto (confidence: 0.43)
- Key Features: api_patterns (0.15), code_examples (0.30)

---

## Prompt Template Library

A collection of templates for various NLP tasks, including classification, extraction, generation, transformation, analysis, question answering, and specialized tasks. These templates can be used to create prompt responses for a variety of applications.

## Template Structure
```markdown
<!--
TEMPLATE CONTRACT
Required: [Title, Description, Configuration Options, Content Sections, Output Format]
Optional: [Success Criteria]
Never Include: [Tutorial-style steps unless describing a workflow]
-->

---
type: reference
---

# {{ title }}

{{ description }}

## Configuration Options
<!-- Arguments or flags -->
- `{{ option_name }}`: {{ description }}

## {{ section_name }}
<!-- Can be Phase 1, or a Topic -->
{{ section_content }}

## Output Format / Reports
{{ output_description }}

## Success Criteria
- {{ criterion_1 }}

```

---

# Prompt Template Library

A library of templates for various NLP tasks, including classification, extraction, generation, transformation, analysis, question answering, and specialized tasks. These templates can be used to create prompt responses for a variety of applications.

## Classification Templates

### Sentiment Analysis
```
Classify the sentiment of the following text as Positive, Negative, or Neutral.

Text: {text}

Sentiment:
```

### Intent Detection
```
Determine the user's intent from the following message.

Possible intents: {intent_list}

Message: {message}

Intent:
```

### Topic Classification
```
Classify the following article into one of these categories: {categories}

Article:
{article}

Category:
```

## Extraction Templates

### Named Entity Recognition
```
Extract all named entities from the text and categorize them.

Text: {text}

Entities (JSON format):
{
  "persons": [],
  "organizations": [],
  "locations": [],
  "dates": []
}
```

### Structured Data Extraction
```
Extract structured information from the job posting.

Job Posting:
{posting}

Extracted Information (JSON):
{
  "title": "",
  "company": "",
  "location": "",
  "salary_range": "",
  "requirements": [],
  "responsibilities": []
}
```

## Generation Templates

### Email Generation
```
Write a professional {email_type} email.

To: {recipient}
Context: {context}
Key points to include:
{key_points}

Email:
Subject:
Body:
```

### Code Generation
```
Generate {language} code for the following task:

Task: {task_description}

Requirements:
{requirements}

Include:
- Error handling
- Input validation
- Inline comments

Code:
```

### Creative Writing
```
Write a {length}-word {style} story about {topic}.

Include these elements:
- {element_1}
- {element_2}
- {element_3}

Story:
```

## Transformation Templates

### Summarization
```
Summarize the following text in {num_sentences} sentences.

Text:
{text}

Summary:
```

### Translation with Context
```
Translate the following {source_lang} text to {target_lang}.

Context: {context}
Tone: {tone}

Text: {text}

Translation:
```

### Format Conversion
```
Convert the following {source_format} to {target_format}.

Input:
{input_data}

Output ({target_format}):
```

## Analysis Templates

### Code Review
```
Review the following code for:
1. Bugs and errors
2. Performance issues
3. Security vulnerabilities
4. Best practice violations

Code:
{code}

Review:
```

### SWOT Analysis
```
Conduct a SWOT analysis for: {subject}

Context: {context}

Analysis:
Strengths:
-

Weaknesses:
-

Opportunities:
-

Threats:
-
```

## Question Answering Templates

### RAG Template
```
Answer the question based on the provided context. If the context doesn't contain enough information, say so.

Context:
{context}

Question: {question}

Answer:
```

### Multi-Turn Q&A
```
Previous conversation:
{conversation_history}

New question: {question}

Answer (continue naturally from conversation):
```

## Specialized Templates

### SQL Query Generation
```
Generate a SQL query for the following request.

Database schema:
{schema}

Request: {request}

SQL Query:
```

### Regex Pattern Creation
```
Create a regex pattern to match: {requirement}

Test cases that should match:
{positive_examples}

Test cases that should NOT match:
{negative_examples}

Regex pattern:
```

### API Documentation
```
Generate API documentation for this function:

Code:
{function_code}

Documentation (follow {doc_format} format):
```

## Use these templates by filling in the {variables}

[source: llm-application-dev/skills/prompt-engineering-patterns/assets/prompt-template-library.md]