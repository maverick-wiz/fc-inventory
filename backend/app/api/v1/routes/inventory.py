"""Inventory routes — stock levels, transactions, low-stock."""
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.deps import get_current_user, get_tenant_id, require_role
from app.services.inventory_service import (
    get_inventory_levels, record_stock_transaction, get_low_stock
)
import uuid

router = APIRouter()


class StockTransactionRequest(BaseModel):
    product_id: str
    warehouse_id: str
    type: str  # receive | pick | transfer | writeoff | return
    qty: int
    destination_warehouse_id: Optional[str] = None


@router.get("/", summary="Stock levels by warehouse + SKU")
async def list_inventory(
    db: Annotated[AsyncSession, Depends(get_db)],
    tenant_id: Annotated[str, Depends(get_tenant_id)],
    current_user: Annotated[dict, Depends(get_current_user)],
    warehouse_id: Optional[str] = Query(None),
    sku: Optional[str] = Query(None),
):
    return await get_inventory_levels(db, uuid.UUID(tenant_id), warehouse_id=warehouse_id, sku=sku)


@router.post("/transactions", status_code=201, summary="Record stock movement")
async def transaction(
    body: StockTransactionRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    tenant_id: Annotated[str, Depends(get_tenant_id)],
    _: Annotated[dict, Depends(require_role(["warehouse_op", "store_manager", "tenant_admin"]))],
):
    return await record_stock_transaction(db, uuid.UUID(tenant_id), body.model_dump())


@router.get("/low-stock", summary="All SKUs below reorder point")
async def low_stock(
    db: Annotated[AsyncSession, Depends(get_db)],
    tenant_id: Annotated[str, Depends(get_tenant_id)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    return await get_low_stock(db, uuid.UUID(tenant_id))
