"use client";

import { useCallback, useEffect, useRef, useState, type CSSProperties } from "react";
import { motion } from "framer-motion";
import { IterationDetailOverlay } from "@/components/iterations/IterationDetailOverlay";
import { IterationTrack } from "@/components/iterations/IterationTrack";
import { StageBackdrop } from "@/components/iterations/StageBackdrop";
import { StageHeader } from "@/components/iterations/StageHeader";
import { TuningGate } from "@/components/iterations/TuningGate";
import { getIteration } from "@/components/iterations/data";
import { defaultCarouselTuning } from "@/components/iterations/tuning";
import { useIterationScroll } from "@/components/iterations/useIterationScroll";
import type { Iteration } from "@/components/iterations/types";

export function IterationExperience() {
  const [detailOpen, setDetailOpen] = useState(false);
  const [detailBaseId, setDetailBaseId] = useState(1);
  const [tuningOpen, setTuningOpen] = useState(false);
  const [tuning, setTuning] = useState(defaultCarouselTuning);
  const experienceRef = useRef<HTMLElement>(null);
  const { activeId, progress, progressScale, sceneRef } = useIterationScroll();

  const activeIteration = getIteration(activeId);
  const resolvedTuning = { ...defaultCarouselTuning, ...tuning };

  const openDetail = useCallback((iteration: Iteration) => {
    setDetailBaseId(iteration.id);
    setDetailOpen(true);
  }, []);

  useEffect(() => {
    const frame = window.requestAnimationFrame(() => {
      experienceRef.current?.focus({ preventScroll: true });
    });

    return () => window.cancelAnimationFrame(frame);
  }, []);

  return (
    <main
      className="experience"
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
          <StageBackdrop tuning={resolvedTuning} />

          <IterationTrack
            onSelect={openDetail}
            progress={progress}
            tuning={resolvedTuning}
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
        />
      ) : null}
    </main>
  );
}
