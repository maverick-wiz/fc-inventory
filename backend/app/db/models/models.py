"""
SQLAlchemy async database models — FC-Inventory
All tables carry tenant_id for RLS.
SCRUM-63: OMEGA Onboarding 2 — Project Scaffolding
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, Integer, Numeric, DateTime, Text, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import DeclarativeBase, relationship
import enum


class Base(DeclarativeBase):
    pass


# ── Enums ──────────────────────────────────────────────────────────────────

class UserRole(str, enum.Enum):
    tenant_admin = "tenant_admin"
    store_manager = "store_manager"
    warehouse_op = "warehouse_op"
    read_only = "read_only"


class WarehouseType(str, enum.Enum):
    DC = "DC"
    store = "store"
    third_pl = "3PL"


class StockTransactionType(str, enum.Enum):
    receive = "receive"
    pick = "pick"
    transfer = "transfer"
    writeoff = "writeoff"
    return_ = "return"


class POStatus(str, enum.Enum):
    open = "open"
    in_transit = "in_transit"
    received = "received"


class CalendarEventType(str, enum.Enum):
    delivery = "delivery"
    store_audit = "store_audit"
    promo = "promo"
    reorder = "reorder"


# ── Models ─────────────────────────────────────────────────────────────────

class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    subdomain = Column(String(100), unique=True, nullable=False)
    config_json = Column(JSONB, default={})
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    email = Column(String(255), nullable=False)       # pgcrypto encrypted in prod
    role = Column(SAEnum(UserRole), nullable=False, default=UserRole.read_only)
    sso_provider = Column(String(50), nullable=True)
    mfa_enabled = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class Warehouse(Base):
    __tablename__ = "warehouses"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    name = Column(String(150), nullable=False)
    location = Column(String(255))
    type = Column(SAEnum(WarehouseType), nullable=False, default=WarehouseType.store)


class Supplier(Base):
    __tablename__ = "suppliers"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    name = Column(String(150), nullable=False)
    lead_time_days = Column(Integer, default=7)
    rating = Column(Numeric(3, 2), default=3.0)


class Category(Base):
    __tablename__ = "categories"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    name = Column(String(100), nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)


class Product(Base):
    __tablename__ = "products"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    sku = Column(String(100), nullable=False)
    name = Column(String(255), nullable=False)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)
    upc = Column(String(50), nullable=True)
    unit_cost = Column(Numeric(10, 2), nullable=False)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class InventoryLevel(Base):
    __tablename__ = "inventory_levels"
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), primary_key=True)
    warehouse_id = Column(UUID(as_uuid=True), ForeignKey("warehouses.id"), primary_key=True)
    qty_on_hand = Column(Integer, default=0)
    qty_on_order = Column(Integer, default=0)
    reorder_point = Column(Integer, default=10)


class StockTransaction(Base):
    __tablename__ = "stock_transactions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    warehouse_id = Column(UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=False)
    type = Column(SAEnum(StockTransactionType), nullable=False)
    qty = Column(Integer, nullable=False)
    ts = Column(DateTime(timezone=True), default=datetime.utcnow)


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False)
    status = Column(SAEnum(POStatus), nullable=False, default=POStatus.open)
    expected_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    line_items = relationship("POLineItem", back_populates="purchase_order")


class POLineItem(Base):
    __tablename__ = "po_line_items"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    po_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    qty_ordered = Column(Integer, nullable=False)
    qty_received = Column(Integer, default=0)
    unit_cost = Column(Numeric(10, 2), nullable=False)
    purchase_order = relationship("PurchaseOrder", back_populates="line_items")


class CalendarEvent(Base):
    __tablename__ = "calendar_events"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    type = Column(SAEnum(CalendarEventType), nullable=False)
    linked_entity = Column(UUID(as_uuid=True), nullable=True)
    start_ts = Column(DateTime(timezone=True), nullable=False)
    end_ts = Column(DateTime(timezone=True), nullable=True)
    rrule = Column(Text, nullable=True)  # RFC 5545


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    entity = Column(String(100), nullable=False)
    old_val = Column(JSONB, nullable=True)
    new_val = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class ReportSnapshot(Base):
    __tablename__ = "report_snapshots"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    report_type = Column(String(100), nullable=False)
    params_json = Column(JSONB, default={})
    s3_key = Column(String(512), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
