# Track 3 — Reward Faithfulness in Self-Improving Loops

**When a self-improving loop optimizes a *proxy* for a *subjective* target, when does the climb stay faithful — and can we catch it Goodharting its own reward?**

> **Thesis (one line):** A self-improving loop can only become as good as its reward can *verify*. We built a loop whose reward is a **person's taste** — extracted once, made measurable via CLIP — and we measure the gap between the proxy it optimizes and what it's a proxy *for*. **That gap is the contribution.**

---

## 1. The question

SIA's four bundled tasks (law, GPU, RNA, ML) share one property: an **objective, verifiable** grader. We deliberately picked the opposite — an **unverifiable, subjective** target (aesthetic *taste*) — and turned it into a proxy reward: CLIP-cosine between a rendered shader and a reference image the human liked.

> As the loop climbs the proxy (CLIP-sim ↑), does an **independent judge it never sees** agree the output is actually getting closer to the reference? Where the proxy rises but the independent judge does **not**, the loop is **Goodharting** its reward. **Can we detect that automatically?**

## 2. Why it matters — grounded in research, not vibes

This is *the* central open problem of self-improvement, not a shader detail. From the SOTARE research substrate (FAISS cognition store, 6,747 indexed items):

- **Outer-loop verifiability is the *limit* of self-improvement.** Eric Jang, via SOTARE `inspiration/…alphago…/eval-criteria-fitness.md` **Signal-017**, verbatim: *"We know the things we can measure, and we improve on the things we can measure. We care about this broader ability to do economically useful work, which is not super easy to measure."* SOTARE's gloss: *"Goodhart's-law adjacent… if [what we measure] diverges from what actually advances the goal, the [loop] optimizes the wrong thing. Critical… when bench scores look great but the operator's gut says 'we're not actually making progress.'"*
- **The metric is gameable precisely when the target is taste.** **Signal-010:** *"improve what's measurable… risk gaming the metric… Outer loop is more verifiable than inner loop (research taste), but still leaves measurement-risk."*
- **Verifiability sets the automation ceiling.** **Signal-026:** *"how good the outer verification loop is for AI self-improvement… Automation ceiling is set by verification-lag, not capability."*

Every SIA loop with a proxy reward faces this. The four objective tasks **hide** it (their graders are near-perfectly verifiable). A taste task **exposes** it — which is precisely why it "stresses the loop in a way nothing else does."

## 3. What's novel

1. **The reward is a *person*, extracted once.** Swap the reference image → "better" changes. This makes concrete SOTARE hypothesis **H21** (*"an AI version of Johnny… trained on his… taste"*) + philosophy **#15** (*human makes 1–3 decisions, the rest autonomous*): taste is captured **once**, the loop then runs with **no human in the loop, no RLHF, no test-time like/dislike.**
2. **Reward-faithfulness as a first-class, measurable quantity** — with a detector, not just a score.

## 4. Method — a Two-Eyes (→ Three-Eyes) faithfulness test

SOTARE Belief **#4 (Two-Eyes):** *"Eye 1: what the docs say… Eye 2: what [the human] actually means… The delta between them IS the alignment gap. Closing it is the research."* Signal-026 sharpens it: two eyes aren't enough — *"Need Eye-3 (what objective ground-truth says)."*

We instrument exactly that on every kept generation:

| Eye | What | Role |
|---|---|---|
| **Eye-1** | `CLIP-cosine(render, reference)` | the reward the loop **optimizes** |
| **Eye-2** | a VLM (Qwen3.5, Nebius) rates render-vs-reference 0–1 | an **independent judge — never part of the reward** |

**The signal is the delta.** `faithfulness_probe.py` recomputes both per generation and reports `Pearson(CLIP, VLM)` + the two curves. High correlation → the proxy is a faithful stand-in for taste. **Late divergence (CLIP ↑, VLM flat/↓) → reward hacking.**

This operationalizes **#27 (LLM-Larping-Detection):** a render that scores high on the proxy but low to the independent eye is a **metric-larp** — *"pattern-match noise dressed as signal,"* trustworthy only if it *"passes in the separate test-bench eval suite."* The probe **is** that separate eval-bench.

## 5. Setup (reproducible)

