
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from 'react';

import type { ReactNode } from 'react';
import { authApi } from '../lib/auth';
import type { Credentials, Registration, User } from '../lib/auth';

type AuthContextType = {
  user: User | null;
  loading: boolean;
  login: (data: Credentials) => Promise<User>;
  register: (data: Registration) => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<User | null>;
};

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // Retrieve the currently authenticated user
  const refresh = useCallback(async (): Promise<User | null> => {
    const next = await authApi.me();
    setUser(next);
    return next;
  }, []);

  // Check for an existing session when the app loads
  useEffect(() => {
    let active = true;

    authApi.me()
      .then((next) => {
        if (active) setUser(next);
      })
      .catch(() => {
        if (active) setUser(null);
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, []);

  // Log in and retrieve the authenticated user
  const login = async (data: Credentials): Promise<User> => {
    await authApi.login(data);

    const next = await refresh();

    if (!next) {
      throw new Error(
        'Login succeeded, but no session was established.'
      );
    }

    return next;
  };

  // Create an account without automatically logging in
  const register = async (data: Registration): Promise<void> => {
    await authApi.register(data);
  };

  // Log out and clear the authenticated user
  const logout = async (): Promise<void> => {
    await authApi.logout();
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        register,
        logout,
        refresh,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const value = useContext(AuthContext);

  if (!value) {
    throw new Error('useAuth must be called within AuthProvider');
  }

  return value;
}
