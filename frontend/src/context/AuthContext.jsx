import React, { createContext, useContext, useState, useEffect } from 'react';
import { api, getCsrfToken } from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('livebid_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [authMode, setAuthMode] = useState('login'); // 'login' | 'register'

  useEffect(() => {
    // Prime the CSRF token and verify active Django session on startup
    const initAuth = async () => {
      await getCsrfToken();
      try {
        const data = await api.getCurrentUser();
        if (data.authenticated && data.user) {
          setUser(data.user);
          localStorage.setItem('livebid_user', JSON.stringify(data.user));
        } else {
          setUser(null);
          localStorage.removeItem('livebid_user');
        }
      } catch (err) {
        // If server is not yet up, preserve local state until connected
      }
    };
    initAuth();
  }, []);

  const login = async (username, password) => {
    const res = await api.login(username, password);
    const userData = { username };
    setUser(userData);
    localStorage.setItem('livebid_user', JSON.stringify(userData));
    setIsAuthModalOpen(false);
    return res;
  };

  const register = async (username, email, password) => {
    const res = await api.register(username, email, password);
    // Automatically log in after registration
    await login(username, password);
    return res;
  };

  const logout = async () => {
    try {
      await api.logout();
    } catch (e) {
      console.warn('Logout warning:', e);
    }
    setUser(null);
    localStorage.removeItem('livebid_user');
  };

  const openAuth = (mode = 'login') => {
    setAuthMode(mode);
    setIsAuthModalOpen(true);
  };

  const closeAuth = () => {
    setIsAuthModalOpen(false);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        login,
        register,
        logout,
        isAuthModalOpen,
        authMode,
        openAuth,
        closeAuth,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
