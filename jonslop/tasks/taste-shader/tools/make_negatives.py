#!/usr/bin/env python3
"""
Generate the NEGATIVE anchor for the taste DIRECTION: ~16 TRIVIAL / GENERIC
shader renders (solid colors, plain linear gradients, plain fbm noise, near-black)
rendered with the SAME inlined render code the trusted judge uses, saved to
data/private/taste/negatives/.

fit_taste.py uses mean(neg_emb) as the "off-taste / trivial" pole of Johnny's
taste direction:  w = normalize(mean(liked_emb) - mean(neg_emb)).  These are the
shaders that should land near score 0 — exactly the cheap output the old
liked-only centroid scored too high (near-black 78, generic gradient/sphere ~59).

Self-contained: render code is inlined, mirrors data/public/evaluate.py.

Usage:
    python tools/make_negatives.py
"""

from __future__ import annotations

from pathlib import Path

import moderngl
import numpy as np
from PIL import Image

OUTPUT_SIZE = (256, 256)

TOOLS_DIR = Path(__file__).resolve().parent
TASK_DIR = TOOLS_DIR.parent
NEG_DIR = TASK_DIR / "data" / "private" / "taste" / "negatives"

VERTEX_SHADER = """
#version 330
in vec2 in_pos;
out vec2 v_uv;
void main() {
    v_uv = in_pos * 0.5 + 0.5;
    gl_Position = vec4(in_pos, 0.0, 1.0);
}
"""

HEADER = """#version 330
uniform sampler2D u_input;
uniform vec2 u_resolution;
uniform float u_time;
in vec2 v_uv;
out vec4 f_color;
"""

NOISE_LIB = """
float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p){
    vec2 i = floor(p); vec2 f = fract(p);
    float a = hash(i), b = hash(i+vec2(1.,0.)), c = hash(i+vec2(0.,1.)), d = hash(i+vec2(1.,1.));
    vec2 u = f*f*(3.-2.*f);
    return mix(a,b,u.x) + (c-a)*u.y*(1.-u.x) + (d-b)*u.x*u.y;
}
float fbm(vec2 p){
    float v = 0.0, a = 0.5;
    for(int k=0;k<5;k++){ v += a*noise(p); p *= 2.0; a *= 0.5; }
    return v;
}
"""


def _solid(r: float, g: float, b: float) -> str:
    return HEADER + f"void main(){{ f_color = vec4({r}, {g}, {b}, 1.0); }}\n"


def _linear_gradient(ax: float, ay: float, c0: str, c1: str) -> str:
    return HEADER + (
        "void main(){\n"
        f"  float t = clamp(v_uv.x*{ax} + v_uv.y*{ay}, 0.0, 1.0);\n"
        f"  vec3 col = mix(vec3({c0}), vec3({c1}), t);\n"
        "  f_color = vec4(col, 1.0);\n"
        "}\n"
    )


def _plain_fbm(scale: float, tint: str) -> str:
    return HEADER + NOISE_LIB + (
        "void main(){\n"
        f"  float n = fbm(v_uv * {scale});\n"
        f"  vec3 col = vec3(n) * vec3({tint});\n"
        "  f_color = vec4(col, 1.0);\n"
        "}\n"
    )


def _near_black(level: float, scale: float) -> str:
    # Near-black with faint noise — passes the flat gate but is visually empty.
    return HEADER + NOISE_LIB + (
        "void main(){\n"
        f"  float n = fbm(v_uv * {scale});\n"
        f"  vec3 col = vec3({level}) + 0.04 * vec3(n);\n"
        "  f_color = vec4(col, 1.0);\n"
        "}\n"
    )


def _sparse_sparkle(scale: float, thresh: float) -> str:
    # Sparse white sparkles on black — the cheap "starfield" that fools a
    # particle-tuned centroid (the near-black render that scored 78). Trivial.
    return HEADER + NOISE_LIB + (
        "void main(){\n"
        f"  float n = hash(floor(v_uv * {scale}));\n"
        f"  float spark = step({thresh}, n);\n"
        "  vec3 col = vec3(0.01) + spark * vec3(0.7);\n"
        "  f_color = vec4(col, 1.0);\n"
        "}\n"
    )


