# NeuralNotes

NeuralNotes is a native-feeling macOS app that turns Apple Notes into an interactive semantic knowledge galaxy. Notes stay local, embeddings are cached on device, and the UI is built around a smooth dark-space visualization inspired by Apple-native software.

## What It Does

- Indexes Apple Notes from local macOS storage.
- Embeds note text locally with `sentence-transformers`.
- Caches notes, embeddings, layout coordinates, clusters, and graph edges in SQLite.
- Projects notes into a semantic 2D space with UMAP/PCA.
- Clusters related notes with HDBSCAN/KMeans.
- Renders notes as glowing galaxy nodes with D3, React, TypeScript, TailwindCSS, and Framer Motion.
- Supports galaxy, time-evolution, and knowledge-graph modes.
- Falls back to polished sample data when Apple Notes permissions or dependencies are unavailable.

## Architecture

```text
NeuralNotes/
  apps/desktop/          React + TypeScript + Tauri app
  backend/               FastAPI local indexing service
  docs/                  Research notes and implementation plan
  sample-data/           Reserved for local exports, fixtures, and experiments
```

The desktop app talks only to `http://127.0.0.1:8717`. There is no cloud API and no external note upload path.

## Apple Notes Integration

Modern macOS stores Notes data at:

```text
~/Library/Group Containers/group.com.apple.notes/NoteStore.sqlite
```

NeuralNotes uses a layered reader:

1. `apple-notes-parser` for modern SQLite/protobuf note parsing, tags, folders, and attachment metadata.
2. Read-only SQLite metadata fallback for titles, folders, and timestamps.
3. AppleScript fallback for plain-text note access through the Notes app.

The SQLite body payload in recent macOS versions can involve compressed protobuf data, so the app keeps that parsing isolated in `backend/app/services/apple_notes.py`.

## Local Development

Install desktop dependencies:

```bash
cd NeuralNotes
npm install
npm --prefix apps/desktop install
```

Create the Python environment:

```bash
cd NeuralNotes/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Seed the local index:

```bash
cd NeuralNotes/backend
source .venv/bin/activate
PYTHONPATH=. python scripts/index_once.py
```

Run the API and desktop frontend:

```bash
cd NeuralNotes
npm run dev
```

Run the Tauri app:

```bash
cd NeuralNotes
npm run tauri -- dev
```

## Performance Plan For 10k+ Notes

- Incremental sync based on content hashes and updated timestamps.
- Embedding cache keyed by Apple Notes identifier.
- Edge limit and similarity threshold to avoid graph clutter.
- Progressive rendering: draw nodes first, then graph edges and labels.
- Semantic zoom: labels and larger interaction targets appear only when useful.
- Cluster-level summaries for low zoom; note-level details for high zoom.

## Privacy Model

- Notes are read from local macOS storage.
- The index lives in `~/Library/Application Support/NeuralNotes/index.sqlite`.
- The embedding model runs locally.
- No note content is sent to a network service.
- The app can be developed and used offline after dependencies and model files are installed.

## Portfolio-Ready Roadmap

- Add macOS permission onboarding for Notes database access.
- Replace sample fallback with first-run guided Apple Notes sync.
- Add vector search route with nearest-neighbor highlighting.
- Add local LLM summarization via Ollama or MLX.
- Add entity extraction for people/projects/topics.
- Add daily note evolution playback export.
- Add bridge-note detection using graph betweenness centrality.
