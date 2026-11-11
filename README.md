# LeadFlow

**LeadFlow** is a lightweight lead intake and management API for small businesses.
It accepts customer requests, stores them in SQLite, lets an administrator search
and update their status, and can send new-lead notifications to Telegram.

> Portfolio project: the first version is an API backend. It does not claim to be
> a complete CRM or a production-hardened service.

## Features

- Create leads with name, phone, service and message.
- Store data in SQLite using parameterized SQL queries.
- List, filter and search leads with pagination.
- Update a lead status: `new`, `in_progress`, `completed`, `rejected`.
- View a summary report grouped by status.
- Optional Telegram notification on new lead.
- Interactive API documentation via Swagger UI.
- Automated API tests.

## Stack

Python 3.11+, FastAPI, SQLite, Pydantic, HTTPX, pytest.

## Run locally

```bash
# 1. Create and activate a virtual environment
python -m venv .venv

# Windows PowerShell
.venv\\Scripts\\Activate.ps1

# macOS / Linux
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create local configuration
# Windows: copy .env.example .env
# macOS/Linux: cp .env.example .env

# 4. Start the API
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for interactive API documentation.

## API examples

Create a lead:

```bash
curl -X POST "http://127.0.0.1:8000/leads" \\
  -H "Content-Type: application/json" \\
  -d '{"name":"Ivan Petrov","phone":"+79990000000","service":"Laptop repair","message":"Device will not start"}'
```

List leads:

```bash
curl "http://127.0.0.1:8000/leads?status=new&limit=20"
```

Search:

```bash
curl "http://127.0.0.1:8000/leads?search=Ivan"
```

Change status:

```bash
curl -X PATCH "http://127.0.0.1:8000/leads/1/status" \\
  -H "Content-Type: application/json" \\
  -d '{"status":"in_progress"}'
```

Get report:

```bash
curl "http://127.0.0.1:8000/reports/summary"
```

## Telegram notifications (optional)

1. Create a bot with BotFather and obtain its token.
2. Get the chat ID for the administrator.
3. Put both values in `.env`.
4. Restart the API.

If Telegram is not configured or is temporarily unavailable, the lead is still
saved. Never commit `.env` or publish real bot tokens.

## Run tests

```bash
pytest -q
```

## Project structure

```text
LeadFlow/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   ├── main.py
│   ├── notifications.py
│   └── schemas.py
├── tests/
│   └── test_api.py
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

## Current limitations

- No authentication or role management yet.
- No web dashboard yet; the API docs are used to demonstrate operations.
- No editing/deleting customer contact details.
- SQLite is intended for a small demo workload, not concurrent high-volume use.
- Telegram delivery is best-effort and is not stored in a retry queue.
- Before real business use, add authentication, rate limiting, backups, audit logs,
  privacy controls and deployment configuration.

## Roadmap

- [ ] Add admin authentication and authorization.
- [ ] Add a simple web admin dashboard.
- [ ] Add CSV/XLSX export.
- [ ] Add audit history for status changes.
- [ ] Add notification retry queue and delivery log.
- [ ] Add Docker deployment and CI workflow.

## Portfolio demo checklist

- [ ] Run the API locally.
- [ ] Create at least three sample leads.
- [ ] Demonstrate search and status changes.
- [ ] Show the summary endpoint.
- [ ] Run tests and capture the result.
- [ ] Add screenshots of `/docs` and example responses.
- [ ] Publish the repository with `.env` excluded.
