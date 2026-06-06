"use client";

import {
  useCallback,
  useEffect,
  useRef,
  type Dispatch,
  type MouseEvent,
  type PointerEvent,
  type SetStateAction,
} from "react";
import { motion } from "framer-motion";
import { CarouselTuningControls } from "./CarouselTuningControls";
import type { CarouselTuning } from "./types";

export function TuningGate({
  onChange,
  onOpenChange,
  open,
  tuning,
}: {
  onChange: (next: CarouselTuning) => void;
  onOpenChange: Dispatch<SetStateAction<boolean>>;
  open: boolean;
  tuning: CarouselTuning;
}) {
  const pointerHandledRef = useRef(false);

  const toggle = useCallback(() => {
    onOpenChange((current) => !current);
  }, [onOpenChange]);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onOpenChange(false);
        return;
      }

      if (
        isTypingTarget(event.target) ||
        event.metaKey ||
        event.ctrlKey ||
        event.altKey ||
        (event.key.toLowerCase() !== "p" && event.code !== "KeyP")
      ) {
        return;
      }

      event.preventDefault();
      toggle();
    };

    document.addEventListener("keydown", onKeyDown, true);
    return () => document.removeEventListener("keydown", onKeyDown, true);
  }, [onOpenChange, toggle]);

  const onPointerDown = useCallback(
    (event: PointerEvent<HTMLButtonElement>) => {
      pointerHandledRef.current = true;
      event.preventDefault();
      toggle();
    },
    [toggle],
  );

  const onClick = useCallback(
    (event: MouseEvent<HTMLButtonElement>) => {
      if (pointerHandledRef.current) {
        pointerHandledRef.current = false;
        return;
      }

      event.preventDefault();
      toggle();
    },
    [toggle],
  );

  return (
    <>
      <button
        aria-expanded={open}
        aria-label="Toggle tuning panel"
        className="tuning-trigger"
        onClick={onClick}
        onPointerDown={onPointerDown}
        type="button"
      >
        P
      </button>

      {open ? (
        <motion.div
          animate={{ filter: "blur(0px)", opacity: 1, y: 0 }}
          className="tuning-panel-motion"
          initial={{ filter: "blur(8px)", opacity: 0, y: -8 }}
          transition={{ duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
        >
          <CarouselTuningControls onChange={onChange} tuning={tuning} />
        </motion.div>
      ) : null}
    </>
  );
}

function isTypingTarget(target: EventTarget | null) {
  if (!(target instanceof HTMLElement)) return false;

  const tagName = target.tagName.toLowerCase();
  if (target instanceof HTMLInputElement) {
    return !["button", "checkbox", "radio", "range"].includes(target.type);
  }

  return (
    tagName === "select" ||
    tagName === "textarea" ||
    target.isContentEditable
  );
}
