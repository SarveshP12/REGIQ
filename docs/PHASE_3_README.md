# 🎯 REGIQ — Phase 3: AI-Based Impact Analysis

> **Duration:** Q1–Q2 2026 (4 months)  
> **Goal:** Deploy the Intelligent Impact Analysis Engine, confidence scoring, XAI panels, CI/CD API integration, and the regression suite optimization engine.  
> **Prerequisite:** Phase 2 (Intelligent Classification) completed.

---

## 📋 Phase 3 Overview

Phase 3 is the **technical heart** of REGIQ — the Impact Analysis Engine. This is the most technically complex phase, orchestrating multiple AI models, graph algorithms, and scoring functions to produce ranked, confidence-scored test case recommendations for any given change set.

### Exit Criteria

| Criteria | Target |
|----------|--------|
| Impact analysis precision | > 85% |
| CI/CD pipeline integration | Live with at least 1 pipeline |
| Pilot customers | 3 active pilot customers |
| Impact analysis latency | < 60 seconds for 1,000 components |

---

## 🔬 Task 1: Intelligent Impact Analysis Engine

### What to Build

The 9-phase impact analysis pipeline that combines AI models, graph traversal, and scoring to identify impacted test cases.

### Impact Analysis Pipeline (9 Phases)

| Phase | Process | AI/Algorithm | Output |
|-------|---------|-------------|--------|
| **1: Change Ingestion** | Parse update set XML; extract component list with metadata | Rule-based parser + NLP entity extraction | Structured change manifest |
| **2: Component Classification** | Classify each changed component by type, scope, and test relevance | Fine-tuned classification model | Labeled component inventory |
| **3: Direct Mapping** | Direct test-case-to-component matching via stored relationships | Neo4j graph lookup | Tier-1 directly impacted tests |
| **4: Dependency Traversal** | Traverse upstream/downstream dependency graph for indirect impacts | BFS/DFS graph traversal with depth limit | Tier-2 indirectly impacted tests |
| **5: Similarity Matching** | Find semantically related test cases not captured by direct/graph methods | SBERT vector similarity (cosine ≥ 0.78) | Tier-3 similarity-matched tests |
| **6: Historical Weighting** | Apply defect frequency scores and historical execution failure rates | Gradient boosted scoring model | Risk-weighted test list |
| **7: Business Criticality Overlay** | Multiply risk score by criticality weight to produce final priority rank | Weighted scoring formula | Priority-ranked suite recommendation |
| **8: Confidence Scoring** | Generate per-test confidence score with source attribution | Ensemble confidence model | Confidence-annotated recommendations |
| **9: Suite Optimization** | Remove duplicates, resolve coverage redundancy, generate execution strategies | Greedy set cover + constraint optimization | Optimized suite options |

### Architecture

```
Change Event ──► Impact Analysis Orchestrator (FastAPI/Python)
                        │
        ┌───────────────┼───────────────┐
        │               │               │
  Phase 1-2:         Phase 3-4:       Phase 5:
  Change Parser      Neo4j Graph     SBERT Similarity
  + NLP Classifier   Traversal       Matching (FAISS)
        │               │               │
        └───────────────┼───────────────┘
                        │
                  Phase 6-7:
                  Historical Scoring
                  + Criticality Overlay
                        │
                  Phase 8-9:
                  Confidence Scoring
                  + Suite Optimization
                        │
                  Ranked Recommendations
                  with Explanations
```

### AI Models Involved

| Model | Type | Framework | Role in Impact Analysis |
|-------|------|-----------|------------------------|
| **Impact Analysis Ranker (IAR)** | Learning-to-Rank (LTR) | LightGBM + FAISS | Rank impacted tests by relevance and risk |
| **Semantic Embedding Model (SEM)** | Sentence embedding | SBERT (fine-tuned) | Embed changes + test cases for similarity matching |
| **Dependency Graph Reasoner (DGR)** | Graph Neural Network | PyTorch Geometric (GraphSAGE) | Learn dependency propagation patterns |
| **NLP Change Analyzer (NCA)** | NER + relation extraction | SpaCy + LangChain + GPT-4 | Parse change descriptions for structured intent |

