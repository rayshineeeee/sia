import type { MotionValue } from "framer-motion";
import { iterations } from "./data";
import { IterationFrame } from "./IterationFrame";
import type { CarouselTuning, Iteration } from "./types";

export function IterationTrack({
  onSelect,
  progress,
  tuning,
}: {
  onSelect: (iteration: Iteration) => void;
  progress: MotionValue<number>;
  tuning: CarouselTuning;
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
            tuning={tuning}
          />
        ))}
      </div>
    </div>
  );
}
