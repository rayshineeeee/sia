# SIA Framework Notes — codebase findings

> Captured 2026-06-06 by reading the repo. This is what we need to know to build fast.
> Pair with [hackathon-brief.md](./hackathon-brief.md). A full `/understand` knowledge graph
> is being generated in the background for deeper navigation.

## What SIA actually is

A self-improvement loop coordinating **three agent roles** over successive *generations*:

1. **Meta-Agent** — reads `task.md` and writes the initial `target_agent.py`.
2. **Target / Task-Specific Agent** — runs the task, logs actions/results to `agent_execution.json`.
3. **Feedback / Improvement Agent** — reads the logs + eval metrics, writes `improvement.md` and the
   next generation's `target_agent.py`.

Each generation's artifacts land in `runs/run_{id}/gen_{n}/`:
`target_agent.py`, `agent_execution.json`, `improvement.md` (gen 2+), `submission.*`, `results.json`.
A live dashboard auto-starts at `http://127.0.0.1:8000` during a run (`--no-web` to disable).

## CLI (entry point: `sia run`)

```bash
sia run --task lawbench --max_gen 5 --run_id 1
sia run --task_dir ./tasks/my-task --max_gen 5 --run_id 1   # <-- custom task = Applied AI track
```

Key flags (`sia/cli.py`):
- `--task {gpqa,lawbench,longcot-chess,spaceship-titanic}` **xor** `--task_dir <path>` (required).
- `--max_gen` (default 3), `--run_id` (default 1).
- `--meta-agent-profile` / `--target-agent-profile` — JSON profiles bundling agent_impl + model + provider.
- `--focus {harness,weights}` — **harness** (default; code/prompt edits) or **weights** (RL/TTRL weight tuning).
- `--training_sandbox {modal,sandboxfusion}` — for `train.py` execution in weights mode (default modal).
- `--sandbox {none,docker}` — target agent execution sandbox.
- `--no-web`, `--web-port`, `--web-host`.

## The task contract (how to add a domain task — the Applied AI track)

A task is **just a directory**. Point `--task_dir` at it. Layout (mirrors `sia/tasks/<name>/`):

```
my-task/
├── data/
│   ├── public/
│   │   ├── task.md            # task description the agent reads (REQUIRED)
│   │   ├── evaluate.py        # defines evaluate(submission_path)->dict + main(--gen-dir) (REQUIRED)
│   │   ├── *.csv / data files # train/test/sample_submission, classes.json, etc.
│   └── private/
│       └── test.csv           # held-out ground truth (agent must NOT see this)
└── reference/
    ├── SAMPLE_TASK_DESCRIPTIONS.md
    └── reference_target_agent.py   # seed/example agent
```

### `task.md` — the spec the agent reads
Free-form markdown. Effective ones (see `sia/tasks/lawbench/data/public/task.md`) include:
Background · Data (files + columns) · Objective · **Evaluation** (orchestrator auto-runs it) ·
Constraints · **Submission Format** (e.g. `submission.csv` with exact columns, saved to `working_dir`) ·
Baseline Context (zero-shot vs SOTA numbers) · **Model** to use as the solver (e.g. `openai/gpt-oss-120b`).

### `evaluate.py` — the grader (see `EVALUATION_GUIDE.md`)
- Must expose `evaluate(submission_path: Path) -> dict` and a `main()` that accepts `--gen-dir`.
- Flow: orchestrator runs `python evaluate.py --gen-dir gen_n/` → your script finds the submission
  (e.g. `submission.csv`), compares to `data/private/` ground truth, writes `gen_n/results.json`.
- Return dict is flexible; top-level scalars get surfaced into the feedback context.
- Ground truth lives in `data/private/` so the agent can't peek.

**Implication for us:** building an Applied AI task = (1) write `task.md`, (2) drop public data +
`data/private` ground truth, (3) write `evaluate.py`. Then `sia run --task_dir ...` does the rest.

## Agent implementations (`sia/agent_impls/`)
- `claude.py` — Claude Agent SDK (Claude models only). Install `sia-agent[claude]`.
- `openhands.py` — multi-provider (Gemini/OpenAI/Anthropic/etc.). Install `sia-agent[openhands]`.
- `pydantic_ai.py` — Pydantic-AI based impl.
- `base.py` — shared interface.

## Providers & profiles — **Nebius is already wired in** (matters for free H200 credits)

Providers (`sia/defaults/providers/`): `anthropic`, `gemini`, `openai`, `nebius`, `tinker`, `together`.
A provider is just a JSON file (client_kind ∈ anthropic|openai|google, base_url, api_key_env) — adding
one is dropping a file, no code change.

Bundled profiles (`sia/defaults/profiles/`) — `--target-agent-profile` / `--meta-agent-profile`:
- `default-meta` (Claude Haiku), `default-target` (Claude Haiku)
- `gemini-meta` (Gemini 3.1 Pro via OpenHands)
- **`gptoss-nebius-target`** — `openai/gpt-oss-120b-fast` on Nebius
- **`qwen-nebius-target`** — `Qwen/Qwen3-Next-80B-A3B-Thinking-fast` on Nebius
- **`kimi-nebius-meta` / `kimi-nebius-target`** — `moonshotai/Kimi-K2.6` on Nebius
- `gptoss-tinker-target`, `qwen3-tinker-target` (Tinker, for weight updates / RL)

**To use the hackathon's Nebius credits:** set `NEBIUS_API_KEY` (check `sia/defaults/providers/nebius.json`
for the exact env var) and pass e.g. `--target-agent-profile gptoss-nebius-target`. GLM/Gemma/DeepSeek
are available on Nebius Token Factory — a new profile JSON for them is a 5-line drop-in.

## Key source files (for the Framework Enhancement / Research tracks)
- `sia/orchestrator.py` (~36 KB) — main loop; holds `META_AGENT_PROMPT` & `FEEDBACK_AGENT_PROMPT`.
- `sia/prompts.py` (~40 KB) — the prompt library that drives self-improvement.
- `sia/context_manager.py` (~22 KB) — run/context tracking, what gets fed back each generation.
- `sia/profiles.py`, `sia/providers.py`, `sia/config*.py` — model/provider wiring.
- `sia/agent_reference.py` — seed target-agent code.
- `sia/web/` — the runs visualizer (FastAPI dashboard).
- `sia/prepare_mlebench_dataset.py` — MLE-bench dataset prep.

## Bundled tasks (templates to copy)
`gpqa` (multiple-choice QA), `lawbench` (191-class text classification, has the cleanest
`evaluate.py`), `longcot-chess` (long-CoT reasoning), `spaceship-titanic` (Kaggle tabular ML).
`spaceship-titanic` and `lawbench` are the best copy-paste starting points for a new task.

## Fast-path ideas by track (see hackathon-brief for full context)
- **Applied AI:** new `--task_dir` task in a domain a judge instantly gets, with a baseline→SIA metric
  curve. Reuse the `lawbench`/`spaceship-titanic` skeleton; solver model on Nebius.
- **Framework Enhancement:** edit `orchestrator.py` prompts / `context_manager.py` feedback; new
  provider/profile (GLM/Gemma/DeepSeek); better improvement.md schema; faster eval loop.
- **Research:** "Autonomous Goal Proposer" (task-discovery stage), or a novel TTRL pseudo-reward /
  evaluation methodology (the slides explicitly tee these up).
