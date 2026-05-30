"""
Inventory business logic: products, stock transactions, levels, low-stock.
"""
import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from fastapi import HTTPException
from app.db.models.models import (
    Product, InventoryLevel, StockTransaction,
    StockTransactionType, Supplier
)
from app.workers.tasks import dispatch_low_stock_alert
import logging

log = logging.getLogger(__name__)


async def get_products(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    page: int = 1,
    page_size: int = 20,
    sku: Optional[str] = None,
    category_id: Optional[uuid.UUID] = None,
    warehouse_id: Optional[uuid.UUID] = None,
    status_filter: Optional[str] = None,
) -> dict:
    filters = [Product.tenant_id == tenant_id, not Product.is_deleted]
    if sku:
        filters.append(Product.sku.ilike(f"%{sku}%"))
    if category_id:
        filters.append(Product.category_id == category_id)

    q = select(Product).where(and_(*filters)).offset((page - 1) * page_size).limit(page_size)
    total_q = select(func.count()).select_from(Product).where(and_(*filters))

    result = await db.execute(q)
    total = await db.execute(total_q)
    products = result.scalars().all()

    return {
        "items": [_product_to_dict(p) for p in products],
        "total": total.scalar_one(),
        "page": page,
        "page_size": page_size,
        "has_next": (page * page_size) < total.scalar_one(),
    }


async def create_product(db: AsyncSession, tenant_id: uuid.UUID, data: dict) -> dict:
    # Check duplicate SKU for tenant
    existing = await db.execute(
        select(Product).where(Product.tenant_id == tenant_id, Product.sku == data["sku"])
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"SKU '{data['sku']}' already exists for this tenant")

    product = Product(
        id=uuid.uuid4(), tenant_id=tenant_id,
        sku=data["sku"], name=data["name"],
        category_id=data.get("category_id"), upc=data.get("upc"),
        unit_cost=data["unit_cost"], is_deleted=False
    )
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return _product_to_dict(product)


