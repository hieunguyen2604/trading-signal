"use client";

import { cn } from "@/lib/utils";

interface SignalBadgeProps {
  signal: "BUY" | "WATCH" | "SELL";
  score: number;
}

export function SignalBadge({ signal, score }: SignalBadgeProps) {
  const isBuy = signal === "BUY";
  const isSell = signal === "SELL";
  const isWatch = signal === "WATCH";

  return (
    <div className={cn(
      "px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest border transition-all duration-500",
      isBuy ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/20 shadow-[0_0_15px_rgba(16,185,129,0.1)]" : 
      isSell ? "bg-rose-500/10 text-rose-500 border-rose-500/20 shadow-[0_0_15px_rgba(244,63,94,0.1)]" : 
      "bg-zinc-800 text-zinc-400 border-zinc-700/50"
    )}>
      {signal}
    </div>
  );
}
