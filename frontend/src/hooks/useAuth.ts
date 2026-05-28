import { useAuthStore } from "@/stores/authStore";
import type { UserRole } from "@/types";

const ROLE_HIERARCHY: Record<UserRole, number> = {
  read_only: 0,
  warehouse_op: 1,
  store_manager: 2,
  tenant_admin: 3,
};

export function useAuth() {
  const { user, token, isAuthenticated, logout } = useAuthStore();

  const hasRole = (minRole: UserRole): boolean => {
    if (!user) return false;
    return ROLE_HIERARCHY[user.role] >= ROLE_HIERARCHY[minRole];
  };

  const isAdmin = user?.role === "tenant_admin";
  const isManager = hasRole("store_manager");
  const isWarehouseOp = hasRole("warehouse_op");

  return { user, token, isAuthenticated, logout, hasRole, isAdmin, isManager, isWarehouseOp };
}
