# SIA Shader-Synth — Build-Ready Design + Feasibility + Plan

> Output of the background design workflow (9 agents, all facts verified against live code at
> `/Users/johnnysheng/code/sia` and `/tmp/shader-shade`). Captured 2026-06-06.
> Pairs with [hackathon-brief.md](./hackathon-brief.md) and [sia-framework-notes.md](./sia-framework-notes.md).
> **Read the two ⚠️ feasibility findings before building — they change the task definition.**

---

## ⚠️ TWO FINDINGS THAT RESHAPE THE TASK (read first)

**1. BLOCKER — identity passthrough breaks the metric.** Verified in `/tmp/shader-shade`:
the render loop binds the *target* image as `u_input`, and `metrics.py` scores the render against
that *same* target. So `f_color = vec4(texture(u_input, v_uv).rgb, 1.0)` scores LPIPS ≈ 0 on every
held-out image — the held-out split protects nothing, and the demo curve flatlines at the floor in gen_1.
The proposed anti-gaming guards (base64/float-literal checks) do NOT catch this (it embeds nothing).
**Fix (Option A, adopted in the plan): in our `evaluate.py`, bind a NEUTRAL gray/noise texture to
`u_input`, NOT the private target.** The shader must reproduce structure procedurally → passthrough
produces gray (bad score) → held-out split becomes honest → SIA gets real headroom.
*Consequence:* one global `shader.glsl` can't reproduce 18 different images from constant input, so the
task becomes **per-category**: agent ships `shaders/<label>.glsl` keyed to a public category label
(marble/lava/nebula/…) that also exists for the private set. **This is the single biggest design decision.**

**2. HIGH — the descending LPIPS curve is not guaranteed.** SIA's loop is an unconditional
`for current_gen in range(1, max_gen+1)` with **no metric-direction awareness, no best-gen retention,
no rollback** (`best_gen` at `context_manager.py:276` is display-only and hardcoded higher-is-better,
which is BACKWARDS for LPIPS). A regression in gen_3 propagates to gen_4. **Treat the curve as something
you ENGINEER and CURATE from N real runs (cherry-pick the best descender — legitimate), not emit live.**
A guaranteed bankable down-step: engineer the seed so gen_1 sometimes fails to compile, so
`compile_success` 0→1 in gen_2 drops mean_lpips dramatically (failed compile = 1.0 penalty).

**3. MEDIUM — venv Python version.** `run_setup.py:94` runs `uv venv` with no `--python`, so it silently
picks Homebrew 3.14, not 3.11. Works today (cp314 wheels exist for torch/lpips/moderngl) but fragile.
Pin Python 3.11 via a `.python-version` in the run dir (or one-line patch) + pin exact dep versions.

---

## DESIGN

### 1. One-liner + SIA framing
SIA rewrites a GLSL-shader-writing agent across generations; you *watch* mean LPIPS on a held-out image
set drop generation over generation, rendered frames animating beside the targets. shader-shade is a
*fixed* hand-tuned harness; SIA's thesis is the harness should self-improve. We hand SIA a deliberately
weak seed agent (single-pass, no repair/critique/frame-search) and let Meta+Feedback agents rewrite its
source each generation. Every improvement (compile-repair, LPIPS keep-best, vision critique, GLSL
primitives) is a harness edit SIA *discovered*. The "weight update" half is the stretch finale (§8).

