import React, { useState } from "react";
import { useApp, api } from "@/contexts/AppContext";
import AppShell from "@/components/AppShell";
import { Trophy, Cog, Send, User, Info, TrendingDown, Cpu, ArrowRight, Award, ThumbsUp, ThumbsDown } from "lucide-react";

const MODELS = [
  { key: "claude", name: "Claude Sonnet 4.6", cost: 0.003, letter: "A", tone: "#c8f" },
  { key: "openai", name: "GPT-5.4 Turbo", cost: 0.005, letter: "G", tone: "#10a37f" },
  { key: "gemini", name: "Gemini 3 Flash", cost: 0.002, letter: "G", tone: "#4a90e2" },
];

export default function ConsensusPage() {
  const { t } = useApp();
  const [q, setQ] = useState("Explain the impact of quantum computing on cybersecurity and encryption algorithms.");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [feedback, setFeedback] = useState(null); // 'positive' | 'negative' | 'neutral'
  const [feedbackSent, setFeedbackSent] = useState(false);

  const ask = async () => {
    if (!q.trim()) return;
    setLoading(true); setFeedback(null); setFeedbackSent(false);
    try {
      const { data } = await api.post("/consensus/query", { question: q });
      setResult(data);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  const sendFeedback = async (fb) => {
    if (!result?.log_id || feedbackSent) return;
    setFeedback(fb);
    setFeedbackSent(true);
    try {
      await api.post("/learning/feedback", { log_id: result.log_id, feedback: fb, comment: "" });
    } catch (e) { console.error(e); setFeedbackSent(false); }
  };

  const winner = result?.winner;
  const ranked = result?.ranked || [];
  const responses = result?.results || MODELS.map((m, i) => ({ key: m.key, display: m.name, response: "—", confidence: [88,92,90][i], scores: {}, cost: m.cost, latency: 0, icon: m.letter }));

  const conf = (v) => v >= 90 ? "#00E676" : v >= 75 ? "#FFD93D" : v >= 50 ? "#FF8C42" : "#FF4757";

  return (
    <AppShell>
      <div className="grid-bg p-6" data-testid="consensus-page">
        <div className="flex items-start justify-between mb-6 flex-wrap gap-4">
          <div>
            <h1 className="font-brand text-3xl font-bold leading-tight">Hub3 Multi-AI<br/><span className="text-cyan">{t.consensusTitle}</span></h1>
            <p className="text-sm text-slate-400 mt-2">{t.consensusSubtitle}</p>
          </div>
          <div className="hud-card px-4 py-3 flex items-center gap-3 border-green-500/40 relative">
            <div className="hud-bl"/><div className="hud-br"/>
            <Trophy className="text-orange" size={22}/>
            <div>
              <div className="font-bold text-green-400 text-sm">{t.bestAnswer}</div>
              <div className="text-[11px] text-slate-400">{t.selectedVia}</div>
            </div>
            <div className="pl-4 border-l border-green-500/30">
              <div className="text-2xl font-black text-green-400">{winner?.confidence ?? 95}%</div>
              <div className="text-[9px] label-mini">CONFIDENCE</div>
            </div>
            <ArrowRight className="text-cyan" size={18}/>
            <div className="text-xs text-slate-400 max-w-[130px]">{t.answerReturned}</div>
          </div>
        </div>

        <div className="grid grid-cols-12 gap-4">
          {/* Left flow labels */}
          <div className="col-span-2 space-y-6 pt-4">
            {[
              { icon: "💬", num: "1", title: t.parallelCalls, desc: t.eachIndependent },
              { icon: "🧠", num: "2", title: t.aiProcessing, desc: t.eachIndependent },
              { icon: "⚖", num: "3", title: t.consensusVoting, desc: t.votingDesc },
            ].map((s, i) => (
              <div key={i} className="flex items-start gap-2">
                <div className="w-8 h-8 rounded-full bg-cyan-500/10 border border-cyan-500/40 text-cyan flex items-center justify-center text-sm font-bold">{s.num}</div>
                <div>
                  <div className="label-mini text-cyan">{s.title}</div>
                  <div className="text-[11px] text-slate-400">{s.desc}</div>
                </div>
              </div>
            ))}
          </div>

          {/* Center: Model cards + engine */}
          <div className="col-span-7">
            <div className="grid grid-cols-3 gap-3">
              {responses.map((r, i) => (
                <div key={r.key} className="hud-card p-4 relative" data-testid={`model-card-${r.key}`}>
                  <div className="hud-bl"/><div className="hud-br"/>
                  <div className="text-center text-cyan text-xs font-bold mb-1">{i+1}</div>
                  <div className="mx-auto w-12 h-12 rounded-xl bg-white text-slate-900 flex items-center justify-center font-brand font-bold text-lg mb-2">{r.icon || MODELS[i]?.letter}</div>
                  <div className="text-center font-semibold text-sm">{r.display}</div>
                  <div className="text-center text-[10px] text-slate-500 mt-0.5">${MODELS[i]?.cost} / 1K tokens</div>
                  <div className="mt-3 rounded-lg border border-cyan-500/25 p-2">
                    <div className="label-mini text-center mb-1">RESPONSE {i+1}</div>
                    <div className="text-[10px] text-slate-400 line-clamp-3 h-10 overflow-hidden">{r.response?.slice(0, 90) || "—"}</div>
                    <div className="mt-1 text-center">
                      <span className="inline-block px-2 py-0.5 rounded-full text-[10px] font-bold" style={{background: `${conf(r.confidence)}22`, color: conf(r.confidence)}}>{r.confidence}% CONFIDENCE</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Consensus engine visual */}
            <div className="relative mt-8 flex items-center justify-center">
              <div className="relative w-40 h-40 rounded-full bg-orange-500/10 border-2 border-orange-400 flex items-center justify-center" style={{boxShadow: "0 0 40px rgba(255,140,66,0.4), inset 0 0 30px rgba(255,140,66,0.2)"}}>
                <div className="pulse-ring"/>
                <Cog size={56} className="text-orange animate-spin" style={{animationDuration: "12s"}}/>
                <div className="absolute -bottom-2 bg-[#0A0E27] px-2 text-[10px] font-bold text-orange tracking-widest">CONSENSUS<br/>ENGINE</div>
              </div>
            </div>

            {/* Voting mechanism + Scores */}
            <div className="grid grid-cols-2 gap-4 mt-8">
              <div className="hud-card p-4 relative"><div className="hud-bl"/><div className="hud-br"/>
                <div className="label-mini text-orange mb-2">{t.votingMechanism}</div>
                {[t.relevance, t.accuracy, t.completeness, t.clarity, t.recency].map((v) => (
                  <div key={v} className="flex items-center gap-2 text-xs py-1 text-slate-300"><span className="w-1.5 h-1.5 rounded-full bg-cyan"/> {v}</div>
                ))}
              </div>
              <div className="hud-card p-4 relative"><div className="hud-bl"/><div className="hud-br"/>
                <div className="label-mini text-orange mb-2">{t.aiResponseScores}</div>
                {ranked.length === 0 ? <div className="text-xs text-slate-500">Ask a question to see live scores.</div> : ranked.map((r, i) => (
                  <div key={r.key} className={`flex items-center gap-2 px-2 py-1 rounded ${i===0?'bg-green-500/10 border border-green-500/30':''}`}>
                    <div className="w-5 text-[11px] text-slate-400">{i+1}</div>
                    <div className="flex-1 text-sm">{r.display}</div>
                    <div className="text-sm font-bold" style={{color: conf(r.confidence)}}>{r.confidence}%</div>
                  </div>
                ))}
                {winner && (
                  <div className="mt-2 flex items-center justify-between border border-green-500/40 bg-green-500/10 rounded-lg p-2">
                    <div className="flex items-center gap-2"><Award className="text-green-400" size={16}/><span className="text-sm font-bold text-green-400">{t.winner}: {winner.display}</span></div>
                    <div className="text-lg font-black text-green-400">{winner.confidence}%</div>
                  </div>
                )}
                {result?.log_id && (
                  <div className="mt-2 flex items-center justify-between border border-cyan-500/25 rounded-lg p-2">
                    <div className="text-xs text-slate-400">{t.helpful || 'Was this helpful?'}</div>
                    <div className="flex gap-1.5">
                      <button data-testid="feedback-positive" disabled={feedbackSent} onClick={() => sendFeedback('positive')} className={`w-8 h-8 rounded-full border flex items-center justify-center transition ${feedback==='positive'?'bg-green-500/20 border-green-400 text-green-400':'border-cyan-500/25 text-slate-400 hover:text-green-400 hover:border-green-500/40'} disabled:opacity-70`}>
                        <ThumbsUp size={13}/>
                      </button>
                      <button data-testid="feedback-neutral" disabled={feedbackSent} onClick={() => sendFeedback('neutral')} className={`w-8 h-8 rounded-full border flex items-center justify-center transition ${feedback==='neutral'?'bg-cyan-500/20 border-cyan text-cyan':'border-cyan-500/25 text-slate-400 hover:text-cyan hover:border-cyan-500/60'} disabled:opacity-70 text-[10px] font-bold`}>–</button>
                      <button data-testid="feedback-negative" disabled={feedbackSent} onClick={() => sendFeedback('negative')} className={`w-8 h-8 rounded-full border flex items-center justify-center transition ${feedback==='negative'?'bg-red-500/20 border-red-400 text-red-400':'border-cyan-500/25 text-slate-400 hover:text-red-400 hover:border-red-500/40'} disabled:opacity-70`}>
                        <ThumbsDown size={13}/>
                      </button>
                    </div>
                  </div>
                )}
                {feedbackSent && <div className="text-[10px] text-green-400 text-center mt-1">{t.thanks || 'Thanks for your feedback!'}</div>}
              </div>
            </div>

            {/* User question box */}
            <div className="hud-card p-4 mt-6 relative"><div className="hud-bl"/><div className="hud-br"/>
              <div className="flex items-center gap-2 mb-2"><User className="text-cyan" size={16}/><span className="label-mini text-cyan">{t.userQuestion}</span></div>
              <div className="flex gap-2">
                <input value={q} onChange={(e) => setQ(e.target.value)} data-testid="consensus-input" placeholder={t.askAnything} className="flex-1 bg-[#0A0E27] border border-cyan-500/25 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:border-cyan"/>
                <button onClick={ask} disabled={loading} data-testid="consensus-ask-btn" className="btn-primary flex items-center gap-2 disabled:opacity-60">{loading ? t.asking : t.ask} <Send size={14}/></button>
              </div>
            </div>
          </div>

          {/* Right column */}
          <div className="col-span-3 space-y-4">
            <div className="hud-card p-4 relative"><div className="hud-bl"/><div className="hud-br"/>
              <div className="label-mini text-cyan mb-1 flex items-center gap-1"><TrendingDown size={12}/> {t.costOptimization}</div>
              <div className="label-mini mt-2">{t.totalCost}</div>
              <div className="text-4xl font-black text-cyan">${(result?.metrics?.total_cost ?? 0.020).toFixed(3)}</div>
              <div className="text-green-400 text-sm font-semibold">~70% {t.cheaper}</div>
              <div className="text-[10px] text-slate-500">{t.vsSingle}</div>
            </div>
            <div className="hud-card p-4 relative"><div className="hud-bl"/><div className="hud-br"/>
              <div className="label-mini text-cyan mb-2">{t.smartRouting}</div>
              {[t.cheapestFirst, t.earlyExit, t.tokenOptimized, t.redundantAvoided].map(v => (
                <div key={v} className="flex items-center gap-2 text-xs py-1 text-slate-300"><span className="text-green-400">✓</span>{v}</div>
              ))}
            </div>
            <div className="hud-card p-4 relative"><div className="hud-bl"/><div className="hud-br"/>
              <div className="label-mini text-cyan mb-2 flex items-center gap-1"><Cpu size={12}/> {t.systemMetrics}</div>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between"><span className="text-slate-400">{t.totalTime}</span><span className="font-bold">{result?.metrics?.total_time ?? 2.48}s</span></div>
                <div className="flex justify-between"><span className="text-slate-400">{t.modelsResponded}</span><span className="font-bold">{result?.metrics?.models_responded ?? 3}/{result?.metrics?.models_total ?? 3}</span></div>
                <div className="flex justify-between"><span className="text-slate-400">{t.consensusConfidence}</span><span className="font-bold text-green-400">{result?.metrics?.consensus_confidence ?? 95}%</span></div>
                <div className="flex justify-between"><span className="text-slate-400">{t.agreementLevel}</span><span className="font-bold text-green-400">{result?.metrics?.agreement_level ?? 'High'}</span></div>
              </div>
            </div>
            <div className="hud-card p-4 relative"><div className="hud-bl"/><div className="hud-br"/>
              <div className="label-mini mb-2 flex items-center gap-1"><Info size={12}/> {t.confidenceGuide}</div>
              {[
                { c: "#00E676", r: "90%+", l: t.veryHigh },
                { c: "#FFD93D", r: "75% – 89%", l: t.high },
                { c: "#FF8C42", r: "50% – 74%", l: t.medium },
                { c: "#FF4757", r: "< 50%", l: t.low },
              ].map(x => (
                <div key={x.r} className="flex items-center gap-2 text-xs py-1"><span className="w-2 h-2 rounded-full" style={{background:x.c}}/> <span className="w-16 font-semibold text-slate-300">{x.r}</span> <span className="text-slate-400">{x.l}</span></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
