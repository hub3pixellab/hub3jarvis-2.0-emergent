import React, { useEffect, useState } from "react";
import { useApp, api } from "@/contexts/AppContext";
import AppShell from "@/components/AppShell";
import { Brain, Plus, Search, Trash2, ShieldCheck, Phone, User as UserIcon, Zap, TrendingUp, ThumbsUp, ThumbsDown, Upload, Sparkles } from "lucide-react";

export default function BrainPage() {
  const { t, lang } = useApp();
  const [tab, setTab] = useState("brain"); // brain | policy | learning
  const [items, setItems] = useState([]);
  const [content, setContent] = useState("");
  const [query, setQuery] = useState("");
  const [searchRes, setSearchRes] = useState(null);
  const [stats, setStats] = useState({total_knowledge: 0, total_preferences: 0});
  const [patterns, setPatterns] = useState(null);
  const [whitelist, setWhitelist] = useState([]);
  const [wlForm, setWlForm] = useState({phone:"", name:"", level:"absolute"});

  const load = async () => {
    const [rec, st, wl, pt] = await Promise.all([
      api.get("/brain/recent"),
      api.get("/brain/stats"),
      api.get("/policy/whitelist"),
      api.get("/learning/patterns"),
    ]);
    setItems(rec.data);
    setStats(st.data);
    setWhitelist(wl.data);
    setPatterns(pt.data);
  };
  useEffect(() => { load(); }, []);

  const add = async () => {
    if (!content.trim()) return;
    await api.post("/brain/add", { content, source: "manual", k_type: "insight" });
    setContent("");
    load();
  };
  const search = async () => {
    if (!query.trim()) { setSearchRes(null); return; }
    const { data } = await api.post("/brain/search", { query, limit: 10 });
    setSearchRes(data);
  };
  const addWhitelist = async () => {
    if (!wlForm.phone || !wlForm.name) return;
    await api.post("/policy/whitelist", wlForm);
    setWlForm({phone:"", name:"", level:"absolute"});
    load();
  };

  return (
    <AppShell>
      <div className="grid-bg p-6" data-testid="brain-page">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2"><Brain className="text-cyan" size={24}/> {lang==='pt'?'Segundo Cérebro & Governança':'Second Brain & Governance'}</h1>
            <div className="text-sm text-slate-400">{lang==='pt'?'Memória de longo prazo, políticas de proteção e aprendizado contínuo':'Long-term memory, protection policies & self-learning'}</div>
          </div>
          <div className="flex gap-4">
            <StatBox icon={Brain} value={stats.total_knowledge} label={lang==='pt'?'Conhecimentos':'Knowledge'}/>
            <StatBox icon={UserIcon} value={stats.total_preferences} label={lang==='pt'?'Preferências':'Preferences'}/>
            <StatBox icon={ShieldCheck} value={whitelist.length} label={lang==='pt'?'Whitelist':'Whitelist'}/>
            <StatBox icon={TrendingUp} value={patterns?.total_interactions ?? 0} label={lang==='pt'?'Interações IA':'AI Interactions'}/>
          </div>
        </div>

        <div className="flex gap-2 mb-5">
          {[
            {k:"brain", label: lang==='pt'?'Segundo Cérebro':'Second Brain', icon: Brain},
            {k:"policy", label: lang==='pt'?'Motor de Políticas':'Policy Engine', icon: ShieldCheck},
            {k:"learning", label: lang==='pt'?'Auto-Aprendizado':'Self-Learning', icon: Zap},
          ].map(x => (
            <button key={x.k} onClick={()=>setTab(x.k)} data-testid={`brain-tab-${x.k}`} className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm transition ${tab===x.k?'bg-cyan-500/15 border border-cyan-500/50 text-cyan':'border border-cyan-500/20 text-slate-400 hover:text-white'}`}>
              <x.icon size={14}/> {x.label}
            </button>
          ))}
        </div>

        {tab === "brain" && (
          <div className="grid grid-cols-2 gap-5">
            <div className="hud-card p-5 relative"><div className="hud-bl"/><div className="hud-br"/>
              <div className="label-mini mb-3 text-cyan flex items-center gap-2"><Plus size={12}/> {lang==='pt'?'Adicionar conhecimento':'Add knowledge'}</div>
              <textarea data-testid="brain-add-input" value={content} onChange={e=>setContent(e.target.value)} placeholder={lang==='pt'?'Ex: Meu objetivo Q2 é lançar o Project Orion...':'e.g. My Q2 goal is to launch Project Orion...'} rows={4} className="w-full bg-[#0A0E27] border border-cyan-500/25 rounded-lg p-3 text-sm resize-none focus:outline-none focus:border-cyan"/>
              <button onClick={add} data-testid="brain-add-btn" className="btn-primary mt-2 flex items-center gap-2"><Plus size={14}/> {lang==='pt'?'Guardar no cérebro':'Store in brain'}</button>

              <div className="mt-4 flex items-center gap-2 border-t border-cyan-500/15 pt-4">
                <label data-testid="brain-import-label" className="btn-secondary flex items-center gap-2 cursor-pointer text-xs">
                  <Upload size={13}/> {lang==='pt'?'Importar JSON':'Import JSON'}
                  <input type="file" accept="application/json,.json" data-testid="brain-import-file" className="hidden" onChange={async (e)=>{
                    const f = e.target.files?.[0]; if (!f) return;
                    const fd = new FormData(); fd.append("file", f);
                    const { data } = await api.post("/brain/import-file", fd, { headers: { "Content-Type": "multipart/form-data" } });
                    alert((lang==='pt'?'Importado: ':'Imported: ') + (data.inserted || 0) + (lang==='pt'?' itens':' items'));
                    load();
                  }}/>
                </label>
                <button onClick={async ()=>{const {data}=await api.post("/brain/reindex"); alert(`${lang==='pt'?'Re-indexados':'Re-indexed'}: ${data.reindexed}`); load();}} data-testid="brain-reindex-btn" className="btn-secondary flex items-center gap-2 text-xs">
                  <Sparkles size={13}/> {lang==='pt'?'Re-indexar':'Re-index'}
                </button>
                <div className="text-[10px] text-slate-500 ml-auto">
                  {lang==='pt'?'Vetores':'Vectors'}: <span className="text-cyan font-bold">{stats.with_embeddings||0}/{stats.total_knowledge||0}</span>
                </div>
              </div>

              <div className="mt-5 label-mini mb-2 text-cyan flex items-center gap-2"><Search size={12}/> {lang==='pt'?'Buscar semântica':'Semantic search'}</div>
              <div className="flex gap-2">
                <input value={query} onChange={e=>setQuery(e.target.value)} onKeyDown={e=>e.key==='Enter'&&search()} data-testid="brain-search-input" placeholder={lang==='pt'?'Ex: projeto orion':'e.g. project orion'} className="flex-1 bg-[#0A0E27] border border-cyan-500/25 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-cyan"/>
                <button onClick={search} data-testid="brain-search-btn" className="btn-secondary">{lang==='pt'?'Buscar':'Search'}</button>
              </div>
              {searchRes && (
                <div className="mt-3 space-y-2">
                  <div className="text-xs text-slate-500">{searchRes.length} {lang==='pt'?'resultado(s)':'result(s)'}</div>
                  {searchRes.map(r => (
                    <div key={r.id} className="border border-cyan-500/20 rounded-lg p-2 text-xs">
                      <div className="text-slate-300">{r.content}</div>
                      <div className="text-[10px] text-slate-500 mt-1 flex justify-between">
                        <span>
                          {r.match === 'semantic'
                            ? <><span className="text-cyan">semantic</span> · sim {(r.similarity*100).toFixed(1)}%</>
                            : <>keyword · score {r.relevance_score}</>}
                        </span>
                        <span>{r.source}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="hud-card p-5 relative"><div className="hud-bl"/><div className="hud-br"/>
              <div className="label-mini mb-3 text-cyan">{lang==='pt'?'Últimas memórias':'Recent memories'}</div>
              <div className="space-y-2 max-h-[500px] overflow-y-auto">
                {items.length === 0 && <div className="text-sm text-slate-500">{lang==='pt'?'Nada guardado ainda.':'Nothing stored yet.'}</div>}
                {items.map(it => (
                  <div key={it.id} className="border border-cyan-500/15 rounded-lg p-3 text-sm">
                    <div className="text-slate-200">{it.content}</div>
                    <div className="text-[10px] text-slate-500 mt-1 flex justify-between">
                      <span>{it.source} · {it.type}</span>
                      <span>{new Date(it.created_at).toLocaleString()}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {tab === "policy" && (
          <div className="grid grid-cols-2 gap-5">
            <div className="hud-card p-5 relative"><div className="hud-bl"/><div className="hud-br"/>
              <div className="label-mini mb-3 text-cyan flex items-center gap-2"><ShieldCheck size={12}/> {lang==='pt'?'As 3 Leis':'The 3 Laws'}</div>
              <div className="space-y-3 text-sm">
                <Law num="1" title={lang==='pt'?'Whitelist de contatos protegidos':'Protected contacts whitelist'} desc={lang==='pt'?'Contatos na whitelist têm níveis de proteção (absolute/high/medium). Ações vetadas são recusadas pelo Jarvis.':'Whitelisted contacts have protection levels (absolute/high/medium). Forbidden actions get refused by Jarvis.'}/>
                <Law num="2" title={lang==='pt'?'Confirmação em ações sensíveis':'Confirmation on sensitive actions'} desc={lang==='pt'?'Financeiro, jurídico, envio de e-mail, WhatsApp, controle de dispositivo — tudo requer confirmação.':'Financial, legal, email/WhatsApp send, device control — all require confirmation.'}/>
                <Law num="3" title={lang==='pt'?'Fontes bloqueadas em pesquisas':'Blocked search sources'} desc={lang==='pt'?'Onion / darknet / tor / dark.web nunca são consultados pelo Deep Search.':'Onion / darknet / tor / dark.web are never queried by Deep Search.'}/>
              </div>
            </div>
            <div className="hud-card p-5 relative"><div className="hud-bl"/><div className="hud-br"/>
              <div className="label-mini mb-3 text-cyan flex items-center gap-2"><Phone size={12}/> {lang==='pt'?'Whitelist':'Whitelist'}</div>
              <div className="grid grid-cols-4 gap-2 mb-3">
                <input value={wlForm.name} onChange={e=>setWlForm({...wlForm, name:e.target.value})} placeholder="Nome" data-testid="wl-name" className="col-span-2 bg-[#0A0E27] border border-cyan-500/25 rounded-lg px-2 py-1.5 text-xs"/>
                <input value={wlForm.phone} onChange={e=>setWlForm({...wlForm, phone:e.target.value})} placeholder="+55..." data-testid="wl-phone" className="bg-[#0A0E27] border border-cyan-500/25 rounded-lg px-2 py-1.5 text-xs"/>
                <select value={wlForm.level} onChange={e=>setWlForm({...wlForm, level:e.target.value})} className="bg-[#0A0E27] border border-cyan-500/25 rounded-lg px-2 py-1.5 text-xs text-white">
                  <option value="absolute">absolute</option>
                  <option value="high">high</option>
                  <option value="medium">medium</option>
                </select>
              </div>
              <button onClick={addWhitelist} data-testid="wl-add-btn" className="btn-primary text-xs w-full">+ {lang==='pt'?'Adicionar contato':'Add contact'}</button>
              <div className="mt-3 space-y-1 max-h-[300px] overflow-y-auto">
                {whitelist.length === 0 && <div className="text-xs text-slate-500">{lang==='pt'?'Nenhum contato protegido.':'No protected contact yet.'}</div>}
                {whitelist.map(c => (
                  <div key={c.phone} className="flex items-center justify-between border border-cyan-500/15 rounded-lg px-3 py-2 text-xs">
                    <span>{c.name} · <span className="text-slate-500">{c.phone}</span></span>
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${c.level==='absolute'?'bg-red-500/20 text-red-400':c.level==='high'?'bg-orange-500/20 text-orange-400':'bg-cyan-500/20 text-cyan'}`}>{c.level}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {tab === "learning" && patterns && (
          <div className="grid grid-cols-3 gap-5">
            <div className="hud-card p-5 relative"><div className="hud-bl"/><div className="hud-br"/>
              <div className="label-mini text-cyan mb-2">{lang==='pt'?'Total de interações':'Total interactions'}</div>
              <div className="text-5xl font-black">{patterns.total_interactions}</div>
              <div className="text-xs text-slate-400 mt-1">custo acumulado: ${patterns.total_cost}</div>
            </div>
            <div className="hud-card p-5 relative"><div className="hud-bl"/><div className="hud-br"/>
              <div className="label-mini text-cyan mb-2">{lang==='pt'?'Satisfação':'Satisfaction rate'}</div>
              <div className="text-5xl font-black text-green-400">{patterns.satisfaction_rate}%</div>
              <div className="flex gap-3 text-xs mt-2">
                <span className="text-green-400 flex items-center gap-1"><ThumbsUp size={12}/> {patterns.positive_feedback}</span>
                <span className="text-red-400 flex items-center gap-1"><ThumbsDown size={12}/> {patterns.negative_feedback}</span>
              </div>
            </div>
            <div className="hud-card p-5 relative"><div className="hud-bl"/><div className="hud-br"/>
              <div className="label-mini text-cyan mb-2">{lang==='pt'?'Uso por modelo':'Model usage'}</div>
              {Object.keys(patterns.model_usage).length === 0 && <div className="text-xs text-slate-500">{lang==='pt'?'Faça uma pergunta no Consensus para começar.':'Ask a question on Consensus to start.'}</div>}
              {Object.entries(patterns.model_usage).map(([m,c]) => (
                <div key={m} className="flex items-center justify-between text-sm py-1">
                  <span className="text-slate-300 truncate">{m}</span>
                  <span className="font-bold text-cyan">{c}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}

function StatBox({icon:I, value, label}) {
  return (
    <div className="hud-card px-4 py-2 relative min-w-[110px]"><div className="hud-bl"/><div className="hud-br"/>
      <div className="flex items-center gap-2">
        <div className="halo-icon" style={{width:28,height:28}}><I size={13}/></div>
        <div>
          <div className="text-xl font-black leading-none">{value}</div>
          <div className="label-mini">{label}</div>
        </div>
      </div>
    </div>
  );
}
function Law({num, title, desc}) {
  return (
    <div className="flex gap-3 border border-cyan-500/15 rounded-lg p-3">
      <div className="w-9 h-9 rounded-full bg-orange-500/15 border border-orange-400 text-orange font-bold flex items-center justify-center shrink-0">{num}</div>
      <div>
        <div className="font-semibold text-white text-sm">{title}</div>
        <div className="text-xs text-slate-400">{desc}</div>
      </div>
    </div>
  );
}
