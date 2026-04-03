"use client";

import { SignalUpdate } from "@/hooks/useSignalWebSocket";
import { formatCurrency, cn } from "@/lib/utils";
import { motion, AnimatePresence } from "framer-motion";
import { ShieldAlert, Target, Activity, ChevronRight } from "lucide-react";

interface TradeExecutionPanelProps {
  activeTrades: SignalUpdate[];
}

export function TradeExecutionPanel({ activeTrades }: TradeExecutionPanelProps) {
  return (
    <div className="panel rounded-2xl p-4 border border-zinc-800">
      
      <div className="flex items-center justify-between mb-4 border-b border-zinc-800 pb-3">
        <h3 className="text-xs font-black uppercase tracking-widest text-zinc-300">Active Positions</h3>
        <div className="px-2 py-0.5 rounded bg-zinc-800 text-[10px] font-mono text-zinc-400">
           {activeTrades.length}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        <AnimatePresence mode="popLayout">
          {activeTrades.length > 0 ? (
            activeTrades.map((trade) => (
              <ActiveTradeCard key={trade.symbol} trade={trade} />
            ))
          ) : (
            <div className="col-span-full py-12 flex flex-col items-center justify-center text-center space-y-2 border border-dashed border-zinc-800 rounded-xl bg-zinc-900/50">
               <Activity className="w-5 h-5 text-zinc-600 animate-pulse" />
               <p className="text-[10px] font-black text-zinc-500 uppercase tracking-widest">Awaiting Alpha Entry</p>
            </div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

function ActiveTradeCard({ trade }: { trade: SignalUpdate }) {
  const isProfit = (trade.pnlPct || 0) >= 0;
  
  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95 }}
      className="p-4 rounded-xl card hover:border-zinc-700 transition-colors"
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="text-sm font-bold text-white">{trade.symbol}</div>
          <div className={cn(
            "px-2 py-0.5 rounded text-[9px] font-black uppercase tracking-widest",
            trade.signal === "BUY" ? "bg-emerald-500/10 text-emerald-500" : "bg-rose-500/10 text-rose-500"
          )}>
            {trade.signal === "BUY" ? "LONG" : "SHORT"}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <div className="text-[9px] font-bold text-zinc-600 uppercase tracking-widest mb-1">Entry</div>
          <div className="text-sm font-mono text-zinc-300">{formatCurrency(trade.entryPrice)}</div>
        </div>
        <div>
          <div className="text-[9px] font-bold text-zinc-600 uppercase tracking-widest mb-1">Size</div>
          <div className="text-sm font-mono text-zinc-400">{(trade.positionSize || 0).toFixed(2)}</div>
        </div>
      </div>

      <div className="space-y-2 mb-4 bg-zinc-950 p-3 rounded-lg border border-zinc-800">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-3 h-3 text-rose-500/80" />
            <span className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest">Stop</span>
          </div>
          <span className="text-xs font-mono text-rose-500">{formatCurrency(trade.stopLoss)}</span>
        </div>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Target className="w-3 h-3 text-emerald-500/80" />
            <span className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest">Target</span>
          </div>
          <span className="text-xs font-mono text-emerald-500">{formatCurrency(trade.takeProfit2)}</span>
        </div>
      </div>

      <div className="pt-3 flex items-center justify-between border-t border-zinc-800">
        <div className={cn(
          "text-xl font-bold tabular-nums",
          isProfit ? "text-emerald-500" : "text-rose-500"
        )}>
          {isProfit ? "+" : ""}{trade.pnlPct}%
        </div>
        <button className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 transition-colors">
          <span className="text-[10px] font-bold text-zinc-300 uppercase">Manage</span>
          <ChevronRight className="w-3 h-3 text-zinc-500" />
        </button>
      </div>
    </motion.div>
  );
}