async def update_product(db: AsyncSession, tenant_id: uuid.UUID, sku: str, data: dict) -> dict:
    result = await db.execute(
        select(Product).where(Product.tenant_id == tenant_id, Product.sku == sku, not Product.is_deleted)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    for k, v in data.items():
        if hasattr(product, k) and v is not None:
            setattr(product, k, v)
    await db.commit()
    await db.refresh(product)
    return _product_to_dict(product)


async def soft_delete_product(db: AsyncSession, tenant_id: uuid.UUID, sku: str):
    result = await db.execute(
        select(Product).where(Product.tenant_id == tenant_id, Product.sku == sku)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product.is_deleted = True
    await db.commit()


async def record_stock_transaction(
    db: AsyncSession, tenant_id: uuid.UUID, data: dict
) -> dict:
    """Atomic: update inventory_levels + append immutable ledger entry."""
    product_id = uuid.UUID(data["product_id"])
    warehouse_id = uuid.UUID(data["warehouse_id"])
    txn_type = StockTransactionType(data["type"])
    qty = int(data["qty"])

    if qty <= 0:
        raise HTTPException(status_code=422, detail="qty must be positive")

    # Get or create inventory level
    level_result = await db.execute(
        select(InventoryLevel).where(
            InventoryLevel.product_id == product_id,
            InventoryLevel.warehouse_id == warehouse_id,
        )
    )
    level = level_result.scalar_one_or_none()
    if not level:
        level = InventoryLevel(product_id=product_id, warehouse_id=warehouse_id,
                               qty_on_hand=0, qty_on_order=0, reorder_point=10)
        db.add(level)

    # Apply transaction
    if txn_type == StockTransactionType.receive:
        level.qty_on_hand += qty
        level.qty_on_order = max(0, level.qty_on_order - qty)
    elif txn_type == StockTransactionType.pick:
        if level.qty_on_hand < qty:
            raise HTTPException(status_code=400, detail=f"Insufficient stock: {level.qty_on_hand} on hand, requested {qty}")
        level.qty_on_hand -= qty
    elif txn_type == StockTransactionType.writeoff:
        if level.qty_on_hand < qty:
            raise HTTPException(status_code=400, detail="Insufficient stock for write-off")
        level.qty_on_hand -= qty
    elif txn_type == StockTransactionType.return_:
        level.qty_on_hand += qty
    elif txn_type == StockTransactionType.transfer:
        dest_id = data.get("destination_warehouse_id")
        if not dest_id:
            raise HTTPException(status_code=422, detail="destination_warehouse_id required for transfer")
        if level.qty_on_hand < qty:
            raise HTTPException(status_code=400, detail="Insufficient stock for transfer")
        level.qty_on_hand -= qty
        dest_result = await db.execute(
            select(InventoryLevel).where(
                InventoryLevel.product_id == product_id,
                InventoryLevel.warehouse_id == uuid.UUID(dest_id)
            )
        )
        dest_level = dest_result.scalar_one_or_none()
        if not dest_level:
            dest_level = InventoryLevel(product_id=product_id,
                                        warehouse_id=uuid.UUID(dest_id),
                                        qty_on_hand=0, qty_on_order=0, reorder_point=10)
            db.add(dest_level)
        dest_level.qty_on_hand += qty

    # Append immutable ledger entry
    txn = StockTransaction(
        id=uuid.uuid4(), tenant_id=tenant_id,
        product_id=product_id, warehouse_id=warehouse_id,
        type=txn_type, qty=qty,
    )
    db.add(txn)
    await db.commit()

    # Low-stock check (fire-and-forget)
    if level.qty_on_hand <= level.reorder_point:
        try:
            dispatch_low_stock_alert.delay(str(tenant_id), str(product_id), level.qty_on_hand, level.reorder_point)
        except Exception:
            log.warning("Celery not available — skipping low-stock alert dispatch")

    return {
        "transaction_id": str(txn.id),
        "product_id": str(product_id),
        "warehouse_id": str(warehouse_id),
        "type": txn_type.value,
        "qty": qty,
        "qty_on_hand_after": level.qty_on_hand,
    }


async def get_inventory_levels(
    db: AsyncSession, tenant_id: uuid.UUID,
    warehouse_id: Optional[str] = None,
    sku: Optional[str] = None,
) -> list:
    q = (
        select(InventoryLevel, Product)
        .join(Product, InventoryLevel.product_id == Product.id)
        .where(Product.tenant_id == tenant_id, not Product.is_deleted)
    )
    if warehouse_id:
        q = q.where(InventoryLevel.warehouse_id == uuid.UUID(warehouse_id))
    if sku:
        q = q.where(Product.sku.ilike(f"%{sku}%"))

    result = await db.execute(q)
    rows = result.all()

    items = []
    for level, product in rows:
        status = _compute_status(level)
        items.append({
            "product_id": str(product.id),
            "sku": product.sku,
            "name": product.name,
            "warehouse_id": str(level.warehouse_id),
            "qty_on_hand": level.qty_on_hand,
            "qty_on_order": level.qty_on_order,
            "reorder_point": level.reorder_point,
            "status": status,
        })
    return items


async def get_low_stock(db: AsyncSession, tenant_id: uuid.UUID) -> list:
    q = (
        select(InventoryLevel, Product, Supplier)
        .join(Product, InventoryLevel.product_id == Product.id)
        .outerjoin(Supplier, Product.supplier_id == Supplier.id)
        .where(
            Product.tenant_id == tenant_id,
            not Product.is_deleted,
            InventoryLevel.qty_on_hand <= InventoryLevel.reorder_point,
        )
    )
    result = await db.execute(q)
    rows = result.all()
    items = []
    for level, product, supplier in rows:
        lead_days = supplier.lead_time_days if supplier else 7
        suggested_qty = int(lead_days * 1.2 * 10)  # simplified: 10 units/day avg
        items.append({
            "product_id": str(product.id),
            "sku": product.sku,
            "name": product.name,
            "qty_on_hand": level.qty_on_hand,
            "reorder_point": level.reorder_point,
            "status": _compute_status(level),
            "suggested_reorder_qty": suggested_qty,
            "supplier_lead_days": lead_days,
        })
    return items


def _compute_status(level: InventoryLevel) -> str:
    if level.qty_on_hand == 0 and level.qty_on_order > 0:
        return "on_order"
    elif level.qty_on_hand == 0:
        return "out_of_stock"
    elif level.qty_on_hand <= level.reorder_point:
        return "low_stock"
    return "in_stock"


def _product_to_dict(p: Product) -> dict:
    return {
        "id": str(p.id), "sku": p.sku, "name": p.name,
        "category_id": str(p.category_id) if p.category_id else None,
        "upc": p.upc, "unit_cost": float(p.unit_cost),
        "is_deleted": p.is_deleted,
    }
