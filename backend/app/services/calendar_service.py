"""Calendar event business logic."""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from fastapi import HTTPException
from app.db.models.models import CalendarEvent, CalendarEventType


async def list_events(
    db: AsyncSession, tenant_id: uuid.UUID,
    from_ts: Optional[datetime] = None, to_ts: Optional[datetime] = None,
    event_type: Optional[str] = None,
) -> list:
    filters = [CalendarEvent.tenant_id == tenant_id]
    if from_ts:
        filters.append(CalendarEvent.start_ts >= from_ts)
    if to_ts:
        filters.append(CalendarEvent.start_ts <= to_ts)
    if event_type:
        filters.append(CalendarEvent.type == CalendarEventType(event_type))

    result = await db.execute(select(CalendarEvent).where(and_(*filters)))
    return [_event_to_dict(e) for e in result.scalars().all()]


async def create_event(db: AsyncSession, tenant_id: uuid.UUID, data: dict) -> dict:
    event = CalendarEvent(
        id=uuid.uuid4(), tenant_id=tenant_id,
        type=CalendarEventType(data["type"]),
        linked_entity=uuid.UUID(data["linked_entity"]) if data.get("linked_entity") else None,
        start_ts=data["start_ts"], end_ts=data.get("end_ts"),
        rrule=data.get("rrule"),
    )
    db.add(event)

    # Conflict detection for deliveries
    if event.type == CalendarEventType.delivery and data.get("linked_entity"):
        conflicts_q = await db.execute(
            select(CalendarEvent).where(
                CalendarEvent.tenant_id == tenant_id,
                CalendarEvent.type == CalendarEventType.delivery,
                CalendarEvent.linked_entity == event.linked_entity,
                CalendarEvent.id != event.id,
                CalendarEvent.start_ts < event.end_ts,
                CalendarEvent.end_ts > event.start_ts,
            )
        )
        conflicts = conflicts_q.scalars().all()
        if conflicts and not data.get("force"):
            raise HTTPException(status_code=409, detail={
                "message": "Delivery window conflict",
                "conflicting_event_ids": [str(c.id) for c in conflicts]
            })

    await db.commit()
    await db.refresh(event)
    return _event_to_dict(event)


async def update_event(db: AsyncSession, tenant_id: uuid.UUID, event_id: str, data: dict) -> dict:
    result = await db.execute(
        select(CalendarEvent).where(CalendarEvent.id == uuid.UUID(event_id), CalendarEvent.tenant_id == tenant_id)
    )
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    for k, v in data.items():
        if hasattr(event, k) and v is not None:
            setattr(event, k, v)
    await db.commit()
    await db.refresh(event)
    return _event_to_dict(event)


def _event_to_dict(e: CalendarEvent) -> dict:
    return {
        "id": str(e.id), "type": e.type.value,
        "linked_entity": str(e.linked_entity) if e.linked_entity else None,
        "start_ts": str(e.start_ts), "end_ts": str(e.end_ts) if e.end_ts else None,
        "rrule": e.rrule,
    }
