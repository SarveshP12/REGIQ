# 🏗️ REGIQ — Phase 1: Repository Platform

> **Duration:** Q3 2025 (3 months)  
> **Goal:** Build the foundational platform — enterprise test repository, ServiceNow integration, user management, RBAC, REST API layer, and deployment infrastructure.

---

## 📋 Phase 1 Overview

Phase 1 establishes the **core foundation** of REGIQ. Everything built here becomes the backbone for all future AI-powered features. The focus is on getting a rock-solid, multi-tenant platform that can ingest test cases, connect to ServiceNow, and serve a clean REST API.

### Exit Criteria

| Criteria | Target |
|----------|--------|
| Test cases imported | 500+ |
| ServiceNow sync | Operational |
| RBAC roles | All 6 roles functional |
| API documentation | 100% OpenAPI 3.1 coverage |
| Deployment time | < 2 hours from scratch |

---

## 🔧 Task 1: Project Scaffolding & Setup

### Directory Structure

```
regiq/
├── apps/
│   ├── web/                    # Next.js 14 frontend (App Router)
│   └── api/                    # Python 3.11 + FastAPI backend
├── services/
│   ├── integration-service/    # ServiceNow connector (Python/FastAPI)
│   └── notification-service/   # Email/Slack dispatcher (Python)
├── infra/
│   ├── docker/                 # Dockerfiles per service
│   ├── docker-compose.yml      # Local dev environment
│   ├── helm/                   # Kubernetes Helm charts
│   └── terraform/              # IaC for AWS/Azure
├── docs/
└── .github/workflows/          # CI/CD pipelines
```

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, React 18, Tailwind CSS v3, Shadcn/UI |
| Backend | Python 3.11, FastAPI, SQLAlchemy, Alembic |
| State Management | Zustand (client), React Query v5 (server) |
| Package Manager | Poetry (Python backend) / pnpm (frontend) |

### Deliverables

- [ ] Initialize repository with monorepo setup (or separate directories for web/api)
- [ ] Scaffold Next.js 14 app with App Router in `apps/web`
- [ ] Scaffold FastAPI + Python API in `apps/api` with Poetry
- [ ] Create shared database schema configurations using SQLAlchemy models
- [ ] Set up Ruff for Python linting/formatting and ESLint/Prettier for Next.js
- [ ] Create base Dockerfiles for each service
- [ ] Create `docker-compose.yml` with PostgreSQL, Redis, MongoDB, and app services
- [ ] Set up environment variable management (`.env.example` files)
- [ ] Add basic health check endpoints (`GET /health`)

---

## 🔐 Task 2: Authentication & User Management (RBAC)

### RBAC Roles

| Role | Description | Permissions |
|------|-------------|-------------|
| **Super Admin** | Platform-wide administration | Full access to all tenants and settings |
| **Tenant Admin** | Tenant-level administration | Manage users, integrations, settings within tenant |
| **Test Manager** | QA leadership | Full test repo access, suite management, reports, approvals |
| **QA Engineer** | Daily QA user | Test CRUD, suite execution, impact review, feedback |
| **Viewer** | Read-only stakeholder | View dashboards, reports, test cases (no modification) |
| **API Service Account** | Machine-to-machine | API access for CI/CD pipelines (scoped permissions) |

### Authentication Stack

| Component | Technology |
|-----------|-----------|
| SSO Provider | NextAuth.js with OAuth2/OIDC (Okta, Azure AD, ADFS) |
| Token Format | JWT with RS256 signing |
| Token Expiry | 1 hour access + refresh token rotation |
| API Keys | HMAC-SHA256 request signing for CI/CD |
| MFA | Enforced for admin roles |

### Key Database Tables

