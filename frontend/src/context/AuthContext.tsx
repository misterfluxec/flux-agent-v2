"use client";

import React, { createContext, useContext, useEffect, useState } from 'react';
import { UserRole, UserSession } from '@/types/auth';
import { FEATURES } from '@/config/features';

interface AuthContextType {
  user: UserSession | null;
  role: UserRole;
  isAuthenticated: boolean;
  isLoading: boolean;
  features: typeof FEATURES;
  logout: () => void;
  refreshSession: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserSession | null>(null);
  const [role, setRole] = useState<UserRole>('user');
  const [isLoading, setIsLoading] = useState(true);

  const refreshSession = () => {
    try {
      // En un entorno Next.js, leemos las cookies del lado del cliente
      const getCookie = (name: string) => {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop()?.split(';').shift();
        return undefined;
      };

      const token = getCookie('auth_token');
      const cookieRole = getCookie('user_role') as UserRole;
      
      // En una implementación real, aquí haríamos un fetch a /me
      // Para esta fase, confiamos en las cookies (blindadas por el middleware)
      if (token) {
        setRole(cookieRole || 'user');
        setUser({
          id: 'me', // Placeholder
          email: '', // Placeholder
          role: cookieRole || 'user',
          tenant_id: getCookie('flux_tenant_id') || 'default',
          name: 'Usuario Flux'
        });
      } else {
        setUser(null);
        setRole('user');
      }
    } catch (error) {
      console.error('Error refreshing session:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    refreshSession();
  }, []);

  const logout = () => {
    document.cookie = "auth_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
    document.cookie = "user_role=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
    localStorage.removeItem("flux_token");
    setUser(null);
    setRole('user');
    window.location.href = '/';
  };

  return (
    <AuthContext.Provider value={{ 
      user, 
      role, 
      isAuthenticated: !!user, 
      isLoading, 
      features: FEATURES,
      logout,
      refreshSession
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
