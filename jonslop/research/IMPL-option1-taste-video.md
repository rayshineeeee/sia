> ⚠️ **SUPERSEDED (2026-06-06).** Medium pivoted **video → shaders** (video render too slow for the loop). The
> taste mechanism here still applies; the render/model layer is replaced. Active plan:
> [IMPL-FINAL-taste-shader.md](./IMPL-FINAL-taste-shader.md).

# IMPLEMENTATION PLAN — Option 1: Taste-Video (thin-merge)

> Executable plan. Every task has an explicit **Input → Output** and a **traceable artifact (file)** so each
> change is auditable. Grounds: [taste-video-design.md](./taste-video-design.md) (code-level detail),
> conversation decisions, verified SIA contract. Parachute: [shader-sia-design.md](./shader-sia-design.md).
> **Companion plan:** [IMPL-option3-sidecar.md](./IMPL-option3-sidecar.md) — built in parallel, demoed together.

## GOAL (the live e2e flow that must work on stage)
`sia run` over a new **taste-video** task → a multi-generation run where SIA rewrites a *prompt-writer* agent to
score higher on a CLIP **taste-proxy** fit once from a human ranking → we pick the best gen → render **before/after
video** → demo shows: **mood-board (memory) → injected taste context → SIA self-improvement loop → before/after
video + running-max taste curve + prompt diff**, narrated as the Personalized Prompt Harness architecture.

## HARD CONSTRAINTS (no major structural changes to SIA)
- **Zero edits to SIA core** for Option 1. Everything lives under `jonslop/tasks/taste-video/`. SIA sees it only
  via `--task_dir`. (Option 3 owns the additive SIA-core hooks; Option 1 must run on stock SIA.)