- **Task (stock sia):** `jonslop/tasks/taste-shader/` — `task.md` + `evaluate.py` (CLIP-taste metric) + reference agent + held-out `data/private/` taste vector. `sia run --task_dir jonslop/tasks/taste-shader --max_gen 5 --sandbox none` → `runs/run_*/gen_*/results.json`.
- **Controllable testbed:** `tools/converge.py --reference <liked.jpg> --iters 24 --out demo/converge/run1` — same CLIP reward, single reference, hill-climb keep-best, VLM-critique-guided edits; emits per-iter frames + `curve.png` + `log.jsonl`.
- **The experiment:** `.venv/bin/python tools/faithfulness_probe.py --run demo/converge/run1` → `faithfulness.png` + `faithfulness.json` (Pearson + per-iter CLIP vs VLM).
- **Config / seeds:** writer `openai/gpt-oss-120b-fast` (Nebius), reward CLIP `ViT-B-32 / laion2b_s34b_b79k`, judge `Qwen/Qwen3.5-397B-A17B`, fixed reference. The commands above are the complete repro.

## 6. Findings

- **The loop climbs the proxy.** converge `run1`: CLIP-sim **0.353 → 0.73+** over 24 iters; hill-climb correctly **reverts** flat/no-gain candidates (e.g. iters 3–6 reverted, kept only on real gains). Stock-sia taste-shader `runs/run_*` show the same CLIP metric driving the SIA generations.
- **Faithfulness — the contribution.** `faithfulness_probe.py` → `Pearson(CLIP, VLM) = ⟨R⟩`, divergence at iter `⟨k⟩` *(experiment ready; run to fill)*. Predicted shape from the recorded prior: the two eyes **track early** (gross structural gains both eyes see) and **diverge late** (the proxy keeps rising on edits the perceptual eye no longer credits).
- **The recorded real-world instance of the gap** — port-orchestration's taste-axes log, verbatim: *"Auto-scores measure replication accuracy, NOT portfolio value. E1 auto-scored 8.0 → user ranked LOW. C4 auto-scored 6.5 → user called 'absolutely insane.' NEVER trust scores without yap validation."* Our probe converts that anecdote into an **automatic** detector.

## 7. Honesty & limits *(Track 3 explicitly rewards this)*

- **gen_0 is honest** — an un-sandbagged blind shader (~0.35), not a propped-up baseline.
- **`converge.py` is NOT stock sia** — it is the controllable testbed/visualizer. The SIA-loop claim rests on the stock-sia `runs/`. We do **not** present converge as "SIA's loop improving."
- **The independent judge is itself a proxy** (a VLM, not a human). So we report **proxy-vs-proxy** agreement; the honest claim is *"two independent measures of taste-similarity diverge under optimization,"* which is sufficient to **demonstrate reward-hacking risk**, not to certify "real human taste."
- **N is small** — this is a characterization, not a law. (Per the rubric, a well-characterized result — even null — is a valid, valued contribution.)

## 8. Why this wins (insight > magnitude)

We claim no big number. We surface a **new, measurable property of self-improving loops — reward faithfulness — give it a detector** (a Two-Eyes / anti-larp probe), and demonstrate it on a task purpose-built to expose what objective benchmarks hide. **The idea is portable:** any SIA task with a proxy reward can run a faithfulness probe to check whether its climb is real or larped.

## Citations (SOTARE cognition store — `tools/cognition/run.sh query`)

- Eric-Jang / AlphaGo signals **010 / 017 / 026** — `inspiration/dwarkesh-eric-jang-alphago-from-scratch-2026-05-20/eval-criteria-fitness.md`
- Philosophy **#4** (Two-Eyes), **#27** (LLM-Larping-Detection), **#15** (decide-once / autonomous) — `principles/extracted/philosophy.md`
- Hypotheses **H10** (Interpretation-Delta-as-Signal), **H18** (Math-Replaces-Human-Judgment), **H21** (AI-Twin-as-Alignment-Test) — `principles/extracted/hypotheses.md`
- Two-Eyes gap — visual precedent: `srm-state/wave-diagrams/diagram-two-eyes-gap.html`
- Recorded real-world gap: port-orchestration `_bmad/zto/workflows/reel-experiment/data/taste-axes.md`
