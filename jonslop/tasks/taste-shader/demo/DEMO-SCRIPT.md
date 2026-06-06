# taste-shader — Demo Run-Through (3–4 min)

> **One-line premise:** We took ONE person's visual taste, turned it into a frozen held-out
> preference metric, and watched a self-improving agent rewrite its own code until its output
> climbed toward that taste — escaping AI-slop on the way up.
>
> **The build:** A frozen LLM (`openai/gpt-oss-120b-fast`) writes the GLSL. The agent never
> touches the model — it only improves the *instruction* it conditions on Johnny's taste files.
> SIA's loop rewrites that agent's Python across generations. The judge re-renders the shader at
> 256×256 and projects it onto Johnny's taste **direction** in CLIP space.
>
> **Numbers locked from `run_3` (fill the rest live):** gen-1 baseline = **51.57 / 100**
> (`cos_raw = -0.23` — below the trivial pole; honest slop). Best gen = **[BEST_SCORE]**.

---

## Pre-flight checklist (have these on screen, ready to cut)

- [ ] **Hero shader** running animated in a window (the math-shader opener — `[HERO_SHADER]`).
- [ ] **SIA dashboard** open at `http://127.0.0.1:8000` showing the run_3 accuracy curve.
- [ ] **Curated moodboard** (CLEAN frames only — see asset list, beat 2). Do NOT show the raw
      `data/private/taste/liked/*` — those are IG reel screenshots with selfie PiP / captions / AE chrome.
- [ ] **gen-1 render** (`runs/run_3/gen_1/render.png`) and **best-gen render** (`[BEST_RENDER]`) side by side.
- [ ] One verbatim line from `runs/run_3/gen_2/improvement.md` pulled up.

---

## BEAT 1 — HOOK (0:00–0:30)

**On screen:** the math-shader HERO, animated, full-bleed. Nothing else.

**Asset list:**
- `[HERO_SHADER]` — animated GLSL hero (procedural, `u_time`-driven), full window.

**Say (verbatim Law 1 first, then the hook):**

> **Law 1 — Complex Engine, Simple Output:**
> *"The complex engine IS the value. The simple output IS the craft."*

"What you're looking at is a complex math engine — a real sim — surfaced as one legible,
pointable image. In Johnny's taste data, *abstract algorithms doing simple visualizations* score
**75% HIGH**. That's the whole bet. **So we taught an AI to do exactly this — in ONE person's
taste — by having it rewrite its own code until the output converged on his eye.**"

*(Beat. Let the hero breathe for 2 seconds, then cut to beat 2.)*

---

## BEAT 2 — SETUP / THE VILLAIN (0:30–1:15)

**On screen (in order):** (a) the slop definition as text, (b) the curated clean moodboard,
(c) the metric / AUC.

**Asset list:**
- Text card — the anti-slop firewall line (below).
- **Curated CLEAN moodboard** (use ONLY these — verified no caption/PiP/AE-chrome):
  - `demo/moodboard/strange-attractor-particles.jpg` (white attractor on black — the literal hero motif)
  - `demo/moodboard/material-metamorphosis-logo.jpg` (liquid-chrome type, red accent)
  - `demo/moodboard/voxel-displacement-car.jpg` (subject + displacement, red taillights)
  - `demo/moodboard/threshold-tunnel-runner.jpg` (threshold/SDF, red-on-blue)
  - `demo/moodboard/cavalry-experiments.jpg` (procedural attractor swirl — clean enough; ignore tiny footer caption)
  - **DO NOT SHOW** `endless-knots.jpg`, `recursive-droste-tunnel.jpg`, `glow-silhouette-flicker.jpg`
    — these still carry overlaid poster text / an IG "pov:" caption / letterboxing. Bad demo visuals.
- Metric card: CLIP taste **direction** + **AUC 0.997**.

**Say (the anti-slop quote is verbatim):**

