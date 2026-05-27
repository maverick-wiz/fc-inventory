#!/usr/bin/env python3
"""
FC-Inventory seed data — 4 tenants (Walmart, Target, Loblaws, Best Buy)
500+ products per tenant, warehouses, suppliers, users, stock history.
Run: python scripts/seed_data.py
Idempotent: safe to re-run.
"""
import asyncio
import uuid
import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.core.config import settings
from app.core.security import hash_password
from app.db.models.models import (
    Tenant, User, Warehouse, Supplier, Category, Product,
    InventoryLevel, StockTransaction, PurchaseOrder, POLineItem,
    UserRole, WarehouseType, StockTransactionType, POStatus
)

engine = create_async_engine(settings.DATABASE_URL, echo=False)
Session = async_sessionmaker(engine, expire_on_commit=False)

TENANTS = [
    {"name": "Walmart", "subdomain": "walmart",
     "config_json": {"logo_url": "https://cdn.walmart.com/logo.png", "primary_color": "#0071CE", "portal_name": "Walmart Inventory"}},
    {"name": "Target", "subdomain": "target",
     "config_json": {"logo_url": "https://cdn.target.com/logo.png", "primary_color": "#CC0000", "portal_name": "Target Inventory"}},
    {"name": "Loblaws", "subdomain": "loblaws",
     "config_json": {"logo_url": "https://cdn.loblaws.ca/logo.png", "primary_color": "#F7941D", "portal_name": "Loblaws Inventory"}},
    {"name": "Best Buy", "subdomain": "bestbuy",
     "config_json": {"logo_url": "https://cdn.bestbuy.com/logo.png", "primary_color": "#FFE000", "portal_name": "Best Buy Inventory"}},
]

WAREHOUSE_TEMPLATES = [
    {"name": "Main DC", "type": WarehouseType.DC, "location": "Chicago, IL"},
    {"name": "Northeast DC", "type": WarehouseType.DC, "location": "Newark, NJ"},
    {"name": "West Coast DC", "type": WarehouseType.DC, "location": "Los Angeles, CA"},
    {"name": "Store 001", "type": WarehouseType.store, "location": "New York, NY"},
    {"name": "Store 002", "type": WarehouseType.store, "location": "Dallas, TX"},
    {"name": "Store 003", "type": WarehouseType.store, "location": "Phoenix, AZ"},
]

SUPPLIER_TEMPLATES = [
    {"name": "Global Supply Co.", "lead_time_days": 7, "rating": Decimal("4.5")},
    {"name": "FastShip Logistics", "lead_time_days": 3, "rating": Decimal("4.8")},
    {"name": "Mega Wholesale Ltd", "lead_time_days": 14, "rating": Decimal("3.9")},
    {"name": "Pacific Imports Inc", "lead_time_days": 21, "rating": Decimal("4.2")},
    {"name": "Local Distributors", "lead_time_days": 2, "rating": Decimal("4.6")},
]

CATEGORIES = [
    "Electronics", "Groceries", "Apparel", "Home & Garden",
    "Sports & Outdoors", "Toys & Games", "Beauty & Personal Care",
    "Automotive", "Office Supplies", "Books & Media",
]

PRODUCT_TEMPLATES = [
    ("SKU-{:04d}", "{} Item {:04d}", 5.99, 299.99),
]


def generate_products(tenant_id: uuid.UUID, category_ids: list, supplier_ids: list, count=500) -> list:
    products = []
    for i in range(count):
        cat = random.choice(category_ids)
        sup = random.choice(supplier_ids) if supplier_ids else None
        products.append(Product(
            id=uuid.uuid4(), tenant_id=tenant_id,
            sku=f"SKU-{i+1:04d}",
            name=f"Product {i+1:04d} — {random.choice(CATEGORIES)}",
            category_id=cat, supplier_id=sup,
            unit_cost=Decimal(str(round(random.uniform(2.99, 199.99), 2))),
            is_deleted=False,
        ))
    return products


