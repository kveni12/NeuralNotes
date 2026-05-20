export const clusterColors = ["#7de3ff", "#8affc1", "#ffd47a", "#ff7aaa", "#b79cff", "#f6e27f", "#7cc7ff", "#f09cff", "#a7f3d0"];

export function clusterColor(clusterId: number) {
  return clusterColors[Math.abs(clusterId) % clusterColors.length];
}
