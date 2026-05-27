"""Purchase order routes."""
from typing import Annotated, Optional, List
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.deps import get_current_user, get_tenant_id, require_role
from app.services.order_service import create_purchase_order, list_purchase_orders, receive_purchase_order
import uuid

router = APIRouter()


class LineItemCreate(BaseModel):
    product_id: str
    qty_ordered: int
    unit_cost: float


class POCreate(BaseModel):
    supplier_id: str
    expected_date: Optional[str] = None
    line_items: List[LineItemCreate]


class LineReceive(BaseModel):
    line_item_id: str
    qty_received: int
    warehouse_id: str


@router.get("/", summary="List purchase orders")
async def list_pos(
    db: Annotated[AsyncSession, Depends(get_db)],
    tenant_id: Annotated[str, Depends(get_tenant_id)],
    current_user: Annotated[dict, Depends(get_current_user)],
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    return await list_purchase_orders(db, uuid.UUID(tenant_id), status_filter=status, page=page, page_size=page_size)


@router.post("/", status_code=201, summary="Create purchase order")
async def create_po(
    body: POCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    tenant_id: Annotated[str, Depends(get_tenant_id)],
    _: Annotated[dict, Depends(require_role(["store_manager", "tenant_admin"]))],
):
    return await create_purchase_order(db, uuid.UUID(tenant_id), body.model_dump())


@router.patch("/{po_id}/receive", summary="Receive PO lines → increments stock")
async def receive_po(
    po_id: str,
    body: List[LineReceive],
    db: Annotated[AsyncSession, Depends(get_db)],
    tenant_id: Annotated[str, Depends(get_tenant_id)],
    _: Annotated[dict, Depends(require_role(["warehouse_op", "store_manager", "tenant_admin"]))],
):
    return await receive_purchase_order(db, uuid.UUID(tenant_id), po_id, [r.model_dump() for r in body])
