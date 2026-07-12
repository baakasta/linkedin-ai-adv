## Tech Stack

- **Python 3.12**
- **FastAPI** — web framework
- **SQLAlchemy 2.0 (async)** — database ORM
- **PostgreSQL** — database
- **Alembic** — database migrations
- **JWT** — authentication
- **uv** — package manager

---

## Requirements

Before starting, make sure you have the following installed:

- [Python 3.12](https://www.python.org/downloads/)
- [PostgreSQL](https://www.postgresql.org/download/) — install and make sure it's running
- [uv](https://docs.astral.sh/uv/getting-started/installation/) — package manager

---

## Setup

### 1 — Clone the repository

```bash
git clone https://github.com/baakasta/linkedin-ai-adv.git
cd linkedin-ai-adv
```

### 2 — Create a virtual environment and install dependencies

```bash
uv venv --python 3.12
```

Activate the virtual environment:

```bash
# Windows
.venv\Scripts\activate

# Mac / Linux
source .venv/bin/activate
```

Then install dependencies:

```bash
uv sync
```

### 3 — Create your PostgreSQL database

Open your PostgreSQL client (pgAdmin or psql) and run:

```sql
CREATE DATABASE linkedin_ai_advisor;
CREATE USER youruser WITH PASSWORD 'yourpassword';
GRANT ALL PRIVILEGES ON DATABASE linkedin_ai_advisor TO youruser;
```

You can use any username and password you want — just make sure they match what you put in your `.env` file in the next step.

### 4 — Set up your environment variables

Copy the example file:

```bash
# Windows
copy .env.example .env

# Mac / Linux
cp .env.example .env
```

Open `.env` and fill in your values:

```
DATABASE_URL=postgresql+asyncpg://youruser:yourpassword@localhost:5432/linkedin_ai_advisor
SECRET_KEY=    ← generate one (see below)
MAIL_USERNAME= ← your Mailtrap username
MAIL_PASSWORD= ← your Mailtrap password
```

**Generating a SECRET_KEY:**

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Copy the output and paste it as the value of `SECRET_KEY` in your `.env`.

**Setting up Mailtrap (for email testing):**

1. Create a free account at [mailtrap.io](https://mailtrap.io)
2. Go to **Email Testing → Inboxes → your inbox → SMTP Settings**
3. Select **Python** from the integrations dropdown
4. Copy the `MAIL_USERNAME` and `MAIL_PASSWORD` values into your `.env`

### 5 — Run database migrations

```bash
python -m alembic upgrade head
```

This creates all the tables in your database automatically.

### 6 — Run the app

```bash
uvicorn backend.main:app --reload
```

The API will be available at `http://localhost:8000`

Interactive API documentation: `http://localhost:8000/docs`

## API Overview

### Auth
| Method | Endpoint | Description | Auth required |
|--------|----------|-------------|---------------|
| POST | `/api/users/create` | Register new user | No |
| POST | `/api/users/token` | Login, get JWT token | No |
| GET | `/api/users/me` | Get current user | Yes |
| PATCH | `/api/users/me` | Update current user | Yes |
| DELETE | `/api/users/me` | Delete current user | Yes |
| PATCH | `/api/users/me/password` | Change password | Yes |
| POST | `/api/users/forgot-password` | Request password reset email | No |
| POST | `/api/users/reset-password` | Reset password with token | No |

### Accounts
| Method | Endpoint | Description | Auth required |
|--------|----------|-------------|---------------|
| GET | `/api/accounts/me` | Get your account | Yes |
| PATCH | `/api/accounts/me` | Update your account | Yes |
| GET | `/api/accounts/me/subscription` | Get your subscription | Yes |

### Companies
| Method | Endpoint | Description | Auth required |
|--------|----------|-------------|---------------|
| GET | `/api/companies/me` | Get your companies | Yes |
| POST | `/api/companies/create` | Create a company | Yes |
| GET | `/api/companies/{id}` | Get a company | Yes |
| PATCH | `/api/companies/{id}` | Update a company | Yes |
| DELETE | `/api/companies/{id}` | Delete a company | Yes |

### Executives
| Method | Endpoint | Description | Auth required |
|--------|----------|-------------|---------------|
| POST | `/api/executives/create` | Create an executive | Yes |
| GET | `/api/executives/{id}` | Get an executive | Yes |
| PATCH | `/api/executives/{id}` | Update an executive | Yes |
| DELETE | `/api/executives/{id}` | Delete an executive | Yes |

---

## How to use the API (quick start)

1. **Register** via `POST /api/users/create`
2. **Login** via `POST /api/users/token` — copy the `access_token` from the response
3. In `/docs`, click **Authorize** and paste the token in the `Value` field
4. All protected endpoints will now work automatically


