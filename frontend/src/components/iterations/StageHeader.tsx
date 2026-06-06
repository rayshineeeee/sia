import { TOTAL_ITERATIONS } from "./data";
import type { Iteration } from "./types";

export function StageHeader({
  activeIteration,
}: {
  activeIteration: Iteration;
}) {
  return (
    <header className="app-bar">
      <div className="brand-lockup">SIA</div>
      <div className="active-readout" aria-live="polite">
        <span>{activeIteration.number}</span>
        <span>/ {TOTAL_ITERATIONS}</span>
      </div>
    </header>
  );
}
