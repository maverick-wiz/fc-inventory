import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { inventoryApi } from "@/api/inventory";

export function useProducts(params?: Record<string, unknown>) {
  return useQuery({
    queryKey: ["products", params],
    queryFn: () => inventoryApi.listProducts(params).then((r) => r.data),
    staleTime: 30_000,
  });
}

export function useInventoryLevels(params?: Record<string, unknown>) {
  return useQuery({
    queryKey: ["inventory", params],
    queryFn: () => inventoryApi.listInventory(params).then((r) => r.data),
    staleTime: 30_000,
    refetchInterval: 60_000, // Real-time: refetch every 60s
  });
}

export function useLowStock() {
  return useQuery({
    queryKey: ["inventory", "low-stock"],
    queryFn: () => inventoryApi.getLowStock().then((r) => r.data),
    staleTime: 30_000,
    refetchInterval: 60_000,
  });
}

export function useRecordTransaction() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: inventoryApi.recordTransaction,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["inventory"] });
      qc.invalidateQueries({ queryKey: ["products"] });
    },
  });
}

export function useCreateProduct() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: inventoryApi.createProduct,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["products"] }),
  });
}
