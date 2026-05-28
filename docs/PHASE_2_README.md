# 🧠 REGIQ — Phase 2: Intelligent Classification

> **Duration:** Q4 2025 (3 months)  
> **Goal:** Deploy the AI classification engine, criticality scoring, dependency mapping foundation, defect ingestion, and basic dashboards.  
> **Prerequisite:** Phase 1 (Repository Platform) completed.

---

## 📋 Phase 2 Overview

Phase 2 introduces **AI intelligence** to the platform. Every test case gets automatically classified by business process, criticality, type, and dependencies. The Neo4j dependency graph is established, defect data begins flowing in, and dashboards evolve from basic metrics to AI-powered insights.

### Exit Criteria

| Criteria | Target |
|----------|--------|
| AI classification accuracy | > 88% |
| Dependency graph | Operational for at least 1 ServiceNow module |
| Criticality scoring | All imported test cases scored |
| Defect ingestion | Working from at least 1 source (Jira/ADO/ServiceNow) |

---

## 🤖 Task 1: AI Classification Engine (TCC Model)

### What to Build

A fine-tuned BERT multi-label text classifier that automatically classifies every test case across 6 dimensions.

### Classification Dimensions

| Dimension | Sub-Categories | AI Model |
|-----------|----------------|----------|
| **Business Process** | Incident Mgmt, Change Mgmt, Problem Mgmt, CMDB, Service Catalog, Asset Mgmt, HRSD, ITOM, SecOps, Event Mgmt, GRC | Fine-tuned BERT multi-class |
| **Criticality Level** | Critical / High / Medium / Low (composite score) | Rule engine + gradient boosted scoring |
| **Test Case Type** | Inbound, Outbound, Reports, Processes, APIs, Integrations, UI, Workflow, Notifications, Scheduled Jobs, Batch | Multi-label text classifier |
| **Dependency Class** | Upstream, Downstream, Cross-module, Integration, Standalone | Graph-assisted classification + NLP |
| **Automation Feasibility** | Fully Automatable, Partially Automatable, Manual-only | Heuristic rule engine + ML scorer |
| **Execution Frequency** | Every Release, Monthly, Quarterly, On-demand, Smoke only | Historical execution pattern analysis |

### Tech Stack

| Component | Technology |
|-----------|-----------|
| Model | Fine-tuned BERT (HuggingFace Transformers) |
| Training Framework | PyTorch + HuggingFace Trainer |
| Serving | Python 3.11 + FastAPI |
| Deployment | GPU-enabled Kubernetes pod |
| API | `/classify` endpoint returning multi-label results + confidence scores |

### AI Service Architecture

```
apps/api (FastAPI/Python) ──► POST /classify ──► AI Classification Service (FastAPI/Python)
                                               │
                                    ┌──────────┼──────────┐
                                    │          │          │
                              BERT Model  Rule Engine  ML Scorer
                                    │          │          │
                                    └──────────┴──────────┘
                                               │
                                    Multi-label classification result
                                    with per-label confidence scores
```

### NLP Pipeline for Classification

