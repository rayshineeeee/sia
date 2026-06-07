"use client";

import { motion } from "framer-motion";
import type { CSSProperties } from "react";
import { ThomasAttractorPlane } from "./ThomasAttractorPlane";
import type { CarouselTuning, ExperienceVariant } from "./types";

export function StageBackdrop({
  tuning,
  variant = "v1",
}: {
  tuning: CarouselTuning;
  variant?: ExperienceVariant;
}) {
  const shaderDuration = Math.max(4, tuning.shaderSpin);
  const isThomasBackdrop = variant === "v3";

  return (
    <div className="stage-backdrop" aria-hidden="true">
      <div
        className="background-title-card"
        style={
          {
            "--title-card-opacity": tuning.titleOpacity,
            "--title-card-scale": tuning.titleScale,
            "--title-card-y": `${tuning.titleY}vh`,
          } as CSSProperties
        }
      >
        <span>deSIAgn</span>
      </div>

      <motion.div
        animate={isThomasBackdrop ? undefined : { rotate: 360 }}
        className="background-shader-plane"
        style={{
          opacity: isThomasBackdrop ? 1 : tuning.shaderOpacity,
          scale: tuning.shaderScale,
        }}
        transition={{
          duration: shaderDuration,
          ease: "linear",
          repeat: isThomasBackdrop ? 0 : Infinity,
        }}
      >
        {isThomasBackdrop ? (
          <ThomasAttractorPlane
            opacity={tuning.shaderOpacity}
            spin={tuning.shaderSpin}
          />
        ) : (
          <>
            <span />
            <span />
            <span />
          </>
        )}
      </motion.div>
    </div>
  );
}