### Graph Traversal Algorithms

**Breadth-First Traversal (Downstream Impact):**
- Start from modified node, follow outbound DEPENDS_ON and TRIGGERS edges
- Depth-based weight decay: depth-1 = 1.0, depth-2 = 0.75, depth-3 = 0.50, depth-4+ = 0.25
- Max depth: 4 hops (configurable per tenant)
- Visited-node set prevents re-traversal: O(V+E) complexity

**Upstream Dependency Tracing:**
- Reverse traversal following inbound edges
- Identifies components the modified element depends on

**Critical Path Analysis:**
- Weighted shortest-path through high-criticality business processes
- Test cases on critical paths always included regardless of depth

### Deliverables

- [ ] Build Impact Analysis Orchestrator service (coordinates all 9 phases)
- [ ] Implement change ingestion pipeline (Phase 1-2)
- [ ] Build Neo4j graph traversal engine (BFS downstream + reverse upstream)
- [ ] Implement depth-based weight decay for confidence scoring
- [ ] Build SBERT similarity matching with FAISS index
- [ ] Train Impact Analysis Ranker (IAR) using LightGBM
- [ ] Train Dependency Graph Reasoner (DGR) using PyTorch Geometric GraphSAGE
- [ ] Build NLP Change Analyzer with SpaCy NER + LangChain
- [ ] Implement critical path analysis algorithm
- [ ] Build historical weighting with gradient boosted scoring
- [ ] Build suite optimization (greedy set cover + constraint optimization)
- [ ] Store analysis runs in MongoDB (`ai_analysis_runs` collection)

---

## 📊 Task 2: Confidence Scoring Model

### What to Build

Every recommended test case gets a confidence score (0.00–1.00) calculated from 4 source signals.

### Confidence Score Formula

| Signal | Weight | Description |
|--------|--------|-------------|
| Direct Dependency Match | 40% | Test directly linked to modified component in graph |
| Graph Traversal Depth | 25% | Score decays: depth-1=1.0, depth-2=0.75, depth-3=0.50, depth-4+=0.25 |
| Semantic Similarity Score | 20% | Cosine similarity between change and test case embeddings |
| Historical Co-failure Rate | 15% | How often this test failed with similar change profiles |

### Confidence Levels

| Level | Score Range |
|-------|------------|
| **High** | ≥ 0.85 |
| **Medium** | 0.65 – 0.84 |
| **Low** | 0.45 – 0.64 |
| **Speculative** | < 0.45 |

### Deliverables

- [ ] Implement ensemble confidence scoring model
- [ ] Build confidence calibration using Platt scaling + isotonic regression
- [ ] Set default minimum confidence threshold at 0.45 (configurable)
- [ ] Display confidence scores with color-coded indicators in UI
- [ ] Log all confidence score computations for audit trail

---

## 🔍 Task 3: Explainable AI (XAI) Panels

### What to Build

Transparent AI recommendations that QA engineers can audit, challenge, and override.

### XAI Mechanisms

| Mechanism | Description | Where Displayed |
|-----------|-------------|-----------------|
| **SHAP Explanations** | Per-prediction feature importance for gradient boosted models (IAR, RSM) | Expandable waterfall chart on each recommendation card |
| **Source Attribution Cards** | Shows: Direct Dependency, Graph Traversal Depth-N, Semantic Similarity X, Historical Failure Y% | Chips on each recommended test case |
| **Confidence Intervals** | Prediction intervals reflecting model uncertainty | Bar indicators on recommendations |
| **Counterfactual Explanations** | "Why was this test NOT recommended?" — shows which signals fell below threshold | Available on request per test case |
| **Audit Trail API** | All AI decisions logged with input features, model version, output scores | API endpoint for compliance |

### Deliverables

- [ ] Implement SHAP value computation for IAR model predictions
- [ ] Build Source Attribution Card component (React)
- [ ] Build confidence interval display
- [ ] Implement counterfactual explanation generation
- [ ] Build Audit Trail API (`GET /api/v1/audit/ai-decisions`)
- [ ] Create expandable XAI panel in Impact Analysis Dashboard

