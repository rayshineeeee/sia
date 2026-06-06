import { useMemo } from "react";
import type { Iteration } from "./types";

export function IterationVisual({
  iteration,
  large = false,
}: {
  iteration: Iteration;
  large?: boolean;
}) {
  const points = useMemo(() => buildPoints(iteration.id), [iteration.id]);
  const path = points
    .slice(0, 9)
    .map((point, index) => `${index === 0 ? "M" : "L"} ${point.x} ${point.y}`)
    .join(" ");

  return (
    <svg
      aria-hidden="true"
      className={`iteration-visual ${large ? "iteration-visual-large" : ""}`}
      viewBox="0 0 640 360"
    >
      <path className="visual-path" d={path} />
      {points.map((point, index) => (
        <circle
          className="visual-point"
          cx={point.x}
          cy={point.y}
          key={`${point.x}-${point.y}-${index}`}
          r={point.r}
        />
      ))}
    </svg>
  );
}

function buildPoints(seed: number) {
  return Array.from({ length: 14 }, (_, index) => {
    const x = 84 + ((seed * 41 + index * 73) % 472);
    const y = 62 + ((seed * 31 + index * 43) % 218);
    const r = index % 5 === 0 ? 3.1 : 2.25;

    return { r, x, y };
  }).sort((a, b) => a.x - b.x);
}
