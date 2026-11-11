from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from app.database import get_connection, init_db
from app.schemas import LeadCreate, LeadOut, LeadStatusUpdate
from app.notifications import notify_admin_about_lead


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="LeadFlow API",
    description="A lightweight lead intake and management service for small businesses.",
    version="1.0.0",
    lifespan=lifespan,
)


def row_to_dict(row):
    return dict(row) if row is not None else None


@app.get("/health")
def health():
    return {"status": "ok", "service": "LeadFlow"}


@app.post("/leads", response_model=LeadOut, status_code=201)
async def create_lead(payload: LeadCreate):
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO leads (name, phone, service, message)
            VALUES (?, ?, ?, ?)
            """,
            (payload.name.strip(), payload.phone.strip(),
             payload.service.strip(), payload.message.strip()),
        )
        lead_id = cursor.lastrowid
        row = connection.execute(
            "SELECT * FROM leads WHERE id = ?", (lead_id,)
        ).fetchone()
        lead = row_to_dict(row)

    # Notification is optional and cannot roll back a successfully saved lead.
    await notify_admin_about_lead(lead)
    return lead


@app.get("/leads", response_model=list[LeadOut])
def list_leads(
    status: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None, max_length=100),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    allowed_statuses = {"new", "in_progress", "completed", "rejected"}
    if status and status not in allowed_statuses:
        raise HTTPException(status_code=422, detail="Unknown lead status")

    sql = "SELECT * FROM leads WHERE 1 = 1"
    params = []
    if status:
        sql += " AND status = ?"
        params.append(status)
    if search:
        sql += " AND (name LIKE ? OR phone LIKE ? OR service LIKE ?)"
        pattern = f"%{search}%"
        params.extend([pattern, pattern, pattern])
    sql += " ORDER BY id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with get_connection() as connection:
        rows = connection.execute(sql, params).fetchall()
    return [row_to_dict(row) for row in rows]


@app.get("/leads/{lead_id}", response_model=LeadOut)
def get_lead(lead_id: int):
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM leads WHERE id = ?", (lead_id,)
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Lead not found")
    return row_to_dict(row)


@app.patch("/leads/{lead_id}/status", response_model=LeadOut)
def update_lead_status(lead_id: int, payload: LeadStatusUpdate):
    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE leads
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (payload.status, lead_id),
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Lead not found")
        row = connection.execute(
            "SELECT * FROM leads WHERE id = ?", (lead_id,)
        ).fetchone()
    return row_to_dict(row)


@app.get("/reports/summary")
def report_summary():
    with get_connection() as connection:
        total = connection.execute(
            "SELECT COUNT(*) AS count FROM leads"
        ).fetchone()["count"]
        rows = connection.execute(
            "SELECT status, COUNT(*) AS count FROM leads GROUP BY status"
        ).fetchall()
    by_status = {row["status"]: row["count"] for row in rows}
    for status in ("new", "in_progress", "completed", "rejected"):
        by_status.setdefault(status, 0)
    return {"total": total, "by_status": by_status}
