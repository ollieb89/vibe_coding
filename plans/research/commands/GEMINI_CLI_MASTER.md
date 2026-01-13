# GEMINI CLI PLUGINS, EXTENSIONS & AGENTS - MASTER GUIDE

> **Research Date:** January 13, 2026  
> **Coverage:** 287+ Extensions | 100+ Agent Patterns | 1,000+ Commands  
> **Sources Analyzed:** 104 web sources, 15+ GitHub repositories

---

## TABLE OF CONTENTS

### PART 1: EXTENSIONS & PLUGINS
1. [Introduction to Gemini CLI Extensions](#introduction)
2. [Installation & Management](#installation--management)
3. [Official Google Extensions](#official-google-extensions) (10)
4. [Development & Code Review](#development--code-review) (10)
5. [Cloud & Infrastructure](#cloud--infrastructure) (9)
6. [Database & Data](#database--data) (9)
7. [Security & Quality](#security--quality) (4)
8. [Design & Frontend](#design--frontend) (3)
9. [AI & ML](#ai--ml) (8)
10. [Productivity & Workflow](#productivity--workflow) (9)
11. [Communication & Collaboration](#communication--collaboration) (7)
12. [Additional Notable Extensions](#additional-notable-extensions) (10)

### PART 2: CUSTOM COMMANDS & WORKFLOWS
13. [Understanding Custom Commands](#understanding-custom-commands)
14. [Command Syntax & Patterns](#command-syntax--patterns)
15. [Essential Command Examples](#essential-command-examples) (15+)
16. [MCP Prompts as Commands](#mcp-prompts-as-commands)
17. [Best Practices](#command-best-practices)

### PART 3: AGENTS & ORCHESTRATION
18. [Gemini CLI Agent Architecture](#gemini-cli-agent-architecture)
19. [Google ADK (Agent Development Kit)](#google-adk-agent-development-kit)
20. [Multi-Agent Orchestration Patterns](#multi-agent-orchestration-patterns)
21. [Custom Agent Implementation](#custom-agent-implementation)
22. [Advanced Agent Workflows](#advanced-agent-workflows)

### PART 4: REFERENCE
23. [Core Features & Built-in Tools](#core-features--built-in-tools)
24. [Configuration Guide](#configuration-guide)
25. [Comparison: Gemini CLI vs Claude Code](#comparison-gemini-cli-vs-claude-code)
26. [Resources & Community](#resources--community)

---

# PART 1: EXTENSIONS & PLUGINS

## INTRODUCTION

### What Are Gemini CLI Extensions?

Gemini CLI extensions are **modular packages** that enhance the functionality of Google's command-line AI assistant. Each extension can bundle:

- **MCP Servers** - Model Context Protocol servers for external tool integration
- **Custom Commands** - Slash commands for common workflows  
- **Context Files** - Documentation and best practices (GEMINI.md)
- **Hooks** - Automated event-driven actions
- **Tools** - Specialized capabilities (databases, APIs, services)

### Key Benefits

| Benefit | Description |
|---------|-------------|
| **1M Token Context** | Massive context window (5x larger than competitors) |
| **Free Tier** | 1,000 requests/day with personal Google account |
| **One-Command Install** | `gemini extensions install <github-url>` |
| **Open Source** | Full transparency and customization |
| **287+ Extensions** | Largest growing ecosystem |
| **MCP Native** | Full Model Context Protocol support |
| **GitHub Actions** | Native CI/CD integration |

### Extension Architecture

```
Gemini CLI Core
    ├── MCP Servers (external tool connections)
    ├── Custom Commands (slash commands)
    ├── Context Files (GEMINI.md knowledge)
    └── Hooks (automation triggers)
```

---

## INSTALLATION & MANAGEMENT

### Installation

**Basic Install:**
```bash
gemini extensions install https://github.com/[owner]/[repo]
```

**Install with Alias:**
```bash
gemini extensions install https://github.com/gemini-cli-extensions/firebase --alias fb
```

**Install Multiple:**
```bash
gemini extensions install \
  https://github.com/gemini-cli-extensions/firebase \
  https://github.com/github/github-mcp-server \
  https://github.com/gemini-cli-extensions/security
```

### Management Commands

| Command | Description |
|---------|-------------|
| `gemini extensions list` | List all installed extensions |
| `gemini extensions search <keyword>` | Search extension marketplace |
| `gemini extensions info <name>` | View extension details |
| `gemini extensions update <name>` | Update specific extension |
| `gemini extensions update --all` | Update all extensions |
| `gemini extensions enable <name>` | Enable extension |
| `gemini extensions disable <name>` | Disable extension globally |
| `gemini extensions disable <name> --scope=workspace` | Disable for current workspace |
| `gemini extensions uninstall <name>` | Remove extension |
| `gemini extensions new <name> <type>` | Create extension template |

### In-CLI Commands

```bash
/extensions list        # View installed extensions
/extensions enable <name>   # Enable extension
/mcp                   # View MCP server status and tools
/mcp restart <server>  # Restart MCP server
```

### Session-Specific Activation

```bash
# Activate only specific extensions for current session
gemini --extensions firebase,github,security

# Run with single extension
gemini -e firebase -p "Deploy my app"
```

---

## OFFICIAL GOOGLE EXTENSIONS

### 1. Firebase Extension ⭐
**Repository:** https://github.com/gemini-cli-extensions/firebase  
**Stars:** 98  
**Category:** Backend Infrastructure  
**Install:** `gemini extensions install https://github.com/gemini-cli-extensions/firebase`

**Commands:**
- `/firebase:init` - Setup Firebase project (AI Logic, Firestore, Auth)
- `/firebase:deploy` - Deploy to Cloud Run or App Hosting
- `/firebase:consult` - Get Firebase best practices

**Key Features:**
- Automated service configuration
- Firebase AI Logic implementation
- Firestore collection management
- Authentication setup
- Intelligent hosting selection (auto-detects Cloud Run vs App Hosting)

**Example Workflow:**
```bash
gemini -e firebase -p "/firebase:init with Firestore and Auth"
# AI configures entire backend

gemini -e firebase -p "/firebase:deploy to production"
# AI builds, deploys, configures hosting
```

**Use Cases:**
- Full-stack app backend setup
- AI chat feature integration
- Database and auth scaffolding
- Production deployment automation

---

### 2. Cloud Run Extension
**Repository:** https://github.com/GoogleCloudPlatform/cloud-run-mcp  
**Stars:** 512  
**Install:** `gemini extensions install https://github.com/GoogleCloudPlatform/cloud-run-mcp`

**Commands:**
- `/deploy` - Full CI/CD pipeline to Cloud Run

**What It Does:**
- Automated containerization (Dockerfile generation)
- Image building and pushing to Artifact Registry
- Cloud Run service configuration
- Environment variable management
- Traffic routing and scaling

**Example:**
```bash
gemini -e cloud-run -p "Deploy this Node.js app to Cloud Run with 2GB memory"
```

---

### 3. GKE (Google Kubernetes Engine) Extension
**Repository:** https://github.com/GoogleCloudPlatform/gke-mcp  
**Stars:** 106  
**Install:** `gemini extensions install https://github.com/GoogleCloudPlatform/gke-mcp`

**Capabilities:**
- Create and manage GKE clusters
- Deploy and scale Kubernetes workloads
- Query cluster status and resources
- Manage namespaces and services
- Configure autoscaling policies

---

### 4. Google Workspace Extension ⭐
**Repository:** https://github.com/gemini-cli-extensions/workspace  
**Stars:** 222  
**Install:** `gemini extensions install https://github.com/gemini-cli-extensions/workspace`

**MCP Tools Provided:**
- `read_google_doc`, `write_google_doc`, `update_google_doc`
- `send_email`, `search_emails`, `read_email`
- `create_calendar_event`, `list_calendar_events`
- `read_sheet`, `write_sheet`, `query_sheet`
- `search_drive`, `upload_file`, `download_file`

**Use Cases:**
- **Automated Reporting:** Generate docs with data from Sheets
- **Email Workflows:** Send templated emails with attachments
- **Meeting Scheduling:** AI-powered calendar management
- **Data Analysis:** Query Sheets, generate insights in Docs

**Example:**
```bash
gemini -e workspace -p "Create a weekly report doc summarizing data from Q1 Sales Sheet"
```

---

### 5. Google Workspace Developer Tools
**Repository:** https://github.com/googleworkspace/developer-tools  
**Stars:** 56  
**Install:** `gemini extensions install https://github.com/googleworkspace/developer-tools`

**Focus:** Developer-centric Workspace operations
- Build Workspace add-ons
- Access Workspace APIs with AI guidance
- Develop Apps Script integrations
- Grounded documentation context

---

### 6. CLASP (Google Apps Script CLI)
**Repository:** https://github.com/google/clasp  
**Stars:** 5,406  
**Install:** `gemini extensions install https://github.com/google/clasp`

**Commands:**
- `clasp create` - Create Apps Script project
- `clasp push` - Upload local code to Apps Script
- `clasp deploy` - Create deployment version
- `clasp logs` - View execution logs

**AI Integration:**
- Generate Apps Script code with Gemini
- Deploy and test automatically
- Debug script errors

---

### 7. Google Cloud Assist
**Repository:** https://github.com/GoogleCloudPlatform/gemini-cloud-assist-mcp  
**Stars:** 46  
**Install:** `gemini extensions install https://github.com/GoogleCloudPlatform/gemini-cloud-assist-mcp`

**Purpose:** General GCP assistance
- Cloud resource management guidance
- GCP best practices
- Service recommendations
- Cost optimization suggestions

---

### 8. GCloud Extension
**Repository:** https://github.com/gemini-cli-extensions/gcloud  
**Stars:** 35  
**Install:** `gemini extensions install https://github.com/gemini-cli-extensions/gcloud`

**Capabilities:**
- Execute gcloud CLI commands via MCP
- Manage projects, IAM, resources
- Query resource metadata
- Configure services

---

### 9. Google Maps Platform
**Repository:** https://github.com/googlemaps/platform-ai  
**Stars:** 75  
**Install:** `gemini extensions install https://github.com/googlemaps/platform-ai`

**Features:**
- Access Maps Platform documentation
- Generate code for geocoding, directions, places
- Implement map visualizations
- Distance Matrix API integration

**Example:**
```bash
gemini -e maps -p "Generate code to find coffee shops within 1 mile of user location"
```

---

### 10. BigQuery Data Analytics
**Repository:** https://github.com/gemini-cli-extensions/bigquery-data-analytics  
**Install:** `gemini extensions install https://github.com/gemini-cli-extensions/bigquery-data-analytics`

**Capabilities:**
- Natural language to SQL translation
- Query BigQuery datasets
- Generate data insights and visualizations
- Build data pipelines
- Schema exploration

**Example:**
```bash
gemini -e bigquery -p "What were total sales by region last quarter?"
# AI generates SQL, executes query, formats results
```

---

## DEVELOPMENT & CODE REVIEW

### 11. GitHub Official Extension ⭐
**Repository:** https://github.com/github/github-mcp-server  
**Stars:** 25,843 (Most popular MCP server)  
**Install:** `gemini extensions install https://github.com/github/github-mcp-server`

**Commands:**
- `/gemini summary` - Generate PR summary
- `/gemini review` - Perform code review
- `@gemini-cli` - Mention in issues/PRs to delegate tasks

**MCP Tools:**
- `create_or_update_file`, `push_files`, `create_branch`
- `create_pull_request`, `create_issue`, `add_issue_comment`
- `search_repositories`, `get_file_contents`, `list_commits`
- `fork_repository`, `create_repository`

**GitHub Actions Integration:**
```yaml
- uses: google-github-actions/run-gemini-cli@v1
  with:
    prompt: "Review this PR for security issues"
    extensions: github,security
```

**Use Cases:**
- **Automated PR Reviews:** Code quality, security, best practices
- **Issue Triage:** Auto-label, prioritize, assign issues
- **Feature Implementation:** "@gemini-cli implement user authentication"
- **Documentation:** Generate README, API docs from code

**Example:**
```bash
gemini -e github -p "Review PR #123 focusing on performance and security"
```

---

### 12. Code Review Extension (Google) ⭐
**Repository:** https://github.com/gemini-cli-extensions/code-review  
**Stars:** 284  
**Install:** `gemini extensions install https://github.com/gemini-cli-extensions/code-review`

**Command:** `/code-review`

**Review Checklist:**
- Code clarity and readability
- Function and variable naming
- Code duplication
- Error handling
- Security vulnerabilities (secrets, injection)
- Input validation
- Test coverage
- Performance considerations
- Best practices compliance

**YOLO Mode (Non-Interactive):**
```bash
gemini "/code-review" --yolo -e code-review > code-review.md
```

**Output Format:**
- Critical Issues (must fix)
- Warnings (should fix)
- Suggestions (consider)
- Line-specific feedback with examples

---

### 13. Security Extension (Google) ⭐
**Repository:** https://github.com/gemini-cli-extensions/security  
**Stars:** 340  
**Install:** `gemini extensions install https://github.com/gemini-cli-extensions/security`

**Command:** `/security:analyze`

**Vulnerability Detection:**
- SQL injection
- XSS (Cross-site scripting)
- Hardcoded secrets (API keys, passwords)
- Authentication flaws
- Authorization issues (broken access control)
- Insecure data handling
- CSRF vulnerabilities
- Insecure deserialization

**Output:**
- Creates `.gemini_security/` directory
- Generates `security-analysis.md` report
- Severity ratings (Critical/High/Medium/Low)
- Remediation recommendations

**Example:**
```bash
gemini -e security --yolo -p "/security:analyze" > security-report.md
```

---

### 14. Jules Extension (Autonomous Agent)
**Repository:** https://github.com/gemini-cli-extensions/jules  
**Stars:** 271  
**Install:** `gemini extensions install https://github.com/gemini-cli-extensions/jules`

**Purpose:** Asynchronous task execution
- Long-running bug fixes
- Refactoring large codebases
- Dependency updates
- Background maintenance tasks

**Usage:**
```bash
gemini -e jules -p "Refactor authentication module to use JWT tokens" &
# Runs in background while you work
```

---

### 15. Conductor Extension
**Repository:** https://github.com/gemini-cli-extensions/conductor  
**Stars:** 1,519  
**Install:** `gemini extensions install https://github.com/gemini-cli-extensions/conductor`

**Purpose:** Feature planning and orchestration
- Specify features with natural language
- AI generates implementation plan
- Breaks down complex features into tasks
- Coordinates execution across tools

---

### 16. Blueprint Extension
**Repository:** https://github.com/gplasky/gemini-cli-blueprint-extension  
**Stars:** 49  
**Install:** `gemini extensions install https://github.com/gplasky/gemini-cli-blueprint-extension`

**Workflow:** Concept → Specification → Implementation
- Structured planning process
- Design documentation generation
- Code scaffolding

---

### 17. Spec-Flow Extension
**Repository:** https://github.com/marcusgoll/Spec-Flow  
**Stars:** 32  
**Install:** `gemini extensions install https://github.com/marcusgoll/Spec-Flow`

**Approach:** Specification-first development
- Write specs in natural language
- AI generates implementation
- Ported from Claude Code skills

---

### 18. Outline Driven Development
**Repository:** https://github.com/OutlineDriven/outline-driven-development  
**Stars:** 31  
**Install:** `gemini extensions install https://github.com/OutlineDriven/outline-driven-development`

**Features:**
- AST (Abstract Syntax Tree) analysis
- Modern CLI tools integration (ripgrep, fd, ast-grep)
- Context engineering for better AI output

---

### 19. Chrome DevTools Extension
**Repository:** https://github.com/ChromeDevTools/chrome-devtools-mcp  
**Stars:** 20,571  
**Install:** `gemini extensions install https://github.com/ChromeDevTools/chrome-devtools-mcp`

**Capabilities:**
- Live browser automation from CLI
- Performance profiling
- Network request inspection
- Console log capture
- Screenshot and PDF generation
- Element inspection

**Example:**
```bash
gemini -e chrome-devtools -p "Run Lighthouse audit on https://example.com"
```

---

### 20. Computer Use Extension
**Repository:** https://github.com/automateyournetwork/GeminiCLI_ComputerUse_Extension  
**Stars:** 55  
**Install:** `gemini extensions install https://github.com/automateyournetwork/GeminiCLI_ComputerUse_Extension`

**Actions:**
- Autonomous web browsing
- Click, type, scroll actions
- Screenshot capture
- Form filling
- PDF generation
- Web testing automation

---

## CLOUD & INFRASTRUCTURE

### 21. Terraform Extension
**Repository:** https://github.com/hashicorp/terraform-mcp-server  
**Stars:** 1,129  
**Install:** `gemini extensions install https://github.com/hashicorp/terraform-mcp-server`

**Capabilities:**
- Generate Terraform configurations from natural language
- Execute `terraform plan`, `terraform apply`
- Manage state files
- Module discovery and usage
- Resource dependency graphing

**Example:**
```bash
gemini -e terraform -p "Create GCP infrastructure: VPC, Cloud SQL, GKE cluster"
```

---

### 22. Kubernetes Extension
**Repository:** https://github.com/Flux159/mcp-server-kubernetes  
**Stars:** 1,257  
**Install:** `gemini extensions install https://github.com/Flux159/mcp-server-kubernetes`

**Features:**
- Cluster management
- Deploy manifests from natural language
- Scale workloads
- Debug pods, services
- View logs and events

---

### 23. Supabase Extension
**Repository:** https://github.com/supabase-community/supabase-mcp  
**Stars:** 2,379  
**Install:** `gemini extensions install https://github.com/supabase-community/supabase-mcp`

**Tools:**
- Create and manage Supabase projects
- Database table operations (create, query, update)
- Authentication setup
- Storage bucket management
- Real-time subscription configuration

---

### 24. Cloud SQL PostgreSQL
**Repository:** https://github.com/gemini-cli-extensions/cloud-sql-postgresql  
**Stars:** 24  
**Install:** `gemini extensions install https://github.com/gemini-cli-extensions/cloud-sql-postgresql`

**Capabilities:**
- Create Cloud SQL instances
- Connect to PostgreSQL databases
- Execute queries with natural language
- Schema migrations

---

### 25. Browserbase Extension
**Repository:** https://github.com/browserbase/mcp-server-browserbase  
**Stars:** 3,044  
**Install:** `gemini extensions install https://github.com/browserbase/mcp-server-browserbase`

**Purpose:** Headless browser automation
- Web scraping at scale
- E2E testing
- Screenshot/PDF generation
- Multi-browser support

---

### 26. Vercel Extension
**What It Does:**
- Deploy to Vercel platform
- Manage serverless functions
- Environment variables
- Preview deployments
- Domain configuration

---

### 27. CloudBase AI Toolkit (Tencent)
**Repository:** https://github.com/TencentCloudBase/CloudBase-MCP  
**Stars:** 926  
**Install:** `gemini extensions install https://github.com/TencentCloudBase/CloudBase-MCP`

**Focus:** Tencent Cloud ecosystem
- Full-stack app deployment
- Mini-program development
- Cloud function management

---

### 28. ACK (Alibaba Cloud Kubernetes)
**Repository:** https://github.com/aliyun/alibabacloud-ack-mcp-server  
**Stars:** 96  
**Install:** `gemini extensions install https://github.com/aliyun/alibabacloud-ack-mcp-server`

**Focus:** Alibaba Cloud containers
- Container-native AIOps
- Natural language infrastructure control

---

### 29. Bitrise Extension
**Repository:** https://github.com/bitrise-io/bitrise-mcp  
**Stars:** 27  
**Install:** `gemini extensions install https://github.com/bitrise-io/bitrise-mcp`

**Purpose:** Mobile CI/CD
- Build management
- Artifact handling
- App deployment workflows

---

## DATABASE & DATA

### 30. MCP Toolbox for Databases ⭐
**Repository:** https://github.com/googleapis/genai-toolbox  
**Stars:** 12,390  
**Install:** `gemini extensions install https://github.com/googleapis/genai-toolbox`

**Supported Databases (30+):**
- **SQL:** PostgreSQL, MySQL, SQLite, Oracle, SQL Server, MariaDB
- **NoSQL:** MongoDB, Redis, Cassandra, Couchbase, DynamoDB
- **Cloud:** BigQuery, Snowflake, Redshift, Azure SQL, Cloud Spanner
- **Graph:** Neo4j, ArangoDB
- **Vector:** Pinecone, Milvus, Weaviate, Qdrant
- **Time-series:** InfluxDB, TimescaleDB
- **And 15+ more**

**Features:**
- Universal database interface
- Natural language to query translation
- Schema exploration
- Query optimization
- Data migration

**Example:**
```bash
gemini -e genai-toolbox -p "Connect to PostgreSQL and find users who signed up last week"
```

---

### 31. PostgreSQL Extension
**Repository:** https://github.com/gemini-cli-extensions/postgres  
**Stars:** 56  
**Install:** `gemini extensions install https://github.com/gemini-cli-extensions/postgres`

**Capabilities:**
- Direct PostgreSQL connections
- Query execution and optimization
- Schema management
- Index analysis
- Data analysis

---

### 32. Redis Extension
**Repository:** https://github.com/redis/mcp-redis  
**Stars:** 384  
**Install:** `gemini extensions install https://github.com/redis/mcp-redis`

**Features:**
- Redis data operations
- Search with RediSearch
- Cache optimization
- Real-time data queries
- Stream processing

---

### 33. Neo4j Extension
**Repository:** https://github.com/neo4j-contrib/mcp-neo4j  
**Stars:** 868  
**Install:** `gemini extensions install https://github.com/neo4j-contrib/mcp-neo4j`

**Capabilities:**
- Cypher query generation
- Graph data analysis
- Relationship exploration
- Pattern matching

---

### 34. Milvus Vector Database
**Repository:** https://github.com/zilliztech/mcp-server-milvus  
**Stars:** 209  
**Install:** `gemini extensions install https://github.com/zilliztech/mcp-server-milvus`

**Use Cases:**
- Vector similarity search
- Embedding management
- Semantic search
- RAG (Retrieval-Augmented Generation) applications

---

### 35. Pinecone Extension
**Repository:** https://github.com/pinecone-io/pinecone-mcp  
**Stars:** 50  
**Install:** `gemini extensions install https://github.com/pinecone-io/pinecone-mcp`

**Features:**
- Vector database operations
- Index management
- Metadata filtering
- Hybrid search

---

### 36. Elasticsearch Extension
**Repository:** https://github.com/elastic/gemini-cli-elasticsearch  
**Stars:** 93  
**Install:** `gemini extensions install https://github.com/elastic/gemini-cli-elasticsearch`

**Capabilities:**
- Full-text search
- Log analysis
- Data aggregations
- Index management

---

### 37. Grafana Extension
**Repository:** https://github.com/grafana/mcp-grafana  
**Stars:** 2,105  
**Install:** `gemini extensions install https://github.com/grafana/mcp-grafana`

**Features:**
- Dashboard creation from natural language
- Metrics visualization
- Alert rule configuration
- Data source queries

---

### 38. Confluent Extension
**Repository:** https://github.com/confluentinc/mcp-confluent  
**Stars:** 129  
**Install:** `gemini extensions install https://github.com/confluentinc/mcp-confluent`

**Capabilities:**
- Kafka topic management
- Stream processing
- Producer/consumer workflows
- Schema registry operations

---

## SECURITY & QUALITY

### 39. SonarQube Extension
**Repository:** https://github.com/SonarSource/sonarqube-mcp-server  
**Stars:** 344  
**Install:** `gemini extensions install https://github.com/SonarSource/sonarqube-mcp-server`

**Analysis:**
- Code quality metrics
- Security vulnerability detection
- Code smell identification
- Technical debt tracking
- Test coverage analysis

**Supports:** SonarQube Server and Cloud

---

### 40. Endor Labs Code Security
**Repository:** https://github.com/endorlabs/gemini-extension  
**Stars:** 66  
**Install:** `gemini extensions install https://github.com/endorlabs/gemini-extension`

**Focus:**
- Real-time security scanning
- Vulnerability remediation
- Secure coding patterns

---

### 41. Snyk Extension
**Capabilities:**
- Dependency vulnerability scanning
- Container security analysis
- Infrastructure as Code scanning
- Real-time security alerts

---

### 42. UUV Testing Framework
**Repository:** https://github.com/e2e-test-quest/uuv  
**Stars:** 135  
**Install:** `gemini extensions install https://github.com/e2e-test-quest/uuv`

**Features:**
- BDD (Behavior-Driven Development)
- E2E test automation
- Accessibility testing
- Test generation from user stories

---

## DESIGN & FRONTEND

### 43. Figma Extension ⭐
**Repository:** https://github.com/figma/figma-gemini-cli-extension  
**Stars:** 81  
**Install:** `gemini extensions install https://github.com/figma/figma-gemini-cli-extension`

**Commands:**
- "Generate React components from Frame 'Product Card'"
- "Convert design to Tailwind CSS"

**Workflow:**
1. Connect to Figma file
2. AI extracts design system (colors, typography, spacing, breakpoints)
3. Generates production-ready code (React + Tailwind)
4. Includes responsive variants

**Example:**
```bash
gemini -e figma -p "Generate React component from Figma frame 'Header' with responsive breakpoints"
```

---

### 44. Flutter Extension
**Repository:** https://github.com/gemini-cli-extensions/flutter  
**Stars:** 345  
**Install:** `gemini extensions install https://github.com/gemini-cli-extensions/flutter`

**Capabilities:**
- Create Flutter apps
- Build and refactor code
- AI-powered debugging
- Dart language support

---

### 45. Genkit Extension
**Repository:** https://github.com/gemini-cli-extensions/genkit  
**Stars:** 144  
**Install:** `gemini extensions install https://github.com/gemini-cli-extensions/genkit`

**Purpose:** Build AI-powered apps with Genkit framework

---

## AI & ML

### 46. Nano Banana Extension
**Repository:** https://github.com/gemini-cli-extensions/nanobanana  
**Stars:** 679  
**Install:** `gemini extensions install https://github.com/gemini-cli-extensions/nanobanana`

**Features:**
- Text-to-image generation
- Image manipulation
- Terminal-based image creation

---

### 47. Vision Extension
**Repository:** https://github.com/automateyournetwork/GeminiCLI_Vision_Extension  
**Stars:** 37  
**Install:** `gemini extensions install https://github.com/automateyournetwork/GeminiCLI_Vision_Extension`

**Modes:**
- Webcam/iPhone camera integration
- ASL (American Sign Language) recognition
- Nano Banana image generation
- Veo3 video processing

---

### 48. Hugging Face Hub Extension
**Repository:** https://github.com/huggingface/hf-mcp-server  
**Stars:** 181  
**Install:** `gemini extensions install https://github.com/huggingface/hf-mcp-server`

**Capabilities:**
- Model discovery and testing
- Dataset exploration
- Model deployment
- Inference API access

---

### 49. Hugging Face Skills Extension
**Repository:** https://github.com/huggingface/skills  
**Stars:** 880  
**Install:** `gemini extensions install https://github.com/huggingface/skills`

**Features:**
- Pre-built AI workflows
- Model fine-tuning
- Pipeline creation

---

### 50. ElevenLabs Extension
**Repository:** https://github.com/elevenlabs/elevenlabs-mcp  
**Stars:** 1,145  
**Install:** `gemini extensions install https://github.com/elevenlabs/elevenlabs-mcp`

**Capabilities:**
- Text-to-speech generation
- Voice design and cloning
- Conversational AI
- Sound effects and music

---

### 51. Open Aware (Qodo AI)
**Repository:** https://github.com/qodo-ai/open-aware  
**Stars:** 413  
**Install:** `gemini extensions install https://github.com/qodo-ai/open-aware`

**Purpose:** Deep code research agent
- Complex codebase understanding
- Architectural analysis
- Knowledge synthesis

---

### 52. Skillz Extension
**Repository:** https://github.com/intellectronica/gemini-cli-skillz  
**Stars:** 48  
**Install:** `gemini extensions install https://github.com/intellectronica/gemini-cli-skillz`

**Feature:** Load Claude-style skills into Gemini CLI

---

### 53. Skill Porter
**Repository:** https://github.com/jduncan-rva/skill-porter  
**Stars:** 71  
**Install:** `gemini extensions install https://github.com/jduncan-rva/skill-porter`

**Purpose:** Convert between Claude Code and Gemini CLI formats

---

## PRODUCTIVITY & WORKFLOW

### 54. Context7 Extension ⭐
**Repository:** https://github.com/upstash/context7  
**Stars:** 41,690  
**Install:** `gemini extensions install https://github.com/upstash/context7`

**Purpose:** Up-to-date code documentation for AI

---

### 55. DocFork Extension
**Repository:** https://github.com/docfork/docfork  
**Stars:** 374  
**Install:** `gemini extensions install https://github.com/docfork/docfork`

**Purpose:** Real-time API documentation access

---

### 56. Gemini Docs Extension
**Repository:** https://github.com/markmcd/gemini-docs-ext  
**Stars:** 48  
**Install:** `gemini extensions install https://github.com/markmcd/gemini-docs-ext`

**Purpose:** Gemini API documentation in CLI

---

### 57. Gemini Prompt Library ⭐
**Repository:** https://github.com/harish-garg/gemini-cli-prompt-library  
**Stars:** 220  
**Install:** `gemini extensions install https://github.com/harish-garg/gemini-cli-prompt-library`

**Categories (30+ prompts):**
- Code review (security, performance, best practices)
- Testing (unit, integration, e2e)
- Documentation (README, API docs)
- Learning (concept explanations)
- Refactoring patterns

**Commands:**
- `/code-review:security`
- `/testing:generate-unit-tests`
- `/docs:write-readme`
- `/learning:explain-concept`

---

### 58. Gemini Flow Extension
**Repository:** https://github.com/clduab11/gemini-flow  
**Stars:** 326  
**Install:** `gemini extensions install https://github.com/clduab11/gemini-flow`

**Features:** 9 MCP servers bundled for orchestration

---

### 59. Gemini AutoPM
**Repository:** https://github.com/rafeekpro/GeminiAutoPM  
**Stars:** 13  
**Install:** `gemini extensions install https://github.com/rafeekpro/GeminiAutoPM`

**Purpose:** Intelligent project management automation

---

### 60. Ralph Wiggum Extension
**Repository:** https://github.com/AsyncFuncAI/ralph-wiggum-extension  
**Stars:** 34  
**Install:** `gemini extensions install https://github.com/AsyncFuncAI/ralph-wiggum-extension`

**Purpose:** Humor-themed personality mode

---

### 61. Critical Think Extension
**Repository:** https://github.com/abagames/slash-criticalthink  
**Stars:** 75  
**Install:** `gemini extensions install https://github.com/abagames/slash-criticalthink`

**Command:** `/criticalthink`

**Purpose:** Enable skeptical analysis to counter confirmation bias

---

## COMMUNICATION & COLLABORATION

### 62. Atlassian Rovo (Jira/Confluence)
**Repository:** https://github.com/atlassian/atlassian-mcp-server  
**Stars:** 193  
**Install:** `gemini extensions install https://github.com/atlassian/atlassian-mcp-server`

**Capabilities:**
- Manage Jira issues and tickets
- Create/update Confluence documentation
- Search across Atlassian products
- Sprint planning automation

---

### 63. Monday.com Extension
**Repository:** https://github.com/mondaycom/mcp  
**Stars:** 359  
**Install:** `gemini extensions install https://github.com/mondaycom/mcp`

**Features:**
- Project management automation
- Task tracking
- Workflow management

---

### 64. Postman Extension
**Repository:** https://github.com/postmanlabs/postman-mcp-server  
**Stars:** 145  
**Install:** `gemini extensions install https://github.com/postmanlabs/postman-mcp-server`

**Capabilities:**
- Test API endpoints
- Generate API documentation
- Collection management

---

### 65. Slack Extension
**Capabilities:**
- Send messages and notifications
- Channel management
- File sharing
- Workflow automation

---

### 66. Notion Extension
**Features:**
- Database queries
- Page creation/updates
- Note management

---

### 67. Linear Extension
**Features:**
- Issue management
- Project tracking
- Sprint planning

---

### 68. Asana Extension
**Features:**
- Task management
- Team coordination

---

## ADDITIONAL NOTABLE EXTENSIONS

### 69. Stripe Extension
**Repository:** https://github.com/stripe/ai  
**Stars:** 1,192  
**Install:** `gemini extensions install https://github.com/stripe/ai`

**Capabilities:**
- Payment integration automation
- Subscription management
- Billing workflows

---

### 70. Shopify Extension
**Features:**
- E-commerce automation
- Shopify API operations

---

### 71. Sentry Extension
**Features:**
- Error monitoring
- Performance tracking

---

### 72. Dynatrace Extension
**Repository:** https://github.com/dynatrace-oss/dynatrace-mcp  
**Stars:** 189  
**Install:** `gemini extensions install https://github.com/dynatrace-oss/dynatrace-mcp`

**Features:**
- Application performance monitoring
- Root-cause analysis

---

### 73. ThoughtSpot Extension
**Repository:** https://github.com/thoughtspot/mcp-server  
**Stars:** 24  
**Install:** `gemini extensions install https://github.com/thoughtspot/mcp-server`

**Purpose:** Business intelligence queries

---

### 74. Globalping Extension
**Repository:** https://github.com/jsdelivr/globalping-mcp-server  
**Stars:** 38  
**Install:** `gemini extensions install https://github.com/jsdelivr/globalping-mcp-server`

**Purpose:** Global network measurements

---

### 75. Exa Search Extension
**Repository:** https://github.com/exa-labs/exa-mcp-server  
**Stars:** 3,536  
**Install:** `gemini extensions install https://github.com/exa-labs/exa-mcp-server`

**Purpose:** AI-powered web search and crawling

---

### 76. Google Ads API Extension
**Repository:** https://github.com/googleads/google-ads-api-developer-assistant  
**Stars:** 24  
**Install:** `gemini extensions install https://github.com/googleads/google-ads-api-developer-assistant`

**Purpose:** Google Ads campaign management

---

### 77. IPSW Skill (Apple Firmware)
**Repository:** https://github.com/blacktop/ipsw-skill  
**Stars:** 31  
**Install:** `gemini extensions install https://github.com/blacktop/ipsw-skill`

**Purpose:** Apple firmware analysis

---

### 78. Google ADK Agent Extension
**Repository:** https://github.com/simonliu-ai-product/adk-agent-extension  
**Stars:** 38  
**Install:** `gemini extensions install https://github.com/simonliu-ai-product/adk-agent-extension`

**Commands:**
- `list_adks`, `list_adk_agents`
- `create_session`, `send_message_to_agent`

**Purpose:** Control deployed ADK agents from Gemini CLI

---

# PART 2: CUSTOM COMMANDS & WORKFLOWS

## UNDERSTANDING CUSTOM COMMANDS

### What Are Custom Commands?

Custom commands are **reusable prompt templates** saved as `.toml` files that create personalized slash commands.

**Benefits:**
- ✅ Reusable prompts for common workflows
- ✅ Team collaboration (commit to Git)
- ✅ Consistency across projects
- ✅ Automation ready (CI/CD, scripts)
- ✅ Namespace organization

### Command Scopes

| Scope | Location | Availability |
|-------|----------|--------------|
| **Global** | `~/.gemini/commands/` | All projects |
| **Project** | `.gemini/commands/` | Current project only |
| **Session** | `--commands` CLI flag | Current session only |

### Naming Conventions

| File Path | Command | Notes |
|-----------|---------|-------|
| `~/.gemini/commands/test.toml` | `/test` | Global command |
| `~/.gemini/commands/git/commit.toml` | `/git:commit` | Namespaced |
| `.gemini/commands/review.toml` | `/review` | Project-specific |
| `~/.gemini/commands/db/migrate.toml` | `/db:migrate` | Nested namespace |

---

## COMMAND SYNTAX & PATTERNS

### Basic Structure

```toml
description = "One-line description shown in /help"
prompt = """
Your detailed prompt here.
Multi-line supported.
"""
```

### With Arguments

```toml
description = "Deploy to environment"
prompt = "Deploy the application to {{args}} environment with proper configuration"
```

**Usage:** `/deploy staging`

---

### Positional Arguments

```toml
description = "Review pull request"
argument-hint = "[pr-number] [focus-area]"
prompt = "Review PR #$1 focusing on $2"
```

**Usage:** `/review 123 security`

---

### Shell Command Integration

```toml
description = "Generate commit message"
prompt = """
Generate a Conventional Commit message for these changes:

```diff
!{git diff --staged}
```

Format: type(scope): description
"""
```

**Shell Commands Available:**
- `!{git diff}` - Git diff output
- `!{git log -5}` - Recent commits
- `!{npm test}` - Test output
- `!{ls -la}` - Any shell command

---

### File References

```toml
description = "Review implementation"
prompt = "Review the code in @src/auth/login.js focusing on security"
```

**File Reference Syntax:**
- `@filename` - Include file content
- `@folder/` - Include all files in folder
- `@**/*.test.js` - Glob pattern

---

### Multi-Step Workflows

```toml
description = "Complete feature workflow"
prompt = """
Execute this workflow:

1. Create feature branch: feature/{{args}}
2. Implement the feature described in the issue
3. Write unit tests
4. Run test suite
5. Generate commit message
6. Commit changes
7. Create pull request
"""
```

---

## ESSENTIAL COMMAND EXAMPLES

### 1. Smart Commit

**File:** `~/.gemini/commands/git/commit.toml`
```toml
description = "Generate and create commit with Conventional Commits format"
prompt = """
1. Analyze staged changes:
   ```diff
   !{git diff --staged}
   ```

2. Check recent commits for style:
   ```
   !{git log --oneline -5}
   ```

3. Generate Conventional Commit message:
   - Format: type(scope): description
   - Types: feat, fix, docs, style, refactor, test, chore
   - Include breaking changes if applicable

4. Stage all changes if needed
5. Create the commit
"""
```

**Usage:** `/git:commit`

---

### 2. Automated Push Workflow

**File:** `~/.gemini/commands/push.toml`
```toml
description = "Stage all, commit, and push in one command"
prompt = """
Workflow:
1. Stage all changes: git add .
2. Generate Conventional Commit message from diff
3. Commit with generated message
4. Push to current branch on remote

```diff
!{git diff}
```
"""
```

**Usage:** `/push`

---

### 3. Pull Request Creator

**File:** `~/.gemini/commands/pr.toml`
```toml
description = "Create pull request with AI-generated description"
prompt = """
1. Fetch commits on current branch: !{git log main..HEAD --oneline}
2. Generate PR title (50 chars max, imperative mood)
3. Generate PR description:
   - Summary of changes
   - Motivation and context
   - Testing done
   - Related issues
4. Check if PR exists: gh pr list --head $(git branch --show-current)
5. If no PR exists, create: gh pr create --title "..." --body "..."
"""
```

**Usage:** `/pr`

---

### 4. Lint and Auto-Fix

**File:** `~/.gemini/commands/lint.toml`
```toml
description = "Run linter with auto-fix, then fix remaining issues"
prompt = """
1. Run linter with auto-fix enabled
2. If errors remain, analyze and fix in code
3. Use fast model (gemini-2.5-flash-lite) for speed
4. Report summary of fixes made
"""
```

**Usage:** `/lint`

---

### 5. Test Runner and Fixer

**File:** `~/.gemini/commands/test.toml`
```toml
description = "Run tests and fix failures"
prompt = """
1. Run test suite: !{npm test}
2. If failures exist:
   - Analyze stack traces
   - Fix IMPLEMENTATION code (not tests)
   - Tests define expected behavior
3. Re-run tests to verify
4. Report results
"""
```

**Usage:** `/test`

---

### 6. Code Review with Focus

**File:** `.gemini/commands/review.toml`
```toml
description = "Focused code review"
argument-hint = "[focus-area]"
prompt = """
Review current changes focusing on: {{args}}

Check for:
- Code quality issues
- Security vulnerabilities
- Performance problems
- Best practices violations
- {{args}}-specific concerns

```diff
!{git diff}
```

Provide:
- Critical issues (must fix)
- Warnings (should fix)
- Suggestions (consider)
- Line-specific feedback with examples
"""
```

**Usage:** `/review security` or `/review performance`

---

### 7. Feature Branch Creator

**File:** `~/.gemini/commands/branch.toml`
```toml
description = "Create feature branch with proper naming"
prompt = """
1. Convert to kebab-case: {{args}}
2. Create branch: feature/[kebab-case-name]
3. Check out new branch
4. Confirm creation with: git branch --show-current
"""
```

**Usage:** `/branch User Authentication Feature`  
**Result:** `feature/user-authentication-feature`

---

### 8. CI Pipeline Fixer

**File:** `~/.gemini/commands/fix-ci.toml`
```toml
description = "Debug and fix failing CI/CD pipeline"
prompt = """
1. Fetch CI logs: gh run view --log-failed
2. Analyze errors carefully
3. Identify root cause
4. Fix issue in codebase
5. Use advanced model (gemini-2.5-pro) for complex debugging
6. Never propose fixes without reading actual errors
"""
```

**Usage:** `/fix-ci`

---

### 9. Test Generator

**File:** `~/.gemini/commands/test-gen.toml`
```toml
description = "Generate comprehensive tests for file"
prompt = """
Generate tests for: @{{args}}

Include:
1. Unit tests for all exported functions
2. Edge cases and boundary conditions
3. Error handling scenarios
4. Mock external dependencies
5. Use project's testing framework (detect from package.json)
6. Follow project's test file naming convention
"""
```

**Usage:** `/test-gen src/auth/login.js`

---

### 10. API Documentation Generator

**File:** `~/.gemini/commands/docs/api.toml`
```toml
description = "Generate OpenAPI/Swagger documentation"
prompt = """
Generate API documentation for: @{{args}}

Include:
1. Endpoint descriptions
2. Request/response schemas
3. Example payloads (request and response)
4. HTTP status codes
5. Authentication requirements
6. Error response formats
7. OpenAPI 3.0 format
"""
```

**Usage:** `/docs:api src/routes/users.js`

---

### 11. Database Migration Creator

**File:** `.gemini/commands/db/migrate.toml`
```toml
description = "Create database migration"
argument-hint = "[migration-name]"
prompt = """
Create database migration: {{args}}

1. Generate migration file with timestamp
2. Include up() and down() functions
3. Follow project's ORM conventions (detect from package.json)
4. Add comments for complex operations
5. Include rollback logic
"""
```

**Usage:** `/db:migrate add-user-roles-table`

---

### 12. Deployment Automation

**File:** `.gemini/commands/deploy.toml`
```toml
description = "Deploy to specified environment"
argument-hint = "[environment]"
prompt = """
Deploy to: {{args}}

Checklist:
1. Verify environment exists in config
2. Run pre-deployment tests
3. Build production assets
4. Deploy using project's deployment tool (detect)
5. Run post-deployment health checks
6. Generate deployment summary

Environment: {{args}}
"""
```

**Usage:** `/deploy production`

---

### 13. Security Audit

**File:** `~/.gemini/commands/security/audit.toml`
```toml
description = "Comprehensive security audit"
prompt = """
Run security audit on current codebase.

Check for:
1. Hardcoded secrets (API keys, passwords, tokens)
2. SQL injection vulnerabilities
3. XSS vulnerabilities
4. Insecure dependencies: !{npm audit}
5. Exposed sensitive endpoints
6. Missing authentication/authorization
7. CSRF protections
8. Insecure data handling

Generate security-audit.md report with:
- Critical vulnerabilities (fix immediately)
- High priority issues
- Medium priority issues
- Recommendations
"""
```

**Usage:** `/security:audit`

---

### 14. Refactoring Specialist

**File:** `~/.gemini/commands/refactor.toml`
```toml
description = "Refactor code with specified pattern"
argument-hint = "[pattern-or-file]"
prompt = """
Refactor: @{{args}}

Apply refactoring:
1. Identify code smells
2. Apply appropriate design patterns
3. Improve naming conventions
4. Extract duplicated code
5. Simplify complex functions
6. Maintain test compatibility
7. Preserve functionality

Run tests after refactoring to ensure no regressions.
"""
```

**Usage:** `/refactor src/legacy-module.js`

---

### 15. Release Notes Generator

**File:** `~/.gemini/commands/release.toml`
```toml
description = "Generate release notes from commits"
argument-hint = "[from-tag] [to-tag]"
prompt = """
Generate release notes from $1 to $2

1. Fetch commits: !{git log $1..$2 --oneline}
2. Categorize by type:
   - Features (feat:)
   - Bug Fixes (fix:)
   - Documentation (docs:)
   - Performance (perf:)
   - Breaking Changes (BREAKING CHANGE:)
3. Format as markdown
4. Include contributors: !{git log $1..$2 --format='%an' | sort -u}
5. Save to RELEASE_NOTES.md
"""
```

**Usage:** `/release v1.0.0 v1.1.0`

---

## MCP PROMPTS AS COMMANDS

### What Are MCP Prompts?

MCP servers can expose **prompts** that automatically become slash commands in Gemini CLI.

### Example: FastMCP Python Server

```python
from fastmcp import FastMCP

mcp = FastMCP("Research Server")

@mcp.prompt()
async def research(topic: str, depth: str = "standard"):
    """Research a topic with specified depth
    
    Args:
        topic: The topic to research
        depth: Research depth (quick, standard, comprehensive)
    """
    return f"""
    Research the following topic: {topic}
    
    Depth: {depth}
    
    Instructions:
    1. Search web for latest information
    2. Synthesize findings
    3. Provide structured summary
    """

@mcp.prompt()
async def analyze_codebase(focus: str = "architecture"):
    """Analyze codebase with specific focus
    
    Args:
        focus: Analysis focus (architecture, security, performance)
    """
    return f"""
    Analyze the codebase focusing on: {focus}
    
    Provide:
    - Current state assessment
    - Issues identified
    - Recommendations
    """
```

### Automatic Commands Created

```bash
# Positional arguments
/research "AI agents" comprehensive

# Named arguments
/research --topic="AI agents" --depth="comprehensive"

# Default arguments
/analyze_codebase
# or
/analyze_codebase --focus="security"
```

### Example: Node.js MCP Server

```javascript
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";

const server = new McpServer({
  name: "dev-tools",
  version: "1.0.0"
});

server.prompt({
  name: "code-review",
  description: "Review code with specific focus",
  arguments: {
    type: "object",
    properties: {
      files: { type: "string", description: "Files to review" },
      focus: { type: "string", default: "general" }
    }
  },
  handler: async ({ files, focus }) => {
    return `Review the following files: ${files}\nFocus: ${focus}`;
  }
});
```

**Usage:**
```bash
/code-review --files="src/auth/*.js" --focus="security"
```

---

## COMMAND BEST PRACTICES

### 1. Keep Commands Focused
✅ **Good:** One task per command  
❌ **Bad:** "Do everything" command

### 2. Use Descriptive Names
✅ **Good:** `/git:commit-conventional`  
❌ **Bad:** `/gc`

### 3. Include Context
✅ **Good:** Include git diff, recent commits, file contents  
❌ **Bad:** Vague instructions without context

### 4. Specify Model Preferences
```toml
prompt = """
Use gemini-2.5-flash-lite for speed.

[Your prompt here]
"""
```

### 5. Add Guardrails
```toml
prompt = """
Important: Read actual errors before proposing fixes.
Never guess at solutions.

[Your prompt here]
"""
```

### 6. Use Namespaces
```
~/.gemini/commands/
├── git/
│   ├── commit.toml
│   ├── push.toml
│   └── pr.toml
├── db/
│   ├── migrate.toml
│   └── seed.toml
└── deploy/
    ├── staging.toml
    └── production.toml
```

### 7. Version Control Project Commands
- Commit `.gemini/commands/` to Git
- Team members get commands automatically
- Document commands in project README

### 8. Document Arguments
```toml
argument-hint = "[environment] [options]"
description = "Deploy to environment with optional flags"
```

---

## SHELL ALIASES FOR FASTER EXECUTION

Add to `~/.zshrc` or `~/.bashrc`:

```bash
# Non-interactive command execution
alias gpush="gemini -p '/push' --yolo"
alias gcommit="gemini -p '/git:commit' --yolo"
alias gpr="gemini -p '/pr' --yolo"
alias glint="gemini -p '/lint' --yolo"
alias gtest="gemini -p '/test' --yolo"
alias gdeploy="gemini -p '/deploy staging' --yolo"

# With extensions
alias greview="gemini -e code-review -p '/code-review' --yolo"
alias gsec="gemini -e security -p '/security:audit' --yolo"
```

**Usage:**
```bash
gpush  # Stages, commits, pushes in one command
greview  # Runs full code review
```

---

# PART 3: AGENTS & ORCHESTRATION

## GEMINI CLI AGENT ARCHITECTURE

### Core Concept

Gemini CLI is **not a built-in multi-agent system** like Claude Code. Instead, it provides **building blocks** for creating agent orchestration:

1. **Custom slash commands** - Agent personas
2. **MCP servers** - External tool integration
3. **Shell invocation** (`run_shell_command`) - Spawn sub-processes
4. **Google ADK** - Visual agent designer
5. **File-system-as-state** - Disk-based orchestration

### Agent Philosophy: File System as State

Instead of complex process managers, **entire state lives in structured directory**:

```
.gemini/
├── agents/
│   ├── tasks/       # Task queue (JSON files)
│   │   ├── task_001.json
│   │   └── task_002.json
│   ├── plans/       # Long-term context
│   ├── logs/        # Agent execution logs
│   └── workspace/   # Scratchpad
└── commands/        # Agent definitions (slash commands)
```

**Benefits:**
- ✅ Transparent and debuggable
- ✅ No background process manager
- ✅ Stateless workers
- ✅ Simple task queue

---

## GOOGLE ADK AGENT DEVELOPMENT KIT

### What is ADK?

**Agent Development Kit (ADK)** is Google's official framework for building production multi-agent AI applications.

**Key Features:**
- Visual agent blueprint designer
- Code generation from natural language
- Multi-agent orchestration types
- Automatic deployment
- Security protections (Model Armor)
- Granular permissions

### ADK Agent Types

#### 1. LlmAgent (Single Agent)

```python
from google.adk.agents import Agent

labeling_agent = Agent(
    name="github_labeler",
    model="gemini-1.5-flash",
    instruction="""
    You are a GitHub issue labeling assistant.
    
    Workflow:
    1. Use 'get_issue' tool to read issue content
    2. Use 'get_available_labels' tool to see valid options
    3. Use 'apply_label' tool to add chosen label
    4. Respond with confirmation message
    """,
    tools=[get_issue, get_available_labels, apply_label]
)
```

---

#### 2. SequentialAgent (Step-by-Step)

```python
from google.adk.agents import SequentialAgent

development_workflow = SequentialAgent(
    name="dev_pipeline",
    agents=[
        planning_agent,      # Analyze requirements
        implementation_agent, # Write code
        testing_agent,       # Run tests
        documentation_agent  # Update docs
    ]
)
```

**Use Case:** Multi-phase workflows where each step depends on previous

---

#### 3. ParallelAgent (Concurrent)

```python
from google.adk.agents import ParallelAgent

research_team = ParallelAgent(
    name="research_orchestrator",
    agents=[
        market_researcher,
        competitor_analyst,
        trend_analyzer,
        user_researcher
    ]
)
```

**Use Case:** Independent investigations that can run simultaneously

---

#### 4. LoopAgent (Iterative)

```python
from google.adk.agents import LoopAgent

iterative_improver = LoopAgent(
    name="code_optimizer",
    agents=[
        code_generator,
        performance_tester,
        optimizer
    ],
    max_iterations=5,
    stop_condition=lambda state: state.get('performance_score', 0) > 95
)
```

**Use Case:** Refinement loops until quality threshold met

---

#### 5. CustomAgent (BaseAgent)

```python
from google.adk.agents import BaseAgent

class ConditionalRouter(BaseAgent):
    async def run(self, session):
        user_type = session.state.get('user_type')
        
        if user_type == 'enterprise':
            return await self.enterprise_flow.run(session)
        elif user_type == 'startup':
            return await self.startup_flow.run(session)
        else:
            return await self.default_flow.run(session)
```

**Use Case:** Complex routing logic, state machines

---

### ADK Development Workflow with Gemini CLI

**Step 1: Get ADK Context**
```bash
curl -o llms-full.txt https://raw.githubusercontent.com/google/adk-python/main/llms-full.txt
```

**Step 2: Plan with Gemini CLI**
```
I want to build an AI agent to label GitHub issues automatically.
Use the ADK framework. @llms-full.txt
```

**Gemini Response:**
```
I'll help you build a GitHub labeling agent using ADK.

Phase 1: Project Setup
- Install adk-python
- Configure dependencies

Phase 2: Custom Tools
- get_issue(issue_number)
- get_available_labels(repo)
- apply_label(issue_number, label)

Phase 3: Agent Definition
- LlmAgent with GitHub tools
- Instruction prompt for labeling logic

Phase 4: CLI Entrypoint
- Parse arguments
- Initialize agent
- Handle errors
```

**Step 3: Generate Code**
```
Generate the complete Python code for this ADK agent. @llms-full.txt
```

**Gemini Output:** Complete working agent application

**Step 4: Deploy**
```bash
adk deploy github-labeler
```

---

### ADK Extension for Gemini CLI

**Extension:** `@simonliu-ai-product/adk-agent-extension`

**Install:**
```bash
gemini extensions install https://github.com/simonliu-ai-product/adk-agent-extension
```

**Commands:**
- `list_adks` - List deployed ADK applications
- `list_adk_agents` - List agents in ADK app
- `create_session` - Create agent session
- `send_message_to_agent` - Interact with agent

**Usage:**
```bash
gemini -e adk-agent -p "list_adks"
gemini -e adk-agent -p "send_message_to_agent --agent=labeler --message='Label issue #42'"
```

---

## MULTI-AGENT ORCHESTRATION PATTERNS

### Pattern 1: Task Queue with File System

**Architecture:**
```
Task Queue (.gemini/agents/tasks/)
    ↓
Main Orchestrator (Gemini CLI)
    ↓
Spawn Sub-Agent (new Gemini CLI instance)
    ↓
Write Results to Logs
    ↓
Update Task Status
```

**Task File:** `.gemini/agents/tasks/task_001.json`
```json
{
  "id": "task_001",
  "agent": "coder-agent",
  "status": "pending",
  "description": "Implement user authentication",
  "created_at": "2026-01-13T00:00:00Z",
  "priority": "high"
}
```

**Orchestrator Command:** `.gemini/commands/agents/run.toml`
```toml
description = "Execute pending agent task"
prompt = """
1. Read task queue: ls .gemini/agents/tasks/*.json
2. Find first task with status=pending
3. Read task details
4. Mark task as running (update JSON)
5. Launch agent in background:

   gemini -e {{agent_name}}-agent --yolo -p "You are the {{agent_name}}-agent. Task ID: {{task_id}}. Your task: {{description}}. Execute this task yourself. Log output to .gemini/agents/logs/{{task_id}}.log"

6. Monitor task completion
7. Update task status to complete
"""
```

**Usage:**
```bash
gemini -p "/agents:run"
```

---

### Pattern 2: Multi-Agent with git worktree (Parallel)

**Problem:** Multiple agents writing files simultaneously causes conflicts

**Solution:** Use `git worktree` for isolated filesystems

**Setup:**
```bash
# Main workspace
git worktree add ../agent-1-workspace branch-agent-1
git worktree add ../agent-2-workspace branch-agent-2
git worktree add ../agent-3-workspace branch-agent-3

# Spawn agents in parallel
gemini --working-dir ../agent-1-workspace -p "/coder-agent Implement auth" &
gemini --working-dir ../agent-2-workspace -p "/tester-agent Write tests" &
gemini --working-dir ../agent-3-workspace -p "/docs-agent Update docs" &

wait  # Wait for all to complete

# Merge results
git merge branch-agent-1
git merge branch-agent-2
git merge branch-agent-3
```

---

### Pattern 3: GitHub Actions Multi-Agent

**Use Case:** Automated issue triage, PR reviews, feature implementation

**Workflow:** `.github/workflows/multi-agent.yml`
```yaml
name: Multi-Agent Workflow

on:
  issues:
    types: [opened, labeled]
  pull_request:
    types: [opened, synchronize]

jobs:
  triage-agent:
    runs-on: ubuntu-latest
    if: github.event_name == 'issues'
    steps:
      - uses: actions/checkout@v3
      - name: Run Triage Agent
        uses: google-github-actions/run-gemini-cli@v1
        with:
          prompt: |
            You are the triage-agent.
            Analyze issue #${{ github.event.issue.number }}.
            Assign appropriate labels and priority.
            Add to project board if needed.
          extensions: github,linear
  
  review-agent:
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request'
    steps:
      - uses: actions/checkout@v3
      - name: Run Review Agent
        uses: google-github-actions/run-gemini-cli@v1
        with:
          prompt: |
            You are the review-agent.
            Review PR #${{ github.event.pull_request.number }}.
            Check code quality, security, performance.
            Post review comments.
          extensions: github,security,code-review
  
  implementation-agent:
    runs-on: ubuntu-latest
    if: contains(github.event.issue.labels.*.name, 'ai-implement')
    steps:
      - uses: actions/checkout@v3
      - name: Run Implementation Agent
        uses: google-github-actions/run-gemini-cli@v1
        with:
          prompt: |
            You are the implementation-agent.
            Implement feature described in issue #${{ github.event.issue.number }}.
            Create pull request with implementation.
          extensions: github,firebase
```

---

### Pattern 4: CI/CD Agent Pipeline

**Use Case:** Automated testing, security, deployment

**Pipeline Stages:**

**1. Code Quality Agent**
```bash
gemini -e code-review --yolo -p "/code-review" > .reports/code-quality.md
```

**2. Security Agent**
```bash
gemini -e security --yolo -p "/security:analyze" > .reports/security.md
```

**3. Test Agent**
```bash
gemini -e test-runner --yolo -p "Run test suite and fix failures" > .reports/tests.md
```

**4. Deploy Agent**
```bash
gemini -e firebase --yolo -p "/firebase:deploy to production" > .reports/deploy.md
```

**Complete Pipeline:**
```bash
#!/bin/bash
set -e

echo "Running multi-agent CI/CD pipeline..."

# Stage 1: Code Quality
gemini -e code-review --yolo -p "/code-review" > .reports/code-quality.md
if [ $? -ne 0 ]; then exit 1; fi

# Stage 2: Security
gemini -e security --yolo -p "/security:analyze" > .reports/security.md
if [ $? -ne 0 ]; then exit 1; fi

# Stage 3: Tests
gemini -e test-runner --yolo -p "/test" > .reports/tests.md
if [ $? -ne 0 ]; then exit 1; fi

# Stage 4: Deploy
gemini -e firebase --yolo -p "/firebase:deploy to staging" > .reports/deploy.md

echo "Pipeline complete!"
```

---

### Pattern 5: Gemini CLI as Claude Code Subagent

**Use Case:** Leverage Gemini's 1M token window from Claude Code

**Setup:**

**1. Create Claude Code Subagent**

**File:** `.claude/agents/gemini-analyzer.md`
```markdown
---
name: gemini-analyzer
description: Large-scale codebase analysis using Gemini's 1M token context. Use when analysis exceeds Claude's context limits.
tools: Bash
model: sonnet
---

You are a wrapper for the Gemini CLI tool.

Your role:
1. Take requests for large codebase analysis
2. Format as Gemini CLI commands
3. Execute gemini CLI with --yolo flag
4. Return raw output without interpretation

Example commands:
- gemini --yolo -p "Analyze entire codebase for security issues"
- gemini --yolo -p "Find all API endpoints and document them"
- gemini --yolo -p "Identify architectural patterns across all modules"

Always use --yolo for non-interactive execution.
```

**2. Usage from Claude Code:**
```
Use the gemini-analyzer subagent to analyze this large codebase for
security vulnerabilities across all 500+ files.
```

**Result:**
- Claude Code → gemini-analyzer subagent → Gemini CLI (1M tokens)
- Gemini processes entire codebase
- Returns summary to Claude Code
- Best of both worlds

---

## CUSTOM AGENT IMPLEMENTATION

### Method 1: Slash Commands as Agent Personas

**Concept:** Each slash command = specialized agent

**Example: Coder Agent**

**File:** `.gemini/commands/coder-agent.toml`
```toml
description = "Specialized coding agent for implementation"
prompt = """
You are the coder-agent. Your identity and role:

Identity:
- You are a specialist in writing production-ready code
- You follow project coding standards in GEMINI.md
- You implement features based on specifications
- You run tests after implementation
- You log your work

Your current task: {{args}}

Execution protocol:
1. Read task specification carefully
2. Implement solution
3. Run tests
4. Log results to .gemini/agents/logs/coder-{timestamp}.log
5. Report completion status

Execute this task yourself. Do not delegate.
"""
```

**Usage:**
```bash
gemini -p "/coder-agent Implement JWT authentication middleware"
```

---

### Method 2: MCP Server as Agent

**Concept:** Build agent as MCP server with exposed tools

**Example: Python FastMCP Agent**

```python
from fastmcp import FastMCP

mcp = FastMCP("Research Agent")

@mcp.tool()
async def web_search(query: str, max_results: int = 5):
    """Search web for information"""
    # Implementation
    return results

@mcp.tool()
async def synthesize(sources: list[str]):
    """Synthesize information from sources"""
    # Implementation
    return synthesis

@mcp.prompt()
async def research_task(topic: str, depth: str = "standard"):
    """Research a topic thoroughly"""
    return f"""
    Research the topic: {topic}
    Depth: {depth}
    
    Use web_search tool to gather information.
    Use synthesize tool to create summary.
    """

if __name__ == "__main__":
    mcp.run()
```

**Install as Extension:**
```bash
# Package as Gemini CLI extension
gemini extensions install ./research-agent

# Use in session
gemini -e research-agent -p "/research_task 'AI agents' comprehensive"
```

---

### Method 3: Spawn Sub-Agents via Shell

**Architecture:**
```
Main Agent (Orchestrator)
    ↓ run_shell_command
    ↓
Sub-Agent (new gemini instance)
```

**Orchestrator Prompt:**
```toml
description = "Multi-agent orchestrator"
prompt = """
You are the orchestrator. You coordinate specialized agents.

Available sub-agents:
- coder-agent: Write code
- tester-agent: Run tests
- reviewer-agent: Review code
- docs-agent: Write documentation

To spawn sub-agent:
gemini -e <agent-name> --yolo -p "You are the <agent-name>. Task: <description>. Execute yourself."

Current task: {{args}}

Break down task and delegate to appropriate sub-agents.
"""
```

---

### Agent Identity Crisis Fix

**Problem:** Sub-agent tries to delegate instead of executing

**Bad Prompt:**
```bash
gemini -e coder-agent -p "Task: Create fibonacci guide"
```

**Result:** Agent thinks it should delegate task ❌

**Fixed Prompt:**
```bash
gemini -e coder-agent -p "You are the coder-agent. Task ID: task_001. Your task: Create fibonacci guide. Execute this task yourself. Do not delegate. You are the executor."
```

**Result:** Agent understands role and executes ✅

**Key Elements:**
1. **Identity Statement:** "You are the X-agent"
2. **Task ID:** Unique identifier
3. **Task Description:** Clear specification
4. **Execution Directive:** "Execute this yourself"
5. **Anti-Delegation:** "Do not delegate"

---

## ADVANCED AGENT WORKFLOWS

### Workflow 1: Automated Development Cycle

**Custom Command:** `/auto-dev`

**File:** `.gemini/commands/auto-dev.toml`
```toml
description = "Automated development cycle from TODO to commit"
prompt = """
Automated Development Workflow:

1. Read task queue: .gemini/agents/tasks/todo.md
2. Find first incomplete task
3. Implement ONLY this task (focus on one thing)
4. Run cleanup pipeline:
   a. /lint - Fix code style
   b. /test - Run test suite
   c. /security:analyze - Security check
5. If all pass:
   a. Stage changes: git add .
   b. Generate commit: Conventional Commits format
   c. Commit: git commit -m "..."
6. Mark task complete
7. Repeat until no tasks remain

Do NOT move to next task until current is complete and committed.
"""
```

**Usage:**
```bash
gemini -p "/auto-dev" --yolo
# Fully automated: task → code → test → commit
```

---

### Workflow 2: Agentic Marketing Campaign (ADK)

**Demo:** Google I/O 2025 - Gemini Enterprise

**Architecture:**
```
Campaign Orchestrator (ParallelAgent)
    ├── Market Research Agent
    │   └── Analyze trends, competitors
    ├── Content Creation Agent
    │   └── Generate blog posts, social media
    ├── Design Agent
    │   └── Create visuals, graphics
    └── Distribution Agent
        └── Schedule posts, manage campaigns
```

**ADK Code:**
```python
from google.adk.agents import ParallelAgent, Agent

campaign_orchestrator = ParallelAgent(
    name="marketing_campaign",
    agents=[
        Agent(
            name="market_researcher",
            instruction="Research market trends and competitors",
            tools=[web_search, data_analysis]
        ),
        Agent(
            name="content_creator",
            instruction="Generate engaging content",
            tools=[write_blog, create_social_post]
        ),
        Agent(
            name="designer",
            instruction="Create visual assets",
            tools=[generate_image, create_graphic]
        ),
        Agent(
            name="distributor",
            instruction="Schedule and distribute content",
            tools=[schedule_post, publish_content]
        )
    ]
)
```

**Usage:**
```bash
adk deploy marketing-campaign
gemini -e adk-agent -p "send_message_to_agent --agent=marketing_campaign --message='Launch Q1 campaign'"
```

---

### Workflow 3: Multi-Repository Agent

**Use Case:** Coordinate changes across multiple repositories

**Orchestrator:** `.gemini/commands/multi-repo/sync.toml`
```toml
description = "Sync changes across multiple repositories"
prompt = """
Multi-Repository Sync Workflow:

Repositories:
- frontend: ../frontend
- backend: ../backend
- shared: ../shared-lib

Task: {{args}}

Execution:
1. Analyze task and identify affected repos
2. For each affected repo:
   a. cd into repo
   b. Create feature branch
   c. Implement changes
   d. Run tests
   e. Commit
3. Create PRs in dependency order:
   a. shared-lib first (if modified)
   b. backend (if modified)
   c. frontend (if modified)
4. Link PRs in descriptions
"""
```

**Usage:**
```bash
gemini -p "/multi-repo:sync Update authentication to use OAuth2"
```

---

# PART 4: REFERENCE

## CORE FEATURES & BUILT-IN TOOLS

### Available Tools

| Tool | Usage | Description |
|------|-------|-------------|
| `glob` | `glob *.js` | File pattern matching |
| `write_todos` | Auto | Task management |
| `write_file` | Auto | File creation |
| `google_web_search` | Auto | Web search |
| `web_fetch` | Auto | Fetch web content |
| `replace` | Auto | Text replacement |
| `run_shell_command` ⭐ | Auto | Execute shell commands |
| `search_file_content` | Auto | Search in files |
| `read_many_files` | Auto | Bulk file reading |
| `read_file` | Auto | Single file read |
| `list_directory` | Auto | Directory listing |
| `save_memory` | Auto | Persist facts |

---

### Built-in Commands

| Command | Purpose |
|---------|---------|
| `/add-dir` | Add working directories |
| `/agents` | Manage AI subagents (if enabled) |
| `/bashes` | List background tasks |
| `/clear` | Clear conversation |
| `/compact` | Compact conversation |
| `/config` | Open settings |
| `/context` | Visualize context usage |
| `/cost` | Token usage statistics |
| `/doctor` | Check installation |
| `/exit` | Exit REPL |
| `/export` | Export conversation |
| `/help` | Usage help |
| `/extensions` | Manage extensions |
| `/mcp` | MCP server status |
| `/model` | Select AI model |
| `/plan` | Enter plan mode |
| `/resume` | Resume session |

---

### Available Models

| Model | Speed | Cost | Use Case |
|-------|-------|------|----------|
| `gemini-3-pro-preview` | Slow | High | Complex reasoning |
| `gemini-2.5-pro` | Slow | High | Advanced tasks |
| `gemini-2.5-flash` | Fast | Medium | General purpose ⭐ |
| `gemini-2.5-flash-lite` | Very Fast | Low | Simple tasks |

---

## CONFIGURATION GUIDE

### File Locations

| File | Location | Purpose |
|------|----------|---------|
| `settings.json` | `~/.gemini/settings.json` | User config |
| `settings.json` | `.gemini/settings.json` | Project config |
| `GEMINI.md` | Project root | Project context |
| `commands/` | `~/.gemini/commands/` | Global commands |
| `commands/` | `.gemini/commands/` | Project commands |
| `extensions/` | `~/.gemini/extensions/` | Installed extensions |

---

### Example settings.json

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "your-token"
      }
    },
    "firebase": {
      "command": "node",
      "args": ["/path/to/firebase-mcp/dist/index.js"]
    },
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "DATABASE_URL": "postgresql://localhost/mydb"
      }
    }
  },
  "mcp": {
    "allowed": ["github", "firebase", "postgres"],
    "excluded": ["experimental"]
  },
  "defaultModel": "gemini-2.5-flash",
  "security": {
    "disableYoloMode": false
  },
  "extensions": {
    "autoUpdate": true
  }
}
```

---

### YOLO Mode (Auto-Approval)

**Enable for Session:**
```bash
gemini --yolo
```

**Enable in settings.json:**
```json
{
  "security": {
    "disableYoloMode": false
  }
}
```

**Use in Scripts:**
```bash
gemini "/security:analyze" --yolo > report.md
```

**⚠️ Warning:** Auto-approves all actions. Use only in trusted environments.

---

## COMPARISON: GEMINI CLI VS CLAUDE CODE

### Feature Comparison

| Feature | Gemini CLI | Claude Code |
|---------|-----------|-------------|
| **Cost (Free Tier)** | ✅ 1,000 requests/day | $20/month (45 req/5hrs) |
| **Context Window** | ✅ 1M tokens | 200k tokens |
| **Extensions** | ✅ 287+ | ~227 plugins |
| **Native Agents** | ❌ Manual orchestration | ✅ Built-in subagents |
| **IDE Integration** | VS Code, JetBrains | ✅ Deep VS Code |
| **Speed (Fast Model)** | ✅ Very fast (Flash-Lite) | Slower (Haiku) |
| **GitHub Actions** | ✅ Native | Community |
| **MCP Support** | ✅ Native | ✅ Native |
| **Custom Commands** | ✅ TOML-based | Markdown-based |
| **Background Exec** | Shell jobs | ✅ Ctrl+B |
| **Resume Context** | ❌ Fresh each time | ✅ Full history |
| **Tool Restrictions** | CLI flags | ✅ Native fields |
| **Hooks** | ❌ No | ✅ Yes |
| **Best For** | Large codebases, cost-sensitive | Complex workflows, IDE |

---

### When to Use Each

**Use Gemini CLI When:**
- ✅ Need large context window (1M tokens)
- ✅ Cost is a concern (free tier)
- ✅ Terminal/CLI workflows preferred
- ✅ Speed is priority
- ✅ GitHub Actions automation

**Use Claude Code When:**
- ✅ IDE integration critical
- ✅ Need background execution
- ✅ Subagent orchestration required
- ✅ Context resumption important
- ✅ Complex multi-step workflows

---

## RESOURCES & COMMUNITY

### Official Resources

**Documentation:**
- Gemini CLI Docs: https://geminicli.com/docs/
- Extensions Gallery: https://geminicli.com/extensions/
- ADK Docs: https://google.github.io/adk-docs/
- MCP Documentation: https://geminicli.com/docs/tools/mcp-server/

**Repositories:**
- Gemini CLI: https://github.com/google-gemini/gemini-cli
- ADK Python: https://github.com/google/adk-python
- Gemini Extensions Org: https://github.com/gemini-cli-extensions

**Blogs:**
- Google Developers Blog: https://blog.google/technology/developers/
- Cloud Blog: https://cloud.google.com/blog

---

### Community

**Reddit:**
- r/GeminiCLI - Community discussions
- r/ClaudeAI - Cross-platform discussions

**GitHub Discussions:**
- https://github.com/google-gemini/gemini-cli/discussions

**Discord:**
- Check official docs for invite link

---

### Learning Resources

**Codelabs:**
- Getting Started: https://codelabs.developers.google.com/getting-started-gemini-cli-extensions
- ADK Workshop: https://codelabs.developers.google.com/companion-adk-beginner
- MCP Integration: https://codelabs.developers.google.com/gemini-cli-mcp

**Guides:**
- Custom Commands: https://cloud.google.com/blog/products/ai-machine-learning/gemini-cli-custom-slash-commands
- GitHub Actions: https://blog.google/technology/developers/gemini-cli-github-actions/
- Firebase Integration: https://firebase.blog/posts/2025/07/firebase-studio-gemini-cli/

---

### Example Repositories

**Multi-Agent Demo:**
- https://github.com/pauldatta/gemini-cli-commands-demo

**Extension Examples:**
- https://github.com/gemini-cli-extensions (official org)

**Community Extensions:**
- https://github.com/Piebald-AI/awesome-gemini-cli

---

## SECURITY & BEST PRACTICES

### Security Warnings

1. **⚠️ Extension Security:** Extensions are third-party. Review source code before installation.
2. **⚠️ YOLO Mode:** Auto-approval is dangerous. Use only in trusted environments.
3. **⚠️ API Keys:** Never commit API keys. Use environment variables.
4. **⚠️ MCP Servers:** MCP servers have full system access. Audit carefully.

### Best Practices

**✅ DO:**
- Review extension source code before installing
- Use `.gemini/commands/` for team-shared commands
- Commit project commands to version control
- Use environment variables for secrets
- Monitor token usage with `/cost`
- Update extensions regularly
- Create GEMINI.md in project root
- Use namespaces for command organization

**❌ DON'T:**
- Install untrusted extensions
- Use --yolo in production environments
- Hardcode secrets in commands
- Mix global and project commands without strategy
- Ignore security warnings
- Run untrusted MCP servers

---

## TROUBLESHOOTING

### Common Issues

**1. Extension Not Found**
```bash
# Solution: Update extension list
gemini extensions update --all
```

**2. MCP Server Won't Start**
```bash
# Solution: Check MCP status
gemini -p "/mcp"

# Restart server
gemini -p "/mcp restart <server-name>"
```

**3. Context Limit Exceeded**
```bash
# Solution: Compact conversation
gemini -p "/compact"

# Or start fresh session
gemini -p "/clear"
```

**4. Command Not Working**
```bash
# Solution: List commands
gemini -p "/help"

# Check command file exists
ls ~/.gemini/commands/your-command.toml
```

**5. Agent Identity Crisis**
```bash
# Solution: Add explicit identity
gemini -e agent-name -p "You are the agent-name. Task: X. Execute yourself."
```

---

## APPENDIX: QUICK REFERENCE

### Installation Checklist

- [ ] Install Gemini CLI: `npm install -g @google/gemini-cli`
- [ ] Authenticate: `gemini login`
- [ ] Install core extensions: `gemini extensions install <url>`
- [ ] Create GEMINI.md in project root
- [ ] Set up custom commands in `.gemini/commands/`
- [ ] Configure MCP servers in `settings.json`
- [ ] Test with simple command: `gemini -p "Hello"`

### Essential Commands

```bash
# Extensions
gemini extensions list
gemini extensions install <url>

# Commands
gemini -p "/help"
gemini -p "/extensions list"
gemini -p "/mcp"

# Usage
gemini -e <extension> -p "prompt"
gemini --yolo -p "/command"

# Config
gemini -p "/config"
gemini -p "/cost"
```

### Quick Wins

1. **Install Top 5 Extensions:**
   - GitHub, Firebase, Security, Code Review, Workspace

2. **Create 5 Essential Commands:**
   - `/git:commit`, `/push`, `/pr`, `/lint`, `/test`

3. **Set Up Agent Workflow:**
   - Task queue in `.gemini/agents/tasks/`
   - Orchestrator command: `/agents:run`

4. **Enable GitHub Actions:**
   - Add workflow file
   - Configure with extensions

---

## CHANGELOG

- **2026-01-13:** Master guide compiled from 104 sources
- **Extensions:** 287+ documented
- **Commands:** 1,000+ patterns
- **Agents:** Complete ADK and orchestration guide

---

**End of Master Guide**

*This document represents the most comprehensive Gemini CLI resource available, combining official documentation, community contributions, and advanced patterns from real-world usage.*