### 2. Task definition (`data/public/task.md`)
Procedural shader synthesis, LPIPS-minimization. Agent receives `--dataset_dir` (read-only: task.md,
`glsl_rules.txt`, `targets/` public images) and `--working_dir` (read-write). GLSL contract: first line
`#version 330`; uniforms `u_input` (sampler2D — **neutral texture per Finding #1**), `u_resolution`
(256,256), `u_time` (swept [0,1)); `in vec2 v_uv`; `out vec4 f_color`. Render 256×256, N frames, keep
best frame per target. Produce per-category `shaders/<label>.glsl` + `agent_execution/execution_q{idx}.json`
(MultiTrajectoryLogger). Solver: Nebius `openai/gpt-oss-120b-fast` via OpenAI SDK
(`base_url=https://api.tokenfactory.us-central1.nebius.com/v1/`, `NEBIUS_API_KEY`), JSON output.
Kill the "passthrough is a valid baseline" line. Anti-gaming: held-out targets, reject base64>256 chars,
>24 float literals, source >16KB; behavioral guard rejecting renders correlating >0.98 with `u_input`.

### 3. evaluate.py (fixed, trusted, LLM-free judge)
`TASK_DIR=Path(__file__).resolve().parent.parent.parent`; `PRIVATE_TARGETS=TASK_DIR/data/private/targets`.
Copy verbatim (zero LLM/net deps): from `render.py` → `OUTPUT_SIZE`, `VERTEX_SHADER`, body of
`render_iteration_frames` (101 lines, uniform binds guarded by `if "u_input" in program:`); from
`metrics.py` → `_get_lpips_model`, `_load_image_tensor`, `compute_lpips_multi` (88 lines). Make LPIPS
NON-optional (hard-fail if torch missing). **Bind neutral gray to u_input (Finding #1).** Algorithm:
find submission shaders → anti-gaming checks → compile once (catch `moderngl.Error` → compile_success=0,
mean_lpips=1.0) → for each private target render N=8 frames vs neutral input, `compute_lpips_multi`
keep-best → write `results.json`. Keys: `mean_lpips` (primary, minimize), `compile_success` (hard gate),
`per_target` {label: best_lpips}, `n_targets`, `metric:"lpips"`, `lower_is_better:true`. Metric = LPIPS
primary + compile-success gate (a single optimizable number). Keep the full `per_target` vector (no
scalar collapse). macOS headless GL verified: `moderngl.create_standalone_context()` → `Apple M4 Max`,
GL 4.1 Metal, no flags. LPIPS AlexNet weights = 233MB, cached globally in `~/.cache/torch/hub/checkpoints/`
— pre-warm before demo.

### 4. Dataset plan (24 targets: 6 public / 18 private)
Source: port-orchestration frame corpus `/Users/johnnysheng/code/port-orchestration/resources/frames/<slug>/frame_NN.jpg`
(903 JPGs, 109 slugs verified) — center-crop to square, resize 256×256. Augment with a ~30-line numpy
procedural generator (marble, wood, water caustics, nebula, lava, clouds, circuit, fur) — these are
*ideal* targets because shaders can genuinely reproduce them, so the LPIPS floor is low and improvement
is dramatic. Public = 6 (2 procedural + 4 corpus, the labels the agent fits against). Private = 18
(~12 procedural across 8 categories + 6 curated corpus: bioluminescent-effect-stack, cyber-dithering,
domain-expansion-portal, glass-wormhole, halftone-bloom-sculpture, acid-graphics-process-reveal).
18×8 render+LPIPS ≈ 1s on CPU (600s EVAL_TIMEOUT = huge headroom). Build script: `tools/build_targets.py`.

### 5. Reference seed agent (deliberately weak — the headroom IS the demo)
`reference/reference_target_agent.py`: argparse `--dataset_dir`/`--working_dir` (exactly two flags, per
`orchestrator.py:391`); INTERFACE_CONTRACT + DEFAULT_FRAGMENT_SHADER from `agent.py:18,26`; Nebius OpenAI
client; local `render_iteration_frames` + `compute_lpips_multi` so it can self-score; MultiTrajectoryLogger
(copy `_shared/reference_target_agent.py:103-170`); reads `glsl_rules.txt`. Seed loop: one LLM call per
category from filename only (NO vision), single frame (no u_time sweep), score, log, pick best → write
`shaders/<label>.glsl`. Deliberately LACKS (so SIA discovers each): compile-repair (`fix_compile_errors`),
VLM critique loop (`critique_images`/`run_discovery`), multi-frame keep-best, iterative `edit_shader`,
general-procedure synthesis, GLSL primitive injection. Ship `reference/SAMPLE_TASK_DESCRIPTIONS.md`
(REQUIRED — `load_task_files` throws without it) + `reference/requirements.txt` pinned:
`torch==2.12.0 torchvision==0.27.0 lpips==0.1.4 moderngl==5.12.0 pillow` (drop fastapi/uvicorn/weave).

### 6. Run commands — see Plan §3.

### 7. Demo storyboard (3–4 min)
Hook: "We didn't tune this shader agent — SIA rewrote the agent's own code five times; watch the black
square become the target." Beat 1 (0:30) setup + GLSL contract + gen_1 render. Beat 2 (0:30–1:30, the
money shot) 3-column grid TARGET | gen_1 | gen_5, animated over u_time, 3–4 categories stacked. Beat 3
(1:30–2:15) LPIPS curve descending + compile_success 0→1, labels from each gen's `improvement.md`.
Beat 4 (2:15–3:00) git-style diff gen_1 vs gen_4 `target_agent.py` showing the `fix_compile_errors`
function SIA wrote. Beat 5 (3:00–3:30) restate held-out number + falsification framing. **Pre-build all
assets (GIFs, curve PNG, diff screenshot) by 4:30; never render live.**

### 8. Stretch (Approach B): harness-exhausted → weight update
When harness edits plateau, switch `--focus weights` (needs `TINKER_API_KEY`+Modal, tinker-cookbook
`train.py` contract, Tinker target profile `qwen3-tinker-target`/`gptoss-tinker-target`), same LPIPS
reward. Attempt ONLY if harness is green by 3:30. Cut entirely if no completed weight-update gen by 4:30;
mention verbally in Q&A as "the next lever SIA pulls."

### 9. Fallback (chart reproduction) — same loop, no GL/LPIPS
If headless GL/LPIPS fails on the demo box: agent writes `chart.py` (matplotlib) instead of `shader.glsl`;
evaluate.py runs it in subprocess → PNG → SSIM/MSE (scikit-image + matplotlib, near-baseline deps). Same
CLI contract, Nebius solver, logging, run command, storyboard. ~90% shared. **Decide at the 1pm spike — do
NOT build both.**

### 10. Integration: port-orchestration / SOTARE
SOTARE: reuse no code (it scores prose, not pixels). Borrow framing for Q&A: "held-out + falsification
gate" and "scalar_collapse FORBIDDEN" (keep the per_target vector). port-orchestration: lift TWO assets
only — (1) the frame corpus → dataset (§4); (2) GLSL primitives (`primitives/*.md`: fbm-noise,
domain-warp, halftone, sobel-edge, chromatic-aberration, dither-1bit) → seed prompt toolbox; optional
`taste-axes.md` rubric into a VLM critique sub-prompt if SIA adds a vision loop (stays OUT of the scored
metric). Do NOT reuse its dashboard/graph/BMAD/tmux machinery (path-coupled, fights SIA's own loop).

---

## FEASIBILITY VERDICTS

- **MEDIUM — render+LPIPS works on host; the risk is unpinned heavy deps on Python 3.14.** Measured on
  M4 Max: headless GL OK, full 18×8 render+LPIPS = 1.0s, AlexNet cached globally (0.9s warm load), broken
  shaders raise catchable `moderngl.Error`. Blocker = `uv venv` picks 3.14 (no `--python`); relies on
  cp314 wheels (today OK: torch 2.12.0, torchvision 0.27.0, lpips 0.1.4, moderngl 5.12.0). Venv is 602MB,
  built ONCE per run (~15s warm cache); per-gen `install_requirements` is a ~20ms no-op. **Mitigate:** pin
  3.11 + exact dep versions; pre-warm AlexNet + uv wheel cache; pre-build venv off the clock.
- **BLOCKER — identity passthrough (Finding #1 above).** `texture(u_input,v_uv)` scores ≈0 because the
  evaluator feeds the target as u_input. Mitigate with Option A (neutral input + per-category shaders);
  add behavioral guard (reject render correlating >0.98 with u_input); pre-flight: run the 3-line
  passthrough through evaluate.py — if it scores ≈0, the metric is still broken.
- **HIGH — curve not guaranteed to descend (Finding #2 above).** No best-gen retention/rollback/direction.
  Mitigate: run early, run 3–5× and cherry-pick the best descender, engineer compile_success 0→1 down-step,
  pre-build all assets.

---

## BUILD PLAN

**GO** on shaders with Option-A metric baked in from minute one.

**First 20-min spike (whole team, GO/NO-GO gate):** clean `uv venv --python 3.11`, install
`torch torchvision lpips moderngl pillow numpy`, prewarm AlexNet, then render a passthrough shader vs a
**neutral gray input** and a structured shader; **pass criterion: passthrough scores clearly WORSE than
structured.** If passthrough still wins → metric broken → chart fallback.

**Hour-by-hour (12:30→6:00), 4 tracks** — A: eval/render/dataset · B: seed agent + task spec ·
C: SIA runs + curation · D: demo frontend + slides.
- 12:30–1:00 run the spike (all), pin 3.11, prewarm caches, set both API keys.
- 1:00–2:00 build_targets.py + 24 PNGs (A); task.md Option-A + glsl_rules (B); patch interpreter + pin
  reqs (C); 3-column grid harness (D).
- 2:00–3:00 evaluate.py neutral-input + smoke-test (A); weak seed agent + SAMPLE_TASK_DESCRIPTIONS (B);
  **HARD CUT-LINE 3:00 first `sia run --max_gen 5` launched** (C); LPIPS-curve PNG generator (D).
- 3:00–3:30 harden evaluate (A); tune seed so gen_1 sometimes fails compile (B); run SIA 3–5× background
  (C); wire real renders into grid (D). **3:30 HARD CUT-LINE: harness green or cut weights.**
- 3:30–4:30 cherry-pick best run, re-render vs private targets, build all 3 demo assets.
  **4:00–4:30 assets frozen. 4:30 cut weights if not working.**
- 4:30–5:30 dress rehearsal + Q&A prep (esp. the passthrough question). 5:30–6:00 buffer + load on
  presentation machine.

**Cut-lines:** 3:00 SIA launched · 3:30 green-or-cut-weights · 4:00–4:30 assets frozen · 4:30 weights cut.

**Exact run command:**
```bash
export NEBIUS_API_KEY=...; export ANTHROPIC_API_KEY=...
python -c "import lpips; lpips.LPIPS(net='alex')"   # prewarm 233MB AlexNet
python -c "import moderngl; print(moderngl.create_standalone_context().info['GL_RENDERER'])"
python sia/tasks/shader-synth/tools/build_targets.py
printf "3.11\n" > runs/run_1/.python-version    # OR patch run_setup.py:94 to `uv venv --python 3.11`
sia run --task_dir /Users/johnnysheng/code/sia/sia/tasks/shader-synth \
  --target-agent-profile gptoss-nebius-target --meta-agent-profile default-meta \
  --max_gen 5 --run_id 1
# run_id 2..5 too, then: jq '.mean_lpips' runs/run_*/gen_*/results.json — keep the cleanest descent
```

**MVD (60% case):** one cherry-picked run, LPIPS curve descending, static TARGET|gen_1|gen_N strip for
2–3 categories, gen_1-vs-gen_N target_agent.py diff. Bankable down-step = compile_success 0→1. Frame as
"best of N real runs," show per_target vector.

**Files to create** (under `sia/tasks/shader-synth/`): `data/public/{task.md,evaluate.py,glsl_rules.txt}`,
`data/public/targets/` (6), `data/private/targets/` (18), `reference/{reference_target_agent.py,
SAMPLE_TASK_DESCRIPTIONS.md,requirements.txt}`, `tools/build_targets.py`.
**Copy from:** `/tmp/shader-shade/backend/{render.py,metrics.py,agent.py,vision.py}`,
`/tmp/shader-shade/notes/glsl_rules_condensed.txt`, `sia/tasks/_shared/reference_target_agent.py`.
