import type { Iteration } from "./types";

export function IterationCardFields({ iteration }: { iteration: Iteration }) {
  return (
    <>
      <span className="frame-number">{iteration.number}</span>
      <span className="frame-copy">
        <span className="frame-summary">{iteration.summary}</span>
        {iteration.renderUrl && iteration.originalPrompt ? (
          <span style={{ display: "block", fontSize: 10, opacity: 0.6, marginTop: 4 }}>
            critique → {iteration.originalPrompt.slice(0, 90)}
          </span>
        ) : null}
      </span>
    </>
  );
}
