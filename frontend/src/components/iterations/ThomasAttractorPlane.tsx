"use client";

import { useEffect, useRef } from "react";
import { computeThomasAttractor } from "./thomasAttractor";

const LINE_POINT_COUNT = 36000;
const BACKGROUND_COLOR = "#f7f7f3";
const LINE_COLOR = "rgba(10, 10, 10, 0.62)";

export function ThomasAttractorPlane({
  opacity = 0.76,
  spin = 28,
}: {
  opacity?: number;
  spin?: number;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const context = canvas.getContext("2d", {
      alpha: false,
      desynchronized: true,
    });
    if (!context) return;

    const points = computeThomasAttractor({
      scale: 2.15,
      seed: 1,
      total: LINE_POINT_COUNT,
    });

    let frame = 0;
    const startedAt = performance.now();

    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      const pixelScale = Math.min(window.devicePixelRatio || 1, 2);
      const width = Math.max(1, Math.round(rect.width * pixelScale));
      const height = Math.max(1, Math.round(rect.height * pixelScale));

      if (canvas.width !== width || canvas.height !== height) {
        canvas.width = width;
        canvas.height = height;
      }

      return { height, pixelScale, width };
    };

    const render = () => {
      const { height, pixelScale, width } = resize();
      const time = (performance.now() - startedAt) / 1000;
      const speed = 7 / Math.max(spin, 1);
      const yaw = time * speed;
      const pitch = 0.7 + Math.sin(time * speed * 0.45) * 0.1;
      const sinYaw = Math.sin(yaw);
      const cosYaw = Math.cos(yaw);
      const sinPitch = Math.sin(pitch);
      const cosPitch = Math.cos(pitch);
      const size = Math.min(width, height) * 0.78;
      const centerX = width * 0.22;
      const centerY = height * 0.56;

      context.fillStyle = BACKGROUND_COLOR;
      context.fillRect(0, 0, width, height);
      context.lineCap = "round";
      context.lineJoin = "round";
      context.lineWidth = Math.max(0.8, pixelScale * 0.9);
      context.globalAlpha = Math.max(0, Math.min(1, opacity)) * 0.52;
      context.strokeStyle = LINE_COLOR;
      context.beginPath();

      for (let index = 0; index < points.length; index += 6) {
        const x = points[index];
        const y = points[index + 1];
        const z = points[index + 2];

        const rotatedX = x * cosYaw + z * sinYaw;
        const rotatedZ = z * cosYaw - x * sinYaw;
        const rotatedY = y * cosPitch - rotatedZ * sinPitch;
        const depth = rotatedZ * cosPitch + y * sinPitch;
        const perspective = 1.35 / (1.8 - depth * 0.26);
        const screenX = centerX + rotatedX * size * perspective;
        const screenY = centerY + rotatedY * size * perspective;

        if (index === 0) {
          context.moveTo(screenX, screenY);
        } else {
          context.lineTo(screenX, screenY);
        }
      }

      context.stroke();
      context.globalAlpha = 1;
      frame = window.requestAnimationFrame(render);
    };

    render();

    return () => {
      window.cancelAnimationFrame(frame);
    };
  }, [opacity, spin]);

  return (
    <canvas
      aria-hidden="true"
      className="thomas-attractor-plane"
      ref={canvasRef}
    />
  );
}
