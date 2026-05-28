# 🔮 REGIQ — Phase 4: Predictive Intelligence

> **Duration:** Q3–Q4 2026 (4 months)  
> **Goal:** Deploy defect recurrence prediction, release risk scoring, predictive release quality management, generative AI test suggestions, conversational QA assistant (beta), and automated defect filing.  
> **Prerequisite:** Phase 3 (AI-Based Impact Analysis) completed.

---

## 📋 Phase 4 Overview

Phase 4 shifts REGIQ from **reactive** analysis to **predictive** intelligence. The platform can now forecast which modules are likely to produce defects, score release risk before deployment, suggest new test cases using generative AI, and begin automating defect documentation.

### Exit Criteria

| Criteria | Target |
|----------|--------|
| Risk score correlation with actual defect outcomes | > 0.82 (Spearman ρ) |
| Enterprise customers | 10 active |
| AI copilot beta | Feedback collected from pilot users |
| Defect recurrence prediction AUC-ROC | > 0.87 |

---

## 🐛 Task 1: Defect Recurrence Predictor (DRP Model)

### What to Build

A prediction model that forecasts the probability of defect recurrence per module per release.

### Model Specifications

| Attribute | Details |
|-----------|---------|
| **Model Type** | Binary + multi-class classification |
| **Framework** | XGBoost with temporal features |
| **Input Features** | Defect count per module (last 3 releases), repeat defect flag, MTTR, severity distribution, resolution category, change complexity |
| **Output** | Defect recurrence probability per module per release |
| **Primary KPI** | AUC-ROC > 0.87 |
| **Monitoring** | Historical defect comparison |

### Feature Engineering

| Feature Category | Features |
|------------------|----------|
| Defect History | Defect count per module (last 3 releases), repeat defect flag, MTTR, severity distribution, resolution category |
| Change Context | Change type, component count, scope, update set size, release type, days since last change |
| Historical Execution | Pass rate (last 5 releases), failure streak count, last execution date, flakiness score |
| Business Context | Process criticality score, module stability score, SLA sensitivity flag, integration dependency count |

### Defect Analytics Capabilities

| Capability | Description |
|------------|-------------|
| **Repeat Defect Detection** | NLP clustering (SBERT + DBSCAN) and exact-match analysis to find recurring defects |
| **Failure Pattern Analysis** | Statistical analysis of failure frequency per test case, module, and release type |
| **Defect Clustering** | Group semantically similar defects using SBERT embeddings and DBSCAN |
| **Risk Heatmap** | Defect density visualization per ServiceNow module × time period matrix |
| **Regression Priority Input** | Defect-weighted scores feed into Impact Analysis Engine |

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/defects/predictions/{module}` | Get defect recurrence predictions for a module |
| GET | `/api/v1/defects/heatmap` | Get defect density heatmap data |
| GET | `/api/v1/defects/clusters` | Get defect clusters with themes |
| GET | `/api/v1/defects/repeat-analysis` | Get repeat defect analysis |
| GET | `/api/v1/defects/stability-scores` | Get module stability scores |

### Deliverables

- [ ] Train XGBoost defect recurrence predictor with temporal features
- [ ] Implement SBERT + DBSCAN defect clustering pipeline
- [ ] Build repeat defect detection using NLP similarity + exact match
- [ ] Build failure pattern analysis (statistical module stability scoring)
- [ ] Build defect risk heatmap API and visualization (D3.js)
- [ ] Feed defect-weighted priority scores into Impact Analysis Engine
- [ ] Store defect clusters in MongoDB (`defect_clusters` collection)
- [ ] Create model card for DRP model

---

## 📈 Task 2: Risk Score Model (RSM)

### What to Build

Composite release risk scoring that forecasts the probability of production incidents before release sign-off.

### Model Specifications

| Attribute | Details |
|-----------|---------|
| **Model Type** | Regression + ordinal classification |
| **Framework** | Gradient Boosting Regressor (scikit-learn) |
| **Primary KPI** | Brier Score < 0.15; Spearman ρ > 0.82 with actual outcomes |
| **Output** | Release risk score + per-module risk breakdown |

### Risk Score Components

| Factor | Description |
|--------|-------------|
| Historical defect density per module | How defect-prone is each module historically? |
| Change complexity score | Number and type of changed components in this release |
| Coverage completeness | What % of impacted areas have regression coverage? |
| Team execution velocity | How quickly is the team completing test execution? |
| AI recommendation acceptance rate | Are QA engineers following AI guidance? |
| Module stability score | From DRP's failure pattern analysis |

### Release Readiness Score

A composite metric (0–100) presented as a **go/no-go recommendation**:

| Score Range | Recommendation |
|-------------|---------------|
| 85–100 | ✅ **Go** — Low risk, high coverage |
| 70–84 | ⚠️ **Conditional Go** — Acceptable risk with noted gaps |
| 50–69 | ⛔ **Hold** — Significant uncovered risk areas |
| < 50 | 🚫 **No-Go** — Critical gaps require additional testing |

### "What If" Simulation

Enable release managers to run simulations:
- "What if we skip module X tests?" → Risk increases by Y%
- "What if we add integration tests?" → Risk decreases by Z%

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/releases/{id}/readiness` | Get Release Readiness Score + factor breakdown |
| POST | `/api/v1/releases/{id}/simulate` | Run "What If" risk simulation |
| GET | `/api/v1/releases/{id}/risk-breakdown` | Module-level risk breakdown |

