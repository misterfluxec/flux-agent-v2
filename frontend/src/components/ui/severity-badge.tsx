import React from "react";

export type Severity = "INFO" | "WARNING" | "HIGH" | "CRITICAL";

const severityStyles: Record<Severity, string> = {
  INFO:     "bg-blue-500/10 text-blue-400 border-blue-500/20",
  WARNING:  "bg-amber-500/10 text-amber-400 border-amber-500/20",
  HIGH:     "bg-orange-500/10 text-orange-400 border-orange-500/20",
  CRITICAL: "bg-rose-500/10 text-rose-400 border-rose-500/20",
};

const severityDot: Record<Severity, string> = {
  INFO:     "bg-blue-400",
  WARNING:  "bg-amber-400",
  HIGH:     "bg-orange-400",
  CRITICAL: "bg-rose-400",
};

interface SeverityBadgeProps {
  severity: Severity;
  pulse?: boolean;
}

export function SeverityBadge({ severity, pulse = false }: SeverityBadgeProps) {
  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${severityStyles[severity]}`}>
      {pulse && severity === "CRITICAL" ? (
        <span className="relative flex h-2 w-2">
          <span className={`animate-ping absolute inline-flex h-full w-full rounded-full ${severityDot[severity]} opacity-75`}></span>
          <span className={`relative inline-flex rounded-full h-2 w-2 ${severityDot[severity]}`}></span>
        </span>
      ) : (
        <span className={`inline-flex rounded-full h-2 w-2 ${severityDot[severity]}`}></span>
      )}
      {severity}
    </span>
  );
}
