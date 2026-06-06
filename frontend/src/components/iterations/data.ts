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

const originalPrompts = [
  "Review the current run, keep the user constraints intact, and produce the next iteration.",
  "Compress the task context without losing the interaction goals or visual direction.",
  "Route the feedback into a cleaner card stack and preserve the scrolling behavior.",
  "Reduce tool noise while keeping the frontend preview editable and inspectable.",
];

const refinedPrompts = [
  "Prioritize the visible card state, keep labels minimal, and preserve the train-like depth.",
  "Summarize the active constraints, isolate the UI change, and return a focused iteration.",
  "Keep the card primitive reusable while making the selection behavior explicit.",
  "Use the existing visual system and avoid adding extra copy beyond the requested fields.",
];

export const iterations: Iteration[] = Array.from(
  { length: TOTAL_ITERATIONS },
  (_, index) => {
    const id = index + 1;

    return {
      id,
      label: "Iteration",
      number: padIteration(id),
      originalPrompt: originalPrompts[index % originalPrompts.length],
      refinedPrompt: refinedPrompts[index % refinedPrompts.length],
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
  return String(id);
}
