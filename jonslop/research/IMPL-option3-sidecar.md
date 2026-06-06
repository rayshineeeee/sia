> ⛔ **DROPPED — OUT OF SCOPE (2026-06-06).** Johnny decided to ship **Option 1 (taste-video) only**; no new
> sidecar. This file is kept as a record of the thinking. The "personalization platform" idea survives only as an
> optional closing-slide narrative for the demo, not a build. Active plan: [IMPL-option1-taste-video.md](./IMPL-option1-taste-video.md).

# IMPLEMENTATION PLAN — Option 3: Personalization Sidecar (minimal demoable slice)

> Executable plan. Every task has explicit **Input → Output** + a **traceable artifact (file)**. Grounds:
> Johnny's Personalized-Prompt-Harness architecture doc, verified SIA contract. **This is the minimal demoable
> slice, NOT the full architecture** (full = multi-day). Companion: [IMPL-option1-taste-video.md](./IMPL-option1-taste-video.md)
> — built in parallel, demoed together.

## GOAL (the live e2e flow that must work on stage)
A **personalization sidecar** turns a provenance-backed **memory card** into a "Personalization Context" block
injected into SIA's `build_meta_prompt` via an **optional** param + CLI flag. Run the SAME task with
`--personalization-mode off` vs `assist` → show the **injected card**, the **original→personalized prompt diff**,
the **resulting output difference**, and a **reflector** that promoted that card from a small clarification log.
Story: "SIA personalizes the prompt that enters its own loop, and learns the defaults from your history."

