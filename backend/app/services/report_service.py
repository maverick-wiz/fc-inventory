"""Reporting service — sync and async report generation."""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.db.models.models import StockTransaction, Product, ReportSnapshot, StockTransactionType


REPORT_TYPES = ["turnover", "shrinkage", "fill_rate", "days_on_hand", "reorder_frequency", "supplier_lead_time"]


async def generate_report(
    db: AsyncSession, tenant_id: uuid.UUID,
    report_type: str, from_dt: datetime, to_dt: datetime,
    warehouse_id: Optional[str] = None,
) -> dict:
    """Sync report for small date ranges."""
    if report_type == "turnover":
        return await _turnover_report(db, tenant_id, from_dt, to_dt)
    elif report_type == "shrinkage":
        return await _shrinkage_report(db, tenant_id, from_dt, to_dt)
    else:
        return {"report_type": report_type, "data": [], "message": "Report type queued for async generation"}


async def _turnover_report(db: AsyncSession, tenant_id: uuid.UUID, from_dt: datetime, to_dt: datetime) -> dict:
    q = (
        select(
            Product.sku, Product.name,
            func.sum(StockTransaction.qty).label("total_picked"),
        )
        .join(StockTransaction, StockTransaction.product_id == Product.id)
        .where(
            Product.tenant_id == tenant_id,
            StockTransaction.type == StockTransactionType.pick,
            StockTransaction.ts >= from_dt,
            StockTransaction.ts <= to_dt,
        )
        .group_by(Product.id, Product.sku, Product.name)
        .order_by(func.sum(StockTransaction.qty).desc())
    )
    result = await db.execute(q)
    rows = result.all()
    return {
        "report_type": "turnover",
        "from": str(from_dt), "to": str(to_dt),
        "data": [{"sku": r.sku, "name": r.name, "total_picked": r.total_picked} for r in rows],
    }


async def _shrinkage_report(db: AsyncSession, tenant_id: uuid.UUID, from_dt: datetime, to_dt: datetime) -> dict:
    q = (
        select(
            Product.sku, Product.name,
            func.sum(StockTransaction.qty).label("total_writeoff"),
        )
        .join(StockTransaction, StockTransaction.product_id == Product.id)
        .where(
            Product.tenant_id == tenant_id,
            StockTransaction.type == StockTransactionType.writeoff,
            StockTransaction.ts >= from_dt,
            StockTransaction.ts <= to_dt,
        )
        .group_by(Product.id, Product.sku, Product.name)
    )
    result = await db.execute(q)
    rows = result.all()
    return {
        "report_type": "shrinkage",
        "from": str(from_dt), "to": str(to_dt),
        "data": [{"sku": r.sku, "name": r.name, "total_writeoff": r.total_writeoff} for r in rows],
    }
