"use client";

import { useEffect, useState, useRef, useCallback } from "react";

export type PriceUpdate = {
  symbol: string;
  price: number;
  direction: "up" | "down";
  timestamp: number;
  obi: number;
  liq_side: "BUY" | "SELL" | "NONE"; // Alpha v5.0
  liq_val: number; // Volume of recent liquidation
};

export function usePriceWebSocket(url: string) {
  const [prices, setPrices] = useState<Record<string, PriceUpdate>>({});
  const [isConnected, setIsConnected] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);

  const connect = useCallback(() => {
    if (socketRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(url);
    socketRef.current = ws;

    ws.onopen = () => setIsConnected(true);
    ws.onmessage = (event) => {
      const data: PriceUpdate = JSON.parse(event.data);
      setPrices((prev) => ({
        ...prev,
        [data.symbol]: data
      }));
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

  return { prices, isConnected };
}
