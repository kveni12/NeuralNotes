import { Archive, Eye, FileStack } from "lucide-react";
import type { ReactNode } from "react";
import type { NoteNode } from "../lib/types";

type Props = {
  notes: NoteNode[];
  onPreview: (note: NoteNode) => void;
};

export function TriagePanel({ notes, onPreview }: Props) {
  const reviewableNotes = notes.filter((note) => !looksSensitive(note));

  const condense = [...reviewableNotes]
    .filter((note) => note.body.length > 850 || (note.score > 0.16 && note.body.length > 520))
    .sort((a, b) => b.body.length + b.score * 1200 - (a.body.length + a.score * 1200))
    .slice(0, 4);

  const archive = [...reviewableNotes]
    .filter((note) => {
      const updated = Date.parse(note.updatedAt);
      const isOld = Number.isFinite(updated) && Date.now() - updated > 180 * 86400_000;
      const isThin = note.body.trim().length < 90 || note.title.trim().length < 8;
      return isOld && (isThin || note.score < 0.04);
    })
    .sort((a, b) => a.body.length - b.body.length)
    .slice(0, 4);

  if (!condense.length && !archive.length) return null;

  return (
    <div className="pointer-events-auto glass-panel compact-panel triage-panel">
      <div className="panel-row mb-2">
        <span>Review suggestions</span>
        <Archive size={14} />
      </div>

      {condense.length > 0 && (
        <SuggestionGroup icon={<FileStack size={14} />} label="Condense candidates" notes={condense} onPreview={onPreview} />
      )}

      {archive.length > 0 && (
        <SuggestionGroup icon={<Archive size={14} />} label="Archive candidates" notes={archive} onPreview={onPreview} />
      )}
    </div>
  );
}

function looksSensitive(note: NoteNode) {
  const text = `${note.title} ${note.body}`.toLowerCase();
  if (/[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}/i.test(text)) return true;
  if (/\b[a-z ]{2,24}number\s*:/i.test(text)) return true;
  return /\b(social security|ssn|passport|driver'?s license|membership number|api key|token|secret|password|card number|routing number|account number)\b/.test(
    text
  );
}

function SuggestionGroup({
  icon,
  label,
  notes,
  onPreview
}: {
  icon: ReactNode;
  label: string;
  notes: NoteNode[];
  onPreview: (note: NoteNode) => void;
}) {
  return (
    <section className="triage-group">
      <div className="triage-heading">
        {icon}
        <span>{label}</span>
      </div>
      <div className="triage-list">
        {notes.map((note) => (
          <button key={`${label}-${note.id}`} className="triage-item" onClick={() => onPreview(note)}>
            <span className="triage-copy">
              <span className="triage-title">{note.title}</span>
              <span className="triage-meta">
                {note.clusterLabel} • {note.body.length.toLocaleString()} chars
              </span>
            </span>
            <span className="triage-action">
              <Eye size={13} />
              View
            </span>
          </button>
        ))}
      </div>
    </section>
  );
}
