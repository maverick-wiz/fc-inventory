import { clsx } from "clsx";
import type { StockStatus } from "@/types";

const STATUS_CONFIG: Record<StockStatus, { label: string; className: string }> = {
  in_stock:     { label: "In Stock",     className: "bg-green-100 text-green-800 ring-green-600/20" },
  low_stock:    { label: "Low Stock",    className: "bg-amber-100 text-amber-800 ring-amber-600/20" },
  out_of_stock: { label: "Out of Stock", className: "bg-red-100 text-red-800 ring-red-600/20" },
  on_order:     { label: "On Order",     className: "bg-blue-100 text-blue-800 ring-blue-600/20" },
};

interface StatusBadgeProps {
  status: StockStatus;
  className?: string;
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const { label, className: statusClass } = STATUS_CONFIG[status];
  return (
    <span
      className={clsx(
        "inline-flex items-center rounded-md px-2 py-1 text-xs font-medium ring-1 ring-inset",
        statusClass,
        className
      )}
      aria-label={`Stock status: ${label}`}
    >
      {label}
    </span>
  );
}
