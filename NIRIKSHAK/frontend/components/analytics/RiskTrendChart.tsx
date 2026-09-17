"use client";

import React from "react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  CartesianGrid,
} from "recharts";

interface RiskTrendChartProps {
  events: Array<{
    id: string;
    event_id: string;
    timestamp: string;
    total_score: number | null;
    risk_level: string | null;
    user_identifier: string;
    action: string;
  }>;
  onSelectEvent?: (eventId: string) => void;
}

export const RiskTrendChart: React.FC<RiskTrendChartProps> = ({ events, onSelectEvent }) => {
  if (!events || events.length === 0) {
    return (
      <div className="h-44 flex items-center justify-center text-xs text-slate-500 font-mono">
        Awaiting telemetry to plot risk score velocity...
      </div>
    );
  }

  const chartData = [...events]
    .filter((e) => e.total_score !== null)
    .reverse()
    .map((e, idx) => {
      const timeStr = e.timestamp ? e.timestamp.slice(11, 19) : `T-${idx}`;
      return {
        id: e.id,
        event_id: e.event_id,
        time: timeStr,
        score: e.total_score || 0,
        risk_level: e.risk_level || "LOW",
        user: e.user_identifier,
        action: e.action,
      };
    });

  return (
    <div className="w-full h-48">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
          <defs>
            <linearGradient id="riskGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#ef4444" stopOpacity={0.6} />
              <stop offset="50%" stopColor="#f59e0b" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#10b981" stopOpacity={0.05} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} />
          <XAxis dataKey="time" stroke="#64748b" tick={{ fontSize: 10, fill: "#64748b" }} />
          <YAxis domain={[0, 100]} stroke="#64748b" tick={{ fontSize: 10, fill: "#64748b" }} />
          <Tooltip
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const d = payload[0].payload;
                return (
                  <div className="bg-slate-900 border border-slate-700 p-2 rounded shadow-xl text-xs font-mono">
                    <div className="text-slate-400 font-bold">{d.event_id}</div>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-slate-300">Score:</span>
                      <span className="text-amber-400 font-semibold">{d.score} / 100</span>
                      <span className="text-[10px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-300">
                        {d.risk_level}
                      </span>
                    </div>
                    <div className="text-[10px] text-slate-400 mt-1">
                      {d.user} • {d.action} • {d.time}
                    </div>
                  </div>
                );
              }
              return null;
            }}
          />
          <ReferenceLine y={81} stroke="#ef4444" strokeDasharray="3 3" label={{ value: "CRITICAL", fill: "#ef4444", fontSize: 9 }} />
          <ReferenceLine y={61} stroke="#f97316" strokeDasharray="3 3" label={{ value: "HIGH", fill: "#f97316", fontSize: 9 }} />
          <ReferenceLine y={31} stroke="#eab308" strokeDasharray="3 3" label={{ value: "MODERATE", fill: "#eab308", fontSize: 9 }} />
          <Area
            type="monotone"
            dataKey="score"
            stroke="#f59e0b"
            strokeWidth={2}
            fillOpacity={1}
            fill="url(#riskGradient)"
            activeDot={{
              r: 5,
              onClick: (_, e: any) => {
                if (onSelectEvent && e && e.payload) onSelectEvent(e.payload.event_id);
              },
            }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};
