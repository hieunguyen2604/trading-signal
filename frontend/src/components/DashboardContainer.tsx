"use client";

import React, { useState } from "react";
import { useSignalWebSocket } from "@/hooks/useSignalWebSocket";
import { SignalTable } from "./SignalTable";
import { PriceBoard } from "./PriceBoard";
import { TradeExecutionPanel } from "./TradeExecutionPanel";
import { EdgeStatsMatrix } from "./EdgeStatsMatrix";
import { SentimentWidget } from "./SentimentWidget";
import { PerformanceChart } from "./PerformanceChart";
import { PortfolioHub } from "./PortfolioHub";
import { Zap, Activity, Info, BarChart3, Database, Newspaper } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";


export default function DashboardContainer() {
  const { signals, activeTrades, stats, sentiment, portfolio, strategyMode, setStrategyMode, isConnected } = useSignalWebSocket("ws://localhost:8000/api/signals/ws/signals");
  const [isRecalculating, setIsRecalculating] = useState(false);
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);
  }, []);

  const handleToggleMode = async () => {
    setIsRecalculating(true);
    const nextMode = strategyMode === "SCALP" ? "SWING" : "SCALP";
    try {
      await fetch(`http://localhost:8000/api/signals/mode?mode=${nextMode}`, { method: "POST" });
      // The WebSocket will also handle the mode switch and signal clearing
      // but we add a local delay to ensure the UI feels 'refreshed'
      setTimeout(() => setIsRecalculating(false), 800);
    } catch (err) {
      console.error("Failed to toggle mode:", err);
      setIsRecalculating(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans selection:bg-emerald-500/20">
      
      {/* Header */}
      <header className="border-b border-slate-200 bg-white/70 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-[1600px] mx-auto px-4 md:px-8 py-4 md:py-0 md:h-20 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div className="flex items-center gap-6">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-slate-900 flex items-center justify-center text-white shadow-lg shadow-slate-200">
                  <span className="text-xl font-black italic">A</span>
                </div>
                <div className="flex flex-col">
                  <h1 className="text-2xl font-black tracking-tighter text-slate-900 leading-none">
                    AETHER <span className="text-emerald-600 italic">Terminal</span>
                  </h1>
                  <div className="flex items-center gap-2 mt-1">
                    <div className={cn(
                      "w-1 h-1 rounded-full",
                      strategyMode === "SCALP" ? "bg-cyan-500" : "bg-emerald-500"
                    )} />
                    <span className={cn(
                      "text-[8px] font-black uppercase tracking-[0.2em]",
                      strategyMode === "SCALP" ? "text-cyan-500" : "text-emerald-500"
                    )}>{strategyMode} MODE ACTIVE</span>
                  </div>
                </div>
              </div>
            </div>
          
          <div className="flex items-center gap-6">
            <button 
              onClick={handleToggleMode}
              disabled={isRecalculating}
              className={cn(
                "flex items-center gap-3 px-4 py-2 rounded-xl border transition-all group",
                isRecalculating ? "bg-slate-50 border-slate-200 cursor-not-allowed" : "bg-slate-100 border-slate-200 hover:bg-slate-200"
              )}
            >
              <div className="flex flex-col items-end">
                <span className="text-[7px] text-slate-500 font-black uppercase tracking-tighter">
                  {isRecalculating ? "Applying..." : "Switch Strategy"}
                </span>
                <span className="text-[10px] text-slate-900 font-bold">{strategyMode === "SCALP" ? "SWING" : "SCALP"}</span>
              </div>
              <div className="w-10 h-5 rounded-full bg-slate-200 p-1 relative flex items-center">
                {isRecalculating ? (
                  <div className="absolute inset-0 flex items-center justify-center">
                    <Activity className="w-3 h-3 text-slate-400 animate-spin" />
                  </div>
                ) : (
                  <div className={cn(
                    "w-3 h-3 rounded-full transition-all duration-300",
                    strategyMode === "SCALP" ? "translate-x-0 bg-cyan-600" : "translate-x-5 bg-emerald-600"
                  )} />
                )}
              </div>
            </button>

            <div className="flex flex-row md:flex-col items-center md:items-end justify-end group gap-2 md:gap-0">
              <div className="flex items-center gap-2 text-[8px] md:text-[10px] uppercase tracking-widest font-black text-slate-400 group-hover:text-slate-600 transition-colors">
                <Activity className="w-3 h-3 hidden md:block" /> {mounted ? new Date().toLocaleTimeString() : "--:--:--"}
              </div>
              <div className="flex items-center gap-2 mt-0 md:mt-1">
                <div className={cn(
                  "flex items-center gap-2 px-3 py-1 rounded-full text-[8px] md:text-[9px] font-black uppercase tracking-widest border transition-all",
                  isConnected ? "bg-emerald-100 border-emerald-200 text-emerald-700 shadow-sm" : "bg-rose-100 border-rose-200 text-rose-700"
                )}>
                  <div className={cn("w-1.5 h-1.5 rounded-full animate-pulse shrink-0", isConnected ? "bg-emerald-600" : "bg-rose-600")} />
                  {isConnected ? "Engine Synced" : "Offline"}
                </div>
                <div className="flex items-center gap-2 px-3 py-1 rounded-full text-[8px] md:text-[9px] font-black uppercase tracking-widest border border-cyan-200 bg-cyan-50 text-cyan-700">
                  <Zap className="w-2 h-2 text-cyan-600 shrink-0" />
                  Alerts Active
                </div>
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

        {/* Strategy Edge & Performance (Alpha v12.2 Professional Era) */}
        <section className="space-y-4">
          <div className="flex items-center gap-3 text-zinc-500 px-2">
            <Database className="w-4 h-4" />
            <h2 className="uppercase text-[10px] font-black tracking-[0.25em]">Institutional Analytics Hub</h2>
          </div>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
            <EdgeStatsMatrix stats={stats} />
            <PerformanceChart />
          </div>
        </section>

        {/* Market Sentiment (Alpha v8.0) */}
        <section className="space-y-4">
          <div className="flex items-center gap-3 text-zinc-500 px-2">
            <Newspaper className="w-4 h-4" />
            <h2 className="uppercase text-[10px] font-black tracking-[0.25em]">Market Intelligence Layer</h2>
          </div>
          <SentimentWidget sentiment={sentiment} />
        </section>

        {/* Live Execution (Horizontal) */}
        <section className="space-y-4">
          <div className="flex items-center gap-3 mb-8">
            <div className="p-2 bg-rose-500 rounded-lg shadow-lg shadow-rose-200">
              <Zap className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-black text-slate-900 tracking-tight uppercase">Live Execution</h2>
              <div className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Tactical Alpha Stream Active</span>
              </div>
            </div>
          </div>

          {/* Alpha v12.1 Portfolio Exposure Hub */}
          <PortfolioHub portfolio={portfolio} />
          
          <TradeExecutionPanel activeTrades={activeTrades} />
        </section>

        {/* Main Alpha Table */}
        <section className="space-y-6">
          <div className="flex items-center justify-between px-2">
            <div className="flex items-center gap-3">
              <h2 className="text-xl font-black text-slate-900 italic tracking-tight">Top 5 Quantitative Alpha</h2>
              <div className="px-2 py-0.5 rounded bg-slate-200 border border-slate-300 text-[8px] font-black text-slate-600 uppercase tracking-widest">Calculated</div>
            </div>
          </div>
          
          <div className="panel rounded-2xl overflow-hidden relative">
            <AnimatePresence>
              {isRecalculating && (
                <motion.div 
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="absolute inset-0 z-20 bg-white/60 backdrop-blur-sm flex flex-col items-center justify-center gap-4"
                >
                  <div className="flex items-center gap-3">
                    <Activity className="w-6 h-6 text-slate-900 animate-pulse" />
                    <span className="text-sm font-black uppercase tracking-[0.3em] text-slate-900">Tactical Calibration</span>
                  </div>
                  <div className="w-48 h-1 bg-slate-100 rounded-full overflow-hidden">
                    <motion.div 
                      initial={{ x: "-100%" }}
                      animate={{ x: "100%" }}
                      transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                      className="w-full h-full bg-slate-900"
                    />
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
            
             <SignalTable 
            signals={signals} 
            strategyMode={strategyMode} 
            isRecalculating={false} // Handled by local overlay
          />
          </div>

          
          <div className="p-6 rounded-xl panel flex items-start gap-4 mt-6 w-full lg:w-2/3">
            <Info className="w-5 h-5 text-slate-400 mt-1" />
            <div className="space-y-2">
              <h4 className="text-xs font-black text-slate-600 uppercase tracking-widest italic">Quant Advisory</h4>
              <p className="text-xs leading-relaxed text-slate-500">
                Signals are generated using **MTF Trend confirmation (1h/4h/1d)** and **Swing Intelligence**. Always wait for "CONFIRMED" status before tactical entry.
              </p>
            </div>
          </div>
        </section>
      </main>

    </div>
  );
}
