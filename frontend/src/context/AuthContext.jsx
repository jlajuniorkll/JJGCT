import React, { useEffect, useMemo, useState } from 'react';
import AuthContext from './AuthContextInstance';
import { configService } from '../services/api';

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    const savedUser = localStorage.getItem('user');
    return savedUser ? JSON.parse(savedUser) : null;
  });
  const [loading] = useState(false);
  const [appConfig, setAppConfig] = useState(null);

  const fetchConfig = async () => {
    try {
      const res = await configService.get();
      setAppConfig(res.data || null);
      return res.data || null;
    } catch {
      setAppConfig(null);
      return null;
    }
  };

  useEffect(() => {
    if (!user) {
      setAppConfig(null);
      return;
    }
    fetchConfig();
  }, [user]);

  const iaEnabled = useMemo(() => {
    return !!appConfig?.anthropic_api_key_configured || !!appConfig?.gemini_api_key_configured;
  }, [appConfig?.anthropic_api_key_configured, appConfig?.gemini_api_key_configured]);

  const login = async (userData) => {
    setUser(userData);
    localStorage.setItem('user', JSON.stringify(userData));
    await fetchConfig();
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('user');
    setAppConfig(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, loading, appConfig, iaEnabled, refreshConfig: fetchConfig }}>
      {children}
    </AuthContext.Provider>
  );
};
