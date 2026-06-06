"use client";

import { useEffect, useRef } from "react";
import { computeThomasAttractor } from "./thomasAttractor";
import type { Iteration } from "./types";
import { createProgram } from "./webgl";

const PARTICLE_COUNT = 28000;

const vertexShaderSource = `
attribute vec3 position;
uniform float pointSize;
uniform float seed;
uniform float time;
varying float vDepth;
varying float vPulse;

mat3 rotateX(float angle) {
  float s = sin(angle);
  float c = cos(angle);
  return mat3(
    1.0, 0.0, 0.0,
    0.0, c, -s,
    0.0, s, c
  );
}

mat3 rotateY(float angle) {
  float s = sin(angle);
  float c = cos(angle);
  return mat3(
    c, 0.0, s,
    0.0, 1.0, 0.0,
    -s, 0.0, c
  );
}

void main() {
  float drift = time * (0.12 + seed * 0.006);
  vec3 point = rotateY(drift + seed * 0.11) * rotateX(0.62 + sin(time * 0.08 + seed) * 0.12) * position;
  float depth = clamp(point.z * 0.48 + 0.54, 0.0, 1.0);
  vec2 screen = point.xy * vec2(0.66, 0.82);

  vDepth = depth;
  vPulse = 0.72 + sin(time * 0.75 + seed + point.z * 4.0) * 0.12;
  gl_Position = vec4(screen, 0.0, 1.0);
  gl_PointSize = pointSize * (0.7 + depth * 1.7);
}
`;

const fragmentShaderSource = `
precision mediump float;
varying float vDepth;
varying float vPulse;

void main() {
  vec2 center = gl_PointCoord - 0.5;
  float radius = dot(center, center);
  float alpha = smoothstep(0.25, 0.02, radius) * (0.38 + vDepth * 0.72);
  vec3 ember = vec3(0.92, 0.06, 0.0);
  vec3 deepRed = vec3(0.34, 0.015, 0.0);
  vec3 color = mix(deepRed, ember, vDepth) * vPulse;

  gl_FragColor = vec4(color, alpha);
}
`;

export function ShaderTile({
  active = true,
  className = "",
  iteration,
}: {
  active?: boolean;
  className?: string;
  iteration: Iteration;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!active || !canvas) return;

    const gl = canvas.getContext("webgl", {
      alpha: false,
      antialias: false,
      depth: false,
      powerPreference: "high-performance",
      stencil: false,
    });
    if (!gl) return;

    const program = createProgram(gl, vertexShaderSource, fragmentShaderSource);
    if (!program) return;

    const positionLocation = gl.getAttribLocation(program, "position");
    const pointSizeLocation = gl.getUniformLocation(program, "pointSize");
    const seedLocation = gl.getUniformLocation(program, "seed");
    const timeLocation = gl.getUniformLocation(program, "time");

    if (
      positionLocation < 0 ||
      !pointSizeLocation ||
      !seedLocation ||
      !timeLocation
    ) {
      gl.deleteProgram(program);
      return;
    }

    const positions = computeThomasAttractor({
      seed: iteration.id,
      total: PARTICLE_COUNT,
    });
    const buffer = gl.createBuffer();
    if (!buffer) {
      gl.deleteProgram(program);
      return;
    }

    gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
    gl.bufferData(gl.ARRAY_BUFFER, positions, gl.STATIC_DRAW);
    gl.disable(gl.DEPTH_TEST);
    gl.enable(gl.BLEND);
    gl.blendFunc(gl.SRC_ALPHA, gl.ONE);

    const startedAt = performance.now();
    let frame = 0;

    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      const scale = Math.min(window.devicePixelRatio || 1, 2);
      const width = Math.max(1, Math.round(rect.width * scale));
      const height = Math.max(1, Math.round(rect.height * scale));

      if (canvas.width !== width || canvas.height !== height) {
        canvas.width = width;
        canvas.height = height;
      }

      gl.viewport(0, 0, width, height);
      return scale;
    };

    const render = () => {
      const pixelScale = resize();
      const time = (performance.now() - startedAt) / 1000;
      const reveal = Math.min(1, 0.1 + time * 0.22);
      const visible = Math.max(256, Math.floor(PARTICLE_COUNT * reveal));

      gl.clearColor(0.006, 0.004, 0.003, 1);
      gl.clear(gl.COLOR_BUFFER_BIT);
      gl.useProgram(program);
      gl.enableVertexAttribArray(positionLocation);
      gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
      gl.vertexAttribPointer(positionLocation, 3, gl.FLOAT, false, 0, 0);
      gl.uniform1f(pointSizeLocation, 1.35 * pixelScale);
      gl.uniform1f(seedLocation, iteration.id);
      gl.uniform1f(timeLocation, time);
      gl.drawArrays(gl.POINTS, 0, visible);

      frame = window.requestAnimationFrame(render);
    };

    render();

    return () => {
      window.cancelAnimationFrame(frame);
      gl.deleteBuffer(buffer);
      gl.deleteProgram(program);
    };
  }, [active, iteration.id]);

  return <canvas aria-hidden="true" className={`shader-tile ${className}`} ref={canvasRef} />;
}
