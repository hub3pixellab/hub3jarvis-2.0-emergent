import React, { useEffect, useState } from "react";
import { useApp, api } from "@/contexts/AppContext";
import AppShell from "@/components/AppShell";
import { Search, Bell, Settings, Cloud, Clock, Home, LayoutGrid, Lightbulb, Thermometer, Video, Tv, Lock, Volume2, HeartPulse, Plug, Snowflake, Wind, Calendar, Power, Bluetooth, Sliders, ChevronUp, ChevronDown, VolumeX, ArrowLeftRight, Wifi, Shield, RefreshCw } from "lucide-react";

const SIDE = [
  { key: "dashboard", icon: LayoutGrid, label: "Dashboard", active: true },
  { key: "devices", icon: Lightbulb, label: "Devices" },
  { key: "rooms", icon: Home, label: "Rooms" },
  { key: "automation", icon: RefreshCw, label: "Automation" },
  { key: "scenes", icon: Sliders, label: "Scenes" },
  { key: "energy", icon: Plug, label: "Energy" },
  { key: "alerts", icon: Bell, label: "Alerts" },
  { key: "calendar", icon: Calendar, label: "Calendar" },
  { key: "settings", icon: Settings, label: "Settings" },
];

function DeviceCard({ title, subtitle, online, children, testid }) {
  return (
    <div className="hud-card p-4 relative" data-testid={testid}>
      <div className="hud-bl"/><div className="hud-br"/>
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="font-semibold text-white">{title}</div>
          <div className="text-[11px] text-slate-500">{subtitle}</div>
        </div>
        <div className="text-[10px] flex items-center gap-1 text-green-400"><span className="w-1.5 h-1.5 rounded-full bg-green-400"/> {online ? "Online" : "Offline"}</div>
      </div>
      {children}
    </div>
  );
}

function ColorWheel({ selected, onSelect }) {
  return (
    <div className="relative w-32 h-32 mx-auto rounded-full" style={{background: "conic-gradient(from 0deg, red, yellow, lime, cyan, blue, magenta, red)"}}>
      <div className="absolute inset-2 rounded-full bg-[#0F1729]"/>
      <div className="absolute w-4 h-4 rounded-full border-2 border-white top-1 left-1/2" style={{background: selected}}/>
    </div>
  );
}

