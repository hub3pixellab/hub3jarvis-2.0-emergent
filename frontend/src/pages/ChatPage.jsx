import React, { useEffect, useRef, useState } from "react";
import { useApp, api } from "@/contexts/AppContext";
import AppShell from "@/components/AppShell";
import { MessageSquare, Users, Radio, Settings, Search, Filter, Check, Smile, Paperclip, Send, MoreVertical, ChevronRight, Bot, Lightbulb, Thermometer, Video, Tv, Power } from "lucide-react";

const AV_COLORS = { jarvis: "#00D4FF", family: "#8b5cf6", user: "#00E676", work: "#3b82f6", home: "#00E676", support: "#ec4899", group: "#8b5cf6" };

export default function ChatPage() {
  const { t, user } = useApp();
  const [convs, setConvs] = useState([]);
  const [active, setActive] = useState("jarvis");
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const scroller = useRef();

  useEffect(() => { api.get("/chat/conversations").then(({data}) => setConvs(data)); }, []);
  useEffect(() => { api.get(`/chat/history/${active}`).then(({data}) => setMessages(data)); }, [active]);
  useEffect(() => { if (scroller.current) scroller.current.scrollTop = scroller.current.scrollHeight; }, [messages]);

  const send = async () => {
    if (!input.trim() || sending) return;
    const text = input.trim();
    setInput("");
    const nowIso = new Date().toISOString();
    setMessages(m => [...m, {id:`tmp-${Date.now()}`, role:"user", text, created_at: nowIso}]);
    setSending(true);

    // Streaming via SSE
    const token = localStorage.getItem("hub3_token") || "";
    const url = `${process.env.REACT_APP_BACKEND_URL}/api/chat/stream?text=${encodeURIComponent(text)}&conversation_id=${encodeURIComponent(active)}&token=${encodeURIComponent(token)}`;
    const es = new EventSource(url);
    const aiId = `ai-${Date.now()}`;
    let aiText = "";
    let inlineCard = null;
    setMessages(m => [...m, { id: aiId, role: "assistant", text: "", created_at: new Date().toISOString(), streaming: true }]);
    es.addEventListener("meta", (ev) => {
      try {
        const meta = JSON.parse(ev.data);
        inlineCard = meta.inline_card || null;
      } catch {}
    });
    es.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data);
        if (data.delta) {
          aiText += data.delta;
          setMessages(m => m.map(x => x.id === aiId ? { ...x, text: aiText, inline_card: inlineCard } : x));
        }
      } catch {}
    };
    es.addEventListener("done", (ev) => {
      try {
        const data = JSON.parse(ev.data);
        setMessages(m => m.map(x => x.id === aiId ? { ...x, text: data.text || aiText, created_at: data.created_at, inline_card: inlineCard, streaming: false } : x));
      } catch {}
      es.close();
      setSending(false);
    });
    es.onerror = () => {
      es.close();
      setSending(false);
      setMessages(m => m.map(x => x.id === aiId ? { ...x, text: aiText || "Erro no streaming.", streaming: false } : x));
    };
  };

  const timeStr = (iso) => new Date(iso).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'});

  return (
    <AppShell>
      <div className="min-h-screen bg-dashboard flex" data-testid="chat-page">
        {/* Left */}
        <aside className="w-80 border-r border-cyan-500/15 flex flex-col shrink-0">
          <div className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-cyan-500/10 border border-cyan-500/40 flex items-center justify-center">
              <div className="w-4 h-4 border-2 border-cyan rotate-45"/>
            </div>
            <div className="font-brand text-2xl font-bold">HUB3</div>
          </div>
          <div className="flex justify-around px-4 border-b border-cyan-500/15 pb-2">
            {[MessageSquare, Users, Radio, Settings].map((I, i) => (
              <button key={i} className={`p-2 rounded-lg ${i===0?'text-cyan border-b-2 border-cyan':'text-slate-500'}`}><I size={18}/></button>
            ))}
          </div>
          <div className="p-3">
            <div className="relative">
              <Search size={13} className="absolute left-3 top-2.5 text-slate-500"/>
              <input placeholder={t.chatSearch} className="w-full bg-[#0F1729] border border-cyan-500/25 rounded-full pl-9 pr-9 py-2 text-sm focus:outline-none focus:border-cyan"/>
              <Filter size={13} className="absolute right-3 top-2.5 text-slate-500"/>
            </div>
          </div>
          <div className="flex-1 overflow-y-auto">
            {convs.map(c => (
              <button key={c.id} onClick={() => setActive(c.id)} data-testid={`conv-${c.id}`} className={`w-full flex items-center gap-3 p-3 border-l-2 transition ${active===c.id?'bg-cyan-500/10 border-cyan':'border-transparent hover:bg-white/5'}`}>
                <div className="w-11 h-11 rounded-full flex items-center justify-center font-bold text-slate-900 shrink-0" style={{background: AV_COLORS[c.avatar_type] || "#8B95A5"}}>
                  {c.avatar_type === "jarvis" ? <Bot size={18} className="text-white"/> : c.name[0]}
                </div>
                <div className="flex-1 min-w-0 text-left">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-sm truncate">{c.name}</span>
                    <span className="text-[10px] text-slate-500">{c.time}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-slate-400 truncate">{c.last}</span>
                    {c.unread > 0 && <span className="ml-2 min-w-[18px] h-4 rounded-full bg-green-500 text-[10px] font-bold flex items-center justify-center text-white px-1">{c.unread}</span>}
                  </div>
                </div>
              </button>
            ))}
          </div>
          <div className="p-3">
            <div className="hud-card p-3 relative flex items-center gap-3"><div className="hud-bl"/><div className="hud-br"/>
              <div className="w-9 h-9 rounded-lg bg-cyan-500/15 border border-cyan-500/40 flex items-center justify-center"><div className="w-3 h-3 border-2 border-cyan rotate-45"/></div>
              <div className="flex-1">
                <div className="text-cyan font-semibold text-sm">{t.hub3SmartLiving}</div>
                <div className="text-[10px] text-slate-400">{t.connectingFuture}</div>
              </div>
              <ChevronRight className="text-cyan" size={14}/>
            </div>
          </div>
        </aside>

        {/* Chat */}
        <div className="flex-1 flex flex-col min-w-0">
          <div className="flex items-center justify-between p-4 border-b border-cyan-500/15">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full border-2 border-cyan bg-[#0F1729] flex items-center justify-center"><Bot size={16} className="text-cyan"/></div>
              <div>
                <div className="font-semibold flex items-center gap-1">Hub3 Jarvis <span className="w-4 h-4 rounded-full bg-cyan flex items-center justify-center"><Check size={10} className="text-slate-900"/></span></div>
                <div className="text-[11px] text-green-400 flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-green-400"/> {t.online}</div>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <button className="text-slate-400 hover:text-cyan"><Search size={16}/></button>
              <button className="text-slate-400 hover:text-cyan"><MoreVertical size={16}/></button>
            </div>
          </div>

          <div ref={scroller} className="flex-1 overflow-y-auto p-6 space-y-3" data-testid="chat-messages">
            <div className="flex justify-center"><span className="px-3 py-1 rounded-full border border-cyan-500/25 text-[10px] text-slate-400">{t.today}</span></div>

            {messages.length === 0 && (
              <div className="text-center text-slate-500 text-sm mt-10">Say hi to Hub3 Jarvis 👋</div>
            )}

            {messages.map((m) => (
              <div key={m.id}>
                <div className={`flex gap-2 ${m.role==='user'?'justify-end':'justify-start'}`}>
                  {m.role !== 'user' && <div className="w-8 h-8 rounded-full border-2 border-cyan bg-[#0F1729] flex items-center justify-center shrink-0"><Bot size={13} className="text-cyan"/></div>}
                  <div className={`${m.role==='user'?'bubble-user':'bubble-ai'} px-3.5 py-2 max-w-[70%]`}>
                    <div className="text-sm whitespace-pre-wrap">{m.text}{m.streaming && <span className="inline-block w-1.5 h-3.5 bg-cyan align-middle ml-0.5 animate-pulse"/>}</div>
                    <div className={`text-[10px] mt-1 flex items-center justify-end gap-1 ${m.role==='user'?'text-slate-800':'text-slate-500'}`}>
                      {timeStr(m.created_at)} {m.role==='user' && <Check size={10}/>}
                    </div>
                  </div>
                </div>
                {m.inline_card === 'devices_snapshot' && (
                  <div className="flex gap-2 mt-2 ml-10">
                    <div className="hud-card p-4 relative w-full max-w-2xl"><div className="hud-bl"/><div className="hud-br"/>
                      <div className="text-sm text-slate-300 mb-3">Aqui está o status dos seus dispositivos:</div>
                      <div className="grid grid-cols-4 gap-3">
                        <div className="border border-orange-400/50 rounded-xl p-3">
                          <div className="flex items-center gap-2 mb-2"><Lightbulb size={16} className="text-orange"/><div><div className="text-sm font-semibold">Luzes da Sala</div><div className="text-[10px] text-slate-400">2 dispositivos</div></div></div>
                          <div className="flex justify-center"><div className="w-14 h-7 rounded-full bg-orange-500 flex items-center px-1 justify-end"><div className="w-5 h-5 rounded-full bg-white"/></div></div>
                          <div className="text-center text-[10px] text-orange font-bold mt-1">ON</div>
                        </div>
                        <div className="border border-orange-400/50 rounded-xl p-3">
                          <div className="flex items-center gap-2 mb-2"><Thermometer size={16} className="text-orange"/><div><div className="text-sm font-semibold">Termostato</div><div className="text-[10px] text-slate-400">Sala</div></div></div>
                          <div className="text-center text-2xl font-black">23°<span className="text-xs">C</span></div>
                          <div className="h-1.5 bg-slate-700 rounded-full my-1"><div className="h-full grad-bar rounded-full" style={{width:'50%'}}/></div>
                          <div className="flex justify-between text-[9px] text-slate-500"><span>16°C</span><span>30°C</span></div>
                        </div>
                        <div className="border border-orange-400/50 rounded-xl p-3">
                          <div className="flex items-center gap-2 mb-2"><Video size={16} className="text-orange"/><div><div className="text-sm font-semibold">Câmera Entrada</div><div className="text-[10px] text-slate-400">Ao vivo</div></div></div>
                          <div className="relative h-14 rounded-lg bg-gradient-to-br from-slate-700 to-slate-900 flex items-end justify-between p-1">
                            <div className="text-[9px] text-red-400 flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse"/>LIVE</div>
                          </div>
                        </div>
                        <div className="border border-orange-400/50 rounded-xl p-3">
                          <div className="flex items-center gap-2 mb-2"><Tv size={16} className="text-orange"/><div><div className="text-sm font-semibold">TV da Sala</div><div className="text-[10px] text-slate-400">Samsung QLED</div></div></div>
                          <div className="flex justify-center"><div className="w-12 h-12 rounded-full bg-orange-500 flex items-center justify-center"><Power size={16}/></div></div>
                          <div className="text-center text-[10px] text-orange font-bold mt-1">LIGADA</div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
            {sending && <div className="flex gap-2"><div className="w-8 h-8 rounded-full border-2 border-cyan bg-[#0F1729] flex items-center justify-center"><Bot size={13} className="text-cyan"/></div><div className="bubble-ai px-3 py-2 text-sm text-slate-400">…</div></div>}
          </div>

          <div className="p-4 border-t border-cyan-500/15 flex items-center gap-2">
            <button className="w-10 h-10 rounded-full border border-cyan-500/25 flex items-center justify-center text-slate-400 hover:text-cyan"><Smile size={16}/></button>
            <button className="w-10 h-10 rounded-full border border-cyan-500/25 flex items-center justify-center text-slate-400 hover:text-cyan"><Paperclip size={16}/></button>
            <input value={input} onChange={(e)=>setInput(e.target.value)} onKeyDown={(e)=>e.key==='Enter' && send()} placeholder={t.typeMessage} data-testid="chat-input" className="flex-1 bg-[#0F1729] border border-cyan-500/25 rounded-full px-4 py-2.5 text-sm focus:outline-none focus:border-cyan"/>
            <button onClick={send} disabled={sending} data-testid="chat-send-btn" className="w-11 h-11 rounded-full bg-cyan text-slate-900 flex items-center justify-center hover:bg-cyan-400 disabled:opacity-60" style={{boxShadow:"0 0 18px rgba(0,212,255,0.5)"}}>
              <Send size={16}/>
            </button>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
