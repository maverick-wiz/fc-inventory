"""
Webhooks routes — Webhook registration + inbound POS.
FCINV-232: scaffold — full implementation in sprint stories.
"""
from fastapi import APIRouter, Depends
from app.core.deps import get_current_user, get_tenant_id
from typing import Annotated

router = APIRouter()


@router.get("/", summary="Webhook registration + inbound POS")
async def list_webhooks(
    tenant_id: Annotated[str, Depends(get_tenant_id)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    return {"items": [], "total": 0, "page": 1, "page_size": 20, "has_next": False}
