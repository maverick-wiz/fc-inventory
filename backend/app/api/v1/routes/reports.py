"""Reports routes — sync + async generation."""
import uuid
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from app.db.session import get_db
from app.core.deps import get_current_user, get_tenant_id

router = APIRouter()


@router.get("/{report_type}", summary="Generate or retrieve report")
async def get_report(
    report_type: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    tenant_id: Annotated[str, Depends(get_tenant_id)],
    current_user: Annotated[dict, Depends(get_current_user)],
    from_dt: str = Query(..., alias="from"),
    to_dt: str = Query(..., alias="to"),
    warehouse_id: Optional[str] = Query(None),
):
    from app.services.report_service import generate_report
    from_parsed = datetime.fromisoformat(from_dt)
    to_parsed = datetime.fromisoformat(to_dt)
    days = (to_parsed - from_parsed).days

    if days > 30:
        # Async path
        snapshot_id = str(uuid.uuid4())
        from app.workers.tasks import generate_report_async
        try:
            generate_report_async.delay(
                tenant_id, report_type,
                {"from": from_dt, "to": to_dt, "warehouse_id": warehouse_id},
                snapshot_id
            )
        except Exception:
            pass
        return JSONResponse(status_code=202, content={
            "report_id": snapshot_id, "status": "processing",
            "message": "Large report queued. Poll GET /reports/{id}/status"
        })

    return await generate_report(db, uuid.UUID(tenant_id), report_type, from_parsed, to_parsed, warehouse_id)


@router.get("/{report_id}/download", summary="Download report as PDF or CSV")
async def download_report(
    report_id: str,
    tenant_id: Annotated[str, Depends(get_tenant_id)],
    current_user: Annotated[dict, Depends(get_current_user)],
    format: str = Query("pdf", pattern="^(pdf|csv)$"),
):
    # TODO: fetch s3_key from report_snapshots and return presigned URL
    return {"report_id": report_id, "format": format, "url": f"https://s3.example.com/reports/{report_id}.{format}"}
