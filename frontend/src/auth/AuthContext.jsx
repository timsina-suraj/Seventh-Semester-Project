import { createContext, useContext, useEffect, useState } from "react";
import * as api from "../api/endpoints";
import { KEY_TOKEN, KEY_ROLE, KEY_EMAIL } from "../api/client";

const KEY_MCP = "medishield_must_change_password";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null); // { email, role, mustChangePassword }
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem(KEY_TOKEN);
    const role  = localStorage.getItem(KEY_ROLE);
    const email = localStorage.getItem(KEY_EMAIL);
    const mustChangePassword = localStorage.getItem(KEY_MCP) === "true";
    if (token && role && email) {
      setUser({ email, role, mustChangePassword });
    }
    setLoading(false);
  }, []);

  const login = async (email, password) => {
    const { data } = await api.login(email, password);
    localStorage.setItem(KEY_TOKEN, data.access_token);
    localStorage.setItem(KEY_ROLE, data.role);
    localStorage.setItem(KEY_EMAIL, data.email);
    localStorage.setItem(KEY_MCP, String(!!data.must_change_password));
    setUser({ email: data.email, role: data.role, mustChangePassword: !!data.must_change_password });
    return data;
  };

  const loginWithOTP = async (email, otp) => {
    const { data } = await api.loginWithOTP({ email, otp });
    localStorage.setItem(KEY_TOKEN, data.access_token);
    localStorage.setItem(KEY_ROLE, data.role);
    localStorage.setItem(KEY_EMAIL, data.email);
    localStorage.setItem(KEY_MCP, String(!!data.must_change_password));
    setUser({ email: data.email, role: data.role, mustChangePassword: !!data.must_change_password });
    return data;
  };

  const clearMustChangePassword = () => {
    localStorage.setItem(KEY_MCP, "false");
    setUser((u) => (u ? { ...u, mustChangePassword: false } : u));
  };

  const logout = () => {
    localStorage.removeItem(KEY_TOKEN);
    localStorage.removeItem(KEY_ROLE);
    localStorage.removeItem(KEY_EMAIL);
    localStorage.removeItem(KEY_MCP);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, loginWithOTP, logout, clearMustChangePassword }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}