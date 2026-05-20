import { AnimatePresence, motion } from "framer-motion";
import { BrainCircuit, CalendarClock, GitBranch, Lock, Search, Sparkles, WandSparkles } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
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

  const filteredPayload = useMemo(() => {
    if (!payload) return null;
    const normalized = query.trim().toLowerCase();
    const notes = payload.notes.filter((note) => {
      const matchesQuery =
        !normalized ||
        `${note.title} ${note.body} ${note.tags.join(" ")} ${note.folder}`.toLowerCase().includes(normalized);
      const matchesTime = mode !== "time" || new Date(note.updatedAt).getTime() <= Date.now() - (100 - time) * 12 * 86400_000;
      return matchesQuery && matchesTime;
    });
    const ids = new Set(notes.map((note) => note.id));
    return {
      ...payload,
      notes,
      edges: payload.edges.filter((edge) => ids.has(edge.source) && ids.has(edge.target))
    };
  }, [mode, payload, query, time]);

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

      <header className="pointer-events-none absolute left-0 right-0 top-0 z-20 flex items-start justify-between p-5">
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="pointer-events-auto glass-panel flex items-center gap-3 px-4 py-3"
        >
          <div className="grid h-9 w-9 place-items-center rounded-2xl bg-white/10 shadow-glow">
            <BrainCircuit size={19} />
          </div>
          <div>
            <h1 className="text-[15px] font-semibold tracking-normal">NeuralNotes</h1>
            <p className="text-xs text-white/55">Local semantic galaxy for Apple Notes</p>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.06 }}
          className="pointer-events-auto glass-panel flex items-center gap-2 px-2 py-2"
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

      <aside className="pointer-events-none absolute bottom-5 left-5 top-24 z-20 flex w-[330px] flex-col gap-3">
        <div className="pointer-events-auto glass-panel p-3">
          <div className="flex items-center gap-2 rounded-2xl bg-white/[0.07] px-3 py-2">
            <Search size={16} className="text-white/50" />
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search notes, tags, folders"
              className="min-w-0 flex-1 bg-transparent text-sm outline-none placeholder:text-white/35"
            />
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            {folders.slice(0, 6).map((folder) => (
              <button key={folder} className="filter-chip">
                {folder}
              </button>
            ))}
          </div>
        </div>

        <InsightPanel payload={payload} />
      </aside>

      <aside className="pointer-events-none absolute bottom-5 right-5 top-24 z-20 flex w-[360px] flex-col gap-3">
        <div className="pointer-events-auto glass-panel p-3">
          <div className="mb-3 flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm font-medium">
              <Lock size={15} />
              On-device index
            </div>
            <button onClick={onSync} className="primary-button" disabled={syncing}>
              <WandSparkles size={15} />
              {syncing ? "Syncing" : "Sync"}
            </button>
          </div>
          <p className="text-xs leading-5 text-white/55">
            Reads Apple Notes locally, caches embeddings in SQLite, and never sends note content to external services.
          </p>
        </div>

        {mode === "time" && <TimelineScrubber value={time} onChange={setTime} />}

        <AnimatePresence mode="popLayout">
          {selected && <NotePreview note={selected} onClose={() => setSelected(null)} />}
        </AnimatePresence>
      </aside>
    </main>
  );
}