- `users` — id (UUID), email, name, role, tenant_id, is_active, last_login
- `tenants` — id (UUID), name, slug, settings (JSONB)
- `api_keys` — id (UUID), user_id, tenant_id, key_hash, scopes[], expires_at
- `audit_logs` — id (UUID), user_id, action, resource_type, resource_id, details (JSONB), ip_address

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/login` | Authenticate user, return JWT |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| POST | `/api/v1/auth/logout` | Invalidate refresh token |
| GET | `/api/v1/users` | List users (admin) |
| GET | `/api/v1/users/{id}` | Get user details |
| PUT | `/api/v1/users/{id}/role` | Update user role (admin) |
| GET | `/api/v1/users/{id}/permissions` | Get user permissions |
| POST | `/api/v1/api-keys` | Generate API key |
| GET | `/api/v1/audit/logs` | Query audit logs |

### Security Checklist

- [ ] TLS 1.3 minimum for all communications
- [ ] AES-256 encryption for credentials and API keys at rest
- [ ] Zero plaintext secrets in code (use env vars / secrets manager)
- [ ] All user actions logged to audit_logs table
- [ ] Rate limiting per tenant and per user (HTTP 429)
- [ ] Middleware-enforced permission checks on every endpoint
- [ ] Row-level security for multi-tenant data isolation

### Deliverables

- [ ] Implement NextAuth.js on the frontend and Python-based JWT verification middleware on the backend
- [ ] Build JWT issuance and validation handlers in Python (using PyJWT / Passlib)
- [ ] Create RBAC middleware/dependency injection rules with role-permission mapping in FastAPI
- [ ] Build user management CRUD APIs in Python
- [ ] Implement API key generation and HMAC-SHA256 validation
- [ ] Build audit logging decorators/middleware (auto-log all mutations to DB)
- [ ] Set up rate limiting with Redis (using fastapi-limiter)
- [ ] Create login/registration UI pages
- [ ] Build user management admin panel

---

## 🗄️ Task 3: PostgreSQL Database Schema

### Core Tables

| Table | Key Columns | Purpose |
|-------|-------------|---------|
| `business_processes` | name, module, parent_id (self-ref), criticality_level, sla_impact, revenue_impact | ServiceNow module hierarchy |
| `test_cases` | title, description, steps (JSONB), status, criticality, business_process_id, type_tags[], automation_flag, embedding_id, version | Central test entity |
| `releases` | name, version, environment, planned_date, status, risk_score, readiness_score, go_nogo_status | Release tracking |
| `regression_suites` | name, release_id, strategy_type, status, total_tests, risk_score, coverage_pct, generated_by | Suite management |
| `suite_test_cases` | suite_id, test_case_id, inclusion_reason, confidence_score, priority_rank, execution_status, result | Suite ↔ Test junction |
| `execution_history` | test_case_id, suite_id, release_id, result, duration_ms, executed_by, defects_found[] | Execution tracking |
| `change_sets` | release_id, source_type, update_set_ref, component_count, analysis_status, impact_count | Change tracking |
| `change_components` | change_set_id, component_type, component_name, scope, table_name, change_type, raw_diff (JSONB) | Parsed changes |

### MongoDB Collections (Document Store)

| Collection | Purpose |
|------------|---------|
| `test_case_versions` | Version snapshots: {test_case_id, version, snapshot, changed_fields[], changed_by, timestamp} |
| `update_set_raw` | Raw XML storage: {change_set_id, raw_xml, parsed_components[], metadata, tenant_id} |
| `notification_logs` | Notification history with TTL index (30 days) |

### Deliverables

- [ ] Set up migration tool (Alembic)
- [ ] Create all core table migrations with proper types and constraints (SQLAlchemy models)
- [ ] Add indexes on tenant_id, status, created_at, business_process_id
- [ ] Set up seed data scripts for development
- [ ] Implement connection pooling (SQLAlchemy engine configuration)
- [ ] Configure row-level security policies for multi-tenancy in PostgreSQL

---

## 📦 Task 4: Enterprise Test Repository

### Repository Hierarchy

```
Tenant → Product → Module → Business Process → Test Suite → Test Case
```

### Test Case Lifecycle

```
Draft → Review → Approved → Active → Deprecated → Archived
```

### Features

| Feature | Details |
|---------|---------|
| **CRUD** | Create, read, update, delete with multi-format authoring (structured, step-by-step, Gherkin BDD) |
| **Versioning** | Full version history with diff comparison (snapshots in MongoDB `test_case_versions`) |
| **Clone** | Clone with relationship inheritance and auto-incremented ID |
| **Bulk Import** | Excel (.xlsx) and CSV with field mapping wizard, validation preview, duplicate detection |
| **Bulk Export** | Excel, PDF, ServiceNow ATF format with filtered export |
| **Search** | Full-text search (PostgreSQL tsvector) with faceted filtering by module, criticality, status, type, owner |
| **Saved Searches** | Per-user saved search profiles |
| **Tagging** | Multi-dimensional: business process, criticality, type, integration, owner, release |
| **Traceability** | Matrix linking: test case ↔ requirement ↔ defect ↔ release |
| **Duplicate Detection** | Basic text similarity check before creation (NLP-based in Phase 2) |

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/tests` | List with pagination, filtering, search |
| POST | `/api/v1/tests` | Create new test case |
| GET | `/api/v1/tests/{id}` | Get full details |
| PUT | `/api/v1/tests/{id}` | Update (creates new version) |
| DELETE | `/api/v1/tests/{id}` | Soft delete (archive) |
| POST | `/api/v1/tests/import` | Bulk import from Excel/CSV |
| GET | `/api/v1/tests/export` | Export to Excel/PDF/ATF |
| POST | `/api/v1/tests/{id}/clone` | Clone test case |
| GET | `/api/v1/tests/{id}/versions` | Version history |
| GET | `/api/v1/tests/{id}/versions/{v}/diff` | Diff between versions |

