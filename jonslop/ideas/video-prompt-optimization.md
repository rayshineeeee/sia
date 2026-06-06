# Idea: SIA optimizes LTX-2 video prompts (advisor-suggested)

> Source: voice transcript with an experienced advisor (35 hackathons), 2026-06-06.
> Status: CAPTURED, not decided. Gated on a GO/NO-GO spike (below).

## The idea
Scope SIA to the **prompt layer** of a video-gen pipeline. SIA's target agent = a text
agent that writes prompts for **LTX-2** (Lightricks' open-source video model). The harness
loop (Meta + Feedback) evolves the prompt-writing agent across generations to get better
scenes / better input-adherence out of LTX-2. LTX-2 is a black-box renderer downstream —
**SIA never fine-tunes it.**

Origin: Lightricks (LA; "fine-tune Fridays") open-sourced LTX-2 + a LoRA fine-tune cookbook
(2B/13B) to make videos adhere to inputs / render a character (their example: "get Yoda to
render better").

## Why it's attractive
- Demo wow ceiling >> shaders — video generation is visceral on stage.
- Advisor principle: **win hackathons by designing the DEMO first and working backwards.**
  Don't misrepresent, but the demo matters more than every component being perfect.
- Smart scoping move: put SIA on the part of the pipeline you CONTROL (prompt text) to
  sidestep the infra you DON'T (video-model weights / Tinker).

## The snag the advisor flagged — CONFIRMED (2026-06-06, verified vs code + live docs)
- **Tinker (Thinking Machines) is LLM-only** — Qwen3 / Llama 3 / Kimi-K2 / gpt-oss. It will
  NOT fine-tune LTX-2 (video diffusion). SIA's only weight profiles are `gptoss-tinker-target`
  / `qwen3-tinker-target` (text LLMs; GRPO via tinker-cookbook — `sia/prompts.py`,
  `sia/config.py:71`).
- => SIA's WEIGHT-UPDATE half is OFF the table for LTX-2. BUT the prompt-only framing means
  we never use Tinker → snag dissolved. We'd demo SIA's **harness-update half only**, which
  is fine (the design notes treat weights as the stretch anyway).

## Open risks — MUST spike before committing (rules 2 / 6 / 13)
1. **METRIC (the crux).** SIA needs a deterministic, hard-to-cheat scalar. "Nicer scene" via
   VLM/CLIP = fuzzy + gameable (the exact weakness the shader analysis rejected). Strongest
   candidate: **image-to-video keyframe reconstruction** — score generated frame vs a held-out
   target frame (LPIPS/MSE, reusing existing machinery). If the best metric is "a VLM says it's
   nicer" => NO-GO.
2. **LATENCY x eval count.** Each SIA eval = generate an LTX-2 clip (seconds-minutes).
   x prompts x generations x rollouts can blow the 5-hr clock. Shader eval = 1s. Time ONE clip
   in the spike, multiply by a max_gen=2 eval count.
3. **COMPUTE PATH.** Nebius free compute hosts NVIDIA Cosmos (video) but NOT LTX-2. LTX-2 =
   fal.ai (paid API) or self-host. Options: fal.ai LTX-2 (simplest, pay) / self-host /
   swap model to Nebius Cosmos (free).
4. **No published baseline.** Graft "naive prompt" as the baseline analog (like synth-from-label).

## Decision rule
Run a ~20-min GO/NO-GO spike answering 1-3. PASS => higher-wow path, take it.
FAIL any => fall back to de-risked **shader restore/enhance** (green, full build plan ready).

## Reusable patterns from the advisor (worth keeping past this hackathon)
- Design the demo first, work backwards from it.
- Scope the self-improving loop onto the pipeline stage you control; treat un-tunable infra
  as a fixed black box.
