import * as d3 from "d3";
import { useEffect, useMemo, useRef } from "react";
import { clusterColors } from "../lib/colors";
import type { GalaxyPayload, NoteNode } from "../lib/types";

type Props = {
  payload: GalaxyPayload;
  mode: "galaxy" | "time" | "graph";
  searchQuery: string;
  selectedId?: string;
  onSelect: (note: NoteNode) => void;
};

type SimNode = NoteNode & { sx: number; sy: number };

export function GalaxyView({ payload, mode, searchQuery, selectedId, onSelect }: Props) {
  const svgRef = useRef<SVGSVGElement | null>(null);

  const nodes = useMemo<SimNode[]>(() => payload.notes.map((note) => ({ ...note, sx: note.x, sy: note.y })), [payload.notes]);

  useEffect(() => {
    if (!svgRef.current) return;

    const svg = d3.select(svgRef.current);
    const width = window.innerWidth;
    const height = window.innerHeight;
    svg.selectAll("*").remove();

    const root = svg.append("g").attr("class", "galaxy-root");
    const edgeLayer = root.append("g").attr("class", "edge-layer");
    const haloLayer = root.append("g").attr("class", "halo-layer");
    const labelLayer = root.append("g").attr("class", "label-layer");
    const nodeLayer = root.append("g").attr("class", "node-layer");

    const color = d3
      .scaleOrdinal<number, string>()
      .domain(payload.clusters.map((cluster) => cluster.id))
      .range(clusterColors);

    const edgeData = mode === "graph" ? payload.edges.slice(0, 900) : [];
    const edges = edgeLayer
      .selectAll("line")
      .data(edgeData)
      .join("line")
      .attr("stroke", "rgba(180,220,255,0.16)")
      .attr("stroke-width", (edge) => Math.max(0.45, edge.similarity * 3.2));

    const halos = haloLayer
      .selectAll("circle")
      .data(payload.clusters)
      .join("circle")
      .attr("r", (cluster) => Math.sqrt(cluster.count) * 27)
      .attr("fill", (cluster) => color(cluster.id))
      .attr("opacity", 0.055)
      .attr("filter", "url(#clusterBlur)");

    const labels = labelLayer
      .selectAll("text")
      .data(payload.clusters)
      .join("text")
      .text((cluster) => cluster.label)
      .attr("fill", "rgba(255,255,255,0.66)")
      .attr("font-size", 13)
      .attr("font-weight", 600)
      .attr("text-anchor", "middle")
      .attr("opacity", 1);

    const node = nodeLayer
      .selectAll("circle")
      .data(nodes)
      .join("circle")
      .attr("r", (note) => note.radius)
      .attr("fill", (note) => color(note.clusterId))
      .attr("stroke", (note) => (note.id === selectedId ? "rgba(255,255,255,0.95)" : "rgba(255,255,255,0.38)"))
      .attr("stroke-width", (note) => (note.id === selectedId ? 2 : 0.6))
      .attr("opacity", (note) => (searchQuery && note.score < 0.55 ? 0.24 : 0.92))
      .style("filter", "drop-shadow(0 0 8px currentColor)")
      .style("cursor", "pointer");

    node.append("title").text((note) => `${note.title}\n${note.clusterLabel}`);
    node.on("click", (_, note) => onSelect(note));

    const linksById = new Map(nodes.map((note) => [note.id, note]));
    const simulation = d3
      .forceSimulation(nodes)
      .alpha(0.55)
      .alphaDecay(0.055)
      .force("x", d3.forceX<SimNode>((note) => width / 2 + note.sx * width * 0.34).strength(0.12))
      .force("y", d3.forceY<SimNode>((note) => height / 2 + note.sy * height * 0.34).strength(0.12))
      .force("charge", d3.forceManyBody().strength(-9))
      .force("collide", d3.forceCollide<SimNode>().radius((note) => note.radius + 4))
      .on("tick", () => {
        node.attr("cx", (note) => note.x).attr("cy", (note) => note.y);
        halos
          .attr("cx", (cluster) => width / 2 + cluster.centroid[0] * width * 0.34)
          .attr("cy", (cluster) => height / 2 + cluster.centroid[1] * height * 0.34);
        labels
          .attr("x", (cluster) => width / 2 + cluster.centroid[0] * width * 0.34)
          .attr("y", (cluster) => height / 2 + cluster.centroid[1] * height * 0.34);
        edges
          .attr("x1", (edge) => linksById.get(edge.source)?.x ?? 0)
          .attr("y1", (edge) => linksById.get(edge.source)?.y ?? 0)
          .attr("x2", (edge) => linksById.get(edge.target)?.x ?? 0)
          .attr("y2", (edge) => linksById.get(edge.target)?.y ?? 0);
      });

    const zoom = d3
      .zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.25, 7])
      .on("zoom", (event) => {
        root.attr("transform", event.transform.toString());
        labels.attr("opacity", event.transform.k > 0.72 ? 1 : 0);
        node.attr("r", (note) => Math.max(1.8, note.radius / Math.sqrt(event.transform.k)));
      });

    svg.call(zoom);

    return () => {
      simulation.stop();
      svg.on(".zoom", null);
    };
  }, [mode, nodes, onSelect, payload.clusters, payload.edges, searchQuery, selectedId]);

  return (
    <div className="relative h-full w-full">
      <svg ref={svgRef} className="h-full w-full">
        <defs>
          <filter id="clusterBlur">
            <feGaussianBlur stdDeviation="18" />
          </filter>
        </defs>
      </svg>
    </div>
  );
}
