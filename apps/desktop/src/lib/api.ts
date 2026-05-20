import type { GalaxyPayload } from "./types";

const API_BASE = import.meta.env.VITE_NEURALNOTES_API ?? "http://127.0.0.1:8717";

export async function fetchGalaxy(): Promise<GalaxyPayload> {
  try {
    const response = await fetch(`${API_BASE}/api/galaxy`);
    if (!response.ok) throw new Error(`API responded ${response.status}`);
    return response.json();
  } catch {
    const local = await fetch("/sample-galaxy.json");
    return local.json();
  }
}

export async function triggerSync() {
  const response = await fetch(`${API_BASE}/api/sync`, { method: "POST" });
  if (!response.ok) throw new Error("Unable to start sync");
  return response.json();
}
