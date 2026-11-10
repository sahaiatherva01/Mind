import React, { createContext, useContext, useState, useEffect } from 'react';
import { apiRequest } from '../api/client';

export type UserRole =
  | 'platform_admin'
  | 'school_admin'
  | 'academic_coordinator'
  | 'teacher'
  | 'student'
  | 'admin';

export interface User {
  id: string;
  school_id?: string | null;
  email: string;
  full_name: string;
  role: UserRole;
  designation?: string;
  status: string;
  must_change_password?: boolean;
}

export interface School {
  id: string;
  name: string;
  slug: string;
  timezone: string;
  code?: string;
  board?: string;
}

interface AuthContextType {
  user: User | null;
  school: School | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshMe: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [school, setSchool] = useState<School | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const refreshMe = async () => {
    try {
      const data = await apiRequest<{ user: User; school?: School | null }>('/auth/me');
      setUser(data.user);
      setSchool(data.school || null);
    } catch (err) {
      setUser(null);
      setSchool(null);
      localStorage.removeItem('mind_session_token');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    refreshMe();
  }, []);

  const login = async (email: string, password: string) => {
    const data = await apiRequest<{ user: User; session_token: string }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    localStorage.setItem('mind_session_token', data.session_token);
    await refreshMe();
  };

  const logout = async () => {
    try {
      await apiRequest('/auth/logout', { method: 'POST' });
    } catch {
      // Ignore network errors on logout
    }
    localStorage.removeItem('mind_session_token');
    setUser(null);
    setSchool(null);
  };

  return (
    <AuthContext.Provider value={{ user, school, isLoading, login, logout, refreshMe }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
