"use client";

import { motion } from "framer-motion";
import type { CSSProperties } from "react";
import type { CarouselTuning } from "./types";

export function StageBackdrop({ tuning }: { tuning: CarouselTuning }) {
  const shaderDuration = Math.max(4, tuning.shaderSpin);

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
        <span>SIA</span>
      </div>

      <motion.div
        animate={{ rotate: 360 }}
        className="background-shader-plane"
        style={{
          opacity: tuning.shaderOpacity,
          scale: tuning.shaderScale,
        }}
        transition={{
          duration: shaderDuration,
          ease: "linear",
          repeat: Infinity,
        }}
      >
        <span />
        <span />
        <span />
      </motion.div>
    </div>
  );
}
