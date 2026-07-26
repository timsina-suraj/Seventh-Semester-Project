import { createContext, useContext, useEffect, useState } from "react";
import * as api from "../api/endpoints";
import { KEY_TOKEN, KEY_ROLE, KEY_EMAIL, KEY_FULL_NAME } from "../api/client";

const KEY_MCP = "medishield_must_change_password";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null); // { email, fullName, role, mustChangePassword }
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem(KEY_TOKEN);
    const role = localStorage.getItem(KEY_ROLE);
    const email = localStorage.getItem(KEY_EMAIL);
    const fullName = localStorage.getItem(KEY_FULL_NAME);
    const mustChangePassword = localStorage.getItem(KEY_MCP) === "true";
    if (token && role && email) {
      setUser({ email, fullName, role, mustChangePassword });

      // Sessions started before full_name was tracked won't have it cached
      // yet — backfill it once from /auth/me so the top bar can show a
      // name instead of the email without forcing a re-login.
      if (!fullName) {
        api
          .me()
          .then(({ data }) => {
            if (data.full_name) {
              localStorage.setItem(KEY_FULL_NAME, data.full_name);
              setUser((u) => (u ? { ...u, fullName: data.full_name } : u));
            }
          })
          .catch(() => {});
      }
    }
    setLoading(false);
  }, []);

  const persistSession = (data) => {
    localStorage.setItem(KEY_TOKEN, data.access_token);
    localStorage.setItem(KEY_ROLE, data.role);
    localStorage.setItem(KEY_EMAIL, data.email);
    if (data.full_name) {
      localStorage.setItem(KEY_FULL_NAME, data.full_name);
    } else {
      localStorage.removeItem(KEY_FULL_NAME);
    }
    localStorage.setItem(KEY_MCP, String(!!data.must_change_password));
    setUser({
      email: data.email,
      fullName: data.full_name || null,
      role: data.role,
      mustChangePassword: !!data.must_change_password,
    });
  };

  const login = async (email, password) => {
    const { data } = await api.login(email, password);
    persistSession(data);
    return data;
  };

  const loginWithOTP = async (email, otp) => {
    const { data } = await api.loginWithOTP({ email, otp });
    persistSession(data);
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
    localStorage.removeItem(KEY_FULL_NAME);
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