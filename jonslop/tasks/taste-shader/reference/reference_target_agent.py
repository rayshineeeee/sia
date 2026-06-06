#!/usr/bin/env python3
"""
SEED prompt-writer for the `taste-shader` task (DELIBERATELY WEAK).

The loop: this agent builds a text instruction -> sends it to a FROZEN LLM
(Nebius openai/gpt-oss-120b-fast) -> gets back a GLSL fragment shader ->
renders it locally with ModernGL -> writes outputs to --working_dir.

This seed is intentionally generic so SIA has headroom to improve it. It:
  - IGNORES the taste files in data/public/taste/ (does not read taste-dna,
    taxonomy, synthesis, or the knowledge graph).
  - builds ONE generic "make an abstract flowing visual" instruction.
  - calls the frozen LLM ONCE (no multi-candidate selection).
  - does NOT extract taste tokens, add a style / negative-style suffix.
  - does NOT do compile-repair if the shader fails to compile.

What SIA should add over generations = exactly the above gaps.

Self-contained: the render code is inlined (SIA copies this file into per-gen
working dirs), so it must not depend on a shared package.

Usage:
    python reference_target_agent.py --dataset_dir <data/public> --working_dir <gen_dir>
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path

import moderngl
import numpy as np
from openai import OpenAI
from PIL import Image

# ---------------------------------------------------------------------------
# Frozen LLM (Nebius Token Factory) — DO NOT change model.
# ---------------------------------------------------------------------------
NEBIUS_BASE_URL = "https://api.tokenfactory.us-central1.nebius.com/v1/"
NEBIUS_API_KEY_ENV = "NEBIUS_API_KEY"
NEBIUS_MODEL = "openai/gpt-oss-120b-fast"

# ---------------------------------------------------------------------------
# Inlined render code (mirrors the trusted judge in evaluate.py).
# ---------------------------------------------------------------------------
OUTPUT_SIZE = (256, 256)

VERTEX_SHADER = """
#version 330
in vec2 in_pos;
out vec2 v_uv;
void main() {
    v_uv = in_pos * 0.5 + 0.5;
    gl_Position = vec4(in_pos, 0.0, 1.0);
}
"""

INTERFACE_CONTRACT = (
    "Shader interface contract (must follow exactly):\n"
    "- GLSL version: #version 330\n"
    "- Input: in vec2 v_uv;   (v_uv in [0,1])\n"
    "- Uniforms: uniform sampler2D u_input; uniform vec2 u_resolution; uniform float u_time;\n"
    "- Output: out vec4 f_color;\n"
    "- Entry point: void main() — NOT Shadertoy void mainImage(out vec4, in vec2).\n"
    "- Desktop GLSL only: first line exactly '#version 330' (NOT '#version 300 es').\n"
    "- Single fragment shader only. No multipass, no Shadertoy buffers.\n"
    "- Generate procedural content; the judge renders against a neutral gray input.\n"
)


def neutral_gray_input() -> Image.Image:
    arr = np.full((OUTPUT_SIZE[1], OUTPUT_SIZE[0], 3), 128, dtype=np.uint8)
    return Image.fromarray(arr, mode="RGB")


def render_frames(
    fragment_shader: str, input_img: Image.Image, num_frames: int = 8
) -> list[Image.Image]:
    """Render `num_frames` animation frames over u_time in [0,1). Raises on compile
    error. The trusted judge re-renders 8 frames and scores the BEST one, so an
    improved agent MAY render multiple frames and keep the best (this seed renders
    only one and does not use this headroom)."""
    input_img = input_img.convert("RGB").resize(OUTPUT_SIZE)
    input_arr = np.asarray(input_img, dtype=np.uint8)

    ctx = moderngl.create_standalone_context()
    try:
        fbo = ctx.simple_framebuffer(OUTPUT_SIZE)
        fbo.use()
        program = ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=fragment_shader)

        vertices = np.array([-1.0, -1.0, 3.0, -1.0, -1.0, 3.0], dtype="f4")
        vbo = ctx.buffer(vertices.tobytes())
        vao = ctx.simple_vertex_array(program, vbo, "in_pos")

        texture = ctx.texture(OUTPUT_SIZE, 3, input_arr.tobytes())
        texture.use(location=0)
        if "u_input" in program:
            program["u_input"] = 0
        if "u_resolution" in program:
            program["u_resolution"] = OUTPUT_SIZE

        frames: list[Image.Image] = []
        for f in range(num_frames):
            if "u_time" in program:
                program["u_time"] = float(f) / float(max(num_frames, 1))
            fbo.clear(0.0, 0.0, 0.0, 1.0)
            vao.render(mode=moderngl.TRIANGLES)
            data = fbo.read(components=3)
            frames.append(Image.frombytes("RGB", OUTPUT_SIZE, data))

        vao.release()
        vbo.release()
        texture.release()
        fbo.release()
        return frames
    finally:
        ctx.release()


def render_shader(fragment_shader: str, input_img: Image.Image, u_time: float = 0.0) -> Image.Image:
    """Render a single frame. Raises on compile error."""
    return render_frames(fragment_shader, input_img, num_frames=1)[0]


# ---------------------------------------------------------------------------
# The (weak) prompt-writer.
# ---------------------------------------------------------------------------
def read_brief(dataset_dir: Path) -> str:
    """Read just the one-line brief from task.md (generic, no taste files)."""
    task_md = dataset_dir / "task.md"
    if not task_md.exists():
        return "A full-screen abstract flowing generative visual effect."
    lines = task_md.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        if line.strip().startswith("## The brief"):
            for j in range(i + 1, len(lines)):
                t = lines[j].strip()
                if t and not t.startswith("<!--") and not t.startswith("#"):
                    return t
    return "A full-screen abstract flowing generative visual effect."


def build_instruction(brief: str) -> str:
    """GENERIC instruction. Deliberately ignores Johnny's taste files."""
    return (
        "You are a GLSL shader author. Return JSON only.\n"
        "Write a single-pass GLSL fragment shader that depicts:\n"
        f"  {brief}\n\n"
        "Make it look interesting and not flat. Use some procedural noise or pattern.\n\n"
        f"{INTERFACE_CONTRACT}\n"
        'Return JSON with keys: "fragment_shader" (the full GLSL string) and "notes" (a short string).\n'
    )


