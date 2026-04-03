"use client";

import { SignalUpdate } from "@/hooks/useSignalWebSocket";
import { formatCurrency, cn } from "@/lib/utils";
import { motion, AnimatePresence } from "framer-motion";
import { Copy, Target, Activity, CheckCircle2, ShieldAlert, Link } from "lucide-react";
import { useState } from "react";

interface SignalTableProps {
  signals: SignalUpdate[];
}

export function SignalTable({ signals }: SignalTableProps) {
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
        <thead className="bg-[#0f0f13]">
          <tr className="border-b border-zinc-900">
            <th className="px-6 py-4 text-[9px] font-black tracking-[0.2em] text-zinc-500 uppercase">Asset</th>
            <th className="px-4 py-4 text-[9px] font-black tracking-[0.2em] text-zinc-500 uppercase text-center">Sync</th>
            <th className="px-4 py-4 text-[9px] font-black tracking-[0.2em] text-zinc-500 uppercase text-center">Flow</th>
            <th className="px-4 py-4 text-[9px] font-black tracking-[0.2em] text-zinc-500 uppercase text-center">Magnet</th>
            <th className="px-4 py-4 text-[9px] font-black tracking-[0.2em] text-zinc-500 uppercase text-center">Entry</th>
            <th className="px-4 py-4 text-[9px] font-black tracking-[0.2em] text-zinc-500 uppercase text-center">Stop</th>
            <th className="px-4 py-4 text-[9px] font-black tracking-[0.2em] text-zinc-500 uppercase text-center">Score</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-zinc-900/50">
          {signals.map((signal) => {
            const distance = signal.currentPrice && signal.entryPrice 
              ? ((Math.abs(signal.currentPrice - signal.entryPrice) / signal.entryPrice) * 100).toFixed(2)
              : null;
            
            const isStrong = signal.score >= 85;

            return (
              <tr 
                key={signal.symbol}
                className="hover:bg-zinc-900/30 transition-colors"
              >
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded border border-zinc-800 bg-zinc-900 flex items-center justify-center font-bold text-xs text-zinc-400">
                        {signal.symbol.slice(0, 3)}
                      </div>
                      <div className="flex flex-col">
                        <span className="font-bold text-white text-sm">{signal.symbol}</span>
                        <div className={cn(
                          "text-[8px] font-bold uppercase tracking-widest flex items-center gap-1",
                          signal.confidence.includes("BUY") ? "text-emerald-500" : 
                          signal.confidence.includes("SELL") ? "text-rose-500" : 
                          "text-zinc-500"
                        )}>
                          {signal.is_final ? <CheckCircle2 className="w-2.5 h-2.5" /> : <Activity className="w-2.5 h-2.5" />}
                          {signal.confidence}
                        </div>
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

                  <td className="px-4 py-4">
                     <div className="flex justify-center">
                        <span className={cn(
                          "text-xs font-mono",
                          signal.obi > 0 ? "text-emerald-500" : "text-rose-500"
                        )}>
                          {(signal.obi * 100).toFixed(0)}%
                        </span>
                     </div>
                  </td>

                  <td className="px-4 py-4 text-center">
                    {signal.liq_magnet_price > 0 ? (
                      <div className="flex flex-col items-center gap-0.5 opacity-80 hover:opacity-100 transition-opacity cursor-pointer">
                         <div className="flex items-center gap-1.5">
                           <Target className="w-3 h-3 text-cyan-500" />
                           <span className="text-xs font-mono text-zinc-300">{formatCurrency(signal.liq_magnet_price)}</span>
                         </div>
                         <span className="text-[8px] font-black text-cyan-600 uppercase tracking-widest">{formatCurrency(signal.liq_vol / 1000)}k</span>
                      </div>
                    ) : (
                      <span className="text-[10px] text-zinc-700">-</span>
                    )}
                  </td>

                  <td className="px-4 py-4 text-center">
                    <div className="flex items-center justify-center gap-2 group">
                      <span className="text-sm font-mono text-white">{formatCurrency(signal.entryPrice)}</span>
                      <button onClick={() => copyToClipboard(signal.entryPrice, "Entry")} className="opacity-0 group-hover:opacity-100 p-1 hover:bg-zinc-800 rounded">
                        <Copy className="w-3 h-3 text-zinc-500" />
                      </button>
                    </div>
                    {distance && <div className="text-[9px] text-zinc-600 mt-0.5">{distance}% away</div>}
                  </td>

                  <td className="px-4 py-4 text-center">
                    <div className="flex items-center justify-center gap-2 group">
                      <span className="text-sm font-mono text-rose-500">{formatCurrency(signal.stopLoss)}</span>
                      <button onClick={() => copyToClipboard(signal.stopLoss, "SL")} className="opacity-0 group-hover:opacity-100 p-1 hover:bg-zinc-800 rounded">
                        <Copy className="w-3 h-3 text-zinc-500" />
                      </button>
                    </div>
                  </td>

                  <td className="px-4 py-4 text-center">
                    <div className="flex flex-col items-center">
                      <span className={cn(
                        "text-sm font-black tabular-nums",
                        isStrong ? "text-emerald-500" : "text-white"
                      )}>{signal.score}</span>
                      <span className="text-[8px] text-zinc-600 uppercase">{signal.riskReward}</span>
                    </div>
                  </td>
                </tr>
              );
            })}
        </tbody>
      </table>
    </div>
  );
}