- Run venv = **Python 3.12** (stock `uv venv` picks 3.14 → torch wheels missing). `--sandbox none`.
- Taste vector `w` lives in `data/private/` (agent's `--dataset_dir` = `data/public` only).
- Primary metric key = `accuracy`, emitted on a **0–100** scale, higher-is-better (SIA retention/curve contract).

## PREREQUISITES (gate — Task A0 must pass before anything downstream)
API keys: `NEBIUS_API_KEY` (image), `ANTHROPIC_API_KEY` (prompt-writer + meta), `OPENAI_API_KEY` (optional VLM
gate), `FAL_KEY` (demo video only). Verified image-gen base_url (design's `us-central1` host is suspect).

## TASK TABLE
Tracks: **A**=Infra/SIA · **B**=Data/Proxy · **C**=Task/Agent · **D**=Demo. `⊣` = depends on.

| ID | Trk | Input | Output (traceable artifact) | File / change | Box | Acceptance | ⊣ |
|----|----|-------|------------------------------|---------------|-----|------------|---|
| **A0** Spike/gate | A | API keys | GO/NO-GO; verified `IMAGE_BASE_URL`; `.venv`(3.12); cached CLIP weights at fixed `HF_HOME` | `.venv/`, `jonslop/tasks/taste-video/.hfcache/`, note `IMAGE_BASE_URL` | 30m | `import torch,open_clip,sia` OK **and** one `images.generate` returns b64 | — |
| **B1** Batch render | B | fixed subject + 14 style suffixes | 14 candidate stills | `…/data/public/moodboard/cand_*.png` via `tools/make_batch.py` | 25m | 14 PNGs exist, non-degenerate | A0 |
| **B2** Human rank | B | 14 stills | ordered ranking | `…/moodboard/ranking.json` + renamed `rank_NN_*.png` | 10m | 12–16 entries best→worst | B1 |
| **B3** Captions | B | ranked stills | per-frame captions | `…/moodboard/captions.json` | 10m | one caption/ranked frame | B2 |
| **B4** Fit proxy | B | ranking + stills | taste vector + **pairwise-acc number** | `…/data/private/taste_proxy.npz`; stdout acc | `tools/fit_taste.py` | 20m | npz has `w,lo,hi,holdout_*`; pairwise acc printed (the demo's licensing number) | B2 |
| **C1** task.md | C | design §2 | task spec the agent reads | `…/data/public/task.md` | 20m | matches contract; uses verified `IMAGE_BASE_URL` | A0 |
| **C2** evaluate.py | C | design §4 | the fixed scorer | `…/data/public/evaluate.py` (+`judge_prompt.txt`) | 40m | standalone `--gen-dir` on a dummy render writes `results.json` w/ `accuracy`∈[0,100] | B4 |
| **C3** seed agent | C | design §5 | deliberately-weak prompt-writer + required files | `…/reference/{reference_target_agent.py,SAMPLE_TASK_DESCRIPTIONS.md,requirements.txt}` | 30m | runs standalone → writes `prompt.txt`+`renders/seed{0,1,2}.png`+`agent_execution.json` | A0 |
| **C4** memory card (thin-merge bridge) | C | ranking + proxy provenance | provenance-backed "preference memory card" (Option-3 contract shape) | `…/data/public/preference_memory_card.json` | 15m | JSON matches Prompt-Context-Contract fields (`id,text,confidence,source_ids`) — the artifact that visually unifies opt1↔opt3 | B4 |
| **A1** 1-gen smoke | A | C1–C3, B4 | proof the loop closes | `runs/run_smoke/gen_1/results.json` | 20m | nonzero `accuracy`; run venv is 3.12 | C1,C2,C3,B4 |
| **A2** N runs | A | smoke green | 3–4 real runs | `runs/run_{1..4}/gen_*/{results.json,prompt.txt,renders/}` | 30m+bg | each ≥3 gens with results.json | A1 |
| **A3** best-gen select | A | all runs | best (run,gen) by max `accuracy` | `…/demo/best_gen.json` (pointer) | 10m | reproducible selection across `runs/*/gen_*/results.json` | A2 |
| **D1** curve PNG | D | results.json across gens | **running-max** taste curve | `…/demo/taste_curve.png` via `tools/plot_curve.py` | 20m | monotone running-max plotted from raw results.json (NOT context.md) | A2 |
| **D2** before/after video | D | gen_1 prompt + best-gen prompt | 2 clips | `…/demo/before.mp4`, `after.mp4` via `tools/render_video.py` (fal, `generate_audio:false`, best gen `seed0.png` as `image_url`) | 30m | both mp4s play; after visibly more on-taste | A3 |
| **D3** prompt diff | D | gen_1 vs best-gen `prompt.txt` | side-by-side diff artifact | `…/demo/prompt_diff.md` | 10m | shows `prompt=SUBJECT` → SIA-authored taste injection | A3 |
| **D4** deck | D | D1–D3 + B2 moodboard + B4 acc | slides incl. architecture frame | `…/demo/deck.(md|pdf)` | 40m | storyboard §7 beats; closing = Prompt-Harness platform slide | D1,D2,D3,C4 |

## TIMELINE MAPPING
- **T+0:00–0:30** A0 (whole team watches; gate). HARD CUT: if A0 red → parachute to shader-synth.
- **T+0:30–1:30** B1→B2→B3 ‖ C1 ‖ C3 ‖ D scaffold.
- **T+1:30–2:30** B4 ‖ C2 ‖ C4 ‖ A1 (1-gen smoke). HARD CUT 2:30: no nonzero `results.json` → fix loop only.
- **T+2:30–3:30** A2 (N runs, bg) ‖ D1 ‖ D2 (once fal ok) ‖ D3.
- **T+3:30–4:30** A3 ‖ D4. HARD CUT 4:30: lock deck + mp4s; no live renders after.
- **T+4:30–6:00** dress rehearsal ×2 + Q&A drill.

## DEMO ACCEPTANCE (e2e that must run)
1. Show `preference_memory_card.json` + moodboard → "this is the encoded taste (memory), with provenance."
2. Show `taste_curve.png` rising (running-max) + `prompt_diff.md` → "SIA wrote the taste-injection; the metric drove it."
3. Play `before.mp4` vs `after.mp4` → "same frozen model, same seed — feel the difference."
4. Closing slide = the Prompt-Harness architecture (bridge to Option 3).

## RISKS → MITIGATIONS (detail in design doc feasibility)
R1 deps/timeout → 3.12 venv + pinned `requirements.txt` + pre-cached `HF_HOME` + loud asserts (A0,C2,A1).
R2 wrong image endpoint / no video → A0 verifies endpoint; **image before/after is the guaranteed spine**, video is a bonus (D2 time-boxed). R3 non-monotonic curve → N runs + best-gen select + running-max plot (A2,A3,D1).
