import { motion } from "framer-motion";
import { Activity, Orbit, TrendingUp, Waves } from "lucide-react";
import type { GalaxyPayload } from "../lib/types";

type Props = {
  payload: GalaxyPayload | null;
};

export function InsightPanel({ payload }: Props) {
  const largest = payload ? [...payload.clusters].sort((a, b) => b.count - a.count)[0] : null;
  const stale = payload?.notes.filter((note) => note.forgottenMonths >= 6).slice(0, 2) ?? [];

  const insights = [
    {
      icon: TrendingUp,
      label: "Rapidly growing cluster",
      value: largest ? largest.label : "Indexing",
      tint: "text-neural-mint"
    },
    {
      icon: Orbit,
      label: "Recurring theme",
      value: payload ? "Systems thinking" : "Calculating",
      tint: "text-neural-cyan"
    },
    {
      icon: Waves,
      label: "Forgotten memory",
      value: stale[0] ? `${stale[0].title} surfaced` : "None yet",
      tint: "text-neural-amber"
    },
    {
      icon: Activity,
      label: "Graph health",
      value: payload ? `${payload.edges.length} semantic links` : "Loading",
      tint: "text-neural-rose"
    }
  ];

  return (
    <motion.div
      initial={{ opacity: 0, x: -12 }}
      animate={{ opacity: 1, x: 0 }}
      className="pointer-events-auto glass-panel p-3"
    >
      <div className="mb-3 text-sm font-medium">AI insights</div>
      <div className="space-y-2">
        {insights.map(({ icon: Icon, label, value, tint }) => (
          <div key={label} className="rounded-2xl bg-white/[0.055] p-3">
            <div className="flex items-center gap-2 text-xs text-white/45">
              <Icon size={14} className={tint} />
              {label}
            </div>
            <div className="mt-1 truncate text-sm text-white/85">{value}</div>
          </div>
        ))}
      </div>
    </motion.div>
  );
}
