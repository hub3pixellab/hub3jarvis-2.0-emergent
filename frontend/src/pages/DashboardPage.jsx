import React, { useEffect, useState, useRef, useMemo } from "react";
import { useApp, api } from "@/contexts/AppContext";
import AppShell from "@/components/AppShell";
import { User, Target, Briefcase, Layers, DollarSign, BookOpen, HeartPulse, Users, Lightbulb, Share2, Clock, TrendingUp, Mic, Bell, Calendar, Settings, ChevronRight, Trophy, Zap, Brain } from "lucide-react";
import ForceGraph2D from "react-force-graph-2d";

const ICON = { user: User, target: Target, briefcase: Briefcase, layers: Layers, "dollar-sign": DollarSign, "book-open": BookOpen, "heart-pulse": HeartPulse, users: Users, lightbulb: Lightbulb, "share-2": Share2, clock: Clock, "trending-up": TrendingUp };

function LifeBalanceDonut({ value }) {
  const R = 26, C = 2 * Math.PI * R;
  return (
    <div className="flex items-center gap-3">
      <svg width="70" height="70" viewBox="0 0 70 70">
        <circle cx="35" cy="35" r={R} stroke="#1a2340" strokeWidth="8" fill="none" />
        <circle cx="35" cy="35" r={R} stroke="url(#donutGrad)" strokeWidth="8" fill="none" strokeDasharray={`${(value/100)*C} ${C}`} strokeDashoffset={C/4} strokeLinecap="round" transform="rotate(-90 35 35)" />
        <defs><linearGradient id="donutGrad" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stopColor="#00D4FF"/><stop offset="100%" stopColor="#FF8C42"/></linearGradient></defs>
      </svg>
      <div>
        <div className="text-2xl font-bold">{value}%</div>
        <div className="label-mini">Balanced</div>
      </div>
    </div>
  );
}

function BrainGraph({ areas }) {
  const ref = useRef();
  const containerRef = useRef();
  const [dims, setDims] = useState({ w: 600, h: 380 });
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const ro = new ResizeObserver(() => {
      setDims({ w: el.clientWidth, h: el.clientHeight });
    });
    ro.observe(el);
    setDims({ w: el.clientWidth, h: el.clientHeight });
    return () => ro.disconnect();
  }, []);
  useEffect(() => {
    if (!ref.current) return;
    try {
      const fg = ref.current;
      fg.d3Force('link').distance(120).strength(0.5);
      fg.d3Force('charge').strength(-350);
    } catch {}
    setTimeout(() => { try { ref.current.zoom(2.2, 500); ref.current.centerAt(0, 0, 500); } catch {} }, 1200);
  }, [dims]);
  const data = useMemo(() => {
    const nodes = [{ id: "hub3", name: "Hub3", size: 28, color: "#00D4FF", central: true, fx: 0, fy: 0 }];
    areas.forEach((a) => nodes.push({ id: a.key, name: a.en, size: 14, color: a.color }));
    const links = areas.map((a) => ({ source: "hub3", target: a.key, color: a.color }));
    for (let i = 0; i < areas.length; i++) {
      links.push({ source: areas[i].key, target: areas[(i+2) % areas.length].key, color: "#00D4FF" });
    }
    return { nodes, links };
  }, [areas]);

  return (
    <div ref={containerRef} className="w-full h-full neural-container relative overflow-hidden">
      <ForceGraph2D
        ref={ref}
        width={dims.w}
        height={dims.h}
        graphData={data}
        backgroundColor="rgba(0,0,0,0)"
        d3AlphaDecay={0.02}
        d3VelocityDecay={0.4}
        enableZoomInteraction={false}
        enablePanInteraction={false}
        nodeLabel="name"
        linkColor={(l) => l.color}
        linkWidth={0.8}
        linkDirectionalParticles={2}
        linkDirectionalParticleWidth={1.8}
        linkDirectionalParticleColor={(l) => l.color}
        linkDirectionalParticleSpeed={0.006}
        cooldownTicks={80}
        nodeCanvasObject={(node, ctx) => {
          const r = node.central ? 20 : 10;
          ctx.beginPath();
          ctx.arc(node.x, node.y, r + 4, 0, 2*Math.PI);
          ctx.fillStyle = node.central ? "rgba(0,212,255,0.15)" : `${node.color}22`;
          ctx.fill();
          ctx.beginPath();
          ctx.arc(node.x, node.y, r, 0, 2*Math.PI);
          ctx.fillStyle = node.central ? "#0A0E27" : "#0F1729";
          ctx.fill();
          ctx.lineWidth = 1.5;
          ctx.strokeStyle = node.color;
          ctx.stroke();
          ctx.fillStyle = "#fff";
          ctx.font = `${node.central ? 700 : 500} ${node.central ? 10 : 7}px Inter`;
          ctx.textAlign = "center"; ctx.textBaseline = "middle";
          ctx.fillText(node.name, node.x, node.central ? node.y : node.y + r + 8);
        }}
      />
    </div>
  );
}