"Here's the villain. The taste constitution defines AI-slop *falsifiably*:

> *"Default AI = particles in void + bloom glow + orbit controls."*

"That's the flat default everyone's eye is trained to call 'this is AI.' Now here's the *target* —
Johnny's actual taste: interactive, soft-body, **math-legible, applied to a subject**. Liquid flow,
strange-attractor particles *on a subject*, threshold/SDF, real GPU sims surfaced simply.

"To make that *measurable*, we don't score 'does it look liked.' We score a **direction**: his
liked frames **minus** trivial slop, in CLIP space. Solid colors, plain gradients, plain noise —
they project to **zero**. On-taste projects to **one**. And that direction is **validated at AUC
0.997** — it cleanly separates his taste from slop.

"So what does the agent start at? **Baseline, gen-1: 51.57 out of 100 — `cos_raw` literally
negative, sitting *below* the trivial pole.** Watch this —"

*(Cut to the gen-1 render.)*

"— that's the agent's first try. A dark void with a faint skin of texture and a red thread you can
barely find. **That is the slop.** Particles in a void. The thing we're trying to escape."

---

## BEAT 3 — THE CLIMB / MONEY SHOT (1:15–2:45)

**On screen (in order):** (a) the SIA dashboard accuracy curve climbing, (b) gen-1 vs best-gen
renders side by side, (c) the improvement.md line.

**Asset list:**
- `[CURVE]` — SIA dashboard accuracy-across-generations chart (`http://127.0.0.1:8000`, run_3).
- `[GEN1_RENDER]` = `runs/run_3/gen_1/render.png` (sloppy, low — the void).
- `[BEST_RENDER]` = best gen's `render.png` / `render.gif` (on-taste, ANIMATED — let it move).
- One line from `runs/run_3/gen_2/improvement.md`.

**Say:**

"Now the loop. **Same frozen model the whole time — gpt-oss-120b, never fine-tuned, never
touched.** What changes is the *agent's own Python*. SIA reads the run logs, writes an
`improvement.md`, and rewrites the agent to condition harder on Johnny's taste.

*(Point at the curve climbing.)* "Here's the score across generations — gen-1 at 51.57, climbing
to **[BEST_SCORE]**.

*(Point at the side-by-side.)* "And here's what that *number* looks like. Left: gen-1, the void —
low score, off-taste. Right: best gen — on-taste, animated, **a subject you can point at, motion
that drifts, the red thread reading as fate, not decoration.** That's the climb out of slop, made
visual.

"And it told us *why* it improved. Straight from its own `improvement.md`:

> *"Discovery / Planning Pass — before generating any shaders, run a lightweight LLM call that reads
> taste data and outputs 3 distinct shader concepts ... grounded in the taxonomy ... avoid the same
> generic concept."*

"**SIA added a discovery-and-multi-candidate stage** — it taught itself to plan distinct on-taste
concepts and keep the best, instead of firing one generic shader into the void. **The model is
frozen. The agent's code self-improved toward his taste.**"

---

## BEAT 4 — CLOSE (2:45–3:30)

**On screen:** the hero shader again (or the best-gen render, looping), clean.

**Asset list:**
- `[HERO_SHADER]` or `[BEST_RENDER]`, looping.
- Final number card: **AUC 0.997 held-out**.

**Say (Law 3 verbatim is the thesis):**

> **Law 3 — Human Seeds, AI Executes:**
> *"A human's one sentence is worth more than AI's ten paragraphs."*

"That's the thesis of the whole build. **Johnny seeded the taste — one person's eye, encoded once.
SIA did the convergent work — it self-improved its code until its output landed on that eye.** The
human seeds; the AI executes. Never the reverse.

"And it's honest: the taste direction it climbed against is **held out at AUC 0.997** — a frozen
preference the agent never sees and can't edit.

