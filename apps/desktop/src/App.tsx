import { AnimatePresence, motion } from "framer-motion";
import { BrainCircuit, CalendarClock, GitBranch, Lock, Search, Sparkles, WandSparkles } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { ClusterLegend } from "./components/ClusterLegend";
import { GalaxyView } from "./components/GalaxyView";
import { InsightPanel } from "./components/InsightPanel";
import { NotePreview } from "./components/NotePreview";
import { TimelineScrubber } from "./components/TimelineScrubber";
import { fetchGalaxy, triggerSync } from "./lib/api";
import type { GalaxyPayload, NoteNode } from "./lib/types";

type Mode = "galaxy" | "time" | "graph";

export function App() {
  const [payload, setPayload] = useState<GalaxyPayload | null>(null);
  const [selected, setSelected] = useState<NoteNode | null>(null);
  const [query, setQuery] = useState("");
  const [mode, setMode] = useState<Mode>("galaxy");
  const [time, setTime] = useState(100);
  const [syncing, setSyncing] = useState(false);

  useEffect(() => {
    fetchGalaxy().then(setPayload);
  }, []);

  const folders = useMemo(() => {
    if (!payload) return [];
    return [...new Set(payload.notes.map((note) => note.folder))].sort();
  }, [payload]);

  const timeWindow = useMemo(() => {
    const timestamps = payload?.notes
      .map((note) => parseNoteDate(note.updatedAt))
      .filter((timestamp): timestamp is number => timestamp !== null) ?? [];
    if (!timestamps.length) return null;
    return {
      start: Math.min(...timestamps),
      end: Math.max(...timestamps)
    };
  }, [payload]);

  const filteredPayload = useMemo(() => {
    if (!payload) return null;
    const normalized = query.trim().toLowerCase();
    const cutoff =
      mode === "time" && timeWindow
        ? timeWindow.start + ((timeWindow.end - timeWindow.start) * time) / 100
        : Number.POSITIVE_INFINITY;
    const notes = payload.notes.filter((note) => {
      const matchesQuery =
        !normalized ||
        `${note.title} ${note.body} ${note.tags.join(" ")} ${note.folder}`.toLowerCase().includes(normalized);
      const updated = parseNoteDate(note.updatedAt);
      const matchesTime = mode !== "time" || !updated || updated <= cutoff;
      return matchesQuery && matchesTime;
    });
    const ids = new Set(notes.map((note) => note.id));
    return {
      ...payload,
      notes,
      edges: payload.edges.filter((edge) => ids.has(edge.source) && ids.has(edge.target))
    };
  }, [mode, payload, query, time, timeWindow]);

  async function onSync() {
    setSyncing(true);
    try {
      await triggerSync();
      setPayload(await fetchGalaxy());
    } finally {
      setSyncing(false);
    }
  }

  return (
    <main className="relative h-screen w-screen overflow-hidden bg-space-950 text-white">
      <div className="absolute inset-0 starfield" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(125,227,255,0.12),transparent_24%),radial-gradient(circle_at_84%_30%,rgba(255,122,170,0.10),transparent_22%),linear-gradient(180deg,rgba(3,4,10,0),rgba(3,4,10,0.92))]" />

      <header className="pointer-events-none absolute left-0 right-0 top-0 z-20 flex items-start justify-between p-4">
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="pointer-events-auto glass-panel top-brand"
        >
          <div className="grid h-8 w-8 place-items-center rounded-2xl bg-white/10 shadow-glow">
            <BrainCircuit size={17} />
          </div>
          <div>
            <h1 className="text-[15px] font-semibold tracking-normal">NeuralNotes</h1>
            <p className="text-[11px] text-white/48">{payload ? `${payload.notes.length} local notes` : "Indexing notes"}</p>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.06 }}
          className="pointer-events-auto glass-panel mode-switcher"
        >
          {[
            ["galaxy", Sparkles, "Galaxy"],
            ["time", CalendarClock, "Time"],
            ["graph", GitBranch, "Graph"]
          ].map(([value, Icon, label]) => (
            <button
              key={value as string}
              title={`${label} mode`}
              onClick={() => setMode(value as Mode)}
              className={`segmented-button ${mode === value ? "is-active" : ""}`}
            >
              <Icon size={16} />
              <span>{label as string}</span>
            </button>
          ))}
        </motion.div>
      </header>

      <section className="absolute inset-0 z-10">
        {filteredPayload && (
          <GalaxyView
            payload={filteredPayload}
            mode={mode}
            searchQuery={query}
            onSelect={setSelected}
            selectedId={selected?.id}
          />
        )}
      </section>

      <aside className="pointer-events-none absolute bottom-24 left-4 top-[88px] z-20 flex w-[min(23vw,272px)] min-w-[230px] flex-col gap-2">
        <div className="pointer-events-auto glass-panel compact-panel p-2.5">
          <div className="flex items-center gap-2 rounded-2xl bg-white/[0.07] px-3 py-2">
            <Search size={16} className="text-white/50" />
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search notes, tags, folders"
              className="min-w-0 flex-1 bg-transparent text-sm outline-none placeholder:text-white/35"
            />
          </div>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {folders.slice(0, 6).map((folder) => (
              <button key={folder} className="filter-chip">
                {folder}
              </button>
            ))}
          </div>
        </div>

        <InsightPanel payload={payload} />
      </aside>

      <aside className="pointer-events-none absolute bottom-24 right-4 top-[88px] z-20 flex w-[min(24vw,304px)] min-w-[250px] flex-col gap-2">
        <div className="pointer-events-auto glass-panel compact-panel p-2.5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm font-medium">
              <Lock size={15} />
              On-device index
            </div>
            <button onClick={onSync} className="primary-button" disabled={syncing}>
              <WandSparkles size={15} />
              {syncing ? "Syncing" : "Sync"}
            </button>
          </div>
          <div className="mt-2 text-[11px] leading-4 text-white/48">
            {payload ? `${filteredPayload?.notes.length ?? payload.notes.length} visible • ${payload.edges.length} links` : "Loading local cache"}
          </div>
        </div>

        {mode === "time" && (
          <TimelineScrubber
            value={time}
            onChange={setTime}
            label={timeWindow ? new Date(timeWindow.start + ((timeWindow.end - timeWindow.start) * time) / 100).toLocaleDateString() : "No dates"}
          />
        )}

        <AnimatePresence mode="popLayout">
          {selected && <NotePreview note={selected} onClose={() => setSelected(null)} />}
        </AnimatePresence>
      </aside>

      <div className="pointer-events-none absolute bottom-4 left-1/2 z-30 w-[min(740px,calc(100vw-36px))] -translate-x-1/2">
        <ClusterLegend payload={payload} />
      </div>
    </main>
  );
}

function parseNoteDate(value: string): number | null {
  const direct = Date.parse(value);
  if (Number.isFinite(direct)) return direct;
  const cleaned = value.replace(/\s+at\s+/i, " ").replace(/[\u202f\u00a0]/g, " ");
  const parsed = Date.parse(cleaned);
  return Number.isFinite(parsed) ? parsed : null;
}
