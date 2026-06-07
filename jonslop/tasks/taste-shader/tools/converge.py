#!/usr/bin/env python3
"""
Reference-convergence loop for the taste-shader demo.

A shader SELF-IMPROVES toward ONE of Johnny's liked TASTE IMAGES (the reference),
over N iterations, with every step viewable. This is the demo + the proof that the
taste target is HIS: the reward IS a saved reference image. Swap the reference and
you get a different convergence.

Mechanism (ported from shader-shade /tmp/shader-shade/backend/{agent,render,vision}.py):
  - METRIC ANCHOR: embed the reference with CLIP (ViT-B-32, laion2b_s34b_b79k) -> ref_emb.
  - GENERATE: gpt-oss (Nebius openai/gpt-oss-120b-fast) writes an initial GLSL shader
    aiming to reproduce the reference, given a text description + the GLSL contract.
  - EACH ITER: render the shader (ModernGL, 256x256, 1 frame) -> CLIP-embed -> similarity
    = cosine(render_emb, ref_emb). HILL-CLIMB: keep the edited shader only if similarity
    improves over best-so-far; else revert to best. Then CRITIQUE + EDIT:
      * If a Nebius VISION model works, send current render + reference -> concrete
        critique (color/structure/density/motion) -> gpt-oss edits using the critique.
        (shader-shade VLM-guided path).
      * Else TEXT critique: gpt-oss gets the description + current/prev similarity +
        current shader, edits to raise similarity.
      * Compile-repair: if an edit fails to compile, ask gpt-oss to fix it.
  - LOG per iter {iter, similarity, kept, notes}; save best-so-far render as
    out/frames/iter_XX.png; write out/curve.png (similarity vs iter, running-max),
    out/convergence.gif (best-so-far renders), out/best_shader.glsl, out/log.jsonl.
    Print each iteration's similarity to stdout so the run is watchable live.

Nebius-only. No silent failures (errors are printed). Fast: 1 frame/iter for the loop;
the final best is animated (8 u_time frames) for the standalone best render gif if cheap.

Usage:
    python tools/converge.py --reference <jpg/png> --iters 50 --out <dir> \
        [--description <txt>] [--vision-model <id>] [--no-vision]
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import traceback
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Optional

import numpy as np
from PIL import Image

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from openai import OpenAI

# ---------------------------------------------------------------------------
# Paths / config.
# ---------------------------------------------------------------------------
TOOLS_DIR = Path(__file__).resolve().parent
TASK_DIR = TOOLS_DIR.parent

# Route CLIP weights to the prewarmed cache so we never cold-download ViT-B-32.
os.environ.setdefault("HF_HOME", str(TASK_DIR / ".hfcache"))

# Load API keys (NEBIUS_API_KEY, CEREBRAS_API_KEY, ...) from sia/.env into env
# if not already set. Cerebras is a DEV-ONLY accelerant: its key lives only in
# the local .env, never in committed code.
def _load_env_keys(*names: str) -> None:
    missing = {n for n in names if not os.environ.get(n)}
    if not missing:
        return
    for env_path in (
        TASK_DIR.parent.parent / ".env",      # sia/.env
        Path("/Users/johnnysheng/code/sia/.env"),
    ):
        if not env_path.exists():
            continue
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            for n in list(missing):
                if line.startswith(f"{n}="):
                    os.environ[n] = line.split("=", 1)[1].strip()
                    missing.discard(n)
        if not missing:
            return


_load_env_keys("NEBIUS_API_KEY", "CEREBRAS_API_KEY")

NEBIUS_BASE_URL = "https://api.tokenfactory.us-central1.nebius.com/v1/"
GPT_OSS_MODEL = "openai/gpt-oss-120b-fast"

# Committed default for the gpt-oss generate/edit/repair calls = NEBIUS.
# DEV-ONLY override (env, never committed): set CONVERGE_LLM=cerebras (or any of
# LLM_BASE_URL / LLM_API_KEY_ENV / LLM_MODEL) to route those calls to Cerebras
# (base_url https://api.cerebras.ai/v1/, key from CEREBRAS_API_KEY, gpt-oss-120b).
# The VLM critique ALWAYS stays on Nebius (Qwen) regardless of this override.
CEREBRAS_BASE_URL = "https://api.cerebras.ai/v1/"
CEREBRAS_MODEL = "gpt-oss-120b"


def _resolve_gpt_oss_provider() -> dict:
    """Pick the gpt-oss provider for generate/edit/repair calls.

    Returns dict {base_url, api_key, model, label}. Default = Nebius (shipped).
    Cerebras is selected only when env opts in:
      - CONVERGE_LLM=cerebras, OR
      - any of LLM_BASE_URL / LLM_API_KEY_ENV / LLM_MODEL is set.
    Generic LLM_* env wins so other providers can be wired without code changes.
    """
    want_cerebras = os.environ.get("CONVERGE_LLM", "").strip().lower() == "cerebras"
    base_url = os.environ.get("LLM_BASE_URL", "").strip()
    api_key_env = os.environ.get("LLM_API_KEY_ENV", "").strip()
    model = os.environ.get("LLM_MODEL", "").strip()

    if base_url or api_key_env or model or want_cerebras:
        # Generic LLM_* override, defaulting any unset field to Cerebras values.
        base_url = base_url or CEREBRAS_BASE_URL
        api_key_env = api_key_env or "CEREBRAS_API_KEY"
        model = model or CEREBRAS_MODEL
        _load_env_keys(api_key_env)
        key = os.environ.get(api_key_env)
        if not key:
            print(
                f"FATAL: gpt-oss override requested (base_url={base_url}, model={model}) "
                f"but {api_key_env} is not set (looked in env + sia/.env)",
                file=sys.stderr,
            )
            sys.exit(1)
        label = "cerebras" if base_url == CEREBRAS_BASE_URL else base_url
        return {"base_url": base_url, "api_key": key, "model": model, "label": label}

    # Shipped default: Nebius.
    key = os.environ.get("NEBIUS_API_KEY")
    if not key:
        print("FATAL: NEBIUS_API_KEY not set (looked in env + sia/.env)", file=sys.stderr)
        sys.exit(1)
    return {
        "base_url": NEBIUS_BASE_URL,
        "api_key": key,
        "model": GPT_OSS_MODEL,
        "label": "nebius",
    }
# Nebius vision model verified by a real two-image call (see build report).
# Qwen3.5 is a thinking model: its final answer is in message.content but it
# spends tokens on a reasoning trace first, so give it a generous max_tokens.
DEFAULT_VISION_MODEL = "Qwen/Qwen3.5-397B-A17B"
VISION_FALLBACK_MODELS = ["Qwen/Qwen3.5-397B-A17B", "moonshotai/Kimi-K2.6"]

CLIP_MODEL_NAME = "ViT-B-32"
CLIP_PRETRAINED = "laion2b_s34b_b79k"

OUTPUT_SIZE = (256, 256)
FLAT_STD_THRESHOLD = 0.02  # std on [0,1]; below this a render is "flat".

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
    "- GLSL version: #version 330  (first line exactly '#version 330', NOT '#version 300 es')\n"
    "- Input: in vec2 v_uv;   (v_uv in [0,1])\n"
    "- Uniforms: uniform sampler2D u_input; uniform vec2 u_resolution; uniform float u_time;\n"
    "- Output: out vec4 f_color;\n"
    "- Entry point: void main() — NOT Shadertoy void mainImage(out vec4, in vec2).\n"
    "- Single fragment shader only. No multipass, no Shadertoy buffers.\n"
    "- Generate PROCEDURAL content; do not rely on u_input for structure.\n"
    "- Animate via u_time so different frames differ.\n"
)

GLSL_RULES = (TASK_DIR / "data" / "public" / "glsl_rules.txt")
GLSL_RULES_TEXT = GLSL_RULES.read_text(encoding="utf-8").strip() if GLSL_RULES.exists() else ""

# Reasonable default description if no johnny-taste node / --description is given.
DEFAULT_DESCRIPTION = (
    "Glowing fine white particle ribbons tracing a 3D strange attractor (Thomas/Lorenz-"
    "style double-lobe) on a pure black background. Delicate 1px silk-like filaments with "
    "a soft bloom/halo where strands overlap; monochrome white/silver on black, high "
    "contrast, lots of negative space, meditative and sculptural. Emergent elegance: "
    "simple rules producing organic, smoke-like complexity. No rainbow color, no flat "
    "noise, no near-black emptiness without structure."
)

DESCRIPTION_NODE = Path(
    "/Users/johnnysheng/code/port-orchestration/resources/references/visual/"
    "strange-attractor-particles.md"
)


# ---------------------------------------------------------------------------
# Render (ModernGL, 256x256) — mirrors evaluate.py's trusted render.
# ---------------------------------------------------------------------------
def neutral_gray_input() -> Image.Image:
    arr = np.full((OUTPUT_SIZE[1], OUTPUT_SIZE[0], 3), 128, dtype=np.uint8)
    return Image.fromarray(arr, mode="RGB")


def render_frames(fragment_shader: str, num_frames: int = 1) -> list[Image.Image]:
    """Render num_frames over u_time in [0,1). Raises on compile/link error."""
    import moderngl

    input_img = neutral_gray_input()
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


def pixel_std(img: Image.Image) -> float:
    return float((np.asarray(img, dtype=np.float32) / 255.0).std())


# ---------------------------------------------------------------------------
# CLIP embedding (ViT-B-32 laion2b) — the metric anchor.
# ---------------------------------------------------------------------------
_CLIP = {}


def _get_clip():
    if "model" in _CLIP:
        return _CLIP["model"], _CLIP["preprocess"], _CLIP["device"]
    import open_clip
    import torch

    print(f"[clip] loading {CLIP_MODEL_NAME} / {CLIP_PRETRAINED} (HF_HOME={os.environ.get('HF_HOME')})")
    model, _, preprocess = open_clip.create_model_and_transforms(
        CLIP_MODEL_NAME, pretrained=CLIP_PRETRAINED
    )
    model.eval()
    device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    model = model.to(device)
    _CLIP.update(model=model, preprocess=preprocess, device=device)
    print(f"[clip] ready on {device}")
    return model, preprocess, device


def clip_embed(img: Image.Image) -> np.ndarray:
    import torch

    model, preprocess, device = _get_clip()
    with torch.no_grad():
        x = preprocess(img.convert("RGB")).unsqueeze(0).to(device)
        feat = model.encode_image(x)
        feat = feat / feat.norm(dim=-1, keepdim=True)
    return feat.cpu().numpy().astype(np.float32)[0]


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    a = a / (np.linalg.norm(a) + 1e-8)
    b = b / (np.linalg.norm(b) + 1e-8)
    return float(np.dot(a, b))


# ---------------------------------------------------------------------------
# Nebius LLM helpers (gpt-oss for GLSL, VLM for critique).
# ---------------------------------------------------------------------------
def make_client() -> OpenAI:
    """Nebius client — used for the VLM critique (always) and gpt-oss by default."""
    key = os.environ.get("NEBIUS_API_KEY")
    if not key:
        print("FATAL: NEBIUS_API_KEY not set (looked in env + sia/.env)", file=sys.stderr)
        sys.exit(1)
    return OpenAI(base_url=NEBIUS_BASE_URL, api_key=key)


def make_gpt_oss_client() -> tuple[OpenAI, str, str]:
    """Client + model for the gpt-oss generate/edit/repair calls.

    Default = Nebius (shipped). Cerebras (or generic LLM_*) only via env override.
    Returns (client, model_id, provider_label).
    """
    p = _resolve_gpt_oss_provider()
    return OpenAI(base_url=p["base_url"], api_key=p["api_key"]), p["model"], p["label"]


def _image_data_url(img: Image.Image) -> str:
    img = img.convert("RGB").resize(OUTPUT_SIZE)
    buf = BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def _extract_shader(raw: str, fallback: str) -> tuple[str, str]:
    """Parse {fragment_shader, notes} JSON; fall back to `fallback` if invalid."""
    try:
        data = json.loads(raw or "{}")
    except json.JSONDecodeError:
        # gpt-oss in json_object mode should be valid; if not, surface it.
        print(f"[warn] LLM did not return valid JSON: {repr(raw)[:160]}")
        return fallback, "json parse failed"
    fs = data.get("fragment_shader")
    notes = data.get("notes", "") if isinstance(data.get("notes"), str) else ""
    if not isinstance(fs, str) or "#version" not in fs:
        print(f"[warn] LLM returned no valid fragment_shader (notes={notes!r})")
        return fallback, notes or "no valid fragment_shader"
    return fs, notes


def gpt_oss_json(
    client: OpenAI, system: str, user: str, model: str = GPT_OSS_MODEL, temperature: float = 0.6
) -> str:
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        response_format={"type": "json_object"},
        temperature=temperature,
    )
    return resp.choices[0].message.content or "{}"


def generate_initial_shader(client: OpenAI, model: str, description: str) -> tuple[str, str]:
    rules = f"\n{GLSL_RULES_TEXT}\n" if GLSL_RULES_TEXT else ""
    user = (
        "You are a GLSL shader author. Return JSON only.\n"
        "Goal: write a single-pass GLSL fragment shader whose RENDER reproduces the\n"
        "reference image described below as closely as possible. Use procedural structure\n"
        "(the judge renders against a neutral gray input; do not depend on u_input).\n\n"
        f"REFERENCE DESCRIPTION:\n{description}\n\n"
        f"{INTERFACE_CONTRACT}{rules}\n"
        'Return JSON with keys: "fragment_shader" (full GLSL string) and "notes" (short string).\n'
    )
    raw = gpt_oss_json(client, "Return valid JSON only.", user, model=model, temperature=0.7)
    return _extract_shader(raw, DEFAULT_FRAGMENT_SHADER)


def edit_shader(
    client: OpenAI,
    model: str,
    current_shader: str,
    critique: str,
    description: str,
    iteration: int,
    total: int,
) -> tuple[str, str]:
    rules = f"\n{GLSL_RULES_TEXT}\n" if GLSL_RULES_TEXT else ""
    early = iteration < total // 2
    pacing = (
        "EARLY iteration — prioritize BOLD structural changes over fine-tuning."
        if early
        else "LATE iteration — prioritize refinement and subtle adjustments, avoid full rewrites."
    )
    user = (
        "You are a GLSL shader editor. Return JSON only.\n"
        "Goal: modify the shader so its render matches the reference image better.\n"
        "Apply the critique. Keep the interface contract unchanged. Keep it procedural.\n\n"
        f"REFERENCE DESCRIPTION:\n{description}\n\n"
        f"CRITIQUE (what is different from the reference, fix these):\n{critique}\n\n"
        f"Iteration {iteration + 1} of {total}. {pacing}\n\n"
        f"CURRENT SHADER:\n{current_shader}\n\n"
        f"{INTERFACE_CONTRACT}{rules}\n"
        'Return JSON with keys: "fragment_shader" (full revised GLSL) and "notes" (short string).\n'
    )
    raw = gpt_oss_json(client, "Return valid JSON only.", user, model=model, temperature=0.6)
    return _extract_shader(raw, current_shader)


def fix_compile_errors(
    client: OpenAI, model: str, shader: str, compile_error: str
) -> tuple[str, str]:
    rules = f"\n{GLSL_RULES_TEXT}\n" if GLSL_RULES_TEXT else ""
    user = (
        "You are a GLSL repair assistant. Return JSON only.\n"
        "Fix the compile error below WITHOUT changing the visual intent.\n"
        "Fix the FIRST error; later 'undeclared identifier' errors are usually cascades.\n\n"
        f"COMPILE ERROR:\n{compile_error}\n\n"
        f"SHADER:\n{shader}\n\n"
        f"{INTERFACE_CONTRACT}{rules}\n"
        'Return JSON with keys: "fragment_shader" (full fixed GLSL) and "notes" (short string).\n'
    )
    raw = gpt_oss_json(client, "Return valid JSON only.", user, model=model, temperature=0.2)
    return _extract_shader(raw, shader)


def vlm_critique(
    client: OpenAI,
    vision_model: str,
    reference_img: Image.Image,
    render_img: Image.Image,
) -> str:
    """Two-image critique. IMAGE 1 = reference (target), IMAGE 2 = current render."""
    prompt = (
        "Compare two images.\n"
        "- IMAGE 1: REFERENCE (the goal).\n"
        "- IMAGE 2: CURRENT shader render.\n\n"
        "Give a concrete critique of what the render must change to match the reference, "
        "in this priority order:\n"
        "1. COLOR/CONTRAST: palette, hue, brightness, contrast vs the reference.\n"
        "2. STRUCTURE: shapes, composition, the attractor's looping ribbon geometry.\n"
        "3. DENSITY/GLOW: line fineness, particle density, bloom/halo intensity.\n"
        "4. MOTION: how it should animate (flow along the ribbons, slow rotation).\n\n"
        "Be specific and actionable for a shader author. Output:\n"
        "SIMILARITY: <1-10>\n"
        "FIX (most important first):\n- ...\n- ...\n"
    )
    resp = client.chat.completions.create(
        model=vision_model,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": _image_data_url(reference_img)}},
                {"type": "image_url", "image_url": {"url": _image_data_url(render_img)}},
            ],
        }],
        temperature=0.2,
        max_tokens=3000,  # thinking model: budget for reasoning + the answer.
    )
    return (resp.choices[0].message.content or "").strip() or "No critique returned."


def text_critique(description: str, sim: float, prev_sim: Optional[float], shader: str) -> str:
    delta = "" if prev_sim is None else f" (previous similarity was {prev_sim:.4f}, change {sim - prev_sim:+.4f})"
    return (
        "No vision model available — critique from the metric.\n"
        f"Reference description:\n{description}\n\n"
        f"Current CLIP cosine similarity to the reference: {sim:.4f}{delta}.\n"
        "The render is too far from the reference. Push HARDER toward the reference's look: "
        "glowing fine white ribbons of a looping strange attractor on pure black, high "
        "contrast, soft bloom where strands overlap, lots of negative space. Avoid flat "
        "noise, rainbow color, and near-black emptiness. Increase structure and the "
        "attractor-ribbon geometry; raise the similarity."
    )


def discover_vision_model(client: OpenAI, requested: Optional[str]) -> Optional[str]:
    """Real probe: send a tiny known image; a model that names the color SEES it.
    Returns a working vision model id, or None for the text-critique fallback."""
    candidates = ([requested] if requested else []) + [
        m for m in VISION_FALLBACK_MODELS if m != requested
    ]
    img = Image.new("RGB", (96, 96), (0, 0, 0))
    for y in range(30, 66):
        for x in range(30, 66):
            img.putpixel((x, y), (255, 0, 0))
    url = _image_data_url(img)
    for m in candidates:
        try:
            resp = client.chat.completions.create(
                model=m,
                messages=[{"role": "user", "content": [
                    {"type": "text", "text": "Name the color of the square. One word only."},
                    {"type": "image_url", "image_url": {"url": url}},
                ]}],
                temperature=0.0,
                max_tokens=1500,
            )
            ans = (resp.choices[0].message.content or "").strip().lower()
            if "red" in ans:
                print(f"[vision] OK  {m}  (saw the red square)")
                return m
            print(f"[vision] reachable but wrong answer  {m}  -> {ans[:40]!r}")
        except Exception as e:
            print(f"[vision] FAIL  {m}  -> {str(e)[:120]}")
    print("[vision] no working vision model -> using TEXT-critique fallback")
    return None


# A minimal valid default so the loop never crashes if gpt-oss returns garbage on iter 0.
DEFAULT_FRAGMENT_SHADER = """#version 330
uniform sampler2D u_input;
uniform vec2 u_resolution;
uniform float u_time;
in vec2 v_uv;
out vec4 f_color;
float h(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
void main(){
    vec2 p = v_uv*2.0-1.0;
    float a = atan(p.y,p.x); float r = length(p);
    float ribbon = exp(-pow(abs(sin(a*3.0+u_time*0.5)-r*1.5),2.0)*40.0);
    float glow = exp(-r*r*2.0)*0.3;
    vec3 c = vec3(ribbon + glow);
    f_color = vec4(c, 1.0);
}
"""


# ---------------------------------------------------------------------------
# Compile-with-repair: render best frame, repairing up to N times.
# ---------------------------------------------------------------------------
def render_or_repair(
    client: OpenAI, model: str, shader: str, max_repairs: int = 3
) -> tuple[Optional[Image.Image], str, str]:
    """Try to render shader (1 frame). On compile error, ask gpt-oss to fix it and
    retry. Returns (image_or_None, working_shader, status_note)."""
    cur = shader
    last_err = ""
    for attempt in range(max_repairs + 1):
        try:
            img = render_frames(cur, num_frames=1)[0]
            note = "compiled" if attempt == 0 else f"compiled after {attempt} repair(s)"
            return img, cur, note
        except Exception as e:
            last_err = str(e)
            print(f"[compile] attempt {attempt} failed: {last_err[:160]}")
            if attempt >= max_repairs:
                break
            cur, _ = fix_compile_errors(client, model, cur, last_err)
    return None, shader, f"compile failed after {max_repairs} repairs: {last_err[:160]}"


# ---------------------------------------------------------------------------
# Outputs: curve + gif.
# ---------------------------------------------------------------------------
def write_curve(log: list[dict], out_png: Path) -> None:
    iters = [e["iter"] for e in log]
    sims = [e["similarity"] for e in log]
    best = []
    b = float("-inf")
    for s in sims:
        b = max(b, s)
        best.append(b)
    plt.figure(figsize=(9, 5))
    plt.plot(iters, sims, marker="o", alpha=0.4, label="per-iteration similarity")
    plt.plot(iters, best, linewidth=2.2, color="crimson", label="best-so-far (running max)")
    plt.xlabel("iteration")
    plt.ylabel("CLIP cosine similarity to reference")
    plt.title("taste-shader: convergence toward the reference")
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=9)
    plt.tight_layout()
    out_png.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_png, dpi=120)
    plt.close()


def write_gif(frames: list[Image.Image], out_gif: Path, duration: int = 200) -> None:
    if not frames:
        return
    out_gif.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        out_gif, save_all=True, append_images=frames[1:], duration=duration, loop=0
    )


# ---------------------------------------------------------------------------
# Live frontend bridge: write the build-iterations.mjs-compatible gen shape and
# refresh the Next.js carousel data after each iteration.
# ---------------------------------------------------------------------------
import subprocess  # noqa: E402  (kept local to this section for clarity)

FRONTEND_DIR = Path(os.environ.get("FRONTEND_DIR", "/Users/johnnysheng/code/sia/frontend"))
FRONTEND_BUILDER = FRONTEND_DIR / "scripts" / "build-iterations.mjs"
# build-iterations.mjs resolves RUNS_DIR as <frontend>/../runs.
FRONTEND_RUNS_DIR = FRONTEND_DIR.parent / "runs"


def write_frontend_gen(
    run_id: int,
    gen: int,
    render_img: Image.Image,
    shader: str,
    similarity: float,
    improvement: str,
    prompt: str,
) -> Path:
    """Write one frontend-compatible generation dir:
        runs/run_<id>/gen_<NN>/{render.png, shader.glsl, results.json,
                                improvement.md, prompt.txt}
    Returns the gen dir. gen is 1-based (the iteration index)."""
    gen_dir = FRONTEND_RUNS_DIR / f"run_{run_id}" / f"gen_{gen:02d}"
    gen_dir.mkdir(parents=True, exist_ok=True)

    render_img.convert("RGB").save(gen_dir / "render.png")
    (gen_dir / "shader.glsl").write_text(shader, encoding="utf-8")
    results = {
        "accuracy": round(similarity * 100, 4),
        "taste_score": round(similarity, 6),
        "metric": "clip_to_reference",
        "compile_ok": True,
        "higher_is_better": True,
    }
    (gen_dir / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    (gen_dir / "improvement.md").write_text((improvement or "").strip() + "\n", encoding="utf-8")
    (gen_dir / "prompt.txt").write_text((prompt or "").strip() + "\n", encoding="utf-8")
    return gen_dir


def refresh_frontend(run_id: int) -> None:
    """Invoke the Next.js builder to regenerate the live carousel data.
    Tolerate node-not-found / builder errors by printing a clear warning instead
    of crashing the convergence loop."""
    if not FRONTEND_BUILDER.exists():
        print(f"[frontend] WARNING: builder not found at {FRONTEND_BUILDER}; skipping refresh")
        return
    cmd = ["node", str(FRONTEND_BUILDER), str(run_id)]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError:
        print(
            "[frontend] WARNING: `node` not found on PATH; skipping live refresh "
            f"(would have run: {' '.join(cmd)})"
        )
        return
    except Exception as e:
        print(f"[frontend] WARNING: builder invocation failed: {str(e)[:160]}")
        return
    if proc.stdout:
        print(proc.stdout.rstrip())
    if proc.returncode != 0:
        print(
            f"[frontend] WARNING: builder exited {proc.returncode}: "
            f"{(proc.stderr or '').strip()[:240]}"
        )


# ---------------------------------------------------------------------------
# The loop.
# ---------------------------------------------------------------------------
def load_description(reference_path: Path, override: Optional[str]) -> str:
    if override:
        return override
    # Prefer the johnny-taste node's Taste Extraction block if present + matching.
    if "strange-attractor" in reference_path.stem and DESCRIPTION_NODE.exists():
        txt = DESCRIPTION_NODE.read_text(encoding="utf-8")
        # Pull the concise visual cues: high-contrast white-on-black particle attractor.
        return (
            "Glowing fine white particle ribbons tracing a 3D strange attractor "
            "(Thomas cyclically-symmetric / Lorenz-style, twisted intersecting loops) "
            "on a pure black background. Delicate ~1px silk/smoke-like filaments with a "
            "soft bloom/halo where strands overlap; strictly monochrome white/silver on "
            "black, very high contrast, lots of negative space, meditative and sculptural. "
            "Emergent elegance: three simple equations producing organic, deep-sea-creature "
            "complexity. NO rainbow color, NO flat fbm noise, NO near-black emptiness "
            "without structure."
        )
    return DEFAULT_DESCRIPTION


def run(args: argparse.Namespace) -> int:
    reference_path = Path(args.reference).resolve()
    out_dir = Path(args.out).resolve()
    frames_dir = out_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    if not reference_path.exists():
        print(f"FATAL: reference not found: {reference_path}", file=sys.stderr)
        return 1

    description = load_description(reference_path, args.description)
    print(f"[setup] reference = {reference_path}")
    print(f"[setup] out       = {out_dir}")
    print(f"[setup] iters     = {args.iters}")
    print(f"[setup] description:\n  {description}\n")

    # Nebius client (VLM critique always; gpt-oss by default).
    client = make_client()
    # gpt-oss client/model for generate/edit/repair (Nebius default; Cerebras via env).
    gpt_client, gpt_model, gpt_label = make_gpt_oss_client()
    print(f"[setup] gpt-oss provider = {gpt_label} (model={gpt_model})")
    if args.frontend_run is not None:
        print(
            f"[setup] frontend live mode = ON -> writing runs/run_{args.frontend_run}/gen_NN "
            f"and refreshing {FRONTEND_BUILDER}"
        )

    # 1. CLIP-embed the reference (the metric anchor).
    reference_img = Image.open(reference_path).convert("RGB")
    ref_emb = clip_embed(reference_img)
    print("[setup] reference embedded with CLIP (metric anchor ready)")
    # Save the reference into the out dir so the demo is self-contained.
    reference_img.resize(OUTPUT_SIZE).save(out_dir / "reference.png")

    # 2. Discover a working Nebius vision model (real probe), unless disabled.
    vision_model = None
    if not args.no_vision:
        vision_model = discover_vision_model(client, args.vision_model)
    mode = f"VLM-guided ({vision_model})" if vision_model else "TEXT-critique fallback"
    print(f"[setup] critique mode = {mode}\n")

    # 3. Iter 0: initial shader.
    print("[iter 0] generating initial shader with gpt-oss ...")
    shader, notes = generate_initial_shader(gpt_client, gpt_model, description)
    img, shader, comp_note = render_or_repair(gpt_client, gpt_model, shader)
    if img is None:
        print(f"FATAL: initial shader never compiled: {comp_note}", file=sys.stderr)
        return 1

    best_shader = shader
    best_img = img
    best_sim = cosine(clip_embed(img), ref_emb)
    best_frames: list[Image.Image] = [best_img.copy()]

    log: list[dict] = []
    log_path = out_dir / "log.jsonl"
    log_f = log_path.open("w", encoding="utf-8")

    def record(it: int, sim: float, kept: bool, note: str) -> None:
        entry = {"iter": it, "similarity": round(sim, 6), "kept": kept, "notes": note}
        log.append(entry)
        log_f.write(json.dumps(entry) + "\n")
        log_f.flush()
        # Always save the BEST-so-far render for this iteration (viewable per-step).
        best_img.save(frames_dir / f"iter_{it:02d}.png")
        flag = "KEPT " if kept else "rev  "
        print(f"[iter {it:>2}] sim={sim:.4f}  best={best_sim:.4f}  {flag} {note[:90]}")

    record(0, best_sim, True, f"initial shader ({comp_note}); {notes[:60]}")

    def publish_frontend(
        gen: int,
        render_img: Image.Image,
        shader_src: str,
        similarity: float,
        improvement: str,
        prompt: str,
    ) -> None:
        """If --frontend-run is set, write this iteration's gen dir (current render,
        so the panel shows the shader evolving) and refresh the live carousel."""
        if args.frontend_run is None:
            return
        gen_dir = write_frontend_gen(
            args.frontend_run, gen, render_img, shader_src, similarity, improvement, prompt
        )
        print(f"[frontend] wrote {gen_dir}")
        refresh_frontend(args.frontend_run)

    # gen 1 = the initial shader (iter 0). The instruction was the generate prompt.
    publish_frontend(
        1,
        best_img,
        best_shader,
        best_sim,
        f"Initial shader ({comp_note}); {notes[:120]}",
        f"Generate a GLSL shader reproducing the reference:\n{description}",
    )

    # 4. Iteration loop: critique -> edit -> render -> hill-climb keep-best.
    for it in range(1, args.iters + 1):
        # Critique the CURRENT BEST render against the reference.
        if vision_model:
            try:
                critique = vlm_critique(client, vision_model, reference_img, best_img)
            except Exception as e:
                print(f"[iter {it}] VLM critique failed, using text fallback: {str(e)[:120]}")
                critique = text_critique(description, best_sim, None, best_shader)
        else:
            prev_sim = log[-1]["similarity"] if len(log) >= 1 else None
            critique = text_critique(description, best_sim, prev_sim, best_shader)

        # gen number for the frontend panel = iteration index + 1 (gen 1 = initial).
        fe_gen = it + 1

        # Edit the best shader using the critique.
        try:
            cand_shader, edit_notes = edit_shader(
                gpt_client, gpt_model, best_shader, critique, description, it, args.iters
            )
        except Exception as e:
            print(f"[iter {it}] edit_shader call failed: {str(e)[:140]}")
            traceback.print_exc()
            record(it, best_sim, False, f"edit call failed: {str(e)[:60]}")
            # Live panel: edit failed -> show best-so-far render, surface the error.
            publish_frontend(
                fe_gen, best_img, best_shader, best_sim,
                f"Edit call failed: {str(e)[:100]}", critique[:140],
            )
            continue

        # Render the candidate (with compile-repair).
        cand_img, cand_shader, comp_note = render_or_repair(gpt_client, gpt_model, cand_shader)
        if cand_img is None:
            record(it, best_sim, False, f"candidate uncompilable: {comp_note[:60]}")
            publish_frontend(
                fe_gen, best_img, best_shader, best_sim,
                f"Candidate uncompilable: {comp_note[:100]}", critique[:140],
            )
            continue
        if pixel_std(cand_img) < FLAT_STD_THRESHOLD:
            record(it, best_sim, False, "candidate flat (std<0.02); reverted")
            publish_frontend(
                fe_gen, cand_img, cand_shader, best_sim,
                "Candidate render was flat (std<0.02); reverted to best.", critique[:140],
            )
            continue

        cand_sim = cosine(clip_embed(cand_img), ref_emb)

        # HILL-CLIMB: keep only if it improves on best-so-far.
        if cand_sim > best_sim:
            best_sim = cand_sim
            best_shader = cand_shader
            best_img = cand_img
            best_frames.append(best_img.copy())
            record(it, cand_sim, True, f"improved ({comp_note}); {edit_notes[:50]}")
            # Live panel: kept -> show THIS iteration's improved render.
            publish_frontend(
                fe_gen, cand_img, cand_shader, cand_sim,
                f"Improved ({comp_note}); {edit_notes[:120]}", critique[:140],
            )
        else:
            # Reverted: log the candidate's (lower) similarity but keep best unchanged.
            record(it, cand_sim, False, f"no gain ({cand_sim:.4f}<={best_sim:.4f}); reverted")
            # Live panel: show THIS iteration's render (the shader still evolving),
            # but report the kept best similarity for the panel's accuracy.
            publish_frontend(
                fe_gen, cand_img, cand_shader, best_sim,
                f"No gain ({cand_sim:.4f} <= best {best_sim:.4f}); reverted. {edit_notes[:90]}",
                critique[:140],
            )

    log_f.close()

    # 5. Final outputs.
    (out_dir / "best_shader.glsl").write_text(best_shader, encoding="utf-8")
    write_curve(log, out_dir / "curve.png")
    write_gif(best_frames, out_dir / "convergence.gif", duration=250)

    # Animate the final best shader (8 u_time frames) into a standalone hero gif.
    try:
        anim = render_frames(best_shader, num_frames=8)
        write_gif(anim, out_dir / "best_animated.gif", duration=120)
        # best.png = the highest-CLIP-sim frame of the final shader.
        best_frame = max(anim, key=lambda fr: cosine(clip_embed(fr), ref_emb))
        best_frame.save(out_dir / "best.png")
    except Exception as e:
        print(f"[final] best-shader animation failed: {str(e)[:140]}")
        best_img.save(out_dir / "best.png")

    summary = {
        "reference": str(reference_path),
        "iters": args.iters,
        "critique_mode": mode,
        "vision_model": vision_model,
        "gpt_oss_provider": gpt_label,
        "gpt_oss_model": gpt_model,
        "frontend_run": args.frontend_run,
        "clip_model": f"{CLIP_MODEL_NAME}/{CLIP_PRETRAINED}",
        "initial_similarity": log[0]["similarity"] if log else None,
        "best_similarity": round(best_sim, 6),
        "improvement": round(best_sim - (log[0]["similarity"] if log else 0.0), 6),
        "kept_steps": sum(1 for e in log if e["kept"]),
        "total_steps": len(log),
        "finished": datetime.now().isoformat(),
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("\n=== CONVERGENCE COMPLETE ===")
    print(json.dumps(summary, indent=2))
    print(f"\nArtifacts in {out_dir}:")
    print("  best_shader.glsl  best.png  best_animated.gif")
    print("  curve.png  convergence.gif  log.jsonl  summary.json  frames/iter_XX.png")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description="Reference-convergence loop for taste-shader")
    ap.add_argument("--reference", required=True, help="Reference image (jpg/png) — the metric anchor.")
    ap.add_argument("--iters", type=int, default=50, help="Number of convergence iterations.")
    ap.add_argument("--out", required=True, help="Output directory.")
    ap.add_argument("--description", default=None, help="Override the reference text description.")
    ap.add_argument("--vision-model", default=DEFAULT_VISION_MODEL,
                    help="Preferred Nebius vision model id to try first.")
    ap.add_argument("--no-vision", action="store_true",
                    help="Skip the vision model; force the text-critique fallback.")
    ap.add_argument(
        "--frontend-run", type=int, default=None, metavar="N",
        help="If set, each iteration ALSO writes the Next.js frontend-compatible shape to "
             "runs/run_N/gen_NN/ (render.png, shader.glsl, results.json, improvement.md, "
             "prompt.txt) and refreshes the live carousel via build-iterations.mjs. Use a NEW "
             "run id that doesn't collide with existing runs (e.g. 9).",
    )
    args = ap.parse_args()
    sys.exit(run(args))


if __name__ == "__main__":
    main()