def _radial_gradient(cx: float, cy: float, c0: str, c1: str) -> str:
    return HEADER + (
        "void main(){\n"
        f"  float d = clamp(distance(v_uv, vec2({cx}, {cy})) * 1.5, 0.0, 1.0);\n"
        f"  vec3 col = mix(vec3({c0}), vec3({c1}), d);\n"
        "  f_color = vec4(col, 1.0);\n"
        "}\n"
    )


# 16 trivial / generic shaders.
NEGATIVES: list[tuple[str, str]] = [
    ("solid_gray", _solid(0.5, 0.5, 0.5)),
    ("solid_white", _solid(0.92, 0.92, 0.92)),
    ("solid_red", _solid(0.75, 0.12, 0.12)),
    ("solid_blue", _solid(0.12, 0.2, 0.7)),
    ("solid_green", _solid(0.15, 0.6, 0.2)),
    ("grad_horiz_blackwhite", _linear_gradient(1.0, 0.0, "0.0,0.0,0.0", "1.0,1.0,1.0")),
    ("grad_vert_bluepink", _linear_gradient(0.0, 1.0, "0.1,0.1,0.4", "0.8,0.4,0.6")),
    ("grad_diag_grayscale", _linear_gradient(0.7, 0.7, "0.1,0.1,0.1", "0.85,0.85,0.85")),
    ("grad_warm", _linear_gradient(1.0, 0.3, "0.9,0.5,0.1", "0.2,0.1,0.3")),
    ("radial_dark", _radial_gradient(0.5, 0.5, "0.6,0.6,0.6", "0.05,0.05,0.05")),
    ("radial_light", _radial_gradient(0.5, 0.5, "0.95,0.95,0.9", "0.3,0.3,0.4")),
    ("fbm_gray", _plain_fbm(6.0, "1.0,1.0,1.0")),
    ("fbm_fine_gray", _plain_fbm(16.0, "0.9,0.9,0.95")),
    ("fbm_blueish", _plain_fbm(8.0, "0.4,0.5,1.0")),
    ("near_black_low", _near_black(0.04, 10.0)),
    ("near_black_sparse", _near_black(0.02, 24.0)),
    ("sparkle_coarse", _sparse_sparkle(48.0, 0.985)),
    ("sparkle_fine", _sparse_sparkle(96.0, 0.99)),
]


def neutral_gray_input() -> Image.Image:
    arr = np.full((OUTPUT_SIZE[1], OUTPUT_SIZE[0], 3), 128, dtype=np.uint8)
    return Image.fromarray(arr, mode="RGB")


def render_shader(fragment_shader: str, input_img: Image.Image, u_time: float = 0.0) -> Image.Image:
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
        if "u_time" in program:
            program["u_time"] = float(u_time)

        fbo.clear(0.0, 0.0, 0.0, 1.0)
        vao.render(mode=moderngl.TRIANGLES)
        data = fbo.read(components=3)
        img = Image.frombytes("RGB", OUTPUT_SIZE, data)

        vao.release()
        vbo.release()
        texture.release()
        fbo.release()
        return img
    finally:
        ctx.release()


def main() -> None:
    NEG_DIR.mkdir(parents=True, exist_ok=True)
    inp = neutral_gray_input()
    n_ok = 0
    for name, shader in NEGATIVES:
        img = render_shader(shader, inp, u_time=0.0)
        out = NEG_DIR / f"{name}.png"
        img.save(out)
        arr = np.asarray(img, dtype=np.float32) / 255.0
        print(f"  rendered {name:24s} std={arr.std():.4f} -> {out.name}")
        n_ok += 1
    print(f"\nWrote {n_ok} negative renders to {NEG_DIR}")


if __name__ == "__main__":
    main()
