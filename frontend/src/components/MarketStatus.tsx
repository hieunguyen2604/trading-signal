import { cn, formatDateTime } from "@/lib/utils";
import { Activity, Clock } from "lucide-react";

interface MarketStatusProps {
  status: string;
  lastUpdated: string | Date;
  isConnected: boolean;
}

export function MarketStatus({ status, lastUpdated, isConnected }: MarketStatusProps) {
  return (
    <div className="flex flex-wrap items-center gap-4 text-sm font-medium">
      <div className="flex items-center gap-1.5 px-3 py-1 bg-zinc-900/50 border border-zinc-800 rounded-lg">
        <Clock className="w-4 h-4 text-zinc-400" />
        <span className="text-zinc-300">Updated:</span>
        <span className="text-zinc-100 tabular-nums">
          {formatDateTime(lastUpdated)}
        </span>
      </div>
      
      <div className={cn(
        "flex items-center gap-1.5 px-3 py-1 border rounded-lg transition-colors",
        isConnected 
          ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" 
          : "bg-rose-500/10 text-rose-400 border-rose-500/20"
      )}>
        <Activity className={cn("w-4 h-4", isConnected && "animate-pulse")} />
        <span>{isConnected ? status : "DISCONNECTED"}</span>
      </div>
    </div>
  );
}
