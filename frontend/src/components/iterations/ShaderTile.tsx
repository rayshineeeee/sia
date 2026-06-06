"use client";

import { useEffect, useRef } from "react";
import type { Iteration } from "./types";

const vertexShaderSource = `
attribute vec2 position;
varying vec2 vUv;

void main() {
  vUv = position * 0.5 + 0.5;
  gl_Position = vec4(position, 0.0, 1.0);
}
`;

const fragmentShaderSource = `
precision mediump float;

uniform vec2 resolution;
uniform float seed;
uniform float time;
varying vec2 vUv;

float line(vec2 point, float angle, float width) {
  vec2 rotated = mat2(cos(angle), -sin(angle), sin(angle), cos(angle)) * point;
  return smoothstep(width, 0.0, abs(fract(rotated.y * 9.0) - 0.5));
}

void main() {
  vec2 aspect = vec2(resolution.x / max(resolution.y, 1.0), 1.0);
  vec2 point = (vUv - 0.5) * aspect;
  float sweep = line(point + vec2(sin(time * 0.18 + seed) * 0.08, 0.0), seed * 0.37, 0.022);
  float counter = line(point * 1.4, -seed * 0.21 - time * 0.03, 0.014);
  float mask = smoothstep(0.68, 0.12, length(point));
  float ink = max(sweep * 0.7, counter * 0.36) * mask;
  vec3 paper = vec3(0.985, 0.985, 0.965);
  vec3 black = vec3(0.04, 0.04, 0.038);

  gl_FragColor = vec4(mix(paper, black, ink), 1.0);
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
      stencil: false,
    });
    if (!gl) return;

    const program = createProgram(gl, vertexShaderSource, fragmentShaderSource);
    if (!program) return;

    const positionLocation = gl.getAttribLocation(program, "position");
    const resolutionLocation = gl.getUniformLocation(program, "resolution");
    const seedLocation = gl.getUniformLocation(program, "seed");
    const timeLocation = gl.getUniformLocation(program, "time");
    const buffer = gl.createBuffer();
    const startedAt = performance.now();
    let frame = 0;

    gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
    gl.bufferData(
      gl.ARRAY_BUFFER,
      new Float32Array([-1, -1, 1, -1, -1, 1, -1, 1, 1, -1, 1, 1]),
      gl.STATIC_DRAW,
    );

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
      return { height, width };
    };

    const render = () => {
      const { height, width } = resize();
      const time = (performance.now() - startedAt) / 1000;

      gl.useProgram(program);
      gl.enableVertexAttribArray(positionLocation);
      gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
      gl.vertexAttribPointer(positionLocation, 2, gl.FLOAT, false, 0, 0);
      gl.uniform2f(resolutionLocation, width, height);
      gl.uniform1f(seedLocation, iteration.id);
      gl.uniform1f(timeLocation, time);
      gl.drawArrays(gl.TRIANGLES, 0, 6);

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

function createProgram(
  gl: WebGLRenderingContext,
  vertexSource: string,
  fragmentSource: string,
) {
  const vertexShader = createShader(gl, gl.VERTEX_SHADER, vertexSource);
  const fragmentShader = createShader(gl, gl.FRAGMENT_SHADER, fragmentSource);
  if (!vertexShader || !fragmentShader) return null;

  const program = gl.createProgram();
  if (!program) return null;

  gl.attachShader(program, vertexShader);
  gl.attachShader(program, fragmentShader);
  gl.linkProgram(program);
  gl.deleteShader(vertexShader);
  gl.deleteShader(fragmentShader);

  if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
    gl.deleteProgram(program);
    return null;
  }

  return program;
}

function createShader(gl: WebGLRenderingContext, type: number, source: string) {
  const shader = gl.createShader(type);
  if (!shader) return null;

  gl.shaderSource(shader, source);
  gl.compileShader(shader);

  if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
    gl.deleteShader(shader);
    return null;
  }

  return shader;
}