---

## 🔄 Task 4: Regression Suite Engine

### What to Build

Generate, optimize, and manage regression test suites based on impact analysis results.

### Suite Strategies

| Strategy | Description | Use Case | Coverage |
|----------|-------------|----------|----------|
| **Fast Track** | Critical + High tests in impacted modules only. ≤ 4 hours execution | Emergency hotfixes, minor changes | 20–30% |
| **Standard** | All impacted tests with risk score > 5.0 | Regular sprint releases | 45–65% |
| **Full Coverage** | All impacted + historically unstable modules | Major releases, platform upgrades | 80–100% |
| **Smoke** | Top 50 Critical tests across all processes | Post-deployment verification | 5–10% |
| **Integration** | All inbound/outbound integration and API tests | Integration changes, API upgrades | Integration only |
| **AI-Optimized** | ML-recommended based on change context + failure patterns | AI-driven precision testing | Variable |

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/suites/generate` | Generate optimized regression suite for a release |
| GET | `/api/v1/suites/{id}/optimize` | Get optimization options (Fast Track, Standard, Full) |
| POST | `/api/v1/suites/{id}/execute` | Trigger suite execution |
| GET | `/api/v1/suites/{id}/coverage` | Get coverage analysis |
| GET | `/api/v1/suites/{id}/history` | Execution history |

### Frontend: Regression Cockpit

- Suite strategy selector with comparison view
- Coverage donut chart per strategy
- Timeline estimates for each strategy
- Risk score comparison across strategies
- Estimated defect detection probability
- One-click suite customization

### Deliverables

- [ ] Build suite generation engine supporting all 6 strategies
- [ ] Implement coverage analysis (tests per module, criticality distribution)
- [ ] Build suite optimization (remove redundancy, greedy set cover)
- [ ] Build Regression Cockpit UI
- [ ] Implement suite execution tracking
- [ ] Build execution history with pass/fail reporting

---

## 🔌 Task 5: CI/CD Pipeline Integration

### What to Build

API-first integration allowing CI/CD pipelines to trigger impact analysis and regression suites automatically.

### Integration Flow

```
Jenkins/GitHub Actions Pipeline
        │
        ▼ POST /api/v1/analysis/impact
        │
    REGIQ Impact Analysis Engine
        │
        ▼ GET /api/v1/analysis/{runId}/results
        │
    Ranked test case list (JSON)
        │
        ▼ POST /api/v1/suites/generate
        │
    Optimized regression suite
        │
        ▼ Execute tests → Results fed back to pipeline
