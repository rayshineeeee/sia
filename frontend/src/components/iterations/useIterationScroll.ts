import { useCallback, useEffect, useRef, useState } from "react";
import {
  useMotionValue,
  useMotionValueEvent,
  useSpring,
  useTransform,
} from "framer-motion";
import { TOTAL_ITERATIONS } from "./data";

const WHEEL_DISTANCE = 8600;
const TOUCH_DISTANCE = 6200;

export function useIterationScroll() {
  const sceneRef = useRef<HTMLDivElement>(null);
  const touchYRef = useRef<number | null>(null);
  const [activeId, setActiveId] = useState(1);
  const targetProgress = useMotionValue(0);

  const smoothProgress = useSpring(targetProgress, {
    stiffness: 54,
    damping: 34,
    mass: 0.42,
  });

  const progressScale = useTransform(smoothProgress, [0, 1], [0.01, 1]);

  const stepProgress = useCallback(
    (delta: number, distance: number) => {
      const next = clamp(targetProgress.get() + delta / distance, 0, 1);
      targetProgress.set(next);
    },
    [targetProgress],
  );

  useEffect(() => {
    const onWheel = (event: WheelEvent) => {
      event.preventDefault();
      stepProgress(event.deltaY, WHEEL_DISTANCE);
    };

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "ArrowDown" || event.key === "PageDown") {
        event.preventDefault();
        stepProgress(190, WHEEL_DISTANCE);
      }

      if (event.key === "ArrowUp" || event.key === "PageUp") {
        event.preventDefault();
        stepProgress(-190, WHEEL_DISTANCE);
      }
    };

    const onTouchStart = (event: TouchEvent) => {
      touchYRef.current = event.touches[0]?.clientY ?? null;
    };

    const onTouchMove = (event: TouchEvent) => {
      const previousY = touchYRef.current;
      const nextY = event.touches[0]?.clientY ?? null;
      if (previousY == null || nextY == null) return;

      event.preventDefault();
      stepProgress(previousY - nextY, TOUCH_DISTANCE);
      touchYRef.current = nextY;
    };

    window.addEventListener("wheel", onWheel, { passive: false });
    window.addEventListener("keydown", onKeyDown);
    window.addEventListener("touchstart", onTouchStart, { passive: true });
    window.addEventListener("touchmove", onTouchMove, { passive: false });

    return () => {
      window.removeEventListener("wheel", onWheel);
      window.removeEventListener("keydown", onKeyDown);
      window.removeEventListener("touchstart", onTouchStart);
      window.removeEventListener("touchmove", onTouchMove);
    };
  }, [stepProgress]);

  useMotionValueEvent(smoothProgress, "change", (latest) => {
    const nextId = Math.max(
      1,
      Math.min(TOTAL_ITERATIONS, Math.round(latest * (TOTAL_ITERATIONS - 1)) + 1),
    );
    setActiveId(nextId);
  });

  return {
    activeId,
    progress: smoothProgress,
    progressScale,
    sceneRef,
  };
}

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}
