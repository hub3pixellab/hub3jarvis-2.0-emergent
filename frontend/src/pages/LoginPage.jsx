import React, { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { useApp } from "@/contexts/AppContext";
import { Network, Mail, Lock, User, Chrome } from "lucide-react";

export default function LoginPage() {
  const { user, login, register, loginWithGoogle, t, lang, setLanguage } = useApp();
  const nav = useNavigate();
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ email: "", password: "", name: "" });
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);

  if (user) return <Navigate to="/dashboard" replace />;

  const submit = async (e) => {
    e.preventDefault();
    setErr(""); setLoading(true);
    try {
      if (mode === "login") await login(form.email, form.password);
      else await register(form.email, form.password, form.name);
      nav("/dashboard");
    } catch (ex) {
      const d = ex.response?.data?.detail;
      setErr(typeof d === "string" ? d : (d?.[0]?.msg || ex.message));
    } finally { setLoading(false); }
  };

  return (
    <div className="min-h-screen grid-bg bg-dashboard flex items-center justify-center p-6">
      <div className="w-full max-w-md">
        <button onClick={() => setLanguage(lang === 'en' ? 'pt' : 'en')} data-testid="lang-toggle-login" className="mb-4 text-[10px] font-bold uppercase tracking-widest text-cyan border border-cyan-500/40 px-3 py-1.5 rounded-full">
          {lang.toUpperCase()} · {lang === 'en' ? 'Português?' : 'English?'}
        </button>
        <div className="hud-card p-8 relative">
          <div className="hud-bl"></div><div className="hud-br"></div>
          <div className="flex items-center gap-3 mb-1">
            <div className="w-12 h-12 rounded-xl bg-cyan-500/10 border border-cyan-500/40 flex items-center justify-center">
              <Network className="text-cyan" size={22} />
            </div>
            <div>
              <h1 className="font-brand text-3xl font-bold">Hub3</h1>
              <div className="text-[10px] uppercase tracking-widest text-slate-500">JARVIS v4.2</div>
            </div>
          </div>
          <p className="text-slate-400 text-sm mt-4">{t.tagline}</p>
          <h2 className="mt-6 text-xl font-semibold">{mode === "login" ? t.welcomeBack : t.createAccount}</h2>

          <form onSubmit={submit} className="mt-6 space-y-3">
            {mode === "register" && (
              <div className="relative">
                <User size={16} className="absolute left-3 top-3.5 text-slate-500" />
                <input required data-testid="input-name" value={form.name} onChange={(e) => setForm({...form, name: e.target.value})} placeholder={t.name} className="w-full bg-[#0A0E27] border border-cyan-500/25 rounded-lg pl-10 pr-3 py-3 text-sm placeholder-slate-500 focus:border-cyan-500/60 focus:outline-none" />
              </div>
            )}
            <div className="relative">
              <Mail size={16} className="absolute left-3 top-3.5 text-slate-500" />
              <input required type="email" data-testid="input-email" value={form.email} onChange={(e) => setForm({...form, email: e.target.value})} placeholder={t.email} className="w-full bg-[#0A0E27] border border-cyan-500/25 rounded-lg pl-10 pr-3 py-3 text-sm placeholder-slate-500 focus:border-cyan-500/60 focus:outline-none" />
            </div>
            <div className="relative">
              <Lock size={16} className="absolute left-3 top-3.5 text-slate-500" />
              <input required type="password" data-testid="input-password" value={form.password} onChange={(e) => setForm({...form, password: e.target.value})} placeholder={t.password} className="w-full bg-[#0A0E27] border border-cyan-500/25 rounded-lg pl-10 pr-3 py-3 text-sm placeholder-slate-500 focus:border-cyan-500/60 focus:outline-none" />
            </div>
            {err && <div data-testid="auth-error" className="text-red-400 text-xs">{err}</div>}
            <button type="submit" data-testid="auth-submit" disabled={loading} className="btn-primary w-full disabled:opacity-60">
              {loading ? "…" : (mode === "login" ? t.signIn : t.signUp)}
            </button>
          </form>

          <div className="flex items-center gap-3 my-5">
            <div className="flex-1 h-px bg-cyan-500/15" />
            <span className="text-xs text-slate-500 uppercase tracking-widest">{t.or}</span>
            <div className="flex-1 h-px bg-cyan-500/15" />
          </div>

          <button onClick={loginWithGoogle} data-testid="google-auth-btn" className="btn-secondary w-full flex items-center justify-center gap-2">
            <Chrome size={16} /> {t.continueGoogle}
          </button>

          <div className="text-center text-sm text-slate-400 mt-5">
            {mode === "login" ? (
              <>{t.noAccount} <button type="button" onClick={() => setMode("register")} data-testid="switch-register" className="text-cyan hover:underline">{t.register}</button></>
            ) : (
              <>{t.haveAccount} <button type="button" onClick={() => setMode("login")} data-testid="switch-login" className="text-cyan hover:underline">{t.login}</button></>
            )}
          </div>
        </div>
        <div className="text-center text-xs text-slate-600 mt-4">© 2026 Hub3 Labs · AI Life Operating System</div>
      </div>
    </div>
  );
}
