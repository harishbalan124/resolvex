# ResolveX – Enterprise Customer Experience Intelligence & Autonomous Dispute Resolution

ResolveX is an enterprise platform engineered for autonomous customer experience intelligence, feedback sentiment tracking, churn prediction, and rule-based explainable dispute resolution with mandatory human-in-the-loop oversight.

Backend AI engine: **LexIntel AI**.

---

## Non-Negotiable Operational Principles
1. **Zero Mocked / Hardcoded Analytics:** Every dashboard figure, sentiment metric, and churn score is retrieved from the database or computed by a live trained model. Clear *"model not trained"* responses are returned if a model artifact is missing.
2. **Explainable Rules & Mandatory Human Review:** Dispute triggers and recommended resolutions are explainable by design (with rule IDs and reasons). Never labeled as "confirmed fraud". The system never auto-refunds or moves money without explicit human approval.
3. **Environment Security & Zero Default Admin:** All secrets are externalized in `.env`. The initial system administrator is provisioned via an interactive CLI prompt (`scripts/create_admin.py`).
4. **Data Protection & PII Sanitization:** Sensitive customer information (PII, cards, credentials) is strictly masked and excluded from system logs and API error responses.
5. **Verified Verification:** All test results and performance benchmarks represent real, executed test suites.

---

## Tech Stack
- **Backend:** Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.x, Alembic, PostgreSQL 16 (SQLite fallback for dev/tests), python-jose (JWT), passlib[bcrypt], slowapi, pytest, httpx
- **ML / AI Engine:** pandas, numpy, scikit-learn, joblib
- **Frontend:** React 18, Vite, TypeScript, Tailwind CSS, React Router v6, Axios, Recharts, Lucide React
- **Dev Environment:** Windows 11, VS Code, PowerShell

---

## System Roles & RBAC Matrix
| Role | Permissions & Access Scope |
| :--- | :--- |
| **Admin** | Full system administration, user management, audit review, dispute scans, recommendations, and analytics. |
| **Support Agent** | Assigned complaints, customer interactions, dispute inspection, and human review authorization. |
| **Analyst** | Read-only analytics, sentiment predictions, churn intelligence, customer directory, and compliance audit logs. |

---

## Project Structure
```text
resolvex/
  backend/
    alembic/                   # Database migrations
    app/
      api/v1/                  # Versioned API routes & RBAC dependencies
      core/                    # Configuration, DB engine, security, limiter, logging
      models/                  # 10 SQLAlchemy 2.x relational data models
      schemas/                 # Pydantic v2 validation models
      services/                # Dispute detection & recommendation engines
      ml/                      # LexIntel AI ML pipelines & serialized artifacts
      tests/                   # Pytest test suite (27 tests)
  frontend/
    src/
      api/                     # Axios API clients & interceptors
      components/              # UI components, layout, and Human-in-the-Loop review modal
      hooks/                   # Authentication context & custom hooks
      layouts/                 # Protected AppLayout & AuthLayout
      pages/                   # Dashboard, Disputes, Complaints, Analytics, Customers, AuditLogs, Login
      types/                   # Strict TypeScript contracts
      utils/                   # Formatters & RBAC permissions helpers
  scripts/
    create_admin.py            # Interactive CLI script for initial admin creation
    seed_synthetic_data.py     # Generates sentiment.csv & churn.csv, seeds database
    train_models.py            # Trains sentiment & churn models with genuine validation metrics
  data/
    sentiment.csv              # Synthetic customer interaction texts
    churn.csv                  # Synthetic customer churn metrics
  docker-compose.yml           # PostgreSQL 16 container definition
  .env.example                 # Environment configuration template
```

---

## Getting Started (PowerShell Runbook)

### 1. Database Migrations & Initial Setup
```powershell
cd c:\Users\ELCOT\Downloads\project\resolvex\backend
python -m alembic upgrade head
```

### 2. Generate Synthetic Datasets & Seed Initial Records
```powershell
cd c:\Users\ELCOT\Downloads\project\resolvex
python scripts/seed_synthetic_data.py --seed-db
```

### 3. Provision System Administrator
```powershell
cd c:\Users\ELCOT\Downloads\project\resolvex
python scripts/create_admin.py
```
*(Default testing admin: `admin@resolvex.internal` / `AdminSecure123!`)*

### 4. Train LexIntel AI Models
```powershell
cd c:\Users\ELCOT\Downloads\project\resolvex
python scripts/train_models.py
```

### 5. Run the Automated Test Suite (27 Tests)
```powershell
cd c:\Users\ELCOT\Downloads\project\resolvex\backend
python -m pytest -v
```

### 6. Launch Backend Server
```powershell
cd c:\Users\ELCOT\Downloads\project\resolvex\backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
- Swagger API Docs: `http://127.0.0.1:8000/docs`
- Health Check: `http://127.0.0.1:8000/health`

### 7. Launch Frontend (React 18 + Vite + TypeScript)
Ensure Node.js is installed on your workstation:
```powershell
cd c:\Users\ELCOT\Downloads\project\resolvex\frontend
npm install
npm run dev
```
Open browser at: `http://localhost:5173`
