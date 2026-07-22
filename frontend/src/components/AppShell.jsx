import React from "react";
import { NavLink, useLocation, useNavigate } from "react-router-dom";
import { Home, Network, HouseWifi, MessageCircle, Brain, LogOut, Globe2, Bell, Calendar, Settings } from "lucide-react";
import { useApp } from "@/contexts/AppContext";

export default function AppShell({ children }) {
  const { user, lang, setLanguage, t, logout } = useApp();
  const navigate = useNavigate();
  const loc = useLocation();

  const navItems = [
    { to: "/dashboard", icon: Home, label: t.dashboard, testid: "nav-dashboard" },
    { to: "/consensus", icon: Network, label: t.consensus, testid: "nav-consensus" },
    { to: "/brain", icon: Brain, label: lang==='pt'?'Cérebro':'Brain', testid: "nav-brain" },
    { to: "/smart-home", icon: HouseWifi, label: t.smartHome, testid: "nav-smart-home" },
    { to: "/chat", icon: MessageCircle, label: t.chat, testid: "nav-chat" },
  ];

  // Chat and Smart Home have their own custom left panels, so we render just a slim top bar for those
  const bareLayout = ["/chat", "/smart-home"].some((p) => loc.pathname.startsWith(p));

  if (bareLayout) {
    return (
      <div className="min-h-screen bg-dashboard flex">
        {/* slim rail */}
        <aside className="w-16 border-r border-cyan-500/10 py-4 flex flex-col items-center gap-4 bg-[#0A0E27]" data-testid="app-slim-rail">
          <div className="w-9 h-9 rounded-lg bg-cyan-500/10 border border-cyan-500/40 flex items-center justify-center font-brand text-cyan text-sm">H3</div>
          {navItems.map((n) => (
            <NavLink key={n.to} to={n.to} data-testid={n.testid} className={({isActive}) => `w-10 h-10 rounded-lg flex items-center justify-center border transition ${isActive ? 'bg-cyan-500/15 border-cyan-500/60 text-cyan' : 'border-transparent text-slate-400 hover:text-cyan hover:border-cyan-500/30'}`}>
              <n.icon size={18} />
            </NavLink>
          ))}
          <div className="flex-1" />
          <button onClick={() => setLanguage(lang === 'en' ? 'pt' : 'en')} data-testid="lang-toggle" className="w-10 h-10 rounded-lg border border-cyan-500/30 text-cyan text-[10px] font-bold uppercase tracking-wider">
            {lang.toUpperCase()}
          </button>
          <button onClick={async () => { await logout(); navigate('/login'); }} data-testid="logout-btn" className="w-10 h-10 rounded-lg border border-red-500/30 text-red-400 flex items-center justify-center hover:bg-red-500/10 transition">
            <LogOut size={16} />
          </button>
        </aside>
        <div className="flex-1 min-w-0">{children}</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-dashboard flex">
      <aside className="w-64 shrink-0 border-r border-cyan-500/15 bg-[#0A0E27] p-5 flex flex-col" data-testid="app-sidebar">
        <div className="flex items-center gap-3 mb-8">
          <div className="w-11 h-11 rounded-xl bg-cyan-500/10 border border-cyan-500/40 flex items-center justify-center">
            <Network size={20} className="text-cyan" />
          </div>
          <div>
            <div className="font-brand text-2xl font-bold text-white leading-none">Hub3</div>
            <div className="text-[10px] uppercase tracking-widest text-slate-500 mt-1">JARVIS v4.2</div>
          </div>
        </div>

        <nav className="flex flex-col gap-1 flex-1">
          {navItems.map((n) => (
            <NavLink key={n.to} to={n.to} data-testid={n.testid} className={({isActive}) => `flex items-center gap-3 px-3 py-2.5 rounded-lg transition ${isActive ? 'bg-cyan-500/10 border border-cyan-500/40 text-cyan' : 'text-slate-400 hover:text-white hover:bg-white/5 border border-transparent'}`}>
              <n.icon size={18} />
              <span className="text-sm font-medium">{n.label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="mt-4 space-y-3">
          <button onClick={() => setLanguage(lang === 'en' ? 'pt' : 'en')} data-testid="lang-toggle" className="w-full flex items-center justify-between px-3 py-2 rounded-lg border border-cyan-500/25 text-slate-300 hover:text-cyan hover:border-cyan-500/50 transition">
            <span className="flex items-center gap-2 text-sm"><Globe2 size={14}/> {lang === 'en' ? 'English' : 'Português'}</span>
            <span className="text-[10px] font-bold text-cyan">{lang.toUpperCase()}</span>
          </button>
          <button onClick={async () => { await logout(); navigate('/login'); }} data-testid="logout-btn" className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-slate-400 hover:text-red-400 hover:bg-red-500/10 transition text-sm">
            <LogOut size={16} /> {t.logout}
          </button>
        </div>
      </aside>
      <div className="flex-1 min-w-0">{children}</div>
    </div>
  );
}