## HARD CONSTRAINTS (no major structural changes to SIA)
- All SIA-core touches are **additive + optional + no-op when `--personalization-mode off` (the default)**, so
  stock behavior (and Option 1's run) is byte-identical when the flag is unused.
- **Golden-test gotcha:** `prompts.py` is pinned by `tests/test_prompts_snapshot.py`. The new param MUST default
  to `None` and, when `None`, return the **exact** prior string → existing goldens stay green; new goldens added
  only for the context-present case.
- Package isolated in `sia/personalization/`. **Build in a git worktree** (it edits core files Option 1 doesn't),
  so parallel execution with Option 1 can't collide.

## PREREQUISITES (gate — O0)
A tiny **preference-sensitive A/B task** to demo on (reuse a bundled task, or a 1-file "build X" task where a
stored preference visibly changes the output). A seeded **event/clarification log** (2–3 synthetic sessions) for
the reflector to mine. `ANTHROPIC_API_KEY` (meta agent + reflector LLM).

## TASK TABLE
Tracks: **E**=Engine/package · **H**=SIA hooks · **R**=Reflector/memory · **G**=Demo. `⊣` = depends on.

| ID | Trk | Input | Output (traceable artifact) | File / change | Box | Acceptance | ⊣ |
|----|----|-------|------------------------------|---------------|-----|------------|---|
| **O0** Gate/scope | E | SIA repo | chosen A/B task + worktree | git worktree `../sia-opt3`; note A/B task id | 15m | worktree builds; A/B task runs stock | — |
| **O1a** events | E | doc §components | JSONL event append/read | `sia/personalization/events.py` | 20m | append+read round-trips an event | O0 |
| **O1b** store | E | memory schema | load/save/query memory cards (JSON MVP; SQLite-FTS optional) | `sia/personalization/store.py` | 25m | load profile → list typed cards | O0 |
| **O1c** retrieval | E | task kind + cards | ranked relevant cards (intent filter + recency/confidence) | `sia/personalization/retrieval.py` | 25m | given task kind returns top-k cards w/ source_ids | O1b |
| **O1d** injector | E | ranked cards + policy | "Personalization Context" block **+ structured prompt delta** (provenance, precedence) | `sia/personalization/prompt_injector.py` | 30m | emits block ≤ max_tokens; delta JSON matches Prompt-Context-Contract | O1c |
| **O2** seed profile | R | the doc's contract + Johnny's prefs | profile w/ preference/recipe/negative cards + provenance | `sia/personalization/profiles/local.json` | 20m | ≥2 cards w/ `id,text,confidence,source_ids` | O1b |
| **O3** prompts hook | H | `sia/prompts.py` | optional `personalization_context=None` in `build_meta_prompt` (+`build_feedback_prompt`), placed after task spec, labeled w/ precedence | diff `sia/prompts.py` (+ new goldens) | 30m | `context=None` → byte-identical to prior (goldens green); context set → block present after task spec | O1d |
| **O4** CLI/config | H | `sia/cli.py`,`config.py` | flags `--personalization-{profile,mode,max-tokens,explain-sources}` | diff `sia/cli.py`,`sia/config.py` | 25m | `--help` shows flags; mode default `off` | O0 |
| **O5** orchestrator hook | H | `sia/orchestrator.py` | call injector pre-`build_meta_prompt` if mode≠off; persist original/personalized prompt + source_ids | diff `sia/orchestrator.py`; `runs/run_N/personalization/{original_prompt.txt,personalized_prompt.txt,sources.json}` | 30m | mode=off → no artifacts, prompt unchanged; mode=assist → artifacts written, block injected | O3,O4,O1d |
| **O6** reflector | R | seeded clarification log | promote a stable preference → reflection card | `sia/personalization/reflector.py`; new card in `profiles/local.json`; `demo/reflection_card.json` | 35m | given 2 sessions w/ same clarification → emits 1 card w/ evidence+confidence | O1b,O2 |
| **O7** A/B run | G | A/B task | off vs assist run artifacts | `demo/ab_off/`, `demo/ab_assist/` (run dirs) | 25m | both complete; assist's meta-prompt contains the card | O5,O2 |
| **O8** diff + metric | G | O7 artifacts | prompt-diff + outcome-diff (+ optional clarification/first-pass number) | `demo/prompt_diff.md`, `demo/outcome_diff.md` | 25m | diff clearly shows injected card changed the output toward the preference | O7 |
| **O9** deck section | G | O6,O8 | sidecar slides (architecture + reflector-learned card + A/B) | `demo/deck_opt3.(md|pdf)` | 30m | tells "personalize the prompt SIA sees + learn it from history" | O6,O8 |
| **O10** together-bridge *(optional)* | G | Opt1 `preference_memory_card.json` | run taste-video w/ `--personalization-mode assist` → taste card injected into its meta-prompt | `runs/run_taste_assist/personalization/personalized_prompt.txt` | 20m | the SAME card drives BOTH the prompt-writer (opt1) and SIA's meta-prompt (opt3) | O5, Opt1.C4 |

## TIMELINE MAPPING (parallel with Option 1, separate worktree)
- **T+0:00–0:30** O0 (worktree + A/B task) ‖ (Option 1 A0).
- **T+0:30–1:30** O1a/b/c/d (package) ‖ O2 (seed profile).
- **T+1:30–2:30** O3 (prompts hook + goldens) ‖ O4 (CLI) → O5 (orchestrator hook). **CUT 2:30:** if hooks aren't injecting cleanly, freeze scope to "injector + prompt-diff artifact" (skip reflector) — that alone demos the architecture.
- **T+2:30–3:30** O6 (reflector) ‖ O7 (A/B run) → O8 (diff/metric).
- **T+3:30–4:30** O9 deck ‖ O10 together-bridge (only if Option 1's run is green). **CUT 4:30:** lock artifacts.
- **T+4:30–6:00** integrate with Option 1's demo; rehearse the unified narrative.

## DEMO ACCEPTANCE (e2e that must run — degrade gracefully)
**Spine (must-have):** show `profiles/local.json` card → `prompt_diff.md` (original vs personalized meta-prompt) →
the off-vs-assist output difference. This alone proves "provenance-backed personalized context injection into SIA."
**+1:** `reflection_card.json` → "the reflector promoted this card from these 2 sessions" (the second loop).
**+2 (together):** O10 — the same memory card drives Option 1's prompt-writer AND Option 3's SIA meta-prompt.
**Fallback if hooks slip:** present the injector output + prompt-diff statically (no live run) — the architecture
still reads, framed as the platform Option 1 instantiates.

## RISKS → MITIGATIONS
- **Golden tests break on `prompts.py` edit** → param defaults `None` returns identical string; regenerate goldens
  only for the context-present case; run `pytest tests/test_prompts_snapshot.py` after O3 (acceptance gate).
- **Numbers-demo is weak** (the core Option-3 risk) → lead with the *prompt diff* (visceral, shows injected card)
  not the metric; the reflector-learned card is the "self-improvement" beat; keep the metric as supporting evidence.
- **No conversation logs** (doc's open Q#1) → use a **seeded** synthetic clarification log for the reflector; state
  it's seeded; the mechanism is the point.
- **Scope overrun kills the demo** → CUT-lines at 2:30 (drop reflector) and 4:30 (lock). Spine = injector + diff.

## HOW THE TWO EXECUTE TOGETHER (handoff to the execution workflow)
- **Isolation:** Option 1 = new files only under `jonslop/tasks/taste-video/` (stock SIA). Option 3 = core edits in
  a **worktree** (`../sia-opt3`). No file collisions → safe true-parallel build.
- **Shared artifact:** `preference_memory_card.json` (Opt1 C4) = the bridge consumed by Opt3's injector (O10).
- **Unified demo:** one architecture (Prompt Harness) shown at two layers — visual taste (Opt1 video) + working-
  style memory (Opt3 sidecar). Applied-AI proof + Framework-Enhancement depth in one story.
- **Execution workflow (next step, after review):** parallel tracks Opt1(A–D) + Opt3(E–G) in worktree isolation;
  each task fans out by the table above (input→output→file already specified); a final integration+verification
  phase merges Opt3's worktree, runs `pytest tests/test_prompts_snapshot.py`, and dry-runs both demos e2e.
