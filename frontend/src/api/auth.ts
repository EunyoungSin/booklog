import { apiClient } from "./client";
import type { User } from "../types/auth";

interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export async function loginRequest(email: string, password: string): Promise<TokenPair> {
  const res = await apiClient.post<TokenPair>("/api/auth/login", { email, password });
  return res.data;
}

export async function registerRequest(
  email: string,
  password: string,
  name: string,
): Promise<TokenPair> {
  const res = await apiClient.post<TokenPair>("/api/auth/register", { email, password, name });
  return res.data;
}

export async function fetchCurrentUser(): Promise<User> {
  const res = await apiClient.get<User>("/api/auth/me");
  return res.data;
}

export async function logoutRequest(refreshToken: string): Promise<void> {
  await apiClient.post("/api/auth/logout", { refresh_token: refreshToken });
}
