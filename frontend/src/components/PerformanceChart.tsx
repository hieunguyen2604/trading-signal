"use client";

import React, { useEffect, useState } from "react";
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import { motion } from "framer-motion";
import { TrendingUp, BarChart3, Download } from "lucide-react";
import { cn } from "@/lib/utils";

export function PerformanceChart() {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/signals/edge/history");
      if (!res.ok) throw new Error(`HTTP Error: ${res.status}`);
      
      const history = await res.json();
      setData(Array.isArray(history) ? history : []);
      setLoading(false);
    } catch (err) {
      console.error("Failed to fetch equity history:", err);
      // Don't set loading to false immediately on first failure to allow retry
      if (data.length > 0) setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000); // Update every 30s
    return () => clearInterval(interval);
  }, []);

  const handleExport = () => {
    window.open("http://127.0.0.1:8000/api/signals/edge/export", "_blank");
  };

  if (loading) {
    return (
      <div className="h-48 w-full bg-slate-50 flex items-center justify-center rounded-2xl border border-slate-100 animate-pulse">
        <BarChart3 className="w-5 h-5 text-slate-300 animate-bounce" />
      </div>
    );
  }

  const latestPnl = data.length > 0 ? data[data.length - 1].pnl : 0;
  const isPositive = latestPnl >= 0;

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="panel p-6 rounded-2xl relative overflow-hidden"
    >
      <div className="flex items-center justify-between mb-8 relative z-10">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-slate-100 rounded-lg">
            <TrendingUp className="w-4 h-4 text-slate-600" />
          </div>
          <div>
            <h3 className="uppercase text-[10px] font-black tracking-[0.2em] text-slate-500">Equity Performance</h3>
            <div className="flex items-center gap-2">
              <span className={cn(
                "text-xl font-black tabular-nums tracking-tighter",
                isPositive ? "text-emerald-600" : "text-rose-600"
              )}>
                {isPositive ? "+" : ""}{latestPnl}%
              </span>
              <span className="text-[9px] font-bold text-slate-400 uppercase tracking-widest leading-none">Cumulative PnL</span>
            </div>
          </div>
        </div>
        
        <button 
          onClick={handleExport}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900 text-white text-[9px] font-black uppercase tracking-widest hover:bg-slate-800 transition-all shadow-lg shadow-slate-200"
        >
          <Download className="w-3 h-3" />
          Export Audit Log
        </button>
      </div>

      <div className="h-48 w-full -mx-4">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>
            <defs>
              <linearGradient id="colorPnl" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={isPositive ? "#10b981" : "#f43f5e"} stopOpacity={0.1}/>
                <stop offset="95%" stopColor={isPositive ? "#10b981" : "#f43f5e"} stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
            <XAxis 
              dataKey="time" 
              hide 
            />
            <YAxis 
              hide 
              domain={['auto', 'auto']}
            />
            <Tooltip 
              contentStyle={{ 
                borderRadius: '12px', 
                border: 'none', 
                boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)',
                fontSize: '10px',
                fontWeight: '900',
                textTransform: 'uppercase',
                letterSpacing: '0.05em'
              }}
              labelStyle={{ display: 'none' }}
              itemStyle={{ color: isPositive ? '#10b981' : '#f43f5e' }}
              formatter={(value: any) => [`${value}% PnL`, ""]}
            />
            <Area 
              type="monotone" 
              dataKey="pnl" 
              stroke={isPositive ? "#10b981" : "#f43f5e"} 
              strokeWidth={3}
              fillOpacity={1} 
              fill="url(#colorPnl)" 
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
      
      {/* Visual Glare */}
      <div className="absolute top-0 right-0 w-32 h-32 bg-slate-100 rounded-full blur-3xl opacity-50 -mr-16 -mt-16" />
    </motion.div>
  );
}
