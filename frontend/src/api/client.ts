/**
 * Base Axios instance with interceptors:
 * 1. Inject X-Tenant-ID from auth store
 * 2. Auto-refresh on 401 (silent, one retry)
 * 3. Rate limit handling on 429
 */
import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios";
import { useAuthStore } from "@/stores/authStore";
import toast from "../utils/toast";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

export const apiClient = axios.create({
  baseURL: BASE_URL,
  withCredentials: true, // send httpOnly cookies
  headers: { "Content-Type": "application/json" },
  timeout: 15_000,
});

// ── Request interceptor: inject auth headers ──
apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const { token, user } = useAuthStore.getState();
  if (token) {
    config.headers["Authorization"] = `Bearer ${token}`;
  }
  if (user?.tenant_id) {
    config.headers["X-Tenant-ID"] = user.tenant_id;
  }
  return config;
});

// ── Response interceptor: handle 401 + 429 ──
let isRefreshing = false;
let failedQueue: Array<{ resolve: (v: unknown) => void; reject: (e: unknown) => void }> = [];

const processQueue = (error: AxiosError | null, token: string | null = null) => {
  failedQueue.forEach(({ resolve, reject }) => (error ? reject(error) : resolve(token)));
  failedQueue = [];
};

apiClient.interceptors.response.use(
  (res) => res,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then((token) => {
          originalRequest.headers["Authorization"] = `Bearer ${token}`;
          return apiClient(originalRequest);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const res = await axios.post(`${BASE_URL}/auth/refresh`, {}, { withCredentials: true });
        const newToken = res.data.access_token;
        useAuthStore.getState().setToken(newToken);
        processQueue(null, newToken);
        originalRequest.headers["Authorization"] = `Bearer ${newToken}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError as AxiosError, null);
        useAuthStore.getState().logout();
        window.location.href = "/login";
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    if (error.response?.status === 429) {
      toast.warn("Too many requests — please wait a moment");
    }

    return Promise.reject(error);
  }
);
