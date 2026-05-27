"""Initial FC-Inventory schema — all 13 tables with RLS + indexes

Revision ID: 0001
Revises: 
Create Date: 2026-05-27
Jira: FCINV-69 (ATLAS Onboarding 1)
Author: ATLAS
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── tenants ──
    op.create_table("tenants",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("subdomain", sa.String(100), unique=True, nullable=False),
        sa.Column("config_json", JSONB, server_default="{}"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── users ──
    op.create_table("users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=True),
        sa.Column("role", sa.Enum("tenant_admin","store_manager","warehouse_op","read_only", name="userrole"), nullable=False),
        sa.Column("sso_provider", sa.String(50), nullable=True),
        sa.Column("mfa_enabled", sa.Boolean, server_default="false"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_users_tenant_email", "users", ["tenant_id", "email"])

    # ── warehouses ──
    op.create_table("warehouses",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("location", sa.String(255)),
        sa.Column("type", sa.Enum("DC","store","third_pl", name="warehousetype"), nullable=False),
    )
    op.create_index("idx_warehouses_tenant", "warehouses", ["tenant_id"])

    # ── suppliers ──
    op.create_table("suppliers",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("lead_time_days", sa.Integer, server_default="7"),
        sa.Column("rating", sa.Numeric(3, 2), server_default="3.0"),
    )

    # ── categories ──
    op.create_table("categories",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("parent_id", UUID(as_uuid=True), sa.ForeignKey("categories.id"), nullable=True),
    )

    # ── products ──
    op.create_table("products",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("sku", sa.String(100), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("category_id", UUID(as_uuid=True), sa.ForeignKey("categories.id"), nullable=True),
        sa.Column("supplier_id", UUID(as_uuid=True), sa.ForeignKey("suppliers.id"), nullable=True),
        sa.Column("upc", sa.String(50), nullable=True),
        sa.Column("unit_cost", sa.Numeric(10, 2), nullable=False),
        sa.Column("is_deleted", sa.Boolean, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "sku", name="uq_products_tenant_sku"),
    )
    op.create_index("idx_products_tenant_sku", "products", ["tenant_id", "sku"])
    op.create_index("idx_products_tenant_cat", "products", ["tenant_id", "category_id"])

    # ── inventory_levels ──
    op.create_table("inventory_levels",
        sa.Column("product_id", UUID(as_uuid=True), sa.ForeignKey("products.id"), primary_key=True),
        sa.Column("warehouse_id", UUID(as_uuid=True), sa.ForeignKey("warehouses.id"), primary_key=True),
        sa.Column("qty_on_hand", sa.Integer, server_default="0"),
        sa.Column("qty_on_order", sa.Integer, server_default="0"),
        sa.Column("reorder_point", sa.Integer, server_default="10"),
    )

    # ── stock_transactions (partitioned by month) ──
    op.execute("""
        CREATE TABLE stock_transactions (
            id UUID NOT NULL,
            tenant_id UUID NOT NULL REFERENCES tenants(id),
            product_id UUID NOT NULL REFERENCES products(id),
            warehouse_id UUID NOT NULL REFERENCES warehouses(id),
            type VARCHAR(20) NOT NULL,
            qty INTEGER NOT NULL,
            ts TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY (id, ts)
        ) PARTITION BY RANGE (ts)
    """)
    op.execute("""
        CREATE TABLE stock_transactions_2026_05
        PARTITION OF stock_transactions
        FOR VALUES FROM ('2026-05-01') TO ('2026-06-01')
    """)
    op.execute("""
        CREATE TABLE stock_transactions_2026_06
        PARTITION OF stock_transactions
        FOR VALUES FROM ('2026-06-01') TO ('2026-07-01')
    """)
    op.execute("""
        CREATE TABLE stock_transactions_2026_07
        PARTITION OF stock_transactions
        FOR VALUES FROM ('2026-07-01') TO ('2026-08-01')
    """)
    op.execute("CREATE INDEX idx_stock_txn_tenant_ts ON stock_transactions(tenant_id, ts DESC)")
    # Immutable ledger rules
    op.execute("CREATE RULE no_update_stock_txn AS ON UPDATE TO stock_transactions DO INSTEAD NOTHING")
    op.execute("CREATE RULE no_delete_stock_txn AS ON DELETE TO stock_transactions DO INSTEAD NOTHING")

    # ── purchase_orders ──
    op.create_table("purchase_orders",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("supplier_id", UUID(as_uuid=True), sa.ForeignKey("suppliers.id"), nullable=False),
        sa.Column("status", sa.Enum("open","in_transit","received", name="postatus"), nullable=False, server_default="open"),
        sa.Column("expected_date", sa.Date, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_po_tenant_status", "purchase_orders", ["tenant_id", "status"])

    # ── po_line_items ──
    op.create_table("po_line_items",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("po_id", UUID(as_uuid=True), sa.ForeignKey("purchase_orders.id"), nullable=False),
        sa.Column("product_id", UUID(as_uuid=True), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("qty_ordered", sa.Integer, nullable=False),
        sa.Column("qty_received", sa.Integer, server_default="0"),
        sa.Column("unit_cost", sa.Numeric(10, 2), nullable=False),
        sa.CheckConstraint("qty_received <= qty_ordered", name="ck_qty_received_le_ordered"),
    )

    # ── calendar_events ──
    op.create_table("calendar_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("type", sa.Enum("delivery","store_audit","promo","reorder", name="calendareventtype"), nullable=False),
        sa.Column("linked_entity", UUID(as_uuid=True), nullable=True),
        sa.Column("start_ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_ts", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rrule", sa.Text, nullable=True),
    )

    # ── audit_logs ──
    op.create_table("audit_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity", sa.String(100), nullable=False),
        sa.Column("old_val", JSONB, nullable=True),
        sa.Column("new_val", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_audit_tenant_ts", "audit_logs", ["tenant_id", "id"])

    # ── report_snapshots ──
    op.create_table("report_snapshots",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("report_type", sa.String(100), nullable=False),
        sa.Column("params_json", JSONB, server_default="{}"),
        sa.Column("s3_key", sa.String(512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── RLS policies ──
    for table in ["users","warehouses","suppliers","categories","products",
                  "inventory_levels","purchase_orders","po_line_items",
                  "calendar_events","audit_logs","report_snapshots"]:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")

    for table in ["users","warehouses","suppliers","categories","products",
                  "purchase_orders","calendar_events","audit_logs","report_snapshots"]:
        op.execute(f"""
            CREATE POLICY tenant_isolation ON {table}
            USING (tenant_id = current_setting('app.tenant_id')::uuid)
        """)

    # inventory_levels via product join
    op.execute("""
        CREATE POLICY tenant_isolation ON inventory_levels
        USING (product_id IN (
            SELECT id FROM products WHERE tenant_id = current_setting('app.tenant_id')::uuid
        ))
    """)

    # Low-stock alert trigger
    op.execute("""
        CREATE OR REPLACE FUNCTION fn_check_low_stock() RETURNS trigger AS $$
        BEGIN
            IF NEW.qty_on_hand <= NEW.reorder_point THEN
                PERFORM pg_notify('low_stock',
                    json_build_object(
                        'product_id', NEW.product_id,
                        'warehouse_id', NEW.warehouse_id,
                        'qty_on_hand', NEW.qty_on_hand,
                        'reorder_point', NEW.reorder_point
                    )::text
                );
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """)
    op.execute("""
        CREATE TRIGGER trg_low_stock
        AFTER INSERT OR UPDATE ON inventory_levels
        FOR EACH ROW EXECUTE FUNCTION fn_check_low_stock()
    """)


def downgrade() -> None:
    for trig in ["trg_low_stock"]:
        op.execute(f"DROP TRIGGER IF EXISTS {trig} ON inventory_levels")
    op.execute("DROP FUNCTION IF EXISTS fn_check_low_stock()")
    for table in ["report_snapshots","audit_logs","calendar_events","po_line_items",
                  "purchase_orders","inventory_levels","stock_transactions_2026_05",
                  "stock_transactions_2026_06","stock_transactions_2026_07",
                  "stock_transactions","products","categories","suppliers",
                  "warehouses","users","tenants"]:
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
    for enum in ["userrole","warehousetype","postatus","calendareventtype"]:
        op.execute(f"DROP TYPE IF EXISTS {enum}")
