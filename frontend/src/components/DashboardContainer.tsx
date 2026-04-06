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
import { SessionPulse } from "./SessionPulse";
import Chatbot from "./Chatbot";
import { Zap, Activity, Info, BarChart3, Database, Newspaper } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";


export default function DashboardContainer() {
  const { signals, activeTrades, stats, sentiment, portfolio, strategyMode, isConnected } = useSignalWebSocket("ws://127.0.0.1:8000/api/signals/ws/signals");
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);
  }, []);


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
                    <div className="w-1 h-1 rounded-full bg-emerald-500" />
                    <span className="text-[8px] font-black uppercase tracking-[0.2em] text-emerald-500">
                      AETHER ENGINE ACTIVE
                    </span>
                  </div>
                </div>
              </div>
            </div>
          
          <div className="flex items-center gap-6">

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

        {/* Strategy Edge & Performance */}
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

        {/* Market Sentiment */}
        <section className="space-y-4">
          <div className="flex items-center gap-3 text-zinc-500 px-2">
            <Newspaper className="w-4 h-4" />
            <h2 className="uppercase text-[10px] font-black tracking-[0.25em]">Market Intelligence Layer</h2>
          </div>
          <div className="grid grid-cols-1 xl:grid-cols-4 gap-8">
            <div className="xl:col-span-3">
              <SentimentWidget sentiment={sentiment} />
            </div>
            <div className="xl:col-span-1">
              <SessionPulse />
            </div>
          </div>
        </section>

        {/* Live Execution */}
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

          {/* Portfolio Exposure Hub */}
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
            
             <SignalTable 
            signals={signals} 
            isRecalculating={false} // Handled by local overlay
          />
          </div>

          
          <div className="p-6 rounded-xl panel flex items-start gap-4 mt-6 w-full lg:w-2/3">
            <Info className="w-5 h-5 text-slate-400 mt-1" />
            <div className="space-y-2">
              <h4 className="text-xs font-black text-slate-600 uppercase tracking-widest italic">Quant Advisory</h4>
              <p className="text-xs leading-relaxed text-slate-500">
                Signals are generated using **MTF Trend confirmation (1h/4h/1d)** and **Tactical Intelligence**. Always wait for "CONFIRMED" status before entry.
              </p>
            </div>
          </div>
        </section>
      </main>

      {/* Floating AI Chatbot */}
      <Chatbot />
    </div>
  );
}
