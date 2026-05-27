"""Products routes — CRUD for tenant-scoped products."""
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.deps import get_current_user, get_tenant_id, require_role
from app.services.inventory_service import (
    get_products, create_product, update_product, soft_delete_product
)
import uuid

router = APIRouter()


class ProductCreate(BaseModel):
    sku: str
    name: str
    category_id: Optional[str] = None
    upc: Optional[str] = None
    unit_cost: float


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    category_id: Optional[str] = None
    upc: Optional[str] = None
    unit_cost: Optional[float] = None


@router.get("/", summary="List products (paginated + filtered)")
async def list_products(
    db: Annotated[AsyncSession, Depends(get_db)],
    tenant_id: Annotated[str, Depends(get_tenant_id)],
    current_user: Annotated[dict, Depends(get_current_user)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sku: Optional[str] = Query(None),
    category_id: Optional[str] = Query(None),
):
    return await get_products(db, uuid.UUID(tenant_id), page, page_size, sku=sku, category_id=uuid.UUID(category_id) if category_id else None)


@router.post("/", status_code=201, summary="Create product")
async def create(
    body: ProductCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    tenant_id: Annotated[str, Depends(get_tenant_id)],
    _: Annotated[dict, Depends(require_role(["store_manager", "tenant_admin"]))],
):
    return await create_product(db, uuid.UUID(tenant_id), body.model_dump())


@router.put("/{sku}", summary="Update product")
async def update(
    sku: str,
    body: ProductUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    tenant_id: Annotated[str, Depends(get_tenant_id)],
    _: Annotated[dict, Depends(require_role(["store_manager", "tenant_admin"]))],
):
    return await update_product(db, uuid.UUID(tenant_id), sku, body.model_dump(exclude_none=True))


@router.delete("/{sku}", status_code=204, summary="Soft-delete product")
async def delete(
    sku: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    tenant_id: Annotated[str, Depends(get_tenant_id)],
    _: Annotated[dict, Depends(require_role(["tenant_admin"]))],
):
    await soft_delete_product(db, uuid.UUID(tenant_id), sku)
