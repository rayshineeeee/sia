"use client";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type CSSProperties,
  type PointerEvent,
} from "react";
import { motion } from "framer-motion";
import { IterationDetailOverlay } from "@/components/iterations/IterationDetailOverlay";
import { IterationTrack } from "@/components/iterations/IterationTrack";
import { StageBackdrop } from "@/components/iterations/StageBackdrop";
import { StageHeader } from "@/components/iterations/StageHeader";
import { TuningGate } from "@/components/iterations/TuningGate";
import { getIteration } from "@/components/iterations/data";
import { getDefaultCarouselTuning } from "@/components/iterations/tuning";
import { useIterationScroll } from "@/components/iterations/useIterationScroll";
import type { ExperienceVariant, Iteration } from "@/components/iterations/types";

export function IterationExperience({
  variant = "v1",
}: {
  variant?: ExperienceVariant;
}) {
  const [detailOpen, setDetailOpen] = useState(false);
  const [detailBaseId, setDetailBaseId] = useState(1);
  const [selectedIterationId, setSelectedIterationId] = useState<number | null>(null);
  const [tuningOpen, setTuningOpen] = useState(false);
  const baseTuning = getDefaultCarouselTuning(variant);
  const [tuning, setTuning] = useState(() => baseTuning);
  const experienceRef = useRef<HTMLElement>(null);
  const { activeId, progress, progressScale, sceneRef } = useIterationScroll();

  const activeIteration = getIteration(activeId);
  const resolvedTuning = { ...baseTuning, ...tuning };

  const handleIterationPress = useCallback(
    (iteration: Iteration) => {
      if (selectedIterationId === iteration.id) {
        setDetailBaseId(iteration.id);
        setDetailOpen(true);
        return;
      }

      setSelectedIterationId(iteration.id);
    },
    [selectedIterationId],
  );

  const handleExperiencePointerDown = useCallback(
    (event: PointerEvent<HTMLElement>) => {
      if (!selectedIterationId || detailOpen) return;

      const target = event.target;
      if (!(target instanceof Element)) return;

      const interactiveTarget = target.closest(
        ".iteration-surface, .tuning-trigger, .tuning-controls, .detail-overlay",
      );

      if (!interactiveTarget) {
        setSelectedIterationId(null);
      }
    },
    [detailOpen, selectedIterationId],
  );

  useEffect(() => {
    const frame = window.requestAnimationFrame(() => {
      experienceRef.current?.focus({ preventScroll: true });
    });

    return () => window.cancelAnimationFrame(frame);
  }, []);

  return (
    <main
      className={`experience experience-${variant}`}
      onPointerDownCapture={handleExperiencePointerDown}
      ref={experienceRef}
      style={
        {
          "--camera-origin-y": `${resolvedTuning.cameraY}%`,
          "--panel-width": `${resolvedTuning.panelWidth}vw`,
          "--surface-rotate-x": `${resolvedTuning.rotateX}deg`,
          "--surface-rotate-y": `${resolvedTuning.rotateY}deg`,
          "--surface-rotate-z": `${resolvedTuning.rotateZ}deg`,
          "--track-top": `${resolvedTuning.trackTop}vh`,
        } as CSSProperties
      }
      tabIndex={-1}
    >
      <motion.div
        animate={{ opacity: 0, scale: 1.03 }}
        className="intro-wash"
        initial={{ opacity: 1, scale: 1 }}
        transition={{ duration: 1.55, ease: [0.22, 1, 0.36, 1] }}
      />

      <section className="scroll-scene" ref={sceneRef}>
        <div className="sticky-stage">
          <StageHeader activeIteration={activeIteration} />

          <div className="stage-plane" aria-hidden="true" />
          <StageBackdrop tuning={resolvedTuning} variant={variant} />

          <IterationTrack
            onSelect={handleIterationPress}
            progress={progress}
            selectedId={selectedIterationId}
            tuning={resolvedTuning}
            variant={variant}
          />

          <div className="progress-rail" aria-hidden="true">
            <motion.span style={{ scaleX: progressScale }} />
          </div>
        </div>
      </section>
      <TuningGate
        onChange={setTuning}
        onOpenChange={setTuningOpen}
        open={tuningOpen}
        tuning={resolvedTuning}
      />

      {detailOpen ? (
        <IterationDetailOverlay
          baseId={detailBaseId}
          key={detailBaseId}
          onClose={() => setDetailOpen(false)}
          variant={variant}
        />
      ) : null}
    </main>
  );
}
