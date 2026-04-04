"use client";

import { useEffect, useState, useRef, useCallback } from "react";

export type SignalUpdate = {
  symbol: string;
  score: number;
  signal: "BUY" | "WATCH" | "SELL";
  confidence: "PROVISIONAL" | "CONFIRMED" | "STRONG BUY" | "STRONG SELL" | "CONTRA-TREND";
  market_sync: boolean;
  btc_trend: "UP" | "DOWN" | "NEUTRAL";
  trend_1st: "UP" | "DOWN" | "NEUTRAL";
  trend_2nd: "UP" | "DOWN" | "NEUTRAL";
  obi: number;
  liq_magnet_price: number;
  liq_vol: number;
  entryPrice: number;
  stopLoss: number;
  takeProfit1: number;
  takeProfit2: number;
  currentPrice?: number;
  riskReward: string;
  is_final: boolean;
  updatedAt: string;
  ai_insight?: string; // Intelligence Era v13.1
  strategy?: string;   // Alpha v12.5: Strategy Mode
  type?: "SIGNAL_UPDATE" | "TRADE_UPDATE" | "STATS_UPDATE";
  tradeStatus?: string;
  positionSize?: number;
  pnlPct?: number;
  sentiment_alignment?: "BULLISH" | "BEARISH" | "NEUTRAL";
};


export type SentimentData = {
  fng_value: number;
  fng_classification: string;
  last_updated: string | null;
  top_news: Array<{
    title: string;
    sentiment: "bullish" | "bearish" | "neutral";
    source: string;
  }>;
};

export type StrategyStats = {
  totalTrades: number;
  winRate: number;
  totalPnlPct: number;
  trades24h: number;
  winRate24h: number;
  netPnL: number;
};

export function useSignalWebSocket(url: string) {
  const [signals, setSignals] = useState<Record<string, SignalUpdate>>({});
  const [activeTrades, setActiveTrades] = useState<Record<string, SignalUpdate>>({});
  const [stats, setStats] = useState<any>(null);
  const [sentiment, setSentiment] = useState<any>(null);
  const [portfolio, setPortfolio] = useState<any>(null);
  const [strategyMode] = useState<string>("AETHER");
  const [isConnected, setIsConnected] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);
  useEffect(() => {
    // Alpha v13.5: Dynamic API Base for Docker/Production
    const API_BASE = process.env.NEXT_PUBLIC_API_URL || 
                    (typeof window !== "undefined" ? `${window.location.protocol}//${window.location.hostname}:8000` : "http://127.0.0.1:8000");

    // Initial data fetch
    const fetchInitialData = async () => {
      try {
        const [statsRes, modeRes, portfolioRes, signalsRes, tradesRes] = await Promise.all([
          fetch(`${API_BASE}/api/signals/status`),
          fetch(`${API_BASE}/api/signals/mode`),
          fetch(`${API_BASE}/api/signals/portfolio/stats`),
          fetch(`${API_BASE}/api/signals/active`),
          fetch(`${API_BASE}/api/signals/trades/active`)
        ]);
        
        const statsData = await statsRes.json();
        const modeData = await modeRes.json();
        const portfolioData = await portfolioRes.json();
        const signalsData = await signalsRes.json();
        const tradesData = await tradesRes.json();
        
        setStats(statsData);
        setPortfolio(portfolioData);
        
        // Populate initial signals
        if (Array.isArray(signalsData)) {
          const signalMap: Record<string, SignalUpdate> = {};
          signalsData.forEach(s => signalMap[s.symbol] = s);
          setSignals(signalMap);
        }

        // Alpha v12.5: Populate initial active positions
        if (Array.isArray(tradesData)) {
          const tradeMap: Record<string, SignalUpdate> = {};
          tradesData.forEach(t => tradeMap[t.symbol] = t);
          setActiveTrades(tradeMap);
        }

      } catch (err) {
        console.error("Failed to fetch initial data:", err);
      }
    };

    fetchInitialData();
  }, []);

  const connect = useCallback(() => {
    if (socketRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(url);
    socketRef.current = ws;

    ws.onopen = () => setIsConnected(true);
    ws.onmessage = (event) => {
      const data: any = JSON.parse(event.data);
      
      if (data.type === "WELCOME_UPDATE") {
        setSentiment(data.sentiment);
        setStats(data.stats);
      } else if (data.type === "PORTFOLIO_SYNC") {
        setPortfolio(data);
      } else if (data.type === "STATS_UPDATE") {
        setStats(data);
      } else if (data.type === "SENTIMENT_UPDATE") {
        setSentiment(data);
      } else if (data.type === "TRADE_UPDATE") {
        setActiveTrades((prev) => ({
          ...prev,
          [data.symbol]: {
            ...prev[data.symbol],
            ...data
          }
        }));
      } else {
        setSignals((prev) => ({
          ...prev,
          [data.symbol]: data
        }));
      }
    };
    ws.onclose = () => {
      setIsConnected(false);
      setTimeout(connect, 3000);
    };
  }, [url]);

  useEffect(() => {
    connect();
    return () => socketRef.current?.close();
  }, [connect]);

  // Sorted list for top 5 signals
  const topSignals = Object.values(signals)
    .sort((a, b) => b.score - a.score)
    .slice(0, 5);

  const liveTrades = Object.values(activeTrades)
    .filter(t => !["STOP_LOSS_HIT", "TP2_HIT"].includes(t.tradeStatus || ""));

  return { 
    signals: topSignals, 
    activeTrades: liveTrades, 
    stats, 
    sentiment, 
    portfolio,
    strategyMode,
    isConnected 
  };
}
