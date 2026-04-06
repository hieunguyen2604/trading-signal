"use client";

import React, { useEffect, useState } from "react";
import { Clock, Zap, Globe, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";

interface Session {
  id: string;
  name: string;
  start_utc: number; // Hour 0-23
  end_utc: number;
}

const SESSIONS: Session[] = [
  { id: "sydney", name: "Sydney", start_utc: 22, end_utc: 7 },
  { id: "tokyo", name: "Tokyo", start_utc: 0, end_utc: 9 },
  { id: "london", name: "London", start_utc: 8, end_utc: 17 },
  { id: "newyork", name: "New York", start_utc: 13, end_utc: 22 },
];

export function SessionPulse() {
  const [now, setNow] = useState(new Date());
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const timer = setInterval(() => setNow(new Date()), 60000);
    return () => clearInterval(timer);
  }, []);

  const getSessionStatus = (session: Session) => {
    const utcHour = now.getUTCHours();
    const utcMin = now.getUTCMinutes();
    const current = utcHour + utcMin / 60;

    const { start_utc, end_utc } = session;
    let isActive = false;

    if (start_utc < end_utc) {
      isActive = current >= start_utc && current < end_utc;
    } else {
      // Overnight (Sydney)
      isActive = current >= start_utc || current < end_utc;
    }

    // Progress
    let progress = 0;
    const duration = start_utc < end_utc ? end_utc - start_utc : (24 - start_utc) + end_utc;
    let elapsed = 0;
    
    if (isActive) {
      if (start_utc < end_utc) {
        elapsed = current - start_utc;
      } else {
        elapsed = current >= start_utc ? current - start_utc : (24 - start_utc) + current;
      }
      progress = (elapsed / duration) * 100;
    }

    return { isActive, progress };
  };

  const isVolatilityOverlap = () => {
    const utcHour = now.getUTCHours();
    // London/NY Overlap: 13:00 - 17:00 UTC
    return utcHour >= 13 && utcHour < 17;
  };

  const localTimeStr = now.toLocaleTimeString("vi-VN", { hour: '2-digit', minute: '2-digit' });

  return (
    <div className="panel p-6 rounded-2xl relative overflow-hidden bg-white/70 backdrop-blur-md">
      <div className="flex items-center justify-between mb-8 relative z-10">
        <div className="flex items-center gap-3">
          <div className={cn(
            "p-2 rounded-lg transition-colors duration-500",
            isVolatilityOverlap() ? "bg-emerald-500 text-white shadow-lg shadow-emerald-200" : "bg-slate-100 text-slate-500"
          )}>
            <Zap className={cn("w-4 h-4", isVolatilityOverlap() && "animate-pulse")} />
          </div>
          <div>
            <h3 className="uppercase text-[10px] font-black tracking-[0.2em] text-slate-500">Global Pulse</h3>
            <div className="flex items-center gap-2">
              <span className="text-xl font-black text-slate-900 tabular-nums">1:2.5 (TACTICAL)</span>
              <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-slate-900 text-white text-[9px] font-black">
                <Clock className="w-2.5 h-2.5" />
                {mounted ? localTimeStr : "--:--"} <span className="text-slate-400 font-medium">ICT</span>
              </div>
            </div>
          </div>
        </div>

        {isVolatilityOverlap() && (
          <motion.div 
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-100 text-emerald-700 border border-emerald-200"
          >
            <AlertCircle className="w-3 h-3" />
            <span className="text-[9px] font-black uppercase tracking-widest animate-pulse">Volatility Wave Active</span>
          </motion.div>
        )}
      </div>

      <div className="space-y-5">
        {SESSIONS.map((session) => {
          const { isActive, progress } = getSessionStatus(session);
          return (
            <div key={session.id} className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className={cn(
                    "w-1.5 h-1.5 rounded-full",
                    isActive ? "bg-emerald-500 shadow-sm shadow-emerald-200 animate-pulse" : "bg-slate-200"
                  )} />
                  <span className={cn(
                    "text-[10px] font-black uppercase tracking-widest",
                    isActive ? "text-slate-900" : "text-slate-400"
                  )}>
                    {session.name}
                  </span>
                </div>
                <span className="text-[9px] font-mono text-slate-400 font-bold">
                  {isActive ? `${Math.floor(progress)}%` : "Dormant"}
                </span>
              </div>
              <div className="h-1 w-full bg-slate-100 rounded-full overflow-hidden">
                <motion.div 
                  initial={{ width: 0 }}
                  animate={{ width: `${progress}%` }}
                  transition={{ duration: 1, ease: "easeOut" }}
                  className={cn(
                    "h-full transition-colors duration-500",
                    isActive ? (isVolatilityOverlap() && (session.id === "london" || session.id === "newyork") ? "bg-emerald-500" : "bg-slate-800") : "bg-transparent"
                  )}
                />
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-8 pt-4 border-t border-slate-50 flex items-center justify-between">
        <div className="flex items-center gap-2 text-[9px] font-bold text-slate-400 uppercase tracking-widest">
          <Globe className="w-3 h-3" />
          Cross-Market Liquidity
        </div>
        <div className="flex items-center gap-1.5">
           <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
           <span className="text-[8px] font-black text-emerald-600 uppercase">Live</span>
        </div>
      </div>
    </div>
  );
}
