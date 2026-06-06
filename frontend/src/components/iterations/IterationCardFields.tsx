import type { Iteration } from "./types";

export function IterationCardFields({ iteration }: { iteration: Iteration }) {
  return (
    <span className="frame-copy">
      <span className="frame-label">{iteration.label}</span>
      <span className="frame-number">{iteration.number}</span>
      <span className="frame-summary">{iteration.summary}</span>
    </span>
  );
}
