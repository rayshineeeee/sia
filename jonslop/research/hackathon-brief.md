# Hackathon Brief — SIA Emergency Hackathon (AGI House SF "Ascension")

> Captured 2026-06-06 during the event. Source: organizer blasts + slides + on-site brief.
> This is the canonical context dump for the build. See also [sia-framework-notes.md](./sia-framework-notes.md).

## The premise

A paper dropped last week that changes how self-improving agents get built.
Emergency Saturday hackathon to "hack towards the next great leap."

**The repo:** SIA — Self-Improving AI with Harness & Weight Updates (Hebbar et al., 2026).
arXiv: 2605.27276. We are building **on top of** the SIA framework.

Headline numbers from the paper:
- **502%** improvement on single-cell RNA denoising
- **91.9%** runtime reduction on GPU kernels
- **56.6%** gain on LawBench

Core idea: today every agent's harness *and* weights get tuned by humans. SIA closes
the loop — a language-model agent that rewrites both its own harness and the underlying
weights of a task-specific agent.

## Tracks (pick one)

1. **Applied AI Track** — use SIA on a real domain task. *(Our lean: this one — "find an applied AI use case.")*
2. **Framework Enhancement Track** — improve the SIA framework itself.
3. **Research Track** — novel evaluation or self-improvement methodology.

**Prize:** Meta Ray-Bans for 1st place in **each** track.

## Logistics / constraints

- **Total build time: ~5 hours.** Hacking 11:30 AM → 6:00 PM (lunch 12:30).
- **Demo: 3–4 minutes per team + live Q&A from judges** (starts 6:00 PM).
- Teams of 2–4, formed on-site.
- **GPU compute: Nebius H200s** via **Nebius Token Factory** — instant model access for
  **DeepSeek, Qwen, GLM, Gemma, NVIDIA Cosmos**. (SIA already ships a `nebius` provider +
  Nebius profiles — plug-and-play, see framework notes.)
- WiFi PW: `attentionisallyouneed`
- Agenda: doors 10:00 · opening 10:45 · hack+teams 11:30 · lunch 12:30 · hack ends 6:00 ·
  demos 6:00 · judging 7:00 · awards 7:30 · adjourn 8:30.

## Framework architecture (from slides)

**The big question:** "Can *we* build an *AI* that can achieve *any* goal we assign?"

Loop (3 agents):
- **Human/Expert** (e.g. Oncologist) *defines* a **Goal** (e.g. "discover drug for cancer").
- **Meta Agent** *creates or updates* a **Task-Specific Agent**.
- Task-Specific Agent runs → produces a **Performance metric** (e.g. "works on 7/100 people").
- Metric feeds back to the Meta Agent → it updates the agent again. Repeat.

### Two kinds of self-improvement (from the sample `improvement.md` slides)

**(A) Harness Update** — Generation g → g+1, weights π_θ held fixed:
- Trajectory observations (τ_g): dominant failure mode, secondary issue, what's working (don't regress).
- Proposed scaffold edits, by component: system prompt / tool dispatch / answer extraction /
  retry & search logic — each with a change + rationale.

**(B) Weight Update** — when the harness is exhausted:
- Why harness is exhausted: stall signature (harness-only Δ < threshold over k generations),
  residual failure mode not reachable by any prompt/tool edit, what scaffold did well (keep as fixed harness).
- **Why TTRL, not PPO/GRPO/DPO:** verifier signal is sparse/noisy/unavailable on test partition →
  deterministic grader can't be invoked per rollout. Instead use **test-instance consensus across N
  sampled rollouts → majority-vote pseudo-reward.** Rollouts cheap to batch; no value head; no preference pairs.
- Training config: base model `gpt-oss-120b` (SIA default), adapter = **LoRA rank r** (bounded parameter movement).

### Research-track seed from slides: "Autonomous Goal Proposer"
- Prior work: human provides a predefined task → agents ideate → agents implement. (✗ no task-discovery stage.)
- Their NEW approach: a **Task-Discovery** stage where the agent *self-discovers* a valuable, novel
  research question — **no human-defined task needed** — then ideates and implements.

## The 4 showcase tasks (HEXOLABS demo benchmarks)

These are what the SIA team demoed — useful as bar-setters and as templates for our own Applied AI task.

### Task 1 · Long-context NLP — LawBench (Chinese criminal charge prediction)
- Read a Chinese court case (事实/prosecutor summary) → predict the criminal charge (罪名) from a
  fixed taxonomy of **191 labels**. Exact-string match is the only thing that counts.
- Why non-trivial: 191 classes, many semantically adjacent (盗窃 theft vs 抢劫 robbery vs 抢夺 snatching);
  compound labels reproduced char-for-char incl. punctuation; published baseline is weak.
- Scoring: random 0.5% · vanilla LLM ~7% · published Meta-harness baseline ~45% · **SIA result 70.1%**.

### Task 2 · GPU kernel optimisation — TriMul (the bottleneck inside AlphaFold3)
- Rewrite the **Triangle Multiplicative Update** from scratch in **Triton** so it runs in fewer µs on
  the same H100. Faster kernel, same answer, lower cost per prediction.
- Why non-trivial: pure-PyTorch submissions rejected (must be a real Triton kernel); **no local testing**
  (no GPU on host — syntax-validate then ship to Modal cloud); Triton 3.3.1 is finicky.
- Hardware H100 (single GPU, Modal-hosted). Metric runtime µs (geo mean across shape grid).
  **SIA result: 1017 µs best fused kernel** (≈14× speedup over baseline per README).

### Task 3 · Computational biology — scRNA-seq denoising
- Single-cell sequencing data is riddled with false zeros. Rewrite the matrix with the values that
  should be there so downstream science (cell typing, disease tracking) works.
- Why non-trivial: **two metrics** (prediction error + biological-plausibility check — optimizing one
  breaks the other); **no labelled truth** (molecular cross-validation: split each cell's molecules in
  half, denoise one, score vs the other); bar is a published algorithm (MAGIC, Cell 2018).
- Scoring: MAGIC baseline 0.3047 (pred error, lower better) · **plausibility gate ≥ 0.97** (below → rejected)
  · **SIA result 0.289** (beats published baseline). (README quotes 0.289 MSE_norm vs prior SOTA 0.220.)

### Task 4 · End-to-end ML engineering — MLE-bench Hard (Google Brain Ventilator Pressure Prediction)
- OpenAI's benchmark of real Kaggle comps graded vs original human leaderboards; "Hard" tier.
- Ventilator Pressure Prediction (Google Brain Kaggle 2021): predict airway pressure during mechanical
  ventilation from control-signal inputs. System must explore raw data, design a model, train, and submit
  a leaderboard-grade CSV **autonomously**.
- Why non-trivial: open-ended (no function signature, no test set); long-horizon (hours of compute,
  failures compound); graded against humans (medal thresholds from the real Kaggle leaderboard).
- Scoring (1/MAE, higher better): Claude Code (frontier coding agent) 2.1124 · **SIA result 7.3855**
  (≈6× lower error).

## Working assumptions for our build

- We lean **Applied AI Track**: pick a *real domain task*, express it in SIA's task contract, and let the
  self-improvement loop beat a credible baseline — with a crisp 3–4 min demo + a live metric.
- Use **Nebius H200** models as the target/meta agents (gpt-oss-120b, Qwen3-80B, Kimi-K2.6, GLM, Gemma,
  DeepSeek) since credits are free and the provider is already wired in.
- The win condition for the demo: a **clear baseline → SIA-improved metric curve over generations**,
  on a task a judge immediately understands matters.
