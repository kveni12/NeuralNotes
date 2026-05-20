import { motion } from "framer-motion";
import { Clock3, Folder, X } from "lucide-react";
import type { NoteNode } from "../lib/types";

type Props = {
  note: NoteNode;
  onClose: () => void;
};

export function NotePreview({ note, onClose }: Props) {
  return (
    <motion.div
      layout
      initial={{ opacity: 0, x: 14 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 14 }}
      className="pointer-events-auto glass-panel max-h-[44vh] overflow-hidden p-4"
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold leading-6">{note.title}</h2>
          <div className="mt-2 flex flex-wrap gap-2 text-[11px] text-white/50">
            <span className="inline-flex items-center gap-1">
              <Folder size={12} />
              {note.folder}
            </span>
            <span className="inline-flex items-center gap-1">
              <Clock3 size={12} />
              {new Date(note.updatedAt).toLocaleDateString()}
            </span>
          </div>
        </div>
        <button onClick={onClose} className="icon-button" title="Close preview">
          <X size={15} />
        </button>
      </div>
      <p className="mt-4 max-h-[20vh] overflow-auto pr-1 text-sm leading-6 text-white/68">{note.body}</p>
      <div className="mt-4 flex flex-wrap gap-2">
        {note.tags.map((tag) => (
          <span key={tag} className="filter-chip">
            #{tag}
          </span>
        ))}
      </div>
    </motion.div>
  );
}
