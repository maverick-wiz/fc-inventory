import { apiClient } from "./client";
import type { User } from "@/types";

export interface LoginPayload { email: string; password: string; tenant_id: string; }
export interface TokenResponse { access_token: string; token_type: string; expires_in: number; }

export const authApi = {
  login: (data: LoginPayload) =>
    apiClient.post<TokenResponse>("/auth/token", data),

  refresh: () =>
    apiClient.post<TokenResponse>("/auth/refresh"),

  logout: () =>
    apiClient.post("/auth/logout"),

  me: () =>
    apiClient.get<User>("/auth/me"),

  tenantConfig: (tenantId: string) =>
    apiClient.get(`/tenants/${tenantId}/config`),
};