| Stage | Process | Technology |
|-------|---------|------------|
| Text Ingestion | Normalize encoding, strip HTML/XML, handle ServiceNow markup | Python BeautifulSoup + regex |
| Tokenization | Tokenize, lowercase, remove stopwords, expand ITSM abbreviations | SpaCy tokenizer + custom ITSM vocabulary |
| Entity Recognition | Identify ServiceNow entities: table names, module references, API endpoints, roles | Custom SpaCy NER model |
| Embedding Generation | Generate 512-dim dense vectors for test cases | SBERT (all-mpnet-base-v2 fine-tuned) |
| Classification | Multi-label classification with confidence scores | Fine-tuned BERT classifier |

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/ai/classify` | Classify a single test case (returns labels + confidence) |
| POST | `/api/v1/ai/classify/batch` | Batch classify multiple test cases |
| PUT | `/api/v1/tests/{id}/classify` | Re-classify a test case (manual override or AI re-run) |
| GET | `/api/v1/ai/classify/stats` | Classification accuracy stats |
| POST | `/api/v1/ai/classify/feedback` | Submit correction for misclassification |

### Training Data Preparation

- [ ] Curate labeled dataset from existing test cases (minimum 2,000 labeled examples)
- [ ] Build ITSM-specific vocabulary (ServiceNow terms, module names, table names)
- [ ] Create train/validation/test split (70/15/15)
- [ ] Define label hierarchy and mapping

### Deliverables

- [ ] Set up Python AI services directory (`services/ai-service/`)
- [ ] Build NLP text preprocessing pipeline (BeautifulSoup + SpaCy)
- [ ] Train custom SpaCy NER model for ServiceNow entities
- [ ] Fine-tune BERT for multi-label business process classification
- [ ] Build FastAPI classification service with `/classify` endpoint
- [ ] Implement batch classification endpoint
- [ ] Create classification feedback API (accept/reject/correct)
- [ ] Integrate classification service with FastAPI core backend
- [ ] Auto-classify on test case creation and import
- [ ] Build classification review queue UI for low-confidence results
- [ ] Implement classification override workflow (human-in-loop)

---

## 📊 Task 2: Criticality Scoring Engine

### What to Build

A weighted composite scoring model that assigns criticality to every test case.

### Scoring Formula

| Factor | Weight | Scoring Criteria | Score Range |
|--------|--------|------------------|-------------|
| Revenue Impact | 30% | Does failure impact revenue-generating processes or SLA penalties? | 0–10 |
| Business Process Criticality | 25% | Is the process mission-critical (Incident/Change Mgmt) vs supporting? | 0–10 |
| Production Risk | 20% | Historical correlation with production incidents when skipped | 0–10 |
| User / Customer Impact | 15% | External-facing vs internal-only functionality | 0–10 |
| Security Sensitivity | 10% | Involves ACLs, data access, SecOps workflows | 0–10 |
| **COMPOSITE SCORE** | **100%** | **Weighted average** | **0–10** |

### Criticality Levels

| Level | Score Range |
|-------|------------|
| **Critical** | ≥ 8.5 |
| **High** | 6.5 – 8.4 |
| **Medium** | 4.0 – 6.4 |
| **Low** | < 4.0 |

### Implementation

- [ ] Build rule engine for factor extraction (revenue impact, SLA sensitivity, etc.)
- [ ] Train gradient boosted scoring model using historical execution and defect data
- [ ] Build scoring API endpoint
- [ ] Auto-score on test case creation and classification
- [ ] Build criticality dashboard with distribution charts
- [ ] Allow manual criticality override with audit logging

---

## 🕸️ Task 3: Dependency Mapping Engine (Neo4j Foundation)

### What to Build

The graph-based dependency mapping engine that will power impact analysis in Phase 3.

### Graph Database Setup (Neo4j)

| Node Label | Key Properties |
|------------|---------------|
| `:Component` | id, name, type, scope, table, script_hash, last_modified, active |
| `:BusinessProcess` | id, name, module, criticality, owner, sla_impact |
| `:Table` | name, scope, parent_table, field_count, is_audited |
| `:Workflow` | id, name, table, version, active, stage_count |
| `:Integration` | id, name, type, direction (in/out/both), protocol, target_system |
| `:TestCase` | id, title, criticality, type, status, automation_flag, embedding_id |
| `:Defect` | id, title, severity, module, release, status, recurrence_count |
| `:Release` | id, name, date, type, risk_score, environment |

### Relationship Types

| Category | Edge Types | Impact Weight |
|----------|-----------|---------------|
| Direct Component | `DEPENDS_ON` | 1.0 (full weight) |
| Workflow | `TRIGGERS`, `EXECUTES` | 0.9 |
| Integration | `INTEGRATES_WITH` | 0.85 |
| Process | `FULFILLS`, `ROUTES_TO` | 0.75 |
| Data | `REFERENCES` | 0.65 |
| Test Coverage | `TESTS`, `COVERS`, `VALIDATES` | N/A (meta-layer) |

### Graph Building Pipeline

```
ServiceNow Metadata Sync ──► Graph Builder Service ──► Neo4j
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
            Parse Components   Extract Relations   Link Test Cases
                    │               │               │
            Create Nodes      Create Edges     Create TESTS edges
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/dependencies/graph` | Retrieve graph nodes/edges for visualization |
| GET | `/api/v1/dependencies/component/{id}` | Get all dependencies for a component |
| GET | `/api/v1/dependencies/test/{id}` | Get dependency chain for a test case |
| POST | `/api/v1/dependencies/rebuild` | Trigger full graph rebuild |

### Frontend: Dependency Graph Explorer

- React-Flow canvas with zoom/pan
- Node type legend with color coding
- Filter sidebar (by module, type, depth)
- Path highlighting on hover
- Impact radius heat overlay
- Export graph as image/JSON

### Deliverables

- [ ] Set up Neo4j database (Docker container for dev)
- [ ] Build graph schema with all node labels and relationship types
- [ ] Create graph builder service that processes ServiceNow metadata into nodes/edges
- [ ] Build graph query service (Python + Neo4j Driver)
- [ ] Link test cases to components via `TESTS`/`COVERS` relationships
- [ ] Build dependency graph REST API
- [ ] Build React-Flow based Dependency Graph Explorer UI
- [ ] Implement graph refresh on ServiceNow sync events
- [ ] Verify graph operational for at least 1 complete ServiceNow module

---

## 🐛 Task 4: Defect Intelligence — Data Ingestion

### What to Build

Automated ingestion of historical defect data from external systems. Full analytics and prediction come in Phase 4.

### Supported Sources

| Source | Integration Method | Data Extracted |
|--------|-------------------|----------------|
| Jira | REST API | Issue key, summary, severity, component, resolution, release |
| Azure DevOps | REST API | Work item ID, title, severity, area path, iteration, state |
| ServiceNow | REST API | Incident sys_id, short_description, severity, assignment_group, state |

### Database Table

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| external_id | VARCHAR | ID from source system |
| source_system | VARCHAR | 'jira', 'ado', 'servicenow' |
| title | TEXT | Defect title/summary |
| severity | VARCHAR | Critical/High/Medium/Low |
| module | VARCHAR | ServiceNow module affected |
| component_id | UUID | Link to change_components |
| release_id | UUID | Release where found |
| status | VARCHAR | Open/Resolved/Closed |
| recurrence_count | INT | How many times this defect recurred |
| is_repeat | BOOLEAN | Flagged as repeat defect |

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/defects/import` | Import defects from external system |
| GET | `/api/v1/defects` | List defects with filtering |
| GET | `/api/v1/defects/{id}` | Get defect details |
| POST | `/api/v1/defects/link` | Link defect to test case / component |

