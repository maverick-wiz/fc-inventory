import { clsx } from "clsx";
import type { ReactNode } from "react";

interface KPICardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: ReactNode;
  trend?: "up" | "down" | "neutral";
  trendValue?: string;
  className?: string;
  loading?: boolean;
}

export function KPICard({
  title, value, subtitle, icon, trend, trendValue, className, loading
}: KPICardProps) {
  return (
    <div className={clsx(
      "rounded-xl border border-gray-200 bg-white p-6 shadow-sm",
      className
    )}>
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-gray-500">{title}</p>
        {icon && <div className="text-gray-400">{icon}</div>}
      </div>

      {loading ? (
        <div className="mt-2 h-8 w-24 animate-pulse rounded bg-gray-200" />
      ) : (
        <p className="mt-2 text-3xl font-bold tracking-tight text-gray-900">{value}</p>
      )}

      {subtitle && <p className="mt-1 text-sm text-gray-500">{subtitle}</p>}

      {trend && trendValue && (
        <p className={clsx("mt-2 text-sm font-medium", {
          "text-green-600": trend === "up",
          "text-red-600": trend === "down",
          "text-gray-500": trend === "neutral",
        })}>
          {trend === "up" ? "↑" : trend === "down" ? "↓" : "→"} {trendValue} vs last week
        </p>
      )}
    </div>
  );
}
