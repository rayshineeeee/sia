# IMPLEMENTATION PLAN — FINAL · Taste-Shader

> The locked build. Supersedes `IMPL-option1-taste-video.md` (video medium dropped — render too slow for the loop)
> and `IMPL-option3-sidecar.md` (dropped). Merges the taste-personalization mechanism with shader-shade's
> free/fast local render. Verified against live code: SIA contract + `/tmp/shader-shade`. Diagram: `flow-diagram.html`.

## GOAL (the live e2e flow)
SIA rewrites a **prompt-writer** agent so a **frozen LLM** (gpt-oss-120b on Nebius) writes a GLSL shader in *your
taste*; ModernGL renders it (free, local); a **CLIP taste-proxy** (fit once from your ranking) scores it; over
generations the taste score climbs. Demo = gen-1 generic shader vs best-gen taste-matched shader, side by side +
the taste-score curve + the prompt/GLSL diff.

## ARCHITECTURE (the shape you confirmed: prompt-writer → frozen LLM → GLSL)
```
[your ranking] --fit once--> Taste Memory (CLIP vector, private)
                                  │ (public moodboard read by agent)
   SIA loop  --rewrites-->  Prompt-writer (target_agent.py)
                                  │ taste-conditioned instruction (prompt.txt)
                                  ▼
                          Frozen LLM = gpt-oss-120b (Nebius)  --> shader.glsl
                                  ▼
                          ModernGL render (render.py)         --> render.png
                                  ▼
                          CLIP taste-proxy (evaluate.py)      --> accuracy (0-100)
                                  │ feedback
                                  └────────► SIA rewrites the prompt-writer next gen
```
- **The only API per iteration is cheap text** (gpt-oss writes GLSL; Claude meta/feedback rewrites the agent).
  No image/video API. Render + CLIP are local. → fast, free iterations.
- **No target image** → the passthrough/gaming exploit from shader-synth does not apply; the shader is purely
  procedural and judged only on taste-match.

