import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import axios from "axios";
import { translations } from "@/locales/translations";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;
export const api = axios.create({ baseURL: API, withCredentials: true });

// Attach token from localStorage
api.interceptors.request.use((cfg) => {
  const t = localStorage.getItem("hub3_token");
  if (t) cfg.headers.Authorization = `Bearer ${t}`;
  return cfg;
});

const AppCtx = createContext(null);
export const useApp = () => useContext(AppCtx);

export function AppProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [lang, setLang] = useState(() => localStorage.getItem("hub3_lang") || "en");
  const t = translations[lang];

  const setLanguage = (l) => { setLang(l); localStorage.setItem("hub3_lang", l); };

  const refreshUser = useCallback(async () => {
    try {
      const { data } = await api.get("/auth/me");
      setUser(data);
    } catch { setUser(null); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => {
    // Handle Google Auth redirect (session_id from fragment)
    const hash = window.location.hash;
    if (hash.includes("session_id=")) {
      const sid = new URLSearchParams(hash.replace("#", "")).get("session_id");
      if (sid) {
        api.post("/auth/google", { session_id: sid })
          .then(({ data }) => {
            localStorage.setItem("hub3_token", data.token);
            setUser(data);
            window.location.hash = "";
            window.location.replace("/dashboard");
          })
          .catch(() => setLoading(false));
        return;
      }
    }
    refreshUser();
  }, [refreshUser]);

  const login = async (email, password) => {
    const { data } = await api.post("/auth/login", { email, password });
    localStorage.setItem("hub3_token", data.token);
    setUser(data);
    return data;
  };
  const register = async (email, password, name) => {
    const { data } = await api.post("/auth/register", { email, password, name });
    localStorage.setItem("hub3_token", data.token);
    setUser(data);
    return data;
  };
  const logout = async () => {
    try { await api.post("/auth/logout"); } catch {}
    localStorage.removeItem("hub3_token");
    setUser(null);
  };
  const loginWithGoogle = () => {
    const redirect = `${window.location.origin}/dashboard`;
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirect)}`;
  };

  return (
    <AppCtx.Provider value={{ user, loading, lang, t, setLanguage, login, register, logout, loginWithGoogle, refreshUser }}>
      {children}
    </AppCtx.Provider>
  );
}
