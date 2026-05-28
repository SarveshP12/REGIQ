# 🧬 REGIQ — Project Roadmap Index

> **REGIQ** (Regression Intelligence Quotient) — AI-Powered ServiceNow ITSM Regression Test Suite Management & Intelligent Impact Analysis Platform

---

## 📋 Phase Overview

| Phase | Name | Duration | Key Focus |
|-------|------|----------|-----------|
| [**Phase 1**](./PHASE_1_README.md) | 🏗️ Repository Platform | Q3 2025 (3 months) | Test repository, ServiceNow integration, auth/RBAC, REST API, deployment |
| [**Phase 2**](./PHASE_2_README.md) | 🧠 Intelligent Classification | Q4 2025 (3 months) | AI classification (BERT), criticality scoring, Neo4j dependency graph, defect ingestion, embeddings |
| [**Phase 3**](./PHASE_3_README.md) | 🎯 AI-Based Impact Analysis | Q1–Q2 2026 (4 months) | 9-phase impact analysis engine, confidence scoring, XAI, regression suite engine, CI/CD integration |
| [**Phase 4**](./PHASE_4_README.md) | 🔮 Predictive Intelligence | Q3–Q4 2026 (4 months) | Defect prediction, risk scoring, release readiness, generative AI tests, QA chatbot, AI copilot |
| [**Phase 5**](./PHASE_5_README.md) | 🚀 Autonomous QA Platform | 2027 (ongoing) | Autonomous regression, self-healing tests, cross-tenant benchmarking, full autonomous validation |

---

## 🏗️ Tech Stack Summary

| Layer | Technology |
|-------|-----------|
| **Frontend** | Next.js 14, React 18, Tailwind CSS v3, Shadcn/UI, D3.js, React-Flow |
| **Backend** | Python 3.11, FastAPI, SQLAlchemy, Alembic |
| **AI Services** | Python 3.11, FastAPI, PyTorch, HuggingFace Transformers, scikit-learn, LangChain |
| **Databases** | PostgreSQL 15, MongoDB 7, Neo4j 5, Redis 7, pgvector/Pinecone |
| **Event Bus** | Apache Kafka 3.x |
| **ML Ops** | MLflow, SHAP, FAISS |
| **DevOps** | Docker, Kubernetes, Helm, Terraform, GitHub Actions, ArgoCD |
| **Observability** | Prometheus, Grafana, ELK Stack, OpenTelemetry, Jaeger, PagerDuty |

---

## 🤖 AI Models (7 Total)

| Model | Phase | Type | Framework |
|-------|-------|------|-----------|
| Test Case Classifier (TCC) | Phase 2 | Multi-label text classification | Fine-tuned BERT |
| Semantic Embedding Model (SEM) | Phase 2–3 | Sentence embedding | SBERT (all-mpnet-base-v2) |
| Impact Analysis Ranker (IAR) | Phase 3 | Learning-to-Rank | LightGBM + FAISS |
| Dependency Graph Reasoner (DGR) | Phase 3 | Graph Neural Network | PyTorch Geometric (GraphSAGE) |
| NLP Change Analyzer (NCA) | Phase 3 | NER + relation extraction | SpaCy + LangChain + GPT-4 |
| Defect Recurrence Predictor (DRP) | Phase 4 | Binary + multi-class classification | XGBoost |
| Risk Score Model (RSM) | Phase 4 | Regression + ordinal classification | Gradient Boosting (scikit-learn) |

---

## 📊 Key Deliverables by Phase

### Phase 1 Deliverables
- Web Platform (Next.js + Python/FastAPI)
- REST API Layer (OpenAPI 3.1 + Postman)
- ServiceNow Integration Package
- Deployment Package (Docker Compose, Helm, Terraform)

### Phase 2 Deliverables
- AI Classification Service (FastAPI)
- Dependency Graph Engine (Neo4j)
- Embedding Service (SBERT + pgvector)
- Model Registry (MLflow)

### Phase 3 Deliverables
- Impact Analysis Engine (9-phase pipeline)
- Regression Suite Engine (6 strategies)
- CI/CD Integration SDK (NPM + Python)
- XAI Panels (SHAP explanations)

### Phase 4 Deliverables
- Defect Recurrence Predictor
- Release Readiness Score + "What If" Simulation
- Generative AI Test Creation
- Conversational QA Assistant (Beta)

### Phase 5 Deliverables
- Autonomous Regression Selection
- Self-Healing Test Suites
- Cross-Tenant Benchmark Analytics
- Full Autonomous Release Validation

---

## 📈 Target Metrics

| Metric | 6-Month | 12-Month |
|--------|---------|----------|
| Regression effort reduction | -35% | -55% |
| Production defect leakage | -25% | -45% |
| Impact analysis precision | > 85% | > 92% |
| AI classification accuracy | > 88% | > 93% |
| Release cycle reduction | -20% | -35% |
| Mean time to validation | -40% | -60% |
| ROI payback period | — | 8–14 months |
