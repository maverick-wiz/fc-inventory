import { apiClient } from "./client";
import type { Product, InventoryLevel, PaginatedResponse } from "@/types";

export const inventoryApi = {
  // Products
  listProducts: (params?: Record<string, unknown>) =>
    apiClient.get<PaginatedResponse<Product>>("/products", { params }),

  createProduct: (data: Partial<Product>) =>
    apiClient.post<Product>("/products", data),

  updateProduct: (sku: string, data: Partial<Product>) =>
    apiClient.put<Product>(`/products/${sku}`, data),

  deleteProduct: (sku: string) =>
    apiClient.delete(`/products/${sku}`),

  // Inventory levels
  listInventory: (params?: Record<string, unknown>) =>
    apiClient.get<InventoryLevel[]>("/inventory", { params }),

  recordTransaction: (data: {
    product_id: string; warehouse_id: string;
    type: string; qty: number; destination_warehouse_id?: string;
  }) => apiClient.post("/inventory/transactions", data),

  getLowStock: () =>
    apiClient.get<InventoryLevel[]>("/inventory/low-stock"),
};
