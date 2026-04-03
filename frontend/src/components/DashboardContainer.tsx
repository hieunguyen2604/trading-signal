"use client";

import { useSignalWebSocket } from "@/hooks/useSignalWebSocket";
import { SignalTable } from "./SignalTable";
import { PriceBoard } from "./PriceBoard";
import { TradeExecutionPanel } from "./TradeExecutionPanel";
import { EdgeStatsMatrix } from "./EdgeStatsMatrix";
import { Zap, Activity, Info, BarChart3, Database } from "lucide-react";
import { cn } from "@/lib/utils";

export default function DashboardContainer() {
  const { signals, activeTrades, stats, isConnected } = useSignalWebSocket("ws://localhost:8000/api/signals/ws/signals");

  return (
    <div className="min-h-screen bg-black text-zinc-400 font-sans selection:bg-emerald-500/30">
      
      {/* Header */}
      <header className="border-b border-zinc-900 bg-black sticky top-0 z-40">
        <div className="max-w-[1600px] mx-auto px-4 md:px-8 py-4 md:py-0 md:h-20 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex items-center justify-between w-full md:w-auto">
            <div className="flex items-center gap-2 md:gap-6">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-emerald-500 flex items-center justify-center text-zinc-950 shrink-0">
                  <Zap className="w-5 h-5 fill-current" />
                </div>
                <span className="uppercase text-[10px] md:text-xs tracking-[0.2em] md:tracking-[0.25em] hidden sm:block">Professional Trade Assistant v7.0</span>
              </div>
              <h1 className="text-xl md:text-3xl font-black tracking-tighter text-white">
                Antigravity <span className="text-emerald-500 italic">Core</span>
              </h1>
            </div>
          </div>
          
          <div className="flex items-center justify-between w-full md:w-auto md:justify-end gap-6">
            <div className="flex flex-row md:flex-col items-center md:items-end w-full justify-between md:justify-end">
              <div className="flex items-center gap-2 text-[8px] md:text-[10px] uppercase tracking-widest font-black text-zinc-500">
                <Activity className="w-3 h-3 hidden md:block" /> {new Date().toLocaleTimeString()}
              </div>
              <div className={cn(
                "flex items-center gap-2 mt-0 md:mt-1 px-3 py-1 rounded-full text-[8px] md:text-[9px] font-black uppercase tracking-widest border",
                isConnected ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-500" : "bg-rose-500/10 border-rose-500/20 text-rose-500"
              )}>
                <div className={cn("w-1.5 h-1.5 rounded-full animate-pulse shrink-0", isConnected ? "bg-emerald-500" : "bg-rose-500")} />
                {isConnected ? "Live Strategy Sync" : "Connection Lost"}
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-[1600px] mx-auto px-4 md:px-8 py-4 md:py-8 space-y-8 md:space-y-12">
        {/* Real-time Tickers */}
        <section className="space-y-4">
          <div className="flex items-center gap-3 text-zinc-500 px-2">
            <BarChart3 className="w-4 h-4" />
            <h2 className="uppercase text-[10px] font-black tracking-[0.25em]">Realtime Fast Price Stream</h2>
          </div>
          <PriceBoard />
        </section>

        {/* Strategy Edge Performance */}
        <section className="space-y-4">
          <div className="flex items-center gap-3 text-zinc-500 px-2">
            <Database className="w-4 h-4" />
            <h2 className="uppercase text-[10px] font-black tracking-[0.25em]">Institutional Strategy Edge</h2>
          </div>
          <EdgeStatsMatrix stats={stats} />
        </section>

        {/* Live Execution (Horizontal) */}
        <section className="space-y-4">
          <div className="flex items-center gap-3 px-2">
            <Zap className="w-4 h-4 text-rose-500" />
            <h2 className="uppercase text-[10px] font-black tracking-[0.25em] text-zinc-500">Live Execution</h2>
          </div>
          <TradeExecutionPanel activeTrades={activeTrades} />
        </section>

        {/* Main Alpha Table */}
        <section className="space-y-6">
          <div className="flex items-center justify-between px-2">
            <div className="flex items-center gap-3">
              <h2 className="text-xl font-black text-white italic tracking-tight">Top 5 Quantitative Alpha</h2>
              <div className="px-2 py-0.5 rounded bg-zinc-800 border border-zinc-700 text-[8px] font-black text-zinc-400 uppercase tracking-widest">Calculated</div>
            </div>
          </div>
          
          <div className="panel rounded-2xl overflow-hidden">
             <SignalTable signals={signals} />
          </div>
          
          <div className="p-6 rounded-xl panel flex items-start gap-4 mt-6 w-full lg:w-2/3">
            <Info className="w-5 h-5 text-zinc-600 mt-1" />
            <div className="space-y-2">
              <h4 className="text-xs font-black text-zinc-300 uppercase tracking-widest italic">Quant Advisory</h4>
              <p className="text-xs leading-relaxed text-zinc-500">
                Signals are generated using **MTF Trend confirmation** and **Order Flow Intelligence**. Always wait for "CONFIRMED" status before tactical entry.
              </p>
            </div>
          </div>
        </section>
      </main>

    </div>
  );
}
