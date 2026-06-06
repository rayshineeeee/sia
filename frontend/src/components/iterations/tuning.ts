import type { CarouselTuning, ExperienceVariant } from "./types";

export const defaultCarouselTuning: CarouselTuning = {
  arc: 10.6,
  cameraY: 70,
  curve: 13.8,
  depth: 30,
  panelWidth: 46,
  rotateX: -27,
  rotateY: -39,
  rotateZ: -0.2,
  shaderOpacity: 0.05,
  shaderScale: 2.05,
  shaderSpin: 15,
  spacingX: 280,
  spacingY: -170,
  titleOpacity: 0.12,
  titleScale: 1,
  titleY: -32,
  trackTop: 20,
};

export const defaultV3CarouselTuning: CarouselTuning = {
  ...defaultCarouselTuning,
  shaderOpacity: 0.72,
  shaderScale: 1.15,
  shaderSpin: 28,
};

export function getDefaultCarouselTuning(variant: ExperienceVariant) {
  return variant === "v3" ? defaultV3CarouselTuning : defaultCarouselTuning;
}
