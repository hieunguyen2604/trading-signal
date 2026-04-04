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
    <div className="panel rounded-2xl p-4 border border-slate-200">
      
      <div className="flex items-center justify-between mb-4 border-b border-slate-100 pb-3">
        <h3 className="text-xs font-black uppercase tracking-widest text-slate-500">Active Positions</h3>
        <div className="px-2 py-0.5 rounded bg-slate-100 text-[10px] font-mono text-slate-600 border border-slate-200 shadow-sm">
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
            <div className="col-span-full py-12 flex flex-col items-center justify-center text-center space-y-2 border border-dashed border-slate-200 rounded-xl bg-slate-50/50">
               <Activity className="w-5 h-5 text-slate-300 animate-pulse" />
               <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Awaiting Alpha Entry</p>
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
      className="p-4 rounded-xl panel hover:border-slate-300 transition-colors border border-slate-100"
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="text-sm font-bold text-slate-900">{trade.symbol}</div>
          <div className={cn(
            "px-2 py-0.5 rounded text-[9px] font-black uppercase tracking-widest",
            trade.signal === "BUY" ? "bg-emerald-100 text-emerald-700" : "bg-rose-100 text-rose-700"
          )}>
            {trade.signal === "BUY" ? "LONG" : "SHORT"}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <div className="text-[9px] font-bold text-slate-400 uppercase tracking-widest mb-1">Entry</div>
          <div className="text-sm font-mono text-slate-700 font-bold">{formatCurrency(trade.entryPrice)}</div>
        </div>
        <div>
          <div className="text-[9px] font-bold text-slate-400 uppercase tracking-widest mb-1">Size</div>
          <div className="text-sm font-mono text-slate-500 font-bold">{(trade.positionSize || 0).toFixed(2)}</div>
        </div>
      </div>

      <div className="space-y-2 mb-4 bg-slate-50 p-3 rounded-lg border border-slate-100">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-3 h-3 text-rose-500" />
            <span className="text-[9px] font-bold text-slate-400 uppercase tracking-widest">Stop</span>
          </div>
          <span className="text-xs font-mono text-rose-600 font-bold">{formatCurrency(trade.stopLoss)}</span>
        </div>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Target className="w-3 h-3 text-emerald-500" />
            <span className="text-[9px] font-bold text-slate-400 uppercase tracking-widest">Target</span>
          </div>
          <span className="text-xs font-mono text-emerald-600 font-bold">
            {formatCurrency(trade.takeProfit2 > 0 ? trade.takeProfit2 : trade.takeProfit1)}
          </span>
        </div>
      </div>

      <div className="pt-3 flex items-center justify-between border-t border-slate-50">
        <div className={cn(
          "text-xl font-bold tabular-nums",
          isProfit ? "text-emerald-600" : "text-rose-600"
        )}>
          {isProfit ? "+" : ""}{trade.pnlPct}%
        </div>
      </div>
    </motion.div>
  );
}
