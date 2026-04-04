"use client";

import { SentimentData } from "@/hooks/useSignalWebSocket";
import { cn } from "@/lib/utils";
import { Newspaper, Gauge, TrendingUp, TrendingDown, Minus } from "lucide-react";

interface SentimentWidgetProps {
  sentiment: SentimentData;
}

export function SentimentWidget({ sentiment }: SentimentWidgetProps) {
  if (!sentiment) {
    return (
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-pulse">
        <div className="panel p-6 rounded-2xl h-48 bg-slate-50 border border-slate-100" />
        <div className="lg:col-span-2 panel p-6 rounded-2xl h-48 bg-slate-50 border border-slate-100" />
      </div>
    );
  }

  const fng = sentiment.fng_value;
  const classification = sentiment.fng_classification;

  const getFngColor = (val: number) => {
    if (val < 25) return "text-rose-600 bg-rose-50 border-rose-200";
    if (val < 45) return "text-orange-600 bg-orange-50 border-orange-200";
    if (val > 75) return "text-emerald-600 bg-emerald-50 border-emerald-200";
    if (val > 55) return "text-lime-600 bg-lime-50 border-lime-200";
    return "text-slate-500 bg-slate-50 border-slate-200";
  };

  const getFngBarColor = (val: number) => {
    if (val < 25) return "bg-rose-600";
    if (val < 45) return "bg-orange-600";
    if (val > 75) return "bg-emerald-600";
    if (val > 55) return "bg-lime-600";
    return "bg-slate-400";
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Fear & Greed Gauge */}
      <div className="panel p-6 rounded-2xl flex flex-col justify-between">
        <div className="flex items-center gap-3 mb-6">
          <Gauge className="w-4 h-4 text-slate-400" />
          <h3 className="uppercase text-[10px] font-black tracking-[0.2em] text-slate-500">Fear & Greed Index</h3>
        </div>
        
        <div className="flex items-end justify-between mb-4">
          <div className="flex flex-col">
            <span className="text-4xl font-black text-slate-900 tracking-tighter">{fng}</span>
            <span className={cn(
              "text-[9px] font-black uppercase tracking-widest px-2 py-0.5 rounded border mt-1",
              getFngColor(fng)
            )}>
              {classification}
            </span>
          </div>
          <div className="text-right">
             <span className="text-[8px] font-bold text-slate-400 uppercase tracking-widest">Global Sentiment</span>
          </div>
        </div>

        <div className="h-1.5 w-full bg-zinc-900 rounded-full overflow-hidden">
          <div 
            className={cn("h-full transition-all duration-1000", getFngBarColor(fng))}
            style={{ width: `${fng}%` }}
          />
        </div>
      </div>

      {/* Latest Market Intelligence */}
      <div className="lg:col-span-2 panel p-6 rounded-2xl">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <Newspaper className="w-4 h-4 text-slate-400" />
            <h3 className="uppercase text-[10px] font-black tracking-[0.2em] text-slate-500">Tactical Market Intelligence</h3>
          </div>
          <span className="text-[8px] font-bold text-slate-400 uppercase tracking-widest">Alpha Feed Live</span>
        </div>

        <div className="space-y-4">
          {sentiment.top_news.map((news, idx) => (
            <div key={idx} className="flex items-start gap-4 group">
              <div className={cn(
                "mt-1 p-1.5 rounded bg-slate-50 border border-slate-200",
                news.sentiment === "bullish" ? "text-emerald-600" : 
                news.sentiment === "bearish" ? "text-rose-600" : 
                "text-slate-400"
              )}>
                {news.sentiment === "bullish" ? <TrendingUp className="w-3 h-3" /> : 
                 news.sentiment === "bearish" ? <TrendingDown className="w-3 h-3" /> : 
                 <Minus className="w-3 h-3" />}
              </div>
              <div className="flex-1 space-y-1">
                <p className="text-[11px] font-bold text-slate-700 leading-normal group-hover:text-slate-950 transition-colors cursor-default">
                  {news.title}
                </p>
                <div className="flex items-center gap-4">
                  <span className="text-[8px] font-black uppercase tracking-widest text-slate-400">{news.source}</span>
                  <div className="w-1 h-1 rounded-full bg-slate-200" />
                  <span className="text-[8px] font-bold text-slate-400 uppercase tracking-widest">Just Now</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
