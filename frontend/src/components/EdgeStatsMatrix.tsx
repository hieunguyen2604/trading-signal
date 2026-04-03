"use client";

import { StrategyStats } from "@/hooks/useSignalWebSocket";
import { cn } from "@/lib/utils";
import { TrendingUp, Award, BarChart4, Cpu, ShieldAlert } from "lucide-react";

interface EdgeStatsMatrixProps {
  stats: StrategyStats;
}

export function EdgeStatsMatrix({ stats }: EdgeStatsMatrixProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      <StatCard 
        label="Global Strategy Edge" 
        value={`${stats.winRate}%`} 
        subtext={`Verified on ${stats.totalTrades} events`}
        icon={<Award className="w-4 h-4 text-zinc-400" />}
        trend={stats.winRate > 50 ? "up" : "down"}
      />
      <StatCard 
        label="24h Yield" 
        value={`${stats.winRate24h}%`} 
        subtext={`${stats.trades24h} signals processed`}
        icon={<BarChart4 className="w-4 h-4 text-zinc-400" />}
        trend={stats.winRate24h > 50 ? "up" : "down"}
      />
      <StatCard 
        label="Aggregated PnL" 
        value={`+${stats.totalPnlPct}%`} 
        subtext="Institutional Return Index"
        icon={<TrendingUp className="w-4 h-4 text-zinc-400" />}
        trend="up"
      />
      
      <div className="p-4 rounded-xl card flex flex-col justify-between">
        <div className="flex items-center gap-2 mb-4">
          <Cpu className="w-4 h-4 text-emerald-500" />
          <span className="text-[10px] font-black text-zinc-500 uppercase tracking-widest">Edge Factor</span>
        </div>
        <div>
          <span className="text-2xl font-black text-white tabular-nums tracking-tighter">
            2.4x
          </span>
          <p className="text-[9px] font-black text-zinc-600 uppercase tracking-widest mt-1">
            Active Advantage
          </p>
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value, subtext, icon, trend }: { 
  label: string; 
  value: string; 
  subtext: string; 
  icon: React.ReactNode;
  trend: "up" | "down";
}) {
  return (
    <div className="p-4 rounded-xl card">
      <div className="flex items-center gap-2 mb-6">
        {icon}
        <span className="text-[10px] font-black text-zinc-500 uppercase tracking-widest leading-none">{label}</span>
      </div>
      
      <div>
        <div className="flex items-center gap-2">
          <span className={cn(
            "text-2xl font-black tracking-tighter tabular-nums text-white",
            trend === "down" && "text-rose-500"
          )}>{value}</span>
        </div>
        <p className="text-[9px] font-black text-zinc-600 uppercase tracking-widest mt-1">
          {subtext}
        </p>
      </div>
    </div>
  );
}
