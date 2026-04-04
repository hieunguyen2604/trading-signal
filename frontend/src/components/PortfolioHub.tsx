"use client";

import { motion } from "framer-motion";
import { Shield, TrendingUp, TrendingDown, AlertTriangle, Wallet, Percent } from "lucide-react";
import { cn, formatCurrency } from "@/lib/utils";

interface PortfolioHubProps {
  portfolio: {
    totalRisk: number;
    riskPercent: number;
    directionalBias: string;
    activePositions: number;
    symbols: string[];
    balance: number;
  } | null;
}

export function PortfolioHub({ portfolio }: PortfolioHubProps) {
  if (!portfolio) return null;

  const isHighRisk = portfolio.riskPercent > 5;
  const isExtremeRisk = portfolio.riskPercent > 8;

  const getBiasConfig = (bias: string) => {
    switch (bias) {
      case "HIGH LONG": return { icon: TrendingUp, color: "text-emerald-600", bg: "bg-emerald-50", border: "border-emerald-200" };
      case "HIGH SHORT": return { icon: TrendingDown, color: "text-rose-600", bg: "bg-rose-50", border: "border-rose-200" };
      case "LONG BIAS": return { icon: TrendingUp, color: "text-cyan-600", bg: "bg-cyan-50", border: "border-cyan-200" };
      case "SHORT BIAS": return { icon: TrendingDown, color: "text-orange-600", bg: "bg-orange-50", border: "border-orange-200" };
      default: return { icon: Shield, color: "text-slate-600", bg: "bg-slate-50", border: "border-slate-200" };
    }
  };

  const biasConfig = getBiasConfig(portfolio.directionalBias);
  const BiasIcon = biasConfig.icon;

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
      {/* Risk Meter */}
      <motion.div 
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className={cn(
          "p-4 rounded-2xl border transition-all duration-500 bg-white/50 backdrop-blur-sm shadow-sm",
          isExtremeRisk ? "border-rose-300 bg-rose-50/30" : isHighRisk ? "border-orange-300 bg-orange-50/30" : "border-slate-200"
        )}
      >
        <div className="flex items-center justify-between mb-2">
          <span className="text-[10px] font-black uppercase tracking-widest text-slate-500">Margin At Risk</span>
          {isHighRisk && <AlertTriangle className={cn("w-3 h-3 animate-pulse", isExtremeRisk ? "text-rose-600" : "text-orange-600")} />}
        </div>
        <div className="flex items-baseline gap-1">
          <span className={cn(
            "text-2xl font-black tabular-nums",
            isExtremeRisk ? "text-rose-600" : isHighRisk ? "text-orange-600" : "text-slate-900"
          )}>{portfolio.riskPercent}%</span>
          <span className="text-[10px] font-bold text-slate-400">/ 10% MAX</span>
        </div>
        <div className="w-full h-1.5 bg-slate-100 rounded-full mt-3 overflow-hidden">
          <motion.div 
            initial={{ width: 0 }}
            animate={{ width: `${Math.min(portfolio.riskPercent * 10, 100)}%` }}
            className={cn(
              "h-full rounded-full transition-colors duration-500",
              isExtremeRisk ? "bg-rose-500" : isHighRisk ? "bg-orange-500" : "bg-cyan-500"
            )}
          />
        </div>
      </motion.div>

      {/* Directional Bias */}
      <motion.div 
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className={cn("p-4 rounded-2xl border bg-white/50 backdrop-blur-sm shadow-sm", biasConfig.border)}
      >
        <span className="text-[10px] font-black uppercase tracking-widest text-slate-500 block mb-2">Directional Bias</span>
        <div className="flex items-center gap-3">
          <div className={cn("p-2 rounded-lg", biasConfig.bg)}>
            <BiasIcon className={cn("w-4 h-4", biasConfig.color)} />
          </div>
          <span className={cn("text-sm font-black uppercase tracking-tight", biasConfig.color)}>
            {portfolio.directionalBias}
          </span>
        </div>
      </motion.div>

      {/* Capital Utilization */}
      <motion.div 
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="p-4 rounded-2xl border border-slate-200 bg-white/50 backdrop-blur-sm shadow-sm"
      >
        <span className="text-[10px] font-black uppercase tracking-widest text-slate-500 block mb-2">Cash Utilization</span>
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-blue-50">
            <Wallet className="w-4 h-4 text-blue-600" />
          </div>
          <div>
            <div className="text-sm font-black text-slate-900">{formatCurrency(portfolio.totalRisk)}</div>
            <div className="text-[9px] font-bold text-slate-400 capitalize">Total Risk Units</div>
          </div>
        </div>
      </motion.div>

      {/* Active Symbols */}
      <motion.div 
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="p-4 rounded-2xl border border-slate-200 bg-white/50 backdrop-blur-sm shadow-sm"
      >
        <span className="text-[10px] font-black uppercase tracking-widest text-slate-500 block mb-2">Tactical Footprint</span>
        <div className="flex flex-wrap gap-1">
          {portfolio.symbols.length > 0 ? portfolio.symbols.map(s => (
            <span key={s} className="px-1.5 py-0.5 rounded bg-slate-100 text-[8px] font-black text-slate-600 uppercase border border-slate-200">
              {s.replace("USDT", "")}
            </span>
          )) : (
            <span className="text-[10px] font-bold text-slate-300 italic">No Active Footprint</span>
          )}
        </div>
      </motion.div>
    </div>
  );
}
