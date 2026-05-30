import { describe, it, expect, beforeEach } from "vitest";
import { renderHook } from "@testing-library/react";
import { useAuth } from "./useAuth";
import { useAuthStore } from "@/stores/authStore";

describe("useAuth", () => {
  beforeEach(() => {
    useAuthStore.setState({ token: null, user: null, isAuthenticated: false });
  });

  it("returns isAuthenticated=false when no token", () => {
    const { result } = renderHook(() => useAuth());
    expect(result.current.isAuthenticated).toBe(false);
  });

  it("hasRole returns false for unauthenticated user", () => {
    const { result } = renderHook(() => useAuth());
    expect(result.current.hasRole("read_only")).toBe(false);
  });

  it("tenant_admin has all roles", () => {
    useAuthStore.setState({
      token: "test",
      user: { user_id: "1", email: "admin@test.com", role: "tenant_admin", tenant_id: "t1" },
      isAuthenticated: true,
    });
    const { result } = renderHook(() => useAuth());
    expect(result.current.hasRole("tenant_admin")).toBe(true);
    expect(result.current.hasRole("store_manager")).toBe(true);
    expect(result.current.hasRole("warehouse_op")).toBe(true);
    expect(result.current.hasRole("read_only")).toBe(true);
  });

  it("read_only cannot access store_manager routes", () => {
    useAuthStore.setState({
      token: "test",
      user: { user_id: "2", email: "viewer@test.com", role: "read_only", tenant_id: "t1" },
      isAuthenticated: true,
    });
    const { result } = renderHook(() => useAuth());
    expect(result.current.hasRole("read_only")).toBe(true);
    expect(result.current.hasRole("store_manager")).toBe(false);
    expect(result.current.isAdmin).toBe(false);
  });

  it("warehouse_op can access warehouse routes but not manager routes", () => {
    useAuthStore.setState({
      token: "test",
      user: { user_id: "3", email: "op@test.com", role: "warehouse_op", tenant_id: "t1" },
      isAuthenticated: true,
    });
    const { result } = renderHook(() => useAuth());
    expect(result.current.hasRole("warehouse_op")).toBe(true);
    expect(result.current.hasRole("store_manager")).toBe(false);
  });
});