### Deliverables

- [ ] Build Jira REST API connector for defect ingestion
- [ ] Build Azure DevOps connector for defect ingestion
- [ ] Build ServiceNow incident/problem import
- [ ] Create normalized defect schema and storage
- [ ] Build defect import scheduling (periodic sync)
- [ ] Link defects to components and test cases
- [ ] Build defect browsing UI with filtering

---

## 📊 Task 5: Enhanced Dashboards

### New/Upgraded Dashboards

| Dashboard | Key Metrics |
|-----------|-------------|
| **Regression Coverage** | Coverage % by module, test type distribution, unmapped test cases, criticality breakdown |
| **Defect Intelligence** (basic) | Defect count by module, severity distribution, repeat defect rate |
| **AI Classification Panel** | Classification distribution, confidence histogram, review queue count, accuracy trend |
| **Dependency Graph Explorer** | Interactive Neo4j-powered graph (built in Task 3) |

### Deliverables

- [ ] Build Regression Coverage dashboard (D3.js coverage heatmap)
- [ ] Build basic Defect Intelligence dashboard
- [ ] Build AI Classification status panel
- [ ] Upgrade Test Repository Health dashboard with classification stats

---

## 📐 Task 6: Embedding Service Setup

### What to Build

Set up the semantic embedding infrastructure that will be essential for Phase 3's impact analysis.

### Architecture

| Component | Technology |
|-----------|-----------|
| Model | SBERT (all-mpnet-base-v2, fine-tuned on ITSM QA pairs) |
| Vector Dimensions | 512-dim dense vectors |
| Vector Store | pgvector (PostgreSQL extension) or Pinecone |
| Serving | Python FastAPI |

### Deliverables

- [ ] Fine-tune SBERT on ITSM test case pairs
- [ ] Build embedding generation service (batch + online)
- [ ] Set up pgvector extension in PostgreSQL (or Pinecone account)
- [ ] Generate embeddings for all existing test cases
- [ ] Auto-generate embedding on test case creation/update
- [ ] Build similarity search endpoint (`/api/v1/tests/similar/{id}`)
- [ ] Implement NLP-based duplicate detection using embeddings (upgrade from Phase 1)

---

## 🔄 Task 7: Model Training Infrastructure

### What to Build

Set up the ML operations infrastructure for model versioning, training pipelines, and monitoring.

### Components

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Model Registry | MLflow | Version models, stage promotion, A/B testing |
| Training Pipeline | Python scripts + scheduled jobs | Batch retraining on new data |
| Feedback Loop | Classification feedback API | Human corrections feed back to training |

### Deliverables

- [ ] Set up MLflow for model versioning
- [ ] Build model training scripts for TCC (BERT classifier)
- [ ] Build model evaluation pipeline (holdout test set)
- [ ] Implement weekly batch retraining trigger
- [ ] Set up model performance monitoring (accuracy tracking over time)
- [ ] Create model card documentation for TCC model

---

## 🚀 Suggested 12-Week Timeline

| Week | Focus |
|------|-------|
| 1–2 | AI service scaffolding, NLP pipeline, training data preparation |
| 3–4 | BERT fine-tuning, classification service, FastAPI deployment |
| 5–6 | Criticality scoring engine, classification UI integration |
| 7–8 | Neo4j setup, graph builder, dependency mapping service |
| 9–10 | Defect ingestion connectors, embedding service |
| 11 | Dependency Graph Explorer UI, enhanced dashboards |
| 12 | MLflow setup, model cards, integration testing |

---

## ✅ Phase 2 Completion Checklist

- [ ] AI classification accuracy > 88% on holdout test set
- [ ] All test cases classified across 6 dimensions
- [ ] Criticality scores computed for all test cases
- [ ] Neo4j dependency graph operational for at least 1 module
- [ ] Defect ingestion working from at least 1 external source
- [ ] Embedding service generating vectors for all test cases
- [ ] Dependency Graph Explorer UI functional
- [ ] MLflow model registry tracking TCC model versions
- [ ] Classification review queue UI for low-confidence items
- [ ] Updated dashboards with AI-powered insights

---

> **Previous Phase:** [Phase 1 — Repository Platform](./PHASE_1_README.md)  
> **Next Phase:** [Phase 3 — AI-Based Impact Analysis](./PHASE_3_README.md)