### Frontend Pages

- [ ] **Test Repository Browser** — DataGrid with faceted filters, multi-tag sidebar, quick preview panel, bulk action toolbar
- [ ] **Test Case Detail View** — Full test case with steps, metadata, version history, related items
- [ ] **Test Case Editor** — Form with structured fields, step editor, tag selector, Gherkin toggle
- [ ] **Import Wizard** — Step-by-step: upload → field mapping → validation preview → confirm
- [ ] **Export Dialog** — Format selection, filter options, download

### Deliverables

- [ ] Build test case CRUD API with validation (FastAPI Pydantic models)
- [ ] Implement version tracking (MongoDB document updates using Beanie or Motor)
- [ ] Build bulk import engine with field mapping (`openpyxl` or `pandas`)
- [ ] Build export engine (Excel via `openpyxl`, PDF via `weasyprint` or `playwright`)
- [ ] Implement full-text search with PostgreSQL tsvector
- [ ] Build faceted filtering with query builder
- [ ] Create all frontend pages listed above
- [ ] Implement basic duplicate detection
- [ ] Add traceability matrix linking

---

## 🔗 Task 5: ServiceNow Integration Module

### Integration Flow

```
ServiceNow Instance(s) ──► Webhook/Polling ──► Integration Service ──► Kafka Events ──► Core Backend
```

### Connection Features

| Feature | Details |
|---------|---------|
| Authentication | OAuth2 client credentials flow |
| Multi-instance | DEV, TEST, UAT, PROD per tenant |
| Health monitoring | Auto re-auth on token expiry; alert on sync failures |
| Scope support | Scoped applications + global scope separation |

### Sync Schedule

| Type | Frequency | Data |
|------|-----------|------|
| Delta sync | Every 15 min | Business rules, workflows, catalog items, ACLs, script includes |
| Full sync | Nightly | Complete metadata snapshot |
| Manual sync | On-demand | User-triggered |

### Update Set Parser — 10 Component Types

