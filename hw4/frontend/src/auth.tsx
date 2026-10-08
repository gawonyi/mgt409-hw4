import { createContext, ReactNode, useContext, useEffect, useState } from "react";
import { fetchMe, loginUser, registerUser } from "./api";
import type { User } from "./types";

const TOKEN_KEY = "cc_token";

interface AuthState {
  user: User | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (data: { first_name: string; last_name: string; email: string; password: string }) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthState | null>(null);

function readToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

function writeToken(token: string | null) {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token);
    else localStorage.removeItem(TOKEN_KEY);
  } catch {
    /* storage unavailable: stay logged in for this tab only */
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(readToken);
  const [user, setUser] = useState<User | null>(null);

  // On page load, turn a saved token back into the logged-in user (or drop it if expired).
  useEffect(() => {
    if (!token) return;
    fetchMe(token)
      .then(setUser)
      .catch(() => {
        setToken(null);
        writeToken(null);
      });
  }, [token]);

  function save(t: string, u: User) {
    writeToken(t);
    setToken(t);
    setUser(u);
  }

  const value: AuthState = {
    user,
    token,
    login: async (email, password) => {
      const res = await loginUser(email, password);
      save(res.token, res.user);
    },
    register: async (data) => {
      const res = await registerUser(data);
      save(res.token, res.user);
    },
    logout: () => {
      writeToken(null);
      setToken(null);
      setUser(null);
    },
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
