import type { Iteration } from "./types";

export const TOTAL_ITERATIONS = 100;

const descriptions = [
  "Quieter recovery loop.",
  "Compressed task context.",
  "Feedback routed into rewrite.",
  "Reduced tool calls.",
  "Stable harness update.",
  "Tighter scoring format.",
  "Failure signal preserved.",
  "Shorter execution path.",
];

export const iterations: Iteration[] = Array.from(
  { length: TOTAL_ITERATIONS },
  (_, index) => {
    const id = index + 1;

    return {
      id,
      label: "Iteration",
      number: padIteration(id),
      summary: descriptions[index % descriptions.length],
      title: `Iteration ${padIteration(id)}`,
    };
  },
);

export function getIteration(id: number) {
  return iterations[Math.max(0, Math.min(iterations.length - 1, id - 1))];
}

export function getComparisonPeer(id: number) {
  return id === TOTAL_ITERATIONS ? TOTAL_ITERATIONS - 1 : id + 1;
}

export function padIteration(id: number) {
  return String(id).padStart(3, "0");
}