export default function DashboardPage() {
  const { user, t, lang } = useApp();
  const [data, setData] = useState(null);
  useEffect(() => { api.get("/dashboard/overview").then(({data}) => setData(data)); }, []);

  const h = new Date().getHours();
  const greet = h < 12 ? t.goodMorning : h < 18 ? t.goodAfternoon : t.goodEvening;
  const now = new Date();
  const dateStr = now.toLocaleDateString(lang === 'pt' ? 'pt-BR' : 'en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' });
  const timeStr = now.toLocaleTimeString(lang === 'pt' ? 'pt-BR' : 'en-US', { hour: '2-digit', minute: '2-digit' });

  if (!data) return <AppShell><div className="p-10 text-slate-400">Loading…</div></AppShell>;

  return (
    <AppShell>
      <div className="grid-bg p-6" data-testid="dashboard-page">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">{greet}, {user?.name?.split(' ')[0] || 'Alex'} <span>👋</span></h1>
            <div className="text-sm text-slate-400">{dateStr} · {timeStr}</div>
          </div>
          <div className="flex items-center gap-4">
            <div className="hud-card px-6 py-2 flex items-center gap-3 relative ei-hub-glow rounded-full" data-testid="ei-hub-button">
              <div className="wave-bars"><span/><span/><span/><span/><span/></div>
              <div className="w-10 h-10 rounded-full bg-cyan-500/20 border border-cyan flex items-center justify-center">
                <Mic size={16} className="text-cyan"/>
              </div>
              <div>
                <div className="font-brand font-bold">{t.eiHub}</div>
                <div className="text-[10px] text-slate-400">{t.tapToActivate}</div>
              </div>
              <div className="wave-bars"><span/><span/><span/><span/><span/></div>
            </div>
            <div className="flex items-center gap-2">
              {[Bell, Calendar, Settings].map((I, i) => (
                <button key={i} className="w-10 h-10 rounded-lg border border-cyan-500/25 hover:border-cyan-500/60 transition flex items-center justify-center text-slate-300">
                  <I size={16}/>
                </button>
              ))}
              <div className="flex items-center gap-2 pl-2">
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-cyan-500 to-orange-500 flex items-center justify-center font-bold">
                  {(user?.name || 'A')[0].toUpperCase()}
                </div>
                <div className="text-sm">
                  <div className="font-semibold">{user?.name || 'Alex Morgan'}</div>
                  <div className="text-[10px] text-cyan">{t.premiumMember}</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-12 gap-5">
          {/* Life areas panel */}
          <div className="col-span-2 hud-card p-4 relative"><div className="hud-bl"/><div className="hud-br"/>
            <div className="space-y-2">
              {data.life_areas.map((a, i) => {
                const Icon = ICON[a.icon] || User;
                return (
                  <div key={a.key} data-testid={`area-${a.key}`} className={`flex items-center gap-3 p-2 rounded-lg cursor-pointer transition ${i===0?'bg-cyan-500/10 border border-cyan-500/40':'hover:bg-white/5 border border-transparent'}`}>
                    <div className={`halo-icon ${a.color === '#FF8C42' ? 'orange' : a.color === '#FF4757' ? 'red' : ''}`} style={{width:34,height:34}}>
                      <Icon size={15}/>
                    </div>
                    <div className="min-w-0">
                      <div className="text-sm font-semibold truncate">{lang === 'pt' ? a.pt : a.en}</div>
                      <div className="text-[10px] text-slate-500 truncate">{lang === 'pt' ? a.sub_pt : a.sub_en}</div>
                    </div>
                    {i===0 && <div className="w-2 h-2 rounded-full bg-cyan ml-auto"/>}
                  </div>
                );
              })}
            </div>
            <div className="mt-4 pt-4 border-t border-cyan-500/15">
              <div className="label-mini mb-2 flex justify-between">{t.lifeBalance} <ChevronRight size={12}/></div>
              <LifeBalanceDonut value={data.life_balance.score}/>
            </div>
          </div>

          {/* Center Brain Network */}
          <div className="col-span-7 hud-card p-4 relative flex flex-col"><div className="hud-bl"/><div className="hud-br"/>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Brain className="text-cyan" size={18}/>
                <div>
                  <div className="font-semibold text-cyan">{t.aiBrainNetwork}</div>
                  <div className="text-xs text-slate-400">{t.realTimeAnalysis}</div>
                </div>
              </div>
              <div className="flex items-center gap-1.5 border border-green-500/30 text-green-400 px-3 py-1 rounded-full text-[10px] font-bold">
                <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse"/> {t.live}
              </div>
            </div>
            <div className="flex-1 min-h-[380px]" data-testid="brain-network">
              <BrainGraph areas={data.life_areas}/>
            </div>
            {/* Metrics */}
            <div className="grid grid-cols-4 gap-3 mt-3">
              {data.metrics.map((m) => {
                const Icon = ICON[m.icon] || Lightbulb;
                return (
                  <div key={m.key} className="hud-card p-3 relative"><div className="hud-bl"/><div className="hud-br"/>
                    <div className="flex items-center gap-2 mb-2">
                      <div className="halo-icon orange" style={{width:28,height:28}}><Icon size={13}/></div>
                      <div className="label-mini">{lang==='pt'?m.label_pt:m.label_en}</div>
                    </div>
                    <div className="text-3xl font-black">{m.value}</div>
                    <div className="text-[11px] text-green-400 mt-1">↑ {m.delta}% {t.vsYesterday}</div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Right Consensus Panel */}
          <div className="col-span-3 space-y-4">
            <div className="hud-card p-4 relative"><div className="hud-bl"/><div className="hud-br"/>
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-2"><Brain className="text-cyan" size={16}/><span className="font-semibold">{t.aiConsensus}</span></div>
                <span className="text-[10px] font-bold text-cyan bg-cyan-500/10 border border-cyan-500/30 px-2 py-0.5 rounded-full">8 {t.aiModels}</span>
              </div>
              <div className="text-xs text-slate-400 mb-3">{t.multiAIPerspective}</div>
              <div className="rounded-lg border border-orange-400/40 bg-orange-500/5 p-3 mb-3">
                <div className="label-mini text-orange mb-1">{t.topRecommendation}</div>
                <div className="flex items-start gap-2">
                  <Trophy className="text-orange mt-0.5" size={18}/>
                  <div className="flex-1">
                    <div className="font-semibold text-sm">{lang==='pt'?data.top_recommendation.title_pt:data.top_recommendation.title_en}</div>
                    <div className="text-xs text-slate-400">{lang==='pt'?data.top_recommendation.desc_pt:data.top_recommendation.desc_en}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-xl font-black text-orange">{data.top_recommendation.consensus}%</div>
                    <div className="text-[9px] text-slate-400">{t.consensusLbl}</div>
                  </div>
                </div>
              </div>
              <div className="label-mini mb-2">{t.aiModelBreakdown}</div>
              <div className="space-y-2">
                {data.ai_models_breakdown.map((m) => (
                  <div key={m.name} className="flex items-center gap-2 text-sm">
                    <div className="w-6 h-6 rounded-md bg-slate-800 border border-cyan-500/20 text-cyan text-[10px] font-bold flex items-center justify-center">{m.icon}</div>
                    <div className="w-24 truncate">{m.name}</div>
                    <div className="flex-1 h-1.5 bg-slate-800 rounded-full overflow-hidden"><div className="h-full grad-bar" style={{width:`${m.score}%`}}/></div>
                    <div className="w-9 text-right text-xs font-semibold">{m.score}%</div>
                  </div>
                ))}
              </div>
              <button className="btn-secondary w-full mt-4 flex items-center justify-center gap-2 text-sm">{t.viewFullAnalysis} <ChevronRight size={14}/></button>
            </div>

            <div className="hud-card p-4 relative"><div className="hud-bl"/><div className="hud-br"/>
              <div className="label-mini text-orange mb-2 flex items-center gap-1"><Zap size={12}/>{t.nextBestAction}</div>
              <div className="flex gap-2">
                <div className="flex-1">
                  <div className="font-semibold text-sm">{lang==='pt'?data.next_best_action.title_pt:data.next_best_action.title_en}</div>
                  <div className="text-xs text-slate-400">{lang==='pt'?data.next_best_action.desc_pt:data.next_best_action.desc_en}</div>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-black text-cyan">{data.next_best_action.impact}%</div>
                  <div className="text-[9px] text-slate-400">{t.impactScore}</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-6 flex items-center justify-between text-xs text-slate-500">
          <div className="italic">{lang==='pt'?data.quote.pt:data.quote.en}</div>
          <div className="flex items-center gap-2 text-cyan"><Brain size={13}/>Hub3 is continuously learning and optimizing for you</div>
        </div>
      </div>
    </AppShell>
  );
}
