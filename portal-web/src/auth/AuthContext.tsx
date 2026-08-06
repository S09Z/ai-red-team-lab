import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

import { api } from "../api/client";

export interface User {
  id: number;
  email: string;
  provider: string;
  name: string;
  avatar: string;
  roles: string[];
  permissions: Record<string, string[]>;
}

interface AuthState {
  user: User | null;
  loading: boolean;
  refresh: () => Promise<void>;
  logout: () => Promise<void>;
  can: (feature: string, action: string) => boolean;
}

const AuthContext = createContext<AuthState | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  async function refresh() {
    const resp = await api("/me");
    setUser(resp.ok ? await resp.json() : null);
    setLoading(false);
  }

  async function logout() {
    await api("/auth/logout", { method: "POST" });
    setUser(null);
  }

  function can(feature: string, action: string): boolean {
    return user?.permissions?.[feature]?.includes(action) ?? false;
  }

  useEffect(() => {
    void refresh();
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, refresh, logout, can }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