### Frontend: Release Readiness Dashboard

- Readiness score gauge (0–100) with color-coded zones
- Module-level readiness grid
- Risk area alerts
- Test execution progress bar
- Go/no-go recommendation panel
- "What If" simulation interface

### Deliverables

- [ ] Train Gradient Boosting risk score model
- [ ] Build Release Readiness Score computation pipeline
- [ ] Implement "What If" simulation engine
- [ ] Build Release Readiness Dashboard UI
- [ ] Feed risk scores back to regression suite prioritization
- [ ] Create model card for RSM model
- [ ] Implement post-release retrospective comparison (predicted vs actual)

---

## ✨ Task 3: Generative AI Test Case Creation

### What to Build

GPT-4-based test case generation from user stories, requirements, and ServiceNow component changes.

### Generation Flow

```
User Story / Requirement Text
        │
        ▼ LangChain + GPT-4
        │
  Generated Test Cases (Draft status)
        │
  Auto-populated in repository
        │
  Human review + approval workflow
```

### Features

| Feature | Description |
|---------|-------------|
| Story-to-test generation | Input a user story → get suggested test cases with steps |
| Change-to-test generation | Input a change component → get regression test suggestions |
| Auto-classification | Generated tests auto-classified using TCC model |
| Duplicate check | Compare against existing tests using embeddings before saving |
| Draft status | All generated tests start as "Draft" requiring human review |

### Deliverables

- [ ] Build LangChain pipeline with GPT-4 for test case generation
- [ ] Create prompt templates for different generation scenarios
- [ ] Implement story-to-test generation endpoint
- [ ] Implement change-to-test generation endpoint
- [ ] Auto-classify and embed generated test cases
- [ ] Duplicate detection against existing repository
- [ ] Build generation UI with review/approve/edit workflow
- [ ] Target: reduce test authoring time by 40%

---

## 💬 Task 4: Conversational QA Assistant (Beta)

### What to Build

A LangChain-powered chatbot that QA engineers can query in natural language.

### Sample Queries

| Query | Response Type |
|-------|---------------|
| "What tests should I run for this change?" | Impact analysis summary |
| "Why did this defect recur?" | Defect history + root cause analysis |
| "What is the blast radius of this update set?" | Dependency graph summary |
| "Show me unstable modules this quarter" | Defect trend analysis |
| "How confident is the AI about this recommendation?" | XAI explanation |

### Architecture

```
User Query ──► LangChain Agent ──► Tool Selection
                                        │
                    ┌───────────────────┼───────────────────┐
                    │                   │                   │
            Impact Analysis API   Defect API        Dependency API
                    │                   │                   │
                    └───────────────────┼───────────────────┘
                                        │
                                Natural Language Response
```

### Deliverables

- [ ] Set up LangChain agent with tool definitions (REGIQ APIs as tools)
- [ ] Build chat interface component (React)
- [ ] Implement query routing to appropriate APIs
- [ ] Build response formatting (tables, charts, summaries)
- [ ] Add conversation history and context management
- [ ] Deploy as beta feature with pilot user feedback collection
- [ ] Target: reduce time to insight by 60%

