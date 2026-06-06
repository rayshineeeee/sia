import type { MotionValue } from "framer-motion";
import { iterations } from "./data";
import { IterationFrame } from "./IterationFrame";
import type { CarouselTuning, ExperienceVariant, Iteration } from "./types";

export function IterationTrack({
  onSelect,
  progress,
  selectedId,
  tuning,
  variant = "v1",
}: {
  onSelect: (iteration: Iteration) => void;
  progress: MotionValue<number>;
  selectedId: number | null;
  tuning: CarouselTuning;
  variant?: ExperienceVariant;
}) {
  return (
    <div className="carousel-viewport">
      <div className="iteration-shadow" aria-hidden="true" />
      <div className="iteration-track">
        {iterations.map((iteration, index) => (
          <IterationFrame
            index={index}
            iteration={iteration}
            key={iteration.id}
            onSelect={onSelect}
            progress={progress}
            selected={selectedId === iteration.id}
            tuning={tuning}
            variant={variant}
          />
        ))}
      </div>
    </div>
  );
}
