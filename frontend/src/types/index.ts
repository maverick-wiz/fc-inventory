// ── Core domain types ──────────────────────────────────────────

export type UserRole = "tenant_admin" | "store_manager" | "warehouse_op" | "read_only";

export interface User {
  user_id: string;
  email: string;
  role: UserRole;
  tenant_id: string;
}

export interface TenantConfig {
  logo_url?: string;
  primary_color: string;
  portal_name: string;
}

export type StockStatus = "in_stock" | "low_stock" | "out_of_stock" | "on_order";

export interface Product {
  id: string;
  sku: string;
  name: string;
  category_id?: string;
  upc?: string;
  unit_cost: number;
  is_deleted: boolean;
}

export interface InventoryLevel {
  product_id: string;
  sku: string;
  name: string;
  warehouse_id: string;
  qty_on_hand: number;
  qty_on_order: number;
  reorder_point: number;
  status: StockStatus;
}

export interface PurchaseOrder {
  id: string;
  tenant_id: string;
  supplier_id: string;
  status: "open" | "in_transit" | "received";
  expected_date?: string;
  created_at?: string;
  line_items?: POLineItem[];
}

export interface POLineItem {
  id: string;
  product_id: string;
  qty_ordered: number;
  qty_received: number;
  unit_cost: number;
}

export interface CalendarEvent {
  id: string;
  type: "delivery" | "store_audit" | "promo" | "reorder";
  linked_entity?: string;
  start_ts: string;
  end_ts?: string;
  rrule?: string;
}

export interface Warehouse {
  id: string;
  name: string;
  location: string;
  type: "DC" | "store" | "3PL";
}

export interface Supplier {
  id: string;
  name: string;
  lead_time_days: number;
  rating: number;
}

// ── Pagination ──────────────────────────────────────────────────

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
}

// ── API Error ───────────────────────────────────────────────────

export interface APIError {
  code: string;
  message: string;
  detail?: string;
}
