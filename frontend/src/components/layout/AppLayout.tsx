import { Outlet, NavLink, useNavigate } from "react-router-dom";
import { LayoutDashboard, Package, ShoppingCart, Calendar, BarChart2, Settings, LogOut } from "lucide-react";
import { clsx } from "clsx";
import { useAuth } from "@/hooks/useAuth";

const NAV_ITEMS = [
  { to: "/dashboard",  label: "Dashboard",  icon: LayoutDashboard, minRole: "read_only" as const },
  { to: "/inventory",  label: "Inventory",  icon: Package,          minRole: "read_only" as const },
  { to: "/orders",     label: "Orders",     icon: ShoppingCart,     minRole: "store_manager" as const },
  { to: "/calendar",   label: "Calendar",   icon: Calendar,         minRole: "read_only" as const },
  { to: "/reports",    label: "Reports",    icon: BarChart2,        minRole: "store_manager" as const },
  { to: "/admin",      label: "Admin",      icon: Settings,         minRole: "tenant_admin" as const },
];

export function AppLayout() {
  const { user, hasRole, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="flex w-60 flex-col bg-white border-r border-gray-200 shadow-sm">
        {/* Brand */}
        <div className="flex items-center gap-2 px-4 py-5 border-b border-gray-100">
          <div
            className="flex h-8 w-8 items-center justify-center rounded-lg text-white text-xs font-bold"
            style={{ backgroundColor: "var(--tenant-primary, #0071CE)" }}
          >
            FC
          </div>
          <span className="text-sm font-semibold text-gray-800">FC-Inventory</span>
        </div>

        {/* Nav */}
        <nav className="flex-1 space-y-0.5 p-3">
          {NAV_ITEMS.filter((item) => hasRole(item.minRole)).map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                clsx(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-blue-50 text-blue-700"
                    : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                )
              }
            >
              <Icon size={16} />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* User */}
        <div className="border-t border-gray-100 p-3">
          <div className="rounded-lg px-3 py-2 text-xs text-gray-500">
            <p className="font-medium text-gray-700 truncate">{user?.email}</p>
            <p className="capitalize">{user?.role?.replace("_", " ")}</p>
          </div>
          <button
            onClick={handleLogout}
            className="mt-1 flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-gray-500 hover:bg-gray-100 hover:text-gray-700 transition-colors"
          >
            <LogOut size={14} />
            Sign out
          </button>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-auto p-8">
        <Outlet />
      </main>
    </div>
  );
}
