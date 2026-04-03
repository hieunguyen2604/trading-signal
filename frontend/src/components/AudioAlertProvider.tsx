"use client";

import { useEffect, useRef, createContext, useContext } from "react";
import { SignalUpdate } from "@/hooks/useSignalWebSocket";

type AudioAlertContextType = {
  playDing: () => void;
  playWarning: () => void;
};

const AudioAlertContext = createContext<AudioAlertContextType | null>(null);

export function useAudioAlert() {
  const context = useContext(AudioAlertContext);
  if (!context) throw new Error("useAudioAlert must be used within AudioAlertProvider");
  return context;
}

export function AudioAlertProvider({ children, signals }: { children: React.ReactNode, signals: SignalUpdate[] }) {
  const audioContextRef = useRef<AudioContext | null>(null);
  const lastPlayedRef = useRef<Record<string, string>>({});

  useEffect(() => {
    // Initialize AudioContext on first user interaction-like moment
    const initAudio = () => {
      if (!audioContextRef.current) {
        audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
      }
    };
    window.addEventListener("mousedown", initAudio, { once: true });
    return () => window.removeEventListener("mousedown", initAudio);
  }, []);

  const playSound = (freq: number, type: OscillatorType, duration: number, volume: number) => {
    if (!audioContextRef.current) return;
    const ctx = audioContextRef.current;
    
    if (ctx.state === "suspended") ctx.resume();

    const osc = ctx.createOscillator();
    const gain = ctx.createGain();

    osc.type = type;
    osc.frequency.setValueAtTime(freq, ctx.currentTime);
    
    gain.gain.setValueAtTime(volume, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + duration);

    osc.connect(gain);
    gain.connect(ctx.destination);

    osc.start();
    osc.stop(ctx.currentTime + duration);
  };

  const playDing = () => playSound(880, "sine", 0.5, 0.1); // High A
  const playWarning = () => {
    playSound(440, "triangle", 0.3, 0.05);
    setTimeout(() => playSound(330, "triangle", 0.3, 0.05), 150);
  };

  // Watch signals for STRONG BUY/SELL
  useEffect(() => {
    signals.forEach(signal => {
      if (signal.confidence.includes("STRONG")) {
        const lastStatus = lastPlayedRef.current[signal.symbol];
        if (lastStatus !== signal.confidence) {
          playDing();
          lastPlayedRef.current[signal.symbol] = signal.confidence;
        }
      }
    });
  }, [signals]);

  return (
    <AudioAlertContext.Provider value={{ playDing, playWarning }}>
      {children}
    </AudioAlertContext.Provider>
  );
}
