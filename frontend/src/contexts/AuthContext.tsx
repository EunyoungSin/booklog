import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { bootstrapAuthFromStorage, getStoredRefreshToken, setTokens } from "../api/client";
import { fetchCurrentUser, loginRequest, logoutRequest, registerRequest } from "../api/auth";
import type { User } from "../types/auth";

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    void (async () => {
      const restoredUser = await bootstrapAuthFromStorage();
      setUser(restoredUser);
      setIsLoading(false);
    })();
  }, []);

  async function login(email: string, password: string) {
    const tokens = await loginRequest(email, password);
    setTokens({ accessToken: tokens.access_token, refreshToken: tokens.refresh_token });
    setUser(await fetchCurrentUser());
  }

  async function register(email: string, password: string, name: string) {
    const tokens = await registerRequest(email, password, name);
    setTokens({ accessToken: tokens.access_token, refreshToken: tokens.refresh_token });
    setUser(await fetchCurrentUser());
  }

  async function logout() {
    const refreshToken = getStoredRefreshToken();
    if (refreshToken) {
      await logoutRequest(refreshToken).catch(() => {
        // best-effort: even if the server call fails, clear the local session
      });
    }
    setTokens(null);
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}