---

## 🤖 Task 5: AI Copilot for Test Authoring (Beta)

### What to Build

Real-time AI suggestions during test case writing.

### Copilot Features

| Feature | Description |
|---------|-------------|
| Auto-complete steps | Suggest next test steps based on context |
| Dependency suggestions | Recommend components and processes to link |
| Similar test warning | Alert when writing a test similar to existing ones |
| Classification preview | Show predicted classification as you type |

### Deliverables

- [ ] Build real-time suggestion API (low latency endpoint)
- [ ] Implement step auto-completion using fine-tuned model
- [ ] Build dependency suggestion engine
- [ ] Implement similar test detection with real-time feedback
- [ ] Build inline copilot UI components in test case editor
- [ ] Collect beta feedback and usage analytics

---

## 📝 Task 6: Automated Defect Filing

### What to Build

When test execution fails, automatically generate and file defect tickets in Jira/Azure DevOps with full context.

### Auto-Filed Defect Content

| Field | Auto-Populated From |
|-------|-------------------|
| Title | Test case title + failure summary |
| Description | Test steps, expected vs actual results |
| Component | Mapped from test case classification |
| Severity | Inferred from test criticality + failure type |
| Impact Context | Which change caused this (from impact analysis) |
| Related Tests | Other tests that may be affected (from dependency graph) |
| Environment | Execution environment info |

### Deliverables

- [ ] Build defect auto-generation engine (format defect from test failure)
- [ ] Implement Jira ticket creation API integration
- [ ] Implement Azure DevOps work item creation
- [ ] Build pre-filing review UI (QA can edit before filing)
- [ ] Add impact context and dependency info to filed defects
- [ ] Target: eliminate manual defect documentation effort

---

## 📊 Task 7: Predictive Dashboards

### New/Upgraded Dashboards

| Dashboard | Key Elements |
|-----------|-------------|
| **Defect Intelligence Dashboard** | Module heatmap, repeat defect timeline, top-10 unstable modules, prediction confidence bars |
| **Release Readiness Dashboard** | Readiness gauge, module grid, risk alerts, progress bar, go/no-go panel, simulation interface |
| **Executive Dashboard** (upgraded) | MTTV trend, defect leakage rate, AI accuracy KPIs, ROI metrics, release confidence trend |

### Deliverables

- [ ] Build full Defect Intelligence Dashboard with heatmap visualization
- [ ] Build Release Readiness Dashboard with simulation support
- [ ] Upgrade Executive Dashboard with predictive metrics
- [ ] Implement drill-down from any metric to underlying data

---

## 🚀 Suggested 16-Week Timeline

| Week | Focus |
|------|-------|
| 1–2 | DRP model training, defect clustering pipeline |
| 3–4 | Risk Score Model, Release Readiness Score computation |
| 5–6 | Release Readiness Dashboard, "What If" simulation |
| 7–8 | Generative AI test creation (LangChain + GPT-4) |
| 9–10 | Conversational QA Assistant (LangChain agent) |
| 11–12 | AI Copilot for test authoring, automated defect filing |
| 13–14 | Predictive dashboards, defect heatmaps |
| 15 | Beta feature deployment, pilot user feedback collection |
| 16 | Integration testing, model cards, performance tuning |

---

## ✅ Phase 4 Completion Checklist

- [ ] DRP model AUC-ROC > 0.87 on historical data
- [ ] Risk Score correlation > 0.82 with actual defect outcomes
- [ ] Release Readiness Score operational with go/no-go recommendations
- [ ] "What If" simulation functional for release managers
- [ ] Generative AI test creation reducing authoring time by 40%
- [ ] Conversational QA Assistant (beta) deployed with pilot feedback
- [ ] AI Copilot (beta) providing real-time suggestions in editor
- [ ] Automated defect filing working for Jira and/or Azure DevOps
- [ ] Defect Intelligence Dashboard with module heatmaps
- [ ] 10 enterprise customers actively using the platform
- [ ] Model cards completed for DRP and RSM models
- [ ] Post-release retrospective comparison automated

---

> **Previous Phase:** [Phase 3 — AI-Based Impact Analysis](./PHASE_3_README.md)  
> **Next Phase:** [Phase 5 — Autonomous QA Platform](./PHASE_5_README.md)
