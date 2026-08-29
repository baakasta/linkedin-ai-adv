# LinkedIn AI Advisor

AI-powered SaaS platform for auditing, optimizing, and managing LinkedIn company profiles.

## Tech Stack

| Component | Technology |
|---|---|
| **Backend API** | Python 3.12, FastAPI, SQLAlchemy 2.0 (async), Alembic |
| **AI Service** | Java 21, Spring AI, Mistral API |
| **Database** | PostgreSQL 16 |
| **Auth** | JWT (access + refresh tokens), Argon2 password hashing |
| **PDF Reports** | ReportLab |
| **Package Manager** | uv (Python), Maven (Java) |
| **Containerization** | Docker, Docker Compose |

---

## Prerequisites

- [Docker + Docker Compose](https://docs.docker.com/get-docker/) (recommended)
- OR [Python 3.12](https://www.python.org/downloads/), [uv](https://docs.astral.sh/uv/getting-started/installation/), [Java 21+](https://adoptium.net/), [Maven](https://maven.apache.org/install.html), [PostgreSQL 16](https://www.postgresql.org/download/)
- [Mistral API key](https://console.mistral.ai/) (for AI features)
- SMTP credentials (e.g. a Gmail account with an [app password](https://support.google.com/accounts/answer/185833)) for password-reset emails

---

## Quick Start (Docker — Recommended)

This runs everything: FastAPI backend, Java AI service, and PostgreSQL.

### 1. Clone

```bash
git clone https://github.com/baakasta/linkedin-ai-adv.git
cd linkedin-ai-adv
```

### 2. Create `.env`

```bash
copy .env.example .env        # Windows
cp .env.example .env          # Mac/Linux
```

Fill in your values:

```env
DATABASE_URL=postgresql+asyncpg://useruser:userpass@db:5432/linkedin_project
SECRET_KEY=your-generated-secret-key
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-gmail@gmail.com(entreprise email)
MAIL_PASSWORD=your-gmail-app-password
MAIL_FROM=your-gmail@gmail.com
MAIL_USE_TLS=true
FRONTEND_URL=http://localhost:8000
AI_SERVICE_URL=http://ai-service:8080
MISTRAL_API_KEY=your-mistral-api-key
```
note:(steps to set email):
  1-Go to myaccount.google.com/security
  2-Enable 2-Step Verification on your Google account         
  3-Go to myaccount.google.com/apppasswords
  4-Under "App name", type something like "LinkedIn Advisor" → click Create
  5-Google shows you a 16-character password like abcd efgh ijkl mnop

> **Note:** When running with Docker, `DATABASE_URL` should use `db` as host (the container name), not `localhost`. The `docker-compose.yml` already overrides this.

**Generate a SECRET_KEY:**

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

### 3. Start everything

```bash
docker compose up -d --build
```

This builds and starts all 3 services. Migrations run automatically on startup.

### 4. Verify

```bash
docker compose ps                          # all containers should be "Up"
curl http://localhost:8000/health           # should return {"status":"healthy"}
```

API docs: `http://localhost:8000/docs`

### Common Docker commands

```bash
docker compose up -d --build               # rebuild and start
docker compose down                         # stop and remove containers
docker compose logs -f app                  # follow backend logs
docker compose logs -f ai-service           # follow AI service logs
docker compose exec app alembic upgrade head    # run migrations manually
docker compose exec app alembic revision --autogenerate -m "description"  # create migration
```

---

## Local Development Setup

Run each service separately on your machine.

### 1. Database

Make sure PostgreSQL is running, then create the database:

```sql
CREATE DATABASE linkedin_project;
CREATE USER useruser WITH PASSWORD 'userpass';
GRANT ALL PRIVILEGES ON DATABASE linkedin_project TO useruser;
```

### 2. Backend (FastAPI)

```bash
# Create venv and install dependencies
uv venv --python 3.12
# Windows
.venv\Scripts\activate
# Mac/Linux
source .venv/bin/activate

uv sync
```

Create `.env` (use `localhost` for DATABASE_URL when running locally):

Run migrations and start:

```bash
python -m alembic upgrade head
uvicorn backend.main:app --reload
```

### 3. AI Service (Java / Spring AI)

```bash
cd ai-service
./mvnw spring-boot:run        # Mac/Linux
mvnw.cmd spring-boot:run      # Windows
```

AI Service: `http://localhost:8080`

---

## API Endpoints

### Auth & Users

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/users/create` | Register new user |
| POST | `/api/users/token` | Login (returns access + refresh token) |
| POST | `/api/users/token/refresh` | Refresh access token |
| POST | `/api/users/logout` | Revoke refresh token |
| GET | `/api/users/me` | Get current user |
| PATCH | `/api/users/me` | Update current user |
| DELETE | `/api/users/me` | Delete current user |
| PATCH | `/api/users/me/password` | Change password |
| POST | `/api/users/forgot-password` | Request password reset email |
| POST | `/api/users/reset-password` | Reset password with token |

### Accounts & Companies

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/accounts/me` | Get my account |
| PATCH | `/api/accounts/me` | Update my account |
| GET | `/api/accounts/me/subscription` | Get my subscription |
| GET | `/api/companies/me` | List my companies |
| POST | `/api/companies/create` | Create company |
| GET | `/api/companies/{id}` | Get company |
| PATCH | `/api/companies/{id}` | Update company |
| DELETE | `/api/companies/{id}` | Delete company |

### Executives

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/executives/{id}` | Get executive |
| POST | `/api/executives/create` | Create executive |
| PATCH | `/api/executives/{id}` | Update executive |
| DELETE | `/api/executives/{id}` | Delete executive |

### AI Modules

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/audits` | Run LinkedIn audit |
| GET | `/api/audits/company/{id}` | List audits for company |
| GET | `/api/audits/{id}` | Get audit detail |
| GET | `/api/audits/{id}/recommendations` | Get recommendations |
| GET | `/api/audits/{id}/optimizations` | Get recommendations + optimizations |
| POST | `/api/optimizations` | Generate optimization variants |
| GET | `/api/optimizations/{id}` | Get optimization detail |
| PATCH | `/api/optimizations/decisions` | Accept/modify/reject optimizations |
| POST | `/api/generations` | Generate LinkedIn content |
| GET | `/api/generations/{id}` | Get generation detail |
| GET | `/api/generations/company/{id}` | List generations for company |
| POST | `/api/benchmarks` | Run competitor benchmark (**Pro+**) |
| GET | `/api/benchmarks/{id}` | Get benchmark detail |
| GET | `/api/benchmarks/company/{id}` | List benchmarks for company |

### Stratégie (LinkedIn Strategy — Module 3)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/strategies` | Generate LinkedIn strategy (placeholder until AI wired) |
| GET | `/api/strategies/{strategy_id}` | Get strategy detail |
| GET | `/api/strategies/company/{company_id}` | List strategies for company |

> Currently returns a local placeholder result (`sources_placeholders: true`). See [AI Developer Integration](#ai-developer-integration) to wire the Java AI engine.

### Assistant IA (Chat — Module 7)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/assistant/conversations` | Create a new conversation |
| GET | `/api/assistant/conversations/{conversation_id}` | Get conversation detail |
| GET | `/api/assistant/conversations/company/{company_id}` | List conversations for company |
| POST | `/api/assistant/conversations/{conversation_id}/messages` | Send a message (`content`), returns assistant reply |
| GET | `/api/assistant/conversations/{conversation_id}/messages` | List conversation messages |

> Sending a message stores the user's message and returns an assistant reply. Until the Java AI service is wired, the reply is a placeholder marked `[Assistant IA - mode placeholder]`. See [AI Developer Integration](#ai-developer-integration).

### Calendar

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/calendars` | Create editorial calendar |
| GET | `/api/calendars/company/{id}` | Get calendar for company |
| PATCH | `/api/calendars/company/{id}` | Update calendar |
| POST | `/api/calendars/slots/{id}/generate` | Generate content for slot |
| DELETE | `/api/calendars/slots/{id}` | Delete calendar slot |

### Veille (Competitor Watch)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/watches` | Create watch |
| GET | `/api/watches/{id}` | Get watch |
| PATCH | `/api/watches/{id}` | Update watch |
| DELETE | `/api/watches/{id}` | Delete watch |
| POST | `/api/watches/{id}/snapshots?audit_id=` | Create snapshot |
| GET | `/api/watches/{id}/snapshots` | List snapshots |
| GET | `/api/watches/{id}/alerts` | List alerts |
| PATCH | `/api/watches/{id}/alerts/{alert_id}` | Mark alert read |
| GET | `/api/watches/{id}/overview` | Full overview with AI analysis |

### Dashboard & Reports

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/companies/{id}/dashboard` | Company dashboard |
| GET | `/api/reports/audit/{id}` | Audit PDF report |
| GET | `/api/reports/benchmark/{id}` | Benchmark PDF report |
| GET | `/api/reports/monthly` | Monthly PDF report |
| GET | `/api/reports/history` | Report history |
| POST | `/api/reports/share` | Create share link |
| GET | `/api/reports/shared/{token}` | Access shared report |
| DELETE | `/api/reports/share/{token}` | Revoke share link |

### Admin (ADMIN role required)

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/admin/stats` | Platform-wide statistics |
| GET | `/api/admin/usage` | Per-account feature usage |
| GET | `/api/admin/users` | List all users |
| PATCH | `/api/admin/users/{id}` | Update user (role, active) |
| GET | `/api/admin/accounts` | List all accounts |
| PATCH | `/api/admin/accounts/{id}/subscription` | Change subscription |
| GET | `/api/admin/companies` | List all companies |
| GET | `/api/admin/executives` | List all executives |

---

## Subscription Plans & Feature Gating

Plans follow the CDC (`backend/models/subscription.py`): **Découverte** (default), **Pro**, **Business**. Each account has one subscription; every user in the account shares it.

> Legend: ✔ included · ✔ `N/mois` included with a monthly usage limit · ✘ not included

No plan includes every module — module availability depends on the tier:

| Module | Feature | Découverte | Pro | Business |
|---|---|---|---|---|
| 1 | Audit IA | ✔ 5/mois | ✔ | ✔ |
| 2 | Optimisation IA | ✔ 5/mois | ✔ | ✔ |
| 3 | Stratégie LinkedIn | ✔ 1/mois | ✔ | ✔ |
| 4 | Générateur de contenu | ✔ 3/mois | ✔ | ✔ |
| 5 | Calendrier éditorial | ✘ | ✔ | ✔ |
| 6 | Benchmark concurrentiel | ✘ | ✔ | ✔ |
| 7 | Assistant IA | ✘ | ✔ | ✔ |
| 8 | Tableau de bord | ✔ | ✔ | ✔ |
| 9 | Veille | ✘ | ✘ | ✔ |
| 10 | Rapports PDF | ✘ | ✔ | ✔ |

- **Découverte** — 5 of 10 modules: Audit, Optimisation, Stratégie, Générateur, Tableau de bord, each with a **monthly usage limit** (see [AI Usage Quotas](#ai-usage-quotas-how-to-change-the-numbers)).
- **Pro** — 9 of 10 modules: everything except **Veille** (M9). Unlimited AI usage.
- **Business** — **all 10 modules**, unlimited AI usage, plus multiple companies and executives.

Gating is enforced server-side via `backend/dependencies.py` (`require_plan`, `check_plan_access`). Insufficient plans return `403 Forbidden` with an explanatory message. Inactive/missing subscriptions block all gated features.

**Company limit:** Découverte and Pro accounts may register **1 company**; Business accounts have no limit (`POST /api/companies/create` enforces this).

> Shared-report links (`/api/reports/shared/{token}`) stay accessible to recipients regardless of the owner's plan.

Change a plan via the admin endpoint:

```bash
curl -X PATCH http://localhost:8000/api/admin/accounts/{account_id}/subscription \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"plan_tier":"business"}'
```

---

## AI Developer Integration

The Python backend calls the Java AI service through `backend/services/ai_client.py` (`call_ai_or_placeholder`). For every AI feature it:

1. POSTs the request to `{AI_SERVICE_URL}{path}` with an `x-company-id` header.
2. Returns the Java response JSON unchanged on success.
3. Falls back to a **pure-Python placeholder** on any error (Java down, timeout, non-200).

This means the whole app is testable end-to-end **without** the Java service running. Responses built locally are marked `sources_placeholders: true` (strategy) or prefixed `[Assistant IA - mode placeholder]` (chat) so it's obvious when real AI isn't wired.

### Java endpoints to implement

The Java service should expose the following endpoints (matching the schemas in `backend/schemas/`):

| Feature | Python router | Java endpoint (from `ai_client`) | Payload sent |
|---|---|---|---|
| LinkedIn Strategy (M3) | `backend/routers/strategy.py` | `POST /api/strategies` | `{"company_id": uuid, ...}` via `x-company-id` header, on `/api/strategies` |
| Assistant Chat (M7) | `backend/routers/assistant.py` | `POST /api/assistant/chat` | `{"conversation_id": uuid, "content": "...", "history": [...]}` |

### Strategy contract

`POST /api/strategies` must return JSON with this shape (see `strategyschema.StrategyResponse.resultat`):

```json
{
  "niveau_maturite": "...",
  "note_globale": 0,
  "cibles": [{"segments": [...], "besoins": [...]}],
  "objets": [{"axe": "...", "objectif": "...", "actions": [...]}],
  "planning": {"frequence": "...", "horaires": [...], "repartition": [{"type": "...", "proportion": "..."}]}
}
```

### Assistant chat contract

`POST /api/assistant/chat` must return the assistant's reply text as JSON `{"content": "..."}`, which the Python router stores as a message with `author = "assistant"`.

---

## Project Structure

```
linkedin-ai-adv/
├── backend/
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Settings (env vars)
│   ├── auth.py                 # JWT, password hashing, dependencies
│   ├── db/
│   │   └── db.py               # Database engine + session
│   ├── models/                 # SQLAlchemy models
│   ├── schemas/                # Pydantic request/response schemas
│   ├── routers/                # API route modules
│   │   ├── users.py            # Auth, user CRUD
│   │   ├── accounts.py         # Account management
│   │   ├── companies.py        # Company CRUD
│   │   ├── executives.py       # Executive CRUD
│   │   ├── ai.py               # Audit, optimization, generation, benchmark
│   │   ├── strategy.py         # Module 3 — LinkedIn strategy
│   │   ├── assistant.py        # Module 7 — Assistant IA chat
│   │   ├── calendar.py         # Editorial calendar
│   │   ├── veille.py           # Competitor watch
│   │   ├── dashboard.py        # Company dashboard
│   │   ├── reports.py          # PDF reports + sharing
│   │   └── admin.py            # Admin endpoints
│   ├── services/               # Business logic
│   │   ├── ai_client.py        # Calls Java AI service (placeholder fallback)
│   │   ├── strategy.py         # Module 3 placeholder strategy builder
│   │   └── assistant.py        # Module 7 placeholder assistant builder
│   └── scheduler.py            # Auto-generation cron loop
├── ai-service/                 # Java Spring AI service
│   ├── src/
│   ├── pom.xml
│   └── Dockerfile
├── alembic/                    # Database migrations
│   └── versions/
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
└── uv.lock
```

---

## Migrations

```bash
# Create a new migration after model changes
docker compose exec app alembic revision --autogenerate -m "description"

# Or locally:
python -m alembic revision --autogenerate -m "description"

# Apply migrations
docker compose exec app alembic upgrade head
# Or locally:
python -m alembic upgrade head

# Rollback one step
docker compose exec app alembic downgrade -1
```

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | Yes | — | PostgreSQL connection string |
| `SECRET_KEY` | Yes | — | JWT signing key |
| `MISTRAL_API_KEY` | Yes | — | Mistral AI API key |
| `MAIL_SERVER` | No | `localhost` | SMTP server |
| `MAIL_PORT` | No | `2525` | SMTP port |
| `MAIL_USERNAME` | No | `""` | SMTP username |
| `MAIL_PASSWORD` | No | `""` | SMTP password |
| `MAIL_FROM` | No | `3LM@example.com` | Sender email |
| `MAIL_USE_TLS` | No | `true` | Enable TLS |
| `FRONTEND_URL` | No | `http://localhost:8000` | Frontend URL |
| `AI_SERVICE_URL` | No | `http://localhost:8080` | Java AI service URL |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `30` | JWT access token TTL |
| `REFRESH_TOKEN_EXPIRE_DAYS` | No | `7` | Refresh token TTL |
| `RESET_TOKEN_EXPIRE_MINUTES` | No | `60` | Password reset token TTL |
| `SCHEDULER_INTERVAL_HOURS` | No | `24` | Auto-generation check interval |
| `GENERATION_LOOKAHEAD_DAYS` | No | `7` | How far ahead to auto-generate |

---

## AI Usage Quotas (how to change the numbers)

Per-plan **monthly** limits are enforced on the AI create endpoints: `POST /api/audits`, `POST /api/optimizations`, `POST /api/generations`, `POST /api/strategies`. Counters reset at the start of each calendar month (UTC). When the limit is reached the endpoint returns `403` with a message like `Monthly quota reached (5/5 audits) on the decouverte plan`.

Module inclusion by plan — all **10 modules**:

| Module | Feature | Découverte | Pro | Business |
|---|---|---|---|---|
| 1 | Audit IA | ✔ 5/mois | ✔ | ✔ |
| 2 | Optimisation IA | ✔ 5/mois | ✔ | ✔ |
| 3 | Stratégie LinkedIn | ✔ 1/mois | ✔ | ✔ |
| 4 | Générateur de contenu | ✔ 3/mois | ✔ | ✔ |
| 5 | Calendrier éditorial | ✘ | ✔ | ✔ |
| 6 | Benchmark concurrentiel | ✘ | ✔ | ✔ |
| 7 | Assistant IA | ✘ | ✔ | ✔ |
| 8 | Tableau de bord | ✔ | ✔ | ✔ |
| 9 | Veille | ✘ | ✘ | ✔ |
| 10 | Rapports PDF | ✘ | ✔ | ✔ |

> Only modules 1–4 carry usage quotas (on Découverte); all modules on Pro/Business are unlimited.

**To change the numbers** (the 4 quota keys above), edit the `AI_QUOTAS` dict at the top of `backend/services/quotas.py`:

```python
AI_QUOTAS: dict[PlanTier, dict[str, int | None]] = {
    PlanTier.DECOUVERTE: {
        "audits": 5,            # change this value
        "optimizations": 5,
        "generations": 3,
        "strategies": 1,
    },
    PlanTier.PRO: {
        "audits": None,         # None = unlimited
        "optimizations": None,
        "generations": None,
        "strategies": None,
    },
    PlanTier.BUSINESS: {
        "audits": None,
        "optimizations": None,
        "generations": None,
        "strategies": None,
    },
}
```

- Feature keys: `audits`, `optimizations`, `generations`, `strategies`.
- A limit is a positive integer. `None` (or omitting the key) means the plan has **no limit** for that feature.
- To add a feature, add a key here **and** a branch in `count_feature_usage()` in the same file.

The quota check runs **before** the AI service is called, and counts rows created during the current month for all companies of the account (the 1-company limit applies to Découverte/Pro, so this is effectively per-account).

Reapply after editing:

```bash
docker compose up -d --build app
```
