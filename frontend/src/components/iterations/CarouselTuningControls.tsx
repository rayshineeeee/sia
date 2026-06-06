"use client";

import type { CarouselTuning } from "./types";

const controls: Array<{
  key: keyof CarouselTuning;
  label: string;
  max: number;
  min: number;
  step: number;
  valueFromTuning?: (tuning: CarouselTuning) => number;
  valueToTuning?: (value: number) => Partial<CarouselTuning>;
}> = [
  { key: "spacingX", label: "spacing", min: 120, max: 900, step: 5 },
  {
    key: "spacingY",
    label: "rise",
    min: 0,
    max: 280,
    step: 2,
    valueFromTuning: (tuning) => Math.abs(tuning.spacingY),
    valueToTuning: (value) => ({ spacingY: -value }),
  },
  { key: "arc", label: "arc", min: 0, max: 40, step: 0.2 },
  { key: "curve", label: "curve", min: -24, max: 72, step: 0.2 },
  { key: "depth", label: "depth", min: 0, max: 220, step: 2 },
  { key: "panelWidth", label: "width", min: 30, max: 118, step: 1 },
  { key: "trackTop", label: "height", min: -8, max: 88, step: 1 },
  { key: "cameraY", label: "camera", min: -30, max: 130, step: 1 },
  { key: "rotateX", label: "tilt x", min: -48, max: 48, step: 1 },
  { key: "rotateY", label: "tilt y", min: -68, max: 32, step: 1 },
  { key: "rotateZ", label: "tilt z", min: -28, max: 28, step: 0.2 },
  { key: "titleScale", label: "title size", min: 0.4, max: 2.4, step: 0.05 },
  { key: "titleOpacity", label: "title fade", min: 0, max: 0.34, step: 0.01 },
  { key: "titleY", label: "title y", min: -32, max: 42, step: 1 },
  { key: "shaderScale", label: "shader size", min: 0.25, max: 2.8, step: 0.05 },
  { key: "shaderOpacity", label: "shader opacity", min: 0, max: 1, step: 0.01 },
  { key: "shaderSpin", label: "shader spin", min: 4, max: 96, step: 1 },
];

export function CarouselTuningControls({
  onChange,
  tuning,
}: {
  onChange: (next: CarouselTuning) => void;
  tuning: CarouselTuning;
}) {
  return (
    <div className="tuning-controls" aria-label="Carousel tuning controls">
      <div className="tuning-title">Tuning</div>
      {controls.map((control) => (
        <label className="tuning-control" key={control.label}>
          <span>{control.label}</span>
          <input
            max={control.max}
            min={control.min}
            onChange={(event) =>
              onChange({
                ...tuning,
                ...(control.valueToTuning
                  ? control.valueToTuning(Number(event.target.value))
                  : { [control.key]: Number(event.target.value) }),
              })
            }
            step={control.step}
            type="range"
            value={
              control.valueFromTuning
                ? control.valueFromTuning(tuning)
                : tuning[control.key]
            }
          />
          <span>
            {formatValue(
              control.valueFromTuning
                ? control.valueFromTuning(tuning)
                : tuning[control.key],
            )}
          </span>
        </label>
      ))}
      <button className="tuning-export" onClick={() => exportJson(tuning)} type="button">
        Export JSON Details
      </button>
    </div>
  );
}

function formatValue(value: number) {
  const safeValue = Number.isFinite(value) ? value : 0;
  return Number.isInteger(safeValue) ? String(safeValue) : safeValue.toFixed(1);
}

function exportJson(tuning: CarouselTuning) {
  const payload = {
    exportedAt: new Date().toISOString(),
    tuning: {
      ...tuning,
      rise: Math.abs(tuning.spacingY),
    },
  };
  const json = JSON.stringify(payload, null, 2);
  const blob = new Blob([json], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");

  void navigator.clipboard?.writeText(json).catch(() => undefined);
  anchor.download = "sia-carousel-tuning.json";
  anchor.href = url;
  anchor.click();
  URL.revokeObjectURL(url);
}