| Component Type | Extracted Attributes |
|----------------|---------------------|
| Business Rules | Name, table, when/order, script content, active status, conditions |
| Workflow Activities | Workflow name, stage, activity type, conditions, transitions |
| UI Policies / Actions | Form, field, condition, action type |
| ACL / Security Policies | Table, operation, condition, script |
| Script Includes | Name, script body, client callable flag |
| REST API Definitions | Endpoint, method, schema changes |
| Catalog Items / Variables | Item name, category, variable set, workflow mapping |
| Scheduled Jobs | Name, run schedule, script reference |
| Email Notifications | Event, condition, template, recipients |
| Table Definitions / Fields | Table name, new/modified fields, type changes |

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/integrations/servicenow/connect` | Register ServiceNow instance |
| POST | `/api/v1/integrations/servicenow/sync` | Trigger manual sync |
| GET | `/api/v1/integrations/health` | Check integration health |
| POST | `/api/v1/changes/parse` | Submit update set XML |
| GET | `/api/v1/changes/{id}/manifest` | Get parsed change manifest |
| GET | `/api/v1/changes/history` | Change history |

### Deliverables

- [ ] Build OAuth2 client credentials connector in Python for ServiceNow REST API
- [ ] Implement multi-instance connection management in the Python backend
- [ ] Build update set XML parser using Python's `lxml` or `xml.etree` (all 10 component types)
- [ ] Implement incremental delta sync engine using Celery / APScheduler
- [ ] Implement nightly full sync job
- [ ] Build webhook listener for update set promotion events
- [ ] Implement polling fallback mechanism
- [ ] Build connection health monitoring with auto-reconnect
- [ ] Create ServiceNow ATF test case import mapper
- [ ] Build integration management UI (connect, configure, monitor)

---

## 📊 Task 6: Basic Dashboards & Reporting

### Dashboards for Phase 1

| Dashboard | Key Metrics |
|-----------|-------------|
| **Test Repository Health** | Total test cases, status distribution, unmapped tests, criticality breakdown, stale test count |
| **Sync Status** | Last sync time, sync health, error count, component counts |
| **User Activity** | Recent actions, active users, API key usage |

### Deliverables

- [ ] Build Test Repository Health dashboard with charts (D3.js or Recharts)
- [ ] Build Sync Status monitor panel
- [ ] Build basic user activity feed
- [ ] Implement export to PDF and Excel for reports

---

## 🐳 Task 7: Deployment Infrastructure

### Docker Compose (Local Dev)

Services: `web` (Next.js), `api` (FastAPI), `postgres` (PostgreSQL 15), `redis` (Redis 7), `mongo` (MongoDB 7), `integration` (ServiceNow connector)

### CI/CD Pipeline (GitHub Actions)

| Stage | Tools | Quality Gates |
|-------|-------|---------------|
| Build | GitHub Actions | Parallel builds per service |
| Unit & Integration Tests | Pytest, HTTPX | Coverage > 80% |
| SAST & Dependency Scan | SonarQube, Snyk | No critical/high vulns |
| Container Build | Docker BuildKit | Image tagged with git SHA |
| Staging Deploy | Helm + ArgoCD | Auto-deploy on main merge |

### Deliverables

- [ ] Create production-ready Dockerfiles (multi-stage builds)
- [ ] Create `docker-compose.yml` for full local environment
- [ ] Set up GitHub Actions CI pipeline
- [ ] Create Helm charts for Kubernetes deployment
- [ ] Create Terraform templates for AWS/Azure
- [ ] Write deployment runbook documentation

---

## 📝 Task 8: REST API Documentation

### Deliverables

- [ ] Generate OpenAPI 3.1 spec (auto-generated by FastAPI)
- [ ] Create Postman collection for all endpoints
- [ ] Set up Swagger/ReDoc UI at `/docs` or `/redoc` (native FastAPI Swagger UI)
- [ ] Document authentication flows and error formats
- [ ] Write API quickstart guide

---

## 🚀 Suggested 12-Week Timeline

| Week | Focus |
|------|-------|
| 1–2 | Scaffolding, DB schema, Auth system |
| 3–4 | Test Repository backend (CRUD, search, versioning) |
| 5–6 | Test Repository frontend (browser, editor, import wizard) |
| 7–8 | ServiceNow Integration (connector, sync, parser) |
| 9–10 | Dashboards, reporting, bulk operations |
| 11 | API docs, deployment infrastructure |
| 12 | Integration testing, bug fixes, documentation |

---

## ✅ Phase 1 Completion Checklist

- [ ] 500+ test cases successfully imported
- [ ] ServiceNow sync operational with at least 1 instance
- [ ] All 6 RBAC roles functional and tested
- [ ] All API endpoints documented in OpenAPI 3.1
- [ ] Deployment achievable in < 2 hours from documentation
- [ ] Unit test coverage > 80%
- [ ] Zero critical/high security vulnerabilities
- [ ] All frontend pages responsive and accessible (WCAG 2.1 AA)
- [ ] Docker Compose local environment working
- [ ] CI/CD pipeline running successfully

---

> **Next Phase:** [Phase 2 — Intelligent Classification](./PHASE_2_README.md)
