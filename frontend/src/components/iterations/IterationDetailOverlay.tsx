"use client";

import { useEffect, useMemo, useState } from "react";
import { X } from "lucide-react";
import { getComparisonPeer, getIteration, iterations } from "./data";
import { IterationCardFields } from "./IterationCardFields";
import { IterationVisual } from "./IterationVisual";
import { ShaderTile } from "./ShaderTile";
import type { ExperienceVariant } from "./types";

export function IterationDetailOverlay({
  baseId,
  onClose,
  variant = "v1",
}: {
  baseId: number;
  onClose: () => void;
  variant?: ExperienceVariant;
}) {
  const [selectedId, setSelectedId] = useState(baseId);
  const [considerId, setConsiderId] = useState(getComparisonPeer(baseId));
  const selectedIteration = useMemo(() => getIteration(selectedId), [selectedId]);
  const considerIteration = useMemo(() => getIteration(considerId), [considerId]);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onClose]);

  return (
    <section
      aria-label="Iteration detail"
      aria-modal="true"
      className="detail-overlay"
      role="dialog"
    >
      <button className="detail-tab" type="button">
        {considerIteration.label} {considerIteration.number}
      </button>

      <button
        aria-label="Close detail"
        className="detail-close"
        onClick={onClose}
        type="button"
      >
        <X aria-hidden="true" size={17} />
      </button>

      <div className="detail-stage">
        <article className="detail-panel">
          {variant === "v2" ? (
            <ShaderTile active iteration={selectedIteration} />
          ) : (
            <IterationVisual iteration={selectedIteration} large />
          )}
          <IterationCardFields iteration={selectedIteration} />
        </article>
      </div>

      <section className="detail-prompts" aria-label="Prompt history">
        <article className="detail-prompt">
          <h2>Original Prompt</h2>
          <p>{selectedIteration.originalPrompt}</p>
        </article>
        <article className="detail-prompt">
          <h2>Refined Prompt</h2>
          <p>{selectedIteration.refinedPrompt}</p>
        </article>
      </section>

      <footer className="detail-controls">
        <label className="detail-range">
          <span>{selectedIteration.label}</span>
          <input
            aria-label="Select iteration"
            max={iterations.length}
            min={1}
            onChange={(event) => setSelectedId(Number(event.target.value))}
            type="range"
            value={selectedId}
          />
          <span>{selectedIteration.number}</span>
        </label>

        <label className="detail-select">
          <span>Consider</span>
          <select
            aria-label="Consider another iteration"
            onChange={(event) => setConsiderId(Number(event.target.value))}
            value={considerId}
          >
            {iterations.map((iteration) => (
              <option key={iteration.id} value={iteration.id}>
                {iteration.label} {iteration.number}
              </option>
            ))}
          </select>
        </label>
      </footer>
    </section>
  );
}
