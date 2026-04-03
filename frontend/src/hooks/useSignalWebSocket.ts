"use client";

import { useEffect, useState, useRef, useCallback } from "react";

export type SignalUpdate = {
  symbol: string;
  score: number;
  signal: "BUY" | "WATCH" | "SELL";
  confidence: "PROVISIONAL" | "CONFIRMED" | "STRONG BUY" | "STRONG SELL" | "CONTRA-TREND";
  market_sync: boolean;
  btc_trend: "UP" | "DOWN" | "NEUTRAL";
  trend_15m: "UP" | "DOWN" | "NEUTRAL";
  trend_1h: "UP" | "DOWN" | "NEUTRAL";
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
  type?: "SIGNAL_UPDATE" | "TRADE_UPDATE" | "STATS_UPDATE";
  tradeStatus?: string;
  positionSize?: number;
  pnlPct?: number;
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
  const [stats, setStats] = useState<StrategyStats>({
    totalTrades: 0,
    winRate: 0,
    totalPnlPct: 0,
    trades24h: 0,
    winRate24h: 0,
    netPnL: 0
  });
  const [isConnected, setIsConnected] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);

  const connect = useCallback(() => {
    if (socketRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(url);
    socketRef.current = ws;

    ws.onopen = () => setIsConnected(true);
    ws.onmessage = (event) => {
      const data: any = JSON.parse(event.data);
      
      if (data.type === "STATS_UPDATE") {
        setStats(data);
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

  return { signals: topSignals, activeTrades: liveTrades, stats, isConnected };
}
