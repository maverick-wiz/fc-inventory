/**
 * Inventory Dashboard — KPI cards + filterable inventory table
 * FCINV-86: F2 — Inventory Dashboard UI
 */
import { useState } from "react";
import { Package, AlertTriangle, TrendingUp } from "lucide-react";
import { KPICard } from "@/components/inventory/KPICard";
import { StatusBadge } from "@/components/inventory/StatusBadge";
import { DataTable } from "@/components/ui/DataTable";
import { useInventoryLevels, useLowStock } from "@/hooks/useInventory";
import type { InventoryLevel } from "@/types";

export default function DashboardPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");

  const { data: inventory, isLoading } = useInventoryLevels({ page, page_size: 20, sku: search || undefined });
  const { data: lowStock } = useLowStock();

  const items = Array.isArray(inventory) ? inventory : [];
  const lowStockCount = lowStock?.length ?? 0;
  const totalSkus = items.length;
  const outOfStockCount = items.filter((i) => i.status === "out_of_stock").length;

  const columns = [
    { key: "sku", header: "SKU", className: "font-mono font-medium" },
    { key: "name", header: "Product Name" },
    {
      key: "status",
      header: "Status",
      render: (row: InventoryLevel) => <StatusBadge status={row.status} />,
    },
    {
      key: "qty_on_hand",
      header: "On Hand",
      render: (row: InventoryLevel) => (
        <span className={row.qty_on_hand <= row.reorder_point ? "font-semibold text-amber-600" : ""}>
          {row.qty_on_hand.toLocaleString()}
        </span>
      ),
    },
    {
      key: "qty_on_order",
      header: "On Order",
      render: (row: InventoryLevel) => row.qty_on_order > 0
        ? <span className="text-blue-600">{row.qty_on_order}</span>
        : <span className="text-gray-400">—</span>,
    },
    {
      key: "reorder_point",
      header: "Reorder At",
      render: (row: InventoryLevel) => <span className="text-gray-500">{row.reorder_point}</span>,
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Inventory Dashboard</h1>
        <p className="text-sm text-gray-500 mt-1">Real-time stock levels across all warehouses</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <KPICard
          title="Total SKUs"
          value={totalSkus.toLocaleString()}
          icon={<Package size={20} />}
          loading={isLoading}
        />
        <KPICard
          title="Low Stock"
          value={lowStockCount}
          subtitle="Below reorder point"
          icon={<AlertTriangle size={20} className="text-amber-500" />}
          trend={lowStockCount > 0 ? "down" : "neutral"}
          loading={isLoading}
        />
        <KPICard
          title="Out of Stock"
          value={outOfStockCount}
          icon={<AlertTriangle size={20} className="text-red-500" />}
          loading={isLoading}
        />
        <KPICard
          title="Fill Rate"
          value={totalSkus > 0 ? `${Math.round(((totalSkus - outOfStockCount) / totalSkus) * 100)}%` : "—"}
          icon={<TrendingUp size={20} className="text-green-500" />}
          trend="up"
          trendValue="2.3%"
          loading={isLoading}
        />
      </div>

      {/* Search + Table */}
      <div className="space-y-3">
        <div className="flex items-center gap-3">
          <input
            type="text"
            placeholder="Search by SKU or product name..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            className="w-full max-w-sm rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
          <span className="text-sm text-gray-400">
            {isLoading ? "Loading..." : `${items.length} items`}
          </span>
        </div>

        <DataTable
          data={items}
          columns={columns}
          total={items.length}
          page={page}
          pageSize={20}
          onPageChange={setPage}
          loading={isLoading}
          emptyMessage="No inventory items found"
        />
      </div>
    </div>
  );
}
