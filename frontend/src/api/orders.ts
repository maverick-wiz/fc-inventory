import { apiClient } from "./client";
import type { PurchaseOrder, PaginatedResponse } from "@/types";

export const ordersApi = {
  list: (params?: Record<string, unknown>) =>
    apiClient.get<PaginatedResponse<PurchaseOrder>>("/purchase-orders", { params }),

  create: (data: {
    supplier_id: string; expected_date?: string;
    line_items: { product_id: string; qty_ordered: number; unit_cost: number }[];
  }) => apiClient.post<PurchaseOrder>("/purchase-orders", data),

  receive: (poId: string, lines: { line_item_id: string; qty_received: number; warehouse_id: string }[]) =>
    apiClient.patch<PurchaseOrder>(`/purchase-orders/${poId}/receive`, lines),
};
