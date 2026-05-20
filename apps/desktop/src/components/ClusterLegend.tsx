import { motion } from "framer-motion";
import { clusterColor } from "../lib/colors";
import type { GalaxyPayload } from "../lib/types";

type Props = {
  payload: GalaxyPayload | null;
};

export function ClusterLegend({ payload }: Props) {
  const clusters = [...(payload?.clusters ?? [])].sort((a, b) => b.count - a.count).slice(0, 9);

  if (!clusters.length) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="pointer-events-auto glass-panel legend-panel"
    >
      <div className="legend-title">Constellations</div>
      <div className="legend-scroll">
        {clusters.map((cluster) => (
          <div key={cluster.id} className="legend-chip" title={`${cluster.label}: ${cluster.count} notes`}>
            <span
              className="legend-dot"
              style={{
                backgroundColor: clusterColor(cluster.id),
                boxShadow: `0 0 16px ${clusterColor(cluster.id)}`
              }}
            />
            <span className="legend-label">{cluster.label}</span>
            <span className="legend-count">{cluster.count}</span>
          </div>
        ))}
      </div>
    </motion.div>
  );
}