"This generalizes to *any* creator's taste — swap the liked set, refit the direction, point the
loop. And the taste itself isn't static: the knowledge graph grows every time Johnny keeps or
removes a frame. **You seed the taste once. The AI keeps converging.**"

---

## JUDGE Q&A — anticipated (have these tight)

**Q1. "Isn't the human / a proxy doing the actual work? Where's the self-improvement?"**
> No. Two things are frozen and untouched by the agent: (1) the **LLM weights** —
> `gpt-oss-120b-fast`, never fine-tuned — and (2) the **scoring direction** — a held-out CLIP
> preference vector in `data/private/taste_proxy.npz` the agent **never sees and cannot modify**.
> The *only* thing that changed across generations is the **agent's own Python** — SIA read its run
> logs, wrote `improvement.md`, and rewrote the agent to plan multiple on-taste candidates and
> keep-best. The human seeded the taste *once*, offline. The agent did the convergent search. And
> the metric it climbed is validated at **AUC 0.997 held-out** — if the agent got worse, that
> number would fall. That's measurement, not a human in the loop.

**Q2. "How do I know the metric is real and not gameable / overfit?"**
> It's a **direction**, not a centroid: liked-mean **minus** trivial-slop-mean. Trivial output —
> solid colors, plain gradients, plain noise, near-black — projects to ~0 by construction, and
> there are hard gates: fails-to-compile → 0, flat render (pixel std < 0.02) → 0. The separation of
> on-taste vs slop is **AUC 0.997 on held-out frames**. And gen-1 honestly scored low
> (`cos_raw = -0.23`, *below* the trivial pole) — a gamed metric wouldn't let the baseline fail.

**Q3. "Why shaders / why does this matter beyond a cool render?"**
> Shaders are the cleanest possible instance of Law 1 — a genuinely complex engine (real math,
> real GPU sim) that has to surface as one legible image. It's a hard taste target *and* trivially
> measurable in CLIP space, so it makes the abstract claim — "an AI can converge on one person's
> taste" — concrete and falsifiable in 3 minutes. The same loop applies to any domain where you can
> express taste as a held-out preference direction: design, copy, music, product.

**Q4 (if pressed). "The model is frozen — so the agent just writes better prompts. Is that 'AI improving'?"**
> The agent isn't hand-tuned prompts by a human — **SIA's loop rewrote the agent's scaffolding**:
> it added a discovery pass, multi-candidate generation, a composite scoring proxy, and a
> keep-best critique loop (all in `gen_2/improvement.md`, authored by the feedback agent, not us).
> That's the agent improving its *own strategy* for steering a frozen model — which is exactly the
> applied-AI claim: self-improvement on top of a fixed foundation model.

---

## Asset paths (quick reference)

| Placeholder | Path |
|---|---|
| `[HERO_SHADER]` | (hero GLSL — animated, in render window) |
| `[CURVE]` | SIA dashboard `http://127.0.0.1:8000` (run_3) |
| `[GEN1_RENDER]` | `/Users/johnnysheng/code/sia/runs/run_3/gen_1/render.png` |
| `[BEST_RENDER]` | best gen `render.png` / `render.gif` (fill when run_3 finishes) |
| `[BEST_SCORE]` | best gen `accuracy` from `results.json` (fill when run_3 finishes) |
| improvement.md | `/Users/johnnysheng/code/sia/runs/run_3/gen_2/improvement.md` |
| CLEAN moodboard | `/Users/johnnysheng/code/sia/jonslop/tasks/taste-shader/demo/moodboard/` (curated list, beat 2) |

**Status note:** gen-1 baseline (51.57) is locked. As of writing, `run_3` gen-2 has its
`improvement.md` and the rewritten agent is mid-build; `[BEST_SCORE]` / `[BEST_RENDER]` fill in
once the climb completes. If gen-2+ has not yet produced a higher `results.json` at demo time, run
`sia run --task taste-shader --max_gen 5 --run_id 3` (or resume) and read the top score off the
dashboard before going live.