def call_frozen_llm(client: OpenAI, instruction: str) -> dict:
    resp = client.chat.completions.create(
        model=NEBIUS_MODEL,
        messages=[
            {"role": "system", "content": "Return valid JSON only."},
            {"role": "user", "content": instruction},
        ],
        response_format={"type": "json_object"},
        temperature=0.7,
    )
    raw = resp.choices[0].message.content or "{}"
    return json.loads(raw)


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed taste-shader prompt-writer")
    parser.add_argument("--dataset_dir", required=True, help="READ-ONLY dataset dir (data/public)")
    parser.add_argument("--working_dir", required=True, help="READ-WRITE working dir (gen dir)")
    args = parser.parse_args()

    dataset_dir = Path(args.dataset_dir)
    working_dir = Path(args.working_dir)
    working_dir.mkdir(parents=True, exist_ok=True)

    start = datetime.now()
    log: dict = {
        "agent": "reference_target_agent_seed",
        "model": NEBIUS_MODEL,
        "task": "taste-shader",
        "start_time": start.isoformat(),
    }

    api_key = os.environ.get(NEBIUS_API_KEY_ENV)
    if not api_key:
        print(f"ERROR: {NEBIUS_API_KEY_ENV} not set", file=sys.stderr)
        sys.exit(1)

    client = OpenAI(base_url=NEBIUS_BASE_URL, api_key=api_key)

    brief = read_brief(dataset_dir)
    instruction = build_instruction(brief)
    log["brief"] = brief
    (working_dir / "prompt.txt").write_text(instruction, encoding="utf-8")

    try:
        data = call_frozen_llm(client, instruction)
    except Exception as e:  # the frozen LLM call failed — surface it, no fallback shader
        log["status"] = "failed"
        log["error"] = f"LLM call/parse failed: {e}"
        (working_dir / "agent_execution.json").write_text(
            json.dumps(log, indent=2), encoding="utf-8"
        )
        traceback.print_exc()
        sys.exit(1)

    fragment_shader = data.get("fragment_shader", "")
    notes = data.get("notes", "")
    log["notes"] = notes

    if not isinstance(fragment_shader, str) or "#version" not in fragment_shader:
        log["status"] = "failed"
        log["error"] = "LLM did not return a valid fragment_shader"
        (working_dir / "agent_execution.json").write_text(
            json.dumps(log, indent=2), encoding="utf-8"
        )
        print("ERROR: no valid fragment_shader returned", file=sys.stderr)
        sys.exit(1)

    # Save the shader (this is what the judge evaluates).
    (working_dir / "shader.glsl").write_text(fragment_shader, encoding="utf-8")

    # Try to render it (seed does NOT repair compile errors).
    compile_ok = True
    try:
        render = render_shader(fragment_shader, neutral_gray_input(), u_time=0.0)
        render.save(working_dir / "render.png")
    except Exception as e:
        compile_ok = False
        log["render_error"] = str(e)
        print(f"WARN: shader failed to render: {e}", file=sys.stderr)

    log["compile_ok"] = compile_ok
    log["status"] = "success"
    log["end_time"] = datetime.now().isoformat()
    log["duration_seconds"] = (datetime.now() - start).total_seconds()
    (working_dir / "agent_execution.json").write_text(json.dumps(log, indent=2), encoding="utf-8")

    print(f"shader.glsl written ({len(fragment_shader)} chars), compile_ok={compile_ok}")


if __name__ == "__main__":
    main()
