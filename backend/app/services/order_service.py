"""Purchase Order business logic."""
import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from fastapi import HTTPException
from app.db.models.models import PurchaseOrder, POLineItem, InventoryLevel, StockTransaction, POStatus, StockTransactionType


async def create_purchase_order(db: AsyncSession, tenant_id: uuid.UUID, data: dict) -> dict:
    po = PurchaseOrder(
        id=uuid.uuid4(), tenant_id=tenant_id,
        supplier_id=uuid.UUID(data["supplier_id"]),
        expected_date=data.get("expected_date"),
        status=POStatus.open,
    )
    db.add(po)

    items = []
    for li in data.get("line_items", []):
        line = POLineItem(
            id=uuid.uuid4(), po_id=po.id,
            product_id=uuid.UUID(li["product_id"]),
            qty_ordered=li["qty_ordered"],
            qty_received=0,
            unit_cost=li["unit_cost"],
        )
        db.add(line)
        items.append(line)

        # Increment qty_on_order
        level_q = await db.execute(
            select(InventoryLevel).where(
                InventoryLevel.product_id == line.product_id,
            )
        )
        for level in level_q.scalars().all():
            level.qty_on_order = (level.qty_on_order or 0) + li["qty_ordered"]

    await db.commit()
    await db.refresh(po)
    return _po_to_dict(po, items)


async def list_purchase_orders(
    db: AsyncSession, tenant_id: uuid.UUID,
    status_filter: Optional[str] = None,
    page: int = 1, page_size: int = 20
) -> dict:
    filters = [PurchaseOrder.tenant_id == tenant_id]
    if status_filter:
        filters.append(PurchaseOrder.status == POStatus(status_filter))

    q = select(PurchaseOrder).where(and_(*filters)).offset((page - 1) * page_size).limit(page_size)
    total_q = select(func.count()).select_from(PurchaseOrder).where(and_(*filters))

    result = await db.execute(q)
    total = (await db.execute(total_q)).scalar_one()
    orders = result.scalars().all()

    return {
        "items": [_po_to_dict(po) for po in orders],
        "total": total, "page": page, "page_size": page_size,
        "has_next": (page * page_size) < total,
    }


async def receive_purchase_order(
    db: AsyncSession, tenant_id: uuid.UUID, po_id: str, line_receives: list
) -> dict:
    po_result = await db.execute(
        select(PurchaseOrder).where(
            PurchaseOrder.id == uuid.UUID(po_id),
            PurchaseOrder.tenant_id == tenant_id
        )
    )
    po = po_result.scalar_one_or_none()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    for receive in line_receives:
        li_result = await db.execute(
            select(POLineItem).where(POLineItem.id == uuid.UUID(receive["line_item_id"]), POLineItem.po_id == po.id)
        )
        li = li_result.scalar_one_or_none()
        if not li:
            continue

        new_received = li.qty_received + receive["qty_received"]
        if new_received > li.qty_ordered:
            raise HTTPException(status_code=400, detail=f"Received qty exceeds ordered for line {li.id}")
        li.qty_received = new_received

        # Create stock transaction
        txn = StockTransaction(
            id=uuid.uuid4(), tenant_id=tenant_id,
            product_id=li.product_id,
            warehouse_id=uuid.UUID(receive.get("warehouse_id", str(uuid.uuid4()))),
            type=StockTransactionType.receive, qty=receive["qty_received"],
        )
        db.add(txn)

        # Update inventory level
        level_q = await db.execute(
            select(InventoryLevel).where(InventoryLevel.product_id == li.product_id)
        )
        for level in level_q.scalars().all():
            level.qty_on_hand += receive["qty_received"]
            level.qty_on_order = max(0, level.qty_on_order - receive["qty_received"])

    # Check if fully received
    lines_q = await db.execute(select(POLineItem).where(POLineItem.po_id == po.id))
    lines = lines_q.scalars().all()
    if all(li.qty_received >= li.qty_ordered for li in lines):
        po.status = POStatus.received
    else:
        po.status = POStatus.in_transit

    await db.commit()
    return _po_to_dict(po)


def _po_to_dict(po, lines=None) -> dict:
    d = {
        "id": str(po.id), "tenant_id": str(po.tenant_id),
        "supplier_id": str(po.supplier_id), "status": po.status.value,
        "expected_date": str(po.expected_date) if po.expected_date else None,
        "created_at": str(po.created_at) if po.created_at else None,
    }
    if lines:
        d["line_items"] = [
            {"id": str(li.id), "product_id": str(li.product_id),
             "qty_ordered": li.qty_ordered, "qty_received": li.qty_received,
             "unit_cost": float(li.unit_cost)} for li in lines
        ]
    return d