## HARD CONSTRAINTS
- Stock SIA, new files only under `jonslop/tasks/taste-shader/` (no SIA-core edits).
- Run venv = **Python 3.12** (stock `uv venv` picks 3.14 → torch/open_clip wheels missing). `--sandbox none`.
- Taste vector `w` in `data/private/` (agent's `--dataset_dir` = `data/public` only).
- Primary metric key = `accuracy`, **0–100 scale**, higher-is-better (SIA retention/curve contract).
- Pre-cache CLIP weights into a fixed `HF_HOME` before the run (avoid the 600s eval-timeout cold-download).

## WHAT YOU PROVIDE (the taste input shape — finalized)
**Decision: drop (a) ranking. Use a SWIPE onboarding (B, made interactive) + a reference set (C). No fallbacks.**
1. **The brief** — ONE line, the subject every shader renders, held constant so only taste varies.
   e.g. `"an abstract flowing organic plasma texture"`. → goes in `task.md`. *(still owed by Johnny)*
2. **Swipe onboarding (B, interactive):** a Tinder-style frontend shows **16 diverse images** (varied niches /
   concepts / places); you **swipe like / dislike** through all 16. The two buckets → `likes.json` / `dislikes.json`.
   This is the PIA-style onboarding — it captures taste with no prior knowledge needed.
3. **Reference set (C):** ~8–12 images you've *already* found and love → folded in as extra "liked" anchors.
4. **(optional) taste sentence** — `"moody, organic, muted earth tones, high contrast, no neon"` → `taste.md`.

**These become a real eval benchmark:** `fit_taste.py` embeds likes+refs vs dislikes with CLIP, fits a preference
direction, and **holds out** some swipes to report a separation accuracy — that held-out number is what makes the
taste-proxy a defensible benchmark, not a vibe.

**Frontend = the swipe UI (onboarding) + SIA's live dashboard + a before/after strip.** Build is **cycle by cycle**,
each cycle gated by a verification you approve (see `flow-diagram.html` → "Build cycles → verification gates").
**No fallbacks** — single path (gpt-oss on Nebius · ModernGL · CLIP).

**Minimum to unblock scaffolding right now:** the **brief (1 line)**. The 16 onboarding images I can source/curate
across niches; you bring the reference set whenever ready.

## SHADER-SHADE REUSE MAP (files to copy/adapt)
| From `/tmp/shader-shade` | Into taste-shader | Change |
|---|---|---|
| `backend/render.py` (`render_iteration_frames`, `OUTPUT_SIZE`, `VERTEX_SHADER`) | `evaluate.py` (re-render trusted) + seed agent (self-render) | pass a **neutral gray** as `input_img` (no target); keep uniforms guarded |
| `backend/agent.py` (`generate_initial_shader`, `edit_shader`, `fix_compile_errors`, `INTERFACE_CONTRACT`, `DEFAULT_FRAGMENT_SHADER`) | the frozen-LLM calls in the seed agent | repoint `OpenAI(base_url=Nebius, key=NEBIUS_API_KEY, model="openai/gpt-oss-120b-fast")`; reaim instruction "match target" → "render brief in this taste"; strip `weave` |
| `notes/glsl_rules_condensed.txt` | `data/public/glsl_rules.txt` | copy verbatim; injected into the GLSL prompt |
| `backend/vision.py` (`critique_images`) | optional VLM co-gate in `evaluate.py` | prime on the top-ranked moodboard; optional |
| `backend/metrics.py` (LPIPS) | — | **not used** (no target); replaced by CLIP taste-proxy |

## TASK CONTRACT (files to create under `jonslop/tasks/taste-shader/`)
- **`data/public/task.md`** — the brief + the GLSL contract (#version 330, `u_input`/`u_resolution`/`u_time`,
  `in v_uv`, `out f_color`) + "encode TASTE in palette/structure/texture; subject is fixed" + "you cannot see the
  score" + submission = `shader.glsl` (+ `prompt.txt`, `renders/seed0.png`, `agent_execution.json`).
- **`data/public/glsl_rules.txt`** — copied from shader-shade notes.
- **`data/public/evaluate.py`** — the trusted scorer: re-render `gen_dir/shader.glsl` via `render_iteration_frames`
  (neutral input) → CLIP-embed → project onto private taste vector → `accuracy` (0–100). Gates: compile-fail → 0;
  flat-render (pixel-std<0.02) → 0; held-out ranked exemplars must order correctly under `w` or → 0; optional VLM
  co-gate. results.json: `accuracy, taste_score, clip_taste, vlm_taste, compile_ok, holdout_ok`.
- **`data/public/taste/moodboard/`** — ranked renders + `ranking.json` (+ captions). Public face of the memory.
- **`data/private/taste_proxy.npz`** — `w, lo, hi, model, pretrained, holdout_emb, holdout_rank`. Private.
- **`reference/reference_target_agent.py`** — deliberately weak seed prompt-writer: builds a **generic** instruction
  (ignores the moodboard), calls frozen gpt-oss → GLSL, renders, writes outputs. What it LACKS = what SIA discovers:
  reading the moodboard captions, extracting taste tokens, style + negative-style suffix, compile-repair
  (`fix_compile_errors`), multi-candidate self-selection.
- **`reference/SAMPLE_TASK_DESCRIPTIONS.md`** — REQUIRED (run crashes without it). One line.
- **`reference/requirements.txt`** — pinned: `torch open_clip_torch torchvision moderngl pillow numpy openai`.
- **`tools/make_batch.py`** — generate ~14 candidate shaders (varied style instructions) → render → moodboard.
- **`tools/fit_taste.py`** — Bradley-Terry on CLIP features → `data/private/taste_proxy.npz`; prints pairwise acc.
- **`tools/plot_curve.py`** — running-max taste curve PNG from `runs/*/gen_*/results.json`.

## RUN COMMANDS
```bash
cd /Users/johnnysheng/code/sia
export NEBIUS_API_KEY=...          # the ONLY key — meta (Kimi) + target (gpt-oss) both run on Nebius; CLIP+render are local
export HF_HOME=/Users/johnnysheng/code/sia/jonslop/tasks/taste-shader/.hfcache
~/.local/bin/uv venv .venv --python 3.12
~/.local/bin/uv pip install --python .venv/bin/python -e '.[openhands]' torch open_clip_torch torchvision moderngl pillow numpy openai
.venv/bin/python -c "import torch, open_clip, moderngl, sia; print('DEPS OK')"
.venv/bin/python -c "import open_clip; open_clip.create_model_and_transforms('ViT-B-32', pretrained='laion2b_s34b_b79k')"  # prewarm
.venv/bin/python jonslop/tasks/taste-shader/tools/make_batch.py     # 14 candidate renders
#   --> you rank: write moodboard/ranking.json
.venv/bin/python jonslop/tasks/taste-shader/tools/fit_taste.py      # data/private/taste_proxy.npz (COMMIT)
.venv/bin/sia run --task_dir $PWD/jonslop/tasks/taste-shader \
  --target-agent-profile gptoss-nebius-target --meta-agent-profile kimi-nebius-meta --max_gen 5 --sandbox none
# run 3-4x (different run_id), pick best gen by max accuracy, plot running-max, screenshot before/after renders
```

## TIMELINE (tracks A=infra · B=taste batch+proxy · C=agent+task · D=demo)
- **0:00–0:30** A: 3.12 venv + deps + verify `import torch,open_clip,moderngl` + prewarm CLIP + confirm Nebius gpt-oss text call. **GATE.**
- **0:30–1:30** B: `make_batch.py` → renders → you rank → `ranking.json`. C: `task.md` + `glsl_rules.txt` + seed agent. A: `evaluate.py`.
- **1:30–2:30** B: `fit_taste.py` (print pairwise acc, commit npz). A: 1-gen smoke (`--max_gen 1`, nonzero accuracy). **CUT 2:30.**
- **2:30–3:30** A: 3–4 `--max_gen 5` runs (bg). D: plot curve + render harness.
- **3:30–4:30** A: pick best gen. D: before/after render strip + prompt diff + deck. **CUT 4:30: freeze assets.**
- **4:30–6:00** dress rehearsal ×2.

## DEMO (3–4 min)
Hook → moodboard + pairwise-acc number → taste-score running-max curve + gen-1-vs-best `prompt.txt`/GLSL diff
("SIA wrote that taste conditioning") → **before/after shader renders side by side** ("feel the difference") →
framework claim (personalize a frozen model on the cheap text+render slice).

## RISKS → MITIGATIONS
1. **torch/open_clip on 3.14** → 3.12 venv + pinned reqs (gate, 0:00).
2. **CLIP cold-download blows eval timeout** → prewarm into fixed `HF_HOME` (0:00).
3. **Curve not monotonic** (no best-gen retention) → 3–4 runs, pick best, plot running-max (2:30–4:30).
4. **gpt-oss endpoint/JSON** → verify text call at gate; fallback `qwen-nebius-target` or Claude as the GLSL writer.
