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
- [Mailtrap](https://mailtrap.io/) account (for email testing in dev)

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
MAIL_SERVER=sandbox.smtp.mailtrap.io
MAIL_PORT=2525
MAIL_USERNAME=your-mailtrap-username
MAIL_PASSWORD=your-mailtrap-password
MAIL_FROM=3LM@example.com
MAIL_USE_TLS=true
FRONTEND_URL=http://localhost:8000
AI_SERVICE_URL=http://ai-service:8080
MISTRAL_API_KEY=your-mistral-api-key
```

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

```env
DATABASE_URL=postgresql+asyncpg://useruser:userpass@localhost:5432/linkedin_project
SECRET_KEY=your-generated-secret-key
MAIL_SERVER=sandbox.smtp.mailtrap.io
MAIL_PORT=2525
MAIL_USERNAME=your-mailtrap-username
MAIL_PASSWORD=your-mailtrap-password
MAIL_FROM=3LM@example.com
MAIL_USE_TLS=true
FRONTEND_URL=http://localhost:8000
AI_SERVICE_URL=http://localhost:8080
MISTRAL_API_KEY=your-mistral-api-key
```

Run migrations and start:

```bash
python -m alembic upgrade head
uvicorn backend.main:app --reload
```

Backend: `http://localhost:8000` — Docs: `http://localhost:8000/docs`

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
| POST | `/api/ai/audits` | Run LinkedIn audit |
| GET | `/api/ai/audits/company/{id}` | List audits for company |
| GET | `/api/ai/audits/{id}` | Get audit detail |
| GET | `/api/ai/audits/{id}/recommendations` | Get recommendations |
| GET | `/api/ai/audits/{id}/optimizations` | Get recommendations + optimizations |
| POST | `/api/ai/optimizations` | Generate optimization variants |
| GET | `/api/ai/optimizations/{id}` | Get optimization detail |
| PATCH | `/api/ai/optimizations/decisions` | Accept/modify/reject optimizations |
| POST | `/api/ai/generations` | Generate LinkedIn content |
| GET | `/api/ai/generations/{id}` | Get generation detail |
| GET | `/api/ai/generations/company/{id}` | List generations for company |
| POST | `/api/ai/benchmarks` | Run competitor benchmark |
| GET | `/api/ai/benchmarks/{id}` | Get benchmark detail |
| GET | `/api/ai/benchmarks/company/{id}` | List benchmarks for company |

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
│   │   ├── calendar.py         # Editorial calendar
│   │   ├── veille.py           # Competitor watch
│   │   ├── dashboard.py        # Company dashboard
│   │   ├── reports.py          # PDF reports + sharing
│   │   └── admin.py            # Admin endpoints
│   ├── services/               # Business logic
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
