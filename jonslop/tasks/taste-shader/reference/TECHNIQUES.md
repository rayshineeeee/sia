# TECHNIQUES — reachable headroom for the taste-shader agent

This file is an EXEMPLAR for the meta/feedback agent. It is NOT loaded by the seed
target agent and NOT hardcoded into gen-1. It summarizes the patterns that let an
agent climb the taste-direction score: condition hard on Johnny's taste, render the
animation and keep the best frame, self-critique with a VLM and edit, repair compile
errors, and run a discovery/gap pass first. These are distilled from a working
shader pipeline (`/tmp/shader-shade/backend/{agent.py,vision.py,render.py}`).

The seed agent does NONE of these. Each one is a lever the loop can pull.

---

## 0. What the judge actually rewards (so optimize for THIS)

`evaluate.py` re-renders `shader.glsl` for `N=8` frames over `u_time in [0,1)`,
CLIP-embeds each frame, projects the (normalized) embedding onto the taste
DIRECTION `w = normalize(mean(liked) - mean(trivial-negatives))`, and keeps the
BEST frame:

    score = clip((emb·w - lo) / (hi - lo), 0, 1)   per frame; accuracy = 100 * max_frame(score)

Implications the agent should exploit:
- It is a DIRECTION, not a lenient centroid. Trivial output (solid color, plain
  gradient, plain fbm, near-black) projects near `lo` -> score ~0. You only gain by
  moving TOWARD Johnny's taste AND AWAY from generic shader-slop.
- Animation can only help: spreading visual variety across the 8 `u_time` frames
  gives the judge more chances to find a high-scoring frame.
- Flat frames (pixel std < 0.02) score 0. Keep contrast and structure.

---

## 1. Condition hard on the taste files (biggest lever)

The seed ignores `taste/`. Read them and turn them into prompt constraints:
- `taste/taste-dna.md` — the constitution / Laws / verdicts.
- `taste/TASTE-SYNTHESIS.md` — what scores HIGH vs DROP (steer toward HIGH, name
  the DROP patterns as an explicit NEGATIVE-style suffix to avoid).
- `taste/taxonomy.md` — the vocabulary of palette / motion / structure / mood.
- `taste/knowledge-graph.json` — recurring motifs (mine node labels / edges for
  concrete nouns and color words to inject into the prompt).

Build a POSITIVE block ("palette, motion, structure, mood, motifs to include") and a
NEGATIVE block ("avoid: generic glossy spheres, teal-orange flow, flat noise,
near-black emptiness — these score ~0"). The direction metric pays for both.

## 2. Discovery / gap pass BEFORE generating (Phase A)

Pattern from `run_discovery()`. Do one LLM call that READS the taste synthesis and
emits a structured plan:
- SIMILAR: which on-taste techniques to reuse directly.
- DIFFERENT: which generic shader habits to drop.
- BRIDGE NEEDED: adaptations to move a plain procedural shader toward Johnny's taste.
- Emit two tailored prompts: `initial_prompt` (first shader) and `edit_prompt`
  (how to revise under critique). Feed these into the generate/edit calls.

## 3. Render the animation and KEEP THE BEST frame

Use the inlined `render_frames(shader, gray, num_frames=8)` (already in the seed file,
unused). Render all 8 `u_time` frames, save `frames/frame_00.png`..`frame_07.png`, a
`render.gif` (PIL `save_all=True, append_images=...`, loop=0), and `render.png` = the
best frame. Pick "best" by your own proxy (e.g. contrast + your VLM critique). The
judge independently re-renders and maxes over frames, so giving it more on-taste
frames is free upside.

```python
frames = render_frames(shader, neutral_gray_input(), num_frames=8)
frames[0].save(working_dir / "render.gif", save_all=True,
               append_images=frames[1:], duration=120, loop=0)
best = max(frames, key=score_proxy)          # your own taste/contrast proxy
best.save(working_dir / "render.png")
```

## 4. Self-critique with a VLM, then edit (the convergence loop)

Pattern from `vision.py: critique_images()` + `agent.py: edit_shader()`. After the
first shader:
1. Render best frame.
2. Ask a VLM to critique it against the taste intent in a FIXED priority order:
   COLOR/CONTRAST first, then STRUCTURE, TEXTURE, EDGES. Force a 1-10 similarity
   score and a concrete "what to change" list.
3. Feed the critique into an `edit_shader` call that rewrites the GLSL.
4. Pace it: EARLY iterations = bold structural changes; LATE iterations = refinement
   only. Keep-best across iterations (never regress below your best score so far).

## 5. Compile-repair loop (never ship a 0)

Pattern from `fix_compile_errors()`. A shader that fails to compile scores 0. On a
compile/render exception, send the GLSL + the exact compile error back to the model
with "fix the error, keep the visual intent, obey the interface contract", and retry
(2-3 attempts). Always validate the FINAL shader compiles before writing it.

## 6. Multi-candidate selection

Generate K candidate shaders (vary temperature / seed wording), render + score each
with your proxy, and keep the best. Cheap diversity, monotone gain under a max.

---

## Interface contract (every generated shader must obey)

- `#version 330` on the first line (NOT `#version 300 es`).
- `in vec2 v_uv;` (v_uv in [0,1]); uniforms `sampler2D u_input; vec2 u_resolution; float u_time;`.
- `out vec4 f_color;`. Entry `void main()` (NOT Shadertoy `mainImage`).
- Single fragment shader, no multipass/buffers. Procedural content (judge uses a
  neutral gray input). Animate via `u_time`.
