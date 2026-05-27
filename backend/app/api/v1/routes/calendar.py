"""Calendar routes — events CRUD with RFC 5545 recurrence."""
from typing import Annotated, Optional, List
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.deps import get_current_user, get_tenant_id
from app.services.calendar_service import list_events, create_event, update_event
import uuid

router = APIRouter()


class EventCreate(BaseModel):
    type: str  # delivery | store_audit | promo | reorder
    linked_entity: Optional[str] = None
    start_ts: str
    end_ts: Optional[str] = None
    rrule: Optional[str] = None
    force: bool = False


@router.get("/events", summary="List calendar events (date range)")
async def list_cal(
    db: Annotated[AsyncSession, Depends(get_db)],
    tenant_id: Annotated[str, Depends(get_tenant_id)],
    current_user: Annotated[dict, Depends(get_current_user)],
    type: Optional[str] = Query(None),
):
    return await list_events(db, uuid.UUID(tenant_id), event_type=type)


@router.post("/events", status_code=201, summary="Create calendar event")
async def create_cal(
    body: EventCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    tenant_id: Annotated[str, Depends(get_tenant_id)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    from datetime import datetime
    data = body.model_dump()
    data["start_ts"] = datetime.fromisoformat(data["start_ts"])
    if data.get("end_ts"):
        data["end_ts"] = datetime.fromisoformat(data["end_ts"])
    return await create_event(db, uuid.UUID(tenant_id), data)


@router.put("/events/{event_id}", summary="Update / reschedule event")
async def update_cal(
    event_id: str,
    body: EventCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    tenant_id: Annotated[str, Depends(get_tenant_id)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    return await update_event(db, uuid.UUID(tenant_id), event_id, body.model_dump(exclude_none=True))
