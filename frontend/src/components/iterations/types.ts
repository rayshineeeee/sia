export type Iteration = {
  id: number;
  label: string;
  number: string;
  summary: string;
  title: string;
};

export type ViewportState = {
  frameWidth: number;
  gap: number;
  height: number;
  width: number;
};

export type CarouselTuning = {
  arc: number;
  cameraY: number;
  curve: number;
  depth: number;
  panelWidth: number;
  rotateX: number;
  rotateY: number;
  rotateZ: number;
  shaderOpacity: number;
  shaderScale: number;
  shaderSpin: number;
  spacingX: number;
  spacingY: number;
  titleOpacity: number;
  titleScale: number;
  titleY: number;
  trackTop: number;
};
