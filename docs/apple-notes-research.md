# Apple Notes Storage Research

As of modern macOS releases, the primary local Notes database is commonly stored at:

```text
~/Library/Group Containers/group.com.apple.notes/NoteStore.sqlite
```

Important implementation notes:

- Rich note bodies are not reliably plain text in a simple table. Newer schemas use compressed/protobuf-backed payloads, often associated with `ZICNOTEDATA` and related CloudKit/Core Data tables.
- The database path normally also has `NoteStore.sqlite-shm` and `NoteStore.sqlite-wal`; a production reader should open SQLite read-only and avoid mutating or locking Apple’s live store.
- Full fidelity parsing is best delegated to maintained tooling where possible.
- AppleScript is a useful fallback for plain text, but it is slower, may prompt for automation permissions, and can be less complete for attachments and rich formatting.

## Chosen Strategy

NeuralNotes uses three local-only readers in order:

1. `apple-notes-parser`, a Python package that parses modern Apple Notes SQLite stores, protobuf note data, tags, folders, and attachment metadata.
2. A conservative read-only SQLite fallback that extracts titles/folders/timestamps when full body parsing is unavailable.
3. AppleScript fallback through the Notes app for plaintext note content.

This approach keeps the app useful during development while leaving a narrow surface for future schema-specific hardening.

## References

- `apple-notes-parser` PyPI project: https://pypi.org/project/apple-notes-parser/
- Apple Notes database parser discussion and path history: https://github.com/ChrLipp/notes-import
- Apple Notes Exporter, a Swift/macOS exporter using database-driven parsing: https://github.com/kzaremski/apple-notes-exporter
- Obsidian importer Apple Notes implementation notes: https://deepwiki.com/obsidianmd/obsidian-importer/3.4-bear/
