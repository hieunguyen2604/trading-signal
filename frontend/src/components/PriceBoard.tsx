"use client";

import { usePriceWebSocket, PriceUpdate } from "@/hooks/usePriceWebSocket";
import { formatCurrency, cn } from "@/lib/utils";
import { motion, AnimatePresence } from "framer-motion";
import { Zap, Activity, Flame } from "lucide-react";

export function PriceBoard() {
  const { prices } = usePriceWebSocket("ws://localhost:8000/api/signals/ws/prices");

  const symbols = Object.keys(prices).sort();

  return (
    <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
      <AnimatePresence mode="popLayout">
        {symbols.map((symbol) => (
          <PriceCard key={symbol} data={prices[symbol]} />
        ))}
      </AnimatePresence>
    </div>
  );
}

function PriceCard({ data }: { data: PriceUpdate }) {
  const isUp = data.direction === "up";
  
  // OBI visualization
  const obiWidth = ((data.obi + 1) / 2) * 100;
  const isStrongBuy = data.obi > 0.4;
  const isStrongSell = data.obi < -0.4;

  const hasLiq = data.liq_side !== "NONE";
  const isLiqLong = data.liq_side === "SELL";

  return (
    <motion.div
      layout
      className={cn(
        "relative p-4 rounded-xl panel overflow-hidden border transition-all duration-300",
        isStrongBuy ? "border-emerald-500 bg-emerald-50/10" : isStrongSell ? "border-rose-500 bg-rose-50/10" : "border-slate-200"
      )}
    >
      <div className="relative z-10">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
             <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">
                {data.symbol.replace("USDT", "")}
             </span>
          </div>
          
          <AnimatePresence mode="wait">
             {hasLiq ? (
                <motion.div 
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className={cn(
                    "flex items-center gap-1 px-1.5 py-0.5 rounded text-[8px] font-black uppercase tracking-tighter",
                    isLiqLong ? "bg-rose-600 text-white" : "bg-emerald-600 text-white"
                  )}
                >
                  <Flame className="w-2.5 h-2.5" />
                  LIQ ${(data.liq_val / 1000).toFixed(0)}k
                </motion.div>
             ) : (
                <Zap className={cn(
                  "w-3 h-3 transition-colors duration-300",
                  isUp ? "text-emerald-600" : "text-rose-600"
                )} />
             )}
          </AnimatePresence>
        </div>

        <div className="space-y-1 mb-4">
          <motion.div
            key={data.price}
            initial={{ y: isUp ? 2 : -2, opacity: 0.8 }}
            animate={{ y: 0, opacity: 1 }}
            className={cn(
              "text-xl font-black tabular-nums tracking-tighter",
              isUp ? "text-emerald-600" : "text-rose-600"
            )}
          >
            {formatCurrency(data.price)}
          </motion.div>
        </div>

        {/* Tactical Meter (Flat) */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5 opacity-60">
                <Activity className="w-2.5 h-2.5 text-slate-400" />
                <span className="text-[7px] font-black text-slate-400 uppercase tracking-widest">Order Pressure</span>
            </div>
            <span className={cn(
              "text-[9px] font-black tabular-nums",
              data.obi > 0 ? "text-emerald-600" : "text-rose-600"
            )}>
              {(data.obi * 100).toFixed(0)}%
            </span>
          </div>
          <div className="h-1 w-full bg-slate-100 rounded-full overflow-hidden">
             <motion.div 
                animate={{ width: `${obiWidth}%` }}
                className={cn("h-full", data.obi > 0 ? "bg-emerald-600" : "bg-rose-600")}
             />
          </div>
        </div>
      </div>
    </motion.div>
  );
}
