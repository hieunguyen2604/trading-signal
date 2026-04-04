"use client";

import { SignalUpdate } from "@/hooks/useSignalWebSocket";
import { formatCurrency, cn } from "@/lib/utils";
import { motion, AnimatePresence } from "framer-motion";
import { Copy, Target, Activity, CheckCircle2, ShieldAlert, Link, TrendingUp, TrendingDown, Minus, Sparkles } from "lucide-react";

import { useState } from "react";

interface SignalTableProps {
  signals: SignalUpdate[];
  isRecalculating?: boolean;
}

export function SignalTable({ signals, isRecalculating }: SignalTableProps) {
  const [copiedValue, setCopiedValue] = useState<string | null>(null);

  const copyToClipboard = (value: string | number, label: string) => {
    navigator.clipboard.writeText(value.toString());
    setCopiedValue(`${label} Copied`);
    setTimeout(() => setCopiedValue(null), 2000);
  };

  return (
    <div className="w-full overflow-x-auto custom-scrollbar pb-2">
      <AnimatePresence>
        {copiedValue && (
          <motion.div 
            initial={{ opacity: 0, y: -20, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            className="absolute top-8 left-1/2 -translate-x-1/2 z-50 px-4 py-2 bg-zinc-800 text-white text-[10px] font-black uppercase tracking-[0.2em] rounded border border-zinc-700"
          >
            {copiedValue}
          </motion.div>
        )}
      </AnimatePresence>

      <table className="w-full text-left border-collapse min-w-[800px]">
        <thead className="bg-slate-100/80">
          <tr className="border-b border-slate-200">
            <th className="px-6 py-4 text-[9px] font-black tracking-[0.2em] text-slate-500 uppercase italic">Asset Identity</th>
            <th className="px-4 py-4 text-[9px] font-black tracking-[0.2em] text-slate-500 uppercase text-center">Market Sync</th>
            <th className="px-4 py-4 text-[9px] font-black tracking-[0.2em] text-slate-500 uppercase text-center">Sentiment</th>
            <th className="px-4 py-4 text-[9px] font-black tracking-[0.2em] text-slate-500 uppercase text-center">Trend Analysis (MTF)</th>
            <th className="px-4 py-4 text-[9px] font-black tracking-[0.2em] text-slate-500 uppercase text-center">Magnet</th>
            <th className="px-4 py-4 text-[9px] font-black tracking-[0.2em] text-slate-500 uppercase text-center">Entry Price</th>
            <th className="px-4 py-4 text-[9px] font-black tracking-[0.2em] text-slate-500 uppercase text-center">Safety SL</th>
            <th className="px-4 py-4 text-[9px] font-black tracking-[0.2em] text-slate-500 uppercase text-center">Alpha Tier</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 relative min-h-[400px]">
          {isRecalculating ? (
            Array.from({ length: 5 }).map((_, i) => (
              <tr key={`loader-${i}`} className="animate-pulse">
                <td colSpan={8} className="px-6 py-6 border-b border-slate-100">
                  <div className="flex items-center gap-4">
                    <div className="w-8 h-8 bg-slate-200 rounded-lg shrink-0" />
                    <div className="flex-1 space-y-2">
                      <div className="h-3 bg-slate-200 rounded-full w-24" />
                      <div className="h-2 bg-slate-100 rounded-full w-16" />
                    </div>
                    <div className="h-3 bg-slate-200 rounded-full w-32 hidden md:block" />
                    <div className="h-3 bg-slate-200 rounded-full w-32" />
                  </div>
                </td>
              </tr>
            ))
          ) : signals.length > 0 ? (
            signals.map((signal) => {
              const distance = signal.currentPrice && signal.entryPrice 
                ? ((Math.abs(signal.currentPrice - signal.entryPrice) / signal.entryPrice) * 100).toFixed(2)
                : null;
              
              const isStrong = signal.score >= 85;

              return (
                <tr 
                  key={signal.symbol}
                  className="hover:bg-slate-100/50 transition-colors"
                >
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded border border-slate-200 bg-white flex items-center justify-center font-bold text-xs text-slate-600 shadow-sm">
                          {signal.symbol.slice(0, 3)}
                        </div>
                        <div className="flex flex-col">
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-slate-900 text-sm">{signal.symbol}</span>
                          </div>
                          <div className={cn(
                            "text-[8px] font-bold uppercase tracking-widest flex items-center gap-1",
                            signal.confidence.includes("BUY") ? "text-emerald-500" : 
                            signal.confidence.includes("SELL") ? "text-rose-500" : 
                            "text-zinc-500"
                          )}>
                            {signal.is_final ? <CheckCircle2 className="w-2.5 h-2.5" /> : <Activity className="w-2.5 h-2.5" />}
                            {signal.confidence}
                          </div>

                          {signal.ai_insight && (
                            <div className="mt-1 max-w-[200px]">
                              <div className="flex items-center gap-1.5 text-[7px] text-zinc-400 font-medium leading-tight">
                                <Sparkles className="w-2 h-2 text-amber-400 shrink-0" />
                                <span className="italic">{signal.ai_insight}</span>
                              </div>
                            </div>
                          )}
                        </div>


                      </div>
                    </td>

                    <td className="px-4 py-4 text-center">
                      <div className="flex justify-center">
                        {signal.symbol === "BTCUSDT" ? (
                          <span className="text-[8px] text-zinc-600">ANCHOR</span>
                        ) : signal.market_sync ? (
                          <Link className="w-4 h-4 text-emerald-500" />
                        ) : (
                          <ShieldAlert className="w-4 h-4 text-zinc-600" />
                        )}
                      </div>
                    </td>

                    <td className="px-4 py-4 text-center">
                      <div className="flex justify-center">
                        <div className={cn(
                          "w-4 h-4 rounded-full flex items-center justify-center",
                          signal.sentiment_alignment === "BULLISH" ? "text-emerald-500" :
                          signal.sentiment_alignment === "BEARISH" ? "text-rose-500" :
                          "text-zinc-500"
                        )}>
                          {signal.sentiment_alignment === "BULLISH" ? <TrendingUp className="w-3 h-3" /> :
                           signal.sentiment_alignment === "BEARISH" ? <TrendingDown className="w-3 h-3" /> :
                           <Minus className="w-3 h-3" />}
                        </div>
                      </div>
                    </td>

                    <td className="px-4 py-4">
                       <div className="flex justify-center items-center gap-3">
                          <div className={cn(
                            "flex flex-col items-center gap-0.5",
                            signal.trend_1st === "UP" ? "text-emerald-500" : signal.trend_1st === "DOWN" ? "text-rose-500" : "text-zinc-600"
                          )}>
                            <span className="text-[7px] font-black">4H</span>
                            {signal.trend_1st === "UP" ? <TrendingUp className="w-3 h-3" /> : signal.trend_1st === "DOWN" ? <TrendingDown className="w-3 h-3" /> : <Minus className="w-3 h-3" />}
                          </div>
                          <div className="w-[1px] h-4 bg-slate-200" />
                          <div className={cn(
                            "flex flex-col items-center gap-0.5",
                            signal.trend_2nd === "UP" ? "text-emerald-500" : signal.trend_2nd === "DOWN" ? "text-rose-500" : "text-zinc-600"
                          )}>
                            <span className="text-[7px] font-black">1D</span>
                            {signal.trend_2nd === "UP" ? <TrendingUp className="w-3 h-3" /> : signal.trend_2nd === "DOWN" ? <TrendingDown className="w-3 h-3" /> : <Minus className="w-3 h-3" />}
                          </div>
                       </div>
                    </td>

                    <td className="px-4 py-4 text-center">
                      {signal.liq_magnet_price > 0 ? (
                        <div className="flex flex-col items-center gap-0.5 opacity-80 hover:opacity-100 transition-opacity cursor-pointer">
                           <div className="flex items-center gap-1.5">
                             <Target className="w-3 h-3 text-cyan-600" />
                             <span className="text-xs font-mono text-slate-700 font-bold">{formatCurrency(signal.liq_magnet_price)}</span>
                           </div>
                           <span className="text-[8px] font-black text-cyan-700 uppercase tracking-widest">{formatCurrency(signal.liq_vol / 1000)}k</span>
                        </div>
                      ) : (
                        <span className="text-[10px] text-slate-300">-</span>
                      )}
                    </td>
   
                    <td className="px-4 py-4 text-center">
                      <div className="flex items-center justify-center gap-2 group">
                        <span className="text-sm font-mono text-slate-900 font-bold">{formatCurrency(signal.entryPrice)}</span>
                        <button onClick={() => copyToClipboard(signal.entryPrice, "Entry")} className="opacity-0 group-hover:opacity-100 p-1 hover:bg-slate-200 rounded">
                          <Copy className="w-3 h-3 text-slate-400" />
                        </button>
                      </div>
                      {distance && <div className="text-[9px] text-slate-400 mt-0.5 font-bold">{distance}% away</div>}
                    </td>
   
                    <td className="px-4 py-4 text-center">
                      <div className="flex items-center justify-center gap-2 group">
                        <span className="text-sm font-mono text-rose-600 font-bold">{formatCurrency(signal.stopLoss)}</span>
                        <button onClick={() => copyToClipboard(signal.stopLoss, "SL")} className="opacity-0 group-hover:opacity-100 p-1 hover:bg-slate-200 rounded">
                          <Copy className="w-3 h-3 text-slate-400" />
                        </button>
                      </div>
                    </td>
   
                    <td className="px-4 py-4 text-center">
                      <div className="flex flex-col items-center">
                        <span className={cn(
                          "text-sm font-black tabular-nums",
                          isStrong ? "text-emerald-600" : "text-slate-900"
                        )}>{signal.score}</span>
                        <span className="text-[8px] text-slate-400 uppercase font-bold">{signal.riskReward}</span>
                      </div>
                    </td>
                  </tr>
                );
              })
          ) : (
            <tr>
              <td colSpan={8} className="py-12 text-center text-[10px] font-black text-slate-400 uppercase tracking-widest">
                 Awaiting tactical entry patterns...
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
