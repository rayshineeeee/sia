import {
  motion,
  useTransform,
  type MotionStyle,
  type MotionValue,
} from "framer-motion";
import { TOTAL_ITERATIONS } from "./data";
import { IterationCardFields } from "./IterationCardFields";
import { IterationVisual } from "./IterationVisual";
import type { CarouselTuning, Iteration } from "./types";

export function IterationFrame({
  index,
  iteration,
  onSelect,
  progress,
  tuning,
}: {
  index: number;
  iteration: Iteration;
  onSelect: (iteration: Iteration) => void;
  progress: MotionValue<number>;
  tuning: CarouselTuning;
}) {
  const relative = useTransform(
    progress,
    (latest) => index - latest * (TOTAL_ITERATIONS - 1),
  );
  const x = useTransform(relative, (value) => {
    const position = clamp(value, -3, 7.8);
    return position * tuning.spacingX + Math.pow(position, 2) * tuning.curve;
  });
  const y = useTransform(relative, (value) => {
    const position = clamp(value, -3, 7.8);
    return position * tuning.spacingY - Math.pow(position, 2) * tuning.arc;
  });
  const scale = useTransform(relative, (value) => {
    if (value < 0) return 1 + Math.max(value, -2.2) * -0.012;
    return Math.max(0.82, 1 - value * 0.018);
  });
  const z = useTransform(relative, (value) => {
    const position = clamp(value, -2.8, 8.7);
    return position * -tuning.depth;
  });
  const zIndex = useTransform(relative, (value) => {
    const position = clamp(value, -2.8, 8.7);
    return Math.round((8.7 - position) * 100);
  });
  const opacity = useTransform(relative, (value) => {
    if (value < -2.4 || value > 8.7) return 0;
    if (value > 7) return 1 - (value - 7) * 0.42;
    if (value < -1.4) return 1 - Math.abs(value + 1.4) * 0.5;
    return 1;
  });
  const pointerEvents = useTransform(relative, (value) =>
    value > -2.2 && value < 6.8 ? "auto" : "none",
  );
  const frameStyle: MotionStyle = {
    opacity,
    pointerEvents,
    scale,
    x,
    y,
    z,
    zIndex,
  };

  return (
    <motion.div className="iteration-frame" style={frameStyle}>
      <button
        className="iteration-surface"
        onClick={() => onSelect(iteration)}
        type="button"
      >
        <IterationVisual iteration={iteration} />
        <IterationCardFields iteration={iteration} />
      </button>
    </motion.div>
  );
}

function clamp(value: number, min: number, max: number) {
  const safeValue = Number.isFinite(value) ? value : 0;
  return Math.min(max, Math.max(min, safeValue));
}
