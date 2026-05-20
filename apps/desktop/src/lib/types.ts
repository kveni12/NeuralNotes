export type NoteNode = {
  id: string;
  title: string;
  body: string;
  folder: string;
  tags: string[];
  createdAt: string;
  updatedAt: string;
  clusterId: number;
  clusterLabel: string;
  x: number;
  y: number;
  radius: number;
  forgottenMonths: number;
  score: number;
};

export type GraphEdge = {
  source: string;
  target: string;
  similarity: number;
};

export type GalaxyPayload = {
  notes: NoteNode[];
  edges: GraphEdge[];
  clusters: Array<{
    id: number;
    label: string;
    color: string;
    centroid: [number, number];
    count: number;
  }>;
};
