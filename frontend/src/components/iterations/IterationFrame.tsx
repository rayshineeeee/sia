"use client";

import { useState } from "react";
import {
  motion,
  useMotionValueEvent,
  useTransform,
  type MotionStyle,
  type MotionValue,
} from "framer-motion";
import { TOTAL_ITERATIONS } from "./data";
import { IterationCardFields } from "./IterationCardFields";
import { IterationVisual } from "./IterationVisual";
import { ShaderTile } from "./ShaderTile";
import type { CarouselTuning, ExperienceVariant, Iteration } from "./types";

export function IterationFrame({
  index,
  iteration,
  onSelect,
  progress,
  selected,
  tuning,
  variant = "v1",
}: {
  index: number;
  iteration: Iteration;
  onSelect: (iteration: Iteration) => void;
  progress: MotionValue<number>;
  selected: boolean;
  tuning: CarouselTuning;
  variant?: ExperienceVariant;
}) {
  const [shaderActive, setShaderActive] = useState(index < 7);
  const relative = useTransform(
    progress,
    (latest) => index - latest * (TOTAL_ITERATIONS - 1),
  );
  useMotionValueEvent(relative, "change", (value) => {
    const nextActive = value > -2.2 && value < 7.4;
    setShaderActive((current) => (current === nextActive ? current : nextActive));
  });

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
    zIndex: selected ? 2400 : zIndex,
  };

  return (
    <motion.div className="iteration-frame" style={frameStyle}>
      <button
        aria-pressed={selected}
        className="iteration-surface"
        data-selected={selected ? "true" : "false"}
        onClick={() => onSelect(iteration)}
        type="button"
      >
        {variant === "v2" ? (
          <ShaderTile active={shaderActive} iteration={iteration} />
        ) : (
          <IterationVisual iteration={iteration} />
        )}
        <IterationCardFields iteration={iteration} />
      </button>
    </motion.div>
  );
}

function clamp(value: number, min: number, max: number) {
  const safeValue = Number.isFinite(value) ? value : 0;
  return Math.min(max, Math.max(min, safeValue));
}
