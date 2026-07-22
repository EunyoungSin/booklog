import axios, { type InternalAxiosRequestConfig } from "axios";
import type { User } from "../types/auth";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
const REFRESH_TOKEN_STORAGE_KEY = "booklog_refresh_token";

export const apiClient = axios.create({ baseURL: API_BASE_URL });

let accessToken: string | null = null;
let refreshToken: string | null = null;
let refreshPromise: Promise<string> | null = null;

interface Tokens {
  accessToken: string;
  refreshToken: string;
}

export function getStoredRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_STORAGE_KEY);
}

export function setTokens(tokens: Tokens | null): void {
  if (tokens) {
    accessToken = tokens.accessToken;
    refreshToken = tokens.refreshToken;
    localStorage.setItem(REFRESH_TOKEN_STORAGE_KEY, tokens.refreshToken);
  } else {
    accessToken = null;
    refreshToken = null;
    localStorage.removeItem(REFRESH_TOKEN_STORAGE_KEY);
  }
}

async function refreshAccessToken(): Promise<string> {
  if (!refreshToken) {
    throw new Error("No refresh token available");
  }
  if (!refreshPromise) {
    refreshPromise = axios
      .post(`${API_BASE_URL}/api/auth/refresh`, { refresh_token: refreshToken })
      .then((res) => {
        setTokens({ accessToken: res.data.access_token, refreshToken: res.data.refresh_token });
        return res.data.access_token as string;
      })
      .finally(() => {
        refreshPromise = null;
      });
  }
  return refreshPromise;
}

/** App startup: restore a session from the refresh token saved in localStorage. */
export async function bootstrapAuthFromStorage(): Promise<User | null> {
  const storedRefreshToken = localStorage.getItem(REFRESH_TOKEN_STORAGE_KEY);
  if (!storedRefreshToken) {
    return null;
  }
  refreshToken = storedRefreshToken;
  try {
    await refreshAccessToken();
    const res = await apiClient.get<User>("/api/auth/me");
    return res.data;
  } catch {
    setTokens(null);
    return null;
  }
}

apiClient.interceptors.request.use((config) => {
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  return config;
});

interface RetryableConfig extends InternalAxiosRequestConfig {
  _retry?: boolean;
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config as RetryableConfig | undefined;

    if (
      error.response?.status === 401 &&
      originalRequest &&
      !originalRequest._retry &&
      refreshToken
    ) {
      originalRequest._retry = true;
      try {
        const newAccessToken = await refreshAccessToken();
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        return apiClient(originalRequest);
      } catch {
        setTokens(null);
      }
    }

    return Promise.reject(error);
  },
);
