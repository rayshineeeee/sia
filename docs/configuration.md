# Configuration

Full reference for SIA's agent **profiles**, **providers**, and command-line arguments.

## Command-line arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--task` | one of | — | Name of a bundled task: `gpqa`, `lawbench`, `longcot-chess`, `spaceship-titanic` |
| `--task_dir` | one of | — | Path to an external task directory (mutually exclusive with `--task`) |
| `--max_gen` | no | `3` | Number of self-improvement generations |
| `--run_id` | no | `1` | Unique run identifier |
| `--meta-profile` | no | `default-meta` | Profile for the meta/feedback agent (name or path to a `.json`) |
| `--target-profile` | no | `default-target` | Profile for the target agent (name or path to a `.json`) |
| `--sandbox` | no | `none` | Target-agent isolation: `none` or `docker` |

There are two agent roles, each selected by a profile:

- the **meta/feedback agent** runs *inside* SIA via a backend (`claude` / `openhands` /
  `pydantic-ai`) — selected with `--meta-profile`;
- the **target agent** is *generated code* SIA never runs directly — its model/provider come
  from `--target-profile`, and the meta-agent refactors the task's reference agent to that
  provider's SDK.

## Profiles and providers

Configuration is **declarative JSON** you can extend without touching code.

### Provider — an endpoint + credentials

```jsonc
// sia/defaults/providers/nebius.json
{
  "provider_id": "nebius",                                   // stable id (also the filename stem)
  "name": "Nebius Token Factory",                            // human-readable display name
  "client_kind": "openai",                                   // anthropic | openai | google
  "base_url": "https://api.tokenfactory.us-central1.nebius.com/v1/",
  "api_key_env": "NEBIUS_API_KEY"
}
```

Bundled providers: `anthropic`, `gemini`, `openai`, `together`, `nebius`.

### AgentProfile — `(backend, model, provider)` for one role

```jsonc
// sia/defaults/profiles/kimi-nebius.json
{
  "profile_id": "kimi-nebius",     // stable id (also the value you pass to --target-profile)
  "name": "Kimi K2.6 on Nebius",   // human-readable display name
  "backend": "codegen",            // a backend name, or "codegen" for the target agent
  "model": "moonshotai/Kimi-K2.6",
  "provider_id": "nebius"          // references a provider by its provider_id
}
```

Each file carries both a stable `*_id` (used for references and on the CLI — keep it equal to the
filename stem so name lookups resolve) and a friendly `name` for display.

Bundled profiles:

| Profile | backend | model | provider |
|---------|---------|-------|----------|
| `default-meta` | `claude` | `haiku` | `anthropic` |
| `default-target` | `codegen` | `claude-haiku-4-5-20251001` | `anthropic` |
| `kimi-nebius` | `codegen` | `moonshotai/Kimi-K2.6` | `nebius` |

### Resolution — name or path

A profile/provider value that contains `/` or ends in `.json` is loaded as a **file path**.
Otherwise a bare **name** resolves in order:

1. the user directory — `$SIA_PROFILES_DIR` / `$SIA_PROVIDERS_DIR`, else `./profiles` / `./providers`;
2. the bundled defaults shipped in the package.

Add your own by dropping a JSON file in `./providers/` or `./profiles/` (no code change):

```bash
sia --task gpqa --target-profile kimi-nebius          # bundled name
sia --task gpqa --target-profile ./profiles/mine.json # explicit path
```

## Running

### Default (Claude target, Claude meta)

```bash
sia --task gpqa --max_gen 5 --run_id 1
```

Claude model shortcuts (used by the `claude` backend and `claude-*` target models):
`haiku` → `claude-haiku-4-5-20251001`, `sonnet` → `claude-sonnet-4-5-20250929`,
`opus` → `claude-opus-4-5-20251101`.

### Kimi-K2.6 on Nebius as the target model

```bash
export NEBIUS_API_KEY="..."        # target provider
export ANTHROPIC_API_KEY="..."     # default-meta agent
sia --task gpqa --target-profile kimi-nebius --max_gen 5 --run_id 2
```

The meta-agent refactors the task's reference agent to call the `openai` SDK at the Nebius
`base_url` with `NEBIUS_API_KEY` (dollar-cost is reported as 0 — per-provider pricing is unknown).

### Pointing the meta/feedback agent at another provider

The `claude` backend is Anthropic-only (a profile pairing `backend: claude` with a non-anthropic
provider is rejected at load time). To run the meta agent elsewhere, author a profile with the
`openhands` or `pydantic-ai` backend:

```jsonc
// ./profiles/gemini-meta.json
{ "profile_id": "gemini-meta", "name": "Gemini meta agent", "backend": "openhands",
  "model": "gemini/gemini-3.1-pro-preview", "provider_id": "gemini" }
```

```bash
sia --task gpqa --meta-profile gemini-meta
```

Backend model-spec conventions: OpenHands uses fully-qualified `provider/model`
(`gemini/gemini-3.1-pro-preview`, `openai/gpt-4`); PydanticAI uses native specs
(`openai:gpt-4o`, `anthropic:claude-sonnet-4-5-20250929`, `google-gla:gemini-3.1-pro-preview`).
Install the PydanticAI extra with `pip install 'sia-agent[pydantic-ai]'`.

## API keys

Set the `api_key_env` for each provider you use (the orchestrator warns at startup if one is unset):

```bash
export ANTHROPIC_API_KEY="..."   # anthropic provider (claude backend / claude target models)
export GEMINI_API_KEY="..."      # gemini provider  (or GOOGLE_API_KEY via openhands)
export OPENAI_API_KEY="..."      # openai provider
export TOGETHER_API_KEY="..."    # together provider
export NEBIUS_API_KEY="..."      # nebius provider
```

## Comparing multiple LLMs on the same task

```bash
sia --task gpqa --max_gen 3 --run_id 1 --target-profile default-target   # Claude
sia --task gpqa --max_gen 3 --run_id 2 --target-profile kimi-nebius      # Kimi on Nebius
```

Each run lands in its own `runs/run_{id}/` directory, so they can be compared side by side.

## Environment-variable defaults

`SIA_META_PROFILE` / `SIA_TARGET_PROFILE` set the default profile names (overridden by the CLI
flags). `SIA_MAX_GENERATIONS`, `SIA_MAX_TURNS`, and `SIA_SANDBOX_MODE` are also honored.

## Notes

- The `claude` backend only accepts the Claude shortcut names (`haiku`, `sonnet`, `opus`) and an
  `anthropic` provider. For any other provider, use an `openhands` or `pydantic-ai` profile.
- Make sure the API key matching each chosen provider is in the environment before launching.