```

### Impact Analysis API

**Request:**
```json
{
  "release_id": "rel-2025-q2-001",
  "change_set_id": "cs-a7f3b291",
  "analysis_config": {
    "max_depth": 3,
    "min_confidence": 0.45,
    "strategy": "ai_optimized",
    "include_historical_weight": true,
    "criticality_filter": ["Critical", "High"]
  }
}
```

**Response (202 Accepted):**
```json
{
  "run_id": "run-c9d2e4f1-2025",
  "status": "processing",
  "estimated_completion_seconds": 45,
  "poll_url": "/api/v1/analysis/run-c9d2e4f1-2025/results",
  "webhook_url": "https://regiq.yourorg.com/webhooks/analysis/run-c9d2e4f1-2025"
}
```

### SDK Deliverables

| Package | Format | Usage |
|---------|--------|-------|
| `@regiq/sdk` | NPM package | JavaScript/TypeScript CI/CD integrations |
| `regiq-sdk` | Python library | Python-based pipeline integrations |

### Deliverables

- [ ] Build full Impact Analysis API (trigger, poll, results, feedback)
- [ ] Implement WebSocket notifications for analysis completion (FastAPI WebSockets or Python-SocketIO)
- [ ] Build NPM SDK package (`@regiq/sdk`)
- [ ] Build Python SDK package (`regiq-sdk`)
- [ ] Create Jenkins pipeline integration example
- [ ] Create GitHub Actions workflow integration example
- [ ] Write CI/CD integration documentation
- [ ] Implement API key authentication for machine-to-machine access

---

## 📊 Task 6: Impact Analysis & AI Dashboards

### New Dashboards

| Dashboard | Key Elements | Audience |
|-----------|-------------|----------|
| **Impact Analysis Dashboard** | Change manifest accordion, tiered test list (Tier-1/2/3 color-coded), confidence bars, source attribution chips, accept/customize/export panel | QA Engineers, Test Managers |
| **AI Recommendations Panel** | Card-based recommendations, SHAP waterfall chart (expandable), accept/reject toggle, reason-code selector on reject | QA Engineers |
| **Executive QA Metrics** | KPI scorecard tiles (MTTV, leakage rate, coverage %), trend sparklines, AI accuracy trend, release timeline heatmap | CIO, QA Director |

### Deliverables

- [ ] Build Impact Analysis Dashboard with tiered test case display
- [ ] Build AI Recommendations Panel with accept/reject workflow
- [ ] Build Executive QA Metrics dashboard
- [ ] Implement real-time analysis progress via WebSocket
- [ ] Build feedback workflow (accept/reject with reason codes)

---

## 🔄 Task 7: Feedback Loop & Model Retraining

### Feedback Events That Trigger Learning

| Event | Signal Type | Model Updated | Trigger |
|-------|-------------|---------------|---------|
| QA accepts recommendation | Positive reinforcement | IAR | Weekly batch |
| QA rejects recommendation | Negative signal + reason | IAR, SEM | Weekly batch |
| Manual test added post-analysis | Coverage gap | DGR | Nightly incremental |
| Non-recommended test fails | False negative (critical!) | IAR, SEM, DGR | **Immediate** priority retraining |
| Recommended test passes 5+ consecutive releases | Over-recommendation | RSM, IAR | Monthly review |
| New defect filed | Risk elevation | DRP (Phase 4) | Real-time score update |

### Deliverables

- [ ] Build feedback collection pipeline (from accept/reject events)
- [ ] Implement weekly batch retraining for IAR model
- [ ] Build priority retraining trigger for false negative events
- [ ] Update model performance metrics in MLflow after each retrain
- [ ] Create model performance comparison dashboard

---

## 🚀 Suggested 16-Week Timeline

| Week | Focus |
|------|-------|
| 1–2 | Impact Analysis Orchestrator scaffolding, NLP Change Analyzer |
| 3–4 | Graph traversal engine (BFS/DFS), direct mapping |
| 5–6 | SBERT similarity matching + FAISS, IAR model training |
| 7–8 | Confidence scoring model, historical weighting |
| 9–10 | Suite optimization engine, regression cockpit UI |
| 11–12 | XAI panels (SHAP, source attribution, counterfactuals) |
| 13–14 | CI/CD integration APIs, SDK packages |
| 15 | Dashboards (Impact Analysis, AI Recommendations, Executive) |
| 16 | Feedback loops, integration testing, pilot customer onboarding |

---

## ✅ Phase 3 Completion Checklist

- [ ] Impact analysis precision > 85% on retrospective labeling
- [ ] Impact analysis completes in < 60 seconds for 1,000 components
- [ ] All 9 pipeline phases operational
- [ ] Confidence scoring calibrated (Platt scaling)
- [ ] XAI panels showing SHAP explanations and source attribution
- [ ] Regression suite engine generating all 6 strategy types
- [ ] CI/CD pipeline integration live (Jenkins or GitHub Actions)
- [ ] NPM and Python SDKs published
- [ ] Feedback loop collecting accept/reject signals
- [ ] 3 pilot customers actively using the platform
- [ ] Impact Analysis Dashboard with real-time progress
- [ ] Model cards completed for IAR, SEM, DGR, NCA models

---

> **Previous Phase:** [Phase 2 — Intelligent Classification](./PHASE_2_README.md)  
> **Next Phase:** [Phase 4 — Predictive Intelligence](./PHASE_4_README.md)
