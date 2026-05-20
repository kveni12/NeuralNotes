import { motion } from "framer-motion";
import { Rewind, StepForward } from "lucide-react";

type Props = {
  value: number;
  onChange: (value: number) => void;
};

export function TimelineScrubber({ value, onChange }: Props) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="pointer-events-auto glass-panel p-4"
    >
      <div className="mb-3 flex items-center justify-between text-sm font-medium">
        <span>Time evolution</span>
        <span className="text-xs text-white/45">{value}%</span>
      </div>
      <div className="flex items-center gap-3">
        <button className="icon-button" title="Rewind timeline" onClick={() => onChange(Math.max(0, value - 10))}>
          <Rewind size={15} />
        </button>
        <input
          aria-label="Timeline"
          type="range"
          min="0"
          max="100"
          value={value}
          onChange={(event) => onChange(Number(event.target.value))}
          className="accent-neural-cyan min-w-0 flex-1"
        />
        <button className="icon-button" title="Step forward" onClick={() => onChange(Math.min(100, value + 10))}>
          <StepForward size={15} />
        </button>
      </div>
    </motion.div>
  );
}