async def seed_tenant(db: AsyncSession, tenant_data: dict) -> Tenant:
    """Create tenant + all related data. Idempotent."""
    # Check if tenant already exists
    result = await db.execute(select(Tenant).where(Tenant.subdomain == tenant_data["subdomain"]))
    existing = result.scalar_one_or_none()
    if existing:
        print(f"  ℹ️  Tenant {tenant_data['name']} already exists — skipping")
        return existing

    print(f"  🌱 Seeding {tenant_data['name']}...")
    tenant = Tenant(id=uuid.uuid4(), **tenant_data, is_active=True)
    db.add(tenant)
    await db.flush()

    # Users — all 4 roles
    for role, email_prefix in [
        (UserRole.tenant_admin, "admin"),
        (UserRole.store_manager, "manager"),
        (UserRole.warehouse_op, "warehouse"),
        (UserRole.read_only, "viewer"),
    ]:
        user = User(
            id=uuid.uuid4(), tenant_id=tenant.id,
            email=f"{email_prefix}@{tenant.subdomain}.fc-inventory.com",
            hashed_password=hash_password("Password123!"),
            role=role, is_active=True, mfa_enabled=(role == UserRole.tenant_admin)
        )
        db.add(user)

    # Warehouses
    warehouses = []
    for wt in WAREHOUSE_TEMPLATES:
        w = Warehouse(id=uuid.uuid4(), tenant_id=tenant.id, **wt)
        db.add(w)
        warehouses.append(w)
    await db.flush()

    # Suppliers
    suppliers = []
    for st in SUPPLIER_TEMPLATES:
        s = Supplier(id=uuid.uuid4(), tenant_id=tenant.id, **st)
        db.add(s)
        suppliers.append(s)
    await db.flush()

    # Categories
    category_ids = []
    for cat_name in CATEGORIES:
        c = Category(id=uuid.uuid4(), tenant_id=tenant.id, name=cat_name)
        db.add(c)
        category_ids.append(c.id)
    await db.flush()

    # Products
    products = generate_products(tenant.id, category_ids, [s.id for s in suppliers], count=500)
    for p in products:
        db.add(p)
    await db.flush()

    # Inventory levels — healthy(70%), low(20%), out(10%)
    warehouse = warehouses[0]  # Main DC
    for i, product in enumerate(products):
        if i % 10 == 0:  # 10% out of stock
            qty = 0
        elif i % 5 == 0:  # 20% low stock
            qty = random.randint(1, 9)
        else:  # 70% healthy
            qty = random.randint(20, 500)

        level = InventoryLevel(
            product_id=product.id, warehouse_id=warehouse.id,
            qty_on_hand=qty, qty_on_order=random.randint(0, 50), reorder_point=10
        )
        db.add(level)

    # 6 months of stock transactions
    now = datetime.now(timezone.utc)
    for days_ago in range(180, 0, -1):
        ts = now - timedelta(days=days_ago)
        sample_products = random.sample(products, min(5, len(products)))
        for product in sample_products:
            txn_type = random.choice([
                StockTransactionType.receive,
                StockTransactionType.pick,
                StockTransactionType.pick,  # picks are more frequent
                StockTransactionType.pick,
            ])
            qty = random.randint(1, 50)
            txn = StockTransaction(
                id=uuid.uuid4(), tenant_id=tenant.id,
                product_id=product.id, warehouse_id=warehouse.id,
                type=txn_type, qty=qty, ts=ts
            )
            db.add(txn)

    # Sample purchase orders
    for status, count in [(POStatus.open, 5), (POStatus.in_transit, 3), (POStatus.received, 10)]:
        for _ in range(count):
            po = PurchaseOrder(
                id=uuid.uuid4(), tenant_id=tenant.id,
                supplier_id=random.choice(suppliers).id,
                status=status,
                expected_date=(now + timedelta(days=random.randint(1, 30))).date(),
            )
            db.add(po)
            await db.flush()
            for _ in range(random.randint(2, 5)):
                product = random.choice(products)
                qty_ordered = random.randint(10, 100)
                line = POLineItem(
                    id=uuid.uuid4(), po_id=po.id, product_id=product.id,
                    qty_ordered=qty_ordered,
                    qty_received=qty_ordered if status == POStatus.received else 0,
                    unit_cost=product.unit_cost,
                )
                db.add(line)

    await db.commit()
    print(f"  ✅ {tenant_data['name']} seeded: 500 products, {len(warehouses)} warehouses, 6mo transactions")
    return tenant


async def main():
    print("🌱 FC-Inventory Seed Data Script")
    print("=" * 50)
    async with Session() as db:
        for tenant_data in TENANTS:
            await seed_tenant(db, tenant_data)
    print("\n✅ All tenants seeded successfully!")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