export default function SmartHomePage() {
  const { t } = useApp();
  const [state, setState] = useState(null);

  const load = () => api.get("/smart-home/state").then(({data}) => setState(data));
  useEffect(() => { load(); }, []);

  const toggle = async (device_id, state_patch) => {
    const { data } = await api.post("/smart-home/toggle", { device_id, state: state_patch });
    setState((s) => ({ ...s, devices: { ...s.devices, [device_id]: data.state } }));
  };

  if (!state) return <AppShell><div className="p-10 text-slate-400">Loading…</div></AppShell>;
  const d = state.devices;
  const now = new Date();

  return (
    <AppShell>
      <div className="min-h-screen bg-dashboard flex">
        {/* Left */}
        <aside className="w-56 border-r border-cyan-500/15 p-4 shrink-0" data-testid="smart-home-sidebar">
          <div className="flex items-center gap-2 mb-6">
            <div className="w-10 h-10 rounded-full bg-cyan-500/10 border-2 border-cyan-500/50 flex items-center justify-center">
              <div className="w-4 h-4 rounded-full bg-cyan animate-pulse"/>
            </div>
            <div>
              <div className="text-cyan text-lg font-bold leading-none">Hub3</div>
              <div className="font-brand text-white text-xl leading-none">JARVIS</div>
            </div>
          </div>
          <nav className="space-y-1">
            {SIDE.map(s => (
              <button key={s.key} className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition ${s.active?'bg-cyan-500/15 border border-cyan-500/40 text-cyan':'text-slate-400 hover:text-white hover:bg-white/5'}`}>
                <s.icon size={16}/> {s.label}
              </button>
            ))}
          </nav>
          <div className="mt-6 hud-card p-3 relative"><div className="hud-bl"/><div className="hud-br"/>
            <div className="flex items-center gap-2">
              <Wifi size={14} className="text-cyan"/>
              <div>
                <div className="text-sm font-semibold">Hub3 Jarvis</div>
                <div className="text-[10px] text-green-400 flex items-center gap-1"><span className="w-1 h-1 rounded-full bg-green-400"/> {t.online}</div>
              </div>
            </div>
          </div>
          <div className="mt-3 hud-card p-3 relative"><div className="hud-bl"/><div className="hud-br"/>
            <div className="text-xs text-slate-400">System Status</div>
            <div className="text-sm text-cyan">{t.allSystemsOperational}</div>
          </div>
        </aside>

        {/* Main */}
        <div className="flex-1 min-w-0 p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-5">
            <div>
              <div className="text-2xl font-bold">{t.smartHomeTitle}</div>
              <div className="text-sm text-slate-400">{t.smartHomeWelcome}</div>
            </div>
            <div className="flex items-center gap-3">
              <div className="relative">
                <Search size={14} className="absolute left-3 top-3 text-slate-500"/>
                <input placeholder="Search devices…" className="bg-[#0F1729] border border-cyan-500/25 rounded-lg pl-9 pr-3 py-2 text-sm w-64 focus:outline-none focus:border-cyan"/>
              </div>
              <button className="w-9 h-9 rounded-lg border border-cyan-500/25 flex items-center justify-center relative"><Bell size={15}/><span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-red-500 text-[9px] flex items-center justify-center font-bold">3</span></button>
              <button className="w-9 h-9 rounded-lg border border-cyan-500/25 flex items-center justify-center"><Settings size={15}/></button>
              <div className="w-9 h-9 rounded-full bg-gradient-to-br from-cyan-500 to-orange-500"/>
              <div className="text-right">
                <div className="text-sm font-semibold">Admin</div>
                <div className="text-[10px] text-slate-400">Administrator</div>
              </div>
              <div className="text-right border-l border-cyan-500/15 pl-3">
                <div className="text-sm font-mono">{now.toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'})}</div>
                <div className="text-[10px] text-slate-400">{now.toLocaleDateString([], {month:'short',day:'numeric',year:'numeric'})}</div>
              </div>
              <div className="text-right">
                <div className="text-sm font-mono flex items-center gap-1"><Cloud size={12}/> 26°C</div>
                <div className="text-[10px] text-slate-400">Cloudy</div>
              </div>
            </div>
          </div>

          {/* Devices grid 4x2 */}
          <div className="grid grid-cols-4 gap-4">
            {/* Smart Lights */}
            <DeviceCard title={t.smartLights} subtitle={t.livingRoom} online={d.lights.online} testid="device-lights">
              <div className="flex items-start gap-3">
                <ColorWheel selected={d.lights.color}/>
                <div className="flex-1">
                  <div className="label-mini">{t.brightness}</div>
                  <div className="text-3xl font-black">{d.lights.brightness}%</div>
                  <input type="range" min="0" max="100" value={d.lights.brightness} onChange={(e)=>toggle("lights",{brightness:+e.target.value})} className="w-full accent-orange-500 mt-1"/>
                </div>
              </div>
              <div className="flex gap-1.5 justify-center my-2">{["#FF8C42","#FFD93D","#00E676","#00D4FF","#8b5cf6","#ec4899"].map(c=>(<button key={c} onClick={()=>toggle("lights",{color:c})} className={`w-5 h-5 rounded-full ${d.lights.color===c?'ring-2 ring-white':''}`} style={{background:c}}/>))}</div>
              <div className="flex items-center gap-2 mt-2">
                <button onClick={()=>toggle("lights",{on:!d.lights.on})} data-testid="lights-power" className={`w-10 h-10 rounded-lg ${d.lights.on?'bg-orange-500':'bg-slate-700'} flex items-center justify-center transition`}><Power size={15}/></button>
                <button className="flex-1 px-3 py-2 border border-cyan-500/30 rounded-lg text-xs text-cyan">Scene: {d.lights.scene} ▾</button>
                <button className="px-3 py-2 border border-cyan-500/30 rounded-lg text-xs">More ▾</button>
              </div>
            </DeviceCard>

            {/* Thermostat */}
            <DeviceCard title={t.thermostat} subtitle={t.hallway} online={d.thermostat.online} testid="device-thermostat">
              <div className="flex items-center justify-center relative">
                <svg width="140" height="140" viewBox="0 0 140 140">
                  <circle cx="70" cy="70" r="60" stroke="#1a2340" strokeWidth="8" fill="none"/>
                  <circle cx="70" cy="70" r="60" stroke="url(#thermoGrad)" strokeWidth="8" fill="none" strokeDasharray={`${2*Math.PI*60*0.7} ${2*Math.PI*60}`} strokeDashoffset={2*Math.PI*60*0.25} strokeLinecap="round" transform="rotate(-90 70 70)"/>
                  <defs><linearGradient id="thermoGrad" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stopColor="#00D4FF"/><stop offset="100%" stopColor="#FF8C42"/></linearGradient></defs>
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <div className="text-4xl font-black">{d.thermostat.temp}<span className="text-lg text-slate-400">°C</span></div>
                  <div className="text-[10px] text-slate-400">Current: {d.thermostat.temp}°C</div>
                  <div className="text-[10px] text-cyan flex items-center gap-1 mt-0.5"><Snowflake size={10}/> {t.cooling}</div>
                </div>
                <div className="absolute right-0 top-2 flex flex-col gap-1">
                  <button onClick={()=>toggle("thermostat",{temp: +(d.thermostat.temp+0.5).toFixed(1)})} className="w-7 h-7 rounded border border-cyan-500/30 flex items-center justify-center"><ChevronUp size={12}/></button>
                  <button onClick={()=>toggle("thermostat",{temp: +(d.thermostat.temp-0.5).toFixed(1)})} className="w-7 h-7 rounded border border-cyan-500/30 flex items-center justify-center"><ChevronDown size={12}/></button>
                </div>
              </div>
              <div className="flex gap-1 mt-2">
                <button onClick={()=>toggle("thermostat",{on:!d.thermostat.on})} data-testid="thermostat-power" className={`w-10 h-9 rounded-lg ${d.thermostat.on?'bg-orange-500':'bg-slate-700'} flex items-center justify-center`}><Power size={14}/></button>
                {[{i:Snowflake,l:"Mode"},{i:Wind,l:"Fan"},{i:Calendar,l:"Schedule"}].map((b,i)=>(
                  <button key={i} className="flex-1 py-2 border border-cyan-500/25 rounded-lg text-[10px] flex flex-col items-center gap-0.5 text-slate-300"><b.i size={12}/>{b.l}</button>
                ))}
              </div>
            </DeviceCard>

            {/* Security Cameras */}
            <DeviceCard title={t.securityCameras} subtitle={`4 ${t.cameras}`} online={d.cameras.online} testid="device-cameras">
              <div className="grid grid-cols-2 gap-1.5">
                {["Front Door","Driveway","Backyard","Garage"].map((n,i)=>(
                  <div key={n} className="relative h-16 rounded-lg overflow-hidden bg-gradient-to-br from-slate-800 to-slate-900 border border-cyan-500/20">
                    <div className="absolute bottom-1 left-1 text-[9px] font-semibold">{n}</div>
                    <div className="absolute top-1 right-1 w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse"/>
                  </div>
                ))}
              </div>
              <button className="mt-2 w-full py-2 border border-cyan-500/30 rounded-lg text-xs text-cyan flex items-center justify-center gap-1">▦ {t.viewAllCameras}</button>
            </DeviceCard>

            {/* Smart TV */}
            <DeviceCard title={t.smartTV} subtitle={t.livingRoom} online={d.tv.online} testid="device-tv">
              <div className="relative h-24 rounded-lg overflow-hidden bg-gradient-to-br from-orange-900 to-slate-900 border border-cyan-500/20 flex items-center justify-center">
                <div className="w-14 h-14 rounded-full border-2 border-orange-400"/>
                <div className="absolute bottom-1 left-2 text-[10px] font-semibold">{d.tv.input}</div>
                <div className="absolute bottom-1 right-2 text-[10px] text-green-400">{t.playing}</div>
              </div>
              <div className="flex items-center gap-1 mt-2">
                <button onClick={()=>toggle("tv",{on:!d.tv.on})} data-testid="tv-power" className={`w-10 h-9 rounded-lg ${d.tv.on?'bg-orange-500':'bg-slate-700'} flex items-center justify-center`}><Power size={14}/></button>
                <button className="w-9 h-9 rounded-lg border border-cyan-500/25 flex items-center justify-center"><VolumeX size={13}/></button>
                <button className="w-9 h-9 rounded-lg border border-cyan-500/25 flex items-center justify-center"><ArrowLeftRight size={13}/></button>
              </div>
              <div className="grid grid-cols-4 gap-1 mt-2">
                {["HDMI 1","HDMI 2","Netflix","YouTube"].map((s,i)=>(
                  <button key={s} className={`py-1.5 rounded text-[10px] ${i===0?'bg-orange-500/20 border border-orange-400 text-orange':'border border-cyan-500/20 text-slate-400'}`}>{s}</button>
                ))}
              </div>
            </DeviceCard>

            {/* Door Lock */}
            <DeviceCard title={t.doorLock} subtitle={t.mainEntrance} online={d.lock.online} testid="device-lock">
              <button onClick={()=>toggle("lock",{locked:!d.lock.locked})} data-testid="lock-toggle" className="w-32 h-32 mx-auto rounded-full border-2 border-cyan flex flex-col items-center justify-center relative" style={{boxShadow:"0 0 30px rgba(0,212,255,0.3), inset 0 0 20px rgba(0,212,255,0.1)"}}>
                <Lock size={30} className="text-cyan mb-1"/>
                <div className="text-[10px] font-bold text-cyan tracking-widest">{d.lock.locked ? t.locked : "UNLOCKED"}</div>
                <div className="text-[9px] text-slate-400 mt-0.5">{t.tapToUnlock}</div>
              </button>
              <div className="grid grid-cols-3 gap-1 mt-3 text-[10px] text-slate-400">
                {[{i:Clock,l:t.history},{i:'👥',l:t.users},{i:Settings,l:t.settings}].map((b,i)=>(
                  <button key={i} className="py-2 border border-cyan-500/20 rounded-lg flex flex-col items-center gap-0.5">{typeof b.i==='string'?<span>{b.i}</span>:<b.i size={11}/>}{b.l}</button>
                ))}
              </div>
            </DeviceCard>

            {/* Speaker */}
            <DeviceCard title={t.speaker} subtitle={t.livingRoom} online={d.speaker.online} testid="device-speaker">
              <div className="wave-bars w-full justify-center mb-2" style={{height:44}}><span/><span/><span/><span/><span/><span/><span/><span/></div>
              <div className="text-center">
                <div className="text-3xl font-black">{d.speaker.volume}<span className="text-lg text-slate-400">%</span></div>
                <div className="text-[10px] text-slate-400">{t.volume}</div>
              </div>
              <input type="range" min="0" max="100" value={d.speaker.volume} onChange={(e)=>toggle("speaker",{volume:+e.target.value})} className="w-full accent-orange-500 mt-1"/>
              <div className="flex gap-1 mt-2">
                <button onClick={()=>toggle("speaker",{on:!d.speaker.on})} data-testid="speaker-power" className={`w-10 h-9 rounded-lg ${d.speaker.on?'bg-orange-500':'bg-slate-700'} flex items-center justify-center`}><Power size={14}/></button>
                <button className="flex-1 py-2 border border-cyan-500/25 rounded-lg text-[11px] flex items-center justify-center gap-1"><Bluetooth size={11}/> {t.bluetooth}</button>
                <button className="flex-1 py-2 border border-cyan-500/25 rounded-lg text-[11px] flex items-center justify-center gap-1"><Sliders size={11}/> {t.eq}</button>
              </div>
            </DeviceCard>

            {/* Wearable Health */}
            <DeviceCard title={t.wearableHealth} subtitle="Jarvis Watch 3" online={d.wearable.online} testid="device-wearable">
              <div className="grid grid-cols-3 gap-2 text-center">
                <div><div className="halo-icon red mx-auto" style={{width:26,height:26}}><HeartPulse size={12}/></div><div className="text-lg font-bold mt-1">{d.wearable.hr}</div><div className="text-[9px] text-slate-400">BPM</div></div>
                <div><div className="halo-icon mx-auto" style={{width:26,height:26}}>👟</div><div className="text-lg font-bold mt-1">{d.wearable.steps.toLocaleString()}</div><div className="text-[9px] text-slate-400">Steps</div></div>
                <div><div className="halo-icon orange mx-auto" style={{width:26,height:26}}>🌙</div><div className="text-lg font-bold mt-1">{d.wearable.sleep}</div><div className="text-[9px] text-green-400">{t.good}</div></div>
                <div><div className="halo-icon orange mx-auto" style={{width:26,height:26}}>🔥</div><div className="text-lg font-bold mt-1">{d.wearable.calories}</div><div className="text-[9px] text-slate-400">kcal</div></div>
                <div><div className="halo-icon mx-auto" style={{width:26,height:26}}>💧</div><div className="text-lg font-bold mt-1">{d.wearable.spo2}%</div><div className="text-[9px] text-slate-400">SpO2</div></div>
              </div>
              <button className="mt-2 w-full py-2 border border-cyan-500/30 rounded-lg text-xs text-cyan">{t.viewFullReport} →</button>
            </DeviceCard>

            {/* Smart Plugs */}
            <DeviceCard title={t.smartPlugs} subtitle="3 Devices" online={true} testid="device-plugs">
              <div className="space-y-2">
                {d.plugs.list.map((p,i)=>(
                  <div key={p.name} className="flex items-center gap-2">
                    <Plug size={14} className={p.online?'text-cyan':'text-red-400'}/>
                    <div className="flex-1">
                      <div className="text-sm font-semibold">{p.name}</div>
                      <div className="text-[10px] flex items-center gap-1 text-slate-400"><span className={`w-1 h-1 rounded-full ${p.online?'bg-green-400':'bg-red-400'}`}/>{p.online?'Online':'Offline'}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-xs font-bold">{p.w||'--'} W</div>
                      <div className="text-[9px] text-slate-400">{p.kwh||0} kWh</div>
                    </div>
                    <button onClick={()=>{const list=[...d.plugs.list]; list[i]={...list[i],on:!list[i].on}; toggle("plugs",{list});}} className={`w-8 h-8 rounded-lg ${p.on?'bg-orange-500':'bg-slate-700'} flex items-center justify-center`}><Power size={12}/></button>
                  </div>
                ))}
              </div>
              <div className="mt-2 pt-2 border-t border-cyan-500/15 flex justify-between text-xs">
                <span className="text-slate-400">{t.totalConsumption}</span>
                <span className="text-cyan font-bold">⚡ 203 W · 1.00 kWh</span>
              </div>
            </DeviceCard>
          </div>

          {/* Footer bar */}
          <div className="mt-5 hud-card px-5 py-3 flex items-center justify-between relative">
            <div className="hud-bl"/><div className="hud-br"/>
            <div className="flex items-center gap-2 text-sm"><Wifi size={14} className="text-cyan"/>{t.networkConnected}</div>
            <div className="flex items-center gap-2 text-sm"><Shield size={14} className="text-green-400"/>{t.securityActive}</div>
            <div className="flex items-center gap-2 text-sm"><LayoutGrid size={14} className="text-cyan"/>{t.devicesOnline}: {state.devices_online}/{state.devices_total}</div>
            <div className="flex items-center gap-2 text-sm"><RefreshCw size={14} className="text-cyan"/>{t.lastSync}: {now.toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'})}</div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
